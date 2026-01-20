import streamlit as st
from utilities import init, sidebar_setup, fetch_job_logs, fetch_profiles,fetch_work_requests,fetch_job_applications,apply_role
from google.cloud import bigquery
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta, date
from io import BytesIO


def mk_gruppe_prosjekt(df_raw):
    prosjekt_col = df_raw["work_type"].apply(lambda x: " ".join(x.split("_")[1:]) if "_" in x and len(x.split("_")) > 1 else x)
    gruppe_col = df_raw["work_type"].apply(lambda x: x.split("_")[0] if "_" in x else x)
    df_raw["gruppe"] = gruppe_col
    df_raw["prosjekt"] = prosjekt_col
    return df_raw.drop(columns=["work_type"],)

init()
sidebar_setup(disable_datepicker=False, disable_custom_datepicker=False)   
st.title("Buk.cash API")
#st.divider()

tabs = st.tabs(["Timer", "Brukere", "Jobber"])
with tabs[0]:
    st.info(f"Viser for periode {st.session_state.dates[0]} til {st.session_state.dates[1]}")

    # ==== DATA CLEANING =====
    df_raw = fetch_job_logs()
    #st.dataframe(df_raw.loc[df_raw["work_type"]=="glenne_vedpakking",:])
    df_raw["name"] = df_raw["worker_first_name"] + " " + df_raw["worker_last_name"]
    df_raw["cost"] = df_raw["hours_worked"] * df_raw["hourly_rate"]
    df_raw = mk_gruppe_prosjekt(df_raw)
    df_raw["date_completed"] = pd.to_datetime(df_raw["date_completed"], utc=True)

    sel_cols = st.columns(2)
    name = sel_cols[0].multiselect("Velg navn (tom for alle)", options=df_raw["name"].unique().tolist(), default=[])
    every_sample = sel_cols[1].toggle("Skru av sammenslåing", value=False)

    sel_cols2 = st.columns(2)
    gruppe = sel_cols2[0].multiselect("Velg gruppe (tom for alle)", 
                                    options=df_raw["gruppe"].unique().tolist(), 
                                    default=df_raw["gruppe"].unique().tolist())
    prosjekt = sel_cols2[1].multiselect("Velg prosjekt (tom for alle)", 
                                        options=df_raw["prosjekt"].unique().tolist(), 
                                        default=df_raw["prosjekt"].unique().tolist())


    try:
        df = df_raw.loc[
        (df_raw['date_completed'] >= pd.to_datetime(st.session_state.dates[0], utc=True)) &
        (df_raw['date_completed'] <= pd.to_datetime(st.session_state.dates[1], utc=True)) & 
        (df_raw['gruppe'].isin(gruppe) if gruppe else True) &
        (df_raw['prosjekt'].isin(prosjekt) if prosjekt else True)
        ].copy()
    except KeyError as e:
        st.error(f"Data loading error: {e}. Missing expected columns in the data.")
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")

    df = df_raw.copy()
        


    #========================
    #      HOUR DATAFRAME
    #========================

    hours = st.container(width="stretch")
    with hours:

        if name:
            df = df[df["navn"].isin(name)]
        else:
            if not every_sample:
                dfg = df.groupby(["name","worker_id",])[["hours_worked","cost"]].sum().reset_index()
            else:
                dfg = df[["date_completed","name","worker_id","hours_worked","cost",]].copy()

        st.divider()
        st.dataframe(dfg.style.format({"hours_worked":"{:,.1f}",
                                    "cost":"{:,.0f} NOK"}),use_container_width=True,)
        
        # ========================
        #      DOWNLOAD DATA
        # ========================

        with st.expander("Last ned data"):
            cols = st.columns(2)
            cols[0].download_button(
                label="Last ned data som CSV",
                data=dfg.to_csv(index=False).encode('utf-8'),
                file_name=f'timer_og_lonn_{st.session_state.dates[0]}_til_{st.session_state.dates[1]}.csv',
                mime='text/csv',
                icon="📄"
            )
            buffer = BytesIO()
            dfg.to_excel(buffer, index=False, engine='openpyxl')
            buffer.seek(0)
            cols[1].download_button(
            label="Last ned data som Excel",
            data=buffer.getvalue(),
            file_name=f'timer_og_lonn_{st.session_state.dates[0]}_til_{st.session_state.dates[1]}.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            icon="📄"
        )
    st.divider()

