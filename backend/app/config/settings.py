import os
from pydantic_settings import BaseSettings # type: ignore

class Settings(BaseSettings):
    # Database settings - use environment variable with fallback
    POSTGRES_URI: str = os.getenv("POSTGRES_URI", "postgresql://postgres:Messilat@2024#@localhost:5432/candidate_db")
    
    # Elasticsearch settings - use environment variable with fallback
    ELASTICSEARCH_URL: str = os.getenv("ELASTICSEARCH_URL", "http://localhost:9200")
    ELASTICSEARCH_INDEX_CANDIDATES: str = "candidates"
    
    # OpenAI settings
    OPENAI_API_KEY: str = ""
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        # Allow extra fields in case there are environment variables not defined in this class
        extra = "ignore"

settings = Settings()
