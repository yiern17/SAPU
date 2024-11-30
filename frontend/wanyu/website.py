import streamlit as st
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
import random
from streamlit_option_menu import option_menu
import requests
import logging
from datetime import datetime
import json
import osmnx as ox
import networkx as nx

# Set up logging
logging.basicConfig(level=logging.INFO)

BASE_URL = "http://127.0.0.1:8000"  # FastAPI server address

# Initialize session state for bookings and driver status
if 'is_driver' not in st.session_state:
    st.session_state.is_driver = False

if 'bookings' not in st.session_state:
    st.session_state.bookings = []  # Initialize empty list for bookings

BUS_ROUTES = {
    "AB": {"schedule": ["07:30","07:50","08:10","08:30","09:10","09:30","10:30","11:00","11:30","12:00","13:30","14:00","15:00","16:00","17:00","18:00","19:00","20:00","21:00"],"live_location":[3.1201,101.6544]},
    "BA": {"schedule": ["07:30","07:50","08:10","08:30","09:10","09:30","10:30","11:00","11:30","12:00","13:30","14:00","15:00","16:00","17:00","18:00","19:00","20:00","21:00"],"live_location":[3.1201,101.6544]},
    "C": {"schedule": ["07:30","08:00","08:30","09:00","09:30","10:30","11:00","11:30","12:00","15:00","16:00","17:00","18:00","19:00","20:00","21:00"],"live_location":[3.1201,101.6544]},
    "D": {"schedule": ["07:30","08:00","08:30","09:00","09:30","10:30","11:00","11:30","12:00","15:00","16:00","17:00","18:00","19:00","20:00","21:00"],"live_location":[3.1201,101.6544]},
    "E": {"schedule": ["07:30","08:00","08:30","09:00","09:30","10:30","11:00","11:30","12:00","15:00","16:00","17:00","18:00","19:00","20:00","21:00"],"live_location":[3.1201,101.6544]},
    
}


# Register Function
def register_user(username, password, full_name):
    url = f"{BASE_URL}/register/user/"
    payload = {
        "username": username,
        "password": password,
        "full_name": full_name,
    }
    logging.info(f"Sending POST request to {url} with payload: {payload}")
    response = requests.post(url, json=payload)
    logging.info(f"Registration response: {response.json()}")
    return response.json()

# driver registration function
def register_driver(token, full_name, license_number, vehicle_model, vehicle_number, contact_number): 
    url = f"{BASE_URL}/register/driver/" 
    payload = { 
               "full_name": full_name, 
               "license_number": license_number, 
               "vehicle_model": vehicle_model, 
               "vehicle_number": vehicle_number, 
               "contact_number": contact_number, } 
    headers = {
        "Authorization": f"Bearer {token}"
        } 
    response = requests.post(url, json=payload, headers=headers) 
    logging.info(f"Driver registration response: {response.json()}") 
    return response.json()


# Login Function
def login_user(username, password):
    url = f"{BASE_URL}/token/"
    payload = {
        "username": username,
        "password": password,
    }
    response = requests.post(url, data=payload)
    return response.json()
# Homepage
def home():
    st.title('Welcome to SAPU')
    st.subheader("Your transportation service app.")
    
    # Display greeting if user is logged in 
    if 'username' in st.session_state: 
        st.write(f"Hi {st.session_state['username']}!") 
        st.write("Choose a service from the menu on the left.")
    else :
        
        # Register form
        with st.form(key='register_form'):
            st.header("Register")
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            full_name = st.text_input("Full Name")
            register_button = st.form_submit_button("Register")
            
            if register_button:
                if username and password and full_name:
                    response = register_user(username, password, full_name)
                    if 'message' in response:
                        st.success(response["message"])
                    else:
                        st.error("Registration failed. Please try again.")
                else:
                    st.error("Please fill all fields.")

        # Login form
        with st.form(key='login_form'):
            st.header("Login")
            username = st.text_input("Username", key='login_username')
            password = st.text_input("Password", type="password", key='login_password')
            login_button = st.form_submit_button("Login")
            
            if login_button:
                if username and password:
                    response = login_user(username, password)
                    if 'access_token' in response:
                        st.success("Login successful!")
                        st.session_state.token = response['access_token']
                        st.session_state.username = username
                        
                    else:
                        st.error("Login failed. Please check your credentials.")
                else:
                    st.error("Please fill all fields.")

    

    

# Function to get coordinates from an address
def get_coordinates(address):
    geolocator = Nominatim(user_agent="saputracker")
    location = geolocator.geocode(address)
    if location:
        return location.latitude, location.longitude
    else:
        return None,None

