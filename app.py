import streamlit as st
import sqlite3
import pandas as pd
import numpy as np
import altair as alt
import os
import requests

# -----------------------------------------------------------------------------
# 1. 설정 및 데이터 로드 (2026-27 NFL 정규시즌 Min/Max Cap Clipping WUV Engine)
# -----------------------------------------------------------------------------
st.set_page_config(page_title="NFL AI 승부예측", page_icon="🏈", layout="wide")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "nfl_data.db")

TRI_TO_KOR = {
    "KC": "캔ザ스시티 치프스", "BUF": "버팔로 빌스", "BAL": "볼티모어 레이븐스",
    "SF": "샌프란시스코 49어스", "DET": "디트로이트 라이온스", "PHI": "필라델피아 이글스",
    "HOU": "휴스턴 텍산스", "GB": "그린베이 패커스", "DAL": "달라스 카우보이스",
    "CIN": "신시내티 벵갈스", "MIA": "마이애미 돌핀스", "TB": "탬파베이 버커니어스",
    "LAR": "로스앤젤레스 램스", "LAC": "로스앤젤레스 차저스", "ATL": "애틀랜타 팰컨스",
    "PIT": "피츠버그 스틸러스", "CLE": "클리블랜드 브라운스", "NYJ": "뉴욕 제츠",
    "MIN": "미네소타 바이킹스", "CHI": "시카고 베어스", "JAX": "잭슨빌 재규어스",
    "IND": "인디애나폴리스 콜츠", "SEA": "시애틀 시호크스", "NO": "뉴올리언스 세인츠",
    "DEN": "덴버 브롱코스", "LV": "라스베이거스 레이더스", "ARI": "애리조나 카디널스",
    "WAS": "워싱턴 커맨더스", "NE": "뉴잉글랜드 패트리어츠", "NYG": "뉴욕 자이언츠",
    "TEN": "테네시 타이탄스", "CAR": "캐롤라이나 팬서스"
}

