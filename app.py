import streamlit as st
import sqlite3
import pandas as pd
import numpy as np
import altair as alt
import os
import requests

# -----------------------------------------------------------------------------
# 1. Page Configuration & Data Loader (2026-27 NFL Season Min/Max Cap Clipping WUV Engine)
# -----------------------------------------------------------------------------
st.set_page_config(page_title="NFL AI Match Predictor", page_icon="🏈", layout="wide")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "nfl_data.db")

TEAMS_DATA = {
    "Baltimore Ravens": {"tri": "BAL", "qb": {"epa_play": 0.30, "cpoe": 5.2, "rating": 106.0}, "offense": {"pbwr": 75.0, "yards_per_game": 395.0}, "defense": {"press_rate": 34.0, "pts_per_drive": 1.70}, "kicker": {"fg_50_pct": 92.0}},
    "Kansas City Chiefs": {"tri": "KC", "qb": {"epa_play": 0.28, "cpoe": 4.8, "rating": 104.5}, "offense": {"pbwr": 76.0, "yards_per_game": 385.0}, "defense": {"press_rate": 36.0, "pts_per_drive": 1.65}, "kicker": {"fg_50_pct": 89.0}},
    "San Francisco 49ers": {"tri": "SF", "qb": {"epa_play": 0.25, "cpoe": 3.8, "rating": 101.5}, "offense": {"pbwr": 74.0, "yards_per_game": 390.0}, "defense": {"press_rate": 34.0, "pts_per_drive": 1.70}, "kicker": {"fg_50_pct": 86.0}},
    "Buffalo Bills": {"tri": "BUF", "qb": {"epa_play": 0.26, "cpoe": 4.2, "rating": 102.8}, "offense": {"pbwr": 72.0, "yards_per_game": 378.0}, "defense": {"press_rate": 33.0, "pts_per_drive": 1.75}, "kicker": {"fg_50_pct": 88.0}},
    "Detroit Lions": {"tri": "DET", "qb": {"epa_play": 0.24, "cpoe": 4.0, "rating": 100.2}, "offense": {"pbwr": 77.0, "yards_per_game": 392.0}, "defense": {"press_rate": 33.0, "pts_per_drive": 1.90}, "kicker": {"fg_50_pct": 85.0}},
    "Philadelphia Eagles": {"tri": "PHI", "qb": {"epa_play": 0.22, "cpoe": 3.2, "rating": 98.5}, "offense": {"pbwr": 78.0, "yards_per_game": 382.0}, "defense": {"press_rate": 33.0, "pts_per_drive": 1.80}, "kicker": {"fg_50_pct": 87.0}},
    "Dallas Cowboys": {"tri": "DAL", "qb": {"epa_play": 0.23, "cpoe": 3.6, "rating": 99.0}, "offense": {"pbwr": 71.0, "yards_per_game": 370.0}, "defense": {"press_rate": 35.0, "pts_per_drive": 1.95}, "kicker": {"fg_50_pct": 91.0}},
    "Houston Texans": {"tri": "HOU", "qb": {"epa_play": 0.23, "cpoe": 3.5, "rating": 99.8}, "offense": {"pbwr": 70.0, "yards_per_game": 365.0}, "defense": {"press_rate": 33.0, "pts_per_drive": 1.90}, "kicker": {"fg_50_pct": 88.0}},
    "Minnesota Vikings": {"tri": "MIN", "qb": {"epa_play": 0.19, "cpoe": 2.4, "rating": 95.0}, "offense": {"pbwr": 68.0, "yards_per_game": 348.0}, "defense": {"press_rate": 37.0, "pts_per_drive": 1.80}, "kicker": {"fg_50_pct": 86.0}},
    "Cincinnati Bengals": {"tri": "CIN", "qb": {"epa_play": 0.27, "cpoe": 4.5, "rating": 103.2}, "offense": {"pbwr": 66.0, "yards_per_game": 375.0}, "defense": {"press_rate": 29.0, "pts_per_drive": 2.10}, "kicker": {"fg_50_pct": 86.0}},
    "Los Angeles Chargers": {"tri": "LAC", "qb": {"epa_play": 0.22, "cpoe": 3.1, "rating": 98.0}, "offense": {"pbwr": 69.0, "yards_per_game": 348.0}, "defense": {"press_rate": 32.0, "pts_per_drive": 1.85}, "kicker": {"fg_50_pct": 87.0}},
    "Green Bay Packers": {"tri": "GB", "qb": {"epa_play": 0.21, "cpoe": 2.8, "rating": 97.2}, "offense": {"pbwr": 73.0, "yards_per_game": 362.0}, "defense": {"press_rate": 31.0, "pts_per_drive": 1.95}, "kicker": {"fg_50_pct": 83.0}},
    "New York Jets": {"tri": "NYJ", "qb": {"epa_play": 0.20, "cpoe": 2.8, "rating": 96.0}, "offense": {"pbwr": 65.0, "yards_per_game": 340.0}, "defense": {"press_rate": 35.0, "pts_per_drive": 1.80}, "kicker": {"fg_50_pct": 84.0}},
    "Pittsburgh Steelers": {"tri": "PIT", "qb": {"epa_play": 0.17, "cpoe": 2.0, "rating": 93.8}, "offense": {"pbwr": 62.0, "yards_per_game": 330.0}, "defense": {"press_rate": 37.0, "pts_per_drive": 1.75}, "kicker": {"fg_50_pct": 90.0}},
    "Los Angeles Rams": {"tri": "LAR", "qb": {"epa_play": 0.21, "cpoe": 2.9, "rating": 97.5}, "offense": {"pbwr": 70.0, "yards_per_game": 360.0}, "defense": {"press_rate": 31.0, "pts_per_drive": 2.00}, "kicker": {"fg_50_pct": 83.0}},
    "Tampa Bay Buccaneers": {"tri": "TB", "qb": {"epa_play": 0.19, "cpoe": 2.5, "rating": 95.8}, "offense": {"pbwr": 69.0, "yards_per_game": 355.0}, "defense": {"press_rate": 30.0, "pts_per_drive": 2.00}, "kicker": {"fg_50_pct": 88.0}},
    "Miami Dolphins": {"tri": "MIA", "qb": {"epa_play": 0.20, "cpoe": 3.0, "rating": 96.5}, "offense": {"pbwr": 68.0, "yards_per_game": 372.0}, "defense": {"press_rate": 28.0, "pts_per_drive": 2.05}, "kicker": {"fg_50_pct": 85.0}},
    "Seattle Seahawks": {"tri": "SEA", "qb": {"epa_play": 0.19, "cpoe": 2.5, "rating": 95.5}, "offense": {"pbwr": 65.0, "yards_per_game": 345.0}, "defense": {"press_rate": 32.0, "pts_per_drive": 2.05}, "kicker": {"fg_50_pct": 87.0}},
    "Denver Broncos": {"tri": "DEN", "qb": {"epa_play": 0.16, "cpoe": 1.6, "rating": 91.0}, "offense": {"pbwr": 67.0, "yards_per_game": 330.0}, "defense": {"press_rate": 33.0, "pts_per_drive": 1.95}, "kicker": {"fg_50_pct": 86.0}},
    "Washington Commanders": {"tri": "WAS", "qb": {"epa_play": 0.21, "cpoe": 3.0, "rating": 97.0}, "offense": {"pbwr": 68.0, "yards_per_game": 355.0}, "defense": {"press_rate": 27.0, "pts_per_drive": 2.15}, "kicker": {"fg_50_pct": 84.0}},
    "Cleveland Browns": {"tri": "CLE", "qb": {"epa_play": 0.12, "cpoe": 0.5, "rating": 88.0}, "offense": {"pbwr": 64.0, "yards_per_game": 325.0}, "defense": {"press_rate": 36.0, "pts_per_drive": 1.85}, "kicker": {"fg_50_pct": 85.0}},
    "Atlanta Falcons": {"tri": "ATL", "qb": {"epa_play": 0.18, "cpoe": 2.2, "rating": 94.5}, "offense": {"pbwr": 71.0, "yards_per_game": 352.0}, "defense": {"press_rate": 26.0, "pts_per_drive": 2.10}, "kicker": {"fg_50_pct": 89.0}},
    "New Orleans Saints": {"tri": "NO", "qb": {"epa_play": 0.17, "cpoe": 2.0, "rating": 93.0}, "offense": {"pbwr": 64.0, "yards_per_game": 338.0}, "defense": {"press_rate": 31.0, "pts_per_drive": 2.05}, "kicker": {"fg_50_pct": 86.0}},
    "Indianapolis Colts": {"tri": "IND", "qb": {"epa_play": 0.17, "cpoe": 1.8, "rating": 92.0}, "offense": {"pbwr": 72.0, "yards_per_game": 350.0}, "defense": {"press_rate": 28.0, "pts_per_drive": 2.15}, "kicker": {"fg_50_pct": 84.0}},
    "Chicago Bears": {"tri": "CHI", "qb": {"epa_play": 0.16, "cpoe": 1.5, "rating": 91.5}, "offense": {"pbwr": 63.0, "yards_per_game": 335.0}, "defense": {"press_rate": 31.0, "pts_per_drive": 2.05}, "kicker": {"fg_50_pct": 87.0}},
    "Jacksonville Jaguars": {"tri": "JAX", "qb": {"epa_play": 0.18, "cpoe": 2.0, "rating": 94.0}, "offense": {"pbwr": 63.0, "yards_per_game": 342.0}, "defense": {"press_rate": 29.0, "pts_per_drive": 2.20}, "kicker": {"fg_50_pct": 85.0}},
    "Arizona Cardinals": {"tri": "ARI", "qb": {"epa_play": 0.18, "cpoe": 2.2, "rating": 94.0}, "offense": {"pbwr": 66.0, "yards_per_game": 340.0}, "defense": {"press_rate": 27.0, "pts_per_drive": 2.25}, "kicker": {"fg_50_pct": 88.0}},
    "Las Vegas Raiders": {"tri": "LV", "qb": {"epa_play": 0.13, "cpoe": 0.8, "rating": 89.0}, "offense": {"pbwr": 61.0, "yards_per_game": 320.0}, "defense": {"press_rate": 34.0, "pts_per_drive": 2.25}, "kicker": {"fg_50_pct": 88.0}},
    "Tennessee Titans": {"tri": "TEN", "qb": {"epa_play": 0.13, "cpoe": 0.7, "rating": 88.5}, "offense": {"pbwr": 59.0, "yards_per_game": 310.0}, "defense": {"press_rate": 30.0, "pts_per_drive": 2.30}, "kicker": {"fg_50_pct": 82.0}},
    "New York Giants": {"tri": "NYG", "qb": {"epa_play": 0.12, "cpoe": 0.5, "rating": 87.5}, "offense": {"pbwr": 57.0, "yards_per_game": 300.0}, "defense": {"press_rate": 32.0, "pts_per_drive": 2.35}, "kicker": {"fg_50_pct": 83.0}},
    "New England Patriots": {"tri": "NE", "qb": {"epa_play": 0.14, "cpoe": 1.0, "rating": 89.5}, "offense": {"pbwr": 58.0, "yards_per_game": 305.0}, "defense": {"press_rate": 27.0, "pts_per_drive": 2.20}, "kicker": {"fg_50_pct": 82.0}},
    "Carolina Panthers": {"tri": "CAR", "qb": {"epa_play": 0.10, "cpoe": -0.5, "rating": 85.0}, "offense": {"pbwr": 56.0, "yards_per_game": 290.0}, "defense": {"press_rate": 25.0, "pts_per_drive": 2.45}, "kicker": {"fg_50_pct": 84.0}}
}

