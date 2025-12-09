import streamlit as st
from google.oauth2 import service_account
from google.cloud import bigquery
from datetime import datetime,timedelta
import calendar
import pandas as pd
from google.api_core.exceptions import NotFound

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
    st.session_state.setdefault("season", "25/26")
    

@st.cache_data(ttl=3600,show_spinner=False)
def run_query(query,spinner_message="Running query..."):
    query_job = st.session_state.client.query(query)
    #with st.spinner(spinner_message):
    df = query_job.result().to_dataframe()
    return df

def season_picker(default = 0,disable_seasonpicker = False):
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


def sidebar_setup(disable_datepicker = False,disable_rolepicker = False,disable_custom_datepicker = False,):
    with st.sidebar:
        st.page_link(page="main.py", label="🏠 Home")
        st.page_link("pages/timer.py", label = "Timer", icon="⏰")
        st.page_link("pages/seasonal_review.py", label = "Seasonal Review", icon="🏕️")
        st.page_link("pages/yearly_review.py", label = "Yearly Review", icon="📊")
        st.page_link("pages/members.py", label = "Medlemmer", icon="👥")

        #season_picker(disable_seasonpicker=disable_seasonpicker)
        custom_dates_picker(disable_datepicker=disable_custom_datepicker)
        date_picker(disable_datepicker=disable_datepicker)
        role_picker(disable_rolepicker=disable_rolepicker)
        
        clear = st.button("Clear Filters")
        if clear:
            st.session_state.clear()
            st.rerun()


def load_all_seasons():
    tables = ["sesong_22_23","sesong_23_24","sesong_24_25","sesong_25_26"]
    dfs = []

    progress_bar = st.progress(0)
    status_text = st.empty()

    for i, table in enumerate(tables):
        status_text.text(f"Loading {table}...")
        df = run_query(f"SELECT * FROM registrations.{table}",spinner_message=None)
        df["season"] = table.replace("sesong_","").replace("_","/")
        dfs.append(df)
        progress_bar.progress((i + 1) / len(tables))

    status_text.text("Done!")
    progress_bar.empty()
    status_text.empty()

    df = pd.concat(dfs, ignore_index=True)
    df['dato'] = pd.to_datetime(df['dato'], utc=True)
    df.sort_values(by="dato", inplace=True)
    return df

def map_roles(df):
    map_role = {"GEN-F":"genf","Hjelpementor":"hjelpementor","Mentor":"mentor"}
    roles = [map_role[role] for role in st.session_state.role if role in map_role]
    return df.loc[df["rolle"].isin(roles),:].copy()


def load_members(season):
    season_year = int("20" + season.split("/")[0])
    
    # if datetime.now().month >= 8:
    #     
    # else:
    #     first_year = datetime.now().year - 16
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    dfs = []
    if season_year >= 2025:
        first_year = season_year - 17
        tables = [first_year + i for i in range(0,5)]
    else:
        first_year = season_year - 15
        tables = [first_year + i for i in range(0,3)]
    for i, year in enumerate(tables):
        status_text.text(f"Loading members {year}...")
        try:
            df = run_query(f"SELECT * FROM members.{year}",)
            df["season"] = season
            if i < 2 and season_year >= 2025:
                df["role"] = "Hjelpementor"
            else:
                df["role"] = "GEN-F"
            dfs.append(df)
        except NotFound:
            st.warning(f"Members for year {year} not found in the database.")
        progress_bar.progress((i + 1) / len(tables))

    status_text.text("Done!")
    progress_bar.empty()
    status_text.empty()
    df = pd.concat(dfs, ignore_index=True)
    return df

def ensure_login():
    if not st.user or not st.user.is_logged_in:
        st.warning("Please log in to access the dashboard.")
        if st.button("Log in"):
            st.login()
    else:
        if st.button("Log out"):
            st.logout()
            st.rerun()