TEAMS_DATA = {
    "볼티모어 레이븐스": {"eng": "Baltimore Ravens", "tri": "BAL", "qb": {"epa_play": 0.30, "cpoe": 5.2, "rating": 106.0}, "offense": {"pbwr": 75.0, "yards_per_game": 395.0}, "defense": {"press_rate": 34.0, "pts_per_drive": 1.70}, "kicker": {"fg_50_pct": 92.0}},
    "캔ザ스시티 치프스": {"eng": "Kansas City Chiefs", "tri": "KC", "qb": {"epa_play": 0.28, "cpoe": 4.8, "rating": 104.5}, "offense": {"pbwr": 76.0, "yards_per_game": 385.0}, "defense": {"press_rate": 36.0, "pts_per_drive": 1.65}, "kicker": {"fg_50_pct": 89.0}},
    "샌프란시스코 49어스": {"eng": "San Francisco 49ers", "tri": "SF", "qb": {"epa_play": 0.25, "cpoe": 3.8, "rating": 101.5}, "offense": {"pbwr": 74.0, "yards_per_game": 390.0}, "defense": {"press_rate": 34.0, "pts_per_drive": 1.70}, "kicker": {"fg_50_pct": 86.0}},
    "버팔로 빌스": {"eng": "Buffalo Bills", "tri": "BUF", "qb": {"epa_play": 0.26, "cpoe": 4.2, "rating": 102.8}, "offense": {"pbwr": 72.0, "yards_per_game": 378.0}, "defense": {"press_rate": 33.0, "pts_per_drive": 1.75}, "kicker": {"fg_50_pct": 88.0}},
    "디트로이트 라이온스": {"eng": "Detroit Lions", "tri": "DET", "qb": {"epa_play": 0.24, "cpoe": 4.0, "rating": 100.2}, "offense": {"pbwr": 77.0, "yards_per_game": 392.0}, "defense": {"press_rate": 33.0, "pts_per_drive": 1.90}, "kicker": {"fg_50_pct": 85.0}},
    "필라델피아 이글스": {"eng": "Philadelphia Eagles", "tri": "PHI", "qb": {"epa_play": 0.22, "cpoe": 3.2, "rating": 98.5}, "offense": {"pbwr": 78.0, "yards_per_game": 382.0}, "defense": {"press_rate": 33.0, "pts_per_drive": 1.80}, "kicker": {"fg_50_pct": 87.0}},
    "달라스 카우보이스": {"eng": "Dallas Cowboys", "tri": "DAL", "qb": {"epa_play": 0.23, "cpoe": 3.6, "rating": 99.0}, "offense": {"pbwr": 71.0, "yards_per_game": 370.0}, "defense": {"press_rate": 35.0, "pts_per_drive": 1.95}, "kicker": {"fg_50_pct": 91.0}},
    "휴스턴 텍산스": {"eng": "Houston Texans", "tri": "HOU", "qb": {"epa_play": 0.23, "cpoe": 3.5, "rating": 99.8}, "offense": {"pbwr": 70.0, "yards_per_game": 365.0}, "defense": {"press_rate": 33.0, "pts_per_drive": 1.90}, "kicker": {"fg_50_pct": 88.0}},
    "미네소타 바이킹스": {"eng": "Minnesota Vikings", "tri": "MIN", "qb": {"epa_play": 0.19, "cpoe": 2.4, "rating": 95.0}, "offense": {"pbwr": 68.0, "yards_per_game": 348.0}, "defense": {"press_rate": 37.0, "pts_per_drive": 1.80}, "kicker": {"fg_50_pct": 86.0}},
    "신시내티 벵갈스": {"eng": "Cincinnati Bengals", "tri": "CIN", "qb": {"epa_play": 0.27, "cpoe": 4.5, "rating": 103.2}, "offense": {"pbwr": 66.0, "yards_per_game": 375.0}, "defense": {"press_rate": 29.0, "pts_per_drive": 2.10}, "kicker": {"fg_50_pct": 86.0}},
    "로스앤젤레스 차저스": {"eng": "Los Angeles Chargers", "tri": "LAC", "qb": {"epa_play": 0.22, "cpoe": 3.1, "rating": 98.0}, "offense": {"pbwr": 69.0, "yards_per_game": 348.0}, "defense": {"press_rate": 32.0, "pts_per_drive": 1.85}, "kicker": {"fg_50_pct": 87.0}},
    "그린베이 패커스": {"eng": "Green Bay Packers", "tri": "GB", "qb": {"epa_play": 0.21, "cpoe": 2.8, "rating": 97.2}, "offense": {"pbwr": 73.0, "yards_per_game": 362.0}, "defense": {"press_rate": 31.0, "pts_per_drive": 1.95}, "kicker": {"fg_50_pct": 83.0}},
    "뉴욕 제츠": {"eng": "New York Jets", "tri": "NYJ", "qb": {"epa_play": 0.20, "cpoe": 2.8, "rating": 96.0}, "offense": {"pbwr": 65.0, "yards_per_game": 340.0}, "defense": {"press_rate": 35.0, "pts_per_drive": 1.80}, "kicker": {"fg_50_pct": 84.0}},
    "피츠버그 스틸러스": {"eng": "Pittsburgh Steelers", "tri": "PIT", "qb": {"epa_play": 0.17, "cpoe": 2.0, "rating": 93.8}, "offense": {"pbwr": 62.0, "yards_per_game": 330.0}, "defense": {"press_rate": 37.0, "pts_per_drive": 1.75}, "kicker": {"fg_50_pct": 90.0}},
    "로스앤젤레스 램스": {"eng": "Los Angeles Rams", "tri": "LAR", "qb": {"epa_play": 0.21, "cpoe": 2.9, "rating": 97.5}, "offense": {"pbwr": 70.0, "yards_per_game": 360.0}, "defense": {"press_rate": 31.0, "pts_per_drive": 2.00}, "kicker": {"fg_50_pct": 83.0}},
    "탬파베이 버커니어스": {"eng": "Tampa Bay Buccaneers", "tri": "TB", "qb": {"epa_play": 0.19, "cpoe": 2.5, "rating": 95.8}, "offense": {"pbwr": 69.0, "yards_per_game": 355.0}, "defense": {"press_rate": 30.0, "pts_per_drive": 2.00}, "kicker": {"fg_50_pct": 88.0}},
    "마이애미 돌핀스": {"eng": "Miami Dolphins", "tri": "MIA", "qb": {"epa_play": 0.20, "cpoe": 3.0, "rating": 96.5}, "offense": {"pbwr": 68.0, "yards_per_game": 372.0}, "defense": {"press_rate": 28.0, "pts_per_drive": 2.05}, "kicker": {"fg_50_pct": 85.0}},
    "시애틀 시호크스": {"eng": "Seattle Seahawks", "tri": "SEA", "qb": {"epa_play": 0.19, "cpoe": 2.5, "rating": 95.5}, "offense": {"pbwr": 65.0, "yards_per_game": 345.0}, "defense": {"press_rate": 32.0, "pts_per_drive": 2.05}, "kicker": {"fg_50_pct": 87.0}},
    "덴버 브롱코스": {"eng": "Denver Broncos", "tri": "DEN", "qb": {"epa_play": 0.16, "cpoe": 1.6, "rating": 91.0}, "offense": {"pbwr": 67.0, "yards_per_game": 330.0}, "defense": {"press_rate": 33.0, "pts_per_drive": 1.95}, "kicker": {"fg_50_pct": 86.0}},
    "워싱턴 커맨더스": {"eng": "Washington Commanders", "tri": "WAS", "qb": {"epa_play": 0.21, "cpoe": 3.0, "rating": 97.0}, "offense": {"pbwr": 68.0, "yards_per_game": 355.0}, "defense": {"press_rate": 27.0, "pts_per_drive": 2.15}, "kicker": {"fg_50_pct": 84.0}},
    "클리블랜드 브라운스": {"eng": "Cleveland Browns", "tri": "CLE", "qb": {"epa_play": 0.12, "cpoe": 0.5, "rating": 88.0}, "offense": {"pbwr": 64.0, "yards_per_game": 325.0}, "defense": {"press_rate": 36.0, "pts_per_drive": 1.85}, "kicker": {"fg_50_pct": 85.0}},
    "애틀랜타 팰컨스": {"eng": "Atlanta Falcons", "tri": "ATL", "qb": {"epa_play": 0.18, "cpoe": 2.2, "rating": 94.5}, "offense": {"pbwr": 71.0, "yards_per_game": 352.0}, "defense": {"press_rate": 26.0, "pts_per_drive": 2.10}, "kicker": {"fg_50_pct": 89.0}},
    "뉴올리언스 세인츠": {"eng": "New Orleans Saints", "tri": "NO", "qb": {"epa_play": 0.17, "cpoe": 2.0, "rating": 93.0}, "offense": {"pbwr": 64.0, "yards_per_game": 338.0}, "defense": {"press_rate": 31.0, "pts_per_drive": 2.05}, "kicker": {"fg_50_pct": 86.0}},
    "인디애나폴리스 콜츠": {"eng": "Indianapolis Colts", "tri": "IND", "qb": {"epa_play": 0.17, "cpoe": 1.8, "rating": 92.0}, "offense": {"pbwr": 72.0, "yards_per_game": 350.0}, "defense": {"press_rate": 28.0, "pts_per_drive": 2.15}, "kicker": {"fg_50_pct": 84.0}},
    "시카고 베어스": {"eng": "Chicago Bears", "tri": "CHI", "qb": {"epa_play": 0.16, "cpoe": 1.5, "rating": 91.5}, "offense": {"pbwr": 63.0, "yards_per_game": 335.0}, "defense": {"press_rate": 31.0, "pts_per_drive": 2.05}, "kicker": {"fg_50_pct": 87.0}},
    "잭슨빌 재규어스": {"eng": "Jacksonville Jaguars", "tri": "JAX", "qb": {"epa_play": 0.18, "cpoe": 2.0, "rating": 94.0}, "offense": {"pbwr": 63.0, "yards_per_game": 342.0}, "defense": {"press_rate": 29.0, "pts_per_drive": 2.20}, "kicker": {"fg_50_pct": 85.0}},
    "애리조나 카디널스": {"eng": "Arizona Cardinals", "tri": "ARI", "qb": {"epa_play": 0.18, "cpoe": 2.2, "rating": 94.0}, "offense": {"pbwr": 66.0, "yards_per_game": 340.0}, "defense": {"press_rate": 27.0, "pts_per_drive": 2.25}, "kicker": {"fg_50_pct": 88.0}},
    "라스베이거스 레이더스": {"eng": "Las Vegas Raiders", "tri": "LV", "qb": {"epa_play": 0.13, "cpoe": 0.8, "rating": 89.0}, "offense": {"pbwr": 61.0, "yards_per_game": 320.0}, "defense": {"press_rate": 34.0, "pts_per_drive": 2.25}, "kicker": {"fg_50_pct": 88.0}},
    "테네시 타이탄스": {"eng": "Tennessee Titans", "tri": "TEN", "qb": {"epa_play": 0.13, "cpoe": 0.7, "rating": 88.5}, "offense": {"pbwr": 59.0, "yards_per_game": 310.0}, "defense": {"press_rate": 30.0, "pts_per_drive": 2.30}, "kicker": {"fg_50_pct": 82.0}},
    "뉴욕 자이언츠": {"eng": "New York Giants", "tri": "NYG", "qb": {"epa_play": 0.12, "cpoe": 0.5, "rating": 87.5}, "offense": {"pbwr": 57.0, "yards_per_game": 300.0}, "defense": {"press_rate": 32.0, "pts_per_drive": 2.35}, "kicker": {"fg_50_pct": 83.0}},
    "뉴잉글랜드 패트리어츠": {"eng": "New England Patriots", "tri": "NE", "qb": {"epa_play": 0.14, "cpoe": 1.0, "rating": 89.5}, "offense": {"pbwr": 58.0, "yards_per_game": 305.0}, "defense": {"press_rate": 27.0, "pts_per_drive": 2.20}, "kicker": {"fg_50_pct": 82.0}},
    "캐롤라이나 팬서스": {"eng": "Carolina Panthers", "tri": "CAR", "qb": {"epa_play": 0.10, "cpoe": -0.5, "rating": 85.0}, "offense": {"pbwr": 56.0, "yards_per_game": 290.0}, "defense": {"press_rate": 25.0, "pts_per_drive": 2.45}, "kicker": {"fg_50_pct": 84.0}}
}

