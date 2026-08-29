import streamlit as st
import sqlite3
import pandas as pd
import numpy as np
import altair as alt
import plotly.graph_objects as go
import os
import requests
import textwrap
from datetime import datetime

# -----------------------------------------------------------------------------
# 1. 페이지 설정 및 상단 탭 네비게이션
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="🏈 NFL AI 승부예측 (2026-27 시즌)",
    page_icon="🏈",
    layout="wide",
    initial_sidebar_state="expanded"
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "nfl_data.db")

# 상단 5대 종목 네비게이션 헤더 (동일 너비 use_container_width=True 적용)
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

# 메인 타이틀 및 스펙 설명
st.title("🏈 NFL AI 승부예측 (2026-27 시즌 by 11.0 WUV predictor)")
st.caption("2026-27 NFL 정규시즌 (2026년 9월 10일 개막) | 11.0 WUV 기준 (QB 3.30 UV + 공격 2.75 UV + 수비 4.18 UV + 키커 0.77 UV) | 홈 어드밴티지(+0.25 UV)")

# Custom CSS
st.markdown(textwrap.dedent("""
<style>
    .match-card {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 18px;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
    }
    .team-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 12px;
    }
    .team-box {
        text-align: center;
        width: 42%;
    }
    .team-logo {
        width: 54px;
        height: 54px;
        object-fit: contain;
    }
    .team-name {
        font-weight: 700;
        font-size: 1.05rem;
        margin-top: 4px;
    }
    .uv-score {
        font-size: 1.25rem;
        font-weight: 800;
        color: #1e3a8a;
    }
    .vs-badge {
        font-size: 0.85rem;
        font-weight: 800;
        color: #64748b;
        background: #f1f5f9;
        padding: 4px 10px;
        border-radius: 20px;
    }
    .qb-box {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 10px;
        font-size: 0.85rem;
        margin-top: 10px;
    }
    .pick-badge {
        background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 100%);
        color: white;
        padding: 8px 14px;
        border-radius: 8px;
        font-weight: 700;
        text-align: center;
        margin-top: 12px;
        font-size: 0.92rem;
    }
    .prob-bar-container {
        display: flex;
        height: 22px;
        border-radius: 11px;
        overflow: hidden;
        margin-top: 10px;
        font-weight: bold;
        font-size: 0.78rem;
        color: white;
    }
    .prob-home {
        background-color: #dc2626;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .prob-away {
        background-color: #2563eb;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .season-badge {
        background-color: #0284c7;
        color: white;
        font-size: 0.82rem;
        font-weight: bold;
        padding: 6px 12px;
        border-radius: 6px;
        display: inline-block;
        margin-bottom: 14px;
    }
</style>
"""), unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. NFL 32개 팀 정적 지표 & 트라이코드 맵핑 (2026-27 시즌 11.0 WUV 스케일)
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
        "offense": {"name": "O-Line & 스킬 포지션 (켈시, 워디, 파체코)", "pbwr": 76.0, "yards_per_game": 385.0},
        "defense": {"name": "수비 프런트 & DB (존스, 맥더피)", "press_rate": 36.0, "pts_per_drive": 1.65},
        "kicker": {"name": "해리슨 버커 (Harrison Butker)", "fg_50_pct": 89.0}
    },
    "버팔로 빌스": {
        "eng_name": "Buffalo Bills", "tri": "BUF",
        "qb": {"name": "조시 앨런 (Josh Allen)", "epa_play": 0.26, "cpoe": 4.2, "rating": 102.8},
        "offense": {"name": "O-Line & 스킬 포지션 (샤키르, 쿡, 노크스)", "pbwr": 72.0, "yards_per_game": 378.0},
        "defense": {"name": "수비 프런트 & DB (밀러, 루소, 밀라노)", "press_rate": 33.0, "pts_per_drive": 1.75},
        "kicker": {"name": "타일러 바스 (Tyler Bass)", "fg_50_pct": 88.0}
    },
    "볼티모어 레이븐스": {
        "eng_name": "Baltimore Ravens", "tri": "BAL",
        "qb": {"name": "라마 잭슨 (Lamar Jackson)", "epa_play": 0.30, "cpoe": 5.2, "rating": 106.0},
        "offense": {"name": "O-Line & 스킬 포지션 (헨리, 플라워스, 앤드루스)", "pbwr": 75.0, "yards_per_game": 395.0},
        "defense": {"name": "수비 프런트 & DB (스미스, 해밀턴, 매더비케)", "press_rate": 34.0, "pts_per_drive": 1.70},
        "kicker": {"name": "저스틴 터커 (Justin Tucker)", "fg_50_pct": 92.0}
    },
    "샌프란시스코 49어스": {
        "eng_name": "San Francisco 49ers", "tri": "SF",
        "qb": {"name": "브록 퍼디 (Brock Purdy)", "epa_play": 0.25, "cpoe": 3.8, "rating": 101.5},
        "offense": {"name": "O-Line & 스킬 포지션 (맥캐프리, 사무엘, 키틀)", "pbwr": 74.0, "yards_per_game": 390.0},
        "defense": {"name": "수비 프런트 & DB (보사, 워너, 윌리엄스)", "press_rate": 34.0, "pts_per_drive": 1.70},
        "kicker": {"name": "제이크 무디 (Jake Moody)", "fg_50_pct": 86.0}
    },
    "디트로이트 라이온스": {
        "eng_name": "Detroit Lions", "tri": "DET",
        "qb": {"name": "재러드 고프 (Jared Goff)", "epa_play": 0.24, "cpoe": 4.0, "rating": 100.2},
        "offense": {"name": "O-Line & 스킬 포지션 (세인트브라운, 깁스, 라포타)", "pbwr": 77.0, "yards_per_game": 392.0},
        "defense": {"name": "수비 프런트 & DB (허친슨, 캠벨, 아놀드)", "press_rate": 33.0, "pts_per_drive": 1.90},
        "kicker": {"name": "제이크 베이츠 (Jake Bates)", "fg_50_pct": 85.0}
    },
    "필라델피아 이글스": {
        "eng_name": "Philadelphia Eagles", "tri": "PHI",
        "qb": {"name": "제일런 허츠 (Jalen Hurts)", "epa_play": 0.22, "cpoe": 3.2, "rating": 98.5},
        "offense": {"name": "O-Line & 스킬 포지션 (바클리, 브라운, 스미스)", "pbwr": 78.0, "yards_per_game": 382.0},
        "defense": {"name": "수비 프런트 & DB (카터, 그래함, 미첼)", "press_rate": 33.0, "pts_per_drive": 1.80},
        "kicker": {"name": "제이크 엘리엇 (Jake Elliott)", "fg_50_pct": 87.0}
    },
    "휴스턴 텍산스": {
        "eng_name": "Houston Texans", "tri": "HOU",
        "qb": {"name": "C.J. 스트라우드 (C.J. Stroud)", "epa_play": 0.23, "cpoe": 3.5, "rating": 99.8},
        "offense": {"name": "O-Line & 스킬 포지션 (콜린스, 믹슨, 델프)", "pbwr": 70.0, "yards_per_game": 365.0},
        "defense": {"name": "수비 프런트 & DB (앤더슨 Jr., 헌터, 스팅글리)", "press_rate": 33.0, "pts_per_drive": 1.90},
        "kicker": {"name": "카이미 페어베언 (Ka'imi Fairbairn)", "fg_50_pct": 88.0}
    },
    "그린베이 패커스": {
        "eng_name": "Green Bay Packers", "tri": "GB",
        "qb": {"name": "조던 러브 (Jordan Love)", "epa_play": 0.21, "cpoe": 2.8, "rating": 97.2},
        "offense": {"name": "O-Line & 스킬 포지션 (제이콥스, 왓슨, 리드)", "pbwr": 73.0, "yards_per_game": 362.0},
        "defense": {"name": "수비 프런트 & DB (클라크, 게리, 알렉산더)", "press_rate": 31.0, "pts_per_drive": 1.95},
        "kicker": {"name": "브랜든 맥매너스 (Brandon McManus)", "fg_50_pct": 83.0}
    },
    "달라스 카우보이스": {
        "eng_name": "Dallas Cowboys", "tri": "DAL",
        "qb": {"name": "닥 프레스캇 (Dak Prescott)", "epa_play": 0.23, "cpoe": 3.6, "rating": 99.0},
        "offense": {"name": "O-Line & 스킬 포지션 (램, 엘리엇, 퍼거슨)", "pbwr": 71.0, "yards_per_game": 370.0},
        "defense": {"name": "수비 프런트 & DB (파슨스, 로렌스, 디그스)", "press_rate": 35.0, "pts_per_drive": 1.95},
        "kicker": {"name": "브랜든 오브리 (Brandon Aubrey)", "fg_50_pct": 91.0}
    },
    "신시내티 벵갈스": {
        "eng_name": "Cincinnati Bengals", "tri": "CIN",
        "qb": {"name": "조 버로우 (Joe Burrow)", "epa_play": 0.27, "cpoe": 4.5, "rating": 103.2},
        "offense": {"name": "O-Line & 스킬 포지션 (체이스, 히긴스, 브라운)", "pbwr": 66.0, "yards_per_game": 375.0},
        "defense": {"name": "수비 프런트 & DB (헨드릭슨, 허버드, 벨)", "press_rate": 29.0, "pts_per_drive": 2.10},
        "kicker": {"name": "에반 맥퍼슨 (Evan McPherson)", "fg_50_pct": 86.0}
    },
    "마이애미 돌핀스": {
        "eng_name": "Miami Dolphins", "tri": "MIA",
        "qb": {"name": "투아 타고바일로아 (Tua Tagovailoa)", "epa_play": 0.20, "cpoe": 3.0, "rating": 96.5},
        "offense": {"name": "O-Line & 스킬 포지션 (힐, 워들, 모스터트)", "pbwr": 68.0, "yards_per_game": 372.0},
        "defense": {"name": "수비 프런트 & DB (필립스, 찹, 램지)", "press_rate": 28.0, "pts_per_drive": 2.05},
        "kicker": {"name": "제이슨 샌더스 (Jason Sanders)", "fg_50_pct": 85.0}
    },
    "탬파베이 버커니어스": {
        "eng_name": "Tampa Bay Buccaneers", "tri": "TB",
        "qb": {"name": "베이커 메이필드 (Baker Mayfield)", "epa_play": 0.19, "cpoe": 2.5, "rating": 95.8},
        "offense": {"name": "O-Line & 스킬 포지션 (에반스, 갓윈, 화이트)", "pbwr": 69.0, "yards_per_game": 355.0},
        "defense": {"name": "수비 프런트 & DB (베이트, 비아, 딘)", "press_rate": 30.0, "pts_per_drive": 2.00},
        "kicker": {"name": "체이스 맥러플린 (Chase McLaughlin)", "fg_50_pct": 88.0}
    },
    "로스앤젤레스 램스": {
        "eng_name": "Los Angeles Rams", "tri": "LAR",
        "qb": {"name": "매튜 스태포드 (Matthew Stafford)", "epa_play": 0.21, "cpoe": 2.9, "rating": 97.5},
        "offense": {"name": "O-Line & 스킬 포지션 (쿠퍼 컵, 나쿠아, 윌리엄스)", "pbwr": 70.0, "yards_per_game": 360.0},
        "defense": {"name": "수비 프런트 & DB (터너, 버스, 두량)", "press_rate": 31.0, "pts_per_drive": 2.00},
        "kicker": {"name": "조슈아 카티 (Joshua Karty)", "fg_50_pct": 83.0}
    },
    "로스앤젤레스 차저스": {
        "eng_name": "Los Angeles Chargers", "tri": "LAC",
        "qb": {"name": "저스틴 허버트 (Justin Herbert)", "epa_play": 0.22, "cpoe": 3.1, "rating": 98.0},
        "offense": {"name": "O-Line & 스킬 포지션 (알트, 에드워즈, 파머)", "pbwr": 69.0, "yards_per_game": 348.0},
        "defense": {"name": "수비 프런트 & DB (보사, 맥, 제임스 Jr.)", "press_rate": 32.0, "pts_per_drive": 1.85},
        "kicker": {"name": "카메론 디커 (Cameron Dicker)", "fg_50_pct": 87.0}
    },
    "애틀랜타 팰컨스": {
        "eng_name": "Atlanta Falcons", "tri": "ATL",
        "qb": {"name": "커크 커즌스 (Kirk Cousins)", "epa_play": 0.18, "cpoe": 2.2, "rating": 94.5},
        "offense": {"name": "O-Line & 스킬 포지션 (비잔 로빈슨, 런던, 피츠)", "pbwr": 71.0, "yards_per_game": 352.0},
        "defense": {"name": "수비 프런트 & DB (주도인, 베이츠 III, 유도라)", "press_rate": 26.0, "pts_per_drive": 2.10},
        "kicker": {"name": "구영회 (Younghoe Koo)", "fg_50_pct": 89.0}
    },
    "피츠버그 스틸러스": {
        "eng_name": "Pittsburgh Steelers", "tri": "PIT",
        "qb": {"name": "러셀 윌슨 (Russell Wilson)", "epa_play": 0.17, "cpoe": 2.0, "rating": 93.8},
        "offense": {"name": "O-Line & 스킬 포지션 (해리스, 피켄스, 프레이어무스)", "pbwr": 62.0, "yards_per_game": 330.0},
        "defense": {"name": "수비 프런트 & DB (와트, 하이구원, 피츠패트릭)", "press_rate": 37.0, "pts_per_drive": 1.75},
        "kicker": {"name": "크리스 보스웰 (Chris Boswell)", "fg_50_pct": 90.0}
    },
    "클리블랜드 브라운스": {
        "eng_name": "Cleveland Browns", "tri": "CLE",
        "qb": {"name": "데샤운 왓슨 (Deshaun Watson)", "epa_play": 0.12, "cpoe": 0.5, "rating": 88.0},
        "offense": {"name": "O-Line & 스킬 포지션 (쿠퍼, 첩, 누조쿠)", "pbwr": 64.0, "yards_per_game": 325.0},
        "defense": {"name": "수비 프런트 & DB (개렛, 스미스, 워드)", "press_rate": 36.0, "pts_per_drive": 1.85},
        "kicker": {"name": "더스틴 홉킨스 (Dustin Hopkins)", "fg_50_pct": 85.0}
    },
    "뉴욕 제츠": {
        "eng_name": "New York Jets", "tri": "NYJ",
        "qb": {"name": "아론 로저스 (Aaron Rodgers)", "epa_play": 0.20, "cpoe": 2.8, "rating": 96.0},
        "offense": {"name": "O-Line & 스킬 포지션 (윌슨, 홀, 라자드)", "pbwr": 65.0, "yards_per_game": 340.0},
        "defense": {"name": "수비 프런트 & DB (윌리엄스, 윌리엄스, 가렛)", "press_rate": 35.0, "pts_per_drive": 1.80},
        "kicker": {"name": "그렉 조라인 (Greg Zuerlein)", "fg_50_pct": 84.0}
    },
    "미네소타 바이킹스": {
        "eng_name": "Minnesota Vikings", "tri": "MIN",
        "qb": {"name": "샘 다놀드 (Sam Darnold)", "epa_play": 0.19, "cpoe": 2.4, "rating": 95.0},
        "offense": {"name": "O-Line & 스킬 포지션 (제퍼슨, 애디슨, 존스)", "pbwr": 68.0, "yards_per_game": 348.0},
        "defense": {"name": "수비 프런트 & DB (그린나드, 바일랜드, 길모어)", "press_rate": 37.0, "pts_per_drive": 1.80},
        "kicker": {"name": "윌 라이카드 (Will Reichard)", "fg_50_pct": 86.0}
    },
    "시카고 베어스": {
        "eng_name": "Chicago Bears", "tri": "CHI",
        "qb": {"name": "케일럽 윌리엄스 (Caleb Williams)", "epa_play": 0.16, "cpoe": 1.5, "rating": 91.5},
        "offense": {"name": "O-Line & 스킬 포지션 (무어, 알렌, 스위프트)", "pbwr": 63.0, "yards_per_game": 335.0},
        "defense": {"name": "수비 프런트 & DB (스윗, 에드워즈, 존슨)", "press_rate": 31.0, "pts_per_drive": 2.05},
        "kicker": {"name": "카이로 산토스 (Cairo Santos)", "fg_50_pct": 87.0}
    },
    "잭슨빌 재규어스": {
        "eng_name": "Jacksonville Jaguars", "tri": "JAX",
        "qb": {"name": "트레버 로렌스 (Trevor Lawrence)", "epa_play": 0.18, "cpoe": 2.0, "rating": 94.0},
        "offense": {"name": "O-Line & 스킬 포지션 (토머스 Jr., 이티엔, 커크)", "pbwr": 63.0, "yards_per_game": 342.0},
        "defense": {"name": "수비 프런트 & DB (하인스-알렌, 워커, 캠벨)", "press_rate": 29.0, "pts_per_drive": 2.20},
        "kicker": {"name": "캠 리틀 (Cam Little)", "fg_50_pct": 85.0}
    },
    "인디애나폴리스 콜츠": {
        "eng_name": "Indianapolis Colts", "tri": "IND",
        "qb": {"name": "앤서니 리차드슨 (Anthony Richardson)", "epa_play": 0.17, "cpoe": 1.8, "rating": 92.0},
        "offense": {"name": "O-Line & 스킬 포지션 (테일러, 피트먼 Jr., 다운스)", "pbwr": 72.0, "yards_per_game": 350.0},
        "defense": {"name": "수비 프런트 & DB (버클너, 레이투, 무어)", "press_rate": 28.0, "pts_per_drive": 2.15},
        "kicker": {"name": "매트 게이 (Matt Gay)", "fg_50_pct": 84.0}
    },
    "시애틀 시호크스": {
        "eng_name": "Seattle Seahawks", "tri": "SEA",
        "qb": {"name": "지노 스미스 (Geno Smith)", "epa_play": 0.19, "cpoe": 2.5, "rating": 95.5},
        "offense": {"name": "O-Line & 스킬 포지션 (메트칼프, 로켓, 워커 III)", "pbwr": 65.0, "yards_per_game": 345.0},
        "defense": {"name": "수비 프런트 & DB (위더스푼, 머피, 로렌스)", "press_rate": 32.0, "pts_per_drive": 2.05},
        "kicker": {"name": "제이슨 마이어스 (Jason Myers)", "fg_50_pct": 87.0}
    },
    "뉴올리언스 세인츠": {
        "eng_name": "New Orleans Saints", "tri": "NO",
        "qb": {"name": "데릭 카 (Derek Carr)", "epa_play": 0.17, "cpoe": 2.0, "rating": 93.0},
        "offense": {"name": "O-Line & 스킬 포지션 (올라베, 카마라, 샤히드)", "pbwr": 64.0, "yards_per_game": 338.0},
        "defense": {"name": "수비 프런트 & DB (조던, 대번포트, 라티모어)", "press_rate": 31.0, "pts_per_drive": 2.05},
        "kicker": {"name": "블레이크 그루프 (Blake Grupe)", "fg_50_pct": 86.0}
    },
    "덴버 브롱코스": {
        "eng_name": "Denver Broncos", "tri": "DEN",
        "qb": {"name": "보 닉스 (Bo Nix)", "epa_play": 0.16, "cpoe": 1.6, "rating": 91.0},
        "offense": {"name": "O-Line & 스킬 포지션 (서튼, 윌리엄스, 듀치치)", "pbwr": 67.0, "yards_per_game": 330.0},
        "defense": {"name": "수비 프런트 & DB (서테인 II, 쿠퍼, 바닝)", "press_rate": 33.0, "pts_per_drive": 1.95},
        "kicker": {"name": "윌 룩스 (Wil Lutz)", "fg_50_pct": 86.0}
    },
    "라스베이거스 레이더스": {
        "eng_name": "Las Vegas Raiders", "tri": "LV",
        "qb": {"name": "가드너 민슈 (Gardner Minshew)", "epa_play": 0.13, "cpoe": 0.8, "rating": 89.0},
        "offense": {"name": "O-Line & 스킬 포지션 (아담스, 바워스, 화이트)", "pbwr": 61.0, "yards_per_game": 320.0},
        "defense": {"name": "수비 프런트 & DB (크로스비, 윌킨스, 홉스)", "press_rate": 34.0, "pts_per_drive": 2.25},
        "kicker": {"name": "다니엘 칼슨 (Daniel Carlson)", "fg_50_pct": 88.0}
    },
    "애리조나 카디널스": {
        "eng_name": "Arizona Cardinals", "tri": "ARI",
        "qb": {"name": "카일러 머레이 (Kyler Murray)", "epa_play": 0.18, "cpoe": 2.2, "rating": 94.0},
        "offense": {"name": "O-Line & 스킬 포지션 (해리슨 Jr., 코너, 맥브라이드)", "pbwr": 66.0, "yards_per_game": 340.0},
        "defense": {"name": "수비 프런트 & DB (콜린스, 베이커, 매치스)", "press_rate": 27.0, "pts_per_drive": 2.25},
        "kicker": {"name": "채드 라일랜드 (Chad Ryland)", "fg_50_pct": 88.0}
    },
    "워싱턴 커맨더스": {
        "eng_name": "Washington Commanders", "tri": "WAS",
        "qb": {"name": "제이든 대니얼스 (Jayden Daniels)", "epa_play": 0.21, "cpoe": 3.0, "rating": 97.0},
        "offense": {"name": "O-Line & 스킬 포지션 (맥클로린, 로빈슨 Jr., 어츠)", "pbwr": 68.0, "yards_per_game": 355.0},
        "defense": {"name": "수비 프런트 & DB (애런스, 페인, 치녹스)", "press_rate": 27.0, "pts_per_drive": 2.15},
        "kicker": {"name": "오스틴 사이버트 (Austin Seibert)", "fg_50_pct": 84.0}
    },
    "뉴잉글랜드 패트리어츠": {
        "eng_name": "New England Patriots", "tri": "NE",
        "qb": {"name": "드레이크 메이 (Drake Maye)", "epa_play": 0.14, "cpoe": 1.0, "rating": 89.5},
        "offense": {"name": "O-Line & 스킬 포지션 (스티븐슨, 포크, 헨리)", "pbwr": 58.0, "yards_per_game": 305.0},
        "defense": {"name": "수비 프런트 & DB (바모어, 타바이, 곤잘레스)", "press_rate": 27.0, "pts_per_drive": 2.20},
        "kicker": {"name": "조이 슬라이 (Joey Slye)", "fg_50_pct": 82.0}
    },
    "뉴욕 자이언츠": {
        "eng_name": "New York Giants", "tri": "NYG",
        "qb": {"name": "대니얼 존스 (Daniel Jones)", "epa_play": 0.12, "cpoe": 0.5, "rating": 87.5},
        "offense": {"name": "O-Line & 스킬 포지션 (나버스, 싱글터리, 셰퍼드)", "pbwr": 57.0, "yards_per_game": 300.0},
        "defense": {"name": "수비 프런트 & DB (티보도, 로렌스, 빈센트)", "press_rate": 32.0, "pts_per_drive": 2.35},
        "kicker": {"name": "그레이엄 가노 (Graham Gano)", "fg_50_pct": 83.0}
    },
    "테네시 타이탄스": {
        "eng_name": "Tennessee Titans", "tri": "TEN",
        "qb": {"name": "윌 리비스 (Will Levis)", "epa_play": 0.13, "cpoe": 0.7, "rating": 88.5},
        "offense": {"name": "O-Line & 스킬 포지션 (리들리, 폴라드, 보이드)", "pbwr": 59.0, "yards_per_game": 310.0},
        "defense": {"name": "수비 프런트 & DB (시몬스, 아부카, 맥크리어리)", "press_rate": 30.0, "pts_per_drive": 2.30},
        "kicker": {"name": "닉 포크 (Nick Folk)", "fg_50_pct": 82.0}
    },
    "캐롤라이나 팬서스": {
        "eng_name": "Carolina Panthers", "tri": "CAR",
        "qb": {"name": "브라이스 영 (Bryce Young)", "epa_play": 0.10, "cpoe": -0.5, "rating": 85.0},
        "offense": {"name": "O-Line & 스킬 포지션 (존슨, 허버드, 르게트)", "pbwr": 56.0, "yards_per_game": 290.0},
        "defense": {"name": "수비 프런트 & DB (클라우니, 톰슨, 혼)", "press_rate": 25.0, "pts_per_drive": 2.45},
        "kicker": {"name": "에디 피네이로 (Eddy Pineiro)", "fg_50_pct": 84.0}
    }
}