def calculate_team_wuv(team_name):
    if team_name not in TEAMS_DATA:
        return 11.00
    else:
        team_info = TEAMS_DATA[team_name]
        q, o, d, k = team_info["qb"], team_info["offense"], team_info["defense"], team_info["kicker"]
        
        # Min/Max Cap Clipping WUV Engine
        # 1. QB UV: min(max(raw_qb_uv, 0.30), 2.20)
        raw_qb_starter = 1.00 + 0.15 * ((q["epa_play"] - 0.18) / 0.10) + 0.10 * ((q["cpoe"] - 2.2) / 2.5) + 0.10 * ((q["rating"] - 94.5) / 10.0)
        qb_starter = min(max(raw_qb_starter, 0.30), 2.20)
        qb_backup = 1.050
        qb_ratio = 0.95 * qb_starter + 0.05 * qb_backup
        qb_wuv = round(3.30 * qb_ratio, 2)
        
        # 2. Offense UV: min(max(raw_off_uv, 0.40), 1.80)
        raw_off_starter = 1.00 + 0.15 * ((o["pbwr"] - 67.0) / 8.0) + 0.15 * ((o["yards_per_game"] - 345.0) / 35.0)
        off_starter = min(max(raw_off_starter, 0.40), 1.80)
        raw_off_bench = 1.00 + 0.08 * ((o["pbwr"] - 67.0) / 8.0)
        off_bench = min(max(raw_off_bench, 0.40), 1.80)
        off_reserve = 0.95
        off_ratio = 0.75 * off_starter + 0.20 * off_bench + 0.05 * off_reserve
        off_wuv = round(2.75 * off_ratio, 2)
        
        # 3. Defense UV: min(max(raw_def_uv, 0.40), 1.70)
        raw_def_starter = 1.00 + 0.15 * ((d["press_rate"] - 31.0) / 5.0) + 0.15 * ((2.05 - d["pts_per_drive"]) / 0.35)
        def_starter = min(max(raw_def_starter, 0.40), 1.70)
        raw_def_bench = 1.00 + 0.08 * ((d["press_rate"] - 31.0) / 5.0)
        def_bench = min(max(raw_def_bench, 0.40), 1.70)
        def_reserve = 0.92
        def_ratio = 0.70 * def_starter + 0.25 * def_bench + 0.05 * def_reserve
        def_wuv = round(4.18 * def_ratio, 2)
        
        # 4. Kicker UV: min(max(raw_kicker_uv, 0.30), 1.60)
        raw_k_starter = 1.00 + 0.15 * ((k["fg_50_pct"] - 86.0) / 5.0)
        k_starter = min(max(raw_k_starter, 0.30), 1.60)
        k_ratio = k_starter * 1.00
        k_wuv = round(0.77 * k_ratio, 2)
        
        total_wuv = round(qb_wuv + off_wuv + def_wuv + k_wuv, 2)
        return total_wuv

