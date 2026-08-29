import streamlit as st
import sqlite3
import pandas as pd
import numpy as np
import altair as alt
import os
import requests
from datetime import datetime

# -----------------------------------------------------------------------------
# 1. 설정 및 데이터 로드
# -----------------------------------------------------------------------------
st.set_page_config(page_title="🏈 NFL AI 승부예측", page_icon="🏈", layout="wide")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "nfl_data.db")

# -----------------------------------------------------------------------------
# NFL 32개 팀 정적 지표 & 트라이코드 맵핑 (11.0 WUV 스케일 엔진)
# -----------------------------------------------------------------------------
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
    "캔ザ스시티 치프스": {
        "eng_name": "Kansas City Chiefs", "tri": "KC",
        "qb": {"name": "패트릭 마홈스 (Patrick Mahomes)", "epa_play": 0.28, "cpoe": 4.8, "rating": 104.5},
        "offense": {"name": "O-Line & 스킬 포지션", "pbwr": 76.0, "yards_per_game": 385.0},
        "defense": {"name": "수비 프런트 & DB", "press_rate": 36.0, "pts_per_drive": 1.65},
        "kicker": {"name": "해리슨 버커", "fg_50_pct": 89.0}
    },
    "버팔로 빌스": {
        "eng_name": "Buffalo Bills", "tri": "BUF",
        "qb": {"name": "조시 앨런 (Josh Allen)", "epa_play": 0.26, "cpoe": 4.2, "rating": 102.8},
        "offense": {"name": "O-Line & 스킬 포지션", "pbwr": 72.0, "yards_per_game": 378.0},
        "defense": {"name": "수비 프런트 & DB", "press_rate": 33.0, "pts_per_drive": 1.75},
        "kicker": {"name": "타일러 바스", "fg_50_pct": 88.0}
    },
    "볼티모어 레이븐스": {
        "eng_name": "Baltimore Ravens", "tri": "BAL",
        "qb": {"name": "라마 잭슨 (Lamar Jackson)", "epa_play": 0.30, "cpoe": 5.2, "rating": 106.0},
        "offense": {"name": "O-Line & 스킬 포지션", "pbwr": 75.0, "yards_per_game": 395.0},
        "defense": {"name": "수비 프런트 & DB", "press_rate": 34.0, "pts_per_drive": 1.70},
        "kicker": {"name": "저스틴 터커", "fg_50_pct": 92.0}
    },
    "샌프란시스코 49어스": {
        "eng_name": "San Francisco 49ers", "tri": "SF",
        "qb": {"name": "브록 퍼디 (Brock Purdy)", "epa_play": 0.25, "cpoe": 3.8, "rating": 101.5},
        "offense": {"name": "O-Line & 스킬 포지션", "pbwr": 74.0, "yards_per_game": 390.0},
        "defense": {"name": "수비 프런트 & DB", "press_rate": 34.0, "pts_per_drive": 1.70},
        "kicker": {"name": "제이크 무디", "fg_50_pct": 86.0}
    },
    "디트로이트 라이온스": {
        "eng_name": "Detroit Lions", "tri": "DET",
        "qb": {"name": "재러드 고프 (Jared Goff)", "epa_play": 0.24, "cpoe": 4.0, "rating": 100.2},
        "offense": {"name": "O-Line & 스킬 포지션", "pbwr": 77.0, "yards_per_game": 392.0},
        "defense": {"name": "수비 프런트 & DB", "press_rate": 33.0, "pts_per_drive": 1.90},
        "kicker": {"name": "제이크 베이츠", "fg_50_pct": 85.0}
    },
    "필라델피아 이글스": {
        "eng_name": "Philadelphia Eagles", "tri": "PHI",
        "qb": {"name": "제일런 허츠 (Jalen Hurts)", "epa_play": 0.22, "cpoe": 3.2, "rating": 98.5},
        "offense": {"name": "O-Line & 스킬 포지션", "pbwr": 78.0, "yards_per_game": 382.0},
        "defense": {"name": "수비 프런트 & DB", "press_rate": 33.0, "pts_per_drive": 1.80},
        "kicker": {"name": "제이크 엘리엇", "fg_50_pct": 87.0}
    },
    "휴스턴 텍산스": {
        "eng_name": "Houston Texans", "tri": "HOU",
        "qb": {"name": "C.J. 스트라우드 (C.J. Stroud)", "epa_play": 0.23, "cpoe": 3.5, "rating": 99.8},
        "offense": {"name": "O-Line & 스킬 포지션", "pbwr": 70.0, "yards_per_game": 365.0},
        "defense": {"name": "수비 프런트 & DB", "press_rate": 33.0, "pts_per_drive": 1.90},
        "kicker": {"name": "카이미 페어베언", "fg_50_pct": 88.0}
    },
    "그린베이 패커스": {
        "eng_name": "Green Bay Packers", "tri": "GB",
        "qb": {"name": "조던 러브 (Jordan Love)", "epa_play": 0.21, "cpoe": 2.8, "rating": 97.2},
        "offense": {"name": "O-Line & 스킬 포지션", "pbwr": 73.0, "yards_per_game": 362.0},
        "defense": {"name": "수비 프런트 & DB", "press_rate": 31.0, "pts_per_drive": 1.95},
        "kicker": {"name": "브랜든 맥매너스", "fg_50_pct": 83.0}
    },
    "달라스 카우보이스": {
        "eng_name": "Dallas Cowboys", "tri": "DAL",
        "qb": {"name": "닥 프레스캇 (Dak Prescott)", "epa_play": 0.23, "cpoe": 3.6, "rating": 99.0},
        "offense": {"name": "O-Line & 스킬 포지션", "pbwr": 71.0, "yards_per_game": 370.0},
        "defense": {"name": "수비 프런트 & DB", "press_rate": 35.0, "pts_per_drive": 1.95},
        "kicker": {"name": "브랜든 오브리", "fg_50_pct": 91.0}
    },
    "신시내티 벵갈스": {
        "eng_name": "Cincinnati Bengals", "tri": "CIN",
        "qb": {"name": "조 버로우 (Joe Burrow)", "epa_play": 0.27, "cpoe": 4.5, "rating": 103.2},
        "offense": {"name": "O-Line & 스킬 포지션", "pbwr": 66.0, "yards_per_game": 375.0},
        "defense": {"name": "수비 프런트 & DB", "press_rate": 29.0, "pts_per_drive": 2.10},
        "kicker": {"name": "에반 맥퍼슨", "fg_50_pct": 86.0}
    },
    "마이애미 돌핀스": {
        "eng_name": "Miami Dolphins", "tri": "MIA",
        "qb": {"name": "투아 타고바일로아 (Tua Tagovailoa)", "epa_play": 0.20, "cpoe": 3.0, "rating": 96.5},
        "offense": {"name": "O-Line & 스킬 포지션", "pbwr": 68.0, "yards_per_game": 372.0},
        "defense": {"name": "수비 프런트 & DB", "press_rate": 28.0, "pts_per_drive": 2.05},
        "kicker": {"name": "제이슨 샌더스", "fg_50_pct": 85.0}
    },
    "탬파베이 버커니어스": {
        "eng_name": "Tampa Bay Buccaneers", "tri": "TB",
        "qb": {"name": "베이커 메이필드 (Baker Mayfield)", "epa_play": 0.19, "cpoe": 2.5, "rating": 95.8},
        "offense": {"name": "O-Line & 스킬 포지션", "pbwr": 69.0, "yards_per_game": 355.0},
        "defense": {"name": "수비 프런트 & DB", "press_rate": 30.0, "pts_per_drive": 2.00},
        "kicker": {"name": "체이스 맥러플린", "fg_50_pct": 88.0}
    },
    "로스앤젤레스 램스": {
        "eng_name": "Los Angeles Rams", "tri": "LAR",
        "qb": {"name": "매튜 스태포드 (Matthew Stafford)", "epa_play": 0.21, "cpoe": 2.9, "rating": 97.5},
        "offense": {"name": "O-Line & 스킬 포지션", "pbwr": 70.0, "yards_per_game": 360.0},
        "defense": {"name": "수비 프런트 & DB", "press_rate": 31.0, "pts_per_drive": 2.00},
        "kicker": {"name": "조슈아 카티", "fg_50_pct": 83.0}
    },
    "로스앤젤레스 차저스": {
        "eng_name": "Los Angeles Chargers", "tri": "LAC",
        "qb": {"name": "저스틴 허버트 (Justin Herbert)", "epa_play": 0.22, "cpoe": 3.1, "rating": 98.0},
        "offense": {"name": "O-Line & 스킬 포지션", "pbwr": 69.0, "yards_per_game": 348.0},
        "defense": {"name": "수비 프런트 & DB", "press_rate": 32.0, "pts_per_drive": 1.85},
        "kicker": {"name": "카메론 디커", "fg_50_pct": 87.0}
    },
    "애틀랜타 팰컨스": {
        "eng_name": "Atlanta Falcons", "tri": "ATL",
        "qb": {"name": "커크 커즌스 (Kirk Cousins)", "epa_play": 0.18, "cpoe": 2.2, "rating": 94.5},
        "offense": {"name": "O-Line & 스킬 포지션", "pbwr": 71.0, "yards_per_game": 352.0},
        "defense": {"name": "수비 프런트 & DB", "press_rate": 26.0, "pts_per_drive": 2.10},
        "kicker": {"name": "구영회", "fg_50_pct": 89.0}
    },
    "피츠버그 스틸러스": {
        "eng_name": "Pittsburgh Steelers", "tri": "PIT",
        "qb": {"name": "러셀 윌슨 (Russell Wilson)", "epa_play": 0.17, "cpoe": 2.0, "rating": 93.8},
        "offense": {"name": "O-Line & 스킬 포지션", "pbwr": 62.0, "yards_per_game": 330.0},
        "defense": {"name": "수비 프런트 & DB", "press_rate": 37.0, "pts_per_drive": 1.75},
        "kicker": {"name": "크리스 보스웰", "fg_50_pct": 90.0}
    },
    "클리블랜드 브라운스": {
        "eng_name": "Cleveland Browns", "tri": "CLE",
        "qb": {"name": "데샤운 왓슨 (Deshaun Watson)", "epa_play": 0.12, "cpoe": 0.5, "rating": 88.0},
        "offense": {"name": "O-Line & 스킬 포지션", "pbwr": 64.0, "yards_per_game": 325.0},
        "defense": {"name": "수비 프런트 & DB", "press_rate": 36.0, "pts_per_drive": 1.85},
        "kicker": {"name": "더스틴 홉킨스", "fg_50_pct": 85.0}
    },
    "뉴욕 제츠": {
        "eng_name": "New York Jets", "tri": "NYJ",
        "qb": {"name": "아론 로저스 (Aaron Rodgers)", "epa_play": 0.20, "cpoe": 2.8, "rating": 96.0},
        "offense": {"name": "O-Line & 스킬 포지션", "pbwr": 65.0, "yards_per_game": 340.0},
        "defense": {"name": "수비 프런트 & DB", "press_rate": 35.0, "pts_per_drive": 1.80},
        "kicker": {"name": "그렉 조라인", "fg_50_pct": 84.0}
    },
    "미네소타 바이킹스": {
        "eng_name": "Minnesota Vikings", "tri": "MIN",
        "qb": {"name": "샘 다놀드 (Sam Darnold)", "epa_play": 0.19, "cpoe": 2.4, "rating": 95.0},
        "offense": {"name": "O-Line & 스킬 포지션", "pbwr": 68.0, "yards_per_game": 348.0},
        "defense": {"name": "수비 프런트 & DB", "press_rate": 37.0, "pts_per_drive": 1.80},
        "kicker": {"name": "윌 라이카드", "fg_50_pct": 86.0}
    },
    "시카고 베어스": {
        "eng_name": "Chicago Bears", "tri": "CHI",
        "qb": {"name": "케일럽 윌리엄스 (Caleb Williams)", "epa_play": 0.16, "cpoe": 1.5, "rating": 91.5},
        "offense": {"name": "O-Line & 스킬 포지션", "pbwr": 63.0, "yards_per_game": 335.0},
        "defense": {"name": "수비 프런트 & DB", "press_rate": 31.0, "pts_per_drive": 2.05},
        "kicker": {"name": "카이로 산토스", "fg_50_pct": 87.0}
    },
    "잭슨빌 재규어스": {
        "eng_name": "Jacksonville Jaguars", "tri": "JAX",
        "qb": {"name": "트레버 로렌스 (Trevor Lawrence)", "epa_play": 0.18, "cpoe": 2.0, "rating": 94.0},
        "offense": {"name": "O-Line & 스킬 포지션", "pbwr": 63.0, "yards_per_game": 342.0},
        "defense": {"name": "수비 프런트 & DB", "press_rate": 29.0, "pts_per_drive": 2.20},
        "kicker": {"name": "캠 리틀", "fg_50_pct": 85.0}
    },
    "인디애나폴리스 콜츠": {
        "eng_name": "Indianapolis Colts", "tri": "IND",
        "qb": {"name": "앤서니 리차드슨 (Anthony Richardson)", "epa_play": 0.17, "cpoe": 1.8, "rating": 92.0},
        "offense": {"name": "O-Line & 스킬 포지션", "pbwr": 72.0, "yards_per_game": 350.0},
        "defense": {"name": "수비 프런트 & DB", "press_rate": 28.0, "pts_per_drive": 2.15},
        "kicker": {"name": "매트 게이", "fg_50_pct": 84.0}
    },
    "시애틀 시호크스": {
        "eng_name": "Seattle Seahawks", "tri": "SEA",
        "qb": {"name": "지노 스미스 (Geno Smith)", "epa_play": 0.19, "cpoe": 2.5, "rating": 95.5},
        "offense": {"name": "O-Line & 스킬 포지션", "pbwr": 65.0, "yards_per_game": 345.0},
        "defense": {"name": "수비 프런트 & DB", "press_rate": 32.0, "pts_per_drive": 2.05},
        "kicker": {"name": "제이슨 마이어스", "fg_50_pct": 87.0}
    },
    "뉴올리언스 세인츠": {
        "eng_name": "New Orleans Saints", "tri": "NO",
        "qb": {"name": "데릭 카 (Derek Carr)", "epa_play": 0.17, "cpoe": 2.0, "rating": 93.0},
        "offense": {"name": "O-Line & 스킬 포지션", "pbwr": 64.0, "yards_per_game": 338.0},
        "defense": {"name": "수비 프런트 & DB", "press_rate": 31.0, "pts_per_drive": 2.05},
        "kicker": {"name": "블레이크 그루프", "fg_50_pct": 86.0}
    },
    "덴버 브롱코스": {
        "eng_name": "Denver Broncos", "tri": "DEN",
        "qb": {"name": "보 닉스 (Bo Nix)", "epa_play": 0.16, "cpoe": 1.6, "rating": 91.0},
        "offense": {"name": "O-Line & 스킬 포지션", "pbwr": 67.0, "yards_per_game": 330.0},
        "defense": {"name": "수비 프런트 & DB", "press_rate": 33.0, "pts_per_drive": 1.95},
        "kicker": {"name": "윌 룩스", "fg_50_pct": 86.0}
    },
    "라스베이거스 레이더스": {
        "eng_name": "Las Vegas Raiders", "tri": "LV",
        "qb": {"name": "가드너 민슈 (Gardner Minshew)", "epa_play": 0.13, "cpoe": 0.8, "rating": 89.0},
        "offense": {"name": "O-Line & 스킬 포지션", "pbwr": 61.0, "yards_per_game": 320.0},
        "defense": {"name": "수비 프런트 & DB", "press_rate": 34.0, "pts_per_drive": 2.25},
        "kicker": {"name": "다니엘 칼슨", "fg_50_pct": 88.0}
    },
    "애리조나 카디널스": {
        "eng_name": "Arizona Cardinals", "tri": "ARI",
        "qb": {"name": "카일러 머레이 (Kyler Murray)", "epa_play": 0.18, "cpoe": 2.2, "rating": 94.0},
        "offense": {"name": "O-Line & 스킬 포지션", "pbwr": 66.0, "yards_per_game": 340.0},
        "defense": {"name": "수비 프런트 & DB", "press_rate": 27.0, "pts_per_drive": 2.25},
        "kicker": {"name": "채드 라일랜드", "fg_50_pct": 88.0}
    },
    "워싱턴 커맨더스": {
        "eng_name": "Washington Commanders", "tri": "WAS",
        "qb": {"name": "제이든 대니얼스 (Jayden Daniels)", "epa_play": 0.21, "cpoe": 3.0, "rating": 97.0},
        "offense": {"name": "O-Line & 스킬 포지션", "pbwr": 68.0, "yards_per_game": 355.0},
        "defense": {"name": "수비 프런트 & DB", "press_rate": 27.0, "pts_per_drive": 2.15},
        "kicker": {"name": "오스틴 사이버트", "fg_50_pct": 84.0}
    },
    "뉴잉글랜드 패트리어츠": {
        "eng_name": "New England Patriots", "tri": "NE",
        "qb": {"name": "드레이크 메이 (Drake Maye)", "epa_play": 0.14, "cpoe": 1.0, "rating": 89.5},
        "offense": {"name": "O-Line & 스킬 포지션", "pbwr": 58.0, "yards_per_game": 305.0},
        "defense": {"name": "수비 프런트 & DB", "press_rate": 27.0, "pts_per_drive": 2.20},
        "kicker": {"name": "조이 슬라이", "fg_50_pct": 82.0}
    },
    "뉴욕 자이언츠": {
        "eng_name": "New York Giants", "tri": "NYG",
        "qb": {"name": "대니얼 존스 (Daniel Jones)", "epa_play": 0.12, "cpoe": 0.5, "rating": 87.5},
        "offense": {"name": "O-Line & 스킬 포지션", "pbwr": 57.0, "yards_per_game": 300.0},
        "defense": {"name": "수비 프런트 & DB", "press_rate": 32.0, "pts_per_drive": 2.35},
        "kicker": {"name": "그레이엄 가노", "fg_50_pct": 83.0}
    },
    "테네시 타이탄스": {
        "eng_name": "Tennessee Titans", "tri": "TEN",
        "qb": {"name": "윌 리비스 (Will Levis)", "epa_play": 0.13, "cpoe": 0.7, "rating": 88.5},
        "offense": {"name": "O-Line & 스킬 포지션", "pbwr": 59.0, "yards_per_game": 310.0},
        "defense": {"name": "수비 프런트 & DB", "press_rate": 30.0, "pts_per_drive": 2.30},
        "kicker": {"name": "닉 포크", "fg_50_pct": 82.0}
    },
    "캐롤라이나 팬서스": {
        "eng_name": "Carolina Panthers", "tri": "CAR",
        "qb": {"name": "브라이스 영 (Bryce Young)", "epa_play": 0.10, "cpoe": -0.5, "rating": 85.0},
        "offense": {"name": "O-Line & 스킬 포지션", "pbwr": 56.0, "yards_per_game": 290.0},
        "defense": {"name": "수비 프런트 & DB", "press_rate": 25.0, "pts_per_drive": 2.45},
        "kicker": {"name": "에디 피네이로", "fg_50_pct": 84.0}
    }
}

