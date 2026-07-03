import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.graph_objects as go
import gspread
from google.oauth2.service_account import Credentials
import bcrypt
import time
import secrets
import html as _html
import re

# ─── Config ───────────────────────────────────────────────────────────────────
st.set_page_config(page_title="MAHAL — Gestion", layout="wide", initial_sidebar_state="collapsed")

SPREADSHEET_ID = st.secrets.get("spreadsheet_id", "1iiBU5dxAymvo6Sxl3lXpyWLvniLMdNHHSnNDw7I7avA")
SCOPES = ["https://www.googleapis.com/auth/spreadsheets",
          "https://www.googleapis.com/auth/drive.file"]
MAX_ATTEMPTS   = 5
LOCKOUT_SECONDS = 300
SESSION_TTL     = 8 * 3600

# ─── CSS ──────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=DM+Serif+Display&display=swap');

*, *::before, *::after { box-sizing: border-box; }
html, body, .stApp { background-color: #F7F6F2; color: #1C1C1C; font-family: 'DM Sans', sans-serif; }
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 3rem 4rem 4rem 4rem; max-width: 1300px; }

input, textarea, [contenteditable] { caret-color: #1C1C1C !important; }

.stTextInput button { background: transparent !important; border: none !important; }
.stTextInput button svg { color: #C8C4BC !important; fill: #C8C4BC !important; opacity: 1 !important; }
.stTextInput button svg path { stroke: #C8C4BC !important; fill: none !important; }
.stTextInput button:hover svg { color: #999 !important; fill: #999 !important; }
.stTextInput button:hover svg path { stroke: #999 !important; }
._terminalButton_rix23_138 { display: none !important;}

.auth-split-bg {
    position: fixed; inset: 0; z-index: 0; pointer-events: none;
    background: linear-gradient(to right, #1C1C1C 48%, #F7F6F2 48%);
}
.auth-left {
    background: #1C1C1C;
    display: flex; flex-direction: column;
    justify-content: space-between;
    padding: 4rem 3.5rem;
    min-height: 88vh;
    border-radius: 0 16px 16px 0;
    position: relative; overflow: hidden;
}
.auth-left::before {
    content: '';
    position: absolute;
    width: 560px; height: 560px;
    border-radius: 50%;
    border: 1px solid rgba(247,246,242,0.05);
    top: -140px; right: -200px;
    pointer-events: none;
}
.auth-left::after {
    content: '';
    position: absolute;
    width: 300px; height: 300px;
    border-radius: 50%;
    background: radial-gradient(circle, rgba(247,246,242,0.04) 0%, transparent 70%);
    bottom: 40px; left: -80px;
    pointer-events: none;
}
.auth-logo-area { position: relative; z-index: 2; }
.auth-brand {
    font-family: 'DM Serif Display', serif;
    font-size: 5.2rem;
    color: #F7F6F2;
    line-height: 0.9;
    letter-spacing: -0.03em;
    margin-bottom: 0.7rem;
}
.auth-brand-sub {
    font-size: 0.65rem;
    color: rgba(247,246,242,0.32);
    letter-spacing: 0.26em;
    text-transform: uppercase;
}
.auth-left-sep {
    width: 40px; height: 1px;
    background: rgba(247,246,242,0.15);
    margin: 3rem 0;
    position: relative; z-index: 2;
}
.auth-left-bottom { position: relative; z-index: 2; }
.auth-tagline {
    font-size: 0.82rem;
    color: rgba(247,246,242,0.45);
    line-height: 1.85;
    max-width: 240px;
    border-left: 1px solid rgba(247,246,242,0.12);
    padding-left: 1.1rem;
    margin-bottom: 2.5rem;
}
.auth-year {
    font-size: 0.6rem;
    color: rgba(247,246,242,0.18);
    letter-spacing: 0.18em;
    text-transform: uppercase;
}
.auth-right-inner {
    max-width: 360px;
    margin: 0 auto;
    padding-top: 1.5rem;
}
.auth-badge {
    display: inline-flex; align-items: center; gap: 0.45rem;
    background: #F0EDE5;
    border: 1px solid #E0DDD5;
    border-radius: 20px;
    padding: 0.32rem 0.9rem;
    font-size: 0.65rem;
    color: #999;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    margin-bottom: 1.8rem;
    font-weight: 500;
}
.auth-badge-dot {
    width: 5px; height: 5px;
    border-radius: 50%;
    background: #B8B4AC;
}
.auth-eyebrow {
    font-size: 0.63rem;
    font-weight: 600;
    letter-spacing: 0.22em;
    text-transform: uppercase;
    color: #C0BAB0;
    margin-bottom: 0.6rem;
}
.auth-form-title {
    font-family: 'DM Serif Display', serif;
    font-size: 2.5rem;
    color: #1C1C1C;
    line-height: 1.02;
    letter-spacing: -0.025em;
    margin-bottom: 0.65rem;
}
.auth-form-desc {
    font-size: 0.8rem;
    color: #AAAAAA;
    line-height: 1.7;
    margin-bottom: 2.2rem;
}
.auth-divider {
    display: flex; align-items: center; gap: 0.8rem;
    margin: 0.4rem 0;
    color: #CCCCCC; font-size: 0.68rem; letter-spacing: 0.1em;
}
.auth-divider::before, .auth-divider::after {
    content: ''; flex: 1; height: 1px; background: #E8E5DE;
}
.auth-switch-text {
    font-size: 0.7rem; color: #C0BAB0;
    text-align: center; margin-top: 1.8rem;
    letter-spacing: 0.04em;
}

[data-testid="stButton"] > button[kind="secondary"] {
    background: #F0EDE5 !important;
    color: #555 !important;
}

.topbar { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.3rem; }
.topbar-user { font-size: 0.8rem; color: #999; letter-spacing: 0.04em; padding-top: 0.8rem; }
.topbar-role { display: inline-block; font-size: 0.68rem; font-weight: 600; letter-spacing: 0.08em; text-transform: uppercase; padding: 0.25rem 0.8rem; border-radius: 20px; margin-left: 0.5rem; }
.role-admin { background: #1C1C1C; color: #F7F6F2; }
.role-sous-admin { background: #2D4A8A; color: #F7F6F2; }
.role-visiteur { background: #E8E5DE; color: #777; }

.notif-badge { display: inline-flex; align-items: center; justify-content: center; background: #E53935; color: #FFF; font-size: 0.65rem; font-weight: 700; width: 18px; height: 18px; border-radius: 50%; margin-left: 6px; vertical-align: middle; }
.notif-banner { background: #FFF3E0; border: 1px solid #FFB74D; border-radius: 8px; padding: 0.75rem 1.2rem; margin-bottom: 1rem; display: flex; align-items: center; gap: 0.8rem; font-size: 0.88rem; color: #7A4100; }
.notif-banner-dot { width: 8px; height: 8px; border-radius: 50%; background: #FFB74D; flex-shrink: 0; }

.badge-pending { display: inline-block; background: #FFF8E1; border: 1px solid #F0C040; color: #7A5C00; font-size: 0.72rem; padding: 0.2rem 0.7rem; border-radius: 20px; font-weight: 500; }
.badge-approved { background: #EEF7EE; border: 1px solid #C3DEC3; color: #2D6A2D; }
.badge-rejected { background: #FDECEA; border: 1px solid #E8B4B0; color: #7A1C1C; }

.page-title { font-family: 'DM Serif Display', serif; font-size: 2.6rem; color: #1C1C1C; margin-bottom: 0.2rem; line-height: 1.1; }
.page-subtitle { font-size: 0.85rem; color: #999; font-weight: 300; letter-spacing: 0.08em; text-transform: uppercase; margin-bottom: 2.5rem; }
.section-title { font-family: 'DM Serif Display', serif; font-size: 1.35rem; color: #1C1C1C; margin-top: 2rem; margin-bottom: 1.2rem; padding-bottom: 0.6rem; border-bottom: 1px solid #E0DDD5; }

.metric-row { display: flex; gap: 1rem; margin-bottom: 2rem; }
.metric-card { background: #FFFFFF; border: 1px solid #E8E5DE; border-radius: 10px; padding: 1.2rem 1.5rem; flex: 1; }
.metric-label { font-size: 0.72rem; font-weight: 500; text-transform: uppercase; letter-spacing: 0.07em; color: #AAA; margin-bottom: 0.5rem; }
.metric-value { font-family: 'DM Serif Display', serif; font-size: 1.55rem; color: #1C1C1C; line-height: 1; }
.metric-value.positive { color: #2D7A3A; }
.metric-value.negative { color: #B03A2E; }

.stTextInput > div > div > input,
.stNumberInput > div > div > input,
.stDateInput > div > div > input {
    background: #F7F6F2 !important; border: 1px solid #DDDAD2 !important;
    border-radius: 8px !important; color: #1C1C1C !important;
    font-family: 'DM Sans', sans-serif !important; font-size: 0.9rem !important;
    padding: 0.55rem 0.9rem !important; -webkit-text-fill-color: #1C1C1C !important;
    caret-color: #1C1C1C !important;
}
.stTextInput > div > div > input::placeholder,
.stNumberInput > div > div > input::placeholder { color: #AAAAAA !important; -webkit-text-fill-color: #AAAAAA !important; opacity: 1 !important; }
.stTextInput > div > div > input:focus,
.stNumberInput > div > div > input:focus { border-color: #1C1C1C !important; box-shadow: none !important; }
.stTextInput label, .stNumberInput label, .stSelectbox label, .stDateInput label, .stMultiSelect label {
    font-size: 0.75rem !important; font-weight: 500 !important; letter-spacing: 0.06em !important;
    text-transform: uppercase !important; color: #999 !important; margin-bottom: 0.3rem !important;
}
.stSelectbox > div > div > div { background: #F7F6F2 !important; border: 1px solid #DDDAD2 !important; border-radius: 8px !important; font-family: 'DM Sans', sans-serif !important; font-size: 0.9rem !important; color: #1C1C1C !important; }
.stSelectbox [data-baseweb="select"] span, .stSelectbox [data-baseweb="select"] div { color: #1C1C1C !important; }
.stSelectbox svg, .stNumberInput svg, .stDateInput svg, .stMultiSelect svg { display: block !important; color: #1C1C1C !important; fill: #1C1C1C !important; }
.stSelectbox input, [data-baseweb="select"] input, [data-baseweb="combobox"] input { color: #1C1C1C !important; -webkit-text-fill-color: #1C1C1C !important; caret-color: #1C1C1C !important; }
[data-baseweb="popover"] li, [data-baseweb="menu"] li, [data-baseweb="option"] { color: #1C1C1C !important; background: #FFFFFF !important; font-family: 'DM Sans', sans-serif !important; font-size: 0.9rem !important; }
[data-baseweb="option"]:hover { background: #F0EDE5 !important; }
.stCheckbox label, .stCheckbox label p, .stCheckbox span { color: #1C1C1C !important; font-size: 0.88rem !important; }

.stButton > button { background: #1C1C1C !important; color: #F7F6F2 !important; border: none !important; border-radius: 8px !important; padding: 0.65rem 2.2rem !important; font-family: 'DM Sans', sans-serif !important; font-size: 0.88rem !important; font-weight: 500 !important; letter-spacing: 0.03em !important; margin-top: 1rem; transition: opacity 0.2s ease !important; }
.stButton > button:hover { opacity: 0.72 !important; }

.stSuccess > div { background: #F0F7F0 !important; border: 1px solid #C3DEC3 !important; border-radius: 8px !important; color: #2D6A2D !important; font-size: 0.88rem !important; }

.stDataFrame { border-radius: 10px !important; overflow: hidden !important; border: 1px solid #E8E5DE !important; }
.stDataFrame table { font-size: 0.88rem !important; font-family: 'DM Sans', sans-serif !important; }
.stDataFrame thead th { background: #F0EDE5 !important; color: #777 !important; font-weight: 500 !important; font-size: 0.75rem !important; letter-spacing: 0.05em !important; text-transform: uppercase !important; padding: 0.75rem 1rem !important; border-bottom: 1px solid #DDDAD2 !important; }
.stDataFrame tbody tr:nth-child(even) td { background: #FAFAF8 !important; }
.stDataFrame tbody td { padding: 0.65rem 1rem !important; border-bottom: 1px solid #F0EDE5 !important; color: #1C1C1C !important; }

.stTabs [data-baseweb="tab-list"] { gap: 0; background: transparent; border-bottom: 1px solid #E0DDD5; }
.stTabs [data-baseweb="tab"] { font-family: 'DM Sans', sans-serif !important; font-size: 0.88rem !important; font-weight: 400 !important; color: #AAA !important; background: transparent !important; border: none !important; border-bottom: 2px solid transparent !important; border-radius: 0 !important; padding: 0.65rem 1.4rem !important; }
.stTabs [aria-selected="true"] { color: #1C1C1C !important; border-bottom: 2px solid #1C1C1C !important; font-weight: 500 !important; }
.stTabs [data-baseweb="tab-panel"] { padding-top: 0 !important; }
.info-count { font-size: 0.8rem; color: #999; margin-bottom: 0.8rem; }

[data-testid="manage-app-button"],
.st-emotion-cache-ztfqz8,
footer .st-emotion-cache-ztfqz8,
[class*="viewerBadge"],
#MainMenu { visibility: hidden !important; display: none !important; }
.stDeployButton { display: none !important; }
div[data-testid="stStatusWidget"] { display: none !important; }

.user-card { background: #FFFFFF; border: 1px solid #E8E5DE; border-radius: 10px; padding: 1rem 1.2rem; margin-bottom: 0.7rem; }
.user-card-name { font-weight: 600; font-size: 0.95rem; color: #1C1C1C; }
.user-card-meta { font-size: 0.75rem; color: #AAA; margin-top: 0.2rem; }

[data-testid="stHorizontalBlock"] > div [data-testid="stButton"] > button {
    background: #F0EDE5 !important; color: #555 !important;
    border: 1px solid #DDDAD2 !important; border-radius: 20px !important;
    padding: 0.2rem 0.75rem !important; font-size: 0.78rem !important;
    font-weight: 400 !important; margin-top: 0 !important;
    letter-spacing: 0 !important;
}
[data-testid="stHorizontalBlock"] > div [data-testid="stButton"] > button:hover {
    background: #E8E5DE !important; opacity: 1 !important;
}

/* Edit form card */
.edit-card {
    background: #FFFFFF;
    border: 1px solid #DDDAD2;
    border-radius: 12px;
    padding: 1.5rem;
    margin-top: 1rem;
}

/* ── ALERTES LISIBLES EN NOIR ── */
div[data-testid="stAlert"] p,
div[data-testid="stAlert"] span,
div[data-testid="stAlert"] { color: #1C1C1C !important; }
div[data-testid="stAlert"][data-alert-type="warning"],
div[data-testid="stAlert"][data-alert-type="info"] {
    background: #F5F3EE !important;
    border: 1px solid #DDDAD2 !important;
    border-radius: 8px !important;
}
.stWarning > div, .stInfo > div {
    background: #F5F3EE !important;
    border: 1px solid #DDDAD2 !important;
    color: #1C1C1C !important;
    border-radius: 8px !important;
}
.stWarning svg, .stInfo svg { color: #1C1C1C !important; fill: #1C1C1C !important; }
/* Streamlit v1.3x+ selector */
div[class*="stAlert"] { color: #1C1C1C !important; }
div[class*="stAlert"] * { color: #1C1C1C !important; }

/* ══════════════════════════════════════════════════
   DATA EDITOR — GLIDE DATA GRID — TEXTE LISIBLE
   ══════════════════════════════════════════════════ */

/* Conteneur principal */
[data-testid="stDataEditor"] {
    background: #FFFFFF !important;
    border: 1px solid #E0DDD5 !important;
    border-radius: 10px !important;
    overflow: hidden !important;
}

/* Variables CSS du canvas Glide Data Grid */
[data-testid="stDataEditor"] {
    --gdg-text-dark:             #1C1C1C !important;
    --gdg-text-medium:           #333333 !important;
    --gdg-text-light:            #555555 !important;
    --gdg-text-header:           #555555 !important;
    --gdg-text-group-header:     #555555 !important;
    --gdg-bg-cell:               #FFFFFF !important;
    --gdg-bg-cell-medium:        #FAFAF8 !important;
    --gdg-bg-header:             #F0EDE5 !important;
    --gdg-bg-header-has-focus:   #E8E5DE !important;
    --gdg-bg-header-hovered:     #E8E5DE !important;
    --gdg-border-color:          #E0DDD5 !important;
    --gdg-horizontal-border-color: #E0DDD5 !important;
    --gdg-accent-color:          #1C1C1C !important;
    --gdg-accent-light:          rgba(28,28,28,0.12) !important;
    --gdg-selection-color:       rgba(28,28,28,0.08) !important;
    --gdg-bg-selected-header:    #E8E5DE !important;
    --gdg-link-color:            #1C1C1C !important;
    --gdg-cell-horizontal-padding: 8px !important;
}

/* Input texte actif dans cellule */
[data-testid="stDataEditor"] input,
[data-testid="stDataEditor"] textarea {
    color: #1C1C1C !important;
    -webkit-text-fill-color: #1C1C1C !important;
    background: #FFFFFF !important;
    caret-color: #1C1C1C !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.88rem !important;
}

/* ── DROPDOWN / POPOVER DU DATA_EDITOR (flotte dans le body) ──
   Le popup de SelectboxColumn est rendu HORS du stDataEditor,
   directement dans le portail du DOM → on cible via Portal/Popover */

/* Fond du portail popover */
[data-baseweb="popover"],
[data-baseweb="tooltip"],
div[class*="portal"] [data-baseweb="popover"] {
    background: #FFFFFF !important;
}

/* Liste d'options dans le menu déroulant */
[data-baseweb="menu"],
[data-baseweb="menu"] ul,
[data-baseweb="menu"] li,
[data-baseweb="option"],
[role="option"],
[role="listbox"],
[role="listbox"] li {
    background: #FFFFFF !important;
    color: #1C1C1C !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.88rem !important;
}

/* Hover sur option */
[data-baseweb="option"]:hover,
[role="option"]:hover,
[data-baseweb="option"][aria-selected="true"],
[role="option"][aria-selected="true"] {
    background: #F0EDE5 !important;
    color: #1C1C1C !important;
}

/* Texte sélectionné dans la cellule (tag/chip) */
[data-testid="stDataEditor"] [data-baseweb="tag"],
[data-testid="stDataEditor"] [data-baseweb="tag"] span {
    background: #E8E5DE !important;
    color: #1C1C1C !important;
}

/* Input de recherche dans le dropdown */
[data-baseweb="select"] input,
[data-baseweb="combobox"] input,
[data-baseweb="popover"] input {
    color: #1C1C1C !important;
    -webkit-text-fill-color: #1C1C1C !important;
    background: #F7F6F2 !important;
    caret-color: #1C1C1C !important;
}

/* Overlay/backdrop du popover */
[data-baseweb="popover"] > div,
div[data-popper-placement] {
    background: #FFFFFF !important;
    border: 1px solid #E0DDD5 !important;
    border-radius: 8px !important;
    box-shadow: 0 4px 12px rgba(0,0,0,0.08) !important;
}

/* Texte dans les popovers généraux */
[data-baseweb="popover"] *,
div[data-popper-placement] * {
    color: #1C1C1C !important;
}

@media screen and (max-width: 768px) {
    .block-container { padding: 1rem 1rem 2rem 1rem !important; max-width: 100% !important; }
    .auth-left { display: none !important; }
    .auth-brand { font-size: 2.4rem !important; }
    .auth-form-title { font-size: 1.6rem !important; }
    .topbar { flex-direction: column !important; align-items: flex-start !important; gap: 0.4rem !important; margin-bottom: 0.8rem !important; }
    .topbar-user { padding-top: 0 !important; font-size: 0.75rem !important; }
    .page-title { font-size: 1.8rem !important; }
    .page-subtitle { font-size: 0.72rem !important; margin-bottom: 1rem !important; }
    .metric-row { display: grid !important; grid-template-columns: 1fr 1fr !important; gap: 0.6rem !important; margin-bottom: 1.2rem !important; }
    .metric-card { padding: 0.8rem 1rem !important; }
    .metric-label { font-size: 0.65rem !important; }
    .metric-value { font-size: 1.2rem !important; }
    .section-title { font-size: 1.1rem !important; margin-top: 1.2rem !important; margin-bottom: 0.8rem !important; }
    .stTabs [data-baseweb="tab-list"] { overflow-x: auto !important; overflow-y: hidden !important; flex-wrap: nowrap !important; -webkit-overflow-scrolling: touch !important; scrollbar-width: none !important; }
    .stTabs [data-baseweb="tab-list"]::-webkit-scrollbar { display: none !important; }
    .stTabs [data-baseweb="tab"] { font-size: 0.78rem !important; padding: 0.5rem 0.85rem !important; white-space: nowrap !important; flex-shrink: 0 !important; }
    [data-testid="column"] { width: 100% !important; flex: 0 0 100% !important; min-width: 100% !important; }
    [data-testid="stHorizontalBlock"] { flex-direction: column !important; gap: 0 !important; }
    .stTextInput > div > div > input, .stNumberInput > div > div > input { font-size: 1rem !important; min-height: 44px !important; }
    .stButton > button { width: 100% !important; padding: 0.8rem 1rem !important; font-size: 0.95rem !important; min-height: 44px !important; }
    .stDataFrame { overflow-x: auto !important; }
    .stDataFrame table { font-size: 0.78rem !important; min-width: 500px !important; }
}

@media screen and (max-width: 480px) {
    .block-container { padding: 0.7rem 0.6rem 1.5rem 0.6rem !important; }
    .page-title { font-size: 1.5rem !important; }
    .metric-value { font-size: 1rem !important; }
    .auth-form-title { font-size: 1.35rem !important; }
}
</style>
""", unsafe_allow_html=True)


# ─── Google Sheets ─────────────────────────────────────────────────────────────
@st.cache_resource
def get_client():
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=SCOPES)
    return gspread.authorize(creds)

@st.cache_data(ttl=30)
def _load_sheet_cached(sheet_name):
    sh = get_client().open_by_key(SPREADSHEET_ID)
    data = sh.worksheet(sheet_name).get_all_records()
    return pd.DataFrame(data) if data else pd.DataFrame()

def load_sheet(sheet_name):
    return _load_sheet_cached(sheet_name)

def clear_data_cache():
    _load_sheet_cached.clear()

def save_sheet(df, sheet_name):
    sh = get_client().open_by_key(SPREADSHEET_ID)
    ws = sh.worksheet(sheet_name)
    ws.clear()
    df2 = df.fillna("").astype(str)
    ws.update([df2.columns.tolist()] + df2.values.tolist())

def append_row(row_dict, sheet_name):
    sh = get_client().open_by_key(SPREADSHEET_ID)
    ws = sh.worksheet(sheet_name)
    headers = ws.row_values(1)
    ws.append_row([str(row_dict.get(h, "")) for h in headers])

def ensure_users_sheet():
    sh = get_client().open_by_key(SPREADSHEET_ID)
    try:
        sh.worksheet("Utilisateurs")
    except gspread.WorksheetNotFound:
        ws = sh.add_worksheet("Utilisateurs", rows=500, cols=12)
        ws.update([["username","password_hash","role","statut","lots_autorises","created_at","nom","prenom"]])

# ─── Auth helpers ──────────────────────────────────────────────────────────────
def hash_password(p): return bcrypt.hashpw(p.encode(), bcrypt.gensalt()).decode()
def check_password(p, h):
    try: return bcrypt.checkpw(p.encode(), h.encode())
    except: return False

def get_users() -> pd.DataFrame:
    try:
        df = load_sheet("Utilisateurs")
        if df.empty:
            df = pd.DataFrame(columns=["username","password_hash","role","statut","lots_autorises","created_at","nom","prenom"])
        for col in ["nom","prenom"]:
            if col not in df.columns: df[col] = ""
        return df
    except gspread.exceptions.WorksheetNotFound:
        ensure_users_sheet()
        return pd.DataFrame(columns=["username","password_hash","role","statut","lots_autorises","created_at","nom","prenom"])
    except Exception:
        return pd.DataFrame(columns=["username","password_hash","role","statut","lots_autorises","created_at","nom","prenom"])

def save_users(df): save_sheet(df, "Utilisateurs")

def update_session_for_user(uname, new_role, new_lots_list):
    store = _session_store()
    for token, entry in store.items():
        u = entry.get("user", {})
        if u.get("username", "").lower() == uname.lower():
            u["role"] = new_role
            u["lots_autorises"] = new_lots_list
            entry["user"] = u
            break

# ─── Sécurité ──────────────────────────────────────────────────────────────────
def h(val: str) -> str:
    return _html.escape(str(val))

def sanitize_text(val: str) -> str:
    val = str(val).strip()
    if val and val[0] in ('=', '+', '-', '@', '|', '%', '\t', '\r', '\n'):
        val = "'" + val
    val = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', val)
    return val

def find_user(uname):
    users = get_users()
    row = users[users["username"].str.lower() == uname.lower()]
    return None if row.empty else row.iloc[0].to_dict()

@st.cache_resource
def _lockout_store():
    return {}

def is_locked_out(uname):
    store = _lockout_store()
    key_lock = f"lockout_{uname.lower()}"
    key_att  = f"attempts_{uname.lower()}"
    if key_lock in store:
        elapsed = time.time() - store[key_lock]
        if elapsed < LOCKOUT_SECONDS: return True
        del store[key_lock]
        store[key_att] = 0
    return False

def record_failed(uname):
    store = _lockout_store()
    key_att  = f"attempts_{uname.lower()}"
    key_lock = f"lockout_{uname.lower()}"
    store[key_att] = store.get(key_att, 0) + 1
    if store[key_att] >= MAX_ATTEMPTS:
        store[key_lock] = time.time()

def reset_attempts(uname):
    store = _lockout_store()
    store.pop(f"attempts_{uname.lower()}", None)
    store.pop(f"lockout_{uname.lower()}", None)

def admin_exists():
    u = get_users(); return not u.empty and not u[u["role"]=="admin"].empty

def count_pending():
    try: return len(get_users().query("statut == 'en_attente'"))
    except: return 0

import hashlib as _hl

SECRET_KEY = st.secrets.get("session_secret", secrets.token_hex(32))

@st.cache_resource
def _session_store():
    return {}

def _make_token(_unused=None):
    return secrets.token_urlsafe(40)

def _store_session(user_dict):
    token = _make_token()
    _session_store()[token] = {
        "user": user_dict,
        "expires_at": time.time() + SESSION_TTL
    }
    return token

def _load_session(token):
    if not token: return None
    entry = _session_store().get(token)
    if not entry: return None
    if time.time() > entry["expires_at"]:
        _session_store().pop(token, None)
        return None
    return entry["user"]

def _clear_session(token):
    _session_store().pop(token, None)

# ─── Session state init ────────────────────────────────────────────────────────
for k, v in [("authenticated", False), ("username", ""), ("role", ""),
              ("lots_autorises", []), ("auth_page", "login"), ("_sess_token", "")]:
    if k not in st.session_state:
        st.session_state[k] = v

if not st.session_state.authenticated:
    token_url = st.query_params.get("t", "")
    if token_url:
        u = _load_session(token_url)
        if u:
            st.session_state.authenticated = True
            st.session_state.username = u["username"]
            st.session_state.role = u["role"]
            st.session_state.lots_autorises = u["lots_autorises"]
            st.session_state["_sess_token"] = token_url
        else:
            st.query_params.clear()

def warn(m): st.warning(m)
def err(m):  st.error(m)
def ok(m):   st.success(m)

# ═══════════════════════════════════════════════════════════════════════════════
# LOGIN
# ═══════════════════════════════════════════════════════════════════════════════
def page_login():
    l, r = st.columns([1.15, 1])
    with l:
        st.markdown("""
        <div class="auth-left">
          <div class="auth-logo-area">
            <div class="auth-brand">Mahal</div>
            <div class="auth-brand-sub">Gestion &amp; Transactions</div>
          </div>
          <div class="auth-left-sep"></div>
          <div class="auth-left-bottom">
            <div class="auth-tagline">
              Suivez vos lots, vos achats, vos ventes et vos dépenses — simplement et en temps réel.
            </div>
            <div class="auth-year">© 2025 — Plateforme privée</div>
          </div>
        </div>
        """, unsafe_allow_html=True)
    with r:
        st.markdown("""
        <div class="auth-right-inner">
          <div class="auth-badge"><span class="auth-badge-dot"></span>Accès sécurisé</div>
          <div class="auth-eyebrow">Bienvenue</div>
          <div class="auth-form-title">Connexion</div>
          <div class="auth-form-desc">Entrez vos identifiants pour accéder à votre tableau de bord.</div>
        </div>
        """, unsafe_allow_html=True)

        uname = st.text_input("Nom d'utilisateur", key="login_user", placeholder="Votre identifiant")
        pwd   = st.text_input("Mot de passe", type="password", key="login_pass", placeholder="••••••••")

        if st.button("Se connecter →", key="btn_login", use_container_width=True):
            if not uname or not pwd: err("Remplis tous les champs."); return
            if is_locked_out(uname):
                rem = int(LOCKOUT_SECONDS - (time.time() - _lockout_store().get(f"lockout_{uname.lower()}", time.time())))
                err(f"Trop de tentatives. Réessaie dans {rem//60}m{rem%60}s."); return
            user = find_user(uname)
            if not user or not check_password(pwd, str(user["password_hash"])):
                record_failed(uname)
                att = _lockout_store().get(f"attempts_{uname.lower()}", 0)
                err(f"Identifiants incorrects. {MAX_ATTEMPTS - att} tentative(s) restante(s)."); return
            if str(user["statut"]) == "en_attente":
                warn("Connexion impossible pour le moment. Contacte l'administrateur."); return
            if str(user["statut"]) == "rejeté":
                err("Connexion impossible pour le moment. Contacte l'administrateur."); return
            reset_attempts(uname)
            lots_raw = str(user.get("lots_autorises",""))
            lots_list = [l.strip() for l in lots_raw.split(",") if l.strip()]
            st.session_state.authenticated = True
            st.session_state.username = str(user["username"])
            st.session_state.role = str(user["role"])
            st.session_state.lots_autorises = lots_list
            token = _store_session({"username": str(user["username"]), "role": str(user["role"]), "lots_autorises": lots_list})
            st.session_state["_sess_token"] = token
            st.query_params["t"] = token
            st.rerun()

        st.markdown('<div class="auth-divider">ou</div>', unsafe_allow_html=True)
        if st.button("Créer un compte", key="btn_go_register", use_container_width=True):
            st.session_state.auth_page = "register"; st.rerun()
        st.markdown('<div class="auth-switch-text">Accès réservé aux membres autorisés.</div>', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# INSCRIPTION
# ═══════════════════════════════════════════════════════════════════════════════
def page_register():
    l, r = st.columns([1.15, 1])
    with l:
        st.markdown("""
        <div class="auth-left">
          <div class="auth-logo-area">
            <div class="auth-brand">Mahal</div>
            <div class="auth-brand-sub">Créer un compte</div>
          </div>
          <div class="auth-left-sep"></div>
          <div class="auth-left-bottom">
            <div class="auth-tagline">
              Votre demande sera examinée par un administrateur avant activation de votre accès.
            </div>
            <div class="auth-year">© 2025 — Plateforme privée</div>
          </div>
        </div>
        """, unsafe_allow_html=True)
    with r:
        st.markdown("""
        <div class="auth-right-inner">
          <div class="auth-badge"><span class="auth-badge-dot"></span>Inscription</div>
          <div class="auth-eyebrow">Nouveau membre</div>
          <div class="auth-form-title">Créer un compte</div>
          <div class="auth-form-desc">Votre demande sera soumise à l'approbation de l'administrateur.</div>
        </div>
        """, unsafe_allow_html=True)

        rc1, rc2 = st.columns(2, gap="small")
        with rc1: prenom = st.text_input("Prénom", key="reg_prenom", placeholder="Votre prénom")
        with rc2: nom    = st.text_input("Nom", key="reg_nom", placeholder="Votre nom")
        uname = st.text_input("Nom d'utilisateur", key="reg_user", placeholder="Choisir un identifiant")
        pwd1  = st.text_input("Mot de passe", type="password", key="reg_pass", placeholder="8 car. min. avec chiffres")
        pwd2  = st.text_input("Confirmer le mot de passe", type="password", key="reg_pass2", placeholder="••••••••")

        if st.button("S'inscrire →", key="btn_register", use_container_width=True,
                     disabled=st.session_state.get("registering", False)):
            if st.session_state.get("registering", False):
                return
            st.session_state["registering"] = True

            if not all([uname, pwd1, pwd2, prenom, nom]):
                st.session_state.pop("registering", None); err("Remplis tous les champs."); return
            if len(uname) < 3:
                st.session_state.pop("registering", None); err("Identifiant trop court (3 car. min.)."); return
            if not re.match(r'^[a-zA-Z0-9_\-\.]+$', uname):
                st.session_state.pop("registering", None); err("Identifiant invalide (lettres, chiffres, _ - . uniquement)."); return
            if len(pwd1) < 8:
                st.session_state.pop("registering", None); err("Mot de passe trop court (8 car. min.)."); return
            if not any(c.isdigit() for c in pwd1) or not any(c.isalpha() for c in pwd1):
                st.session_state.pop("registering", None); err("Le mot de passe doit contenir lettres et chiffres."); return
            if pwd1 != pwd2:
                st.session_state.pop("registering", None); err("Les mots de passe ne correspondent pas."); return
            _load_sheet_cached.clear()
            if find_user(uname):
                st.session_state.pop("registering", None); err("Nom d'utilisateur déjà pris."); return

            is_first = not admin_exists()
            new_u = {"username": sanitize_text(uname),
                     "password_hash": hash_password(pwd1),
                     "role": "admin" if is_first else "sous-admin",
                     "statut": "approuvé" if is_first else "en_attente",
                     "lots_autorises": "",
                     "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                     "nom":    sanitize_text(nom.upper()),
                     "prenom": sanitize_text(prenom.capitalize())}
            try:
                with st.spinner("Enregistrement…"):
                    append_row(new_u, "Utilisateurs")
                    _load_sheet_cached.clear()
                msg = "Compte créé ! Tu peux te connecter." if is_first else "Inscription envoyée — en attente d'approbation."
                ok(msg)
                st.session_state.pop("registering", None)
            except Exception as e:
                st.session_state.pop("registering", None)
                err(f"Erreur : {e}")

        st.markdown('<div class="auth-divider">ou</div>', unsafe_allow_html=True)
        if st.button("Retour à la connexion", key="btn_go_login", use_container_width=True):
            st.session_state.auth_page = "login"; st.rerun()


# ─── Routing ──────────────────────────────────────────────────────────────────
if not st.session_state.authenticated:
    if st.session_state.auth_page == "login": page_login()
    else: page_register()
    st.stop()

# ═══════════════════════════════════════════════════════════════════════════════
# APP PRINCIPALE
# ═══════════════════════════════════════════════════════════════════════════════
role           = st.session_state.role
username       = st.session_state.username
is_admin       = (role == "admin")
is_sous_admin  = (role == "sous-admin")
lots_autorises = st.session_state.lots_autorises

def add_quantity_column(df):
    if 'Quantité (pièces)' not in df.columns: df['Quantité (pièces)'] = 1
    return df

def to_numeric(df, cols):
    for c in cols:
        if c in df.columns: df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)
    return df

def compute_resume_personne(t):
    EMPTY = pd.DataFrame(columns=['Personne','Total Achats','Total Ventes','Total Dépenses','Résultat'])
    if t.empty or 'Personne' not in t.columns: return EMPTY
    t = to_numeric(t.copy(), ['Montant (MAD)']); t = t.dropna(subset=['Personne'])
    if t.empty: return EMPTY
    g = t.groupby('Personne').apply(lambda x: pd.Series({
        'Total Achats':   x.loc[x['Type (Achat/Vente/Dépense)']=='ACHAT','Montant (MAD)'].sum(),
        'Total Ventes':   x.loc[x['Type (Achat/Vente/Dépense)']=='VENTE','Montant (MAD)'].sum(),
        'Total Dépenses': x.loc[x['Type (Achat/Vente/Dépense)']=='DÉPENSE','Montant (MAD)'].sum(),
    }), include_groups=False).reset_index()
    if g.empty or 'Total Ventes' not in g.columns: return EMPTY
    g['Résultat'] = g['Total Ventes'] - (g['Total Achats'] + g['Total Dépenses']); return g

def compute_suivi_lot(t):
    EMPTY = pd.DataFrame(columns=['Lot','Total Achats','Total Ventes','Total Dépenses','Stock Restant (pièces)','Résultat'])
    if t.empty or 'Lot' not in t.columns: return EMPTY
    t = to_numeric(t.copy(), ['Montant (MAD)','Quantité (pièces)'])
    t = t.dropna(subset=['Lot']); t = t[t['Lot'].astype(str).str.strip() != '']
    if t.empty: return EMPTY
    g = t.groupby('Lot').apply(lambda x: pd.Series({
        'Total Achats':           x.loc[x['Type (Achat/Vente/Dépense)']=='ACHAT','Montant (MAD)'].sum(),
        'Total Ventes':           x.loc[x['Type (Achat/Vente/Dépense)']=='VENTE','Montant (MAD)'].sum(),
        'Total Dépenses':         x.loc[x['Type (Achat/Vente/Dépense)']=='DÉPENSE','Montant (MAD)'].sum(),
        'Stock Restant (pièces)': (x.loc[x['Type (Achat/Vente/Dépense)']=='ACHAT','Quantité (pièces)'].sum()
                                 - x.loc[x['Type (Achat/Vente/Dépense)']=='VENTE','Quantité (pièces)'].sum()),
    }), include_groups=False).reset_index()
    if g.empty or 'Total Ventes' not in g.columns: return EMPTY
    g['Résultat'] = g['Total Ventes'] - (g['Total Achats'] + g['Total Dépenses']); return g

def compute_historique_lot(t):
    if t.empty or 'Lot' not in t.columns:
        return pd.DataFrame()
    cols = [c for c in ['Lot','Date','Type (Achat/Vente/Dépense)','Personne','Description',
                         'Montant (MAD)','Quantité (pièces)','Remarque','Statut du lot'] if c in t.columns]
    df = t[cols].copy()
    df = df[df['Lot'].astype(str).str.strip() != '']
    df = df.sort_values(['Lot','Date'], ascending=[True, False])
    return df

def compute_suivi_avances(t):
    EMPTY = pd.DataFrame(columns=['Lot','Personne','Total Avancé','Total Encaissé','Solde'])
    if t.empty or 'Lot' not in t.columns: return EMPTY
    t = to_numeric(t.copy(), ['Montant (MAD)']); t = t.dropna(subset=['Lot','Personne'])
    if t.empty: return EMPTY
    g = t.groupby(['Lot','Personne']).apply(lambda x: pd.Series({
        'Total Avancé':   x.loc[x['Type (Achat/Vente/Dépense)'].isin(['ACHAT','DÉPENSE']),'Montant (MAD)'].sum(),
        'Total Encaissé': x.loc[x['Type (Achat/Vente/Dépense)']=='VENTE','Montant (MAD)'].sum(),
    }), include_groups=False).reset_index()
    if g.empty or 'Total Encaissé' not in g.columns: return EMPTY
    g['Solde'] = g['Total Encaissé'] - g['Total Avancé']; return g

# ─── Chargement ────────────────────────────────────────────────────────────────
try:
    transactions_all = load_sheet("Gestion globale")
except Exception as e:
    st.error(f"Impossible de charger les données : {e}"); st.stop()

transactions_all = add_quantity_column(transactions_all)
transactions_all = to_numeric(transactions_all, ['Montant (MAD)','Quantité (pièces)'])

# Vue filtrée pour non-admins
if is_admin:
    transactions = transactions_all.copy()
else:
    if lots_autorises:
        transactions = transactions_all[transactions_all['Lot'].astype(str).isin(lots_autorises)]
    else:
        transactions = transactions_all.iloc[0:0]

lots_existants       = sorted([l for l in transactions['Lot'].dropna().astype(str).unique() if l.strip()])
personnes_existantes = sorted([p for p in transactions['Personne'].dropna().astype(str).unique() if p.strip()])
pending_count = count_pending() if is_admin else 0

# ─── TOP BAR ───────────────────────────────────────────────────────────────────
if is_admin:
    role_class = "role-admin"
    role_label = "Admin"
elif is_sous_admin:
    role_class = "role-sous-admin"
    role_label = "Sous-Admin"
else:
    role_class = "role-visiteur"
    role_label = "Visiteur"

notif_html = f'<span class="notif-badge">{pending_count}</span>' if (is_admin and pending_count > 0) else ""

if is_admin and pending_count > 0:
    st.markdown(f"""
    <div class="notif-banner">
      <div class="notif-banner-dot"></div>
      <span><strong>{pending_count} nouvelle(s) demande(s) d'inscription</strong> en attente
      — rendez-vous dans l'onglet <strong>Utilisateurs</strong>.</span>
    </div>
    """, unsafe_allow_html=True)

st.markdown(f"""
<div class="topbar">
  <div>
    <div class="page-title">Mahal</div>
    <div class="page-subtitle">Gestion de stock et transactions</div>
  </div>
  <div style="display:flex;align-items:center;padding-top:0.8rem">
    <span class="topbar-user">{h(username)}</span>
    <span class="topbar-role {role_class}">{role_label}</span>{notif_html}
  </div>
</div>
""", unsafe_allow_html=True)

dcol = st.columns([6, 1])[1]
with dcol:
    if st.button("Déconnexion", key="btn_logout"):
        _clear_session(st.session_state.get("_sess_token", ""))
        st.query_params.clear()
        for k in ["authenticated","username","role","lots_autorises","_sess_token"]:
            st.session_state.pop(k, None)
        st.session_state.auth_page = "login"
        st.rerun()

# ─── Métriques ─────────────────────────────────────────────────────────────────
ta = transactions[transactions['Type (Achat/Vente/Dépense)']=='ACHAT']['Montant (MAD)'].sum()
tv = transactions[transactions['Type (Achat/Vente/Dépense)']=='VENTE']['Montant (MAD)'].sum()
td = transactions[transactions['Type (Achat/Vente/Dépense)']=='DÉPENSE']['Montant (MAD)'].sum()
rn = tv - (ta + td)
cr = "positive" if rn >= 0 else "negative"

st.markdown(f"""
<div class="metric-row">
  <div class="metric-card"><div class="metric-label">Total Achats</div><div class="metric-value">{ta:,.0f} <small style="opacity:.5">MAD</small></div></div>
  <div class="metric-card"><div class="metric-label">Total Ventes</div><div class="metric-value">{tv:,.0f} <small style="opacity:.5">MAD</small></div></div>
  <div class="metric-card"><div class="metric-label">Total Dépenses</div><div class="metric-value">{td:,.0f} <small style="opacity:.5">MAD</small></div></div>
  <div class="metric-card"><div class="metric-label">Résultat net</div><div class="metric-value {cr}">{rn:+,.0f} <small style="opacity:.5">MAD</small></div></div>
</div>
""", unsafe_allow_html=True)

# ─── Onglets ───────────────────────────────────────────────────────────────────
if is_admin:
    utl = f"Utilisateurs ({pending_count})" if pending_count > 0 else "Utilisateurs"
    tabs = st.tabs(["Nouvelle transaction","Recherche","Graphiques","Catalogue des lots",
                    "Résumé par personne","Historique des lots","Suivi des avances", utl,"Finance",])
    tab1,tab2,tab3,tab4,tab5,tab6,tab7,tab8,tab9, = tabs
elif is_sous_admin:
    tabs = st.tabs(["Nouvelle transaction","Mes lots","Recherche","Graphiques","Modifier une transaction"])
    tab1,tab2,tab3,tab4,tab5 = tabs
else:
    tabs = st.tabs(["Mes lots","Recherche","Graphiques"])
    tab1,tab2,tab3 = tabs


# ═══════════════════════════════════════════════════════════════════════════════
# HELPER — Formulaire d'édition de transaction
# ═══════════════════════════════════════════════════════════════════════════════
def render_edit_transaction_form(transactions_df, lots_filter=None, personne_filter=None, key_prefix="edit"):
    """
    Affiche le sélecteur + formulaire d'édition d'une transaction.
    - lots_filter : liste des lots autorisés (None = tous)
    - personne_filter : forcer le champ Personne à une valeur (pour sous-admin)
    """
    lots_all_edit = sorted(transactions_df['Lot'].dropna().astype(str).unique().tolist())
    personnes_all_edit = sorted(transactions_df['Personne'].dropna().astype(str).unique().tolist())

    sf1, sf2, sf3 = st.columns(3, gap="large")
    with sf1:
        lots_opts = ["Tous"] + (lots_filter if lots_filter else lots_all_edit)
        f_lot = st.selectbox("Filtrer par lot", lots_opts, key=f"{key_prefix}_flot")
    with sf2:
        if personne_filter:
            f_pers = personne_filter
            st.text_input("Filtrer par personne", value=f_pers, disabled=True, key=f"{key_prefix}_fpers_disp")
        else:
            pers_f = ["Tous"] + personnes_all_edit
            f_pers = st.selectbox("Filtrer par personne", pers_f, key=f"{key_prefix}_fpers")
    with sf3:
        f_type = st.selectbox("Filtrer par type", ["Tous","ACHAT","VENTE","DÉPENSE"], key=f"{key_prefix}_ftype")

    df_edit = transactions_df.copy().reset_index(drop=False)  # garde l'index original dans colonne 'index'
    if f_lot  != "Tous": df_edit = df_edit[df_edit['Lot']==f_lot]
    if personne_filter:
        df_edit = df_edit[df_edit['Personne'].astype(str).str.upper()==personne_filter.upper()]
    elif f_pers != "Tous":
        df_edit = df_edit[df_edit['Personne']==f_pers]
    if f_type != "Tous": df_edit = df_edit[df_edit['Type (Achat/Vente/Dépense)']==f_type]

    if df_edit.empty:
        st.warning("Aucune transaction ne correspond aux filtres.")
        return transactions_df

    def make_label(r):
        return f"{r.get('Date','')} | {r.get('Lot','')} | {r.get('Personne','')} | {r.get('Type (Achat/Vente/Dépense)','')} | {float(r.get('Montant (MAD)',0)):,.0f} MAD"

    labels = [make_label(row) for _, row in df_edit.iterrows()]
    orig_indices = df_edit['index'].tolist()

    st.caption(f"{len(df_edit)} transaction(s) filtrée(s)")
    choix_label = st.selectbox("Sélectionner la transaction à modifier", ["— sélectionner —"] + labels, key=f"{key_prefix}_sel")

    if choix_label == "— sélectionner —":
        return transactions_df

    ligne_idx = labels.index(choix_label)
    orig_idx  = orig_indices[ligne_idx]
    row_sel   = transactions_df.loc[orig_idx]

    st.markdown('<div class="edit-card">', unsafe_allow_html=True)
    st.markdown(f"**Modifier la transaction — {h(str(row_sel.get('Lot','')))}**")

    ec1, ec2, ec3 = st.columns(3, gap="large")

    with ec1:
        try:
            date_val = datetime.strptime(str(row_sel.get('Date','')), "%Y-%m-%d").date()
        except:
            date_val = datetime.now().date()
        new_date = st.date_input("Date", value=date_val, key=f"{key_prefix}_date")

        if personne_filter:
            new_personne = personne_filter.upper()
            st.text_input("Personne (fixé)", value=new_personne, disabled=True, key=f"{key_prefix}_pers_disp")
        else:
            new_personne = st.text_input("Personne", value=str(row_sel.get('Personne','')), key=f"{key_prefix}_pers")

        types_list = ["ACHAT","VENTE","DÉPENSE"]
        cur_type = str(row_sel.get('Type (Achat/Vente/Dépense)','ACHAT'))
        tidx = types_list.index(cur_type) if cur_type in types_list else 0
        new_type = st.selectbox("Type de transaction", types_list, index=tidx, key=f"{key_prefix}_type")

    with ec2:
        if lots_filter:
            lot_opts = lots_filter
        else:
            lot_opts = lots_all_edit
        cur_lot = str(row_sel.get('Lot',''))
        lidx = lot_opts.index(cur_lot) if cur_lot in lot_opts else 0
        new_lot = st.selectbox("Lot", lot_opts, index=lidx, key=f"{key_prefix}_lot")

        new_description = st.text_input("Description", value=str(row_sel.get('Description','')), key=f"{key_prefix}_desc")
        new_montant = st.number_input("Montant (MAD)", min_value=0.0, step=0.01,
                                       value=float(row_sel.get('Montant (MAD)',0)), key=f"{key_prefix}_montant")

    with ec3:
        new_quantite = st.number_input("Quantité (pièces)", min_value=1, step=1,
                                        value=max(1, int(float(row_sel.get('Quantité (pièces)',1)))),
                                        key=f"{key_prefix}_qty")
        new_mode = st.text_input("Mode de paiement", value=str(row_sel.get('Mode de paiement','')), key=f"{key_prefix}_mode")
        statuts = ["Actif","Fermé"]
        cur_statut = str(row_sel.get('Statut du lot','Actif'))
        sidx = statuts.index(cur_statut) if cur_statut in statuts else 0
        new_statut = st.selectbox("Statut du lot", statuts, index=sidx, key=f"{key_prefix}_statut")

    new_remarque = st.text_input("Remarque", value=str(row_sel.get('Remarque','')), key=f"{key_prefix}_remarque")
    st.markdown('</div>', unsafe_allow_html=True)

    if st.button("💾 Enregistrer les modifications", key=f"{key_prefix}_save"):
        transactions_df.at[orig_idx, 'Date']                       = str(new_date)
        transactions_df.at[orig_idx, 'Personne']                   = sanitize_text(new_personne.upper())
        transactions_df.at[orig_idx, 'Type (Achat/Vente/Dépense)'] = new_type
        transactions_df.at[orig_idx, 'Lot']                        = sanitize_text(new_lot.upper())
        transactions_df.at[orig_idx, 'Description']                = sanitize_text(new_description)
        transactions_df.at[orig_idx, 'Montant (MAD)']              = new_montant
        transactions_df.at[orig_idx, 'Quantité (pièces)']          = new_quantite
        transactions_df.at[orig_idx, 'Mode de paiement']           = sanitize_text(new_mode)
        transactions_df.at[orig_idx, 'Remarque']                   = sanitize_text(new_remarque)
        transactions_df.at[orig_idx, 'Statut du lot']              = new_statut
        try:
            save_sheet(transactions_df, "Gestion globale")
            st.success("✅ Transaction modifiée avec succès.")
            clear_data_cache()
            st.rerun()
        except Exception as e:
            st.error(f"Erreur lors de la sauvegarde : {e}")

    return transactions_df


# ═══════════════════════════════════════════════════════════════════════════════
# ADMIN
# ═══════════════════════════════════════════════════════════════════════════════
if is_admin:

    with tab1:
        st.markdown('<div class="section-title">Nouvelle transaction</div>', unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3, gap="large")

        with c1:
            date = st.date_input("Date", datetime.now())
            personne_val = st.selectbox(
                "Personne",
                options=personnes_existantes,
                index=None,
                placeholder="Sélectionner ou taper un nom...",
                key="sel_personne"
            )
            if personne_val is None:
                personne_val = st.text_input("Nouveau nom", key="new_personne_input", placeholder="Ex: DUPONT")
            type_trans = st.selectbox("Type de transaction", ["ACHAT","VENTE","DÉPENSE"])

        with c2:
            lot_val = st.selectbox(
                "Lot",
                options=lots_existants,
                index=None,
                placeholder="Sélectionner ou taper un lot...",
                key="sel_lot"
            )
            if lot_val is None:
                lot_val = st.text_input("Nouveau lot", key="new_lot_input", placeholder="Ex: LOT-001")
            description = st.text_input("Description")
            montant     = st.number_input("Montant (MAD)", min_value=0.0, step=0.01)

        with c3:
            quantite      = st.number_input("Quantité (pièces)", min_value=1, step=1)
            mode_paiement = st.text_input("Mode de paiement")
            statut_lot    = st.selectbox("Statut du lot", ["Actif","Fermé"])

        remarque = st.text_input("Remarque")

        if st.button("Enregistrer"):
            row = {'Date': str(date),
                   'Personne':                    sanitize_text(personne_val.upper()),
                   'Type (Achat/Vente/Dépense)':  type_trans,
                   'Description':                 sanitize_text(description),
                   'Lot':                         sanitize_text(lot_val.upper()),
                   'Montant (MAD)':               montant,
                   'Quantité (pièces)':           quantite,
                   'Mode de paiement':            sanitize_text(mode_paiement),
                   'Remarque':                    sanitize_text(remarque),
                   'Statut du lot':               statut_lot}
            try:
                append_row(row, "Gestion globale")
                st.success("Transaction enregistrée.")
                clear_data_cache()
            except Exception as e:
                st.error(f"Erreur : {e}")

    with tab2:
        st.markdown('<div class="section-title">Recherche</div>', unsafe_allow_html=True)
        cs1, cs2, cs3 = st.columns([2,1,1], gap="large")
        with cs1: query = st.text_input("Rechercher", placeholder="Nom, lot, description...")
        with cs2: filtre_type = st.selectbox("Type", ["Tous","ACHAT","VENTE","DÉPENSE"])
        with cs3:
            lots_dispo = ["Tous"] + sorted(transactions['Lot'].dropna().astype(str).unique().tolist())
            filtre_lot = st.selectbox("Lot", lots_dispo)
        df_f = transactions.copy()
        if query:
            mask = (df_f['Personne'].astype(str).str.contains(query,case=False,na=False) |
                    df_f['Lot'].astype(str).str.contains(query,case=False,na=False) |
                    df_f['Description'].astype(str).str.contains(query,case=False,na=False) |
                    df_f['Remarque'].astype(str).str.contains(query,case=False,na=False))
            df_f = df_f[mask]
        if filtre_type != "Tous": df_f = df_f[df_f['Type (Achat/Vente/Dépense)']==filtre_type]
        if filtre_lot != "Tous":  df_f = df_f[df_f['Lot']==filtre_lot]
        st.markdown(f'<div class="info-count">{len(df_f)} transaction(s)</div>', unsafe_allow_html=True)
        st.dataframe(df_f, width='stretch', hide_index=True)

    with tab3:
        st.markdown('<div class="section-title">Graphiques</div>', unsafe_allow_html=True)
        COLORS = {'ACHAT':'#5C85D6','VENTE':'#2D7A3A','DÉPENSE':'#C0864A'}
        PL = dict(paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)',
                  font=dict(family='DM Sans',color='#555',size=12),margin=dict(l=10,r=10,t=40,b=10))
        gc1,gc2 = st.columns(2,gap="large")
        with gc1:
            st.markdown('<div class="section-title" style="font-size:1rem;">Répartition globale</div>', unsafe_allow_html=True)
            fig = go.Figure(go.Pie(labels=['Achats','Ventes','Dépenses'], values=[ta,tv,td], hole=0.55,
                marker=dict(colors=['#5C85D6','#2D7A3A','#C0864A'],line=dict(color='#F7F6F2',width=3)),
                hovertemplate='%{label}<br>%{value:,.0f} MAD<extra></extra>'))
            fig.update_layout(**PL,showlegend=True,legend=dict(orientation='h',y=-0.15,x=0.5,xanchor='center'))
            st.plotly_chart(fig,use_container_width=True)
        with gc2:
            st.markdown('<div class="section-title" style="font-size:1rem;">Résultat par lot</div>', unsafe_allow_html=True)
            sl = compute_suivi_lot(transactions)
            fig2 = go.Figure(go.Bar(x=sl['Lot'],y=sl['Résultat'],
                marker_color=['#2D7A3A' if v>=0 else '#B03A2E' for v in sl['Résultat']],
                hovertemplate='%{x}<br>%{y:,.0f} MAD<extra></extra>'))
            fig2.update_layout(**PL,xaxis=dict(showgrid=False),yaxis=dict(showgrid=True,gridcolor='#EEE',tickformat=',.0f'))
            st.plotly_chart(fig2,use_container_width=True)
        st.markdown('<div class="section-title" style="font-size:1rem;">Évolution dans le temps</div>', unsafe_allow_html=True)
        df_t = transactions.copy()
        df_t['Date'] = pd.to_datetime(df_t['Date'],errors='coerce')
        df_t = df_t.dropna(subset=['Date'])
        df_t['Mois'] = df_t['Date'].dt.to_period('M').astype(str)
        dp = df_t.groupby(['Mois','Type (Achat/Vente/Dépense)'])['Montant (MAD)'].sum().reset_index()
        fig3 = go.Figure()
        for tv2, col in COLORS.items():
            d = dp[dp['Type (Achat/Vente/Dépense)']==tv2]
            if not d.empty:
                fig3.add_trace(go.Scatter(x=d['Mois'],y=d['Montant (MAD)'],mode='lines+markers',name=tv2,
                    line=dict(color=col,width=2),marker=dict(size=6)))
        fig3.update_layout(**PL,xaxis=dict(showgrid=False),yaxis=dict(showgrid=True,gridcolor='#EEE',tickformat=',.0f'),
            legend=dict(orientation='h',y=-0.2,x=0.5,xanchor='center'))
        st.plotly_chart(fig3,use_container_width=True)
        st.markdown('<div class="section-title" style="font-size:1rem;">Résultat par personne</div>', unsafe_allow_html=True)
        rp = compute_resume_personne(transactions)
        fig4 = go.Figure(go.Bar(x=rp['Personne'],y=rp['Résultat'],
            marker_color=['#2D7A3A' if v>=0 else '#B03A2E' for v in rp['Résultat']],
            hovertemplate='%{x}<br>%{y:,.0f} MAD<extra></extra>'))
        fig4.update_layout(**PL,xaxis=dict(showgrid=False),yaxis=dict(showgrid=True,gridcolor='#EEE',tickformat=',.0f'))
        st.plotly_chart(fig4,use_container_width=True)

    with tab4:
        st.markdown('<div class="section-title">Catalogue des lots</div>', unsafe_allow_html=True)
        st.dataframe(compute_suivi_lot(transactions), width='stretch', hide_index=True)

    with tab5:
        st.markdown('<div class="section-title">Résumé par personne</div>', unsafe_allow_html=True)
        st.dataframe(compute_resume_personne(transactions), width='stretch', hide_index=True)

    with tab6:
        st.markdown('<div class="section-title">Historique des lots</div>', unsafe_allow_html=True)
        filtre_lot_hist = st.selectbox("Filtrer par lot", ["Tous"] + lots_existants, key="hist_filtre")
        hist_df = compute_historique_lot(transactions)
        if filtre_lot_hist != "Tous":
            hist_df = hist_df[hist_df['Lot'] == filtre_lot_hist]
            t_lot = transactions[transactions['Lot'] == filtre_lot_hist]
            a_l = t_lot[t_lot['Type (Achat/Vente/Dépense)']=='ACHAT']['Montant (MAD)'].sum()
            v_l = t_lot[t_lot['Type (Achat/Vente/Dépense)']=='VENTE']['Montant (MAD)'].sum()
            d_l = t_lot[t_lot['Type (Achat/Vente/Dépense)']=='DÉPENSE']['Montant (MAD)'].sum()
            r_l = v_l - (a_l + d_l)
            cr_l = "#2D7A3A" if r_l >= 0 else "#B03A2E"
            st.markdown(f"""
            <div class="metric-row" style="margin-bottom:1rem">
              <div class="metric-card"><div class="metric-label">Achats</div><div class="metric-value">{a_l:,.0f} <small style="opacity:.5">MAD</small></div></div>
              <div class="metric-card"><div class="metric-label">Ventes</div><div class="metric-value">{v_l:,.0f} <small style="opacity:.5">MAD</small></div></div>
              <div class="metric-card"><div class="metric-label">Dépenses</div><div class="metric-value">{d_l:,.0f} <small style="opacity:.5">MAD</small></div></div>
              <div class="metric-card"><div class="metric-label">Résultat</div><div class="metric-value" style="color:{cr_l}">{r_l:+,.0f} <small style="opacity:.5">MAD</small></div></div>
            </div>
            """, unsafe_allow_html=True)
        if not hist_df.empty:
            st.markdown(f'<div class="info-count">{len(hist_df)} transaction(s)</div>', unsafe_allow_html=True)
            st.dataframe(hist_df, width='stretch', hide_index=True)
        else:
            st.warning("Aucune transaction pour ce lot.")

    with tab7:
        st.markdown('<div class="section-title">Suivi des avances</div>', unsafe_allow_html=True)

        # ── ÉDITION DIRECTE DANS LE TABLEUR ──────────────────────────────────
        st.markdown('<div class="section-title">Modifier les transactions</div>', unsafe_allow_html=True)
        st.caption("Cliquez sur une cellule pour la modifier directement. Appuyez sur **Sauvegarder** pour enregistrer toutes les modifications.")

        # Filtres pour réduire le tableau affiché
        ef1, ef2, ef3 = st.columns(3, gap="large")
        with ef1:
            lots_edit_opts = ["Tous"] + sorted(transactions_all['Lot'].dropna().astype(str).unique().tolist())
            e_lot = st.selectbox("Filtrer par lot", lots_edit_opts, key="edit_inline_lot")
        with ef2:
            pers_edit_opts = ["Tous"] + sorted(transactions_all['Personne'].dropna().astype(str).unique().tolist())
            e_pers = st.selectbox("Filtrer par personne", pers_edit_opts, key="edit_inline_pers")
        with ef3:
            e_type = st.selectbox("Filtrer par type", ["Tous","ACHAT","VENTE","DÉPENSE"], key="edit_inline_type")

        # Construire le df à afficher (avec index original conservé)
        df_editable = transactions_all.copy()
        df_editable.index = range(len(df_editable))   # index propre 0..N
        df_editable["_orig_idx"] = df_editable.index  # colonne cachée = position dans transactions_all

        mask_edit = pd.Series([True] * len(df_editable))
        if e_lot  != "Tous": mask_edit &= df_editable['Lot'].astype(str) == e_lot
        if e_pers != "Tous": mask_edit &= df_editable['Personne'].astype(str) == e_pers
        if e_type != "Tous": mask_edit &= df_editable['Type (Achat/Vente/Dépense)'].astype(str) == e_type

        df_view = df_editable[mask_edit].copy()

        # Colonnes éditables et leurs types
        cols_show = [c for c in ['Date','Personne','Type (Achat/Vente/Dépense)','Lot',
                                  'Description','Montant (MAD)','Quantité (pièces)',
                                  'Mode de paiement','Remarque','Statut du lot'] if c in df_view.columns]

        column_config = {
            "Date": st.column_config.TextColumn("Date", help="Format YYYY-MM-DD"),
            "Personne": st.column_config.TextColumn("Personne"),
            "Type (Achat/Vente/Dépense)": st.column_config.SelectboxColumn(
                "Type",
                options=["ACHAT","VENTE","DÉPENSE"],
                required=True
            ),
            "Lot": st.column_config.TextColumn("Lot"),
            "Description": st.column_config.TextColumn("Description"),
            "Montant (MAD)": st.column_config.NumberColumn("Montant (MAD)", min_value=0.0, format="%.2f"),
            "Quantité (pièces)": st.column_config.NumberColumn("Quantité", min_value=1, step=1, format="%d"),
            "Mode de paiement": st.column_config.TextColumn("Mode paiement"),
            "Remarque": st.column_config.TextColumn("Remarque"),
            "Statut du lot": st.column_config.SelectboxColumn(
                "Statut",
                options=["Actif","Fermé"],
                required=True
            ),
        }

        st.markdown(f'<div class="info-count">{len(df_view)} transaction(s) affichée(s)</div>', unsafe_allow_html=True)

        edited_df = st.data_editor(
            df_view[cols_show + ["_orig_idx"]],
            column_config=column_config,
            hide_index=True,
            use_container_width=True,
            num_rows="fixed",
            column_order=cols_show,   # cache la colonne _orig_idx visuellement
            key="inline_editor"
        )

        if st.button("💾 Sauvegarder toutes les modifications", key="btn_save_inline"):
            try:
                # Réinjecter les lignes modifiées dans transactions_all
                for _, row_edit in edited_df.iterrows():
                    oi = int(row_edit["_orig_idx"])
                    for col in cols_show:
                        if col in transactions_all.columns:
                            val = row_edit[col]
                            if col in ['Personne','Lot','Description','Remarque','Mode de paiement']:
                                val = sanitize_text(str(val))
                                if col in ['Personne','Lot']:
                                    val = val.upper()
                            transactions_all.at[oi, col] = val
                save_sheet(transactions_all, "Gestion globale")
                st.success("✅ Modifications enregistrées dans Google Sheets.")
                clear_data_cache()
                st.rerun()
            except Exception as e:
                st.error(f"Erreur lors de la sauvegarde : {e}")

        st.markdown('<div class="section-title">Supprimer une transaction précise</div>', unsafe_allow_html=True)

        sf1, sf2, sf3 = st.columns(3, gap="large")
        with sf1:
            lots_f  = ["Tous"] + sorted(transactions['Lot'].dropna().astype(str).unique().tolist())
            f_lot   = st.selectbox("Filtrer par lot", lots_f, key="sf_lot")
        with sf2:
            pers_f  = ["Tous"] + sorted(transactions['Personne'].dropna().astype(str).unique().tolist())
            f_pers  = st.selectbox("Filtrer par personne", pers_f, key="sf_pers")
        with sf3:
            f_type  = st.selectbox("Filtrer par type", ["Tous","ACHAT","VENTE","DÉPENSE"], key="sf_type")

        df_del = transactions.copy()
        df_del = df_del.reset_index(drop=True)
        if f_lot  != "Tous": df_del = df_del[df_del['Lot']==f_lot]
        if f_pers != "Tous": df_del = df_del[df_del['Personne']==f_pers]
        if f_type != "Tous": df_del = df_del[df_del['Type (Achat/Vente/Dépense)']==f_type]

        if not df_del.empty:
            def make_label(r):
                return f"{r.get('Date','')} | {r.get('Lot','')} | {r.get('Personne','')} | {r.get('Type (Achat/Vente/Dépense)','')} | {float(r.get('Montant (MAD)',0)):,.0f} MAD"
            labels = [make_label(row) for _, row in df_del.iterrows()]
            idx_to_orig = df_del.index.tolist()

            st.caption(f"{len(df_del)} transaction(s) filtrée(s)")
            choix_label = st.selectbox("Choisir la transaction à supprimer", ["— sélectionner —"] + labels, key="del_single_sel")

            if choix_label != "— sélectionner —":
                ligne_idx = labels.index(choix_label)
                orig_idx  = idx_to_orig[ligne_idx]
                row_sel   = transactions.loc[orig_idx]

                with st.container(border=True):
                    st.markdown(f"**{h(str(row_sel.get('Lot','')))} — {h(str(row_sel.get('Type (Achat/Vente/Dépense)','')))}**", unsafe_allow_html=True)
                    st.caption(f"{row_sel.get('Date','')} · {row_sel.get('Personne','')} · {float(row_sel.get('Montant (MAD)',0)):,.0f} MAD · {row_sel.get('Description','')}")

                c_single = st.checkbox("Je confirme la suppression de cette transaction", key="confirm_single")
                if st.button("Supprimer cette transaction", key="btn_del_single"):
                    if not c_single:
                        st.warning("Coche la case de confirmation.")
                    else:
                        transactions = transactions.drop(index=orig_idx).reset_index(drop=True)
                        save_sheet(transactions, "Gestion globale")
                        st.success("Transaction supprimée.")
                        clear_data_cache()
                        st.rerun()
        else:
            st.warning("Aucune transaction ne correspond aux filtres.")

        st.markdown('<div class="section-title">Supprimer en masse</div>', unsafe_allow_html=True)
        dc1, dc2 = st.columns(2, gap="large")
        with dc1:
            st.markdown("**Toutes les transactions d'un lot**")
            lots_ex = sorted(transactions['Lot'].dropna().astype(str).unique().tolist())
            lot_sup = st.selectbox("Choisir un lot", ["— sélectionner —"]+lots_ex, key="del_lot")
            if lot_sup != "— sélectionner —":
                st.caption(f"{len(transactions[transactions['Lot']==lot_sup])} transaction(s)")
            c_lot = st.checkbox("Je confirme la suppression du lot", key="confirm_lot")
            if st.button("Supprimer le lot", key="btn_del_lot"):
                if lot_sup == "— sélectionner —": st.warning("Sélectionne un lot.")
                elif not c_lot: st.warning("Coche la case de confirmation.")
                else:
                    transactions = transactions[transactions['Lot']!=lot_sup]
                    save_sheet(transactions,"Gestion globale"); st.success(f"Lot « {lot_sup} » supprimé."); clear_data_cache()
        with dc2:
            st.markdown("**Toutes les transactions d'une personne**")
            pers_ex = sorted(transactions['Personne'].dropna().astype(str).unique().tolist())
            pers_sup = st.selectbox("Choisir une personne", ["— sélectionner —"]+pers_ex, key="del_pers")
            if pers_sup != "— sélectionner —":
                st.caption(f"{len(transactions[transactions['Personne']==pers_sup])} transaction(s)")
            c_pers = st.checkbox("Je confirme la suppression", key="confirm_pers")
            if st.button("Supprimer la personne", key="btn_del_pers"):
                if pers_sup == "— sélectionner —": st.warning("Sélectionne une personne.")
                elif not c_pers: st.warning("Coche la case de confirmation.")
                else:
                    transactions = transactions[transactions['Personne']!=pers_sup]
                    save_sheet(transactions,"Gestion globale"); st.success(f"Personne « {pers_sup} » supprimée."); clear_data_cache()

    with tab8:
        st.markdown('<div class="section-title">Gestion des utilisateurs</div>', unsafe_allow_html=True)
        users_df = get_users()
        lots_all = sorted(transactions['Lot'].dropna().astype(str).unique().tolist())

        pending = users_df[users_df["statut"] == "en_attente"]
        if not pending.empty:
            st.markdown(f"**🔔 Demandes en attente ({len(pending)})**")
            for _, row in pending.iterrows():
                uname = row["username"]
                fn = f"{str(row.get('prenom','')).strip()} {str(row.get('nom','')).strip()}".strip() or "—"
                with st.container():
                    st.markdown(f"""<div class="user-card"><div class="user-card-name">{h(fn)}</div>
                    <div class="user-card-meta">@{h(uname)} · {h(str(row.get('created_at','')))}</div></div>""", unsafe_allow_html=True)
                    pc1, pc2, pc3 = st.columns([3,1,1], gap="small")
                    with pc1: lots_sel = st.multiselect("Lots autorisés", options=lots_all, key=f"lots_{uname}")
                    with pc2:
                        if st.button("✓ Approuver", key=f"approve_{uname}",
                                     disabled=st.session_state.get(f"approving_{uname}", False)):
                            if not st.session_state.get(f"approving_{uname}", False):
                                st.session_state[f"approving_{uname}"] = True
                                with st.spinner(""):
                                    users_df.loc[users_df["username"]==uname,"statut"] = "approuvé"
                                    users_df.loc[users_df["username"]==uname,"lots_autorises"] = ",".join(lots_sel)
                                    save_users(users_df)
                                    _load_sheet_cached.clear()
                                st.rerun()
                    with pc3:
                        if st.button("✗ Refuser", key=f"reject_{uname}",
                                     disabled=st.session_state.get(f"rejecting_{uname}", False)):
                            if not st.session_state.get(f"rejecting_{uname}", False):
                                st.session_state[f"rejecting_{uname}"] = True
                                with st.spinner(""):
                                    users_df.loc[users_df["username"]==uname,"statut"] = "rejeté"
                                    save_users(users_df)
                                    _load_sheet_cached.clear()
                                st.rerun()
            st.markdown("---")

        st.markdown("**Tous les utilisateurs**")
        search_user = st.text_input("Rechercher un utilisateur", placeholder="Nom, prénom ou identifiant...", key="search_users")
        approved = users_df[users_df["statut"] != "en_attente"].copy()
        if search_user:
            m = (approved["username"].astype(str).str.contains(search_user,case=False,na=False) |
                 approved["nom"].astype(str).str.contains(search_user,case=False,na=False) |
                 approved["prenom"].astype(str).str.contains(search_user,case=False,na=False))
            approved = approved[m]
        st.markdown(f'<div class="info-count">{len(approved)} utilisateur(s)</div>', unsafe_allow_html=True)

        for _, row in approved.iterrows():
            uname = row["username"]
            if uname == username: continue
            fn = f"{str(row.get('prenom','')).strip()} {str(row.get('nom','')).strip()}".strip() or "—"
            sb = "badge-approved" if row["statut"]=="approuvé" else "badge-rejected"
            cur_role = str(row["role"])
            role_label_u = "Admin" if cur_role=="admin" else ("Sous-Admin" if cur_role=="sous-admin" else "Visiteur")

            with st.container():
                st.markdown(f"""
                <div class="user-card">
                  <div style="display:flex;justify-content:space-between;align-items:flex-start">
                    <div>
                      <div class="user-card-name">{h(fn)}</div>
                      <div class="user-card-meta">@{h(uname)} · {h(str(row.get('created_at','')))} · {role_label_u}</div>
                    </div>
                    <span class="badge-pending {sb}" style="flex-shrink:0;margin-top:0.1rem">{h(str(row['statut']))}</span>
                  </div>
                </div>
                """, unsafe_allow_html=True)

                ac2, ac3, ac4 = st.columns([3,1,1], gap="small")
                with ac2:
                    la = [x.strip() for x in str(row.get("lots_autorises","")).split(",") if x.strip()]
                    la_valid = [x for x in la if x in lots_all]  # filtre les lots qui n'existent plus dans les transactions
                    new_lots = st.multiselect("Lots", options=lots_all, default=la_valid, key=f"edit_lots_{uname}")
                with ac3:
                    # Rôles disponibles : admin, sous-admin (plus de "visiteur")
                    role_options = ["sous-admin","admin"]
                    role_idx = 0 if cur_role != "admin" else 1
                    new_role = st.selectbox("Rôle", role_options, index=role_idx, key=f"role_{uname}")
                with ac4:
                    if st.button("Sauvegarder", key=f"save_{uname}", disabled=st.session_state.get(f"saving_{uname}", False)):
                        st.session_state[f"saving_{uname}"] = True
                        with st.spinner("Enregistrement…"):
                            users_df.loc[users_df["username"]==uname, "lots_autorises"] = ",".join(new_lots)
                            users_df.loc[users_df["username"]==uname, "role"] = new_role
                            save_users(users_df)
                            update_session_for_user(uname, new_role, new_lots)
                        st.rerun()
                    if st.button("Supprimer", key=f"del_{uname}", disabled=st.session_state.get(f"deleting_{uname}", False)):
                        st.session_state[f"deleting_{uname}"] = True
                        with st.spinner("Suppression…"):
                            users_df = users_df[users_df["username"] != uname]
                            save_users(users_df)
                        st.rerun()
    with tab9:
        st.markdown('<div class="section-title">Finance</div>', unsafe_allow_html=True)

        subtabs = st.tabs([
            "Caisse",
            "Dettes fournisseurs",
            "Charges",
            "Rapport mensuel",
            "Gestion fournisseurs"
        ])
        sub1, sub2, sub3, sub4, sub5 = subtabs

        def compute_caisse(t):
            t = to_numeric(t.copy(), ['Montant (MAD)'])

            total_entrees = t.loc[t['Type (Achat/Vente/Dépense)']=="VENTE","Montant (MAD)"].sum()

            total_sorties = t.loc[
             t['Type (Achat/Vente/Dépense)'].isin(["ACHAT","DÉPENSE"]),
                "Montant (MAD)"
            ].sum()

            return total_entrees - total_sorties

        with sub1:
            solde = compute_caisse(transactions)

            st.metric("Solde en caisse", f"{solde:,.0f} MAD")
        
        def compute_dettes_fournisseurs(t):
            EMPTY = pd.DataFrame(columns=["Fournisseur","Total Achats","Total Paiements","Dette Restante"])

            if t.empty:
                return EMPTY

            t = to_numeric(t.copy(), ['Montant (MAD)'])

            g = t.groupby('Personne').apply(lambda x: pd.Series({
                "Total Achats": x.loc[x['Type (Achat/Vente/Dépense)']=="ACHAT","Montant (MAD)"].sum(),
                "Total Paiements": x.loc[x['Type (Achat/Vente/Dépense)']=="DÉPENSE","Montant (MAD)"].sum()
            }), include_groups=False).reset_index()

            g = g.rename(columns={"Personne":"Fournisseur"})
            g["Dette Restante"] = g["Total Achats"] - g["Total Paiements"]

            return g[g["Total Achats"] > 0]
        
        with sub2:
            df_dettes = compute_dettes_fournisseurs(transactions)
            st.dataframe(df_dettes, use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════════
# SOUS-ADMIN
# ═══════════════════════════════════════════════════════════════════════════════
elif is_sous_admin:

    with tab1:
        st.markdown('<div class="section-title">Nouvelle transaction</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="info-count">Transaction enregistrée sous le nom : <strong>{h(username.upper())}</strong></div>', unsafe_allow_html=True)

        c1, c2, c3 = st.columns(3, gap="large")

        with c1:
            date_sa = st.date_input("Date", datetime.now(), key="sa_date")
            st.text_input("Personne", value=username.upper(), disabled=True, key="sa_pers_display")
            type_trans_sa = st.selectbox("Type de transaction", ["ACHAT","VENTE","DÉPENSE"], key="sa_type")

        with c2:
            # Lot : sélection parmi autorisés OU nouveau lot
            lots_sa_options = lots_autorises if lots_autorises else []
            lot_sel_sa = st.selectbox(
                "Lot (autorisés)",
                options=lots_sa_options,
                index=None,
                placeholder="Choisir un lot existant..." if lots_sa_options else "Aucun lot autorisé",
                key="sa_lot_sel"
            )
            nouveau_lot_sa = st.text_input("Ou créer un nouveau lot", key="sa_new_lot", placeholder="Ex: LOT-007")
            # Priorité au nouveau lot si renseigné
            lot_val_sa = sanitize_text(nouveau_lot_sa).upper() if nouveau_lot_sa.strip() else (lot_sel_sa or None)
            description_sa = st.text_input("Description", key="sa_desc")
            montant_sa     = st.number_input("Montant (MAD)", min_value=0.0, step=0.01, key="sa_montant")

        with c3:
            quantite_sa      = st.number_input("Quantité (pièces)", min_value=1, step=1, key="sa_qty")
            mode_paiement_sa = st.text_input("Mode de paiement", key="sa_mode")
            statut_lot_sa    = st.selectbox("Statut du lot", ["Actif","Fermé"], key="sa_statut")

        remarque_sa = st.text_input("Remarque", key="sa_remarque")

        if st.button("Enregistrer", key="sa_btn_save"):
            if not lot_val_sa:
                st.error("Sélectionne ou crée un lot.")
            else:
                row_sa = {
                    'Date':                        str(date_sa),
                    'Personne':                    sanitize_text(username.upper()),
                    'Type (Achat/Vente/Dépense)':  type_trans_sa,
                    'Description':                 sanitize_text(description_sa),
                    'Lot':                         lot_val_sa,
                    'Montant (MAD)':               montant_sa,
                    'Quantité (pièces)':           quantite_sa,
                    'Mode de paiement':            sanitize_text(mode_paiement_sa),
                    'Remarque':                    sanitize_text(remarque_sa),
                    'Statut du lot':               statut_lot_sa
                }
                try:
                    append_row(row_sa, "Gestion globale")
                    st.success(f"Transaction enregistrée sur le lot {lot_val_sa}.")
                    clear_data_cache()
                except Exception as e:
                    st.error(f"Erreur : {e}")

    with tab2:
        st.markdown('<div class="section-title">Mes lots autorisés</div>', unsafe_allow_html=True)
        if lots_autorises:
            st.markdown(f'<div class="info-count">Lots visibles : {", ".join(lots_autorises)}</div>', unsafe_allow_html=True)
        else:
            warn("Aucun lot ne t'a été attribué. Contacte l'administrateur.")
        st.dataframe(compute_suivi_lot(transactions), width='stretch', hide_index=True)

    with tab3:
        st.markdown('<div class="section-title">Recherche</div>', unsafe_allow_html=True)
        query_sa = st.text_input("Rechercher", placeholder="Nom, lot, description...", key="sa_search")
        filtre_type_sa = st.selectbox("Type", ["Tous","ACHAT","VENTE","DÉPENSE"], key="sa_ftype")
        df_sa = transactions.copy()
        if query_sa:
            mask = (df_sa['Personne'].astype(str).str.contains(query_sa,case=False,na=False) |
                    df_sa['Lot'].astype(str).str.contains(query_sa,case=False,na=False) |
                    df_sa['Description'].astype(str).str.contains(query_sa,case=False,na=False) |
                    df_sa['Remarque'].astype(str).str.contains(query_sa,case=False,na=False))
            df_sa = df_sa[mask]
        if filtre_type_sa != "Tous": df_sa = df_sa[df_sa['Type (Achat/Vente/Dépense)']==filtre_type_sa]
        st.markdown(f'<div class="info-count">{len(df_sa)} transaction(s)</div>', unsafe_allow_html=True)
        st.dataframe(df_sa, width='stretch', hide_index=True)

    with tab4:
        st.markdown('<div class="section-title">Graphiques de mes lots</div>', unsafe_allow_html=True)
        PL = dict(paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)',
                  font=dict(family='DM Sans',color='#555',size=12),margin=dict(l=10,r=10,t=40,b=10))
        sl_sa = compute_suivi_lot(transactions)
        if not sl_sa.empty:
            fig_sa = go.Figure(go.Bar(x=sl_sa['Lot'],y=sl_sa['Résultat'],
                marker_color=['#2D7A3A' if v>=0 else '#B03A2E' for v in sl_sa['Résultat']],
                hovertemplate='%{x}<br>%{y:,.0f} MAD<extra></extra>'))
            fig_sa.update_layout(**PL,xaxis=dict(showgrid=False),yaxis=dict(showgrid=True,gridcolor='#EEE',tickformat=',.0f'))
            st.plotly_chart(fig_sa,use_container_width=True)
        else:
            warn("Aucune donnée à afficher.")

    with tab5:
        st.markdown('<div class="section-title">Modifier mes transactions</div>', unsafe_allow_html=True)
        st.markdown('<div class="info-count">Cliquez sur une cellule pour la modifier. Seules vos transactions sur vos lots sont éditables.</div>', unsafe_allow_html=True)

        # Filtrer : uniquement les transactions du sous-admin sur ses lots autorisés
        df_sa_edit = transactions_all.copy()
        df_sa_edit.index = range(len(df_sa_edit))
        df_sa_edit["_orig_idx"] = df_sa_edit.index 
        # df_sa_edit = index.non

        # Filtrer sur personne = username ET lots autorisés
        mask_sa = df_sa_edit['Personne'].astype(str).str.upper() == username.upper()
        if lots_autorises:
            mask_sa &= df_sa_edit['Lot'].astype(str).isin([l.upper() for l in lots_autorises])
        df_sa_view = df_sa_edit[mask_sa].copy()

        if df_sa_view.empty:
            st.markdown('<div class="info-count">Aucune transaction à afficher pour votre compte.</div>', unsafe_allow_html=True)
        else:
            # Filtre additionnel par lot
            lots_sa_disp = ["Tous"] + sorted(df_sa_view['Lot'].dropna().astype(str).unique().tolist())
            fsa_lot = st.selectbox("Filtrer par lot", lots_sa_disp, key="sa_edit_flot")
            if fsa_lot != "Tous":
                df_sa_view = df_sa_view[df_sa_view['Lot'] == fsa_lot]

            cols_sa_show = [c for c in ['Date','Type (Achat/Vente/Dépense)','Lot',
                                         'Description','Montant (MAD)','Quantité (pièces)',
                                         'Mode de paiement','Remarque','Statut du lot'] if c in df_sa_view.columns]

            cols_show = [c for c in ['Date', 'Personne', 'Type (achat,Vente,Depense)','Lot']]
            
            # Lots disponibles pour ce sous-admin (autorisés + nouveaux créés)
            all_lots_sa = sorted(set(lots_autorises or []) | set(df_sa_view['Lot'].dropna().astype(str).unique().tolist()))

            col_cfg_sa = {
                "Date": st.column_config.TextColumn("Date", help="Format YYYY-MM-DD"),
                "Type (Achat/Vente/Dépense)": st.column_config.SelectboxColumn("Type", options=["ACHAT","VENTE","DÉPENSE"], required=True),
                "Lot": st.column_config.SelectboxColumn("Lot", options=all_lots_sa, required=True),
                "Description": st.column_config.TextColumn("Description"),
                "Montant (MAD)": st.column_config.NumberColumn("Montant (MAD)", min_value=0.0, format="%.2f"),
                "Quantité (pièces)": st.column_config.NumberColumn("Quantité", min_value=1, step=1, format="%d"),
                "Mode de paiement": st.column_config.TextColumn("Mode paiement"),
                "Remarque": st.column_config.TextColumn("Remarque"),
                "Statut du lot": st.column_config.SelectboxColumn("Statut", options=["Actif","Fermé"], required=True),
            }

            st.markdown(f'<div class="info-count">{len(df_sa_view)} transaction(s)</div>', unsafe_allow_html=True)

            edited_sa = st.data_editor(
                df_sa_view[cols_sa_show + ["_orig_idx"]],
                column_config=col_cfg_sa,
                hide_index=True,
                use_container_width=True,
                num_rows="fixed",
                column_order=cols_sa_show,
                key="sa_inline_editor"
            )

            if st.button("💾 Sauvegarder les modifications", key="sa_btn_save_inline"):
                try:
                    for _, row_edit in edited_sa.iterrows():
                        oi = int(row_edit["_orig_idx"])
                        for col in cols_sa_show:
                            if col in transactions_all.columns:
                                val = row_edit[col]
                                if col in ['Lot','Description','Remarque','Mode de paiement']:
                                    val = sanitize_text(str(val))
                                if col == 'Lot':
                                    val = val.upper()
                                transactions_all.at[oi, col] = val
                    save_sheet(transactions_all, "Gestion globale")
                    st.success("✅ Modifications enregistrées.")
                    clear_data_cache()
                    st.rerun()
                except Exception as e:
                    st.error(f"Erreur lors de la sauvegarde : {e}")

# ═══════════════════════════════════════════════════════════════════════════════
# VISITEUR (rôle legacy — au cas où des comptes existent encore)
# ═══════════════════════════════════════════════════════════════════════════════
else:
    with tab1:
        st.markdown('<div class="section-title">Mes lots autorisés</div>', unsafe_allow_html=True)
        if lots_autorises: st.markdown(f'<div class="info-count">Lots visibles : {", ".join(lots_autorises)}</div>', unsafe_allow_html=True)
        else: warn("Aucun lot ne t'a été attribué. Contacte l'administrateur.")
        st.dataframe(compute_suivi_lot(transactions), width='stretch', hide_index=True)

    with tab2:
        st.markdown('<div class="section-title">Recherche</div>', unsafe_allow_html=True)
        query_v = st.text_input("Rechercher", placeholder="Description, remarque...")
        df_v = transactions.copy()
        if query_v:
            mask = (df_v['Description'].astype(str).str.contains(query_v,case=False,na=False) |
                    df_v['Remarque'].astype(str).str.contains(query_v,case=False,na=False))
            df_v = df_v[mask]
        st.markdown(f'<div class="info-count">{len(df_v)} transaction(s)</div>', unsafe_allow_html=True)
        st.dataframe(df_v, width='stretch', hide_index=True)

    with tab3:
        st.markdown('<div class="section-title">Graphiques de mes lots</div>', unsafe_allow_html=True)
        PL = dict(paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)',
                  font=dict(family='DM Sans',color='#555',size=12),margin=dict(l=10,r=10,t=40,b=10))
        sl_v = compute_suivi_lot(transactions)
        if not sl_v.empty:
            fig_v = go.Figure(go.Bar(x=sl_v['Lot'],y=sl_v['Résultat'],
                marker_color=['#2D7A3A' if v>=0 else '#B03A2E' for v in sl_v['Résultat']],
                hovertemplate='%{x}<br>%{y:,.0f} MAD<extra></extra>'))
            fig_v.update_layout(**PL,xaxis=dict(showgrid=False),yaxis=dict(showgrid=True,gridcolor='#EEE',tickformat=',.0f'))
            st.plotly_chart(fig_v,use_container_width=True)
        else:
            warn("Aucune donnée à afficher.")

#sous admin :------- 
#Peut voir les lot a sons nom  
#|
#|
#|
#caisse et charge :-------------
#Dette finacière -------- Dette fourniseur ------ caisse ------- encaissement 
