import streamlit as st
from google.oauth2 import service_account
from google.cloud import bigquery
from datetime import datetime,timedelta
import calendar
import pandas as pd

start_date  = "2025-01-01"
end_date    = datetime.today().date().isoformat()

def init_client():
    credentials = service_account.Credentials.from_service_account_info(
        st.secrets["gcp_service_account"]
    )
    client = bigquery.Client(credentials=credentials)
    return client

def init():
    st.session_state.setdefault("client", init_client())
    st.session_state.setdefault("dates", (None, None))
    st.session_state.setdefault("role", ["GEN-F", "Hjelpementor", "Mentor"])
    st.session_state.setdefault("sesong", "25/26")
    

@st.cache_data(ttl=1200)
def run_query(query):
    query_job = st.session_state.client.query(query)
    df = query_job.result().to_dataframe()
    return df

def season_picker(default = 1,disable_seasonpicker = False):
    sesong = st.radio("Select Season", ["24/25" , "25/26"], index=default, disabled=disable_seasonpicker)
    if sesong:
        st.session_state.sesong = sesong
        if sesong == "24/25":
            start_date = "2024-08-01"
            end_date = "2025-06-30"
            st.session_state.dates = (start_date, end_date)
        elif sesong == "25/26":
            start_date = "2025-08-01"
            end_date = datetime.today().date().isoformat()
            st.session_state.dates = (start_date, end_date)

def custom_dates_picker(disable_datepicker = False):
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
def date_picker(disable_datepicker = False):
    dates = st.date_input("Select Date Range",
                                value=st.session_state.dates if isinstance(st.session_state.dates, tuple) and all(st.session_state.dates) else (start_date, end_date),
                                min_value="2021-01-01",
                                max_value=datetime.today().date(),
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
def role_picker(disable_rolepicker = False):
    role = st.pills("Select Role", options = ["GEN-F", "Hjelpementor", "Mentor"], 
                        default = ["GEN-F", "Hjelpementor", "Mentor"], 
                        selection_mode = "multi",
                        disabled=disable_rolepicker)
    if role:
        st.session_state.role = role


def sidebar_setup(disable_datepicker = False,disable_rolepicker = False,disable_seasonpicker = False):
    with st.sidebar:
        st.page_link(page="main.py", label="🏠 Home")
        st.page_link("pages/timer.py", label = "Timer", icon="⏰")
        st.page_link("pages/camp_status.py", label = "Camp Status", icon="🏕️")

        season_picker(disable_seasonpicker=disable_seasonpicker)
        custom_dates_picker(disable_datepicker=disable_datepicker)
        date_picker(disable_datepicker=disable_datepicker)
        role_picker(disable_rolepicker=disable_rolepicker)
        
        clear = st.button("Clear Filters")
        if clear:
            st.session_state.clear()
            st.rerun()


def ensure_login():
    if not st.user or not st.user.is_logged_in:
        st.warning("Please log in to access the dashboard.")
        if st.button("Log in"):
            st.login()
    else:
        if st.button("Log out"):
            st.logout()
            st.rerun()