def calculate_team_wuv(team_name):
    if team_name not in TEAMS_DATA:
        return 11.00
    else:
        team_info = TEAMS_DATA[team_name]
        q, o, d, k = team_info["qb"], team_info["offense"], team_info["defense"], team_info["kicker"]
        
        # [유닛별 UV 상하한선 클리핑 (Min/Max Cap Clipping Engine)]
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
    h_wuv = round(calculate_team_wuv(home_team) + 0.25, 2) # 홈 어드밴티지 +0.25
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
                
                h_tri = home_comp["team"].get("abbreviation", "")
                a_tri = away_comp["team"].get("abbreviation", "")
                
                h_name = TRI_TO_KOR.get(h_tri, home_comp["team"]["displayName"])
                a_name = TRI_TO_KOR.get(a_tri, away_comp["team"]["displayName"])
                
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
# 2. 상단 네비게이션
# -----------------------------------------------------------------------------
nav_col1, nav_col2, nav_col3, nav_col4, nav_col5 = st.columns([2, 2, 2, 2, 2])
with nav_col1:
    st.link_button(
        "🏀 NBA 대시보드 ↗", 
        "https://nba-uv-prediction-dashboard.streamlit.app/",
        use_container_width=True
    )
with nav_col2:
    st.link_button(
        "⚾ MLB 대시보드 ↗", 
        "https://mlb-uv-prediction-dashboard.streamlit.app/",
        use_container_width=True
    )