# Function to calculate driving distance using OSM data
def calculate_driving_distance(pickup, dropoff):
    pickup_lat, pickup_lon = get_coordinates(pickup)
    dropoff_lat, dropoff_lon = get_coordinates(dropoff)

    if pickup_lat is None or dropoff_lat is None:
        st.error("One or both locations not found. Please enter valid addresses.")
        return None

    # Download the street network for the area around the pickup point
    G = ox.graph_from_point((pickup_lat, pickup_lon), dist=5000, network_type='drive')

    # Find the nearest nodes in the graph to the pickup and dropoff locations
    pickup_node = ox.distance.nearest_nodes(G, X=pickup_lon, Y=pickup_lat)
    dropoff_node = ox.distance.nearest_nodes(G, X=dropoff_lon, Y=dropoff_lat)

    # Calculate the shortest path distance in meters
    route_length = nx.shortest_path_length(G, pickup_node, dropoff_node, weight='length')
    distance_km = route_length / 1000  # Convert meters to kilometers

    return distance_km

# Campus Map (UM Map)
def campus_map():
    st.title("University of Malaya Campus Map")
    
    # Embed the campus map using iframe if available
    iframe_code = '''
    <iframe src="https://www.google.com/maps/embed?pb=!1m14!1m8!1m3!1d3983.897036290883!2d101.656994!3d3.121927!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x31cdb47024217187%3A0x1e85ebc65d47d641!2sUniversity%20of%20Malaya!5e0!3m2!1sen!2smy!4v1732729152662!5m2!1sen!2smy" width="800" height="600" frameborder="0" style="border:0" allowfullscreen></iframe>
    '''
    st.components.v1.html(iframe_code, height=600)

def get_random_coordinates():
    lat_range = (3.0, 3.5)
    lon_range = (101.5, 102.0)
    return (random.uniform(*lat_range), random.uniform(*lon_range))




def book_ride_api(token, pickup_location, destination, pickup_time, passengers):
    url = f"{BASE_URL}/book_ride/"
    payload = {
        "pickup_location": pickup_location,
        "destination": destination,
        "pickup_time": pickup_time.isoformat(),  # Convert datetime to ISO format
        "passengers": passengers
    }
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(url, json=payload, headers=headers)
    return response.json()



# Booking Interface (SAPU)
def booking():
    st.title("Book Your Ride")
    pickup = st.text_input("Enter Pickup Location")
    dropoff = st.text_input("Enter Dropoff Location")
    date = st.date_input("Select Date")
    ride_time = st.time_input("Select Time", value=None)  # Renamed to avoid conflict
    passengers = st.number_input("No. of passenger(s)", min_value=1, step=1)

    # Create a map for displaying pickup and dropoff locations
    map_center = [3.1192, 101.6538]  # Default to UM (you can update based on actual location)
    m = folium.Map(location=map_center, zoom_start=12)

    pickup_lat,pickup_lon = None,None
    dropoff_lat,dropoff_lon = None,None

     # If a pickup location is entered, geocode it and update the map
    if pickup:
        pickup_lat, pickup_lon = get_coordinates(pickup)
        if pickup_lat and pickup_lon:
            folium.Marker([pickup_lat, pickup_lon], popup=f"Pickup: {pickup}", icon=folium.Icon(color='green')).add_to(m)
        else:
            st.error("Pickup location not found. Please enter a valid address.")
            pickup_lat,pickup_lon = get_random_coordinates()

    # If a dropoff location is entered, geocode it and update the map
    if dropoff:
        dropoff_lat, dropoff_lon = get_coordinates(dropoff)
        if dropoff_lat and dropoff_lon:
            folium.Marker([dropoff_lat, dropoff_lon], popup=f"Dropoff: {dropoff}", icon=folium.Icon(color='red')).add_to(m)
        else:
            st.error("Dropoff location not found. Please enter a valid address.")
            dropoff_lat,dropoff_lon = get_random_coordinates()

    m.location = [pickup_lat if pickup_lat else map_center[0], pickup_lon if pickup_lon else map_center[1]]
    st_folium(m, width=700, height=500)


    if st.button("Confirm Booking"):
        if pickup and dropoff and date and ride_time and passengers:
            # Calculate driving distance and price
            distance_km = calculate_driving_distance(pickup,dropoff)
            base_price = 5  # Base fee in dollars
            price_per_km = 1  # Price per kilometer
            total_price = base_price + (price_per_km * distance_km)
            st.write(f"The total distance is: {distance_km:.2f} km")

            new_booking = {
                'pickup_location': pickup,
                'destination': dropoff,
                'pickup_time': str(ride_time),
                'distance_km': round(distance_km,2),
                'price': round(total_price,2),
                'status': 'Pending'
                
            }
            st.session_state.bookings.append(new_booking)
            st.success(f"Booking confirmed! Total price: ${total_price:.2f}. Waiting for driver...")
        else:
            st.error("Please fill in all sections.")


