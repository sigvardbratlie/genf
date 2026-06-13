import streamlit as st
import logging
import pandas as pd
from components.database_module import get_bigquery_module,get_supabase_api
from components.sidebar import SidebarComponent
from dashboard.utilities import init
import os

logger  = logging.getLogger(__name__)

init()
SidebarComponent().sidebar_setup(disable_seasonpicker=False,disable_datepicker=False, disable_custom_datepicker=True)


sync_data = st.button("Synkroniser data", icon="🔄")
if sync_data:
    bq = get_bigquery_module()
    try:
        bq.transfer_to_hours()
        st.success("Data synkronisert!")
    except Exception as e:
        st.error(f"Det skjedde en feil under synkronisering av data: {e}")
        logger.error(f"Feil under synkronisering av data: {e}", exc_info=True)

class ScoresPage:
    def __init__(self, from_date = "2025-08-01", to_date = "2026-08-01"):
        self.bq = get_bigquery_module()
        self.df = self._load_registrations(from_date, to_date)

    def _load_registrations(self, from_date, to_date) -> pd.DataFrame:
            df = self.bq.load_registrations(from_date = from_date, to_date = to_date)
            df["gruppe"] = df["work_type"].apply(self.bq.mk_gruppe)
            df["prosjekt"] = df["work_type"].apply(self.bq.mk_prosjekt)
            df["date_completed"] = pd.to_datetime(df["date_completed"])
            profiles = self.bq.run_query("SELECT id, email FROM `raw.users`")
            profiles.rename(columns={"id":"worker_id"}, inplace=True)
            df = pd.merge(df, profiles, on = "worker_id", how="left")
            df["email"] = df["email_x"].combine_first(df["email_y"])
            df.drop(columns=["email_x","email_y",], inplace=True)
            roles = st.session_state.role if st.session_state.role else ["genf", "mentor", "hjelpementor"]
            df = df.loc[df["role"].isin(roles), :]
            return df

dates = st.session_state.dates if st.session_state.dates else ["2025-08-01", "2026-08-01"]

df = ScoresPage(from_date=dates[0], to_date=dates[1]).df
st.write(f'Dates range from {df["date_completed"].min()} to {df["date_completed"].max()}')
supabase = get_supabase_api()

most_hours = st.expander("Hvem har jobbet mest?", expanded=False)
with most_hours:
    st.header("Hvem har jobbet mest?")
    df_25 = df[df["date_completed"].dt.year == 2025]
    st.markdown("The person with the most hours 2025")
    hours_by_person = df_25.groupby("email")["hours_worked"].sum()
    hours_by_person = hours_by_person.sort_values(ascending=False).reset_index()
    st.dataframe(hours_by_person.head(5))
    

    df_26 = df[df["date_completed"].dt.year == 2026]
    st.markdown("The person with the most hours 2026")
    hours_by_person_26 = df_26.groupby("email")["hours_worked"].sum()
    hours_by_person_26 = hours_by_person_26.sort_values(ascending=False).reset_index()
    st.dataframe(hours_by_person_26.head(5))
    

    comb = df.groupby("email")["hours_worked"].sum()
    comb = comb.sort_values(ascending=False).reset_index()
    st.markdown("The person with the most hours total")
    st.dataframe(comb.head(5))

application = st.expander("Hvem er raskest til å melde seg på jobber?", expanded=False)
with application:
    work_requests = supabase.fetch_work_requests()
    work_request_ids = [(wr["id"],wr["approved_at"],wr["desired_start_date"]) for wr in work_requests if wr["approved_at"]]
    applications = []
    for wid in work_request_ids:
        response = supabase.fetch_job_applications(work_request_id=wid[0])
        if not response:
            print(f"No applications found for work request ID: {wid}")
            continue
        applications.extend([(r.get("user_email"), r.get("created_at"), wid[1], wid[2]) for r in response])

    df = pd.DataFrame(applications, columns=["user_email", "applied", "approved_at", "desired_start_date"])
    df["applied"] = pd.to_datetime(df["applied"])
    df["approved_at"] = pd.to_datetime(df["approved_at"])
    df["desired_start_date"] = pd.to_datetime(df["desired_start_date"])
    #df["diff_from_start_date"] = (df["desired_start_date"].dt.date - df["applied"].dt.date)
    df["diff_from_approve_date"] = (df["applied"] - df["approved_at"])
    df = df.loc[df["diff_from_approve_date"] >= pd.Timedelta(0), :]  # Filter out applications made before approval

    st.markdown("Hvem er rasktest til å melde seg på en jobb?")
    application_speed = df.groupby("user_email")["diff_from_approve_date"].agg(["mean", "count"])
    application_speed = application_speed.loc[application_speed["count"] >= 5, :]
    st.dataframe(application_speed.sort_values(by = "mean", ascending=True))

    st.markdown("Hvem melder seg på senest?")
    st.dataframe(application_speed.sort_values(by = "mean", ascending=False))


     
    
    
    
