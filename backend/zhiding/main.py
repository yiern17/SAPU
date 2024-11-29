from fastapi import FastAPI, HTTPException, Depends, WebSocket
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy import Column, Integer, String, Float, create_engine, ForeignKey, DateTime,func,Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from typing import List 
import enum

# FastAPI setup
app = FastAPI()

# Database setup
Base = declarative_base()
DATABASE_URL = "sqlite:///./sapu.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Security setup
SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Models
class BookingStatus(enum.Enum):
    ACTIVE = "active"
    CANCELED = "canceled"
    COMPLETED = "completed"


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    full_name = Column(String)
    preferences = Column(String, default="")
    bookings = relationship("Booking", back_populates="user")

class Booking(Base):
    __tablename__ = "bookings"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    distance = Column(Float)
    time = Column(Float)
    fare = Column(Float)
    timestamp = Column(String, server_default=func.strftime('%Y-%m-%d %H:%M:%S'))
    status = Column(Enum(BookingStatus), default=BookingStatus.ACTIVE)
    user = relationship("User", back_populates="bookings")
    scheduled_time = Column(DateTime, nullable=True)


Base.metadata.create_all(bind=engine)


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Helper functions
def get_password_hash(password):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Updated get_current_user as async
async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    return user


# Routes
@app.post("/register/")
def register(username: str, password: str, full_name: str, db=Depends(get_db)):
    hashed_password = get_password_hash(password)
    new_user = User(username=username, hashed_password=hashed_password, full_name=full_name)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "User registered successfully"}


@app.post("/token/")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db=Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/profile/")
def read_user_profile(current_user: User = Depends(get_current_user)):
    return {"username": current_user.username, "full_name": current_user.full_name, "preferences": current_user.preferences}


@app.put("/update_preferences/")
def update_preferences(preferences: str, current_user: User = Depends(get_current_user), db=Depends(get_db)):
    current_user.preferences = preferences
    db.commit()
    return {"message": "Preferences updated successfully"}


@app.post("/schedule_ride/")
def schedule_ride(
    distance: float,
    time: float,
    scheduled_time: datetime,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Make scheduled_time timezone-aware if naive
    if scheduled_time.tzinfo is None or scheduled_time.tzinfo.utcoffset(scheduled_time) is None:
        scheduled_time = scheduled_time.replace(tzinfo=timezone.utc)
    
    if scheduled_time < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Scheduled time must be in the future")
    fare = 5 + (distance * 2) + (time * 0.5)
    new_booking = Booking(
        user_id=current_user.id,
        distance=distance,
        time=time,
        fare=fare,
        scheduled_time=scheduled_time,
        status=BookingStatus.ACTIVE
    )
    db.add(new_booking)
    db.commit()
    return {"message": "Ride scheduled successfully", "fare": fare, "booking_id": new_booking.id}


@app.post("/calculate_fare/")
def calculate_fare(distance: float, time: float, current_user: User = Depends(get_current_user), db=Depends(get_db)):
    base_fare = 5  # Base fare in RM
    per_km_rate = 2  # Rate per km
    per_minute_rate = 0.5  # Rate per minute
    fare = base_fare + (distance * per_km_rate) + (time * per_minute_rate)
    
    # Add a try-except block to catch database errors
    try:
        new_booking = Booking(user_id=current_user.id, distance=distance, time=time, fare=fare)
        db.add(new_booking)
        db.commit()
        db.refresh(new_booking)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error saving booking: {str(e)}")
    
    return {"fare": fare, "booking_id": new_booking.id, "message": "Fare calculated successfully"}


@app.post("/cancel_booking/{booking_id}")
def cancel_booking(booking_id: int, current_user: User = Depends(get_current_user), db=Depends(get_db)):
    booking = db.query(Booking).filter(Booking.id == booking_id, Booking.user_id == current_user.id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking.status != BookingStatus.ACTIVE:
        raise HTTPException(status_code=400, detail="Booking cannot be canceled")
    booking.status = BookingStatus.CANCELED
    db.commit()
    return {"message": "Booking canceled successfully"}


@app.put("/modify_booking/{booking_id}")
def modify_booking(booking_id: int, distance: float, time: float, current_user: User = Depends(get_current_user), db=Depends(get_db)):
    booking = db.query(Booking).filter(Booking.id == booking_id, Booking.user_id == current_user.id).first()
    if not booking or booking.status != BookingStatus.ACTIVE:
        raise HTTPException(status_code=404, detail="Booking not found or not modifiable")
    booking.distance = distance
    booking.time = time
    booking.fare = 5 + (distance * 2) + (time * 0.5)  # Recalculate fare
    db.commit()
    return {"message": "Booking modified successfully", "updated_fare": booking.fare}




@app.get("/booking_history/")
def booking_history(current_user: User = Depends(get_current_user), db=Depends(get_db)):
    try:
        bookings = db.query(Booking).filter(Booking.user_id == current_user.id).all()
        if not bookings:
            return {"message": "No bookings found"}
        
        return {
            "bookings": [
                {
                    "booking_id": b.id,
                    "distance": b.distance,
                    "time": b.time,
                    "fare": b.fare,
                    "timestamp": b.timestamp,
                }
                for b in bookings
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving booking history: {str(e)}")


# Real-Time Notifications
@app.websocket("/notifications/")
async def notifications(websocket: WebSocket, token: str, db: Session = Depends(get_db)):
    await websocket.accept()
    try:
        current_user = await get_current_user(token=token, db=db)
        await websocket.send_text(f"Welcome, {current_user.username}! You will receive real-time booking updates here.")
        # Simulated notification
        await websocket.send_text("Your booking has been confirmed!")
    except Exception as e:
        await websocket.send_text(f"Error: {str(e)}")
    finally:
        await websocket.close()





