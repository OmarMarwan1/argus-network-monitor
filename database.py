from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv

load_dotenv()

db_url = f"postgresql+psycopg2://postgres:{os.getenv('DB_PASSWORD')}@localhost:5432/postgres"
engine = create_engine(db_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# this file is finished
