import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

# Railway will inject DATABASE_URL in production
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:wnjQUAGFTDbmvCDHEUkJtUGfuCYbTTxU@postgres.railway.internal:5432/railway"
)

# Create async engine
engine = create_async_engine(DATABASE_URL, echo=False, future=True)

# Session maker
SessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

# Base for models
Base = declarative_base()
