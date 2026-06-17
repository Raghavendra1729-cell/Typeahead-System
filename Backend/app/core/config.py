from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    REDIS_NODE_1: str
    REDIS_NODE_2: str
    REDIS_NODE_3: str

    class Config:
        env_file = ".env"

settings = Settings()