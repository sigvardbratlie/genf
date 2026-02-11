from io import BytesIO
from pdb import run
import streamlit as st
from utilities import init 
import pandas as pd
import plotly.graph_objects as go
from google.cloud import bigquery
from datetime import datetime
from dashboard.components import SidebarComponent, get_supabase_module,get_supabase_api

init()
SidebarComponent().sidebar_setup(disable_datepicker=True, disable_custom_datepicker=False)   
api = get_supabase_api()
sb = get_supabase_module()
st.title("Medlemmer")
st.divider()


# df = sb.load_members(season=st.session_state.season)
# #st.dataframe(df, use_container_width=True)
# #st.dataframe(df["birthdate"].dt.year.value_counts(), use_container_width=True)

# filters = st.columns(2)
# with filters[0]:
#     filter_inactive = st.toggle("Filter Inactive Members", value=False)
#     filter_value = st.slider("Cut-off for Inactive Members (NOK)", min_value=0, max_value=3000, value=500, step=100)

# filters[1].markdown(f"Medlemmer som har jobbet for mindre enn {filter_value}kr i løpet av en sesong regnes som inaktive.")
# data = sb.load_active_users(threshold=filter_value,)
# df["status"] = df["person_id"].apply(lambda x: "Active" if x in data["person_id"].values else "Inactive")
# if filter_inactive:
#     df = df.loc[df["status"]=="Active"].copy()
    
# # ====================
# #     MEMBERS
# # ====================
# with st.container():
#     st.markdown(f"# GEN-F & hjelpementorer")
#     st.markdown(f"## sesong {st.session_state.season}\n\n")
#     #st.divider()
#     sel_cols = st.columns(3)
#     name = sel_cols[0].multiselect("Velg navn (tom for alle)", options=df["display_name"].unique().tolist(), default=[])
#     year = sel_cols[1].multiselect("Velg fødselsår (tom for alle)", options=sorted(df["birthdate"].dt.year.unique().tolist()), default=[])
#     gender = sel_cols[2].multiselect("Velg kjønn (tom for alle)", options=df["gender"].unique().tolist(), default=[])
#     mask = pd.Series([True] * len(df), index=df.index)
#     if name:
#         mask &= df["display_name"].isin(name)
#     if year:
#         mask &= df["birthdate"].dt.year.isin(year)

#     df_filtered = df.loc[mask].copy()

#     st.dataframe(df_filtered, use_container_width=True)

# with st.container():
#     fig = go.Figure()

#     # GEN-F
#     for gender in df_filtered['gender'].unique():
#         fig.add_trace(go.Histogram(
#             x=df_filtered.loc[(df_filtered["role"] == "genf") & (df_filtered["gender"] == gender), 'birthdate'].dt.year,
#             name=f'GEN-F - {gender}',
#             legendgroup='GEN-F'
#         ))

#     # Hjelpementor
#     if int(st.session_state.season.split("/")[0]) >= 25:
#         for gender in df_filtered['gender'].unique():
#             fig.add_trace(go.Histogram(
#                 x=df_filtered.loc[(df_filtered["role"] == "hjelpementor") & (df_filtered["gender"] == gender), 'birthdate'].dt.year,
#                 name=f'Hjelpementor - {gender}',
#                 legendgroup='Hjelpementor'
#             ))

#     fig.update_layout(
#         title='Fordeling av medlemmer etter fødselsår',
#         xaxis_title='Fødselsår',
#         yaxis_title='Antall medlemmer',
#         barmode='stack',
#         bargap=0.2,
#     )
#     st.plotly_chart(fig, use_container_width=True)



    