with nav_col3:
    st.link_button(
        "⚽ EPL 대시보드 ↗", 
        "https://epl-uv-prediction-dashboard.streamlit.app/",
        use_container_width=True
    )
with nav_col4:
    st.link_button(
        "🏒 NHL 대시보드 ↗", 
        "https://nhl-uv-prediction-dashboard.streamlit.app/",
        use_container_width=True
    )
with nav_col5:
    st.button(
        "🏈 NFL 대시보드 (현재)", 
        disabled=True, 
        use_container_width=True
    )

st.divider()

# 메인 타이틀
st.title("🏈 NFL AI 승부예측(by WUV predictor)")

if df.empty:
    st.warning("⚠️ 아직 예측 데이터가 없거나 DB를 불러올 수 없습니다.")
    st.stop()

# -----------------------------------------------------------------------------
# [로직] 적중률 계산 및 넘버링 필터링 (NFL Week 단위)
# -----------------------------------------------------------------------------
df['total_no'] = None
valid_mask = df['actual_winner'] != 'Postponed'
df.loc[valid_mask, 'total_no'] = range(1, len(df[valid_mask]) + 1)
df['total_no'] = df['total_no'].fillna('취소')

stats_df = df[
    (df['actual_winner'] != 'Postponed') & 
    (df['actual_winner'].notna()) & 
    (df['actual_winner'] != '')
].copy()