# -----------------------------------------------------------------------------
# 3. 11.0 WUV 예측 엔진 연동 및 승률/스코어 계산
# -----------------------------------------------------------------------------
def calculate_team_wuv(team_name):
    if team_name not in TEAMS_DATA:
        qb_uv = 1.85
        off_uv = 1.40
        def_uv = 2.10
        k_uv = 0.40
        team_info = {
            "eng_name": team_name, "tri": "NFL",
            "qb": {"name": f"{team_name} 주전 QB", "epa_play": 0.15, "cpoe": 1.0, "rating": 90.0},
            "offense": {"name": "공격 유닛 & O-Line", "pbwr": 62.0, "yards_per_game": 330.0},
            "defense": {"name": "수비 프런트 & DB", "press_rate": 28.0, "pts_per_drive": 2.10},
            "kicker": {"name": "주전 키커", "fg_50_pct": 80.0}
        }
    else:
        team_info = TEAMS_DATA[team_name]
        q = team_info["qb"]
        o = team_info["offense"]
        d = team_info["defense"]
        k = team_info["kicker"]

        # 1. QB UV (3.30 Max)
        q_norm = 0.40 * max(0.1, min(1.0, (q["epa_play"] + 0.10) / 0.40)) + \
                 0.30 * max(0.1, min(1.0, (q["cpoe"] + 5.0) / 11.0)) + \
                 0.30 * max(0.1, min(1.0, (q["rating"] - 75.0) / 35.0))
        qb_uv = round(3.30 * q_norm, 2)

        # 2. Offense UV (2.75 Max)
        o_norm = 0.50 * max(0.1, min(1.0, (o["pbwr"] - 50.0) / 30.0)) + \
                 0.50 * max(0.1, min(1.0, (o["yards_per_game"] - 280.0) / 130.0))
        off_uv = round(2.75 * o_norm, 2)

        # 3. Defense UV (4.18 Max)
        d_norm = 0.50 * max(0.1, min(1.0, (d["press_rate"] - 20.0) / 20.0)) + \
                 0.50 * max(0.1, min(1.0, (2.60 - d["pts_per_drive"]) / 1.20))
        def_uv = round(4.18 * d_norm, 2)

        # 4. Kicker UV (0.77 Max)
        k_norm = max(0.1, min(1.0, (k["fg_50_pct"] - 50.0) / 45.0))
        k_uv = round(0.77 * k_norm, 2)

    total_wuv = round(qb_uv + off_uv + def_uv + k_uv, 2)
    return {
        "team_name": team_name,
        "eng_name": team_info["eng_name"],
        "tri": team_info["tri"],
        "qb_uv": qb_uv,
        "off_uv": off_uv,
        "def_uv": def_uv,
        "k_uv": k_uv,
        "total_wuv": total_wuv,
        "qb": team_info["qb"],
        "offense": team_info["offense"],
        "defense": team_info["defense"],
        "kicker": team_info["kicker"]
    }