def display_timetable (route):
    if route in BUS_ROUTES:
        schedule = BUS_ROUTES[route]["schedule"]
        st.write (f"Bus schedule for route {route}:")
        for time in schedule:
            st.write(f"- {time}")
    else :
        st.error("Invalid route.Please try again. ")

def display_live_location(route): 
    if route in BUS_ROUTES: 
        live_location = BUS_ROUTES[route]["live_location"]
        st.write(f"Live location of bus on route {route}:")
        st.write(f"Latitude: {live_location[0]}, Longitude: {live_location[1]}")
        # Create a map with the live location
        m = folium.Map(location=live_location, zoom_start=15)
        folium.Marker(live_location, popup=f"Bus on Route {route}").add_to(m)
        st_folium(m, width=700, height=500)
    else:
        st.error("Invalid route. Please try again.")


def bus() :
    st.title("Bus Information")

    # Display available bus routes
    st.write("Available Bus Routes:")
    for route in BUS_ROUTES.keys():
        st.write(f"- {route}")

    # User input for selecting a bus route
    route = st.selectbox("Select a bus route:", list(BUS_ROUTES.keys()))

    # Display the timetable for the selected route
    display_timetable(route)

    # Display the live location of the selected route
    display_live_location(route)
    
    
    
# Sidebar for driver registration
def driver_registration():
    st.title("Driver Registration")

    # Form inputs for driver registration
    driver_name = st.text_input("Enter your name:")
    license_number = st.text_input("Enter your license number:")
    vehicle_model = st.text_input("Enter your vehicle model:")
    vehicle_number = st.text_input("Enter your vehicle number:")
    contact_number = st.text_input("Enter your contact number:")
    

    # Register button
    register_button = st.button("Register as Driver")

    # Handle registration logic
    if register_button:
        if driver_name and license_number and vehicle_model and vehicle_number and contact_number :
            st.session_state.is_driver = True  # Mark the user as a driver
            st.success("Driver registered successfully!")
            
            

            st.write(f"Driver Name: {driver_name}")
            st.write(f"License Number: {license_number}")
            st.write(f"Vehicle Model: {vehicle_model}")
            st.write(f"Vehicle Number: {vehicle_number}")
            st.write(f"Contact Number: {contact_number}")
        else:
            st.error("Please fill all the fields!")

    # Show Driver's Only Interface
    if st.session_state.is_driver:
        st.title("Driver Dashboard")

        # Driver-only content
        st.write("Welcome to your dashboard, Driver!")
        st.write("Here you can manage your bookings, availability, and profile.")

        # Display pending bookings for the driver
        if st.session_state.bookings:
            for idx, booking in enumerate(st.session_state.bookings):
                st.write(f"Booking #{idx + 1}:")
                st.write(f"Pickup: {booking['pickup_location']}")
                st.write(f"Destination: {booking['destination']}")
                st.write(f"Price: ${booking['price']}")
                st.write(f"Pick-up Time: {booking['pickup_time']}")
                
                # Action buttons for accepting or rejecting bookings
                accept_button = st.button(f"Accept Booking #{idx + 1}")
                reject_button = st.button(f"Reject Booking #{idx + 1}")

                # Handle booking actions
                if accept_button:
                    st.session_state.bookings[idx]['status'] = 'Accepted'
                    st.success(f"You accepted booking #{idx + 1}")
                if reject_button:
                    st.session_state.bookings[idx]['status'] = 'Rejected'
                    st.warning(f"You rejected booking #{idx + 1}")

                # Display the updated booking status
                st.write(f"Status: {booking['status']}")

        else:
            st.write("No pending bookings available.")

    else:
        # Non-driver view (e.g., user hasn't registered yet)
        st.title("Welcome to the App")
        st.write("Please register as a driver to access the driver dashboard.")


# Main function for Streamlit navigation
def main():
    # Sidebar for navigation
    with st.sidebar :
            page = option_menu(
                menu_title='SAPU',
                options= ['Home', 'Booking', 'Bus', 'Campus Map','Driver Registration'],
                icons = ['house-fill','car-front-fill','bus-front-fill','map-fill','person-raised-hand'],
                default_index=1 ,
                styles={
                    "container": {"padding": "5!important","background-color": 'white'}, 
                "nav-link": {"color": "grey","font-size": "20px", "text-align": "left", "margin": "0px"},
                "nav-link-selected": {"background-color": "#230de0"}}
            )


    if page == "Home":
        home()
    elif page == "Booking":
        booking()
    elif page == "Bus":
        bus()
    elif page == "Campus Map":
        campus_map()
    elif page == "Driver Registration":
        driver_registration()

if __name__ == "__main__":
    main()

