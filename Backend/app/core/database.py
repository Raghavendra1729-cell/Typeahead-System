from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession                                                              
from sqlalchemy.orm import declarative_base, sessionmaker                                                                         
import redis.asyncio as redis                                                                                                     
from app.services.cache_ring import ConsistentHash                                                                                
                                                                                                                                                                                                
DATABASE_URL = "postgresql+asyncpg://typeahead_user:typeahead_password@localhost:5432/typeahead_db"                               
                                                                                                                                    
engine = create_async_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False) # type: ignore
Base = declarative_base()

# 2. Redis Setup
REDIS_NODES = [
    "redis://localhost:6379",
    "redis://localhost:6380",
    "redis://localhost:6381"
]

# Create a connection client for each Redis node
redis_clients = {
    node_url: redis.from_url(node_url, decode_responses=True)
    for node_url in REDIS_NODES
}

# Initialize our Consistent Hashing ring with the Redis node URLs
cache_ring = ConsistentHash(nodes=REDIS_NODES)

# 3. Dependency to get DB session
async def get_db():
    async with SessionLocal() as session: # type: ignore
        yield session

# 4. Helper to get the correct Redis client for a specific prefix
def get_redis_client_for_prefix(prefix: str):
    """Returns the correct Redis client based on the prefix hash."""
    node_url = cache_ring.get_node(prefix)
    return redis_clients[node_url]