def predict_matchup(home_team, away_team):
    h_info = calculate_team_wuv(home_team)
    a_info = calculate_team_wuv(away_team)

    # 홈 어드밴티지 +0.25 UV 적용
    home_eff_wuv = round(h_info["total_wuv"] + 0.25, 2)
    away_eff_wuv = a_info["total_wuv"]

    uv_diff = home_eff_wuv - away_eff_wuv

    # 2-Way 로지스틱 확률 계산
    k = 1.25
    prob_home = 1.0 / (1.0 + np.exp(-k * uv_diff))
    prob_away = 1.0 - prob_home

    home_win_pct = round(prob_home * 100, 1)
    away_win_pct = round(prob_away * 100, 1)

    # 예상 스코어 계산 (NFL 평균득점 ~23.5)
    base_points = 23.5
    home_exp_pts = max(10, int(round(base_points + 4.5 * uv_diff)))
    away_exp_pts = max(10, int(round(base_points - 4.5 * uv_diff)))
    if home_exp_pts == away_exp_pts:
        if uv_diff > 0: home_exp_pts += 3
        else: away_exp_pts += 3

    # AI 추천 픽 결정
    if home_win_pct >= 53.0:
        predicted_winner = home_team
        recommendation = f"🏈 [홈 승 추천] {home_team}"
    elif away_win_pct >= 53.0:
        predicted_winner = away_team
        recommendation = f"🏈 [원정 승 추천] {away_team}"
    else:
        if home_win_pct >= away_win_pct:
            predicted_winner = home_team
            recommendation = f"🏈 [근소 홈 우세] {home_team}"
        else:
            predicted_winner = away_team
            recommendation = f"🏈 [근소 원정 우세] {away_team}"

    return {
        "home_info": h_info,
        "away_info": a_info,
        "home_eff_wuv": home_eff_wuv,
        "away_eff_wuv": away_eff_wuv,
        "uv_diff": uv_diff,
        "home_win_pct": home_win_pct,
        "away_win_pct": away_win_pct,
        "home_exp_pts": home_exp_pts,
        "away_exp_pts": away_exp_pts,
        "predicted_winner": predicted_winner,
        "recommendation": recommendation
    }

