import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    PROJECT_NAME:str = "Skill Bridge AI"
    PROJECT_VERSION:str = "1.0.0"
    PROJECT_DESCRIPTION:str = ""
    POSTGRES_USER : str = os.getenv("POSTGRES_USER")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
    POSTGRES_HOST : str = os.getenv("POSTGRES_HOST")
    POSTGRES_DB : str = os.getenv("POSTGRES_DB")
    SECRET_KEY= os.getenv("SECRET_KEY")
    ALGORITHM = os.getenv("ALGORITHM")
    DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}/{POSTGRES_DB}"
settings = Settings()

