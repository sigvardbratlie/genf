import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from typing import Literal

from components import get_bigquery_module


class SeasonBase:
    def __init__(self):
        self.bq = get_bigquery_module()
        self.df = self._load_registrations()

        self.camp_rates = self.bq.load_camp_rates()
        self.rates = self._prepare_rates()

        self.filter_inactive_bool = False
        self.filter_value = 500

    def _load_registrations(self) -> pd.DataFrame:
        df = self.bq.load_registrations()
        df["gruppe"] = df["work_type"].apply(self.bq.mk_gruppe)
        df["prosjekt"] = df["work_type"].apply(self.bq.mk_prosjekt)
        return df

    def _get_camp_price_season(self, sesong: str, u18: bool = True) -> float:
        prefix = "u" if u18 else "o"
        try:
            y1, y2 = [int("20" + p) for p in sesong.split("/")]
        except Exception:
            return 0.0
        y1_price = self.camp_rates.loc[self.camp_rates["year"] == y1, f"{prefix}18_nc"].sum()
        y2_price = self.camp_rates.loc[
            self.camp_rates["year"] == y2, [f"{prefix}18_pc", f"{prefix}18_sc"]
        ].sum().sum()
        return float(y1_price + y2_price)

    def _prepare_rates(self) -> pd.DataFrame:
        raw = st.session_state.get("rates")
        if not raw:
            return pd.DataFrame()
        df = pd.DataFrame(raw) if isinstance(raw, list) else raw.copy()
        if "season" in df.columns and "sesong" not in df.columns:
            df = df.rename(columns={"season": "sesong"})
        df["camp_u18"] = df["sesong"].apply(lambda s: self._get_camp_price_season(s, u18=True))
        df["camp_o18"] = df["sesong"].apply(lambda s: self._get_camp_price_season(s, u18=False))
        return df

    def _filter_by_role(self, df: pd.DataFrame) -> pd.DataFrame:
        roles = st.session_state.get("role", [])
        return df.loc[df["role"].isin(roles)].copy() if roles else df.copy()

    def _filter_inactive(self):
        prefix = self.__class__.__name__
        self.filter_inactive_bool = st.toggle(
            "Filter Inactive Members",
            key=f"{prefix}_filter_inactive",
        )
        if self.filter_inactive_bool:
            self.filter_value = st.slider(
                "Cut-off for Inactive Members (NOK)",
                min_value=0, max_value=3000, value=500, step=100,
                key=f"{prefix}_filter_value",
            )
            st.markdown(
                f"Medlemmer som har jobbet for mindre enn {self.filter_value} kr "
                "i løpet av en sesong regnes som inaktive."
            )
        else:
            self.filter_value = 0

    def _apply_inactive_filter(self, data: pd.DataFrame) -> pd.DataFrame:
        if self.filter_inactive_bool and self.filter_value > 0:
            return data.loc[data["cost"] > self.filter_value].copy()
        return data.copy()

    def render_individual_distributions(self, data: pd.DataFrame, type: Literal["cost", "hours_worked"] = "cost", color_by: str = "season"):
        period_label = "sesong" if color_by == "season" else "år"
        label = "opptjente beløp" if type == "cost" else "arbeidede timer"
        st.markdown(f"## Fordeling av individuelle {label} per {period_label}")
        fig = px.histogram(data, x=type, nbins=50, color=color_by, barmode="overlay", opacity=0.6)
        st.plotly_chart(fig, use_container_width=True, key=f"{self.__class__.__name__}_dist_{type}")


