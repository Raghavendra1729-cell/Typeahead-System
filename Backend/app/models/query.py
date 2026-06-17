from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from app.core.database import Base

class SearchQuery(Base):
    __tablename__ = "search_queries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    query = Column(String, unique=True, index=True, nullable=False)
    count = Column(Integer, default=1, index=True)
    
    # NEW: Used for the "Recency / Trending Searches" requirement
    # It automatically sets the time on creation and updates it on modification
    last_searched_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), index=True)