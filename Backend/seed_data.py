import os                                                                                                                         
import kagglehub                                                                                                                  
import pandas as pd                                                                                                               
import asyncio                                                                                                                    
from datetime import datetime, timezone                                                                                           
from sqlalchemy.ext.asyncio import AsyncSession                                                                                   
from app.core.database import SessionLocal, get_redis_client_for_prefix                                                           
from app.models.query import SearchQuery                                                                                          
                                                                                                                                    
async def seed_data():                                                                                                            
    print("1. Downloading dataset from Kaggle...")                                                                                
    path = kagglehub.dataset_download("dineshydv/aol-user-session-collection-500k")                                               
                                                                                                                                    
    data_file = None                                                                                                              
    for file in os.listdir(path):                                                                                                 
        if file.endswith('.csv') or file.endswith('.tsv') or file.endswith('.txt'):                                               
            data_file = os.path.join(path, file)                                                                                  
            break                                                                                                                 
                                                                                                                                    
    print(f"2. Reading data from {data_file}...")                                                                                 
    df = pd.read_csv(data_file, sep='\t', on_bad_lines='skip')                                                                    
                                                                                                                                    
    # Standardize column names to lowercase                                                                                       
    df.columns = [col.lower() for col in df.columns]                                                                              
                                                                                                                                    
    print("3. Aggregating queries and finding their latest 2006 timestamp...")                                                    
    df['query'] = df['query'].astype(str).str.lower().str.strip()                                                                 
    df = df[df['query'] != "nan"]                                                                                                 
    df = df[df['query'] != ""]                                                                                                    
                                                                                                                                    
    # Convert Kaggle's QueryTime to actual datetime objects                                                                       
    df['querytime'] = pd.to_datetime(df['querytime'], errors='coerce')                                                            
                                                                                                                                    
    # Group by query: get total count and the maximum (most recent) QueryTime from 2006                                           
    aggregated = df.groupby('query').agg(                                                                                         
        count=('query', 'count'),                                                                                                 
        last_searched_at=('querytime', 'max')                                                                                     
    ).reset_index()                                                                                                               
                                                                                                                                    
    # Take top 20,000 for fast local seeding                                                                                      
    top_queries = aggregated.sort_values('count', ascending=False).head(20000)                                                    
                                                                                                                                    
    print(f"4. Inserting Top {len(top_queries)} queries into Postgres and Redis...")                                              
    async with SessionLocal() as db:                                                                                              
        for index, row in top_queries.iterrows():                                                                                 
            query_str = row['query']                                                                                              
            count = int(row['count'])                                                                                             
                                                                                                                                    
            # Convert timestamp to timezone-aware UTC for Postgres                                                                
            dt = row['last_searched_at']                                                                                          
            if pd.isna(dt):                                                                                                       
                dt = datetime.now(timezone.utc)                                                                                   
            else:                                                                                                                 
                dt = dt.replace(tzinfo=timezone.utc)
            
            # 1. Insert to Postgres with the real 2006 timestamp
            db_query = SearchQuery(query=query_str, count=count, last_searched_at=dt)
            db.add(db_query)
            
            # 2. Insert to Redis cache
            # Because 2006 is > 1 year ago, your bonus formula yields 0. Redis score is just raw count.
            for i in range(1, len(query_str) + 1):
                prefix = query_str[:i]
                redis_client = get_redis_client_for_prefix(prefix)
                await redis_client.zadd(f"prefix:{prefix}", {query_str: count})
                await redis_client.zremrangebyrank(f"prefix:{prefix}", 0, -11)

            if index > 0 and index % 1000 == 0:
                print(f"Inserted {index} queries...")
                await db.commit() 

        await db.commit() 
        
    print("✅ Seeding complete! The 2006 timestamps are safely stored.")

if __name__ == "__main__":
    asyncio.run(seed_data())