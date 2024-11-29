import streamlit as st 
def app() :
    st.write('register as a driver')
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