def predict_matchup(home_team, away_team):
    h_wuv = round(calculate_team_wuv(home_team) + 0.25, 2) # Home Advantage +0.25
    a_wuv = round(calculate_team_wuv(away_team), 2)
    gap = round(abs(h_wuv - a_wuv), 2)
    predicted_winner = home_team if h_wuv >= a_wuv else away_team
    return predicted_winner, gap, h_wuv, a_wuv

def fetch_espn_live_data():
    records = []
    for w in range(1, 19):
        try:
            url = f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?seasontype=2&week={w}"
            res = requests.get(url, timeout=5).json()
            events = res.get("events", [])
            for e in events:
                comp = e["competitions"][0]
                status_type = e["status"]["type"]["name"]
                date_str = e["date"][:10]
                
                home_comp = comp["competitors"][0] if comp["competitors"][0]["homeAway"] == "home" else comp["competitors"][1]
                away_comp = comp["competitors"][1] if comp["competitors"][0]["homeAway"] == "home" else comp["competitors"][0]
                
                h_name = home_comp["team"]["displayName"]
                a_name = away_comp["team"]["displayName"]
                
                pw, gap, h_wuv, a_wuv = predict_matchup(h_name, a_name)
                act = ""
                if status_type == "STATUS_FINAL":
                    hs = int(home_comp.get("score", 0))
                    aws = int(away_comp.get("score", 0))
                    if hs > aws: act = h_name
                    elif aws > hs: act = a_name
                    else: act = "Tie"
                elif status_type in ["STATUS_POSTPONED", "STATUS_CANCELED"]:
                    act = "Postponed"
                    
                is_corr = 1 if (act and act != "Postponed" and act != "Tie" and pw == act) else (0 if act else None)
                
                records.append({
                    "week": w,
                    "week_name": f"Week {w}",
                    "date": date_str,
                    "home_team": h_name,
                    "visit_team": a_name,
                    "predicted_winner": pw,
                    "predicted_gap": gap,
                    "home_uv": h_wuv,
                    "visit_uv": a_wuv,
                    "actual_winner": act,
                    "is_correct": is_corr
                })
        except Exception:
            continue
    df_fresh = pd.DataFrame(records)
    if not df_fresh.empty:
        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute('DROP TABLE IF EXISTS predictions')
            c.execute('''
                CREATE TABLE predictions (
                    week INTEGER,
                    week_name TEXT,
                    date TEXT,
                    home_team TEXT,
                    visit_team TEXT,
                    predicted_winner TEXT,
                    predicted_gap REAL,
                    home_uv REAL,
                    visit_uv REAL,
                    actual_winner TEXT,
                    is_correct INTEGER
                )
            ''')
            for _, r in df_fresh.iterrows():
                c.execute('INSERT INTO predictions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                          (r['week'], r['week_name'], r['date'], r['home_team'], r['visit_team'],
                           r['predicted_winner'], r['predicted_gap'], r['home_uv'], r['visit_uv'],
                           r['actual_winner'], r['is_correct']))
            conn.commit()
            conn.close()
        except Exception:
            pass
    return df_fresh

