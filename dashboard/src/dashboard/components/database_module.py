import streamlit as st
from google.oauth2 import service_account
from google.cloud import bigquery
from datetime import datetime
import calendar
import pandas as pd
from supabase import create_client
from datetime import date, datetime
from typing import Optional,Any, List, Dict
import logging
from abc import ABC, abstractmethod


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseModule(ABC):
    def __init__(self):
        self.start_date  = "2025-08-01"
        self.end_date    = datetime.today().date().isoformat()

    @abstractmethod
    def run_query(self, query: str) -> pd.DataFrame:
        pass

    def map_roles(self, df):
        map_role = {"GEN-F":"genf","Hjelpementor":"hjelpementor","Mentor":"mentor"}
        roles = [map_role[role] for role in st.session_state.role if role in map_role]
        return df.loc[df["role"].isin(roles),:].copy()

    def apply_role(self, date_of_birth : datetime, season : str = None) -> str:
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

    def mk_gruppe_prosjekt(self, df_raw):
        prosjekt_col = df_raw["work_type"].apply(lambda x: " ".join(x.split("_")[1:]) if "_" in x and len(x.split("_")) > 1 else x)
        gruppe_col = df_raw["work_type"].apply(lambda x: x.split("_")[0] if "_" in x else x)
        df_raw["gruppe"] = gruppe_col
        df_raw["prosjekt"] = prosjekt_col
        return df_raw.drop(columns=["work_type"],) 


class BigQueryModule(DatabaseModule):
    def __init__(self, ):
        super().__init__()
        self.client = self._init_gcp_client()

    def _init_gcp_client(self):
        credentials = service_account.Credentials.from_service_account_info(
            st.secrets["gcp_service_account"]
        )
        client = bigquery.Client(credentials=credentials)
        return client
    
    @st.cache_data(ttl=3600,show_spinner=False)
    def run_query(_self, query: str) -> pd.DataFrame:
        query_job = _self.client.query(query)
        df = query_job.result().to_dataframe()
        return df
    
    def load_registrations(self):
        query = """SELECT * FROM registrations.season_22_25"""
        return self.run_query(query)
    
    def load_active_users(self, threshold = 1000):
        query =  f'''SELECT s.person_id,r.email 
            FROM `genf-446213.registrations.season_22_25` r
            JOIN members.specs s ON s.email = r.email
            GROUP BY r.email, s.person_id
            HAVING SUM(cost)>{threshold};'''
        return self.run_query(query)
    
    def load_members(self, season):
        df = self.run_query("""SELECT * FROM members.members""")
        df["role"] = df["birthdate"].apply(lambda x: self.apply_role(x, season=season))
        if not df.empty:
            return df
        #return df.loc[df["role"].isin(["genf","hjelpementor",]), :].copy()


class SupabaseModule(DatabaseModule):
    def __init__(self):
        super().__init__()
        self.supabase_url = st.secrets["supabase"].get("genf").get("SUPABASE_URL")
        self.supabase_api_key = st.secrets["supabase"].get("genf").get("SUPABASE_ANON_KEY")
        self.supabase = create_client(self.supabase_url, self.supabase_api_key)

    @st.cache_data(ttl=3600,show_spinner=False)
    def run_query(_self, table_name: str, cols : list = []) -> pd.DataFrame:
        select_cols = ", ".join(cols) if cols else "*"
        response = _self.supabase.table(table_name).select(select_cols).execute()
        data = response.data
        if data is None:
            return pd.DataFrame()
        return pd.DataFrame(data)
    
    def load_bcc_members(self):
        return self.run_query("buk_cash_members")
    
    def load_users(self):
        return self.run_query("buk_cash")
    
    def load_registrations(self):
        return self.run_query("registrations")
    
#IMPLE;ENT! 
prices = run_query("SELECT * FROM admin.rates")
camp_prices = run_query("SELECT * FROM admin.camp_prices")

def get_camp_price_season(df ,sesong : str,u18: bool = True):
    if u18:
        prefix = "u"
    else:
        prefix = "o"
    years = sesong.split("/")
    year1 = int("20" + years[0])
    year2 = int("20" + years[1])
    y1_price =  camp_prices.loc[df['year'] == year1, f"{prefix}18_nc"].sum()
    y2_price =  df.loc[df['year'] == year2, [f"{prefix}18_pc",f"{prefix}18_sc"]].sum().sum()
    price = y1_price + y2_price
    return price
prices["camp_u18"] = prices['sesong'].apply(lambda x: get_camp_price_season(df=camp_prices, sesong=x, u18=True))
prices["camp_o18"] = prices['sesong'].apply(lambda x: get_camp_price_season(df=camp_prices, sesong=x, u18=False))



