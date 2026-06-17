import asyncio                                                                                                                    
from datetime import datetime, timezone                                                                                           
from sqlalchemy.ext.asyncio import AsyncSession                                                                                   
from sqlalchemy.future import select                                                                                              
                                                                                                                                    
from app.core.database import SessionLocal, get_redis_client_for_prefix                                                           
from app.models.query import SearchQuery                                                                                          
from app.core.scoring import calculate_trending_score                                                                             
                                                                                                                                    
class BatchProcessor:                                                                                                             
    def __init__(self, flush_interval_seconds: int = 5, trending_interval_seconds: int = 30):                                     
        self.buffer = {}                                                                                                          
        self.flush_interval = flush_interval_seconds                                                                              
        self.trending_interval = trending_interval_seconds # YOUR 30-SECOND RULE                                                  
        self.lock = asyncio.Lock()                                                                                                
                                                                                                                                    
    async def add_search(self, query: str):                                                                                       
        async with self.lock:                                                                                                     
            self.buffer[query] = self.buffer.get(query, 0) + 1                                                                    
            if len(self.buffer) >= 100:                                                                                           
                asyncio.create_task(self.flush_to_db())                                                                           
                                                                                                                                    
    async def flush_to_db(self):                                                                                                  
        async with self.lock:                                                                                                     
            if not self.buffer: return                                                                                            
            batch_data = self.buffer.copy()                                                                                       
            self.buffer.clear()                                                                                                   
                                                                                                                                    
        now_utc = datetime.now(timezone.utc)                                                                                      
        async with SessionLocal() as db:                                                                                          
            for query_str, count in batch_data.items():                                                                           
                result = await db.execute(select(SearchQuery).where(SearchQuery.query == query_str))                              
                db_query = result.scalar_one_or_none()                                                                            
                                                                                                                                    
                if db_query:                                                                                                      
                    db_query.count += count                                                                                       
                    db_query.last_searched_at = now_utc                                                                           
                else:                                                                                                             
                    db_query = SearchQuery(query=query_str, count=count, last_searched_at=now_utc)                                
                    db.add(db_query)                                                                                              
            await db.commit()                                                                                                     
                                                                                                                                    
    async def update_global_trending_cache(self):                                                                                 
        """Your idea: Recalculates the Global Trending Top 10 in the background."""                                               
        async with SessionLocal() as db:                                                                                          
            # Grab the top 500 historical searches to see who is trending today                                                   
            result = await db.execute(select(SearchQuery).order_by(SearchQuery.count.desc()).limit(500))                          
            db_queries = result.scalars().all()                                                                                   
                                                                                                                                    
            scored = [                                                                                                            
                (item.query, calculate_trending_score(item.count, item.last_searched_at))                                         
                for item in db_queries                                                                                            
            ]                                                                                                                     
            scored.sort(key=lambda x: x[1], reverse=True)                                                                         
            top_10 = scored[:10]                                                                                                  
                                                                                                                                    
            if top_10:                                                                                                            
                global_redis = get_redis_client_for_prefix("GLOBAL_TRENDING")                                                     
                mapping = {query: score for query, score in top_10}                                                               
                await global_redis.zadd("trending_global", mapping)                                                               
                await global_redis.zremrangebyrank("trending_global", 0, -11)                                                     
                print("🌍 [Background Task] Recalculated Global Trending searches!")                                              
                                                                                                                                    
    async def start_periodic_flush(self):                                                                                         
        while True:                                                                                                               
            await asyncio.sleep(self.flush_interval)                                                                              
            await self.flush_to_db()                                                                                              
                                                                                                                                    
    async def start_trending_updater(self):                                                                                       
        """Runs your 30-second loop forever."""                                                                                   
        while True:                                                                                                               
            await asyncio.sleep(self.trending_interval)                                                                           
            await self.update_global_trending_cache()                                                                             
                                                                                                                                    
batch_processor = BatchProcessor(flush_interval_seconds=5, trending_interval_seconds=30)