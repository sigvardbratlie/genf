import streamlit as st
from utilities import init, run_query,fetch_job_logs
import pandas as pd

init() 

st.title("GEN-F konkurranser 2025/2026!")

# ====================== 
# Team Competition Section
# ======================
tabs = st.tabs(["Konkurranse", "Leaderboard"])
with tabs[0]:
    st.markdown("## Lagkonkurranse")

    data = fetch_job_logs()
    query = """ 
    SELECT * FROM members.teams_25_26
    """
    df_teams = run_query(query)
    df = pd.merge(data,df_teams, left_on = "worker_id",right_on = "id",  how = "left")
    st.dataframe(df)
    dfg = df.groupby("team").agg({"hours_worked":"sum",
                            #"kostnad":"sum"},
                            })
    st.dataframe(dfg)

    colors = {
        "blue": "rgba(59, 130, 246, 0.15)",
        "green": "rgba(34, 197, 94, 0.15)", 
        "orange": "rgba(249, 115, 22, 0.15)",
        "pink": "rgba(236, 72, 153, 0.15)",
        "yellow": "rgba(234, 179, 8, 0.15)"
    }

    for i in range(len(colors)):
        team_name = list(colors.keys())[i]
        st.container(border=True).markdown(
            f"""
            <div style="background-color: {colors[team_name]}; padding: 20px; border-radius: 8px;">
                <h2>TEAM {team_name.upper()}</h2>
            </div>
            """,
            unsafe_allow_html=True
        )
        st.metric(label="Totale timer", value=f"{dfg.loc[team_name, 'hours_worked']:.1f} Poeng")


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
    
    query = f"""
            SELECT 
            display_name AS Navn,
            rolle as Rolle,
            SUM(kostnad) AS Cash, 
            SUM(timer) AS Timer
            FROM `genf-446213.registrations.sesong_25_26` s
            JOIN members.all a ON a.email = s.epost
            WHERE rolle IN ({role})
            GROUP BY epost,rolle,a.display_name
            ORDER BY {view_by} DESC 
            LIMIT 10;"""
    
    df_leader = run_query(query).drop_duplicates(subset=["Navn"])
    df_leader.drop_duplicates(subset=["Navn"],inplace=True)
    st.dataframe(
                df_leader.style.format({"Cash": "{:,.0f} kr", "Timer": "{:,.1f}"}), 
                use_container_width=True,
                hide_index=True  # <-- LEGG TIL DETTE
            )