class SeasonalReviewComponent(SeasonBase):
    def __init__(self):
        super().__init__()

    def _prepare_bar_data(self, data: pd.DataFrame) -> pd.DataFrame:
        bar_data = self._apply_inactive_filter(data)
        bar_data["goal"] = 0.0
        if self.rates.empty:
            return bar_data
        for season in self.rates["sesong"].unique():
            row = self.rates.loc[self.rates["sesong"] == season]
            if row.empty:
                continue
            u18_mask = bar_data["role"].isin(["genf", "hjelpementor"]) & (bar_data["season"] == season)
            o18_mask = (bar_data["role"] == "mentor") & (bar_data["season"] == season)
            bar_data.loc[u18_mask, "goal"] = row["camp_u18"].values[0]
            bar_data.loc[o18_mask, "goal"] = row["camp_o18"].values[0]
        return bar_data

    def render_active_members(self, bar_data: pd.DataFrame):
        st.markdown("## Opptjent vs Mål per Sesong")
        st.markdown("Sammenligning av opptjent beløp mot målbeløp per sesong")
        bar_season = bar_data.groupby("season").agg({"cost": "sum", "goal": "sum"}).reset_index()
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=bar_season["season"], y=bar_season["goal"],
            name="Mål", marker_color="indianred",
        ))
        fig.add_trace(go.Bar(
            x=bar_season["season"], y=bar_season["cost"],
            name="Opptjent", marker_color="lightsalmon",
        ))
        st.plotly_chart(fig, use_container_width=True, key="seasonal_active_members")
        st.markdown("Viser kun oppnåelse av camp-kostnader for de som har jobbet i løpet av sesongen, ikke faktiske camp-deltakere.")
        st.info("**NB**: Husk å huk av for roller i sidebar. Viser alle roller 'by default'", icon="⚙️")

    def render_goal(self, bar_data: pd.DataFrame):
        if "goal" not in bar_data.columns:
            st.warning("Mangler 'goal'-kolonne — kjør render_page for å beregne mål.")
            return
        data = bar_data.copy()
        data["difference"] = data["goal"] - data["cost"]
        st.markdown("## Histogram av Avvik fra Mål per Individ")
        st.markdown("Viser fordelingen av hvor mye hvert individ har tjent i forhold til sitt målbeløp.")
        hue = st.selectbox("Farge etter:", options=["role", "season"], index=0)
        fig = px.histogram(data, x="difference", nbins=50, color=hue, barmode="overlay", opacity=0.6)
        st.plotly_chart(fig, use_container_width=True, key="seasonal_goal_hist")

    def render_active_per_role(self, data: pd.DataFrame, active_threshold: int = 1000):
        st.markdown("## Aktive vs Registrerte Medlemmer per Rolle")
        if len(st.session_state.get("role", [])) < 3:
            st.warning("Velg alle roller i sidepanelet for å se denne visualiseringen.")
            return

        n_members = self.bq.run_query(
            "SELECT season, genf AS n_genf, hjelpementor AS n_hjelpementor, mentor AS n_mentor "
            "FROM members.seasonal_count"
        )
        active = (
            data.loc[data["cost"] > active_threshold, ["worker_name", "season", "role"]]
            .groupby(["role", "season"])
            .agg({"worker_name": "count"})
            .reset_index()
            .rename(columns={"worker_name": "active_members"})
        )
        registered_long = n_members.melt(
            id_vars="season",
            value_vars=["n_genf", "n_hjelpementor", "n_mentor"],
            var_name="role",
            value_name="registered_members",
        )
        registered_long["role"] = registered_long["role"].str.replace("n_", "", regex=False)
        result = registered_long.merge(active, on=["role", "season"], how="left").sort_values("season")

        active_pivot = active.pivot(index="season", columns="role", values="active_members").fillna(0).reset_index()
        registered_pivot = result.pivot(index="season", columns="role", values="registered_members").fillna(0).reset_index()

        colors = {"genf": "#5DADE2", "hjelpementor": "#58D68D", "mentor": "#F8B739"}
        fig = go.Figure()
        for role in ["genf", "hjelpementor", "mentor"]:
            if role in active_pivot.columns:
                fig.add_trace(go.Bar(
                    x=active_pivot["season"], y=active_pivot[role],
                    name=f"Aktiv {role}", offsetgroup="active",
                    marker_color=colors[role], opacity=0.6,
                ))
            if role in registered_pivot.columns:
                fig.add_trace(go.Bar(
                    x=registered_pivot["season"], y=registered_pivot[role],
                    name=f"Registrert {role}", offsetgroup="registered",
                    marker_color=colors[role], opacity=1.0,
                ))
        fig.update_layout(barmode="stack")
        st.plotly_chart(fig, use_container_width=True, key="seasonal_active_per_role")

    def render_page(self):
        if self.rates.empty:
            st.error("Rater ikke tilgjengelige (st.session_state.rates mangler).")
            return

        data = self._filter_by_role(self.df)
        data = (
            data.groupby(["worker_name", "season", "role"])
            .agg({"cost": "sum", "hours_worked": "sum"})
            .reset_index()
        )

        self._filter_inactive()
        bar_data = self._prepare_bar_data(data)

        self.render_active_members(bar_data)
        st.divider()
        self.render_goal(bar_data)
        st.divider()
        self.render_individual_distributions(bar_data, "cost")
        st.divider()
        self.render_individual_distributions(bar_data, "hours_worked")
        st.divider()
        self.render_active_per_role(bar_data)


