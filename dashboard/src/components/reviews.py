import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import tqdm
from typing import Literal
from dashboard.components import get_supabase_module


class SeasonalReviewComponent:
    def __init__(self):
        self.filter_inactive_bool = False
        self.filter_value = 500

    
    def _filter_inactive(self,):
        self.filter_inactive_bool = st.toggle("Filter Inactive Members", value=self.filter_inactive_bool)
        if self.filter_inactive_bool:
            self.filter_value = st.slider("Cut-off for Inactive Members (NOK)", min_value=0, max_value=3000, value=self.filter_value, step=100)
            st.markdown(f"Medlemmer som har jobbet for mindre enn {self.filter_value}kr i løpet av en sesong regnes som inaktive.")
        else:
            self.filter_value = 0
    
    # ========================
    #   Filter Inactive Members
    # ========================
    def render_active_members(self, data: pd.DataFrame, prices: pd.DataFrame):
        st.markdown("## Opptjent vs Mål per Sesong")
        st.markdown("Sammenligning av opptjent beløp mot målbeløp per sesong")
        
        self._filter_inactive()
        bar_data = data.loc[data["cost"] > self.filter_value,:].copy() if self.filter_inactive_bool else data.copy()
        
        for season in prices["sesong"].unique():
            bar_data.loc[(bar_data["role"].isin(["genf","hjelpementor"])) & (bar_data["season"] == season), "goal"] = prices.loc[prices["sesong"] == season,"camp_u18"].values[0]
            bar_data.loc[(bar_data["role"].isin(["mentor"])) & (bar_data["season"] == season), "goal"] = prices.loc[prices["sesong"] == season,"camp_o18"].values[0]

        bar_seasong = bar_data.groupby("season").agg({
            "cost":"sum",
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
            y=bar_seasong["cost"],
            name='Opptjent',
            marker_color='lightsalmon'
        ))  
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("Viser kun oppnåelse av camp-kostnader for de som har jobbet i løpet av sesongen, ikke faktiske camp-deltakere.")
        st.info("**NB**: Husk å huk av for roller i sidebar. Viser alle roller 'by default'", icon="⚙️")

    def render_goal(self,data: pd.DataFrame, prices: pd.DataFrame):
        #st.dataframe(bar_data.head())
        if "goal" not in data.columns or "cost" not in data.columns:
            raise ValueError("Data må inneholde 'goal' og 'cost' kolonner for å beregne avvik.")
        
        data["difference"] = data["goal"] - data["cost"]
        st.markdown("## Histogram av Avvik fra Mål per Individ")
        st.markdown("Viser fordelingen av hvor mye hvert individ har tjent i forhold til sitt målbeløp.")
        hue = st.selectbox("Farge etter:", options=["role", "season",], index=0)
        fig = px.histogram(
                data,
                x="difference",
                nbins=50, 
                color=hue,
                barmode="overlay",  # Overlay istedenfor stack
                opacity=0.6  # Gjennomsiktig
            )
        st.plotly_chart(fig, use_container_width=True )

    def render_page():
        pass

# ========================
#   Distribution of Individual Costs
# ========================
    def render_individual_distributions(self, data: pd.DataFrame, type : Literal["cost","hours_worked"] = "cost"):
        st.markdown(f"## Fordeling av individuelle {type} per sesong")
        fig = px.histogram(
            data,
            x=type,
            nbins=50, 
            color="season",
            barmode="overlay",  # Overlay istedenfor stack
            #title="Distribution of Individual earnings per Season",
            opacity=0.6  # Gjennomsiktig
        )
        st.plotly_chart(fig, use_container_width=True)



    def render_active_per_role(self,data: pd.DataFrame, prices: pd.DataFrame):
        st.markdown("## Active vs Registered Members per Role")
        if len(st.session_state.role) < 3:
            st.warning("Select all roles to see Active vs Registered Members visualization.")
        else:
            n_members = run_query("SELECT season, genf AS n_genf, hjelpementor AS n_hjelpementor, mentor AS n_mentor FROM members.seasonal_count")
            prices = prices.merge(n_members, left_on="sesong", right_on="season", how="left")

            active = data.loc[(data["cost"]> self.filter_value),:][["worker_name","season","role"]]
            active = active.groupby(["role","season"]).agg({"worker_name":"count"})
            active = active.reset_index().rename(columns={"worker_name":"active_members"})

            prices_long = prices[["sesong","n_genf","n_hjelpementor","n_mentor"]].melt(
                id_vars="sesong",
                value_vars=["n_genf","n_hjelpementor","n_mentor"],
                var_name="role",
                value_name="registered_members"
            )

            prices_long["role"] = prices_long["role"].str.replace("n_", "")
            prices_long = prices_long.rename(columns={"sesong": "season"})
            result = prices_long.merge(active, on=["role", "season"], how="left").sort_values(by="season")

            active_pivot = active.pivot(index='season', columns='role', values='active_members').fillna(0).reset_index()
            registered_pivot = result.pivot(index='season', columns='role', values='registered_members').fillna(0).reset_index()

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


class YearlyReviewComponent:
    def __init__(self):
        self.sb = get_supabase_module()

    #========================
    #     BAR PLOT   
    #========================
    def render_yearly_costs(self, ):

        st.markdown("## Årlig kostnadsgjennomgang")
        st.markdown("Viser totale kostnader per år, fordelt på gruppe, sammenlignet med Camp kostnader.")
        st.markdown("Camp kostnader kan skjules/vises (bruk `Skjul Camp kostnader`-knappen) for å bedre se fordelingen av kostnader blant ulike grupper.")
        hide_camp = st.toggle("Skjul Camp kostnader", value=False)

        df = self.sb.load_work_logs()
        df = df.loc[df["role"].isin(st.session_state.role),:].copy() if st.session_state.role else df.copy()

        #df_filtered = df
        df_year = df_filtered.groupby([df_filtered['date_completed'].dt.year, 'gruppe']).agg({'hours_worked':'sum','cost':'sum'}).reset_index()
        df_year = df_year.loc[df_year['date_completed'] >= 2023]
        fig = go.Figure()
        for gruppe in df_year['gruppe'].unique():
            data = df_year[df_year['gruppe'] == gruppe]
            fig.add_trace(go.Bar(
                x=data['date_completed'].astype(str),
                y=data['cost'],
                name=gruppe,
                offsetgroup='1'  # Samme gruppe = stacked
            ))

        #prices = run_query("SELECT * FROM admin.rates")
        camp_prices = self.sb.run_query(table = "camp_rates")
        #members_count = self.sb.run_query(table = "yearly_count")

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
            roles = map_roles(df)['role'].unique().tolist()
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
    def render_cumulative_costs(self, df: pd.DataFrame):
        st.markdown("## Kumulativ kostnad over måneder")
        st.markdown("Viser hvordan kostnadene har akkumulert måned for måned for hvert år.")
        df["month"] = df['date_completed'].dt.month
        df["year"] = df['date_completed'].dt.year
        df_month = df.groupby(['year', 'month']).agg({'hours_worked':'sum','cost':'sum'}).reset_index()
        df_month["cost"] = df_month.groupby('year')['cost'].cumsum()
        fig = go.Figure()
        for year in df_month['year'].unique():
            data = df_month[df_month['year'] == year]
            fig.add_trace(go.Scatter(
                x=data['month'],
                y=data['cost'],
                name=str(year),
                mode='lines'
            ))
        st.plotly_chart(fig)

    def render_page(self):
        pass


