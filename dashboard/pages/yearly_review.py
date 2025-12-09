from utilities import run_query,init, sidebar_setup, load_all_seasons,map_roles
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import tqdm
from typing import Literal

def calc_year_ranges(year):
        genf_range = [year - 16,year - 14]
        hjelpementor_range = [year - 18,year - 17]
        return genf_range, hjelpementor_range
    
def calc_n(year_range):
    n = members_count.loc[(members_count["year"]>=year_range[0]) & (members_count["year"]<=year_range[1]),"members"].sum()
    return n
def calc_cost_u18(year,year_range):
    paske_sommer = calc_n(year_range) * camp_prices.loc[camp_prices['year'] == year, [f"u18_pc",f"u18_sc"]].sum().sum()
    nyttår = calc_n([i+1 for i in year_range]) * camp_prices.loc[camp_prices['year'] == year, f"u18_nc"].sum()
    return int(paske_sommer + nyttår)

def calc_cost(year, n):
    mentor_cost = n * camp_prices.loc[camp_prices['year'] == year, ["o18_nc","o18_sc","o18_pc"]].sum().sum()
    return int(mentor_cost)
    

init()
sidebar_setup(disable_datepicker=True, 
              disable_custom_datepicker=True,
              )

st.title("Yearly Review")
st.divider()

# ========================
#      Load Data
# ========================
df = load_all_seasons()
# ========================
#        BAR PLOT   
# ========================

bar_plot = st.container()
with bar_plot:
    st.markdown("## Årlig kostnadsgjennomgang")
    st.markdown("Viser totale kostnader per år, fordelt på gruppe, sammenlignet med Camp kostnader.")
    st.markdown("Camp kostnader kan skjules/vises (bruk `Skjul Camp kostnader`-knappen) for å bedre se fordelingen av kostnader blant ulike grupper.")
    hide_camp = st.toggle("Skjul Camp kostnader", value=False)

    df_filtered = map_roles(df)

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

    #prices = run_query("SELECT * FROM admin.rates")
    camp_prices = run_query("SELECT * FROM admin.camp_prices")
    members_count = run_query("SELECT * FROM members.yearly_count")

    year = 2026
    

    data_camps = {}
    for year in range(2023, 2026):
        genf_year_range, hjelpementor_year_range = calc_year_ranges(year)
        genf = calc_cost_u18(year, genf_year_range)
        hjelpementor = calc_cost_u18(year, hjelpementor_year_range)
        mentor = calc_cost(year, n= 50)
        
        #genf = calculate_camp_costs_year(year=year, role="genf",prices=prices,camp_prices=camp_prices)
        #mentor = calculate_camp_costs_year(year=year, role="mentor",prices=prices,camp_prices=camp_prices)
        #hjelpementor = calculate_camp_costs_year(year=year, role="hjelpementor",prices=prices,camp_prices=camp_prices)
        data_camps[year] = {"genf":genf, 
                            "hjelpementor":hjelpementor, 
                             "mentor":mentor,
                            "total":genf + mentor + hjelpementor}
    df_costs = pd.DataFrame.from_dict(data_camps, orient='index')


    if not hide_camp:
        roles = map_roles(df)['rolle'].unique().tolist()
        y = df_costs.drop(columns=['total']).loc[:, roles].sum(axis=1) if len(roles) >1 else df_costs.loc[:, roles[0]]
        fig.add_trace(go.Bar(
            x=df_costs.index.astype(str),   
            y=y,
            name="Camp Costs",
            opacity=0.7,
            #marker_color = 'rgba(246, 78, 139, 0.6)',
            offsetgroup='2'  # Egen gruppe = ved siden av
        ))
    fig.update_layout(barmode='stack')
    st.plotly_chart(fig)

    st.markdown("NB: Viser kostnader som om alle registrerte medlemmer deltok på camp, uavhengig av faktisk deltakelse.")
    st.info("**NB**: Husk å huk av for roller i sidebar. Viser alle roller 'by default'", icon="⚙️")



#========================
# Cumulative Cost Over Months
#========================
st.divider()
cum_cost = st.container()
with cum_cost:
    st.markdown("## Kumulativ kostnad over måneder")
    st.markdown("Viser hvordan kostnadene har akkumulert måned for måned for hvert år.")
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




    
