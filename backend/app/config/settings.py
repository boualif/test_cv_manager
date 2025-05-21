from pydantic_settings import BaseSettings # type: ignore

class Settings(BaseSettings):
    # Database settings
    POSTGRES_URI: str = ""
    
    # Elasticsearch settings
    ELASTICSEARCH_URL: str = ""
    ELASTICSEARCH_INDEX_CANDIDATES: str = "candidates"
    
    # OpenAI settings
    OPENAI_API_KEY: str = ""
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        # Allow extra fields in case there are environment variables not defined in this class
        extra = "ignore"

settings = Settings()
