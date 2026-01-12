import streamlit as st
from utilities import init, run_query,fetch_job_logs
import pandas as pd
from streamlit_extras.stylable_container import stylable_container
import plotly.express as px
from datetime import datetime

init() 

st.title("GEN-F konkurranser 2025/2026!")

# ====================== 
# Team Competition Section
# ======================
tabs = st.tabs(["Konkurranse", "Leaderboard"])
with tabs[0]:
    st.markdown("## Lagkonkurranse")
    st.markdown(f"Viser for perioden 01.01.2026 - {datetime.now().strftime('%d.%m.%Y')}")

    data = fetch_job_logs()
    query = """ 
    SELECT * FROM members.teams_25_26
    """
    df_teams = run_query(query)
    query =  '''SELECT bc.first_name, bc.last_name, m.team
                FROM members.buk_cash bc
                JOIN members.teams_25_26 m USING (id)
                WHERE m.contest_role = "leader"
                '''
    df_leaders = run_query(query)
    df = pd.merge(data,df_teams[["id","team"]], left_on = "worker_id",right_on = "id",  how = "left")
    #st.dataframe(df)
    dfg = df.groupby("team").agg({"hours_worked":"sum",
                            #"kostnad":"sum"},
                            })
    avg_hours = dfg["hours_worked"].mean()
    alpha = 0.4
    colors = {
        "blue": f"rgba(59, 130, 246, {alpha})",
        "green": f"rgba(34, 197, 94, {alpha})", 
        "orange": f"rgba(249, 115, 22, {alpha})",
        "pink": f"rgba(236, 72, 153, {alpha})",
        "yellow": f"rgba(234, 179, 8, {alpha})"
    }

    # ==== BAR PLOT =====
    with st.container():
        dfg_plot = dfg.reset_index()
        fig = px.bar(dfg_plot, 
                     x='team', 
                     y='hours_worked', 
                     color='team',
                     color_discrete_map=colors,
                     labels={'team': 'Lag', 'hours_worked': 'Poeng'},
                     #title='Totale timer jobbet per lag',
                     )
        fig.add_hline(y=avg_hours, line_dash="dash", line_color="red",
                      annotation_text="Gjennomsnittlige timer",
                      annotation_position="top left")
        st.plotly_chart(fig, use_container_width=True)
    
    # ==== TEAM METRICS =====
    with st.container():
        for i in range(len(colors)):
            team_name = list(colors.keys())[i]
            hours = dfg.loc[team_name, 'hours_worked']
            delta = hours - avg_hours
            leaders = df_leaders.loc[df_leaders["team"] == team_name]
            style = f"""
                    {{background-color: {colors[team_name]};
                    padding: 20px;
                    border-radius: 10px;
                    border: 1px solid #e0e0e0;
                    }}
                    """
            with stylable_container(key=f"members_container_{team_name}",css_styles=style,):
                cols = st.columns(2)

                cols[0].metric(label="Totale Poeng", 
                          value=f"{hours:.1f} Poeng",
                          delta =f"{hours - avg_hours:.0f} poeng over gjennomsnittet" if delta > 0 else f"{hours - avg_hours:.0f} poeng under gjennomsnittet",
                          delta_color="normal")
                with cols[1]:
                    st.markdown(f"### Lag {team_name.capitalize()} - Lagledere:")
                    for idx, row in leaders.iterrows():
                        st.markdown(f"{row['first_name']} {row['last_name']}")

# ======================
# Leaderboard Section
# ======================
with tabs[1]:
    st.markdown("## Individual Leaderboard TOP 10")
    cols = st.columns(2)
    role = cols[0].pills("Rolle", options = ["GEN-F", "Mentor", "Hjelpementor"], default = ["GEN-F", "Mentor", "Hjelpementor"], selection_mode="multi")
    view_by = cols[1].radio("Vis etter", ["Timer", "Cash"], index=0, horizontal=True)
    role_map = {"GEN-F" : "genf", "Mentor": "mentor", "Hjelpementor": "hjelpementor"}
    role = ", ".join([f"'{role_map[r]}'" for r in role])
    
    # query = f"""
    #         SELECT 
    #         display_name AS Navn,
    #         rolle as Rolle,
    #         SUM(kostnad) AS Cash, 
    #         SUM(timer) AS Timer
    #         FROM `genf-446213.registrations.sesong_25_26` s
    #         JOIN members.all a ON a.email = s.epost
    #         WHERE rolle IN ({role})
    #         GROUP BY epost,rolle,a.display_name
    #         ORDER BY {view_by} DESC 
    #         LIMIT 10;"""

    query = f"""
            SELECT 
            CONCAT(a.first_name, ' ', a.last_name) AS Navn,
            s.rolle as Rolle,
            SUM(s.kostnad) AS Cash, 
            SUM(s.timer) AS Timer
            FROM `genf-446213.registrations.sesong_25_26` s
            JOIN members.buk_cash a ON a.email = s.epost
            WHERE s.rolle IN ({role})
            GROUP BY epost,s.rolle,a.first_name,a.last_name
            ORDER BY {view_by} DESC 
            LIMIT 10;"""
    
    df_leader = run_query(query).drop_duplicates(subset=["Navn"])
    df_leader.drop_duplicates(subset=["Navn"],inplace=True)
    st.divider()
    


