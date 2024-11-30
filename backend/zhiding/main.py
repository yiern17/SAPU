from fastapi import FastAPI, HTTPException, Depends, WebSocket, BackgroundTasks
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy import Column, Integer, String, Float, create_engine, ForeignKey, DateTime, func, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from typing import List, Optional
import enum
import logging
from pydantic import BaseModel, constr


# Set up logging
logging.basicConfig(level=logging.INFO)
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
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    full_name = Column(String)
    preferences = Column(String, default="")
    bookings = relationship("Booking", back_populates="user")
    
class UserRegistrationInput(BaseModel):
    username: str 
    password: str  
    full_name: str
 
class Token(BaseModel): 
    access_token: str 
    token_type: str 
    
class TokenData(BaseModel): 
    username: Optional[str] = None 
    
class UserLoginInput(BaseModel): 
    username: str 
    password: str

class Driver(Base):
    __tablename__ = "drivers"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String)
    license_number = Column(String)
    vehicle_model = Column(String)
    vehicle_number = Column(String)
    contact_number = Column(String)
    bookings = relationship("Booking", back_populates="driver")

class Booking(Base):
    __tablename__ = "bookings"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    driver_id = Column(Integer, ForeignKey("drivers.id"), nullable=True)
    pickup_location = Column(String)
    destination = Column(String)
    distance = Column(Float)
    time = Column(Float)
    fare = Column(Float)
    passengers = Column(Integer, default=1)
    pickup_time = Column(DateTime)
    status = Column(Enum(BookingStatus), default=BookingStatus.PENDING)
    timestamp = Column(DateTime, server_default=func.now())
    user = relationship("User", back_populates="bookings")
    driver = relationship("Driver", back_populates="bookings")

Base.metadata.create_all(bind=engine)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        logging.info("Database connection established")
        yield db
    finally:
        db.close()
        logging.info("Database connection closed")

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
@app.post("/register/user/")
def register_user(user: UserRegistrationInput, db: Session = Depends(get_db)):
    logging.info(f"Received registration request for username: {user.username}")
    existing_user = db.query(User).filter(User.username == user.username).first()
    if existing_user:
        logging.warning(f"Username already exists: {user.username}")
        raise HTTPException(status_code=400, detail="Username already registered")
    
    hashed_password = get_password_hash(user.password)
    new_user = User(username=user.username, hashed_password=hashed_password, full_name=user.full_name)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    logging.info(f"User registered successfully: {user.username}")
    return {"message": "User registered successfully"}


class DriverRegistrationInput(BaseModel):
    driver_name: str
    license_number: str
    vehicle_model: str
    vehicle_number: str
    contact_number: str
    
@app.post("/register/driver/")
def register_driver(driver: DriverRegistrationInput, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == current_user.username).first() 
    if not user: 
        raise HTTPException(status_code=404, detail="User not found") # Check if the user is already a driver 
    existing_driver = db.query(Driver).filter(Driver.user_id == user.id).first() 
    if existing_driver: 
        raise HTTPException(status_code=400, detail="User is already registered as a driver")
    new_driver = Driver( 
                user_id=user.id, 
                name=driver.driver_name, 
                license_number=driver.license_number, 
                vehicle_model=driver.vehicle_model, 
                vehicle_number=driver.vehicle_number, 
                contact_number=driver.contact_number
    )
    db.add(new_driver)
    db.commit()
    db.refresh(new_driver)
    return {"message": "Driver registered successfully"}

@app.post("/token", response_model=Token) 
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)): 
    user = db.query(User).filter(User.username == form_data.username).first() 
    if not user or not verify_password(form_data.password, user.hashed_password): 
        raise HTTPException( 
                    status_code=401, 
                    detail="Incorrect username or password", 
                    headers={"WWW-Authenticate": "Bearer"}, 
        ) 
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES) 
    access_token = create_access_token(data={"sub": user.username}, expires_delta=access_token_expires) 
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/profile/")
def read_user_profile(current_user: User = Depends(get_current_user)):
    return {"username": current_user.username, "full_name": current_user.full_name, "preferences": current_user.preferences}

