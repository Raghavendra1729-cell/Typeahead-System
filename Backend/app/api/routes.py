from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks                                                            
from sqlalchemy.ext.asyncio import AsyncSession                                                                                   
from sqlalchemy.future import select                                                                                              
from datetime import datetime, timezone                                                                                           
                                                                                                                                    
from app.core.database import get_db, get_redis_client_for_prefix, cache_ring                                                     
from app.models.query import SearchQuery                                                                                          
from app.core.scoring import calculate_trending_score                                                                             
from app.services.batch_worker import batch_processor                                                                             
                                                                                                                                    
router = APIRouter()                                                                                                              
                                                                                                                                    
# --- HELPER FUNCTIONS ---                                                                                                        
                                                                                                                                    
async def fetch_fallback_suggestions(prefix: str, db: AsyncSession, redis_client) -> list:                                        
    result = await db.execute(                                                                                                    
        select(SearchQuery).where(SearchQuery.query.like(f"{prefix}%")).order_by(SearchQuery.count.desc()).limit(50)              
    )                                                                                                                             
    scored = [                                                                                                                    
        (item.query, calculate_trending_score(item.count, item.last_searched_at))                                                 
        for item in result.scalars().all()                                                                                        
    ]                                                                                                                             
    scored.sort(key=lambda x: x[1], reverse=True)                                                                                 
    top_10 = scored[:10]                                                                                                          
                                                                                                                                    
    if top_10:                                                                                                                    
        mapping = {query: score for query, score in top_10}                                                                       
        await redis_client.zadd(f"prefix:{prefix}", mapping)                                                                      
        await redis_client.expire(f"prefix:{prefix}", 3600)                                                                       
    return [item[0] for item in top_10]                                                                                           
                                                                                                                                    
# NEW: This runs in the background so the user doesn't wait for Redis!                                                            
async def background_prefix_update(query_str: str, final_score: int):                                                             
    for i in range(1, len(query_str) + 1):                                                                                        
        prefix = query_str[:i]                                                                                                    
        redis_client = get_redis_client_for_prefix(prefix)                                                                        
        await redis_client.zadd(f"prefix:{prefix}", {query_str: final_score})                                                     
        await redis_client.zremrangebyrank(f"prefix:{prefix}", 0, -11)                                                            
                                                                                                                                    
# --- ROUTES ---                                                                                                                  
                                                                                                                                    
@router.get("/suggest")                                                                                                           
async def get_suggestions(q: str = "", db: AsyncSession = Depends(get_db)):                                                       
    if not q: return []                                                                                                           
    prefix = q.lower().strip()                                                                                                    
    redis_client = get_redis_client_for_prefix(prefix)                                                                            
                                                                                                                                    
    if await redis_client.exists(f"prefix:{prefix}"):                                                                             
        return {"source": "cache", "data": await redis_client.zrevrange(f"prefix:{prefix}", 0, 9)}                                
                                                                                                                                    
    fallback_data = await fetch_fallback_suggestions(prefix, db, redis_client)                                                    
    return {"source": "database", "data": fallback_data}                                                                          
                                                                                                                                    
                                                                                                                                    
@router.post("/search")                                                                                                           
async def submit_search(q: str, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):                           
    if not q: raise HTTPException(status_code=400, detail="Query cannot be empty")                                                
    query_str = q.lower().strip()                                                                                                 
                                                                                                                                    
    result = await db.execute(select(SearchQuery).where(SearchQuery.query == query_str))                                          
    db_query = result.scalar_one_or_none()                                                                                        
    new_total_count = (db_query.count if db_query else 0) + batch_processor.buffer.get(query_str, 0) + 1                          
                                                                                                                                    
    await batch_processor.add_search(query_str) # Postgres batching                                                               
                                                                                                                                    
    final_score = calculate_trending_score(new_total_count, datetime.now(timezone.utc))                                           
                                                                                                                                    
    # NEW: Offload the Redis loop to a background task! The API returns instantly.                                                
    background_tasks.add_task(background_prefix_update, query_str, final_score)                                                   
                                                                                                                                    
    return {"message": "Searched", "score": final_score}                                                                          
                                                                                                                                    
                                                                                                                                    
@router.get("/trending")                                                                                                          
async def get_trending_searches():                                                                                                
    global_redis = get_redis_client_for_prefix("GLOBAL_TRENDING")                                                                 
    trending = await global_redis.zrevrange("trending_global", 0, 9)                                                              
    return {"source": "cache", "data": trending}                                                                                  
                                                                                                                                    
                                                                                                                                    
@router.get("/cache/debug")
async def debug_cache(prefix: str):
    if not prefix: raise HTTPException(status_code=400, detail="Prefix is required")
    prefix = prefix.lower().strip()
    redis_client = get_redis_client_for_prefix(prefix)
    return {
        "prefix": prefix,
        "responsible_node": cache_ring.get_node(prefix),
        "cache_status": "hit" if await redis_client.exists(f"prefix:{prefix}") else "miss"
    }