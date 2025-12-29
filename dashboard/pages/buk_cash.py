import streamlit as st
from utilities import init, sidebar_setup, fetch_job_logs
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta, date
from io import BytesIO


init()
sidebar_setup(disable_datepicker=False, disable_custom_datepicker=False)   
st.title("Stream from Buk.cash")
st.divider()

df_raw = fetch_job_logs()
st.info(f"Viser timer og lønn for periode {st.session_state.dates[0]} til {st.session_state.dates[1]}")
st.dataframe(df_raw)
df_raw["name"] = df_raw["worker_first_name"] + " " + df_raw["worker_last_name"]
df_raw["cost"] = df_raw["hours_worked"] * df_raw["hourly_rate"]

sel_cols = st.columns(2)
name = sel_cols[0].multiselect("Velg navn (tom for alle)", options=df_raw["name"].unique().tolist(), default=[])
every_sample = sel_cols[1].toggle("Skru av sammenslåing", value=False)

sel_cols2 = st.columns(2)
#gruppe = sel_cols2[0].multiselect("Velg gruppe (tom for alle)", options=df_raw["gruppe"].unique().tolist(), default=[])
prosjekt = sel_cols2[1].multiselect("Velg prosjekt (tom for alle)", options=df_raw["work_type"].unique().tolist(), default=[])
    

#st.dataframe(df_raw)


# try:
#     df = df_raw.loc[
#     (df_raw['dato'] >= pd.to_datetime(st.session_state.dates[0], utc=True)) &
#     (df_raw['dato'] <= pd.to_datetime(st.session_state.dates[1], utc=True)) & 
#     #(df_raw['gruppe'].isin(gruppe) if gruppe else True) &
#     (df_raw['prosjekt'].isin(prosjekt) if prosjekt else True)
#     ].copy()
# except KeyError as e:
#     st.error(f"Data loading error: {e}. Missing expected columns in the data.")
# except Exception as e:
#     st.error(f"An unexpected error occurred: {e}")

df = df_raw.copy()
    


#========================
#      HOUR DATAFRAME
#========================

hours = st.container(width="stretch")
with hours:
    # delta_time = st.session_state.dates[1] - st.session_state.dates[0]
    # delta_start = st.session_state.dates[0] - delta_time - timedelta(days=1)
    # delta_df = df_raw.loc[
    #     (df_raw['dato'] >= pd.to_datetime(delta_start, utc=True)) &
    #     (df_raw['dato'] < pd.to_datetime(st.session_state.dates[0], utc=True))
    #     ].copy()
    # cols = st.columns(3)
    # cols[0].metric(label = "Total antall timer", value = f"{df['timer'].sum():,.0f}", 
    #                delta = f"{df['timer'].sum() - delta_df['timer'].sum():,.0f} fra forrige periode")
    # cols[1].metric(label = "Totale kostnader", value = f"{df['kostnad'].sum():,.0f} NOK",
    #                delta = f"{df['kostnad'].sum() - delta_df['kostnad'].sum():,.0f} NOK fra forrige periode")
    # cols[2].metric(label = "Antall unike brukere", value = f"{df['navn'].nunique():,.0f}",
    #                delta = f"{df['navn'].nunique() - delta_df['navn'].nunique():,.0f} fra forrige periode")

    if name:
        df = df[df["navn"].isin(name)]
    else:
        if not every_sample:
            dfg = df.groupby(["name","worker_id",])[["hours_worked","cost"]].sum().reset_index()
        else:
            dfg = df[["name","worker_id","hours_worked","cost","hourly_rate"]].copy()

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

