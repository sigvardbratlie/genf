from utilities import run_query,init, sidebar_setup, load_all_seasons,map_roles,load_members
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import tqdm
from typing import Literal


    

init()
sidebar_setup(disable_datepicker=True, 
              disable_custom_datepicker=True,
              )

st.title("Seasonal Review")
st.divider()

prices = run_query("SELECT * FROM admin.rates")
camp_prices = run_query("SELECT * FROM admin.camp_prices")

def get_camp_price_season(df ,sesong : str,u18: bool = True):
    if u18:
        prefix = "u"
    else:
        prefix = "o"
    years = sesong.split("/")
    year1 = int("20" + years[0])
    year2 = int("20" + years[1])
    y1_price =  camp_prices.loc[df['year'] == year1, f"{prefix}18_nc"].sum()
    y2_price =  df.loc[df['year'] == year2, [f"{prefix}18_pc",f"{prefix}18_sc"]].sum().sum()
    price = y1_price + y2_price
    return price
prices["camp_u18"] = prices['sesong'].apply(lambda x: get_camp_price_season(df=camp_prices, sesong=x, u18=True))
prices["camp_o18"] = prices['sesong'].apply(lambda x: get_camp_price_season(df=camp_prices, sesong=x, u18=False))

# ========================
#      Load Data
# ========================


df = load_all_seasons()


data = map_roles(df)
data = data.groupby(["navn","season","rolle"]).agg({
    "kostnad":"sum",
    "timer":"sum",}).reset_index()


# ========================
#        BAR PLOT   
# ========================

with st.container():
    st.markdown("## Opptjent vs Mål per Sesong")
    st.markdown("Sammenligning av opptjent beløp mot målbeløp per sesong, fordelt på roller.")
    st.markdown("Medlemmer som har jobbet for mindre enn 1000kr i løpet av en sesong regnes som inaktive.")
    #st.divider()

# ========================
#   Filter Inactive Members
# ========================
    filter_inactive = st.toggle("Filter Inactive Members", value=False)
    
    if filter_inactive:
        bar_data = data.loc[data["kostnad"] > 1000,:].copy()
    else:
        bar_data = data.copy()
    
    for season in prices["sesong"].unique():
        bar_data.loc[(bar_data["rolle"].isin(["genf","hjelpementor"])) & (bar_data["season"] == season), "goal"] = prices.loc[prices["sesong"] == season,"camp_u18"].values[0]
        bar_data.loc[(bar_data["rolle"].isin(["mentor"])) & (bar_data["season"] == season), "goal"] = prices.loc[prices["sesong"] == season,"camp_o18"].values[0]

    bar_seasong = bar_data.groupby("season").agg({
        "kostnad":"sum",
        "goal":"sum",}).reset_index()
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=bar_seasong["season"],
        y=bar_seasong["goal"],
        name='Mål',
        marker_color='indianred'
    ))
    fig.add_trace(go.Bar(  
        x=bar_seasong["season"],
        y=bar_seasong["kostnad"],
        name='Opptjent',
        marker_color='lightsalmon'
    ))  
    st.plotly_chart(fig, use_container_width=True)


# ========================
#   Distribution of Individual Costs
# ========================
dist = st.container()
with dist:
    st.markdown("## Distribution of Individual Earnings per Season")
    fig = px.histogram(
        data.loc[data["kostnad"] > 0, :],
        x="kostnad", 
        nbins=50, 
        color="season",
        barmode="overlay",  # Overlay istedenfor stack
        #title="Distribution of Individual earnings per Season",
        opacity=0.6  # Gjennomsiktig
    )
    st.plotly_chart(fig, use_container_width=True)





#=======================
#   Active vs Registered Members per Role
#=======================
members = st.container()
with members:
    st.markdown("## Active vs Registered Members per Role")
    if len(st.session_state.role) < 3:
        st.warning("Select all roles to see Active vs Registered Members visualization.")
    else:
        n_members = run_query("SELECT season, genf AS n_genf, hjelpementor AS n_hjelpementor, mentor AS n_mentor FROM members.seasonal_count")
        prices = prices.merge(n_members, left_on="sesong", right_on="season", how="left")

        active = data.loc[(data["kostnad"]> 1000),:][["navn","season","rolle"]]
        active = active.groupby(["rolle","season"]).agg({"navn":"count"})
        active = active.reset_index().rename(columns={"navn":"active_members"})

        prices_long = prices[["sesong","n_genf","n_hjelpementor","n_mentor"]].melt(
            id_vars="sesong",
            value_vars=["n_genf","n_hjelpementor","n_mentor"],
            var_name="rolle",
            value_name="registered_members"
        )


        prices_long["rolle"] = prices_long["rolle"].str.replace("n_", "")
        prices_long = prices_long.rename(columns={"sesong": "season"})
        result = prices_long.merge(active, on=["rolle", "season"], how="left").sort_values(by="season")

        active_pivot = active.pivot(index='season', columns='rolle', values='active_members').fillna(0).reset_index()
        registered_pivot = result.pivot(index='season', columns='rolle', values='registered_members').fillna(0).reset_index()

        fig = go.Figure()

        colors = {
            'genf': '#5DADE2',
            'hjelpementor': '#58D68D', 
            'mentor': '#F8B739'
        }

        # Active bars (stacked)
        for role in ['genf', 'hjelpementor', 'mentor']:
            fig.add_trace(go.Bar(
                x=active_pivot["season"],
                y=active_pivot[role],
                name=f"Active {role}",
                offsetgroup='active',
                marker_color=colors[role],
                opacity=0.6
            ))

        # Registered bars (stacked)
        for role in ['genf', 'hjelpementor', 'mentor']:
            fig.add_trace(go.Bar(
                x=registered_pivot["season"],
                y=registered_pivot[role],
                name=f"Registered {role}",
                offsetgroup='registered',
                marker_color=colors[role],
                opacity=1.0
            ))

        fig.update_layout(barmode='stack')
        st.plotly_chart(fig, use_container_width=True)