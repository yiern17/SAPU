import streamlit as st

# Function to handle login
def login():
    st.session_state.logged_in = True
    st.success("Logged in successfully!")

# Function to handle sign-up
def sign_up():
    st.session_state.signed_up = True
    st.success("Signed up successfully!")

# Function to display the login page
def display_login_page():
    st.title("Login Page")

    # Initialize session state variables
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'signed_up' not in st.session_state:
        st.session_state.signed_up = False

    # Login form
    with st.form(key='login_form'):
        email = st.text_input("Email:")
        password = st.text_input("Password:", type='password')
        login_button = st.form_submit_button("Login")
        sign_up_button = st.form_submit_button("Sign Up")

    # Handle login and sign-up buttons
    if login_button:
        login()
    if sign_up_button:
        sign_up()

    # Display content based on login/sign-up status
    if st.session_state.logged_in:
        st.write("Welcome! You are logged in.")
    if st.session_state.signed_up:
        st.write("Welcome! You have signed up.")