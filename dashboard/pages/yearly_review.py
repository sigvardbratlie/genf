from utilities import run_query,init, sidebar_setup
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import tqdm
from typing import Literal

def calculate_camp_costs_year(year : int, prices, camp_prices, role : Literal["genf","mentor","hjelpementor"] = "genf"):
    if role == "genf":
        prefix = "u"
    elif role == "hjelpementor":
        prefix = "u"
    else:
        prefix = "o"
    short_year = int(str(year).replace("20", ""))
    
    try:
        part1  = int(prices.loc[prices["sesong"] == f"{short_year-1}/{short_year}", f"n_{role}"] * camp_prices.loc[camp_prices['year'] == year, f"{prefix}18_nc"].sum())
    except:
        part1 = 0
    
    try:
        part2 =  int(prices.loc[prices["sesong"] == f"{short_year}/{short_year+1}", f"n_{role}"] * camp_prices.loc[camp_prices['year'] == year, [f"{prefix}18_sc",f"{prefix}18_pc"]].sum().sum()) 
    except:
        part2 = 0
    
    return int(part1) + int(part2)
    

init()
sidebar_setup(disable_datepicker=True, disable_seasonpicker=True)

st.title("Yearly Review")
st.divider()

# ========================
#      Load Data
# ========================
tables = ["sesong_22_23","sesong_23_24","sesong_24_25","sesong_25_26",]
dfs = []
for table in tqdm.tqdm(tables):
    df = run_query(f"SELECT * FROM genf.{table}",spinner_message=f"Loading {table}...")
    dfs.append(df)
df = pd.concat(dfs, ignore_index=True)
df['dato'] = pd.to_datetime(df['dato'], utc=True)
#df = df.loc[df["dato"].dt.year >= 2023]
df.sort_values(by = "dato", inplace=True)


# ========================
#        BAR PLOT   
# ========================

bar_plot = st.container()
with bar_plot:
    st.markdown("## Yearly Cost Review")
    
    hide_camp = st.toggle("Hide Camp Costs", value=False)

    map_role = {"GEN-F":"genf","Hjelpementor":"hjelpementor","Mentor":"mentor"}
    roles = [map_role[role] for role in st.session_state.role if role in map_role]
    df_filtered = df.loc[df["rolle"].isin(roles) | df["rolle"].isna()].copy()

    #df_filtered = df
    df_year = df_filtered.groupby([df_filtered['dato'].dt.year, 'gruppe']).agg({'timer':'sum','kostnad':'sum'}).reset_index()
    df_year = df_year.loc[df_year['dato'] >= 2023]
    fig = go.Figure()
    for gruppe in df_year['gruppe'].unique():
        data = df_year[df_year['gruppe'] == gruppe]
        fig.add_trace(go.Bar(
            x=data['dato'].astype(str),
            y=data['kostnad'],
            name=gruppe,
            offsetgroup='1'  # Samme gruppe = stacked
        ))

    prices = run_query("SELECT * FROM genf.priser")
    camp_prices = run_query("SELECT * FROM genf.camp_priser")

    data_camps = {}
    for year in range(2023, 2026):
        genf = calculate_camp_costs_year(year=year, role="genf",prices=prices,camp_prices=camp_prices)
        mentor = calculate_camp_costs_year(year=year, role="mentor",prices=prices,camp_prices=camp_prices)
        hjelpementor = calculate_camp_costs_year(year=year, role="hjelpementor",prices=prices,camp_prices=camp_prices)
        data_camps[year] = {"genf":genf, "mentor":mentor, "hjelpementor":hjelpementor, "total":genf + mentor + hjelpementor}
    df_costs = pd.DataFrame.from_dict(data_camps, orient='index')


    if not hide_camp:
        y = df_costs.drop(columns=['total']).loc[:, roles].sum(axis=1) if len(roles) >1 else df_costs.loc[:, roles[0]]
        fig.add_trace(go.Bar(
            x=df_costs.index.astype(str),   
            y=y,
            name="Camp Costs",
            offsetgroup='2'  # Egen gruppe = ved siden av
        ))
    fig.update_layout(barmode='stack')
    st.plotly_chart(fig)




#========================
# Cumulative Cost Over Months
#========================
cum_cost = st.container()
with cum_cost:
    df["month"] = df['dato'].dt.month
    df["year"] = df['dato'].dt.year
    df_month = df.groupby(['year', 'month']).agg({'timer':'sum','kostnad':'sum'}).reset_index()
    df_month["kostnad"] = df_month.groupby('year')['kostnad'].cumsum()
    fig = go.Figure()
    for year in df_month['year'].unique():
        data = df_month[df_month['year'] == year]
        fig.add_trace(go.Scatter(
            x=data['month'],
            y=data['kostnad'],
            name=str(year),
            mode='lines'
        ))
    st.plotly_chart(fig)




    