class SupaBaseApi(DatabaseModule):
    def __init__(self):
        super().__init__()
        self.supabase_url = st.secrets["supabase"].get("buk_cash").get("SUPABASE_URL")
        self.supabase_key = st.secrets["supabase"].get("buk_cash").get("SUPABASE_ANON_KEY")
        self.supabase_api_key = st.secrets["supabase"].get("buk_cash").get("API_KEY")
        self.supabase = create_client(self.supabase_url, self.supabase_key)

    def run_query(self, query: str):
        pass
    
    @st.cache_data(ttl=600,show_spinner=False)
    def fetch_job_logs(_self,
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
                from_date = st.session_state.dates[0] if isinstance(st.session_state.dates[0], date) else _self.start_date
                to_date = st.session_state.dates[1] if isinstance(st.session_state.dates[1], date) else _self.end_date
            except:
                st.warning("Invalid dates in session state, defaulting to no date filter.")
                from_date = None
                to_date = None

        params = {"p_api_key": _self.supabase_api_key}
        params["p_from_date"] = from_date.isoformat()
        params["p_to_date"] = to_date.isoformat()
        
        try:
            # Call the RPC function
            response = _self.supabase.rpc("get_job_logs_with_api_key", params).execute()
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
    def fetch_profiles(_self) -> list[dict[str, Any]]:
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
            response = _self.supabase.rpc("get_profiles_with_api_key", {
                "p_api_key": _self.supabase_api_key
            }).execute()
            df = pd.DataFrame(response.data) if response.data else pd.DataFrame()
            return df
        except Exception as e:
            print(f"Error fetching profiles: {e}")
            raise

    @st.cache_data(ttl=600,show_spinner=False)
    def fetch_work_requests(_self,
        
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
            params = {"p_api_key": _self.supabase_api_key}
            
            if from_date is not None:
                params["p_from_date"] = from_date.isoformat()
            if to_date is not None:
                params["p_to_date"] = to_date.isoformat()
            
            response = _self.supabase.rpc("get_work_requests_with_api_key", params).execute()
            
            return response.data if response.data else []
        except Exception as e:
            print(f"Error fetching work requests: {e}")
            raise

    @st.cache_data(ttl=600,show_spinner=False)
    def fetch_job_applications(_self,
       
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
            response = _self.supabase.rpc("get_job_applications_with_api_key", {
                "p_api_key": _self.supabase_api_key,
                "p_work_request_id": work_request_id
            }).execute()
            
            return response.data if response.data else []
        except Exception as e:
            print(f"Error fetching job applications: {e}")
            raise


@st.cache_resource(ttl=3600, show_spinner=False)
def get_supabase_api():
    return SupaBaseApi()

@st.cache_resource(ttl=3600, show_spinner=False)
def get_bigquery_module():
    return BigQueryModule()

@st.cache_resource(ttl=3600, show_spinner=False)
def get_supabase_module():
    return SupabaseModule()

# def load_all_seasons():
#     with st.spinner("Laster data..."):
#         df_raw = run_query("""SELECT s.* EXCEPT(comments,date_of_birth), bc.id AS worker_id 
#                         FROM registrations.season_22_25 s 
#                         LEFT JOIN members.buk_cash bc ON bc.email = s.email""")
#         bc_m = fetch_profiles()
#         df_bc = fetch_job_logs("2026-01-01")


#     #st.dataframe(df_bc)
#     df_raw = map_roles(df_raw)
#     bc_m["role"] = bc_m["date_of_birth"].apply(lambda x: apply_role(x))
#     df_bc = pd.merge(df_bc, bc_m.loc[:,['id','email',"bank_account_number","role"]], left_on='worker_id', right_on='id', how='left')
#     #df_bc["cost"] = df_bc["hours_worked"] * df_bc["hourly_rate"]
#     if "units_completed" in df_bc.columns:
#         df_bc["cost"] = df_bc.loc[(df_bc["work_type"] == "glenne_vedpakking") & (df_bc["role"] == "genf"), "units_completed"] * 15
#         df_bc["cost"] = df_bc["cost"].fillna(df_bc["hours_worked"] * df_bc["hourly_rate"])
#     else:
#         st.warning("units_completed column not found in data from buk.cash")
#         df_bc["cost"] = df_bc["hours_worked"] * df_bc["hourly_rate"]
#     df_bc["worker_name"] = df_bc["worker_first_name"] + " " + df_bc["worker_last_name"]
#     df_bc["season"] = "25/26"
#     to_keep = ["worker_id","cost",
#                "hours_worked","worker_name","date_completed",
#                "work_type","email","bank_account_number",
#                "role","season","units_completed","hourly_rate",
#                "comments",
#                ]
#     df_bc = df_bc.loc[:,to_keep].copy()
#     df = pd.concat([df_raw, df_bc])
#     df["gruppe"] = df["work_type"].apply(lambda x: x.split("_")[0] if x and "_" in x  else x)
#     df["prosjekt"] = df["work_type"].apply(lambda x: " ".join(x.split("_")[1:]) if x and "_" in x and len(x.split("_")) > 1 else x)
#     df["date_completed"] = pd.to_datetime(df["date_completed"], errors='coerce', utc=True)
#     #st.dataframe(df)
#     return df