# -----------------------------------------------------------------------------
# 4. ESPN API 연동 (2026-27 정규시즌 1~18주차 공식 일정 로드)
# -----------------------------------------------------------------------------
@st.cache_data(ttl=600)
def fetch_espn_nfl_schedule(seasontype=2, week=1):
    url = f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?seasontype={seasontype}&week={week}"
    try:
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            data = res.json()
            events = data.get("events", [])
            games = []
            for ev in events:
                try:
                    comp = ev["competitions"][0]
                    status_type = ev["status"]["type"]["name"]
                    status_detail = ev["status"]["type"]["shortDetail"]
                    date_str = ev["date"][:10]
                    
                    home_comp = comp["competitors"][0] if comp["competitors"][0]["homeAway"] == "home" else comp["competitors"][1]
                    away_comp = comp["competitors"][1] if comp["competitors"][0]["homeAway"] == "home" else comp["competitors"][0]
                    
                    home_raw_name = home_comp["team"]["displayName"]
                    away_raw_name = away_comp["team"]["displayName"]
                    home_tri = home_comp["team"].get("abbreviation", "")
                    away_tri = away_comp["team"].get("abbreviation", "")
                    
                    home_kor = TRI_TO_KOR.get(home_tri, home_raw_name)
                    away_kor = TRI_TO_KOR.get(away_tri, away_raw_name)
                    
                    home_logo = home_comp["team"].get("logo", "https://a.espncdn.com/i/teamlogos/nfl/500/scoreboard/nfl.png")
                    away_logo = away_comp["team"].get("logo", "https://a.espncdn.com/i/teamlogos/nfl/500/scoreboard/nfl.png")
                    
                    home_score = home_comp.get("score", "")
                    away_score = away_comp.get("score", "")
                    
                    actual_winner = ""
                    if status_type == "STATUS_FINAL" and home_score and away_score:
                        hs = int(home_score)
                        aws = int(away_score)
                        if hs > aws: actual_winner = home_kor
                        elif aws > hs: actual_winner = away_kor
                        else: actual_winner = "Tie"

                    games.append({
                        "date": date_str,
                        "home_team": home_kor,
                        "visit_team": away_kor,
                        "home_logo": home_logo,
                        "visit_logo": away_logo,
                        "home_score": home_score,
                        "visit_score": away_score,
                        "status_type": status_type,
                        "status_detail": status_detail,
                        "actual_winner": actual_winner
                    })
                except Exception:
                    continue
            if games:
                return pd.DataFrame(games)
    except Exception:
        pass

    # Fallback Sample Data (2026-27 정규시즌 Week 1)
    sample_games = [
        {"date": "2026-09-10", "home_team": "시애틀 시호크스", "visit_team": "뉴잉글랜드 패트리어츠", "home_logo": "https://a.espncdn.com/i/teamlogos/nfl/500/sea.png", "visit_logo": "https://a.espncdn.com/i/teamlogos/nfl/500/ne.png", "home_score": "", "visit_score": "", "status_type": "STATUS_SCHEDULED", "status_detail": "Thu 8:20 PM", "actual_winner": ""},
        {"date": "2026-09-11", "home_team": "로스앤젤레스 램스", "visit_team": "샌프란시스코 49어스", "home_logo": "https://a.espncdn.com/i/teamlogos/nfl/500/lar.png", "visit_logo": "https://a.espncdn.com/i/teamlogos/nfl/500/sf.png", "home_score": "", "visit_score": "", "status_type": "STATUS_SCHEDULED", "status_detail": "Fri 8:15 PM", "actual_winner": ""},
        {"date": "2026-09-13", "home_team": "신시내티 벵갈스", "visit_team": "탬파베이 버커니어스", "home_logo": "https://a.espncdn.com/i/teamlogos/nfl/500/cin.png", "visit_logo": "https://a.espncdn.com/i/teamlogos/nfl/500/tb.png", "home_score": "", "visit_score": "", "status_type": "STATUS_SCHEDULED", "status_detail": "Sun 1:00 PM", "actual_winner": ""},
        {"date": "2026-09-13", "home_team": "디트로이트 라이온스", "visit_team": "뉴올리언스 세인츠", "home_logo": "https://a.espncdn.com/i/teamlogos/nfl/500/det.png", "visit_logo": "https://a.espncdn.com/i/teamlogos/nfl/500/no.png", "home_score": "", "visit_score": "", "status_type": "STATUS_SCHEDULED", "status_detail": "Sun 1:00 PM", "actual_winner": ""},
        {"date": "2026-09-13", "home_team": "테네시 타이탄스", "visit_team": "뉴욕 제츠", "home_logo": "https://a.espncdn.com/i/teamlogos/nfl/500/ten.png", "visit_logo": "https://a.espncdn.com/i/teamlogos/nfl/500/nyj.png", "home_score": "", "visit_score": "", "status_type": "STATUS_SCHEDULED", "status_detail": "Sun 1:00 PM", "actual_winner": ""},
        {"date": "2026-09-13", "home_team": "인디애나폴리스 콜츠", "visit_team": "마이애미 돌핀스", "home_logo": "https://a.espncdn.com/i/teamlogos/nfl/500/ind.png", "visit_logo": "https://a.espncdn.com/i/teamlogos/nfl/500/mia.png", "home_score": "", "visit_score": "", "status_type": "STATUS_SCHEDULED", "status_detail": "Sun 1:00 PM", "actual_winner": ""},
        {"date": "2026-09-13", "home_team": "애틀랜타 팰컨스", "visit_team": "피츠버그 스틸러스", "home_logo": "https://a.espncdn.com/i/teamlogos/nfl/500/atl.png", "visit_logo": "https://a.espncdn.com/i/teamlogos/nfl/500/pit.png", "home_score": "", "visit_score": "", "status_type": "STATUS_SCHEDULED", "status_detail": "Sun 1:00 PM", "actual_winner": ""},
        {"date": "2026-09-13", "home_team": "클리블랜드 브라운스", "visit_team": "달라스 카우보이스", "home_logo": "https://a.espncdn.com/i/teamlogos/nfl/500/cle.png", "visit_logo": "https://a.espncdn.com/i/teamlogos/nfl/500/dal.png", "home_score": "", "visit_score": "", "status_type": "STATUS_SCHEDULED", "status_detail": "Sun 4:25 PM", "actual_winner": ""},
        {"date": "2026-09-13", "home_team": "탬파베이 버커니어스", "visit_team": "워싱턴 커맨더스", "home_logo": "https://a.espncdn.com/i/teamlogos/nfl/500/tb.png", "visit_logo": "https://a.espncdn.com/i/teamlogos/nfl/500/was.png", "home_score": "", "visit_score": "", "status_type": "STATUS_SCHEDULED", "status_detail": "Sun 4:25 PM", "actual_winner": ""},
        {"date": "2026-09-13", "home_team": "로스앤젤레스 차저스", "visit_team": "라스베이거스 레이더스", "home_logo": "https://a.espncdn.com/i/teamlogos/nfl/500/lac.png", "visit_logo": "https://a.espncdn.com/i/teamlogos/nfl/500/lv.png", "home_score": "", "visit_score": "", "status_type": "STATUS_SCHEDULED", "status_detail": "Sun 4:05 PM", "actual_winner": ""},
        {"date": "2026-09-13", "home_team": "캔ザ스시티 치프스", "visit_team": "볼티모어 레이븐스", "home_logo": "https://a.espncdn.com/i/teamlogos/nfl/500/kc.png", "visit_logo": "https://a.espncdn.com/i/teamlogos/nfl/500/bal.png", "home_score": "", "visit_score": "", "status_type": "STATUS_SCHEDULED", "status_detail": "Sun 8:20 PM", "actual_winner": ""},
        {"date": "2026-09-14", "home_team": "샌프란시스코 49어스", "visit_team": "뉴욕 자이언츠", "home_logo": "https://a.espncdn.com/i/teamlogos/nfl/500/sf.png", "visit_logo": "https://a.espncdn.com/i/teamlogos/nfl/500/nyg.png", "home_score": "", "visit_score": "", "status_type": "STATUS_SCHEDULED", "status_detail": "Mon 8:15 PM", "actual_winner": ""}
    ]
    return pd.DataFrame(sample_games)

