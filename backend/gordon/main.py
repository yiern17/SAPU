from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import random
import requests
from typing import Dict
from math import radians, sin, cos, sqrt, atan2

app = FastAPI()

# Define average speeds for different vehicle types in km/h
speeds = {
    "bus": 40,
    "car": 50,
    "truck": 30,
    "taxi": 45,
    "bike": 15
}

# Define Kuala Lumpur bounds (Latitude: 3.1 to 3.2, Longitude: 101.6 to 101.7)
KUALA_LUMPUR_BOUNDS = {
    "lat_min": 3.1,
    "lat_max": 3.2,
    "lon_min": 101.6,
    "lon_max": 101.7
}

# Function to generate random vehicles of different types within Kuala Lumpur
def generate_random_vehicles(num_buses: int, num_cars: int, num_trucks: int, num_taxis: int, num_bikes: int) -> Dict[str, Dict[str, float]]:
    vehicle_data = {}

    def add_vehicles(vehicle_type, count):
        for i in range(1, count + 1):
            # Generate random coordinates within Kuala Lumpur bounds
            latitude = random.uniform(KUALA_LUMPUR_BOUNDS["lat_min"], KUALA_LUMPUR_BOUNDS["lat_max"])
            longitude = random.uniform(KUALA_LUMPUR_BOUNDS["lon_min"], KUALA_LUMPUR_BOUNDS["lon_max"])
            
            # Debugging print statement
            print(f"Generated {vehicle_type}_{i}: Latitude {latitude}, Longitude {longitude}")
            
            # Ensure generated coordinates are valid
            assert KUALA_LUMPUR_BOUNDS["lat_min"] <= latitude <= KUALA_LUMPUR_BOUNDS["lat_max"], f"Latitude out of bounds: {latitude}"
            assert KUALA_LUMPUR_BOUNDS["lon_min"] <= longitude <= KUALA_LUMPUR_BOUNDS["lon_max"], f"Longitude out of bounds: {longitude}"
            
            # Store vehicle data
            vehicle_data[f"{vehicle_type}_{i}"] = {
                "latitude": latitude,
                "longitude": longitude,
                "vehicle_id": f"{vehicle_type}_{i}"
            }

    # Add different types of vehicles
    add_vehicles("bus", num_buses)
    add_vehicles("car", num_cars)
    add_vehicles("truck", num_trucks)
    add_vehicles("taxi", num_taxis)
    add_vehicles("bike", num_bikes)

    return vehicle_data

# Generate vehicles: 10 buses, 20 cars, 5 trucks, 15 taxis, and 10 bikes
vehicles = generate_random_vehicles(num_buses=10, num_cars=20, num_trucks=5, num_taxis=15, num_bikes=10)

# Function to simulate vehicle location updates
def update_vehicle_location(vehicle_id: str) -> Dict[str, float]:
    if vehicle_id not in vehicles:
        raise ValueError(f"Vehicle ID {vehicle_id} not found.")
    
    vehicle = vehicles[vehicle_id]
    lat_change = random.uniform(-0.0005, 0.0005)  # Small changes to simulate movement
    lon_change = random.uniform(-0.0005, 0.0005)
    
    # Ensure vehicle stays within Kuala Lumpur bounds after update
    new_lat = vehicle["latitude"] + lat_change
    new_lon = vehicle["longitude"] + lon_change

    # Adjust to keep within bounds
    new_lat = max(min(new_lat, KUALA_LUMPUR_BOUNDS["lat_max"]), KUALA_LUMPUR_BOUNDS["lat_min"])
    new_lon = max(min(new_lon, KUALA_LUMPUR_BOUNDS["lon_max"]), KUALA_LUMPUR_BOUNDS["lon_min"])
    
    # Debugging print statement
    print(f"Updated {vehicle_id}: New Latitude {new_lat}, New Longitude {new_lon}")

    # Update vehicle data
    vehicle["latitude"] = new_lat
    vehicle["longitude"] = new_lon
    return vehicle

# Haversine formula to calculate the distance between two latitude/longitude points
def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0  # Radius of the Earth in kilometers
    lat1 = radians(lat1)
    lon1 = radians(lon1)
    lat2 = radians(lat2)
    lon2 = radians(lon2)
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    distance = R * c
    return distance

# Define a model for the vehicle location response
class VehicleLocation(BaseModel):
    vehicle_id: str
    latitude: float
    longitude: float

# API to get vehicle location (Real-time updates)
@app.get("/vehicle/{vehicle_id}/location", response_model=VehicleLocation, description="Get the current location of a vehicle.")
async def get_vehicle_location(vehicle_id: str):
    if vehicle_id not in vehicles:
        raise HTTPException(status_code=404, detail=f"Vehicle ID {vehicle_id} not found")
    updated_vehicle = update_vehicle_location(vehicle_id)
    return updated_vehicle

# Predict arrival time based on real-time vehicle location and destination coordinates
@app.get("/vehicle/{vehicle_id}/arrival_time", description="Predict the vehicle's arrival time to the given destination.")
async def predict_arrival_time(vehicle_id: str, destination_lat: float, destination_lon: float):
    if vehicle_id not in vehicles:
        raise HTTPException(status_code=404, detail=f"Vehicle ID {vehicle_id} not found")
    updated_vehicle = update_vehicle_location(vehicle_id)
    distance = haversine(updated_vehicle["latitude"], updated_vehicle["longitude"], destination_lat, destination_lon)
    vehicle_type = vehicle_id.split("_")[0]
    speed = speeds.get(vehicle_type, 50)
    if speed <= 0:
        raise HTTPException(status_code=500, detail="Invalid speed for the vehicle type.")
    time_to_arrival = distance / speed
    time_to_arrival_minutes = time_to_arrival * 60
    return {"vehicle_id": vehicle_id, "arrival_time_minutes": round(time_to_arrival_minutes, 2)}

# Root endpoint
@app.get("/", description="Welcome message.")
def read_root():
    return {"message": "Welcome to the Multi-Vehicle Tracker API!"}