def calculate_team_wuv(team_name):
    if team_name not in TEAMS_DATA:
        qb_uv = 1.85
        off_uv = 1.40
        def_uv = 2.10
        k_uv = 0.40
    else:
        team_info = TEAMS_DATA[team_name]
        q = team_info["qb"]
        o = team_info["offense"]
        d = team_info["defense"]
        k = team_info["kicker"]

        q_norm = 0.40 * max(0.1, min(1.0, (q["epa_play"] + 0.10) / 0.40)) + \
                 0.30 * max(0.1, min(1.0, (q["cpoe"] + 5.0) / 11.0)) + \
                 0.30 * max(0.1, min(1.0, (q["rating"] - 75.0) / 35.0))
        qb_uv = round(3.30 * q_norm, 2)

        o_norm = 0.50 * max(0.1, min(1.0, (o["pbwr"] - 50.0) / 30.0)) + \
                 0.50 * max(0.1, min(1.0, (o["yards_per_game"] - 280.0) / 130.0))
        off_uv = round(2.75 * o_norm, 2)

        d_norm = 0.50 * max(0.1, min(1.0, (d["press_rate"] - 20.0) / 20.0)) + \
                 0.50 * max(0.1, min(1.0, (2.60 - d["pts_per_drive"]) / 1.20))
        def_uv = round(4.18 * d_norm, 2)

        k_norm = max(0.1, min(1.0, (k["fg_50_pct"] - 50.0) / 45.0))
        k_uv = round(0.77 * k_norm, 2)

    total_wuv = round(qb_uv + off_uv + def_uv + k_uv, 2)
    return total_wuv

