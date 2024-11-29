import streamlit as st 
import folium
from streamlit_folium import st_folium
#from home import get_coordinates 
#from map_module import get_random_coordinates
def app() :
    
    st.title("Book Your Ride")
    pickup = st.text_input("Enter Pickup Location")
    dropoff = st.text_input("Enter Dropoff Location")
    date = st.date_input("Select Date")
    ride_time = st.time_input("Select Time", value=None)  # Renamed to avoid conflict
    passengers = st.number_input("No. of passenger(s)", min_value=1, step=1)

    # Create a map for displaying pickup and dropoff locations
    map_center = [3.1192, 101.6538]  # Default to UM (you can update based on actual location)
    m = folium.Map(location=map_center, zoom_start=12)

    