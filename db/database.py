import os
from sqlmodel import create_engine, Session
from dotenv import load_dotenv

# Load variables from .env file
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set")

#THE FIX: Automatically correct Neon's URL format for SQLModel
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# echo=True prints the raw SQL queries to the terminal (great for MVP debugging)
engine = create_engine(DATABASE_URL, echo=True)

def get_session():
    """Dependency injection for FastAPI routes."""
    with Session(engine) as session:
        yield session