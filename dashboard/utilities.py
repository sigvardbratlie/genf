import streamlit as st
from google.oauth2 import service_account
from google.cloud import bigquery
from datetime import datetime,timedelta
import calendar
import pandas as pd
from google.api_core.exceptions import NotFound
from supabase import create_client, Client
from datetime import date, datetime, timedelta
from typing import Optional,Any, List, Dict
import logging

import supabase

logger = logging.getLogger(__name__)
start_date  = "2025-08-01"
end_date    = datetime.today().date().isoformat()

def init_gcp_client():
    credentials = service_account.Credentials.from_service_account_info(
        st.secrets["gcp_service_account"]
    )
    client = bigquery.Client(credentials=credentials)
    return client

def init():
    st.session_state.setdefault("gcp_client", init_gcp_client())
    st.session_state.setdefault("supabase_client", create_client(st.secrets["supabase"].get("SUPABASE_URL"), st.secrets["supabase"].get("SUPABASE_ANON_KEY")))
    st.session_state.setdefault("supabase_api_key", st.secrets["supabase"].get("API_KEY"))
    st.session_state.setdefault("dates", (None, None))
    st.session_state.setdefault("role", ["GEN-F", "Hjelpementor", "Mentor"])
    st.session_state.setdefault("season", "25/26")

@st.cache_data(ttl=3600,show_spinner=False)
def run_query(query,spinner_message="Running query..."):
    query_job = st.session_state.gcp_client.query(query)
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
        st.page_link("pages/buk_cash.py", label="Buk.cash", icon="💰")
        st.page_link("pages/work_types.py", label="Jobb typer", icon="🛠️")

        #season_picker(disable_seasonpicker=disable_seasonpicker)
        custom_dates_picker(disable_datepicker=disable_custom_datepicker)
        date_picker(disable_datepicker=disable_datepicker)
        role_picker(disable_rolepicker=disable_rolepicker)
        
        clear = st.button("Clear Filters")
        if clear:
            st.session_state.clear()
            st.rerun()

def load_all_seasons():
    with st.spinner("Laster data..."):
        df_raw = run_query("""SELECT s.* EXCEPT(comments,date_of_birth), bc.id AS worker_id 
                        FROM registrations.season_22_25 s 
                        LEFT JOIN members.buk_cash bc ON bc.email = s.email""")
        bc_m = fetch_profiles()
        df_bc = fetch_job_logs()

    df_raw = map_roles(df_raw)
    bc_m["role"] = bc_m["date_of_birth"].apply(lambda x: apply_role(x))
    df_bc = pd.merge(df_bc, bc_m.loc[:,['id','email',"bank_account_number","role"]], left_on='worker_id', right_on='id', how='left')
    df_bc["cost"] = df_bc["hours_worked"] * df_bc["hourly_rate"]
    df_bc["worker_name"] = df_bc["worker_first_name"] + " " + df_bc["worker_last_name"]
    df_bc["season"] = "25/26"
    df_bc = df_bc.loc[:,["worker_id","cost","hours_worked","worker_name","date_completed","work_type","email","bank_account_number","role","season"]].copy()
    if "number_of_units" in df_bc.columns:
        df_bc["cost"] = df_bc.loc[(df_bc["work_type"] == "glenne_vedpakking") & (df_bc["role"] == "genf"), "number_of_units"] * 15
    else:
        st.warning("number_of_units column not found in data from buk.cash")
    df = pd.concat([df_raw, df_bc])
    df["gruppe"] = df["work_type"].apply(lambda x: x.split("_")[0] if x and "_" in x  else x)
    df["prosjekt"] = df["work_type"].apply(lambda x: " ".join(x.split("_")[1:]) if x and "_" in x and len(x.split("_")) > 1 else x)
    df["date_completed"] = pd.to_datetime(df["date_completed"], errors='coerce', utc=True)
    return df

def load_active_users(threshold = 1000):
    query =  f'''SELECT s.person_id,r.email 
            FROM `genf-446213.registrations.season_22_25` r
            JOIN members.specs s ON s.email = r.email
            GROUP BY r.email, s.person_id
            HAVING SUM(cost)>{threshold};'''
    df = run_query(query)
    return df

def map_roles(df):
    map_role = {"GEN-F":"genf","Hjelpementor":"hjelpementor","Mentor":"mentor"}
    roles = [map_role[role] for role in st.session_state.role if role in map_role]
    return df.loc[df["role"].isin(roles),:].copy()


def load_members(season):
    df = run_query("""SELECT * FROM members.members""")
    df["role"] = df["birthdate"].apply(lambda x: apply_role(x, season=season))
    return df.loc[df["role"].isin(["genf","hjelpementor",]), :].copy()



@st.cache_data(ttl=600,show_spinner=False)
def fetch_job_logs(
    from_date: Optional[date] = None,
    to_date: Optional[date] = None
) -> list[dict]:
    """
    Fetch job logs using API key with optional date filtering.
    
    Args:
        from_date: Optional start date (inclusive)
        to_date: Optional end date (inclusive)
    
    Returns:
        List of job log records
    """
    # Prepare parameters for the RPC call
    # Only include date parameters if they are provided (not None)
    if from_date is None or to_date is None:
        #st.write(st.session_state.dates)
        try:
            from_date = st.session_state.dates[0] if isinstance(st.session_state.dates[0], date) else datetime(st.session_state.dates[0]) 
            to_date = st.session_state.dates[1] if isinstance(st.session_state.dates[1], date) else datetime(st.session_state.dates[1])
        except:
            st.warning("Invalid dates in session state, defaulting to no date filter.")
            from_date = None
            to_date = None

    params = {"p_api_key": st.session_state.supabase_api_key}
    params["p_from_date"] = from_date.isoformat()
    params["p_to_date"] = to_date.isoformat()
    
    try:
        # Call the RPC function
        response = st.session_state.supabase_client.rpc("get_job_logs_with_api_key", params).execute()
        data = response.data
        
        if data is None:
            return pd.DataFrame()
        
        return pd.DataFrame(data)
    
    except Exception as e:
        logger.error(f"Error fetching job logs: {e}")
        if hasattr(e, 'message'):
            print(f"Error message: {e.message}")
        raise

