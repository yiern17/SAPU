import streamlit as st
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
import random
from streamlit_option_menu import option_menu


# Initialize session state for bookings and driver status
if 'is_driver' not in st.session_state:
    st.session_state.is_driver = False

if 'bookings' not in st.session_state:
    st.session_state.bookings = []  # Initialize empty list for bookings

# Homepage
def home():
    st.title('Welcome to SAPU')
    st.subheader("Your transportation service app.")
    st.write("Choose a service from the menu on the left.")

def get_coordinates(address):
    geolocator = Nominatim(user_agent="saputracker")
    location = geolocator.geocode(address)
    if location:
        return location.latitude, location.longitude
    else:
        return None, None

# Campus Map (UM Map)
def campus_map():
    st.title("University of Malaya Campus Map")
    
    # Embed the campus map using iframe if available
    iframe_code = '''
    <iframe src="https://www.um.edu.my/campus-map" width="800" height="600" frameborder="0" style="border:0" allowfullscreen></iframe>
    '''
    st.components.v1.html(iframe_code, height=600)

def get_random_coordinates():
    lat_range = (3.0, 3.5)
    lon_range = (101.5, 102.0)
    return (random.uniform(*lat_range), random.uniform(*lon_range))

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
            # Add booking to session state
            new_booking = {
                'pickup_location': pickup,
                'destination': dropoff,
                'pickup_time': str(ride_time),
                'price': 20 * passengers,  # Example price logic based on passengers
                'status': 'Pending'
            }
            st.session_state.bookings.append(new_booking)
            st.success(f"Booking confirmed! Waiting for driver...")
        else:
            st.error("Please fill in all sections.")

# Real-Time Tracking
def tracking():
    st.title("Real-Time Tracking")
    status = st.radio("Vehicle Status", ["In Progress", "Arrived", "On the Way"])
    eta = st.text_input("Estimated Time of Arrival", "15 minutes")
    location = st.text_input("Vehicle Location", "Latitude: 37.7749, Longitude: -122.4194")

    # Create a map for real-time tracking
    map_center = [37.7749, -122.4194]  # Default to San Francisco
    m = folium.Map(location=map_center, zoom_start=12)

    # Display the vehicle location on the map (this can be dynamically updated)
    vehicle_location = [37.7749, -122.4194]  # Example location, replace with actual data
    folium.Marker(vehicle_location, popup="Vehicle Location", icon=folium.Icon(color='blue')).add_to(m)
    
    st_folium(m, width=700, height=500)

    # Display the status, ETA, and vehicle location
    st.write(f"Status: {status}")
    st.write(f"ETA: {eta}")
    st.write(f"Location: {location}")

# Sidebar for driver registration
def driver_registration():
    st.title("Driver Registration")

    # Form inputs for driver registration
    driver_name = st.text_input("Enter your name:")
    license_number = st.text_input("Enter your license number:")
    vehicle_model = st.text_input("Enter your vehicle model:")
    vehicle_number = st.text_input("Enter your vehicle number:")
    contact_number = st.text_input("Enter your contact number:")
    uploaded_image = st.file_uploader("Upload your profile picture", type=["jpg", "jpeg", "png"])

    # Register button
    register_button = st.button("Register as Driver")

    # Handle registration logic
    if register_button:
        if driver_name and license_number and vehicle_model and vehicle_number and contact_number and uploaded_image:
            st.session_state.is_driver = True  # Mark the user as a driver
            st.success("Driver registered successfully!")
            
            # Display the uploaded image
            st.image(uploaded_image, caption="Profile Picture", use_container_width=True)

            st.write(f"Driver Name: {driver_name}")
            st.write(f"License Number: {license_number}")
            st.write(f"Vehicle Model: {vehicle_model}")
            st.write(f"Vehicle Number: {vehicle_number}")
            st.write(f"Contact Number: {contact_number}")
        else:
            st.error("Please fill all the fields and upload a picture!")

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
                options= ['Home', 'Booking', 'Real-Time Tracking', 'Campus Map','Driver Registration'],
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
    elif page == "Real-Time Tracking":
        tracking()
    elif page == "Campus Map":
        campus_map()
    elif page == "Driver Registration":
        driver_registration()

if __name__ == "__main__":
    main()