@app.post("/book_ride/")
def book_ride(
    pickup_location: str,
    destination: str,
    pickup_time: datetime,
    passengers: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    fare = 20 * passengers  # Example fare calculation based on passengers
    new_booking = Booking(
        user_id=current_user.id,
        pickup_location=pickup_location,
        destination=destination,
        pickup_time=pickup_time,
        passengers=passengers,
        fare=fare,
        status=BookingStatus.PENDING
    )
    db.add(new_booking)
    db.commit()
    return {"message": "Ride booked successfully", "fare": fare, "booking_id": new_booking.id}

@app.get("/user/bookings/")
def get_user_bookings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    bookings = db.query(Booking).filter(Booking.user_id == current_user.id).all()
    return {"bookings": [booking.__dict__ for booking in bookings]}

@app.post("/cancel_booking/{booking_id}")
def cancel_booking(booking_id: int, current_user: User = Depends(get_current_user), db=Depends(get_db)):
    booking = db.query(Booking).filter(Booking.id == booking_id, Booking.user_id == current_user.id).first()
    if not booking or booking.status not in [BookingStatus.PENDING, BookingStatus.ACCEPTED]:
        raise HTTPException(status_code=404, detail="Booking not found or cannot be canceled")
    booking.status = BookingStatus.CANCELED
    db.commit()
    return {"message": "Booking canceled successfully"}

@app.get("/driver/pending_bookings/")
def get_pending_bookings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    driver = db.query(Driver).filter(Driver.user_id == current_user.id).first()
    if not driver:
        raise HTTPException(status_code=400, detail="Driver not registered")
    bookings = db.query(Booking).filter(Booking.driver_id == None, Booking.status == BookingStatus.PENDING).all()
    return {"bookings": [booking.__dict__ for booking in bookings]}

@app.get("/driver/accepted_bookings/")
def get_accepted_bookings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    driver = db.query(Driver).filter(Driver.user_id == current_user.id).first()
    if not driver:
        raise HTTPException(status_code=400, detail="Driver not registered")
    bookings = db.query(Booking).filter(Booking.driver_id == driver.id, Booking.status == BookingStatus.ACCEPTED).all()
    return {"bookings": [booking.__dict__ for booking in bookings]} 

@app.put("/driver/accept_booking/{booking_id}")
def accept_booking(
    booking_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    driver = db.query(Driver).filter(Driver.user_id == current_user.id).first()
    if not driver:
        raise HTTPException(status_code=400, detail="Driver not registered")
    booking = db.query(Booking).filter(Booking.id == booking_id, Booking.driver_id == None, Booking.status == BookingStatus.PENDING).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found or not pending")
    booking.driver_id = driver.id
    booking.status = BookingStatus.ACCEPTED
    db.commit()
    return {"message": "Booking accepted successfully"}

@app.put("/driver/reject_booking/{booking_id}")
def reject_booking(
    booking_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    driver = db.query(Driver).filter(Driver.user_id == current_user.id).first()
    if not driver:
        raise HTTPException(status_code=400, detail="Driver not registered")
    booking = db.query(Booking).filter(Booking.id == booking_id, Booking.driver_id == None, Booking.status == BookingStatus.PENDING).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found or not pending")
    booking.status = BookingStatus.REJECTED
    db.commit()
    return {"message": "Booking rejected successfully"}

@app.websocket("/realtime_tracking/{booking_id}")
async def websocket_endpoint(booking_id: int, websocket: WebSocket, db: Session = Depends(get_db)):
    await websocket.accept()
    # Implement real-time tracking updates here
    # For example, send location updates to the client
    await websocket.send_text("Tracking started")
    await websocket.close()

# Additional endpoints and handlers can be added as needed
@app.get("/")
def read_root():
    return {"message": "Welcome to the SAPU Backend API"}