def load_data():
    if os.path.exists(DB_PATH):
        try:
            conn = sqlite3.connect(DB_PATH)
            query = "SELECT * FROM predictions ORDER BY week ASC, date ASC, rowid ASC"
            df_db = pd.read_sql(query, conn)
            conn.close()
            if not df_db.empty:
                return df_db
        except Exception:
            pass
    return fetch_espn_live_data()

df = load_data()

# -----------------------------------------------------------------------------
# 2. Top Navigation Bar (7 Leagues)
# -----------------------------------------------------------------------------
nav_cols = st.columns(7)
with nav_cols[0]:
    st.link_button("🏀 NBA ↗", "https://nba-uv-prediction.streamlit.app/", use_container_width=True)
with nav_cols[1]:
    st.link_button("⚾ MLB ↗", "https://mlb-uv-prediction.streamlit.app/", use_container_width=True)
with nav_cols[2]:
    st.link_button("⚽ EPL ↗", "https://epl-uv-prediction.streamlit.app/", use_container_width=True)
with nav_cols[3]:
    st.link_button("⚽ La Liga ↗", "https://llg-uv-prediction.streamlit.app/", use_container_width=True)
with nav_cols[4]:
    st.link_button("🏒 NHL ↗", "https://nhl-uv-prediction.streamlit.app/", use_container_width=True)
