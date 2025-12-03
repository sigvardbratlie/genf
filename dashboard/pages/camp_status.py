from utilities import init, run_query,sidebar_setup
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

init()

st.title("Camp status")
sidebar_setup() 

prices = run_query(f"SELECT * FROM genf.priser WHERE sesong = '{st.session_state.sesong}'")

u18 = prices[["SCU18","PCU18","NCU18"]].sum(axis = 1).values[0]
o18 = prices[["SCO18","PCO18","NCO18"]].sum(axis = 1).values[0]

prices["GEN-F"] = prices["n_genf"] *  u18
prices["Hjelpementor"] = prices["n_hjelpementor"] *  u18
prices["Mentor"] = prices["n_mentor"] *  o18
prices["Total"] = prices[["GEN-F","Hjelpementor","Mentor"]].sum(axis=1)

data = prices[["GEN-F","Hjelpementor","Mentor","Total"]].T.rename(columns={0:"Total Cost (NOK)"})
data.loc[data.index == "GEN-F", "antall"] = prices["n_genf"].values[0]
data.loc[data.index == "Hjelpementor", "antall"] = prices["n_hjelpementor"].values[0]
data.loc[data.index == "Mentor", "antall"] = prices["n_mentor"].values[0]
data.loc[data.index == "Total", "antall"] = prices[["n_genf","n_hjelpementor","n_mentor"]].sum(axis = 1).values[0]
data.loc[:, "antall"] = data["antall"].astype(int,errors="ignore")
st.dataframe(data.style.format({"Total Cost (NOK)" : "{:,.0f} NOK",
                                "antall" : "{:,.0f}"}), use_container_width=True)
pie_data = data.loc[data.index != "Total","Total Cost (NOK)"]
fig = px.pie(pie_data, 
             values="Total Cost (NOK)", 
             names=pie_data.index, 
             title="Cost Distribution by Role",
             color_discrete_sequence=px.colors.sequential.RdBu,
             #textinfo = "label+value"
             )
fig.update_traces(textinfo="label+value")
st.plotly_chart(fig, use_container_width=True)

query_status = f'''
WITH pris AS (
  SELECT *
  FROM genf.priser
  WHERE sesong = "{st.session_state.sesong}"
)
SELECT 
  navn,
  rolle,
  SUM(s.kostnad) AS earned,
  CASE
    WHEN s.rolle IN ("genf", "hjelpementor") 
      THEN (SELECT p.PCU18 + p.SCU18 + p.NCU18 FROM pris p)
    ELSE 
      (SELECT p.PCO18 + p.SCO18 + p.NCO18 FROM pris p)
  END AS goal
FROM genf.sesong_{st.session_state.sesong.replace("/", "_")} s
GROUP BY navn,rolle
'''

status = run_query(query_status)
g = status.groupby("rolle").agg({"navn":"count","earned":"sum","goal":"sum"}).reset_index()

fig = go.Figure()
fig.add_trace(go.Bar(
    x=g["rolle"],
    y=g["goal"],
    name='Mål',
    marker_color='indianred'
))
fig.add_trace(go.Bar(
    x=g["rolle"],
    y=g["earned"],
    name='Opptjent',
    marker_color='lightsalmon'
))  
st.plotly_chart(fig, use_container_width=True)