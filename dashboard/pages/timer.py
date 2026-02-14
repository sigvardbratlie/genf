import streamlit as st
import pandas as pd
import numpy as np
from utilities import init
from dashboard.components import SidebarComponent,get_supabase_api, get_supabase_module,get_combined_module, DownloadComponent
from datetime import datetime,timedelta
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO
import calendar
import logging
logger = logging.getLogger(__name__)

init()

st.title("Timer og lønn")
st.divider()
SidebarComponent().sidebar_setup()



sm = get_supabase_module()
data = sm.run_query("registrations")
st.dataframe(data["season"].value_counts().reset_index(), use_container_width=True)
st.info(len(data))


cm = get_combined_module()

# ========================
#      LOAD DATA
# ========================
df = cm.load_all_registrations()
df["worker_name"] = df["worker_first_name"] + " " + df["worker_last_name"]
df_raw = df.copy()


sel_cols = st.columns(2)

name = sel_cols[0].multiselect("Velg navn (tom for alle)", options=df["worker_name"].unique().tolist(), default=[])
every_sample = sel_cols[1].toggle("Skru av sammenslåing", value=False)

sel_cols2 = st.columns(2)
work_types = sel_cols2[0].multiselect("Velg arbeidstype (tom for alle)", options=df["work_type"].unique().tolist(), default=[])
df = cm.filter_df_by_dates(df)
df = cm.filter_work_type(df, work_types)
if name:
    df = df[df["worker_name"].isin(name)]


st.info(f"Viser timer og lønn for periode {st.session_state.dates[0]} til {st.session_state.dates[1]}")
min_date = df["date_completed"].min().strftime("%Y-%m-%d") if not df.empty else "N/A"
max_date = df["date_completed"].max().strftime("%Y-%m-%d") if not df.empty else "N/A"
st.write(f'**First registration**: {min_date}, **Last registration**: {max_date}')


#========================
#      HOUR DATAFRAME
#========================

hours = st.container(width="stretch")
with hours:
    cm.render_metrics(df, df_raw)
    
    st.divider()
    dfg = cm.apply_grouping(df, every_sample=every_sample)
    st.dataframe(dfg.style.format({"cost":"{:,.0f} NOK",
                                   "hours_worked":"{:,.1f}",
                                   "units_completed":"{:,.0f}"}),use_container_width=True,height=700)
    # ========================
    #      DOWNLOAD DATA
    # ========================

    with st.expander("Last ned data"):
        download_component = DownloadComponent()
        download_component.render_csv_xlsx_download_section(dfg, f'timer_og_lonn_{st.session_state.dates[0]}_til_{st.session_state.dates[1]}')
        
st.divider()
season = st.container()

#========================
# Cumulative Cost Over Months
#========================
cum_cost = st.container()
with cum_cost:
    show_cumulative = st.toggle("Vis kumulativ lønn per sesong", value=False)
    if show_cumulative:
        st.caption("TO BE IMPLEMENTED",)

        
        #IMPLEMENT LOAD FROM BIG QUERY
        # st.markdown("## Kumulativ lønn per sesong")
        # df_raw["month"] = df_raw['date_completed'].dt.month
        # df_raw["year"] = df_raw['date_completed'].dt.year
        # df_raw["fiscal_month"] = ((df_raw['month'] - 8) % 12) + 1
        
        # df_month = df_raw.groupby(['season', 'fiscal_month']).agg({'hours_worked':'sum','cost':'sum'}).reset_index()
        # df_month["cost"] = df_month.groupby('season')['cost'].cumsum()
        
        # fig = go.Figure()
        # for season in df_month['season'].unique():
        #     data = df_month[df_month['season'] == season]
        #     fig.add_trace(go.Scatter(
        #         x=data['fiscal_month'],
        #         y=data['cost'],
        #         name=season,
        #         mode='lines'
        #     ))
        
        # fig.update_xaxes(
        #     tickmode='array',
        #     tickvals=list(range(1, 13)),
        #     ticktext=['Aug', 'Sep', 'Okt', 'Nov', 'Des', 'Jan', 'Feb', 'Mar', 'Apr', 'Mai', 'Jun', 'Jul']
        # )
        # st.plotly_chart(fig)