with nav_cols[5]:
    st.button("🏈 NFL (Current)", disabled=True, use_container_width=True)
with nav_cols[6]:
    st.link_button("⚽ MLS ↗", "https://mls-uv-prediction.streamlit.app/", use_container_width=True)

st.divider()

# Main Title
st.title("🏈 NFL AI Match Predictor (by WUV predictor)")

if df.empty:
    st.warning("⚠️ Prediction data is currently unavailable.")
    st.stop()

# -----------------------------------------------------------------------------
# Accuracy & Game Index Filtering
# -----------------------------------------------------------------------------
df['total_no'] = None
valid_mask = df['actual_winner'] != 'Postponed'
df.loc[valid_mask, 'total_no'] = range(1, len(df[valid_mask]) + 1)
df['total_no'] = df['total_no'].fillna('Canceled')

stats_df = df[
    (df['actual_winner'] != 'Postponed') & 
    (df['actual_winner'].notna()) & 
    (df['actual_winner'] != '')
].copy()

# -----------------------------------------------------------------------------
# 1. Cumulative Prediction Record
# -----------------------------------------------------------------------------
st.header("📊 Cumulative Prediction Record")
total_stats = len(stats_df)
correct_total = stats_df['is_correct'].sum() if total_stats > 0 else 0

col_acc, col_track = st.columns([2, 1])

