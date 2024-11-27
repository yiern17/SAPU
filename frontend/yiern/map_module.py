import streamlit as st
import pandas as pd
import requests

# Sample data with latitude and longitude for University of Malaya locations
static_data = {
    'lat': [3.1201, 3.1340, 2.9210],
    'lon': [101.6544, 101.6865, 101.6967],
    'name': ['Faculty of Computer Science and Information System', 'KL Central', 'Terminal Bersepadu Selatan']
}

# Function to fetch live locations from the backend API
def fetch_live_locations():
    # Replace with the actual API endpoint
    api_url = "https://your-backend-api.com/live-locations"
    try:
        response = requests.get(api_url)
        response.raise_for_status()  # Raise an exception for HTTP errors
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching live locations: {e}")
        return []
    except ValueError as e:
        st.error(f"Error decoding JSON: {e}")
        return []

# Function to display the map
def display_map():
    st.title("Map with Specific Locations at University of Malaya")

    # Display static map
    st.subheader("Static Locations")
    static_df = pd.DataFrame(static_data)
    st.map(static_df)

    # Display live locations
    st.subheader("Live Locations of Buses and SAPU")
    live_locations = fetch_live_locations()

    if not live_locations:
        st.write("No live locations available.")
    else:
        live_df = pd.DataFrame(live_locations)
        st.map(live_df)
