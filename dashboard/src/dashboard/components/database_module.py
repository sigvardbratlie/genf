import streamlit as st
from google.oauth2 import service_account
from google.cloud import bigquery
from datetime import datetime
import calendar
import pandas as pd
from supabase import create_client
from datetime import date, datetime,timedelta
from typing import Optional,Any, List, Dict,Tuple,Literal
import logging
from abc import ABC, abstractmethod


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseModule(ABC):
    def __init__(self):
        self.start_date  = datetime(2025, 8, 1).date()
        self.end_date    = datetime.today().date().isoformat()

    def get_current_season(self)-> str:
        year, month = datetime.now().year, datetime.now().month
        if month < 8:
            year = str(year).replace("20","")
            return f'{int(year)-1}/{year}'
        else:
            return f'{year}/{int(year)+1}'
        
    def parse_role(self, birth_year : int, season : str = None, ) -> str:
        if not season:
            logger.info("No season selected. Choosing current season as default")
            season = self.get_current_season()
        elif not isinstance(season,str): 
            logger.warning(f"Season {season} excepted to be type 'str', but are {type(season)}. Selecting current season as default")
            season = self.get_current_season()
        elif len(season.split("/")) != 2:
            logger.warning("Season expected to have format 'year1/year2. Selecting current season as default")
            season = self.get_current_season()
        
        year = int(f'20{season.split("/")[1]}')
        #print(f'YEAR: {year} with type {type(year)}, BIRTH_YEAR: {birth_year} with type {type(birth_year)}')
        diff = year - birth_year
        if diff <= 16 and diff >= 14:
            return "genf"
        elif diff <= 18 and diff >= 17:
            return "hjelpementor"
        elif diff < 14:
            return "u13"
        else:
            return "mentor"

    def apply_role(self, birth_date : str | date | datetime, season = None):
        # Check for None or NaN
        if birth_date is None or (isinstance(birth_date, float) and pd.isna(birth_date)):
            logger.warning("Birth date is missing. Cannot determine role.")
            return None
        
        if isinstance(birth_date, str):
            try:
                birth_date = datetime.strptime(birth_date, "%Y-%m-%d").date()
            except ValueError as e:
                logger.error(f"Error parsing birth_date string {birth_date}: {e}")
                return None
        
        try:
            birth_year = birth_date.year
            return self.parse_role(birth_year, season)
        except Exception as e:
            logger.error(f"Error applying role for birth_date {birth_date}: {e}")
            return None
 
    def filter_df_by_dates(self, df: pd.DataFrame, dates : tuple = (), date_col: str = "date_completed") -> pd.DataFrame:
        if date_col not in df.columns:
            logger.warning(f"Date column {date_col} not found in DataFrame. Skipping date filtering.")
            return df
        df["date_completed"] = pd.to_datetime(df["date_completed"], errors='coerce', utc=True)
        if not dates:
            st_start_date = st.session_state.get("dates", [None, None])[0]
            st_end_date = st.session_state.get("dates", [None, None])[1]
            if st_start_date:
                self.start_date = st_start_date
            if st_end_date:
                self.end_date = st_end_date
        else:
            self.start_date, self.end_date = dates

        #print("SELECTED DATES:", self.start_date, self.end_date)
        #st.info(f"Filtering data by selected dates: {self.start_date} to {self.end_date}")
        #st.info(f'MIN DATE IN DATA: {df[date_col].min()}, MAX DATE IN DATA: {df[date_col].max()}')
        
        try:
            df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
            filtered_df = df[
                (df[date_col].dt.date >= self.start_date) &
                (df[date_col].dt.date <= self.end_date)
            ].copy()
            return filtered_df
        except Exception as e:
            logger.error(f"Error filtering DataFrame by dates: {e}")
            return df
        
    def filter_work_type(self, df: pd.DataFrame, work_types : list = [], work_type_col: str = "work_type") -> pd.DataFrame:
        if work_type_col not in df.columns:
            logger.warning(f"Work type column {work_type_col} not found in DataFrame. Skipping work type filtering.")
            return df
        if not work_types:
            logger.info("No work types selected. Skipping work type filtering.")
            return df
        if work_types:
            filtered_df = df[df[work_type_col].isin(work_types)].copy()
            return filtered_df
        return df

    def apply_grouping(self,df : pd.DataFrame, every_sample : bool = False) -> pd.DataFrame:
        GROUPING_COLS = ["worker_name","email","bank_account_number","role"]
        AGG_COLS =  ["cost","hours_worked","units_completed"]
        ALL_COLS = ["worker_name","email","bank_account_number","role","prosjekt","gruppe","comments","cost","hours_worked","units_completed","date_completed",]
        MIN_COLS = ["worker_name","role","cost","hours_worked",]
        
        if not set(GROUPING_COLS + AGG_COLS).issubset(df.columns) and not every_sample:
            logger.warning(f"Missing some columns for grouping/aggregation: {set(GROUPING_COLS + AGG_COLS) - set(df.columns)}. Returning ungrouped DataFrame.")
            return df
        if not set(GROUPING_COLS).issubset(df.columns) and every_sample:
            logger.warning(f"Missing some columns for grouping: {set(GROUPING_COLS) - set(df.columns)}. Returning ungrouped DataFrame.")
            return df
        
        if not every_sample:
            dfg = df.groupby(GROUPING_COLS)[AGG_COLS].sum().reset_index()
        else:
            for col in ALL_COLS:
                if col not in df.columns:
                    ALL_COLS.pop(ALL_COLS.index(col))
            dfg = df[ALL_COLS].copy()
        
        return dfg

    def render_metrics(self, df, df_raw):
        REQ_COLS = ["cost","hours_worked","worker_name","date_completed"]
        if not set(REQ_COLS).issubset(df.columns):
            logger.warning(f"Missing required columns {set(REQ_COLS) - set(df.columns)} in DataFrame.")
            return
        delta_time = st.session_state.dates[1] - st.session_state.dates[0]
        delta_start = st.session_state.dates[0] - delta_time - timedelta(days=1)
        #st.info((delta_start, st.session_state.dates,delta_time))
        delta_df = df_raw.loc[
            (df_raw['date_completed'] >= pd.to_datetime(delta_start, utc=True)) &
            (df_raw['date_completed'] < pd.to_datetime(st.session_state.dates[0], utc=True))
            ].copy()
        cols = st.columns(3)
        cols[0].metric(label = "Total antall timer", value = f"{df['hours_worked'].sum():,.0f}", 
                    delta = f"{df['hours_worked'].sum() - delta_df['hours_worked'].sum():,.0f} fra forrige periode")
        cols[1].metric(label = "Totale kostnader", value = f"{df['cost'].sum():,.0f} NOK",
                    delta = f"{df['cost'].sum() - delta_df['cost'].sum():,.0f} NOK fra forrige periode")
        cols[2].metric(label = "Antall unike brukere", value = f"{df['worker_name'].nunique():,.0f}",
                    delta = f"{df['worker_name'].nunique() - delta_df['worker_name'].nunique():,.0f} fra forrige periode")

    @staticmethod
    def mk_gruppe(work_type : str):
        return work_type.split("_")[0] if "_" in work_type else work_type
    @staticmethod
    def mk_prosjekt(work_type : str):
        return " ".join(work_type.split("_")[1:]) if "_" in work_type and len(work_type.split("_")) > 1 else work_type
    
    
    def apply_cost(self,row : pd.Series, rates : list,) -> int:
        season = row["season"] if "season" in row else None
        for rate in rates:
            if rate["season"] == season:
                break

        if "role" not in row or pd.isna(row["role"]):
                raise ValueError(f"'role' is missing from row! row: {row.to_dict()}")
        if "work_type" not in row or pd.isna(row["work_type"]):
                raise ValueError(f"'work_type' is missing from row! row: {row.to_dict()}")
        
        if row["role"] == "u13":
            logger.info(f"Role is 'u13' for row {row.to_dict()}. Setting cost to 0.")
            return 0
        
        if row["work_type"] == "glenne_vedpakking" and row["role"] in ["genf"]:
            if not "vedsekk" in rate:
                logger.warning("vedpakking is missing from rates. Adding 15 kr as default value")
            return row["units_completed"] * rate.get("vedsekk", 15)
        else:
            #print(f' ======= CURRENT ROW: {row.to_dict()} ======= ')
            try:
                return row["hours_worked"] * rate.get(row["role"])
            except TypeError as e:
                logger.warning(f"Error calculating cost for row \n{row.to_dict()} \nand rate \n{rate}\n: {e}\n\n")


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
    def run_query(_self, table_name: str, cols : list = [], return_dataframe : bool = True) -> pd.DataFrame | dict:
        select_cols = ", ".join(cols) if cols else "*"
        response = _self.supabase.table(table_name).select(select_cols).execute()
        data = response.data
        if return_dataframe:
            if data is None:
                    return pd.DataFrame()
            return pd.DataFrame(data)
        else:
            if data is None:
                return {}
            return data
    
    def _calc_camp_season(self, season: str, role: str) -> float:
        """Calculate camp cost for a season (e.g. '2024/2025')"""
        if role in ["genf", "hjelpementor"]:
            age_group = "u"
        else:
            age_group = "o"

        data = self.run_query("camp_rates")
        if data is None or data.empty:
            raise ValueError("Camp rates data is empty or not available")

        try:
            year1, year2 = map(int, season.split("/"))
        except (ValueError, IndexError) as e:
            raise ValueError(f"Invalid season format: {season!r}. Expected e.g. '2024/2025'") from e

        # Get values - with proper error handling
        try:
            nc = data.loc[data["year"] == year1, age_group + "18_s"].item()
            sc_pc = data.loc[data["year"] == year2, age_group + "18_l"].item() * 2
        except (KeyError, ValueError, IndexError) as e:
            raise ValueError(
                f"Missing camp rate data for season {season} "
                f"(years {year1}/{year2}, group {age_group})"
            ) from e

        return nc + sc_pc

    def _calc_camp_year(self, year: int, role: str) -> float:
        """Calculate camp cost for a single year"""
        if role in ["genf", "hjelpementor"]:
            age_group = "u"
        else:
            age_group = "o"

        data = self.run_query("camp_rates")
        if data is None or data.empty:
            raise ValueError("Camp rates data is empty or not available")

        try:
            nc = data.loc[data["year"] == year, age_group + "18_s"].item()
            sc_pc = data.loc[data["year"] == year, age_group + "18_l"].item() * 2
        except (KeyError, ValueError, IndexError) as e:
            raise ValueError(
                f"Missing camp rate data for year {year} (group {age_group})"
            ) from e

        return nc + sc_pc

    def calc_camp_cost(
        self,
        period: str,
        role: Literal["genf", "hjelpementor", "mentor"],
        type_: Literal["year", "season"] = "season"
    ) -> float:
        """
        Main entry point to calculate camp cost.
        
        Args:
            period: "2024/2025" (season) or "2025" (year)
            role: participant role
            type_: "season" or "year"
        """
        if type_ == "season":
            return self._calc_camp_season(period, role)
        elif type_ == "year":
            try:
                year = int(period)
            except ValueError:
                raise ValueError(f"Invalid year format for type_='year': {period!r}")
            return self._calc_camp_year(year, role)
        else:
            raise ValueError(f"Invalid type_: {type_!r} (must be 'year' or 'season')")