if total_stats > 0:
    total_acc = (correct_total / total_stats) * 100
    status_suffix = " (⚡ God Level, Market Distorting)" if total_acc >= 60 else ""
    
    with col_acc:
        st.subheader(f"Overall Accuracy: `{total_acc:.2f}%`{status_suffix}")
        st.markdown(f"**Correct Matches:** {int(correct_total)} / **Total Matches:** {total_stats}")
    
    with col_track:
        remaining = 100 - total_stats
        if remaining > 0:
            st.metric("Until 100-Match Validation", f"{remaining} matches left")
        else:
            st.metric("Validation Status", "Verified (God Level)")
else:
    with col_acc:
        st.subheader(f"2026-27 Regular Season Total: `{len(df)} Matches` (Week 1 ~ Week 18)")
        st.markdown(f"**Completed Matches:** {len(df)} (Real-time accuracy tracked upon match completion)")
    with col_track:
        st.metric("System Status", "Waiting for Season Kickoff")

st.markdown("---")

# -----------------------------------------------------------------------------
# 2. Weekly Prediction Record (Week 1 ~ Week 18)
# -----------------------------------------------------------------------------
st.header("📈 Weekly Prediction Record (NFL Week 1 ~ Week 18)")

if not stats_df.empty:
    weekly_stats = stats_df.groupby('week_name').agg(
        total_games=('home_team', 'count'), 
        correct_games=('is_correct', 'sum') 
    ).reset_index()

    weekly_stats['accuracy'] = (weekly_stats['correct_games'] / weekly_stats['total_games']) * 100
    
    def get_bar_color(acc):
        if acc >= 60: return '#A020F0'      # Purple (God Level)
        elif acc >= 55: return '#FF0000'    # Red (Top Expert/AI)
        elif acc >= 52.4: return '#FFA500'  # Orange (Pro/Expert)
        elif acc >= 45: return '#1E90FF'    # Blue (Average Bettor)
        elif acc >= 35: return '#008000'    # Green (Normal Fan)
        else: return '#808080'             # Gray (Do Not Bet)

    weekly_stats['bar_color'] = weekly_stats['accuracy'].apply(get_bar_color)
    weekly_stats['label_text'] = weekly_stats.apply(
        lambda x: f"{int(x['correct_games'])}/{int(x['total_games'])}", 
        axis=1
    )

    base = alt.Chart(weekly_stats).encode(x=alt.X('week_name', title='Week (NFL Week)'))
    bars = base.mark_bar().encode(
        y=alt.Y('accuracy', title='Accuracy (%)', scale=alt.Scale(domain=[0, 110])),
        color=alt.Color('bar_color', scale=None),
        tooltip=['week_name', 'accuracy', 'total_games']
    )
    text = base.mark_text(align='center', baseline='bottom', dy=-5, fontSize=14, fontWeight='bold').encode(
        y='accuracy', text='label_text'
    )
    st.altair_chart((bars + text).properties(height=350), use_container_width=True)
else:
    st.info("💡 2026-27 Regular Season Week 1~18 matches projected! (Real-time accuracy calculated as matches complete.)")

