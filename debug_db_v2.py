import asyncio
import os
from sqlalchemy import select, text
from single_app import engine, SessionLocal, User, Vehicle, Violation, Challan

async def check():
    print("Connecting to DB...")
    async with engine.connect() as conn:
        print("Table check:")
        res = await conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
        print("Tables:", [r[0] for r in res.all()])

    async with SessionLocal() as db:
        print("\nQuerying Users...")
        users = (await db.execute(select(User))).scalars().all()
        for u in users: print(f"User: {u.email}, ID: {u.id}, Role: {u.role}")

        print("\nQuerying Challans...")
        challans = (await db.execute(select(Challan))).scalars().all()
        for c in challans: print(f"Challan ID: {c.id}, UserID: {c.user_id}, Status: {c.status}")

if __name__ == "__main__":
    print("Starting script...")
    asyncio.run(check())
