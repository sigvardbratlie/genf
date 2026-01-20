import streamlit as st
from utilities import init, sidebar_setup, fetch_job_logs
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
st.title("Stream from Buk.cash")
st.divider()

st.info(f"Viser timer og lønn for periode {st.session_state.dates[0]} til {st.session_state.dates[1]}")

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
season = st.container()