def predict_matchup(home_team, away_team):
    h_wuv = calculate_team_wuv(home_team) + 0.25 # 홈 어드밴티지 +0.25
    a_wuv = calculate_team_wuv(away_team)
    
    gap = round(abs(h_wuv - a_wuv), 2)
    predicted_winner = home_team if h_wuv >= a_wuv else away_team
    return predicted_winner, gap, h_wuv, a_wuv

def load_data():
    if os.path.exists(DB_PATH):
        try:
            conn = sqlite3.connect(DB_PATH)
            query = "SELECT * FROM predictions ORDER BY date ASC, rowid ASC"
            df_db = pd.read_sql(query, conn)
            conn.close()
            if not df_db.empty:
                return df_db
        except Exception:
            pass

    # ESPN NFL 2026-27 정규시즌 1주차 기본 데이터 로드
    games = [
        {"date": "2026-09-10", "home_team": "시애틀 시호크스", "visit_team": "뉴잉글랜드 패트리어츠", "actual_winner": ""},
        {"date": "2026-09-11", "home_team": "로스앤젤레스 램스", "visit_team": "샌프란시스코 49어스", "actual_winner": ""},
        {"date": "2026-09-13", "home_team": "신시내티 벵갈스", "visit_team": "탬파베이 버커니어스", "actual_winner": ""},
        {"date": "2026-09-13", "home_team": "디트로이트 라이온스", "visit_team": "뉴올리언스 세인츠", "actual_winner": ""},
        {"date": "2026-09-13", "home_team": "테네시 타이탄스", "visit_team": "뉴욕 제츠", "actual_winner": ""},
        {"date": "2026-09-13", "home_team": "인디애나폴리스 콜츠", "visit_team": "마이애미 돌핀스", "actual_winner": ""},
        {"date": "2026-09-13", "home_team": "애틀랜타 팰컨스", "visit_team": "피츠버그 스틸러스", "actual_winner": ""},
        {"date": "2026-09-13", "home_team": "클리블랜드 브라운스", "visit_team": "달라스 카우보이스", "actual_winner": ""},
        {"date": "2026-09-13", "home_team": "탬파베이 버커니어스", "visit_team": "워싱턴 커맨더스", "actual_winner": ""},
        {"date": "2026-09-13", "home_team": "로스앤젤레스 차저스", "visit_team": "라스베이거스 레이더스", "actual_winner": ""},
        {"date": "2026-09-13", "home_team": "캔ザ스시티 치프스", "visit_team": "볼티모어 레이븐스", "actual_winner": ""},
        {"date": "2026-09-14", "home_team": "샌프란시스코 49어스", "visit_team": "뉴욕 자이언츠", "actual_winner": ""}
    ]

    records = []
    for g in games:
        pw, gap, h_uv, v_uv = predict_matchup(g["home_team"], g["visit_team"])
        act = g.get("actual_winner", "")
        is_corr = None
        if act and act != "Postponed":
            is_corr = 1 if pw == act else 0
            
        records.append({
            "date": g["date"],
            "home_team": g["home_team"],
            "visit_team": g["visit_team"],
            "predicted_winner": pw,
            "predicted_gap": gap,
            "home_uv": h_uv,
            "visit_uv": v_uv,
            "actual_winner": act,
            "is_correct": is_corr
        })
    return pd.DataFrame(records)

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
st.caption("11.0 WUV 기준 (QB 3.30 UV + 공격 2.75 UV + 수비 4.18 UV + 키커 0.77 UV) | 야구/라인업 (선발 QB + O-Line/스킬유닛 + 수비프런트/DB + 키커) | 홈 어드밴티지(+0.25 UV)")

