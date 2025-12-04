from utilities import init, run_query,sidebar_setup
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

init()

st.title("Seasonal Review")
sidebar_setup(disable_datepicker=True, 
              disable_rolepicker=True) 



prices = run_query("SELECT * FROM genf.priser")
camp_prices = run_query("SELECT * FROM genf.camp_priser")

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
st.dataframe(prices)

# ========================
# Camp Status Opptjent vs Mål
# ========================
opptjent = st.container()
with opptjent:
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
  FROM genf.sesong_{st.session_state.sesong.replace("/", "_")} s
  GROUP BY navn,rolle
  '''
  status = run_query(query_status)
  g = status.groupby("rolle").agg({"navn":"count","earned":"sum",}).reset_index()
  st.markdown(f"## Opptjent vs Mål per rolle for sesong {st.session_state.sesong}")
  fig = go.Figure()
  # fig.add_trace(go.Bar(
  #     x=g["rolle"],
  #     y=g["goal"],
  #     name='Mål',
  #     marker_color='indianred'
  # ))
  fig.add_trace(go.Bar(
      x=g["rolle"],
      y=g["earned"],
      name='Opptjent',
      marker_color='lightsalmon'
  ))  
  st.plotly_chart(fig, use_container_width=True)

  st.divider()
#========================
# Cost Distribution by Role
#=======================
cost_dist = st.container()
with cost_dist:
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
  data.loc[data.index == "GEN-F", "tjent"] = g.loc[g["rolle"]== "genf", "earned"].values[0]
  if "hjelpementor" in g["rolle"].values:
    data.loc[data.index == "Hjelpementor", "tjent"] = g.loc[g["rolle"]== "hjelpementor", "earned"].values[0]
  data.loc[data.index == "Mentor", "tjent"] = g.loc[g["rolle"]== "mentor", "earned"].values[0]
  data.loc[data.index == "Total", "tjent"] = g["earned"].sum()
  data = data[["Total Cost (NOK)","tjent","antall"]]

  st.markdown(f"## Fordeling av camp-kostnader for sesong {st.session_state.sesong} pr gruppe")

  st.dataframe(data.style.format({"Total Cost (NOK)" : "{:,.0f} NOK",
                                  "antall" : "{:,.0f}",
                                  "tjent" : "{:,.0f} NOK"}), 
                                  use_container_width=True)
  pie_data = data.loc[data.index != "Total","Total Cost (NOK)"]
  fig = px.pie(pie_data, 
              values="Total Cost (NOK)", 
              names=pie_data.index, 
              #title="Cost Distribution by Role",
              color_discrete_sequence=px.colors.sequential.RdBu,
              #textinfo = "label+value"
              )
  fig.update_traces(textinfo="label+value")
  st.plotly_chart(fig, use_container_width=True)

