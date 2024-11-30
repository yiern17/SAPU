from sqlalchemy.orm import Session
from main import SessionLocal, User, Driver, Booking

db = SessionLocal()

# Fetch users
users = db.query(User).all()
print("Users:", [u.__dict__ for u in users])

# Fetch drivers
drivers = db.query(Driver).all()
print("Drivers:", [d.__dict__ for d in drivers])

# Fetch bookings
bookings = db.query(Booking).all()
print("Bookings:", [b.__dict__ for b in bookings])

db.close()