class YearlyReviewComponent(SeasonBase):
    def __init__(self):
        super().__init__()
        self.members_count = self.bq.run_query("SELECT * FROM members.yearly_count")

    @staticmethod
    def _calc_year_ranges(year: int) -> tuple:
        return [year - 16, year - 14], [year - 18, year - 17]

    def _calc_n(self, year_range: list) -> int:
        return int(self.members_count.loc[
            (self.members_count["year"] >= year_range[0]) &
            (self.members_count["year"] <= year_range[1]),
            "members",
        ].sum())

    def _calc_cost_u18(self, year: int, year_range: list) -> int:
        n = self._calc_n(year_range)
        paske_sommer = n * self.camp_rates.loc[
            self.camp_rates["year"] == year, ["u18_pc", "u18_sc"]
        ].sum().sum()
        nyttaar = self._calc_n([i + 1 for i in year_range]) * self.camp_rates.loc[
            self.camp_rates["year"] == year, "u18_nc"
        ].sum()
        return int(paske_sommer + nyttaar)

    def _calc_cost_mentor(self, year: int, n: int = 50) -> int:
        return int(
            self.camp_rates.loc[
                self.camp_rates["year"] == year, ["o18_nc", "o18_sc", "o18_pc"]
            ].sum().sum() * n
        )

    def _build_camp_costs_df(self, year_from: int = 2023, year_to: int = 2026) -> pd.DataFrame:
        rows = {}
        for year in range(year_from, year_to):
            genf_range, hm_range = self._calc_year_ranges(year)
            genf = self._calc_cost_u18(year, genf_range)
            hm = self._calc_cost_u18(year, hm_range)
            mentor = self._calc_cost_mentor(year)
            rows[year] = {"genf": genf, "hjelpementor": hm, "mentor": mentor, "total": genf + hm + mentor}
        return pd.DataFrame.from_dict(rows, orient="index")

    def render_yearly_costs(self, df: pd.DataFrame):
        st.markdown("## Årlig kostnadsgjennomgang")
        st.markdown(
            "Viser totale kostnader per år, fordelt på gruppe, sammenlignet med Camp kostnader. "
            "Camp kostnader kan skjules/vises for å bedre se fordelingen blant ulike grupper."
        )
        hide_camp = st.toggle("Skjul Camp kostnader", key="yearly_hide_camp")

        df_year = (
            df.groupby([df["date_completed"].dt.year, "gruppe"])
            .agg({"hours_worked": "sum", "cost": "sum"})
            .reset_index()
        )
        df_year = df_year.loc[df_year["date_completed"] >= 2023]

        fig = go.Figure()
        for gruppe in df_year["gruppe"].unique():
            d = df_year[df_year["gruppe"] == gruppe]
            fig.add_trace(go.Bar(
                x=d["date_completed"].astype(str), y=d["cost"],
                name=gruppe, offsetgroup="1",
            ))

        if not hide_camp:
            df_costs = self._build_camp_costs_df()
            roles = [r for r in ["genf", "hjelpementor", "mentor"] if r in df_costs.columns]
            fig.add_trace(go.Bar(
                x=df_costs.index.astype(str),
                y=df_costs[roles].sum(axis=1),
                name="Camp Costs", opacity=0.7, offsetgroup="2",
            ))

        fig.update_layout(barmode="stack")
        st.plotly_chart(fig, use_container_width=True, key="yearly_costs")
        st.markdown("NB: Viser kostnader som om alle registrerte medlemmer deltok på camp, uavhengig av faktisk deltakelse.")
        st.info("**NB**: Husk å huk av for roller i sidebar. Viser alle roller 'by default'", icon="⚙️")

    def render_avg_per_year_per_role(self, data: pd.DataFrame):
        st.markdown("## Gjennomsnitt per År per Rolle")
        st.markdown("Viser gjennomsnittlig opptjent beløp og arbeidede timer per person, fordelt på år og rolle.")

        metric = st.selectbox(
            "Vis gjennomsnitt av:",
            options=["cost", "hours_worked"],
            format_func=lambda x: "Opptjent beløp (NOK)" if x == "cost" else "Arbeidede timer",
            key="yearly_avg_metric",
        )

        avg_data = (
            data.groupby(["year", "role"])
            .agg(avg=(metric, "mean"), count=("worker_name", "count"))
            .reset_index()
            .rename(columns={"avg": f"avg_{metric}"})
            .sort_values("year")
        )

        fig = px.bar(
            avg_data,
            x=avg_data["year"].astype(str),
            y=f"avg_{metric}",
            color="role",
            barmode="group",
            text=avg_data[f"avg_{metric}"].round(0).astype(int),
            labels={
                f"avg_{metric}": "Gjennomsnitt opptjent (NOK)" if metric == "cost" else "Gjennomsnitt timer",
                "x": "År",
                "role": "Rolle",
            },
        )
        fig.update_traces(textposition="outside")
        st.plotly_chart(fig, use_container_width=True, key="yearly_avg_per_year_role")

        with st.expander("Vis talldata"):
            display = avg_data.copy()
            display[f"avg_{metric}"] = display[f"avg_{metric}"].round(1)
            display.columns = ["År", "Rolle", f"Snitt {'NOK' if metric == 'cost' else 'timer'}", "Antall"]
            st.dataframe(display, use_container_width=True, hide_index=True)

    def render_cumulative_costs(self, df: pd.DataFrame):
        st.markdown("## Kumulativ lønn")
        st.markdown("Viser medlemmene har jobbet måned for måned per år")
        df = df.copy()
        df["month"] = df["date_completed"].dt.month
        df["year"] = df["date_completed"].dt.year
        df_month = df.groupby(["year", "month"]).agg({"hours_worked": "sum", "cost": "sum"}).reset_index()
        df_month["cost"] = df_month.groupby("year")["cost"].cumsum()
        fig = go.Figure()
        for year in df_month["year"].unique():
            d = df_month[df_month["year"] == year]
            fig.add_trace(go.Scatter(x=d["month"], y=d["cost"], name=str(year), mode="lines"))
        st.plotly_chart(fig, use_container_width=True, key="yearly_cumulative")

    def render_page(self):
        self._filter_inactive()

        df = self._filter_by_role(self.df)
        df = df.copy()
        df["year"] = df["date_completed"].dt.year

        # Aggregate per person+year+role for per-person metrics
        data_per_year = (
            df.groupby(["worker_name", "year", "role"])
            .agg({"cost": "sum", "hours_worked": "sum"})
            .reset_index()
        )
        data_per_year = self._apply_inactive_filter(data_per_year)

        # Re-join to original df for date-based charts (filter out inactive workers)
        active_workers = data_per_year[["worker_name", "year"]].drop_duplicates()
        df_active = df.merge(active_workers, on=["worker_name", "year"], how="inner")

        self.render_yearly_costs(df_active)
        st.divider()
        self.render_avg_per_year_per_role(data_per_year)
        st.divider()
        self.render_individual_distributions(data_per_year, "cost", color_by="year")
        st.divider()
        self.render_individual_distributions(data_per_year, "hours_worked", color_by="year")
        st.divider()
        self.render_cumulative_costs(df_active)
