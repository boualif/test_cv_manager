from sqlalchemy import create_engine, URL
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Create a connection URL object directly (safer than string concatenation)
connection_url = URL.create(
    "postgresql",
    username="postgres",
    password="Messilat@2024#",  # Original password with special characters
    host="localhost",  # Try localhost instead of postgres
    port=5432,
    database="candidate_db"
)

# Create the engine with the URL object
engine = create_engine(connection_url)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()