# -----------------------------------------------------------------------------
# 5. 주차(Week) 및 시즌 선택 UI
# -----------------------------------------------------------------------------
st.sidebar.header("⚙️ NFL 2026-27 시즌 옵션")

season_mode = st.sidebar.radio(
    "시즌 모드 선택:",
    ["2026-27 정규시즌 (Regular Season)", "2026 프리시즌 (Preseason)"],
    index=0
)

seasontype_val = 2 if "정규시즌" in season_mode else 1

if seasontype_val == 2:
    selected_week = st.sidebar.selectbox("정규시즌 주차(Week) 선택:", range(1, 19), index=0)
else:
    selected_week = st.sidebar.selectbox("프리시즌 주차(Week) 선택:", range(1, 5), index=3)

df = fetch_espn_nfl_schedule(seasontype=seasontype_val, week=selected_week)

# 예측 정보 추가
predicted_winners = []
home_uvs = []
visit_uvs = []
is_corrects = []

for _, row in df.iterrows():
    pred = predict_matchup(row['home_team'], row['visit_team'])
    pw = pred['predicted_winner']
    predicted_winners.append(pw)
    home_uvs.append(pred['home_eff_wuv'])
    visit_uvs.append(pred['away_eff_wuv'])
    
    act = row.get('actual_winner', '')
    if act and act != 'Postponed' and act != 'Tie':
        is_corrects.append(1 if pw == act else 0)
    else:
        is_corrects.append(None)

