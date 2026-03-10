import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine
from single_app import Base

# Load DATABASE_URL from .env manually if needed, or rely on environment
# Given we are running in the same environment, os.getenv should work if we load it
from dotenv import load_dotenv
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

async def migrate():
    if not DATABASE_URL or "sqlite" in DATABASE_URL:
        print(f"ERROR: DATABASE_URL is either missing or still points to SQLite: {DATABASE_URL}")
        return

    print(f"Connecting to: {DATABASE_URL.split('@')[-1]} (password hidden)")
    engine = create_async_engine(DATABASE_URL)
    
    async with engine.begin() as conn:
        print("Creating tables...")
        await conn.run_sync(Base.metadata.create_all)
        print("Tables created successfully!")
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(migrate())