if df.empty:
    st.warning("⚠️ 아직 예측 데이터가 없거나 DB를 불러올 수 없습니다.")
    st.stop()

# -----------------------------------------------------------------------------
# [로직] 적중률 계산 및 넘버링 필터링
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
        st.subheader(f"전체 예측 대상 경기: `{len(df)} 경기`")
        st.markdown(f"**예측 완료 경기:** {len(df)} 경기 (경기 종료 후 실시간 적중률 집계)")
    with col_track:
        st.metric("시스템 상태", "실시간 예측 진행 중")

st.markdown("---")

# -----------------------------------------------------------------------------
# 2. [중단] 일별 예측 성적표 (6단계 등급 및 라벨)
# -----------------------------------------------------------------------------
st.header("📈 일별 예측 성적표 (최근 7일)")

if not stats_df.empty:
    daily_stats = stats_df.groupby('date').agg(
        total_games=('home_team', 'count'), 
        correct_games=('is_correct', 'sum') 
    ).reset_index()

    daily_stats['accuracy'] = (daily_stats['correct_games'] / daily_stats['total_games']) * 100
    
    def get_bar_color(acc):
        if acc >= 60: return '#A020F0'      # 보라 (신계)
        elif acc >= 55: return '#FF0000'    # 빨강 (초고수/AI)
        elif acc >= 52.4: return '#FFA500'  # 주황 (프로/고수)
        elif acc >= 45: return '#1E90FF'    # 파랑 (노력하는 일반인)
        elif acc >= 35: return '#008000'    # 녹색 (지극히 정상인)
        else: return '#808080'             # 회색 (예측 금지)

    daily_stats['bar_color'] = daily_stats['accuracy'].apply(get_bar_color)
    daily_stats['label_text'] = daily_stats.apply(
        lambda x: f"{int(x['correct_games'])}/{int(x['total_games'])}", 
        axis=1
    )

    daily_stats_7d = daily_stats.sort_values('date', ascending=True).tail(7)

    base = alt.Chart(daily_stats_7d).encode(x=alt.X('date', title='날짜(NFL 현지)'))
    bars = base.mark_bar().encode(
        y=alt.Y('accuracy', title='적중률(%)', scale=alt.Scale(domain=[0, 110])),
        color=alt.Color('bar_color', scale=None),
        tooltip=['date', 'accuracy', 'total_games']
    )
    text = base.mark_text(align='center', baseline='bottom', dy=-5, fontSize=14, fontWeight='bold').encode(
        y='accuracy', text='label_text'
    )
    st.altair_chart((bars + text).properties(height=350), use_container_width=True)