@st.cache_data(ttl=600,show_spinner=False)
def fetch_profiles() -> list[dict[str, Any]]:
    """
    Fetch all user profiles for the organization.
    
    API Function: get_profiles_with_api_key(p_api_key text)
    
    Returns:
        List of profile dictionaries with the following fields:
        - id (uuid): User's unique identifier
        - first_name (text): User's first name
        - last_name (text): User's last name
        - phone (text): User's phone number
        - role (user_role): User's role ('admin' or 'member')
        - availability_notes (text): Notes about user availability
        - created_at (timestamp): Account creation timestamp
        - updated_at (timestamp): Last update timestamp
        - organization_id (uuid): Organization identifier
        - monthly_goal (integer): Monthly work hour goal
        - date_of_birth (date): User's date of birth
        - age_category (text): Calculated age category ('U16', 'U18', 'O18')
        - bank_account_number (text): User's bank account number
        - custom_id (integer): External system identifier (e.g., legacy person_id)
        - email (text): User's email address from auth.users
    
    Example:
        profiles = fetch_profiles(supabase, api_key)
        for profile in profiles:
            print(f"{profile['first_name']} {profile['last_name']} - Email: {profile.get('email')} - Custom ID: {profile.get('custom_id')}")
    """
    try:
        response = st.session_state.supabase_client.rpc("get_profiles_with_api_key", {
            "p_api_key": st.session_state.supabase_api_key
        }).execute()
        df = pd.DataFrame(response.data) if response.data else pd.DataFrame()
        return df
    except Exception as e:
        print(f"Error fetching profiles: {e}")
        raise

@st.cache_data(ttl=600,show_spinner=False)
def fetch_work_requests(
    from_date: Optional[date] = None,
    to_date: Optional[date] = None
) -> List[Dict[str, Any]]:
    """
    Fetch work requests (jobs) for the organization with optional date filtering.
    
    API Function: get_work_requests_with_api_key(
        p_api_key text,
        p_from_date date DEFAULT NULL,
        p_to_date date DEFAULT NULL
    )
    
    Args:
        from_date: Optional start date (filters by created_at, inclusive)
        to_date: Optional end date (filters by created_at, inclusive)
    
    Returns:
        List of work request dictionaries
    
    Example:
        # Get all work requests
        requests = fetch_work_requests(supabase, api_key)
        
        # Get work requests from last month
        from_date = date.today() - timedelta(days=30)
        requests = fetch_work_requests(supabase, api_key, from_date=from_date)
    """
    try:
        params = {"p_api_key": st.session_state.supabase_api_key}
        
        if from_date is not None:
            params["p_from_date"] = from_date.isoformat()
        if to_date is not None:
            params["p_to_date"] = to_date.isoformat()
        
        response = st.session_state.supabase_client.rpc("get_work_requests_with_api_key", params).execute()
        
        return response.data if response.data else []
    except Exception as e:
        print(f"Error fetching work requests: {e}")
        raise

@st.cache_data(ttl=600,show_spinner=False)
def fetch_job_applications(
    work_request_id: str
) -> List[Dict[str, Any]]:
    """
    Fetch job applications for a specific work request.
    
    API Function: get_job_applications_with_api_key(
        p_api_key text,
        p_work_request_id uuid
    )
    
    Args:
        work_request_id: UUID of the work request
    
    Returns:
        List of job application dictionaries with fields:
        - id (uuid): Application unique identifier
        - work_request_id (uuid): Work request ID
        - user_id (uuid): ID of user who applied
        - created_at (timestamp): Application timestamp
        - user_first_name (text): Applicant's first name
        - user_last_name (text): Applicant's last name
        - user_email (text): Applicant's email address
    
    Example:
        applications = fetch_job_applications("work-request-uuid-here")
        for app in applications:
            print(f"{app['user_first_name']} {app['user_last_name']} applied")
    """
    try:
        response = st.session_state.supabase_client.rpc("get_job_applications_with_api_key", {
            "p_api_key": st.session_state.supabase_api_key,
            "p_work_request_id": work_request_id
        }).execute()
        
        return response.data if response.data else []
    except Exception as e:
        print(f"Error fetching job applications: {e}")
        raise




def apply_role(date_of_birth : datetime, season : str = None) -> str:
    if isinstance(date_of_birth, str):
        try:
            date_of_birth = datetime.fromisoformat(date_of_birth)
        except Exception as e:
            st.warning(f"Invalid date_of_birth format: {date_of_birth}. Error: {e}")
            return 
    if not isinstance(date_of_birth, datetime):
        logger.error(f"date_of_birth is not a datetime object: {date_of_birth}")
        return
        
    if not season:
        season_year, season_month = datetime.now().year, datetime.now().month
    else:
        years = season.split("/")
        season_year = int("20" + years[0])
        season_month = 8  # August


    if season_month < 8:
        if season_year - date_of_birth.year  <= 16:
            return "genf"
        elif season_year - date_of_birth.year  <= 18:
            return "hjelpementor"
        else:
            return "mentor"
    else:
        if season_year - date_of_birth.year  < 16:
            return "genf"
        elif season_year - date_of_birth.year  < 18:
            return "hjelpementor"
        else:
            return "mentor"