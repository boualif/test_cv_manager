from pydantic_settings import BaseSettings # type: ignore

class Settings(BaseSettings):
    # Make the API key optional with a default empty string
    ELASTICSEARCH_HOST: str = "localhost"
    ELASTICSEARCH_PORT: int = 9200
    ELASTICSEARCH_INDEX_CANDIDATES: str = "candidates"
    
    ELASTICSEARCH_URL: str = ""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Construire l'URL complète
        self.ELASTICSEARCH_URL = f"http://{self.ELASTICSEARCH_HOST}:{self.ELASTICSEARCH_PORT}"
    OPENAI_API_KEY: str = ""
    POSTGRES_URI: str
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        # Allow extra fields in case there are environment variables not defined in this class
        extra = "ignore"

settings = Settings()