with tabs[1]:
    # ======= UPDATE MEMBERS =======
    st.divider()
    with st.container():
        st.markdown("## Hent medlemsliste fra buk.cash og oppdater database")
        data = fetch_profiles()
        members_bc = pd.DataFrame(data)
        members_bc = members_bc.loc[members_bc["role"] != "parent"].copy()
        df_to_save = members_bc[["id","custom_id","email","role","first_name","last_name","bank_account_number","date_of_birth"]]

        st.dataframe(df_to_save, use_container_width=True)
        
        
        cols = st.columns(3)
        
        with cols[0]:
            #if st.button("Last ned (CSV)",icon="📥"):
            csv = df_to_save.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Last ned CSV",
                data=csv,
                file_name='members_buk_cash.csv',
                mime='text/csv',
                icon="📄"
            )
        with cols[1]:
            #if st.button("Last ned (Excel)",icon="📥"):
            buffer = BytesIO()
            df_to_save.to_excel(buffer, index=False, engine='openpyxl')
            buffer.seek(0)
            st.download_button(
                    label="Last ned (Excel)",
                    data=buffer.getvalue(),
                    file_name=f'members_buk_cash.xlsx',
                    mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                    icon="📄")

        with cols[2]:
            if st.button("Oppdater (BigQuery)",icon="🔄"):
                try:
                    st.session_state.gcp_client.load_table_from_dataframe(df_to_save, "members.buk_cash", 
                                                                job_config = bigquery.LoadJobConfig(write_disposition="WRITE_TRUNCATE"))
                    st.success("Medlemsdatabase oppdatert fra buk.cash!")
                except Exception as e:
                    st.error(f"Error updating members database: {e}")


with tabs[2]:
    st.markdown("## Jobber")
    data = fetch_work_requests(from_date = (date.today() - timedelta(days=30)),)
    #st.json(data)
    for i in data:
        if i.get("desired_start_date") >= str(date.today()):
            if st.button(f"{i.get('desired_start_date')}: \t {i.get('title')} - {i.get('location')} - {i.get('estimated_hours')} timer", key=i['id']):
                #with st.expander(f"Jobbdetaljer",expanded=False):
                job_data = fetch_job_applications(work_request_id=i['id'])
                df_r = pd.DataFrame(job_data).loc[:,["user_id","user_first_name", "user_last_name", "user_email"]]
                df = pd.merge(df_r, df_to_save[["id","date_of_birth"]], left_on="user_id", right_on="id", how="left", suffixes=("","_profile"))
                df["role"] = df["date_of_birth"].apply(lambda x: apply_role(x) if pd.notnull(x) else "unknown")
                df.drop(columns=["id"], inplace=True)
                st.dataframe(df, use_container_width=True)

                with st.expander("Last ned data"):
                    cols = st.columns(2)
                    cols[0].download_button(
                                            label="Last ned data som CSV",
                                            data=df.to_csv(index=False).encode('utf-8'),
                                            file_name=f'timer_og_lonn_{st.session_state.dates[0]}_til_{st.session_state.dates[1]}.csv',
                                            mime='text/csv',
                                            key= i['id'] + "_csv",
                                            icon="📄"
                                        )
                    buffer = BytesIO()
                    df.to_excel(buffer, index=False, engine='openpyxl')
                    buffer.seek(0)
                    cols[1].download_button(
                                            label="Last ned data som Excel",
                                            data=buffer.getvalue(),
                                            file_name=f'timer_og_lonn_{st.session_state.dates[0]}_til_{st.session_state.dates[1]}.xlsx',
                                            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                                            key= i['id'] + "_excel",    
                                            icon="📄"
                )
        