st.markdown("""
<div style="text-align: center; padding: 12px; background-color: #f0f2f6; border-radius: 10px; line-height: 1.6;">
    <span style="color: #A020F0;">●</span> <b>God Level</b> (60%↑) &nbsp;&nbsp;
    <span style="color: #FF0000;">●</span> <b>Top Expert / AI</b> (55%~60%) &nbsp;&nbsp;
    <span style="color: #FFA500;">●</span> <b>Pro / Expert</b> (52.4%~55%) &nbsp;&nbsp;
    <span style="color: #1E90FF;">●</span> <b>Average Bettor</b> (45%~52.4%) &nbsp;&nbsp;
    <span style="color: #008000;">●</span> <b>Normal Fan</b> (35%~45%) &nbsp;&nbsp;
    <span style="color: #808080;">●</span> <b>Do Not Bet</b> (35%↓)
    <br><small>* 52.4% is the statistical breakeven point.</small>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# -----------------------------------------------------------------------------
# 3. Weekly Detailed Prediction Report
# -----------------------------------------------------------------------------
st.header("📋 Weekly Detailed Prediction Report")

weeks = sorted(df['week'].unique())
week_labels = [f"Week {w} ({len(df[df['week'] == w])} matches)" for w in weeks]

selected_week_label = st.selectbox("Select Week:", week_labels, index=0)
selected_week = int(selected_week_label.split(" ")[1])

filtered_df = df[df['week'] == selected_week].copy().reset_index(drop=True)

if not filtered_df.empty:
    filtered_df['week_no'] = range(1, len(filtered_df) + 1)

    finished_games = filtered_df[
        (filtered_df['actual_winner'] != 'Postponed') & 
        (filtered_df['actual_winner'].notna()) & 
        (filtered_df['actual_winner'] != '')
    ]
    finished_count = len(finished_games)
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Matches in Week", f"{len(filtered_df)} matches")
    col2.metric("Finished Matches", f"{finished_count} matches")
    if finished_count > 0:
        acc = (finished_games['is_correct'].sum() / finished_count) * 100
        col3.metric("Weekly Accuracy", f"{acc:.1f}%")
    else:
        col3.metric("Weekly Accuracy", "-")

    display_df = filtered_df.copy()
    display_df['home_team_fmt'] = display_df.apply(
        lambda r: f"{r['home_team']} ({r['home_uv']:.2f} WUV)" if pd.notna(r.get('home_uv')) else r['home_team'], axis=1
    )
    display_df['visit_team_fmt'] = display_df.apply(
        lambda r: f"{r['visit_team']} ({r['visit_uv']:.2f} WUV)" if pd.notna(r.get('visit_uv')) else r['visit_team'], axis=1
    )
    
    show_df = display_df[[
        'week_no', 'total_no', 'date', 'home_team_fmt', 'visit_team_fmt', 
        'predicted_winner', 'predicted_gap', 'actual_winner', 'is_correct'
    ]].copy()
    
    show_df.columns = [
        'No.(Week)', 'No.(Total)', 'Date', 'Home Team', 'Away Team', 
        'Predicted Winner', 'Projected Gap (UV)', 'Actual Winner', 'Status'
    ]
    
    def mark_ox(row):
        if row['Actual Winner'] == 'Postponed': return "🆖 Canceled"
        if pd.isna(row['Status']) or row['Actual Winner'] == '': return "⏳ Pending"
        return "✅ Correct" if row['Status'] == 1 else "❌ Incorrect"
    
    show_df['Status'] = show_df.apply(mark_ox, axis=1)
    show_df['Projected Gap (UV)'] = show_df['Projected Gap (UV)'].apply(lambda x: f"{x:.2f}")
    show_df['Actual Winner'] = show_df['Actual Winner'].replace('Postponed', 'Canceled').fillna('⏳ Pending')

    st.dataframe(show_df, hide_index=True, use_container_width=True, height=600)

# -----------------------------------------------------------------------------
# 4. Footer
# -----------------------------------------------------------------------------
st.markdown("---")
st.markdown(
    """
    <div style="text-align: center; color: #888888; padding-top: 20px;">
        <p>ⓒ DROPSHOT (Business Reg: 578-81-03214)</p>
        <p>Contact us: liskhan@gmail.com</p>
    </div>
    """,
    unsafe_allow_html=True
)