class SupaBaseApi(DatabaseModule):
    def __init__(self):
        super().__init__()
        self.supabase_url = st.secrets["supabase"].get("buk_cash").get("SUPABASE_URL")
        self.supabase_key = st.secrets["supabase"].get("buk_cash").get("SUPABASE_ANON_KEY")
        self.supabase_api_key = st.secrets["supabase"].get("buk_cash").get("API_KEY")
        self.supabase = create_client(self.supabase_url, self.supabase_key)

    @st.cache_data(ttl=3600,show_spinner=False)
    def run_query(self, query: str):
        pass
    
    @st.cache_data(ttl=600, show_spinner=False)
    def fetch_job_logs(_self,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None
    ) -> pd.DataFrame:
        """
        Fetch job logs using API key with optional date filtering.
        
        Args:
            from_date: Optional start date (inclusive)
            to_date: Optional end date (inclusive)
        
        Returns:
            DataFrame of job log records
        """
        # If dates are missing, try to get them from session state
        if from_date is None or to_date is None:
            try:
                st_dates = st.session_state.get("dates")
                if st_dates and len(st_dates) == 2:
                    st_from, st_to = st_dates
                    if from_date is None:
                        from_date = st_from
                    if to_date is None:
                        to_date = st_to
            except Exception:
                pass

        # Convert to date objects if they are strings or datetimes
        def to_date_obj(d):
            if isinstance(d, str):
                return date.fromisoformat(d)
            if isinstance(d, datetime):
                return d.date()
            return d

        from_date = to_date_obj(from_date)
        to_date = to_date_obj(to_date)

        params = {"p_api_key": _self.supabase_api_key}
        params["p_from_date"] = from_date.isoformat() if from_date else None
        params["p_to_date"] = to_date.isoformat() if to_date else None
        
        try:
            # Call the RPC function
            response = _self.supabase.rpc("get_job_logs_with_api_key", params).execute()
            data = response.data
            
            if data is None:
                return pd.DataFrame()
            
            return pd.DataFrame(data)
        
        except Exception as e:
            logger.error(f"Error fetching job logs: {e}")
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

    def build_combined(self,):
        bc_m = self.fetch_profiles()
        bc_m = bc_m.loc[bc_m["role"] != "parent", :].drop(columns = ["role"]).copy()
        df_bc = self.fetch_job_logs("2026-01-01")
        df_bc["season"] = "25/26"
        bc_m["role"] = bc_m["date_of_birth"].apply(lambda x: self.apply_role(x, season=st.session_state.get("season", None)))
        df = pd.merge(df_bc, bc_m.loc[:,['id','email',"bank_account_number","role"]], left_on='worker_id', right_on='id', how='left')
        to_keep = ["worker_id",
                "hours_worked",
                "worker_first_name",
                "worker_last_name",
                "date_completed",
                "work_type",
                "email",
                "bank_account_number",
                "role","season",
                "units_completed",
                "comments",
                ]
        df = df.loc[:,to_keep].copy()
        df["date_completed"] = pd.to_datetime(df["date_completed"], errors='coerce', utc=True)
        df["units_completed"] = df["units_completed"].fillna(0)
        return df

class CombinedModule(DatabaseModule):
    def __init__(self):
        super().__init__()
        self.supabase_api = get_supabase_api()
        self.supabase_module = get_supabase_module()

    def load_all_registrations(self):
        df_new = self.supabase_api.build_combined()
        df_old = self.supabase_module.run_query("registrations")
        df = pd.concat([df_old, df_new], ignore_index=True)
        rates = self.supabase_module.run_query("rates", return_dataframe=False)
        df["cost"] =  df.apply(lambda row : self.supabase_api.apply_cost(row, rates,), axis = 1)
        df["units_completed"] = df["units_completed"].fillna(0)
        df["date_completed"] = pd.to_datetime(df["date_completed"], errors='coerce', utc=True)
        return df

#@st.cache_resource(ttl=3600, show_spinner=False)
def get_supabase_api():
    return SupaBaseApi()

#@st.cache_resource(ttl=3600, show_spinner=False)
def get_bigquery_module():
    return BigQueryModule()

#@st.cache_resource(ttl=3600, show_spinner=False)
def get_supabase_module():
    return SupabaseModule()

#@st.cache_resource(ttl=3600, show_spinner=False)
def get_combined_module():
    return CombinedModule()