df['predicted_winner'] = predicted_winners
df['home_uv'] = home_uvs
df['visit_uv'] = visit_uvs
df['is_correct'] = is_corrects

# -----------------------------------------------------------------------------
# 6. [상단] 누적 예측 성적표 & 2026-27 시즌 상태 알림
# -----------------------------------------------------------------------------
st.header("📊 2026-27 시즌 예측 성적표 & 적중률")

st.markdown("""
<div class="season-badge">
    🏈 <b>2026-27 NFL 정규시즌 개막 D-12</b> (2026년 9월 10일 Kickoff!)
</div>
""", unsafe_allow_html=True)

stats_df = df[
    (df['actual_winner'] != 'Postponed') & 
    (df['actual_winner'].notna()) & 
    (df['actual_winner'] != '')
].copy()

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
        remaining = max(0, 100 - total_stats)
        if remaining > 0:
            st.metric("100경기 시스템 검증까지", f"{remaining}경기 남음")
        else:
            st.metric("시스템 검증 상태", "검증 완료 (신계 등급)")
else:
    with col_acc:
        st.subheader(f"2026-27 시즌 Week {selected_week} 예정 경기: `{len(df)} 경기`")
        st.markdown(f"💡 현재 2026 오프시즌/개막 준비 기간입니다. **2026년 9월 10일 정규시즌 개막 후 경기 진행에 따라 실시간 적중률이 집계됩니다.**")
    with col_track:
        st.metric("시즌 상태", f"Week {selected_week} 개막 대기 중")

