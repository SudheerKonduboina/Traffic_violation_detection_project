import asyncio
from sqlalchemy import select
from single_app import SessionLocal, Challan, Violation, User, Vehicle

async def check_db():
    async with SessionLocal() as db:
        async with db.begin():
            # Check users
            users = (await db.execute(select(User.id, User.email))).all()
            print("\n--- USERS ---")
            for u in users: print(f"ID: {u[0]}, Email: {u[1]}")

            # Check vehicles
            vehicles = (await db.execute(select(Vehicle.id, Vehicle.user_id, Vehicle.vehicle_number))).all()
            print("\n--- VEHICLES ---")
            for v in vehicles: print(f"ID: {v[0]}, UserID: {v[1]}, Plate: {v[2]}")

            # Check violations
            violations = (await db.execute(select(Violation.id, Violation.plate_text_norm))).all()
            print("\n--- VIOLATIONS ---")
            for v in violations: print(f"ID: {v[0]}, Plate: {v[1]}")

            # Check challans
            challans = (await db.execute(select(Challan.id, Challan.user_id, Challan.status, Challan.violation_id))).all()
            print("\n--- CHALLANS ---")
            for c in challans: print(f"ID: {c[0]}, UserID: {c[1]}, Status: {c[2]}, ViolationID: {c[3]}")

if __name__ == "__main__":
    asyncio.run(check_db())
