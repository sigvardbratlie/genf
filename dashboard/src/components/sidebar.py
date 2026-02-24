import streamlit as st
from datetime import datetime,timedelta
import calendar
import pandas as pd
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)



class SidebarComponent:
    def __init__(self):
        self.start_date = "2025-08-01"
        self.end_date = datetime.today().date().isoformat()

    def season_picker(self, default = 0,disable_seasonpicker = False):
        sesong = st.radio("Select Season", ["25/26","24/25","23/24","22/23"], index=default, disabled=disable_seasonpicker)
        if sesong:
            st.session_state.sesong = sesong
            if sesong == "25/26":
                start_date = "2025-08-01"
                end_date = datetime.today().date().isoformat()
                st.session_state.dates = (start_date, end_date)   
            else:
                years = sesong.split("/")
                start_date = f"20{years[0]}-08-01"
                end_date = f"20{years[1]}-06-30"
                st.session_state.dates = (start_date, end_date)
            

    def custom_dates_picker(self, disable_datepicker = False):
        with st.expander("Custom Date Range",expanded = True):
            choices = []
            for i in range(4):
                d = pd.Timestamp.today() - pd.DateOffset(months=i+1)
                choices.append(f"{calendar.month_name[d.month]} {d.year}")

            custom_date = st.radio("Velg forhåndsdefinert daterange", 
                                    options = choices , 
                                    index = None, 
                                    horizontal=True,
                                    disabled=disable_datepicker)
            if custom_date:
                month = list(calendar.month_name).index(custom_date.split(" ")[0])
                year = int(custom_date.split(" ")[1])
                first_day = datetime(year=year, month=month, day=1).date()
                last_day = datetime(year=year, month=month, day=calendar.monthrange(year, month)[1]).date()
                st.session_state.dates = (first_day, last_day)
            custom_season = st.radio("Eller velg sesong", 
                                    options = ["25/26","24/25","23/24","22/23"] , 
                                    index = None, 
                                    horizontal=True,
                                    disabled=disable_datepicker)
            if custom_season:
                st.session_state.season = custom_season
                if custom_season == "25/26":
                    start_date = "2025-08-01"
                    end_date = datetime.today().date().isoformat()
                    st.session_state.dates = (start_date, end_date)   
                else:
                    years = custom_season.split("/")
                    start_date = f"20{years[0]}-08-01"
                    end_date = f"20{years[1]}-06-30"
                    st.session_state.dates = (start_date, end_date)
                

    def date_picker(self, disable_datepicker = False):
        
        dates = st.date_input("Select Date Range",
                                    value=st.session_state.dates if isinstance(st.session_state.dates, tuple) and all(st.session_state.dates) else (self.start_date,self.end_date),
                                    min_value="2021-01-01",
                                    max_value=datetime.today().date()+timedelta(days=30),
                                    disabled=disable_datepicker
                                    )
        if len(dates) == 2 and dates[1]>=dates[0]:
                st.session_state.dates = dates
        else:
            if len(dates) != 2:
                st.error("Please select both start and end dates.")
            elif dates[1]<dates[0]:
                st.error("End date must be after start date.")
            else:
                st.error("Invalid date selection.")
    
    def role_picker(self, disable_rolepicker = False):
        role_map = {"GEN-F":"genf","Hjelpementor":"hjelpementor","Mentor":"mentor"}
        role = st.pills("Select Role", options = ["GEN-F", "Hjelpementor", "Mentor"], 
                            default = ["GEN-F", "Hjelpementor", "Mentor"], 
                            selection_mode = "multi",
                            disabled=disable_rolepicker)
        if role:
            st.session_state.role = [role_map[r] if r in role_map else r for r in role]


    def sidebar_setup(self, disable_datepicker = False,disable_rolepicker = False,disable_custom_datepicker = False,):
        with st.sidebar:
            st.page_link(page="main.py", label="🏠 Home")
            st.page_link("pages/timer.py", label = "Timer", icon="⏰")
            st.page_link("pages/review.py", label = "Review", icon="📊")
            st.page_link("pages/buk_cash.py", label="Buk.cash", icon="💰")

            #season_picker(disable_seasonpicker=disable_seasonpicker)
            self.custom_dates_picker(disable_datepicker=disable_custom_datepicker)
            self.date_picker(disable_datepicker=disable_datepicker)
            self.role_picker(disable_rolepicker=disable_rolepicker)
            
            clear = st.button("Clear Filters")
            if clear:
                st.session_state.clear()
                st.rerun()

