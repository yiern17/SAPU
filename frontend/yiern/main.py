import streamlit as st 
from streamlit_option_menu import option_menu
import login, home, booking, map_module, real_time, driver


st.set_page_config(
    page_title = "SAPU"
)

class MultiApp :
    def __ini__(self) :
        self.apps=[]
    def add_app(self,title,function) :
        self.apps.append({
            "title": title,
            "function": function
        })
    def run () :
        
        with st.sidebar :
            app = option_menu(
                menu_title='SAPU',
                options= ['Home', 'Account', 'Bus location', 'Campus map', 'Booking','Be a driver'],
                default_index=1 ,
                styles={
                    "container": {"padding": "5!important","background-color": 'white'}, 
                "nav-link": {"color": "grey","font-size": "20px", "text-align": "left", "margin": "0px"},
                "nav-link-selected": {"background-color": "#230de0"}}
            )
        if app=='Home' :
             home.app()
        if app=='Account' :
             login.app()
        if app=='Bus location' :
             real_time.app()
        if app=='Campus Map' :
             map_module.app()
        if app=='Booking' :
             booking.app()
        if app=='Be a driver' :
             driver.app()
    run()         
    