st.markdown("""
<style>
.podium-card {
    border-radius: 20px;
    padding: 30px 20px;
    text-align: center;
    width: 100%;
    max-width: 300px;
    box-shadow: 0 8px 16px rgba(0,0,0,0.1);
    transition: transform 0.3s ease;
}
.podium-card:hover {
    transform: translateY(-5px);
}
.gold {
    background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%);
    border: 3px solid #C9B037;
}
.silver {
    background: linear-gradient(135deg, #E8E8E8 0%, #C0C0C0 100%);
    border: 3px solid #B4B4B4;
}
.bronze {
    background: linear-gradient(135deg, #E4A672 0%, #CD7F32 100%);
    border: 3px solid #A0522D;
}
.podium-card h3 {
    margin: 0 0 15px 0;
    font-size: 28px;
}
.podium-card p {
    margin: 8px 0;
    font-size: 18px;
}
</style>
""", unsafe_allow_html=True)

with st.container():
    top1 = st.columns(3)
    with top1[1]:
        st.markdown(f"""
        <div class="podium-card gold">
            <h3>🥇 1. Plass</h3>
            <p><strong>{df_leader.iloc[0]['Navn']}</strong></p>
            <p><strong>{df_leader.iloc[0][view_by]:,.0f} {'kr' if view_by == 'Cash' else 'timer'}</strong></p>
        </div>
        """, unsafe_allow_html=True)
    
    top23 = st.columns(3)
    with top23[0]:
        st.markdown(f"""
        <div class="podium-card silver">
            <h3>🥈 2. Plass</h3>
            <p><strong>{df_leader.iloc[1]['Navn']}</strong></p>
            <p><strong>{df_leader.iloc[1][view_by]:,.0f} {'kr' if view_by == 'Cash' else 'timer'}</strong></p>
        </div>
        """, unsafe_allow_html=True)
    
    with top23[2]:
        st.markdown(f"""
        <div class="podium-card bronze">
            <h3>🥉 3. Plass</h3>
            <p><strong>{df_leader.iloc[2]['Navn']}</strong></p>
            <p><strong>{df_leader.iloc[2][view_by]:,.0f} {'kr' if view_by == 'Cash' else 'timer'}</strong></p>
        </div>
        """, unsafe_allow_html=True)
    
    # with st.container():
    #     top1 = st.columns(3)
    #     top1[1].markdown("### 🥇 1. Plass")
    #     top1[1].markdown(f"**{df_leader.iloc[0]['Navn']}**")
    #     top1[1].markdown(f"**{df_leader.iloc[0][view_by]:,.0f} { 'kr' if view_by == 'Cash' else 'timer'}**")

    #     top23 = st.columns(3)
    #     top23[0].markdown("### 🥈 2. Plass")
    #     top23[0].markdown(f"**{df_leader.iloc[1]['Navn']}**")
    #     top23[0].markdown(f"**{df_leader.iloc[1][view_by]:,.0f} { 'kr' if view_by == 'Cash' else 'timer'}**")

    #     top23[2].markdown("### 🥉 3. Plass")
    #     top23[2].markdown(f"**{df_leader.iloc[2]['Navn']}**")
    #     top23[2].markdown(f"**{df_leader.iloc[2][view_by]:,.0f} { 'kr' if view_by == 'Cash' else 'timer'}**")
    
    #st.container(height=100,border=False)
    st.divider()
    show_rest = st.checkbox("Vis resten av topp 10", value=True)
    if show_rest:
        st.dataframe(
                    df_leader.iloc[3:].style.format({"Cash": "{:,.0f} kr", "Timer": "{:,.1f}"}), 
                    use_container_width=True,
                    hide_index=True  
                )