import asyncio
import uuid
from sqlalchemy import select
from single_app import SessionLocal, User, Vehicle, UserRole

async def seed_data():
    async with SessionLocal() as db:
        async with db.begin():
            # Create user if not exists
            email = "user@test.com"
            q = select(User).where(User.email == email)
            user = (await db.execute(q)).scalar_one_or_none()
            if not user:
                user = User(
                    id=str(uuid.uuid4()),
                    role=UserRole.USER,
                    full_name="Test User",
                    email=email,
                    password_hash="mock_hash"
                )
                db.add(user)
                await db.flush()
                print(f"Created user: {user.id}")
            else:
                print(f"User already exists: {user.id}")

            # Create vehicle if not exists
            plate = "AP12AB1234"
            q_v = select(Vehicle).where(Vehicle.vehicle_number == plate)
            vehicle = (await db.execute(q_v)).scalar_one_or_none()
            if not vehicle:
                vehicle = Vehicle(
                    id=str(uuid.uuid4()),
                    user_id=user.id,
                    vehicle_number=plate
                )
                db.add(vehicle)
                print(f"Created vehicle for {plate}")
            else:
                vehicle.user_id = user.id # Ensure it's linked to our test user
                print(f"Vehicle {plate} already exists, linked to user")

if __name__ == "__main__":
    asyncio.run(seed_data())