# -----------------------------------------------------------------------------
# 1. [상단] 누적 예측 성적표 & 100경기 트래킹
# -----------------------------------------------------------------------------
st.header("📊 누적 예측 성적표")
total_stats = len(stats_df)
correct_total = stats_df['is_correct'].sum() if total_stats > 0 else 0

col_acc, col_track = st.columns([2, 1])

if total_stats > 0:
    total_acc = (correct_total / total_stats) * 100
    status_suffix = " (⚡ 신계, 시장 왜곡급)" if total_acc >= 60 else ""
    
    with col_acc:
        st.subheader(f"전체 예측률: `{total_acc:.2f}%`{status_suffix}")
        st.markdown(f"**적중 경기 수:** {int(correct_total)} / **통산 경기 수:** {total_stats}")
    
    with col_track:
        remaining = 100 - total_stats
        if remaining > 0:
            st.metric("100경기 시스템 검증까지", f"{remaining}경기 남음")
        else:
            st.metric("시스템 검증 상태", "검증 완료 (신계 등급)")
else:
    with col_acc:
        st.subheader(f"2026-27 정규시즌 통산: `{len(df)} 경기` (Week 1 ~ Week 18)")
        st.markdown(f"**예측 완료 경기:** {len(df)} 경기 (경기 종료 후 실시간 적중률 집계)")
    with col_track:
        st.metric("시스템 상태", "2026-27 정규시즌 개막 대기 중")

st.markdown("---")

# -----------------------------------------------------------------------------
# 2. [중단] 주차별 예측 성적표 (Week 1 ~ Week 18)
# -----------------------------------------------------------------------------
st.header("📈 주차별 예측 성적표 (NFL Week 1 ~ Week 18)")

if not stats_df.empty:
    weekly_stats = stats_df.groupby('week_name').agg(
        total_games=('home_team', 'count'), 
        correct_games=('is_correct', 'sum') 
    ).reset_index()

    weekly_stats['accuracy'] = (weekly_stats['correct_games'] / weekly_stats['total_games']) * 100
    
    def get_bar_color(acc):
        if acc >= 60: return '#A020F0'      # 보라 (신계)
        elif acc >= 55: return '#FF0000'    # 빨강 (초고수/AI)
        elif acc >= 52.4: return '#FFA500'  # 주황 (프로/고수)
        elif acc >= 45: return '#1E90FF'    # 파랑 (노력하는 일반인)
        elif acc >= 35: return '#008000'    # 녹색 (지극히 정상인)
        else: return '#808080'             # 회색 (예측 금지)

    weekly_stats['bar_color'] = weekly_stats['accuracy'].apply(get_bar_color)
    weekly_stats['label_text'] = weekly_stats.apply(
        lambda x: f"{int(x['correct_games'])}/{int(x['total_games'])}", 
        axis=1
    )

    base = alt.Chart(weekly_stats).encode(x=alt.X('week_name', title='주차(NFL Week)'))
    bars = base.mark_bar().encode(
        y=alt.Y('accuracy', title='적중률(%)', scale=alt.Scale(domain=[0, 110])),
        color=alt.Color('bar_color', scale=None),
        tooltip=['week_name', 'accuracy', 'total_games']
    )
    text = base.mark_text(align='center', baseline='bottom', dy=-5, fontSize=14, fontWeight='bold').encode(
        y='accuracy', text='label_text'
    )
    st.altair_chart((bars + text).properties(height=350), use_container_width=True)
else:
    st.info("💡 2026-27 정규시즌 전체 주차(Week 1~18) 예정 경기 예측 완료! (경기가 종료되는 대로 실시간 적중률이 집계됩니다.)")

