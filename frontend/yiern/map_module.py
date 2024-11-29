import streamlit as st 
import random

def app() :
    
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