st.markdown("---")

# -----------------------------------------------------------------------------
# 7. 적중률 벤치마크 (2-Way 표준 1:1 복사)
# -----------------------------------------------------------------------------
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
# 8. [메인] 2026-27 시즌 주차별 NFL 매치업 카드 그리드
# -----------------------------------------------------------------------------
st.header(f"🏈 2026-27 NFL Week {selected_week} 매치업 카드 리포트")

if not df.empty:
    card_cols = st.columns(2)
    for idx, row in df.iterrows():
        col_idx = idx % 2
        with card_cols[col_idx]:
            home = row['home_team']
            visit = row['visit_team']
            pred = predict_matchup(home, visit)
            
            home_info = pred['home_info']
            away_info = pred['away_info']
            
            h_score = row.get('home_score', '')
            a_score = row.get('visit_score', '')
            status = row.get('status_detail', 'Scheduled')
            
            score_display = f"<b>{a_score} : {h_score}</b>" if (h_score and a_score) else f"예상 스코어<br><b>{pred['away_exp_pts']} : {pred['home_exp_pts']}</b>"
            
            st.markdown(f"""
            <div class="match-card">
                <div style="display: flex; justify-content: space-between; font-size: 0.82rem; color: #64748b; margin-bottom: 8px;">
                    <span>📅 {row['date']}</span>
                    <span>{status}</span>
                </div>
                <div class="team-header">
                    <div class="team-box">
                        <img src="{row.get('visit_logo', '')}" class="team-logo" alt="{visit}"/>
                        <div class="team-name">{visit}</div>
                        <div style="font-size: 0.78rem; color: #64748b;">(원정)</div>
                        <div class="uv-score">{pred['away_eff_wuv']:.2f} <small style="font-size: 0.7rem;">WUV</small></div>
                    </div>
                    <div style="text-align: center;">
                        <span class="vs-badge">VS</span>
                        <div style="font-size: 0.75rem; color: #64748b; margin-top: 6px;">{score_display}</div>
                    </div>
                    <div class="team-box">
                        <img src="{row.get('home_logo', '')}" class="team-logo" alt="{home}"/>
                        <div class="team-name">{home}</div>
                        <div style="font-size: 0.78rem; color: #64748b;">(홈 +0.25)</div>
                        <div class="uv-score">{pred['home_eff_wuv']:.2f} <small style="font-size: 0.7rem;">WUV</small></div>
                    </div>
                </div>
                <div class="qb-box">
                    🎯 <b>선발 QB 대결:</b> {away_info['qb']['name']} vs {home_info['qb']['name']}<br>
                    ⚡ <b>WUV 차이:</b> 원정 {pred['away_eff_wuv']:.2f} vs 홈 {pred['home_eff_wuv']:.2f} (차이 {abs(pred['uv_diff']):.2f})
                </div>
                <div class="prob-bar-container">
                    <div class="prob-away" style="width: {pred['away_win_pct']}%;">{visit} {pred['away_win_pct']}%</div>
                    <div class="prob-home" style="width: {pred['home_win_pct']}%;">{home} {pred['home_win_pct']}%</div>
                </div>
                <div class="pick-badge">
                    {pred['recommendation']}
                </div>
            </div>
            """, unsafe_allow_html=True)

st.markdown("---")

# -----------------------------------------------------------------------------
# 9. [하단 상세 탭] 유닛별 UV 비교 테이블 & 공수 밸런스 레이더 차트
# -----------------------------------------------------------------------------
st.header("🔍 매치업 상세 분석 (11.0 WUV 세부 유닛 & 공수 밸런스)")