else:
    st.info("💡 예정 경기 예측 완료! (경기가 종료되는 대로 실시간 적중률이 집계됩니다.)")

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
# 3. [하단] 일별 상세 예측 리포트
# -----------------------------------------------------------------------------
st.header("📋 일별 상세 예측 리포트")

df['date_dt'] = pd.to_datetime(df['date']).dt.date
unique_dates = sorted(df['date_dt'].unique(), reverse=True)

selected_date = st.date_input("확인하고 싶은 날짜를 선택하세요:", value=unique_dates[0])
filtered_df = df[df['date_dt'] == selected_date].copy().reset_index(drop=True)

if not filtered_df.empty:
    filtered_df['day_no'] = None
    day_valid_mask = filtered_df['actual_winner'] != 'Postponed'
    filtered_df.loc[day_valid_mask, 'day_no'] = range(1, len(filtered_df[day_valid_mask]) + 1)
    filtered_df['day_no'] = filtered_df['day_no'].fillna('취소')

    day_stats_mask = (filtered_df['actual_winner'] != 'Postponed') & (filtered_df['actual_winner'].notna()) & (filtered_df['actual_winner'] != '')
    finished_games = filtered_df[day_stats_mask]
    finished_count = len(finished_games)
    
    col1, col2, col3 = st.columns(3)
    col1.metric("해당일 총 경기 수", f"{len(filtered_df)} 경기")
    col2.metric("종료된 경기", f"{finished_count} 경기")
    if finished_count > 0:
        acc = (finished_games['is_correct'].sum() / finished_count) * 100
        col3.metric("일일 적중률", f"{acc:.1f}%")
    else:
        col3.metric("일일 적중률", "-")

    display_df = filtered_df[[
        'day_no', 'total_no', 'home_team', 'visit_team', 
        'predicted_winner', 'predicted_gap', 'actual_winner', 'is_correct'
    ]].copy()
    
    display_df.columns = [
        'No.(Day)', 'No.(Total)', '홈 팀', '원정 팀', 
        '예측 승리팀', '예상 격차(uv)', '실제 승리팀', '적중 여부'
    ]
    
    def mark_ox(row):
        if row['실제 승리팀'] == 'Postponed': return "🆖 취소"
        if pd.isna(row['적중 여부']) or row['실제 승리팀'] == '': return "⏳ 대기"
        return "✅ 정답" if row['적중 여부'] == 1 else "❌ 오답"
    
    display_df['적중 여부'] = display_df.apply(mark_ox, axis=1)
    display_df['예상 격차(uv)'] = display_df['예상 격차(uv)'].apply(lambda x: f"{x:.2f}")
    display_df['실제 승리팀'] = display_df['실제 승리팀'].replace('Postponed', '취소됨').fillna('⏳ 대기 중')

    st.dataframe(display_df, hide_index=True, use_container_width=True)

if st.button("데이터 새로고침"):
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
