import sys
import os
import streamlit as st

# Add the project directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from frontend.yiern.map_module import display_map
from frontend.yiern.login import display_login_page

# Streamlit app
def main():
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox("Choose a page", ["Login", "Map"])

    if page == "Login":
        display_login_page()
    elif page == "Map":
        display_map()

if __name__ == "__main__":
    main()