st.markdown("""
<div style="text-align: center; padding: 12px; background-color: #f0f2f6; border-radius: 10px; line-height: 1.6;">
    <span style="color: #A020F0;">●</span> <b>신계</b> (60%↑) &nbsp;&nbsp;
    <span style="color: #FF0000;">●</span> <b>초고수/AI</b> (55%~60%) &nbsp;&nbsp;
    <span style="color: #FFA500;">●</span> <b>프로/고수</b> (52.4%~55%) &nbsp;&nbsp;
    <span style="color: #1E90FF;">●</span> <b>노력하는 일반인</b> (45%~52.4%) &nbsp;&nbsp;
    <span style="color: #008000;">●</span> <b>지극히 정상인</b> (35%~45%) &nbsp;&nbsp;
    <span style="color: #808080;">●</span> <b>예측 금지</b> (35%↓)
    <br><small>* 52.4%는 통계적 손익분기점(Breakeven) 기준입니다.</small>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# -----------------------------------------------------------------------------
# 3. [하단] 주차별 상세 예측 리포트 (Week 단위 필터링 및 팀명+WUV 수치 표시)
# -----------------------------------------------------------------------------
st.header("📋 주차별 상세 예측 리포트")

weeks = sorted(df['week'].unique())
week_labels = [f"Week {w} ({len(df[df['week'] == w])}경기)" for w in weeks]

selected_week_label = st.selectbox("확인하고 싶은 주차(Week)를 선택하세요:", week_labels, index=0)
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
    col1.metric("해당 주차 총 경기 수", f"{len(filtered_df)} 경기")
    col2.metric("종료된 경기", f"{finished_count} 경기")
    if finished_count > 0:
        acc = (finished_games['is_correct'].sum() / finished_count) * 100
        col3.metric("주차 적중률", f"{acc:.1f}%")
    else:
        col3.metric("주차 적중률", "-")

    # 팀명(WUV수치) 포맷팅 예시) 볼티모어 레이븐스(13.98 WUV)
    display_df = filtered_df.copy()
    display_df['home_team_fmt'] = display_df.apply(
        lambda r: f"{r['home_team']}({r['home_uv']:.2f} WUV)" if pd.notna(r.get('home_uv')) else r['home_team'], axis=1
    )
    display_df['visit_team_fmt'] = display_df.apply(
        lambda r: f"{r['visit_team']}({r['visit_uv']:.2f} WUV)" if pd.notna(r.get('visit_uv')) else r['visit_team'], axis=1
    )
    
    show_df = display_df[[
        'week_no', 'total_no', 'date', 'home_team_fmt', 'visit_team_fmt', 
        'predicted_winner', 'predicted_gap', 'actual_winner', 'is_correct'
    ]].copy()
    
    show_df.columns = [
        'No.(Week)', 'No.(Total)', '경기 일시', '홈 팀', '원정 팀', 
        '예측 승리팀', '예상 격차(uv)', '실제 승리팀', '적중 여부'
    ]
    
    def mark_ox(row):
        if row['실제 승리팀'] == 'Postponed': return "🆖 취소"
        if pd.isna(row['적중 여부']) or row['실제 승리팀'] == '': return "⏳ 대기"
        return "✅ 정답" if row['적중 여부'] == 1 else "❌ 오답"
    
    show_df['적중 여부'] = show_df.apply(mark_ox, axis=1)
    show_df['예상 격차(uv)'] = show_df['예상 격차(uv)'].apply(lambda x: f"{x:.2f}")
    show_df['실제 승리팀'] = show_df['실제 승리팀'].replace('Postponed', '취소됨').fillna('⏳ 대기 중')

    st.dataframe(show_df, hide_index=True, use_container_width=True)

if st.button("🔄 데이터 새로고침 (ESPN 최신 경기결과 동기화)"):
    with st.spinner("ESPN 최신 경기 스코어 동기화 중..."):
        fetch_espn_live_data()
    st.rerun()

# -----------------------------------------------------------------------------
# 4. [최하단] 푸터 문구
# -----------------------------------------------------------------------------
st.markdown("---")
st.markdown(
    """
    <div style="text-align: center; color: #888888; padding-top: 20px;">
        <p>ⓒ DROPSHOT (사업자 번호: 578-81-03214)</p>
        <p>Contact us: liskhan@gmail.com</p>
    </div>
    """,
    unsafe_allow_html=True
)
