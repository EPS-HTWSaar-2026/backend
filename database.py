from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Conection with SQLite
DATABASE_URL = "sqlite:///./tags.db"

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(bind=engine)

Base = declarative_base()