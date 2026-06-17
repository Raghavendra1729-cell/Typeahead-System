from datetime import datetime, timezone                                                                                           
                                                                                                                                    
def calculate_trending_score(count: int, last_searched_at: datetime) -> int:                                                      
    """                                                                                                                           
    Calculates the final score based on historical count + recency bonus.                                                         
    """                                                                                                                           
    if not last_searched_at:                                                                                                      
        return count
        
    now = datetime.now(timezone.utc)
    
    # Ensure timezone awareness to avoid math errors
    if last_searched_at.tzinfo is None:
        last_searched_at = last_searched_at.replace(tzinfo=timezone.utc)
        
    delta = now - last_searched_at
    hours = delta.total_seconds() / 3600
    days = delta.days
    
    bonus = 0
    if hours <= 1:
        bonus = 1000
    elif hours <= 24:
        bonus = 500
    elif days <= 7:
        bonus = 250
    elif days <= 30:
        bonus = 200
    elif days <= 180:  
        bonus = 100
    elif days <= 365: 
        bonus = 50
    else:
        bonus = 0
        
    return count + bonus