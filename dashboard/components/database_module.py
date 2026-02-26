import streamlit as st
from google.oauth2 import service_account
from google.cloud import bigquery
from datetime import datetime
import calendar
import pandas as pd
from supabase import create_client
from datetime import date, datetime,timedelta
from typing import Optional,Any, List, Dict,Tuple,Literal, Union
import logging
from abc import ABC, abstractmethod
from .models import JobLog, User, WorkRequest, HistoricalJobEntry
import numpy as np


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
        ALL_COLS = ["worker_name","email","bank_account_number","role","prosjekt","gruppe","work_type","comments","cost","hours_worked","units_completed","date_completed",]
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
            cols = [col for col in ALL_COLS if col in df.columns]
            dfg = df[cols].copy()
        
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

    def mk_gruppe(self, work_type : str):
        '''
        Args:
            work_type: str, expected format "gruppe_prosjekt" e.g. "genf_rydding", "hjelpementor_kiosk", "mentor_glenne_vedpakking"
        Returns:
            str: gruppe, e.g. "genf", "hjelpementor", "mentor"

        Usage:
            df['gruppe'] = df['work_type'].apply(lambda wt: self.mk_gruppe(wt))
        '''
        if not work_type:
            return None
        return work_type.split("_")[0] if "_" in work_type else work_type
    def mk_prosjekt(self, work_type : str):
        if not work_type:
            return None
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
        data = self.run_query(query)
        data.replace({"<NA>": None, pd.NaT: None,np.nan : None}, inplace=True)
        data["hours_worked"] = pd.to_numeric(data["hours_worked"], errors="coerce")
        data["cost"] = pd.to_numeric(data["cost"], errors="coerce")
        data["work_type"] = data["work_type"].fillna("unknown")
        [HistoricalJobEntry.model_validate(record) for record in data.to_dict(orient="records")] if not data.empty else None
        return data
        
    
    def load_active_users(self, threshold = 1000):
        query =  f'''SELECT s.person_id,r.email 
            FROM `genf-446213.registrations.season_22_25` r
            JOIN members.specs s ON s.email = r.email
            GROUP BY r.email, s.person_id
            HAVING SUM(cost)>{threshold};'''
        return self.run_query(query)
    
    def load_rates(self):
        query = """SELECT * FROM admin.rates"""
        data = self.run_query(query)
        return data

    def load_camp_rates(self):
        query = """SELECT * FROM admin.camp_rates"""
        data = self.run_query(query)
        return data

    def write_df(
        self,
        df: pd.DataFrame,
        target_table: str = "raw.buk_cash",
        write_type: Literal["append", "replace", "merge"] = "append",
        project_id: str = "genf-446213",
        merge_on: Union[str, List[str]] = "id",
    ) -> int:
        """
        Skriver df til BigQuery. Returnerer antall rader skrevet.

        append  – inserter bare rader nyere enn MAX(date_completed) i måltabellen.
        replace – WRITE_TRUNCATE: sletter og skriver alt på nytt.
        merge   – upsert via temp-tabell + MERGE SQL på merge_on.
        """
        full_table_id = f"{project_id}.{target_table}"
        keys = [merge_on] if isinstance(merge_on, str) else merge_on

        df_clean = df.copy()
        for col in df_clean.select_dtypes(include=["datetimetz"]).columns:
            df_clean[col] = df_clean[col].dt.tz_localize(None)

        if write_type == "replace":
            job_config = bigquery.LoadJobConfig(write_disposition="WRITE_TRUNCATE")
            self.client.load_table_from_dataframe(
                df_clean, full_table_id, job_config=job_config
            ).result()
            return len(df_clean)

        if write_type == "append":
            try:
                max_date_df = self.client.query(
                    f"SELECT MAX(date_completed) AS max_date FROM `{full_table_id}`"
                ).result().to_dataframe()
                max_date = max_date_df["max_date"].iloc[0]
                if pd.notna(max_date):
                    df_clean["date_completed"] = pd.to_datetime(df_clean["date_completed"])
                    df_clean = df_clean[df_clean["date_completed"] > pd.to_datetime(max_date)]
            except Exception:
                pass  # Tabellen finnes ikke ennå — last opp alt

            if df_clean.empty:
                return 0

            job_config = bigquery.LoadJobConfig(write_disposition="WRITE_APPEND")
            self.client.load_table_from_dataframe(
                df_clean, full_table_id, job_config=job_config
            ).result()
            return len(df_clean)

        if write_type == "merge":
            missing = [k for k in keys if k not in df_clean.columns]
            if missing:
                raise ValueError(f"merge_on kolonne(r) mangler i df: {missing}")

            temp_table_id = (
                f"{full_table_id}_temp_{pd.Timestamp.now().strftime('%Y%m%d%H%M%S')}"
            )
            job_config = bigquery.LoadJobConfig(write_disposition="WRITE_TRUNCATE")
            self.client.load_table_from_dataframe(
                df_clean, temp_table_id, job_config=job_config
            ).result()

            on_clause = " AND ".join(f"T.{k} = S.{k}" for k in keys)
            update_cols = ", ".join(
                f"T.{c} = S.{c}" for c in df_clean.columns if c not in keys
            )
            insert_cols = ", ".join(df_clean.columns)
            insert_vals = ", ".join(f"S.{c}" for c in df_clean.columns)

            self.client.query(f"""
                MERGE `{full_table_id}` T
                USING `{temp_table_id}` S
                ON {on_clause}
                WHEN MATCHED THEN UPDATE SET {update_cols}
                WHEN NOT MATCHED THEN INSERT ({insert_cols}) VALUES ({insert_vals})
            """).result()
            self.client.delete_table(temp_table_id, not_found_ok=True)
            return len(df_clean)

        raise ValueError(f"Ukjent write_type: {write_type!r}")

class SupaBaseApi(DatabaseModule):
    def __init__(self):
        super().__init__()
        self.supabase_url = st.secrets["supabase"].get("SUPABASE_URL")
        self.supabase_key = st.secrets["supabase"].get("SUPABASE_ANON_KEY")
        self.supabase_api_key = st.secrets["supabase"].get("API_KEY")
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
            [JobLog.model_validate(record) for record in data] if data else None 
            
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
            [User.model_validate(record) for record in response.data] if response.data else None
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
            [WorkRequest.model_validate(record) for record in response.data] if response.data else None
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
        df["worker_name"] = df["worker_first_name"] + " " + df["worker_last_name"]
        df["cost"] = df.apply(lambda row : self.apply_cost(row, st.session_state.get("rates", []),), axis = 1)
        to_keep = ["worker_id",
                   "worker_name", 
                   "role",
                   "email",
                    "bank_account_number",
                    "season",
                    "comments",
                   "date_completed",
                   "work_type",
                    "hours_worked",
                    "units_completed",
                     "cost",
                ]
        df = df.loc[:,to_keep].copy()
        df["date_completed"] = pd.to_datetime(df["date_completed"], errors='coerce', utc=True)
        df["units_completed"] = df["units_completed"].fillna(0)
        return df
    
def get_supabase_api():
    return SupaBaseApi()

def get_bigquery_module():
    return BigQueryModule()