matchup_list = [f"{r['visit_team']} vs {r['home_team']} ({r['date']})" for _, r in df.iterrows()]
if matchup_list:
    selected_matchup_str = st.selectbox("분석할 경기를 선택하세요:", matchup_list)
    selected_idx = matchup_list.index(selected_matchup_str)
    selected_row = df.iloc[selected_idx]
    
    home_team = selected_row['home_team']
    away_team = selected_row['visit_team']
    
    pred_detail = predict_matchup(home_team, away_team)
    h_info = pred_detail['home_info']
    a_info = pred_detail['away_info']
    
    tab1, tab2, tab3 = st.tabs(["📊 유닛별 UV 상세 비교", "🕸️ 공수 밸런스 레이더 차트", "👤 선발 QB & 유닛 지표 리포트"])
    
    with tab1:
        st.subheader(f"🏈 {away_team} (원정) vs {home_team} (홈) - 11.0 WUV 유닛 세부 분석")
        
        unit_table_data = [
            {
                "유닛 파트": "1. QB 유닛 (30% 가중치)",
                f"{away_team} (원정)": f"{a_info['qb_uv']:.2f} / 3.30 UV",
                f"{home_team} (홈)": f"{h_info['qb_uv']:.2f} / 3.30 UV",
                "핵심 지표": f"EPA/play, CPOE, Passer Rating ({a_info['qb']['name']} vs {h_info['qb']['name']})"
            },
            {
                "유닛 파트": "2. Offense 유닛 (25% 가중치)",
                f"{away_team} (원정)": f"{a_info['off_uv']:.2f} / 2.75 UV",
                f"{home_team} (홈)": f"{h_info['off_uv']:.2f} / 2.75 UV",
                "핵심 지표": "O-Line 패스블로킹 승률(PBWR) & 스킬포지션 야드 효율"
            },
            {
                "유닛 파트": "3. Defense 유닛 (38% 가중치)",
                f"{away_team} (원정)": f"{a_info['def_uv']:.2f} / 4.18 UV",
                f"{home_team} (홈)": f"{h_info['def_uv']:.2f} / 4.18 UV",
                "핵심 지표": "패스러시 압박률(Pressure Rate) & 드라이브 당 실점 억제력"
            },
            {
                "유닛 파트": "4. Kicker 유닛 (7% 가중치)",
                f"{away_team} (원정)": f"{a_info['k_uv']:.2f} / 0.77 UV",
                f"{home_team} (홈)": f"{h_info['k_uv']:.2f} / 0.77 UV",
                "핵심 지표": "50+ 야드 필드골 성공률 & 필드골 안정성"
            },
            {
                "유닛 파트": "5. 홈 어드밴티지",
                f"{away_team} (원정)": "0.00 UV",
                f"{home_team} (홈)": "+0.25 UV",
                "핵심 지표": "홈 구장 및 원정 이동 피로도 표준 가산점"
            },
            {
                "유닛 파트": "🔥 최종 통합 WUV",
                f"{away_team} (원정)": f"<b>{pred_detail['away_eff_wuv']:.2f} WUV</b>",
                f"{home_team} (홈)": f"<b>{pred_detail['home_eff_wuv']:.2f} WUV</b>",
                "핵심 지표": f"<b>승리 확률: {away_team} {pred_detail['away_win_pct']}% vs {home_team} {pred_detail['home_win_pct']}%</b>"
            }
        ]
        st.write(pd.DataFrame(unit_table_data).to_html(escape=False, index=False), unsafe_allow_html=True)
        
    with tab2:
        st.subheader("🕸️ 팀 유닛별 공수 밸런스 비교 레이더 차트")
        
        categories = ['QB 유닛 (3.30)', '공격/O-Line (2.75)', '수비/프런트7 (4.18)', '키커/특수팀 (0.77)']
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatterpolar(
            r=[a_info['qb_uv'], a_info['off_uv'], a_info['def_uv'], a_info['k_uv']],
            theta=categories,
            fill='toself',
            name=f"{away_team} (원정)",
            line_color='#2563eb'
        ))
        fig.add_trace(go.Scatterpolar(
            r=[h_info['qb_uv'], h_info['off_uv'], h_info['def_uv'], h_info['k_uv']],
            theta=categories,
            fill='toself',
            name=f"{home_team} (홈)",
            line_color='#dc2626'
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 4.5]
                )
            ),
            showlegend=True,
            height=450
        )
        st.plotly_chart(fig, use_container_width=True)

    with tab3:
        st.subheader("👤 양 팀 주요 선발 지표 및 리포트")
        col_a, col_h = st.columns(2)
        
        with col_a:
            st.markdown(f"### 🔵 {away_team} (원정)")
            st.markdown(f"- **선발 QB:** {a_info['qb']['name']}")
            st.markdown(f"  * EPA/play: `{a_info['qb']['epa_play']}` | CPOE: `{a_info['qb']['cpoe']}%` | Passer Rating: `{a_info['qb']['rating']}`")
            st.markdown(f"- **공격 유닛:** {a_info['offense']['name']}")
            st.markdown(f"  * O-Line PBWR: `{a_info['offense']['pbwr']}%` | 경기당 야드: `{a_info['offense']['yards_per_game']} yds`")
            st.markdown(f"- **수비 유닛:** {a_info['defense']['name']}")
            st.markdown(f"  * 압박률: `{a_info['defense']['press_rate']}%` | 드라이브 당 실점: `{a_info['defense']['pts_per_drive']} pts`")
            st.markdown(f"- **주전 키커:** {a_info['kicker']['name']} (50+ 야드 성공률: `{a_info['kicker']['fg_50_pct']}%`)")

        with col_h:
            st.markdown(f"### 🔴 {home_team} (홈)")
            st.markdown(f"- **선발 QB:** {h_info['qb']['name']}")
            st.markdown(f"  * EPA/play: `{h_info['qb']['epa_play']}` | CPOE: `{h_info['qb']['cpoe']}%` | Passer Rating: `{h_info['qb']['rating']}`")
            st.markdown(f"- **공격 유닛:** {h_info['offense']['name']}")
            st.markdown(f"  * O-Line PBWR: `{h_info['offense']['pbwr']}%` | 경기당 야드: `{h_info['offense']['yards_per_game']} yds`")
            st.markdown(f"- **수비 유닛:** {h_info['defense']['name']}")
            st.markdown(f"  * 압박률: `{h_info['defense']['press_rate']}%` | 드라이브 당 실점: `{h_info['defense']['pts_per_drive']} pts`")
            st.markdown(f"- **주전 키커:** {h_info['kicker']['name']} (50+ 야드 성공률: `{h_info['kicker']['fg_50_pct']}%`)")
