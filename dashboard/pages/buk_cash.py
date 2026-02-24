import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import timedelta, date
from io import BytesIO
import logging

from dashboard import init
from components import SidebarComponent, get_supabase_api, DownloadComponent, get_bigquery_module

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


init()
api = get_supabase_api()
bq_module = get_bigquery_module()
SidebarComponent().sidebar_setup(disable_datepicker=False, disable_custom_datepicker=False)   
st.title("Buk.cash API")


tabs = st.tabs(["Timer", "Brukere", "Jobber"])

with tabs[0]:
    st.info(f"Viser for periode {st.session_state.dates[0]} til {st.session_state.dates[1]}")
    # ==== DATA CLEANING =====
    df_raw = api.fetch_job_logs()
    df = api.filter_df_by_dates(df_raw.copy(), dates=st.session_state.dates,)
    st.dataframe(df, use_container_width=True)
    
    
    cols  = st.columns(3)
    with cols[0]:
        DownloadComponent().render_csv_download(df, filename="buk_cash")
    
    with cols[1]:
        DownloadComponent().render_xlsx_download(df, filename="buk_cash")
    with cols[2]:
        DownloadComponent().render_bigquery_update(df = df, bq_module=bq_module, target_table="raw.job_logs", write_type="replace")
    
    
with tabs[1]:
    # ======= UPDATE MEMBERS =======
    st.divider()
    with st.container():
        st.markdown("## Hent medlemsliste fra buk.cash og oppdater database")
        data = api.fetch_profiles()
        members_bc = pd.DataFrame(data)
        members_bc = members_bc.loc[members_bc["role"] != "parent"].copy()
        members_bc["date_of_birth"] = pd.to_datetime(members_bc["date_of_birth"], errors='coerce', format="%Y-%m-%d")
        members_bc["role"] = members_bc.apply(lambda row: api.apply_role(row["date_of_birth"]) if pd.notnull(row["date_of_birth"]) else "unknown", axis=1)
        
        with st.expander(f"Medlemmer under 13 år (rolle 'u13')", expanded=False):
            for row in members_bc.loc[members_bc["role"]=="u13",:].itertuples():
                st.warning(f"{row.first_name} {row.last_name} (ID: {row.id}) er under 14 år og har rollen 'u13'. Kostnaden for denne personen vil settes til 0.")
        with st.expander(f"Medlemmer med ukjent alder (rolle 'unknown')", expanded=False):
            for row in members_bc.loc[members_bc["role"]=="unknown",:].itertuples():
                st.error(f"{row.first_name} {row.last_name} (ID: {row.id}) har ukjent alder og får rollen 'unknown'. Vennligst sjekk fødselsdatoen for denne personen.")
        
        # Create display dataframe with datetime column
        df_members = members_bc[["id","custom_id","email","role","first_name","last_name","bank_account_number","date_of_birth"]].copy()
        df_members["name"] = df_members["first_name"] + " " + df_members["last_name"]
        
        sel_cols = st.columns(2)
        name = sel_cols[0].multiselect("Velg navn (tom for alle)", options=df_members["name"].unique().tolist(), default=[])
        worker_id = sel_cols[1].multiselect("Velg ID (tom for alle)", options=df_members["id"].astype(str).unique().tolist(), default=[])

        df_members = df_members.loc[(df_members["name"].isin(name) if name else df_members.index) & (df_members["id"].astype(str).isin(worker_id) if worker_id else df_members.index),:]

        cols = st.columns(3)
        cols[0].metric("Antall mentorer", df_members.loc[df_members["date_of_birth"].dt.year < 2008,"id"].nunique())
        cols[1].metric("Antall hjelpementorer", df_members.loc[(df_members["date_of_birth"].dt.year.isin([2008,2009])),"id"].nunique())
        cols[2].metric("Antall GENF", df_members.loc[df_members["date_of_birth"].dt.year > 2009,"id"].nunique())
        
        st.dataframe(df_members, use_container_width=True)

        raw_data = pd.DataFrame(data)
        cols  = st.columns(3)
        with cols[0]:
            DownloadComponent().render_csv_download(raw_data, filename="buk_cash")
        
        with cols[1]:
            DownloadComponent().render_xlsx_download(raw_data, filename="buk_cash")
        with cols[2]:
            DownloadComponent().render_bigquery_update(raw_data, bq_module=bq_module, target_table="raw.users", write_type="replace")



with tabs[2]:
    st.markdown("## Jobber")
    data = api.fetch_work_requests(from_date = (date.today() - timedelta(days=30)),)
    #st.json(data)
    for i in data:
        if i.get("desired_start_date") >= str(date.today()):
            if st.button(f"{i.get('desired_start_date')}: \t {i.get('title')} - {i.get('location')} - {i.get('estimated_hours')} timer", key=i['id']):
                with st.container(border=True,):
                    job_data = api.fetch_job_applications(work_request_id=i['id'])
                    df_r = pd.DataFrame(job_data).loc[:,["user_id","user_first_name", "user_last_name", "user_email"]]
                    df = pd.merge(df_r, raw_data[["id","date_of_birth"]], left_on="user_id", right_on="id", how="left", suffixes=("","_profile"))
                    df["role"] = df["date_of_birth"].apply(lambda x: api.apply_role(x) if pd.notnull(x) else "unknown")
                    df.drop(columns=["id"], inplace=True)
                    st.dataframe(df, use_container_width=True)
                    cols  = st.columns(3)
                    with cols[0]:
                        DownloadComponent().render_csv_download(df, filename="work_requests")
                    
                    with cols[1]:
                        DownloadComponent().render_xlsx_download(df, filename="work_requests")
                    with cols[2]:
                        DownloadComponent().render_bigquery_update(df, bq_module=bq_module, target_table="raw.work_requests", write_type="replace")
        