import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import base64
import storage as supa_storage
import hashlib
import streamlit.components.v1 as components
import database as db
from datetime import datetime, date

st.set_page_config(page_title="Lhawli – Gestion de bétail", page_icon="🐑",
                   layout="wide", initial_sidebar_state="expanded")

ACCENT       = "#1A5C4A"
ACCENT_DARK  = "#0F3D30"
ACCENT_LIGHT = "#E8F4F0"
RED          = "#E53935"
GREEN        = "#2E7D5B"
STOCK_ACCENT = "#B8860B"
EXPENSE_ACCENT = "#8E24AA"

FEED_TYPES = [
    "Paille",
    "Foin",
    "Céréales",
    "Mélange",
    "Graines",
    "Orge (Ch'ir)",
    "Maïs grain et avoine (Khartal)",
    "Pulpe de betterave séchée",
    "Son de blé (N'khala)",
]
UNIT_TO_KG = {"kg": 1, "sachet": 1, "balle": 1}

EXPENSE_CATEGORIES = [
    "Médicaments",
    "Transport",
    "Nourriture",
    "Main d'œuvre",
    "Entretien",
    "Eau",
    "Autre",
]

# ── SVG helper ──────────────────────────────────────────────────────────
def svg(name, size=18, color="currentColor"):
    s = str(size)
    icons = {
        "dashboard": f'<svg width="{s}" height="{s}" fill="none" stroke="{color}" stroke-width="2" viewBox="0 0 24 24"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></svg>',
        "animals":   f'<svg width="{s}" height="{s}" fill="none" stroke="{color}" stroke-width="2" viewBox="0 0 24 24"><path d="M12 2C6.5 2 2 6.5 2 12s4.5 10 10 10 10-4.5 10-10S17.5 2 12 2z"/><path d="M8 14s1.5 2 4 2 4-2 4-2"/><circle cx="9" cy="9" r="1" fill="{color}"/><circle cx="15" cy="9" r="1" fill="{color}"/></svg>',
        "sales":     f'<svg width="{s}" height="{s}" fill="none" stroke="{color}" stroke-width="2" viewBox="0 0 24 24"><line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 100 7h5a3.5 3.5 0 110 7H6"/></svg>',
        "stats":     f'<svg width="{s}" height="{s}" fill="none" stroke="{color}" stroke-width="2" viewBox="0 0 24 24"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>',
        "users":     f'<svg width="{s}" height="{s}" fill="none" stroke="{color}" stroke-width="2" viewBox="0 0 24 24"><path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 00-3-3.87"/><path d="M16 3.13a4 4 0 010 7.75"/></svg>',
        "settings":  f'<svg width="{s}" height="{s}" fill="none" stroke="{color}" stroke-width="2" viewBox="0 0 24 24"><circle cx="12" cy="12" r="3"/><path d="M12 1v4M12 19v4M4.22 4.22l2.83 2.83M16.95 16.95l2.83 2.83M1 12h4M19 12h4M4.22 19.78l2.83-2.83M16.95 7.05l2.83-2.83"/></svg>',
        "catalogue": f'<svg width="{s}" height="{s}" fill="none" stroke="{color}" stroke-width="2" viewBox="0 0 24 24"><rect x="3" y="3" width="7" height="9" rx="1"/><rect x="14" y="3" width="7" height="5" rx="1"/><rect x="14" y="12" width="7" height="9" rx="1"/><rect x="3" y="16" width="7" height="5" rx="1"/></svg>',
        "logout":    f'<svg width="{s}" height="{s}" fill="none" stroke="{color}" stroke-width="2" viewBox="0 0 24 24"><path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>',
        "add":       f'<svg width="{s}" height="{s}" fill="none" stroke="{color}" stroke-width="2" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="16"/><line x1="8" y1="12" x2="16" y2="12"/></svg>',
        "edit":      f'<svg width="{s}" height="{s}" fill="none" stroke="{color}" stroke-width="2" viewBox="0 0 24 24"><path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>',
        "trash":     f'<svg width="{s}" height="{s}" fill="none" stroke="{color}" stroke-width="2" viewBox="0 0 24 24"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 01-2 2H8a2 2 0 01-2-2L5 6"/><path d="M10 11v6M14 11v6"/><path d="M9 6V4a1 1 0 011-1h4a1 1 0 011 1v2"/></svg>',
        "tag":       f'<svg width="{s}" height="{s}" fill="none" stroke="{color}" stroke-width="2" viewBox="0 0 24 24"><path d="M20.59 13.41l-7.17 7.17a2 2 0 01-2.83 0L2 12V2h10l8.59 8.59a2 2 0 010 2.82z"/><line x1="7" y1="7" x2="7.01" y2="7"/></svg>',
        "weight":    f'<svg width="{s}" height="{s}" fill="none" stroke="{color}" stroke-width="2" viewBox="0 0 24 24"><circle cx="12" cy="5" r="3"/><path d="M6.5 8h11l1 13H5.5L6.5 8z"/></svg>',
        "money":     f'<svg width="{s}" height="{s}" fill="none" stroke="{color}" stroke-width="2" viewBox="0 0 24 24"><rect x="2" y="6" width="20" height="12" rx="2"/><circle cx="12" cy="12" r="3"/></svg>',
        "check":     f'<svg width="{s}" height="{s}" fill="none" stroke="{color}" stroke-width="2.5" viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"/></svg>',
        "close":     f'<svg width="{s}" height="{s}" fill="none" stroke="{color}" stroke-width="2" viewBox="0 0 24 24"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>',
        "eye":       f'<svg width="{s}" height="{s}" fill="none" stroke="{color}" stroke-width="2" viewBox="0 0 24 24"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>',
        "race":      f'<svg width="{s}" height="{s}" fill="none" stroke="{color}" stroke-width="2" viewBox="0 0 24 24"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/></svg>',
        "filter":    f'<svg width="{s}" height="{s}" fill="none" stroke="{color}" stroke-width="2" viewBox="0 0 24 24"><polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"/></svg>',
        "save":      f'<svg width="{s}" height="{s}" fill="none" stroke="{color}" stroke-width="2" viewBox="0 0 24 24"><path d="M19 21H5a2 2 0 01-2-2V5a2 2 0 012-2h11l5 5v11a2 2 0 01-2 2z"/><polyline points="17 21 17 13 7 13 7 21"/><polyline points="7 3 7 8 15 8"/></svg>',
        "sheep":     f'<svg width="{s}" height="{s}" fill="none" stroke="{color}" stroke-width="1.8" viewBox="0 0 24 24"><ellipse cx="12" cy="10" rx="7" ry="6"/><circle cx="7" cy="7" r="2.5"/><circle cx="17" cy="7" r="2.5"/><circle cx="12" cy="5" r="2.5"/><line x1="9" y1="16" x2="8" y2="21"/><line x1="11" y1="16" x2="11" y2="21"/><line x1="13" y1="16" x2="13" y2="21"/><line x1="15" y1="16" x2="16" y2="21"/></svg>',
        "cow":       f'<svg width="{s}" height="{s}" fill="none" stroke="{color}" stroke-width="1.8" viewBox="0 0 24 24"><ellipse cx="12" cy="11" rx="8" ry="6"/><path d="M4 8 C2 6 2 4 4 5"/><path d="M20 8 C22 6 22 4 20 5"/><line x1="9" y1="17" x2="8" y2="22"/><line x1="11" y1="17" x2="11" y2="22"/><line x1="13" y1="17" x2="13" y2="22"/><line x1="15" y1="17" x2="16" y2="22"/><circle cx="9.5" cy="10" r="1" fill="{color}"/><circle cx="14.5" cy="10" r="1" fill="{color}"/></svg>',
        "male":      f'<svg width="{s}" height="{s}" fill="none" stroke="{color}" stroke-width="2" viewBox="0 0 24 24"><circle cx="10" cy="14" r="6"/><line x1="14.83" y1="9.17" x2="21" y2="3"/><polyline points="16 3 21 3 21 8"/></svg>',
        "female":    f'<svg width="{s}" height="{s}" fill="none" stroke="{color}" stroke-width="2" viewBox="0 0 24 24"><circle cx="12" cy="9" r="6"/><line x1="12" y1="15" x2="12" y2="21"/><line x1="9" y1="19" x2="15" y2="19"/></svg>',
        "sell":      f'<svg width="{s}" height="{s}" fill="none" stroke="{color}" stroke-width="2" viewBox="0 0 24 24"><path d="M6 2L3 6v14a2 2 0 002 2h14a2 2 0 002-2V6l-3-4z"/><line x1="3" y1="6" x2="21" y2="6"/><path d="M16 10a4 4 0 01-8 0"/></svg>',
        "camera":    f'<svg width="{s}" height="{s}" fill="none" stroke="{color}" stroke-width="2" viewBox="0 0 24 24"><path d="M23 19a2 2 0 01-2 2H3a2 2 0 01-2-2V8a2 2 0 012-2h4l2-3h6l2 3h4a2 2 0 012 2z"/><circle cx="12" cy="13" r="4"/></svg>',
        "star":      f'<svg width="{s}" height="{s}" fill="{color}" stroke="{color}" stroke-width="1" viewBox="0 0 24 24"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>',
        "back":      f'<svg width="{s}" height="{s}" fill="none" stroke="{color}" stroke-width="2" viewBox="0 0 24 24"><line x1="19" y1="12" x2="5" y2="12"/><polyline points="12 19 5 12 12 5"/></svg>',
        "refresh":   f'<svg width="{s}" height="{s}" fill="none" stroke="{color}" stroke-width="2" viewBox="0 0 24 24"><polyline points="23 4 23 10 17 10"/><polyline points="1 20 1 14 7 14"/><path d="M3.51 9a9 9 0 0114.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0020.49 15"/></svg>',
        "lock":      f'<svg width="{s}" height="{s}" fill="none" stroke="{color}" stroke-width="2" viewBox="0 0 24 24"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0110 0v4"/></svg>',
        "hourglass": f'<svg width="{s}" height="{s}" fill="none" stroke="{color}" stroke-width="2" viewBox="0 0 24 24"><path d="M6 2h12M6 22h12"/><path d="M6 2c0 5 4 7 6 8-2 1-6 3-6 8M18 2c0 5-4 7-6 8 2 1 6 3 6 8"/></svg>',
        "warning":   f'<svg width="{s}" height="{s}" fill="none" stroke="{color}" stroke-width="2" viewBox="0 0 24 24"><path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>',
        "recycle":   f'<svg width="{s}" height="{s}" fill="none" stroke="{color}" stroke-width="2" viewBox="0 0 24 24"><polyline points="1 4 1 10 7 10"/><polyline points="23 20 23 14 17 14"/><path d="M20.49 9A9 9 0 005.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 013.51 15"/></svg>',
        "paw":       f'<svg width="{s}" height="{s}" fill="{color}" stroke="none" viewBox="0 0 24 24"><circle cx="6" cy="9" r="2.3"/><circle cx="12" cy="6.5" r="2.3"/><circle cx="18" cy="9" r="2.3"/><path d="M12 12c-3.5 0-6.5 2.4-6.5 5.3 0 1.7 1.4 2.9 3 2.6 1.2-.2 2.1-.9 3.5-.9s2.3.7 3.5.9c1.6.3 3-.9 3-2.6C18.5 14.4 15.5 12 12 12z"/></svg>',
        "search":    f'<svg width="{s}" height="{s}" fill="none" stroke="{color}" stroke-width="2" viewBox="0 0 24 24"><circle cx="11" cy="11" r="7"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>',
        "birth":     f'<svg width="{s}" height="{s}" fill="none" stroke="{color}" stroke-width="2" viewBox="0 0 24 24"><path d="M12 22c-4-3-7-6.5-7-10a7 7 0 0114 0c0 3.5-3 7-7 10z"/><circle cx="12" cy="11" r="2.5"/></svg>',
        "cart":      f'<svg width="{s}" height="{s}" fill="none" stroke="{color}" stroke-width="2" viewBox="0 0 24 24"><circle cx="9" cy="21" r="1"/><circle cx="20" cy="21" r="1"/><path d="M1 1h4l2.68 13.39a2 2 0 002 1.61h9.72a2 2 0 002-1.61L23 6H6"/></svg>',
        "clock":     f'<svg width="{s}" height="{s}" fill="none" stroke="{color}" stroke-width="2" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>',
        "receipt":   f'<svg width="{s}" height="{s}" fill="none" stroke="{color}" stroke-width="2" viewBox="0 0 24 24"><path d="M4 2h16v20l-3-2-3 2-3-2-3 2-3-2-1 2z"/><line x1="8" y1="7" x2="16" y2="7"/><line x1="8" y1="11" x2="16" y2="11"/><line x1="8" y1="15" x2="12" y2="15"/></svg>',
    }
    return icons.get(name, "")

# ── Alertes stylées (remplace st.success / st.warning / st.error avec icônes SVG) ──
def alert_box(text, kind="success", icon_name=None):
    palette = {
        "success": ("#E8F5E9", "#2E7D32", "check"),
        "warning": ("#FFF8E1", "#92400E", "hourglass"),
        "error":   ("#FFEBEE", "#C62828", "close"),
        "info":    ("#E3F2FD", "#1565C0", "eye"),
    }
    bg, fg, default_icon = palette.get(kind, palette["success"])
    icon_name = icon_name or default_icon
    st.markdown(f"""
    <div style="background:{bg};color:{fg};border-radius:10px;padding:10px 16px;
                display:flex;align-items:center;gap:10px;font-size:13px;font-weight:600;margin:6px 0;">
      {svg(icon_name,16,fg)}<span>{text}</span>
    </div>""", unsafe_allow_html=True)

# ── CSS global ─────────────────────────────────────────────────────────
st.markdown(f"""
<style>
  html, body, [class*="css"] {{ font-family: 'Inter','Segoe UI',sans-serif; }}
  .block-container {{ padding: 1.5rem 2rem 2rem; }}
  [data-testid="stSidebar"] > div:first-child {{ background:#fff; border-right:1px solid #EEE; }}
  [data-testid="stMetric"] {{ background:#fff; border:1px solid #EEE; border-radius:14px; padding:18px 20px !important; }}
  [data-testid="stMetricLabel"] {{ font-size:11px !important; color:#8A8A8A !important; text-transform:uppercase; letter-spacing:.06em; }}
  [data-testid="stMetricValue"] {{ font-size:26px !important; font-weight:700 !important; color:#1A1A1A !important; }}
  [data-testid="stMetricDelta"]  {{ font-size:12px !important; }}

  /* Sidebar */
  div[data-testid="stSidebar"] div[data-testid="stButton"] button {{
    text-align:left !important; padding:10px 14px !important;
    border-radius:10px !important; font-size:13px !important;
    width:100% !important; border:none !important;
    background:transparent !important; color:#555 !important;
    font-weight:400 !important;
  }}
  div[data-testid="stSidebar"] div[data-testid="stButton"] button:hover {{
    background:#F0F0F0 !important; color:#1A1A1A !important;
  }}
  div[data-testid="stSidebar"] div[data-testid="stButton"] button[kind="primary"] {{
    background:{ACCENT} !important; color:#fff !important; font-weight:600 !important;
  }}
  div[data-testid="stSidebar"] div[data-testid="stButton"] button[kind="primary"]:hover {{
    background:{ACCENT_DARK} !important;
  }}

  /* Boutons principaux */
  div[data-testid="stMain"] .stButton > button {{
    background:{ACCENT}; color:#fff; border:none; border-radius:10px;
    font-weight:600; padding:9px 20px;
  }}
  div[data-testid="stMain"] .stButton > button:hover {{ background:{ACCENT_DARK}; color:#fff; }}

  /* Badges */
  .badge-dispo  {{ background:#E8F5E9; color:#2E7D32; border-radius:20px; padding:3px 10px; font-size:11px; font-weight:600; display:inline-block; }}
  .badge-vendu  {{ background:#FFF3E0; color:#E65100; border-radius:20px; padding:3px 10px; font-size:11px; font-weight:600; display:inline-block; }}
  .badge-malade {{ background:#FFEBEE; color:#C62828; border-radius:20px; padding:3px 10px; font-size:11px; font-weight:600; display:inline-block; }}
  .badge-quaran {{ background:#E3F2FD; color:#1565C0; border-radius:20px; padding:3px 10px; font-size:11px; font-weight:600; display:inline-block; }}
  .badge-naissance {{ background:#F3E8FD; color:#7B1FA2; border-radius:20px; padding:3px 10px; font-size:11px; font-weight:600; display:inline-block; }}
  .badge-achat  {{ background:#E3F2FD; color:#1565C0; border-radius:20px; padding:3px 10px; font-size:11px; font-weight:600; display:inline-block; }}

  /* ── Adaptation mobile / petits écrans ────────────────────────────── */
  @media (max-width: 768px) {{
    .block-container {{ padding: 0.8rem 0.8rem 4.5rem !important; }}
    [data-testid="stMetricValue"] {{ font-size:20px !important; }}
    [data-testid="stMetric"] {{ padding:12px 14px !important; }}
    .cat-header {{ font-size:24px !important; margin:4px 0 16px !important; }}
    div[data-testid="stMain"] .stButton > button {{
      padding:11px 16px !important; font-size:14px !important; min-height:42px;
    }}
    /* Les colonnes du contenu principal s'empilent en une seule colonne */
    [data-testid="stMain"] [data-testid="stHorizontalBlock"] {{
      flex-direction: column !important;
    }}
    [data-testid="stMain"] [data-testid="stHorizontalBlock"] > [data-testid="column"] {{
      width: 100% !important;
      flex: 1 1 100% !important;
      min-width: 100% !important;
    }}
    /* Sauf les petites rangées de navigation photo (‹ compteur ›) qu'on garde en ligne */
    [data-testid="stMain"] [data-testid="stHorizontalBlock"].keep-row {{
      flex-direction: row !important;
    }}
    .add-photo-thumb, .cat-card-img-wrap {{ aspect-ratio: 4/3 !important; }}
    h3 {{ font-size:19px !important; }}
  }}
</style>
""", unsafe_allow_html=True)

# ── INITIALISATION & CHARGEMENT DONNÉES ─────────────────────────────
def sanitize_animals(animals):
    """Force tous les champs texte en str pour éviter les erreurs .lower() sur des ints."""
    for a in animals:
        a["earTag"] = str(a.get("earTag", ""))
        a["type"]   = str(a.get("type",   ""))
        a["race"]   = str(a.get("race",   ""))
        a["sex"]    = str(a.get("sex",    ""))
        a["birth"]  = str(a.get("birth",  ""))
        a["status"] = str(a.get("status", ""))
        a["notes"]  = str(a.get("notes",  ""))
        a["origin"] = str(a.get("origin","")) or "Achat"
        a["date_achat"] = str(a.get("date_achat",""))
    return animals

# ── Helpers photos (structure {"url":..., "date":...}) ──────────────
def photo_url(p):
    """Retourne l'URL d'une entrée photo, qu'elle soit dict ou ancienne string."""
    if isinstance(p, dict):
        return p.get("url", "")
    return p or ""

def photo_date(p):
    if isinstance(p, dict):
        return p.get("date", "") or ""
    return ""

def sorted_photos(photos):
    """Trie les photos par date croissante (les photos sans date restent en fin, ordre d'ajout)."""
    with_date    = [p for p in (photos or []) if photo_date(p)]
    without_date = [p for p in (photos or []) if not photo_date(p)]
    with_date.sort(key=lambda p: photo_date(p))
    return with_date + without_date

def age_between(birth, at_date_str):
    """Âge (en mois) entre la date de naissance et une date donnée."""
    try:
        b = date.fromisoformat(str(birth))
        a = date.fromisoformat(str(at_date_str))
        m = (a.year - b.year) * 12 + (a.month - b.month)
        m = max(m, 0)
        return f"{m//12}a {m%12}m" if m >= 12 else f"{m} mois"
    except Exception:
        return "—"

def init_state():
    d = {
        "page":"Dashboard","auth":None,
        "show_form":False,"edit_id":None,"show_race":False,"show_vente":False,
        "catalogue_view":"grid","modal_animal_id":None,"vente_prefill":None,
        "edit_modal_id":None,"confirm_delete_id":None,
        "editing_fiche_id":None,
        "db_loaded": False,
        "show_stock_form": False, "confirm_delete_stock_id": None, "edit_stock_id": None,
        "show_feedtype_form": False,
        "show_expense_form": False, "edit_expense_id": None, "confirm_delete_expense_id": None,
    }
    for k,v in d.items():
        if k not in st.session_state: st.session_state[k]=v

    if not st.session_state.db_loaded:
        try:
            db.init_database()
            st.session_state.animals = sanitize_animals(db.load_animals())
            races_m, races_v = db.load_races()
            st.session_state.races_mouton = races_m
            st.session_state.races_vache  = races_v
            st.session_state.users = db.load_users()
            st.session_state.stock = db.load_stock()
            feed_types = db.load_feed_types()
            st.session_state.feed_types = feed_types if feed_types else list(FEED_TYPES)
            st.session_state.expenses = db.load_expenses()
            st.session_state.db_loaded = True
        except Exception as e:
            st.error(f"Impossible de se connecter à Google Sheets : {e}")
            st.info("Vérifie ton fichier .streamlit/secrets.toml et le partage du Sheet.")
            st.stop()

init_state()
USERS = st.session_state.users

VALID_PAGES = ["Dashboard","Animaux","Catalogue","Ventes","Stock","Depenses","Statistiques","Utilisateurs","Paramètres","FicheAnimal"]

def restore_session_from_url():
    qp = st.query_params
    if st.session_state.auth is None:
        saved_email = qp.get("session_user")
        if saved_email:
            user = next((u for u in USERS if u["email"] == saved_email), None)
            if user:
                st.session_state.auth = {"name": user["name"], "role": user["role"]}
    saved_page = qp.get("page")
    if saved_page in VALID_PAGES:
        st.session_state.page = saved_page
    saved_animal_id = qp.get("animal_id")
    if saved_animal_id and st.session_state.get("modal_animal_id") is None:
        try:
            st.session_state.modal_animal_id = int(saved_animal_id)
        except ValueError:
            pass

restore_session_from_url()

def sync_animals():
    """Sauvegarde les animaux dans Google Sheets avec protection contre l'écrasement accidentel."""
    animals = st.session_state.animals
    if not animals:
        st.warning("Sync annulée : liste vide, aucune donnée envoyée au Sheet.")
        return
    try:
        db.save_all_animals(animals)
    except Exception as e:
        st.error(f"Erreur de synchronisation Google Sheets : {e}")

def sync_stock():
    """Sauvegarde le stock d'alimentation dans Google Sheets."""
    try:
        db.save_all_stock(st.session_state.stock)
    except Exception as e:
        st.error(f"Erreur de synchronisation Google Sheets (Stock) : {e}")

def sync_expenses():
    """Sauvegarde les dépenses dans Google Sheets."""
    try:
        db.save_all_expenses(st.session_state.expenses)
    except Exception as e:
        st.error(f"Erreur de synchronisation Google Sheets (Dépenses) : {e}")

def stock_to_kg(qty, unit):
    return float(qty) * UNIT_TO_KG.get(unit, 1)

def fmt(n): return f"{int(n):,} MAD".replace(",", " ")
def age_str(birth):
    try:
        from datetime import date
        b=date.fromisoformat(birth)
        m=(date.today().year-b.year)*12+(date.today().month-b.month)
        return f"{m//12}a {m%12}m" if m>=12 else f"{m} mois"
    except: return birth

def badge_cls(status):
    return {"Disponible":"badge-dispo","Vendu":"badge-vendu",
            "Malade":"badge-malade","En quarantaine":"badge-quaran"}.get(status,"badge-dispo")

def origin_badge_cls(origin):
    return "badge-naissance" if origin=="Naissance" else "badge-achat"

def go_to_catalogue():
    st.session_state.page = "Catalogue"
    st.session_state.modal_animal_id = None
    st.query_params["page"] = "Catalogue"
    if "animal_id" in st.query_params:
        del st.query_params["animal_id"]

# ══════════════════════════ ZOOM PHOTO (DIALOG) ═══════════════════════
@st.dialog(" ", width="large")
def show_photo_zoom(ear_tag, photo_url_str):
    st.markdown(f"**{ear_tag}**")
    st.image(photo_url_str, use_container_width=True)
    if st.button("Fermer", use_container_width=True, key="close_zoom"):
        st.rerun()

# ══════════════════════════ HISTORIQUE PHOTOS / CROISSANCE ═══════════
def render_growth_timeline(a):
    """Affiche une frise chronologique des photos pour suivre la croissance de l'animal."""
    photos = sorted_photos(a.get("photos") or ([{"url": a["photo"], "date": ""}] if a.get("photo") else []))
    dated = [p for p in photos if photo_date(p)]

    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:8px;margin:22px 0 10px;">
      {svg("clock",18,ACCENT)}<span style="font-weight:700;font-size:15px;">Historique de croissance</span>
    </div>""", unsafe_allow_html=True)

    if not photos:
        st.caption("Aucune photo pour le moment. Ajoute des photos datées pour voir l'animal grandir dans le temps.")
        return
    if not dated:
        st.caption("Astuce : ajoute une date à chaque photo (lors de l'ajout/modification) pour activer la frise de croissance.")
        thumb_cols = st.columns(min(len(photos), 4))
        for col, p in zip(thumb_cols, photos):
            with col:
                st.image(photo_url(p), use_container_width=True)
        return

    slider_key = f"growth_slider_{a['id']}"
    labels = [f"{photo_date(p)} · {age_between(a['birth'], photo_date(p))}" for p in dated]
    if len(dated) == 1:
        sel_label = labels[0]
    else:
        sel_label = st.select_slider("Fais glisser pour voir l'évolution dans le temps",
                                      options=labels, value=labels[-1], key=slider_key)
    sel_idx = labels.index(sel_label)
    sel_photo = dated[sel_idx]

    ic1, ic2 = st.columns([1.3, 1])
    with ic1:
        st.image(photo_url(sel_photo), use_container_width=True)
    with ic2:
        st.markdown(f"""
        <div style="background:{ACCENT_LIGHT};border-radius:12px;padding:16px;margin-top:4px;">
          <div style="font-size:11px;color:#8A8A8A;text-transform:uppercase;letter-spacing:.06em;">Date de la photo</div>
          <div style="font-weight:700;font-size:16px;color:{ACCENT_DARK};margin-bottom:10px;">{photo_date(sel_photo)}</div>
          <div style="font-size:11px;color:#8A8A8A;text-transform:uppercase;letter-spacing:.06em;">Âge à ce moment</div>
          <div style="font-weight:700;font-size:16px;color:{ACCENT_DARK};">{age_between(a["birth"], photo_date(sel_photo))}</div>
        </div>""", unsafe_allow_html=True)

    if len(dated) > 1:
        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
        strip_cols = st.columns(min(len(dated), 6))
        for col, p in zip(strip_cols, dated):
            with col:
                st.image(photo_url(p), use_container_width=True)
                st.caption(photo_date(p))

# ══════════════════════════ PAGE FICHE ANIMAL ══════════════════════════
def page_animal_detail(animal_id):
    a = next((x for x in st.session_state.animals if x["id"]==animal_id), None)
    if not a:
        st.warning("Animal introuvable.")
        if st.button("Retour au catalogue", key="back_notfound"):
            go_to_catalogue()
            st.rerun()
        return

    is_editing = st.session_state.get("editing_fiche_id") == a["id"]
    is_mouton  = a["type"]=="Mouton"
    profit     = a["sellPrice"] - a["buyPrice"]
    profit_c   = GREEN if profit>=0 else RED

    if st.button("Retour au catalogue", key="back_to_catalogue"):
        if is_editing:
            photo_key = f"photos_edit_fiche_{a['id']}"
            if photo_key in st.session_state: del st.session_state[photo_key]
            st.session_state.editing_fiche_id = None
        go_to_catalogue()
        st.rerun()

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
    photos = a.get("photos") or ([{"url": a["photo"], "date": ""}] if a.get("photo") else [])

    gal_col, info_col = st.columns([1.1, 1.4])

    with gal_col:
        if is_editing:
            st.markdown("**Photos**")
            new_photos_edit = photo_uploader_block(f"fiche_{a['id']}", photos)
        elif photos:
            sel_key = f"selected_photo_{a['id']}"
            if sel_key not in st.session_state or st.session_state[sel_key] >= len(photos):
                st.session_state[sel_key] = 0
            st.image(photo_url(photos[st.session_state[sel_key]]), use_container_width=True)
            zc1, zc2 = st.columns([1,3])
            with zc1:
                if st.button("Agrandir", use_container_width=True, key=f"zoom_btn_{a['id']}"):
                    show_photo_zoom(a["earTag"], photo_url(photos[st.session_state[sel_key]]))
            if len(photos) > 1:
                st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
                thumb_cols = st.columns(len(photos))
                for i, (col, p) in enumerate(zip(thumb_cols, photos)):
                    with col:
                        st.image(photo_url(p), use_container_width=True)
                        if st.button("Voir", key=f"thumb_{a['id']}_{i}", use_container_width=True):
                            st.session_state[sel_key] = i
                            st.rerun()
        else:
            st.markdown(f"""
            <div style="width:100%;height:420px;border-radius:16px;background:{ACCENT_LIGHT};
                        display:flex;align-items:center;justify-content:center;margin-bottom:8px;">
              <span style="color:#8A8A8A;font-size:14px;letter-spacing:.04em;">Aucune image</span>
            </div>""", unsafe_allow_html=True)

    with info_col:
        if is_editing:
            st.markdown(f"""<div style="font-weight:800;font-size:22px;margin-bottom:14px;display:flex;align-items:center;gap:8px;">
                {svg("edit",20,ACCENT_DARK)}<span>Modifier {a["earTag"]}</span></div>""", unsafe_allow_html=True)
            origin = st.radio("Origine *", ["Achat","Naissance"],
                               index=["Achat","Naissance"].index(a.get("origin","Achat")),
                               horizontal=True, key=f"e_origin_{a['id']}")
            c1,c2 = st.columns(2)
            with c1:
                atype = st.selectbox("Type *", ["Mouton","Vache"],
                                      index=["Mouton","Vache"].index(a["type"]), key=f"e_type_{a['id']}")
            with c2:
                sex = st.selectbox("Sexe *", ["Mâle","Femelle"],
                                    index=["Mâle","Femelle"].index(a["sex"]), key=f"e_sex_{a['id']}")
            races = st.session_state.races_mouton if atype=="Mouton" else st.session_state.races_vache
            c3,c4 = st.columns(2)
            with c3:
                dr = races.index(a["race"]) if a["race"] in races else 0
                race = st.selectbox("Race *", races, index=dr, key=f"e_race_{a['id']}")
            with c4:
                birth = st.text_input("Date de naissance *", value=a["birth"],
                                       placeholder="YYYY-MM-DD", key=f"e_birth_{a['id']}")
            c5,c6 = st.columns(2)
            with c5:
                ear_tag = st.text_input("N° de boucle *", value=a["earTag"], key=f"e_ear_{a['id']}")
            with c6:
                weight = st.number_input("Poids (kg)", value=float(a["weight"]), min_value=0.0,
                                          key=f"e_weight_{a['id']}")
            date_achat = st.text_input("Date d'achat", value=a.get("date_achat",""),
                                        placeholder="YYYY-MM-DD", key=f"e_date_achat_{a['id']}")
            c7,c8 = st.columns(2)
            with c7:
                buy_p = st.number_input("Prix d'achat (MAD)" if origin=="Achat" else "Coût (optionnel, MAD)",
                                         value=float(a["buyPrice"]), min_value=0.0,
                                         key=f"e_buy_{a['id']}")
            with c8:
                sell_p = st.number_input("Prix de vente (MAD)", value=float(a["sellPrice"]), min_value=0.0,
                                          key=f"e_sell_{a['id']}")
            stats  = ["Disponible","Vendu","Malade","En quarantaine"]
            status = st.selectbox("Statut", stats, index=stats.index(a["status"]), key=f"e_status_{a['id']}")
            notes  = st.text_input("Notes", value=a.get("notes",""),
                                    placeholder="ex: bonne laitière…", key=f"e_notes_{a['id']}")
            st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
            bc1, bc2 = st.columns([1,2])
            with bc1:
                if st.button("Annuler", use_container_width=True, key=f"e_cancel_{a['id']}"):
                    photo_key = f"photos_edit_fiche_{a['id']}"
                    if photo_key in st.session_state: del st.session_state[photo_key]
                    st.session_state.editing_fiche_id = None
                    st.rerun()
            with bc2:
                if st.button("Enregistrer", use_container_width=True, key=f"e_save_{a['id']}"):
                    if not ear_tag or not race or not birth:
                        st.error("Remplissez les champs obligatoires (*).")
                    else:
                        photo_key = f"photos_edit_fiche_{a['id']}"
                        saved_photos = st.session_state.get(photo_key, photos)
                        updated = {
                            "id": a["id"], "type": atype, "race": race, "sex": sex,
                            "birth": birth, "earTag": ear_tag, "buyPrice": buy_p,
                            "sellPrice": sell_p, "status": status, "weight": weight,
                            "notes": notes, "origin": origin, "date_achat": date_achat.strip(),
                            "photos": saved_photos,
                            "photo":  photo_url(saved_photos[0]) if saved_photos else None,
                        }
                        st.session_state.animals = [updated if x["id"]==a["id"] else x
                                                    for x in st.session_state.animals]
                        sync_animals()
                        if photo_key in st.session_state: del st.session_state[photo_key]
                        st.session_state.editing_fiche_id = None
                        alert_box("Animal modifié !", "success")
                        st.rerun()
        else:
            hc1, hc2 = st.columns([3,1])
            with hc1:
                sex_icon = svg("male" if a["sex"]=="Mâle" else "female", 16,
                               "#1565C0" if a["sex"]=="Mâle" else "#C62828")
                st.markdown(f"""
                <div style="display:flex;align-items:center;gap:8px;margin-bottom:2px;">
                  <span style="font-weight:800;font-size:24px">{a["earTag"]}</span>
                  {sex_icon}
                </div>
                <div style="font-size:13px;color:#8A8A8A">{a["type"]} · {a["race"]}</div>
                """, unsafe_allow_html=True)
            with hc2:
                origin_val = a.get("origin","Achat")
                st.markdown(f"""<div style="text-align:right;padding-top:6px;display:flex;flex-direction:column;gap:4px;align-items:flex-end;">
                  <span class="{badge_cls(a["status"])}">{a["status"]}</span>
                  <span class="{origin_badge_cls(origin_val)}">{origin_val}</span>
                </div>""", unsafe_allow_html=True)
            st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
            g1,g2,g3 = st.columns(3)
            for col, label, val in [
                (g1,"Poids",        f"{a['weight']} kg"),
                (g2,"Âge",          age_str(a["birth"])),
                (g3,"Naissance",    a["birth"]),
            ]:
                with col:
                    st.markdown(f"""
                    <div style="background:#F8F8F8;border-radius:10px;padding:12px;text-align:center;">
                      <div style="font-size:10px;color:#8A8A8A;text-transform:uppercase;margin-bottom:4px;">{label}</div>
                      <div style="font-weight:700;font-size:14px">{val}</div>
                    </div>""", unsafe_allow_html=True)
            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
            g4,g5,g6,g7 = st.columns(4)
            for col, label, val, color in [
                (g4,"Prix achat",  fmt(a["buyPrice"]),   "#1A1A1A"),
                (g5,"Prix vente",  fmt(a["sellPrice"]),  "#1A1A1A"),
                (g6,"Bénéfice",    ("+" if profit>=0 else "")+fmt(profit), profit_c),
                (g7,"Date d'achat", a.get("date_achat","") or "—", "#1A1A1A"),
            ]:
                with col:
                    st.markdown(f"""
                    <div style="background:#F8F8F8;border-radius:10px;padding:12px;text-align:center;">
                      <div style="font-size:10px;color:#8A8A8A;text-transform:uppercase;margin-bottom:4px;">{label}</div>
                      <div style="font-weight:700;font-size:14px;color:{color}">{val}</div>
                    </div>""", unsafe_allow_html=True)
            if a.get("notes"):
                st.markdown(f"""
                <div style="background:{ACCENT_LIGHT};border-radius:10px;padding:10px 14px;
                            font-size:12px;color:#555;font-style:italic;margin-top:10px;">
                  {svg("star",12,ACCENT)} {a["notes"]}
                </div>""", unsafe_allow_html=True)
            st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
            if a["status"]=="Disponible":
                if st.button("Vendre cet animal", use_container_width=True, key="modal_sell"):
                    st.session_state.vente_prefill   = a["earTag"]
                    st.session_state.show_vente      = True
                    st.session_state.modal_animal_id = None
                    st.session_state.page            = "Ventes"
                    st.query_params["page"] = "Ventes"
                    if "animal_id" in st.query_params:
                        del st.query_params["animal_id"]
                    st.rerun()
            st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
            ec1, ec2 = st.columns(2)
            with ec1:
                if st.button("Modifier", use_container_width=True, key="fiche_edit"):
                    st.session_state.editing_fiche_id = a["id"]
                    st.rerun()
            with ec2:
                if st.button("Supprimer", use_container_width=True, key="fiche_delete"):
                    st.session_state.confirm_delete_id = a["id"]
                    st.rerun()
            if st.session_state.get("confirm_delete_id") == a["id"]:
                st.warning(f"Confirmer la suppression de **{a['earTag']}** ? Cette action est irréversible.")
                dc1, dc2 = st.columns(2)
                with dc1:
                    if st.button("Annuler", use_container_width=True, key="cancel_delete"):
                        st.session_state.confirm_delete_id = None
                        st.rerun()
                with dc2:
                    if st.button("Confirmer la suppression", use_container_width=True, key="confirm_delete"):
                        photos_to_delete = [photo_url(p) for p in (a.get("photos") or ([{"url": a["photo"]}] if a.get("photo") else []))]
                        if photos_to_delete:
                            with st.spinner("Suppression des photos…"):
                                supa_storage.delete_photos(photos_to_delete)
                        st.session_state.animals = [x for x in st.session_state.animals if x["id"] != a["id"]]
                        sync_animals()
                        st.session_state.confirm_delete_id = None
                        go_to_catalogue()
                        alert_box("Animal supprimé.", "success")
                        st.rerun()

    if not is_editing:
        render_growth_timeline(a)

# ══════════════════════════ MODAL MODIFICATION (pour page Animaux) ═══
@st.dialog("Modifier l'animal", width="large")
def show_edit_modal(animal_id):
    a = next((x for x in st.session_state.animals if x["id"]==animal_id), None)
    if not a:
        st.session_state.edit_modal_id = None
        return
    origin = st.radio("Origine *", ["Achat","Naissance"],
                       index=["Achat","Naissance"].index(a.get("origin","Achat")),
                       horizontal=True, key=f"m_origin_{animal_id}")
    c1,c2 = st.columns(2)
    with c1: atype = st.selectbox("Type *", ["Mouton","Vache"], index=["Mouton","Vache"].index(a["type"]))
    with c2: sex   = st.selectbox("Sexe *", ["Mâle","Femelle"], index=["Mâle","Femelle"].index(a["sex"]))
    races = st.session_state.races_mouton if atype=="Mouton" else st.session_state.races_vache
    c3,c4 = st.columns(2)
    with c3:
        dr = races.index(a["race"]) if a["race"] in races else 0
        race = st.selectbox("Race *", races, index=dr)
    with c4:
        birth = st.text_input("Date de naissance *", value=a["birth"], placeholder="YYYY-MM-DD")
    c5,c6 = st.columns(2)
    with c5: ear_tag = st.text_input("N° de boucle *", value=a["earTag"])
    with c6: weight  = st.number_input("Poids (kg)", value=float(a["weight"]), min_value=0.0)
    date_achat = st.text_input("Date d'achat", value=a.get("date_achat",""), placeholder="YYYY-MM-DD")
    c7,c8 = st.columns(2)
    with c7: buy_p  = st.number_input("Prix d'achat (MAD)" if origin=="Achat" else "Coût (optionnel, MAD)", value=float(a["buyPrice"]), min_value=0.0)
    with c8: sell_p = st.number_input("Prix de vente (MAD)", value=float(a["sellPrice"]), min_value=0.0)
    stats = ["Disponible","Vendu","Malade","En quarantaine"]
    status = st.selectbox("Statut", stats, index=stats.index(a["status"]))
    notes  = st.text_input("Notes", value=a.get("notes",""), placeholder="ex: bonne laitière…")
    st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
    st.markdown("**Photos**")
    current_photos = a.get("photos") or ([{"url": a["photo"], "date": ""}] if a.get("photo") else [])
    new_photos = photo_uploader_block(f"editmodal_{animal_id}", current_photos)
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    bc1, bc2 = st.columns([1,2])
    with bc1:
        if st.button("Annuler", use_container_width=True, key="edit_modal_cancel"):
            photo_key = f"photos_edit_editmodal_{animal_id}"
            if photo_key in st.session_state: del st.session_state[photo_key]
            st.session_state.edit_modal_id = None
            st.rerun()
    with bc2:
        if st.button("Enregistrer", use_container_width=True, key="edit_modal_save"):
            if not ear_tag or not race or not birth:
                st.error("Remplissez les champs obligatoires (*).")
            else:
                updated = {
                    "id": a["id"], "type": atype, "race": race, "sex": sex,
                    "birth": birth, "earTag": ear_tag, "buyPrice": buy_p,
                    "sellPrice": sell_p, "status": status, "weight": weight,
                    "notes": notes, "origin": origin, "date_achat": date_achat.strip(),
                    "photos": new_photos,
                    "photo":  photo_url(new_photos[0]) if new_photos else a.get("photo"),
                }
                st.session_state.animals = [updated if x["id"]==a["id"] else x
                                            for x in st.session_state.animals]
                sync_animals()
                photo_key = f"photos_edit_editmodal_{animal_id}"
                if photo_key in st.session_state: del st.session_state[photo_key]
                st.session_state.edit_modal_id = None
                alert_box("Animal modifié !", "success")
                st.rerun()

# ══════════════════════════ LOGIN ══════════════════════════════════════

def get_base64_image(image_path):
    with open(image_path, "rb") as img:
        return base64.b64encode(img.read()).decode()
def login_page():
    col_l,col_r = st.columns([1.1,1])
    bg = get_base64_image("t.png")
    with col_l:
        st.markdown(f"""
<div style="
    background-image:linear-gradient(rgba(15, 61, 48, 0.3), rgba(15, 61, 48, 0.1)), url('data:image/png;base64,{bg}');
    background-size: cover;
    background-position: center;
    background-repeat: no-repeat;
    border-radius:20px;
    padding:48px 40px;
    height:580px;
    display:flex;
    flex-direction:column;
    justify-content:space-between;
">
            <div style="display:flex;align-items:center;gap:12px;margin-bottom:28px;">
              <div style="width:44px;height:44px;border-radius:12px;background:{ACCENT};
                          display:flex;align-items:center;justify-content:center;">
                {svg("animals",26,"#fff")}
              </div>
              <div>
                <div style="color:#fff;font-weight:800;font-size:22px;">Lhawli</div>
                <div style="color:rgba(255,255,255,.5);font-size:11px;">Gestion de bétail</div>
              </div>
            </div>
            <div style="color:#fff;font-size:24px;font-weight:800;line-height:1.35;margin-bottom:14px;">
              <br>
            </div>
            <div style="color:rgba(255,255,255,.6);font-size:13px;line-height:1.7;">
              Suivi en temps réel, gestion des ventes,<br>statistiques et rapports pour votre exploitation.
            </div>
          </div>
        </div>""", unsafe_allow_html=True)
    with col_r:
        st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
        tab_login, tab_register = st.tabs(["Connexion", "Inscription"])
        with tab_login:
            st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
            email    = st.text_input("Email", placeholder="votre@email.com", key="login_email")
            password = st.text_input("Mot de passe", placeholder="••••••••", type="password", key="login_pwd")
            if st.button("Se connecter", use_container_width=True, key="btn_login"):
                users = st.session_state.get("users", db.load_users())
                email_norm = email.strip().lower()
                user  = next((u for u in users
                              if u["email"].strip().lower()==email_norm and db.verify_password(password, u["password"])), None)
                if not user:
                    st.error("Email ou mot de passe incorrect.")
                elif user.get("statut","Actif") == "En attente":
                    alert_box("Votre compte est en attente de validation par un administrateur.", "warning")
                elif user.get("statut","Actif") == "Refusé":
                    alert_box("Votre demande d'accès a été refusée. Contactez un administrateur.", "error")
                else:
                    st.session_state.auth  = {"name": user["name"], "role": user["role"]}
                    st.session_state.users = users
                    st.query_params["session_user"] = user["email"]
                    st.query_params["page"] = st.session_state.page
                    st.rerun()
        with tab_register:
            st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
            st.caption("Créez un compte — un administrateur devra valider votre accès.")
            r_name  = st.text_input("Nom complet", placeholder="ex: Mohammed Alami", key="reg_name")
            r_email = st.text_input("Email",        placeholder="votre@email.com",   key="reg_email")
            r_pwd   = st.text_input("Mot de passe", placeholder="Min. 6 caractères", type="password", key="reg_pwd")
            r_pwd2  = st.text_input("Confirmer le mot de passe", placeholder="••••••••", type="password", key="reg_pwd2")
            if st.button("Créer mon compte", use_container_width=True, key="btn_register"):
                users = st.session_state.get("users", db.load_users())
                errors = []
                if not r_name.strip():   errors.append("Le nom est requis.")
                if not r_email.strip():  errors.append("L'email est requis.")
                if "@" not in r_email:   errors.append("Email invalide.")
                if len(r_pwd) < 6:       errors.append("Mot de passe trop court (min. 6 caractères).")
                if r_pwd != r_pwd2:      errors.append("Les mots de passe ne correspondent pas.")
                if any(u["email"].strip().lower()==r_email.strip().lower() for u in users):
                    errors.append("Cet email est déjà utilisé.")
                if errors:
                    for e in errors: st.error(e)
                else:
                    try:
                        db.register_user(r_email.strip(), r_pwd, r_name.strip())
                        st.session_state.db_loaded = False
                        alert_box("Compte créé ! Un administrateur va valider votre accès sous peu.", "success")
                        st.info("Revenez vous connecter une fois votre compte approuvé.")
                    except Exception as e:
                        st.error(f"Erreur : {e}")

# ══════════════════════════ SIDEBAR ══════════════════════════════════
def sidebar_nav():
    auth = st.session_state.auth
    with st.sidebar:
        st.markdown(f"""
        <div style="display:flex;align-items:center;gap:10px;padding:4px 0 18px;">
          <div style="width:38px;height:38px;border-radius:10px;background:{ACCENT};
                      display:flex;align-items:center;justify-content:center;">
            {svg("animals",20,"#fff")}
          </div>
          <div>
            <div style="font-weight:800;font-size:16px;color:{ACCENT_DARK}">Lhawli</div>
            <div style="font-size:10px;color:#8A8A8A">Gestion de bétail</div>
          </div>
        </div>
        <hr style="border:none;border-top:1px solid #EEE;margin:0 0 8px;">
        """, unsafe_allow_html=True)

        pages = [
            ("dashboard", "Dashboard",    "Dashboard"),
            ("animals",   "Animaux",      "Animaux"),
            ("catalogue", "Catalogue",    "Catalogue"),
            ("sales",     "Ventes",       "Ventes"),
            ("cart",      "Stock",        "Stock"),
            ("receipt",   "Dépenses",     "Depenses"),
            ("stats",     "Statistiques", "Statistiques"),
            ("users",     "Utilisateurs", "Utilisateurs"),
            ("settings",  "Paramètres",   "Paramètres"),
        ]
        active_page = "Catalogue" if st.session_state.page == "FicheAnimal" else st.session_state.page
        for icon_name, label, key in pages:
            active = active_page == key
            icol, bcol = st.columns([0.15, 0.85])
            with icol:
                icon_color = ACCENT if active else "#8A8A8A"
                st.markdown(
                    f"<div style='padding-top:10px;color:{icon_color};'>{svg(icon_name, 16)}</div>",
                    unsafe_allow_html=True)
            with bcol:
                if st.button(label, key=f"nav_{key}", use_container_width=True,
                             type="primary" if active else "secondary"):
                    st.session_state.page       = key
                    st.session_state.show_form  = False
                    st.session_state.show_race  = False
                    st.session_state.show_vente = False
                    st.session_state.modal_animal_id = None
                    st.query_params["page"] = key
                    if "animal_id" in st.query_params:
                        del st.query_params["animal_id"]
                    st.rerun()

        st.markdown("<hr style='border:none;border-top:1px solid #EEE;margin:10px 0'>", unsafe_allow_html=True)
        st.markdown(f"""
        <div style="display:flex;align-items:center;gap:10px;padding:4px 0 10px;">
          <div style="width:34px;height:34px;border-radius:50%;background:{ACCENT_LIGHT};
                      display:flex;align-items:center;justify-content:center;
                      font-weight:700;color:{ACCENT};font-size:14px;">
            {auth['name'][0].upper()}
          </div>
          <div>
            <div style="font-weight:600;font-size:13px">{auth['name']}</div>
            <div style="font-size:11px;color:#8A8A8A">{auth['role']}</div>
          </div>
        </div>""", unsafe_allow_html=True)

        ric, rbc = st.columns([0.15, 0.85])
        with ric:
            st.markdown(f"<div style='padding-top:10px;color:#8A8A8A;'>{svg('refresh',16)}</div>", unsafe_allow_html=True)
        with rbc:
            if st.button("Rafraîchir depuis Sheets", key="refresh_btn", use_container_width=True):
                st.session_state.animals = sanitize_animals(db.load_animals())
                races_m, races_v = db.load_races()
                st.session_state.races_mouton = races_m
                st.session_state.races_vache  = races_v
                st.session_state.stock = db.load_stock()
                st.session_state.expenses = db.load_expenses()
                alert_box("Données rechargées !", "success")
                st.rerun()

        lic, lbc = st.columns([0.15, 0.85])
        with lic:
            st.markdown(f"<div style='padding-top:10px;color:#8A8A8A;'>{svg('logout',16)}</div>", unsafe_allow_html=True)
        with lbc:
            if st.button("Se déconnecter", key="logout_btn", use_container_width=True):
                st.session_state.auth = None
                st.session_state.page = "Dashboard"
                st.query_params.clear()
                st.rerun()

# ══════════════════════════ DASHBOARD ═══════════════════════════════
def page_dashboard():
    animals = st.session_state.animals
    st.markdown(f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:20px;">{svg("dashboard",22,ACCENT)}<span style="font-size:22px;font-weight:700">Vue d\'ensemble</span></div>', unsafe_allow_html=True)
    tm = sum(1 for a in animals if a["type"]=="Mouton")
    tv = sum(1 for a in animals if a["type"]=="Vache")
    ta = sum(a["buyPrice"] for a in animals)
    tv2= sum(a["sellPrice"] for a in animals if a["status"]=="Vendu")
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Total Moutons",  tm,  delta=f"{sum(1 for a in animals if a['type']=='Mouton' and a['status']=='Disponible')} dispo")
    c2.metric("Total Vaches",   tv,  delta=f"{sum(1 for a in animals if a['type']=='Vache'  and a['status']=='Disponible')} dispo")
    c3.metric("Valeur Achat",   fmt(ta))
    c4.metric("Revenus Ventes", fmt(tv2))
    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    cd,cb,cs = st.columns([1.1,2,1])
    with cd:
        st.markdown("**Répartition**")
        fig = go.Figure(go.Pie(labels=["Moutons","Vaches"],values=[tm,tv],hole=0.6,
                               marker_colors=[ACCENT,ACCENT_LIGHT],textinfo="none"))
        fig.update_layout(margin=dict(t=10,b=10,l=10,r=10),height=180,showlegend=True,
            legend=dict(orientation="v",x=1,y=0.5,font=dict(size=11)),
            annotations=[dict(text=f"<b>{tm+tv}</b><br>bêtes",x=0.5,y=0.5,font_size=13,showarrow=False)])
        st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})
    with cb:
        st.markdown("**Activité mensuelle**")
        mois=["Jan","Fév","Mar","Avr","Mai","Jun","Jul"]; vals=[3,5,4,7,6,8,5]
        colors=[ACCENT if m in ("Mai","Jun") else ACCENT_LIGHT for m in mois]
        fig2=go.Figure(go.Bar(x=mois,y=vals,marker_color=colors,width=0.55))
        fig2.update_layout(margin=dict(t=10,b=10,l=10,r=10),height=180,plot_bgcolor="#fff",paper_bgcolor="#fff",
                           yaxis=dict(showgrid=False,showticklabels=False),xaxis=dict(showgrid=False))
        st.plotly_chart(fig2,use_container_width=True,config={"displayModeBar":False})
    with cs:
        st.markdown("**Statuts**")
        for label,val,color in [
            ("Disponibles",sum(1 for a in animals if a["status"]=="Disponible"),"#2E7D32"),
            ("Vendus",     sum(1 for a in animals if a["status"]=="Vendu"),     "#E65100"),
            ("Malades",    sum(1 for a in animals if a["status"]=="Malade"),    RED),
            ("Quarantaine",sum(1 for a in animals if a["status"]=="En quarantaine"),"#1565C0"),
        ]:
            st.markdown(f"""<div style="display:flex;justify-content:space-between;align-items:center;
                padding:8px 0;border-bottom:1px solid #EEE;">
              <span style="display:flex;align-items:center;gap:7px;font-size:12px;">
                <span style="width:8px;height:8px;border-radius:50%;background:{color};display:inline-block;"></span>{label}
              </span><b style="font-size:13px">{val}</b></div>""", unsafe_allow_html=True)
    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    expenses = st.session_state.get("expenses", [])
    total_depenses = sum(e["montant"] for e in expenses)
    ce1, ce2 = st.columns([1,3])
    with ce1:
        st.markdown("**Dépenses totales**")
        st.markdown(f"""
        <div style="background:#F5EEF9;border-radius:14px;padding:16px;text-align:center;">
          {svg("receipt",22,EXPENSE_ACCENT)}
          <div style="font-weight:800;font-size:20px;color:{EXPENSE_ACCENT};margin-top:6px;">{fmt(total_depenses)}</div>
          <div style="font-size:11px;color:#8A8A8A;">{len(expenses)} dépense(s) enregistrée(s)</div>
        </div>""", unsafe_allow_html=True)
    with ce2:
        st.markdown("**Bilan financier global**")
        bilan = tv2 - ta - total_depenses
        bilan_c = GREEN if bilan >= 0 else RED
        st.markdown(f"""
        <div style="background:#F8F8F8;border-radius:10px;padding:14px;display:flex;justify-content:space-between;align-items:center;">
          <div><div style="font-size:11px;color:#8A8A8A;">Revenus ventes − Achats − Dépenses</div>
          <div style="font-size:12px;color:#8A8A8A;margin-top:2px;">{fmt(tv2)} − {fmt(ta)} − {fmt(total_depenses)}</div></div>
          <div style="font-weight:800;font-size:22px;color:{bilan_c}">{"+" if bilan>=0 else ""}{fmt(bilan)}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    st.markdown("**Animaux récents**")
    rows=[{"N° Boucle":a["earTag"],"Type":a["type"],"Race":a["race"],
           "Sexe":a["sex"],"Naissance":a["birth"],"Date d'achat":a.get("date_achat",""),"Origine":a.get("origin","Achat"),"Prix vente":fmt(a["sellPrice"]),"Statut":a["status"]} for a in animals[:5]]
    st.dataframe(pd.DataFrame(rows),use_container_width=True,hide_index=True)

# ══════════════════════════ CATALOGUE (AVEC NOUVEAU CARROUSEL) ══════
def page_catalogue():
    animals = st.session_state.animals

    # ── CSS spécifique catalogue (inchangé, pour les éléments hors iframe) ──
    st.markdown(f"""
    <style>
    .cat-header {{
        font-family: 'Georgia', serif;
        font-size: 32px;
        font-weight: 400;
        letter-spacing: .04em;
        text-align: center;
        color: #1A1A1A;
        margin: 8px 0 24px;
    }}
    .cat-card {{
        background: #fff;
        border: none;
        cursor: pointer;
        padding: 0;
        margin-bottom: 28px;
    }}
    /* Les classes ci-dessous sont toujours utiles pour le nom/race en dehors de l'iframe */
    .cat-info-tag {{
        font-size: 10px;
        letter-spacing: .08em;
        text-transform: uppercase;
        color: #8A8A8A;
        margin-bottom: 3px;
    }}
    .cat-info-name {{
        font-size: 13px;
        font-weight: 600;
        color: #1A1A1A;
        letter-spacing: .02em;
    }}
    .cat-info-sub {{
        font-size: 11px;
        color: #8A8A8A;
        margin-top: 1px;
    }}
    .cat-divider {{
        border: none;
        border-top: 1px solid #EBEBEB;
        margin: 0 0 28px;
    }}
                    .cat-card-img-wrap {{ position:relative; background:#F5F5F5; border-radius:2px;
         overflow:hidden; aspect-ratio:3/4; display:flex; align-items:center;
         justify-content:center; margin-bottom:8px; }}
     .cat-card-img-wrap img {{ width:100%; height:100%; object-fit:cover; }}
     .cat-badge {{ position:absolute; top:10px; left:10px; font-size:9px; font-weight:700;
         letter-spacing:.1em; text-transform:uppercase; padding:3px 8px; border-radius:2px; }}
     .cat-badge-dispo  {{ background:#E8F5E9; color:#2E7D32; }}
     .cat-badge-vendu  {{ background:#FFF3E0; color:#E65100; }}
     .cat-badge-malade {{ background:#FFEBEE; color:#C62828; }}
     .cat-badge-quaran {{ background:#E3F2FD; color:#1565C0; }}
     .cat-badge-origin {{ position:absolute; top:10px; right:10px; font-size:9px; font-weight:700;
         letter-spacing:.1em; text-transform:uppercase; padding:3px 8px; border-radius:2px;
         background:rgba(255,255,255,.9); color:#1A1A1A; }}
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="cat-header">Catalogue</div>', unsafe_allow_html=True)

    fc1,fc2,fc3 = st.columns([2,1,1])
    with fc1: search = st.text_input("",placeholder="Rechercher par boucle, race…",label_visibility="collapsed")
    with fc2: ftype  = st.selectbox("",["Tous","Mouton","Vache"],label_visibility="collapsed")
    with fc3: fstat  = st.selectbox("",["Tous statuts","Disponible","Vendu","Malade","En quarantaine"],label_visibility="collapsed")

    filtered = [a for a in animals
                if (ftype=="Tous" or a["type"]==ftype)
                and (fstat=="Tous statuts" or a["status"]==fstat)
                and (search.lower() in str(a["earTag"]).lower()
                     or search.lower() in str(a["race"]).lower()
                     or search.lower() in str(a["type"]).lower())]

    st.markdown(f"""
    <div style="display:flex;gap:16px;margin:8px 0 24px;font-size:11px;
                color:#8A8A8A;letter-spacing:.06em;text-transform:uppercase;">
      <span>{len(filtered)} ANIMAUX</span>
      <span style="color:#2E7D32;">{sum(1 for a in filtered if a["status"]=="Disponible")} DISPONIBLES</span>
      <span style="color:#E65100;">{sum(1 for a in filtered if a["status"]=="Vendu")} VENDUS</span>
    </div>
    <hr class="cat-divider">
    """, unsafe_allow_html=True)

    if not filtered:
        st.markdown('<div style="text-align:center;padding:60px 0;color:#8A8A8A;font-size:13px;letter-spacing:.06em;">AUCUN ANIMAL TROUVÉ</div>', unsafe_allow_html=True)
        return

    # ── Grille 3 colonnes (s'empile en 1 colonne sur mobile via CSS) ──
    for i in range(0, len(filtered), 3):
        cols = st.columns(3, gap="large")
        for col, a in zip(cols, filtered[i:i+3]):
            is_mouton = a["type"] == "Mouton"
            photos    = a.get("photos") or ([{"url": a["photo"]}] if a.get("photo") else [])
            badge_map = {
                "Disponible":    ("cat-badge-dispo",  "DISPONIBLE"),
                "Vendu":         ("cat-badge-vendu",  "VENDU"),
                "Malade":        ("cat-badge-malade", "MALADE"),
                "En quarantaine":("cat-badge-quaran", "QUARANTAINE"),
            }
            badge_cls_name, badge_label = badge_map.get(a["status"], ("cat-badge-dispo",""))
            origin_val = a.get("origin","Achat")

            with col:
                idx_key = f"cat_photo_idx_{a['id']}"
                if idx_key not in st.session_state:
                    st.session_state[idx_key] = 0
                if photos and st.session_state[idx_key] >= len(photos):
                    st.session_state[idx_key] = 0

                if photos:
                    current_photo = photo_url(photos[st.session_state[idx_key]])
                    img_html = f'<img src="{current_photo}">'
                else:
                    img_html = f"""
                    <div style="width:100%;height:100%;display:flex;align-items:center;
                                justify-content:center;background:#F0EDE8;">
                        <span style="color:#BDBDBD;font-size:12px;letter-spacing:.04em;">Aucune image</span>
                    </div>"""

                st.markdown(f"""
                <div class="cat-card">
                  <div class="cat-card-img-wrap">
                    <span class="cat-badge {badge_cls_name}">{badge_label}</span>
                    <span class="cat-badge-origin">{origin_val.upper()}</span>
                    {img_html}
                  </div>
                </div>
                """, unsafe_allow_html=True)

                # ── Navigation carrousel : vrais boutons Streamlit (fiable, pas de JS) ──
                if len(photos) > 1:
                    pc1, pc2, pc3 = st.columns([1,2,1])
                    with pc1:
                        if st.button("‹", key=f"prev_{a['id']}", use_container_width=True):
                            st.session_state[idx_key] = (st.session_state[idx_key] - 1) % len(photos)
                            st.rerun()
                    with pc2:
                        st.markdown(
                            f"<div style='text-align:center;font-size:11px;color:#8A8A8A;padding-top:6px;'>"
                            f"{st.session_state[idx_key]+1} / {len(photos)}</div>",
                            unsafe_allow_html=True)
                    with pc3:
                        if st.button("›", key=f"next_{a['id']}", use_container_width=True):
                            st.session_state[idx_key] = (st.session_state[idx_key] + 1) % len(photos)
                            st.rerun()

                st.markdown(f"""
                <div class="cat-info-tag">{a["type"].upper()}</div>
                <div class="cat-info-name">{a["earTag"]}</div>
                <div class="cat-info-sub">{a["race"]}</div>
                """, unsafe_allow_html=True)

                if st.button("Voir la fiche →", key=f"open_{a['id']}", use_container_width=True):
                    st.session_state.modal_animal_id = a["id"]
                    st.session_state.page = "FicheAnimal"
                    st.query_params["page"] = "FicheAnimal"
                    st.query_params["animal_id"] = str(a["id"])
                    st.rerun()

        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
# ══════════════════════════ ANIMAUX ══════════════════════════════════
def page_animals():
    auth=st.session_state.auth; animals=st.session_state.animals; is_obs=auth["role"]=="Observateur"
    hc1,hc2,hc3=st.columns([3,1,1])
    with hc1:
        st.markdown(f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:4px;">{svg("animals",22,ACCENT)}<span style="font-size:22px;font-weight:700">Gestion des Animaux</span></div>', unsafe_allow_html=True)
        if is_obs: st.info("Mode lecture seule")
    if not is_obs:
        with hc2:
            if st.button("Ajouter", use_container_width=True):
                st.session_state.show_form=True; st.session_state.show_race=False; st.session_state.edit_id=None
        with hc3:
            if st.button("Nouvelle race", use_container_width=True):
                st.session_state.show_race=True; st.session_state.show_form=False

    if st.session_state.show_race and not is_obs:
        st.markdown(f'<div style="background:{ACCENT_DARK};border-radius:14px 14px 0 0;padding:14px 20px;color:#fff;font-weight:700;font-size:15px;display:flex;align-items:center;gap:8px;">{svg("paw",18,"#fff")}<span>Ajouter une nouvelle race</span></div>', unsafe_allow_html=True)
        rc1,rc2,rc3=st.columns([1,2,1])
        with rc1: race_type=st.selectbox("Type",["Mouton","Vache"],key="race_type_sel")
        with rc2: new_race =st.text_input("Nom",placeholder="ex: Beni Guil",key="new_race_input")
        with rc3:
            st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
            if st.button("Ajouter",key="btn_add_race",use_container_width=True):
                if new_race.strip():
                    liste=st.session_state.races_mouton if race_type=="Mouton" else st.session_state.races_vache
                    if new_race.strip() not in liste:
                        liste.append(new_race.strip())
                        try:
                            db.add_race(race_type, new_race.strip())
                            alert_box(f"Race « {new_race.strip()} » ajoutée !", "success")
                        except Exception as e:
                            st.error(f"Erreur de synchronisation : {e}")
                    else: st.warning("Cette race existe déjà.")
                else: st.error("Entrez un nom.")
        if st.button("Fermer",key="close_race"): st.session_state.show_race=False; st.rerun()
        st.markdown("<hr>", unsafe_allow_html=True)

    if st.session_state.show_form and not is_obs:
        animal_form()
        return  # ← masque tout le reste de la page

    fc1,fc2=st.columns([3,1])
    with fc1: search=st.text_input("",placeholder="Rechercher…",label_visibility="collapsed")
    with fc2: ftype =st.selectbox("",["Tous","Mouton","Vache"],label_visibility="collapsed")
    filtered=[a for a in animals if (ftype=="Tous" or a["type"]==ftype)
              and (search.lower() in str(a["earTag"]).lower() or search.lower() in str(a["race"]).lower())]
    mc1,mc2,mc3=st.columns(3)
    mc1.metric("Total filtré",len(filtered))
    mc2.metric("Disponibles", sum(1 for a in filtered if a["status"]=="Disponible"))
    mc3.metric("Vendus",      sum(1 for a in filtered if a["status"]=="Vendu"))
    if not filtered: st.warning("Aucun animal trouvé.")
    elif is_obs:
        rows=[{"N° Boucle":a["earTag"],"Type":a["type"],"Race":a["race"],"Sexe":a["sex"],
               "Naissance":a["birth"],"Date d'achat":a.get("date_achat",""),"Origine":a.get("origin","Achat"),"Poids (kg)":a["weight"],
               "Prix achat":fmt(a["buyPrice"]),"Prix vente":fmt(a["sellPrice"]),"Statut":a["status"]} for a in filtered]
        st.dataframe(pd.DataFrame(rows),use_container_width=True,hide_index=True)
    else:
        st.caption("Modifie directement une cellule, puis clique sur *Enregistrer les modifications du tableau*.")
        all_races = sorted(set(st.session_state.races_mouton) | set(st.session_state.races_vache))
        edit_rows=[{
            "id":            a["id"],
            "N° Boucle":     a["earTag"],
            "Type":          a["type"],
            "Race":          a["race"],
            "Sexe":          a["sex"],
            "Naissance":     pd.to_datetime(a.get("birth",""), errors="coerce"),
            "Date d'achat":  pd.to_datetime(a.get("date_achat",""), errors="coerce"),
            "Origine":       a.get("origin","Achat"),
            "Poids (kg)":    float(a["weight"]),
            "Prix achat":    float(a["buyPrice"]),
            "Prix vente":    float(a["sellPrice"]),
            "Statut":        a["status"],
        } for a in filtered]
        edit_df = pd.DataFrame(edit_rows).set_index("id")

        edited_df = st.data_editor(
            edit_df,
            use_container_width=True,
            num_rows="fixed",
            key="animals_table_editor",
            column_config={
                "N° Boucle":    st.column_config.TextColumn("N° Boucle"),
                "Type":         st.column_config.SelectboxColumn("Type", options=["Mouton","Vache"]),
                "Race":         st.column_config.SelectboxColumn("Race", options=all_races),
                "Sexe":         st.column_config.SelectboxColumn("Sexe", options=["Mâle","Femelle"]),
                "Naissance":    st.column_config.DateColumn("Naissance", format="YYYY-MM-DD"),
                "Date d'achat": st.column_config.DateColumn("Date d'achat", format="YYYY-MM-DD"),
                "Origine":      st.column_config.SelectboxColumn("Origine", options=["Achat","Naissance"]),
                "Poids (kg)":   st.column_config.NumberColumn("Poids (kg)", min_value=0.0, step=1.0),
                "Prix achat":   st.column_config.NumberColumn("Prix achat", min_value=0.0, step=1.0),
                "Prix vente":   st.column_config.NumberColumn("Prix vente", min_value=0.0, step=1.0),
                "Statut":       st.column_config.SelectboxColumn("Statut", options=["Disponible","Vendu","Malade","En quarantaine"]),
            },
        )

        if st.button("Enregistrer les modifications du tableau", key="save_animals_table"):
            updated_map = {}
            for aid, row in edited_df.iterrows():
                birth_d = row["Naissance"]
                achat_d = row["Date d'achat"]
                updated_map[int(aid)] = {
                    "earTag":     row["N° Boucle"],
                    "type":       row["Type"],
                    "race":       row["Race"],
                    "sex":        row["Sexe"],
                    "birth":      birth_d.strftime("%Y-%m-%d") if pd.notna(birth_d) else "",
                    "date_achat": achat_d.strftime("%Y-%m-%d") if pd.notna(achat_d) else "",
                    "origin":     row["Origine"],
                    "weight":     float(row["Poids (kg)"]),
                    "buyPrice":   float(row["Prix achat"]),
                    "sellPrice":  float(row["Prix vente"]),
                    "status":     row["Statut"],
                }
            for a in st.session_state.animals:
                if a["id"] in updated_map:
                    a.update(updated_map[a["id"]])
            sync_animals()
            alert_box("Tableau mis à jour !", "success")
            st.rerun()

        st.markdown("**Actions :**")
        ac1,ac2,ac3=st.columns([2,1,1])
        with ac1:
            opts={a["earTag"]:a["id"] for a in filtered}
            sel_tag=st.selectbox("",list(opts.keys()),label_visibility="collapsed")
            sel_id=opts[sel_tag]
        with ac2:
            if st.button("Modifier (photos, notes…)",use_container_width=True):
                st.session_state.edit_id   = sel_id
                st.session_state.show_form = True
                st.rerun()
        with ac3:
            if st.button("Supprimer",use_container_width=True):
                a_to_delete = next((a for a in st.session_state.animals if a["id"]==sel_id), None)
                if a_to_delete:
                    photos_to_delete = [photo_url(p) for p in (a_to_delete.get("photos") or ([{"url": a_to_delete["photo"]}] if a_to_delete.get("photo") else []))]
                    if photos_to_delete:
                        with st.spinner("Suppression des photos…"):
                            supa_storage.delete_photos(photos_to_delete)
                st.session_state.animals=[a for a in st.session_state.animals if a["id"]!=sel_id]
                sync_animals()
                alert_box("Supprimé.", "success"); st.rerun()

    if st.session_state.get("edit_modal_id") is not None:
        show_edit_modal(st.session_state.edit_modal_id)


def photo_uploader_block(key_prefix, current_photos):
    """
    Gère l'upload/suppression de photos via Supabase Storage.
    Les photos sont stockées sur Supabase, seules les URLs (+ date de prise) sont gardées
    en session sous la forme {"url":..., "date":"YYYY-MM-DD"}.
    Retourne la liste des entrées photo (dicts).
    """
    state_key = f"photos_edit_{key_prefix}"
    hash_key  = f"{state_key}_last_hash"

    # Initialiser depuis current_photos si pas encore en session
    if state_key not in st.session_state:
        normed = []
        for p in (current_photos or []):
            if isinstance(p, dict) and p.get("url"):
                normed.append({"url": p["url"], "date": p.get("date","") or ""})
            elif isinstance(p, str) and p:
                normed.append({"url": p, "date": ""})
        st.session_state[state_key] = normed

    photos = st.session_state[state_key]

    # ── Miniatures existantes avec lightbox + suppression ──
    if photos:
        lightbox_html = ""
        thumbs_html   = ""
        for i, p in enumerate(photos):
            url = photo_url(p)
            d   = photo_date(p)
            date_badge = f'<div style="position:absolute;bottom:2px;left:2px;right:2px;background:rgba(0,0,0,.55);color:#fff;font-size:9px;text-align:center;border-radius:6px;padding:1px 0;">{d}</div>' if d else ""
            lightbox_html += f"""
            <div id="lb_{key_prefix}_{i}"
                 style="display:none;position:fixed;inset:0;background:rgba(0,0,0,.88);
                        z-index:99999;align-items:center;justify-content:center;flex-direction:column;"
                 onclick="this.style.display='none'">
              <img src="{url}" style="max-width:92vw;max-height:88vh;border-radius:14px;" />
              <div style="color:rgba(255,255,255,.5);font-size:11px;margin-top:10px;letter-spacing:.06em;">
                CLIQUER POUR FERMER
              </div>
            </div>"""
            thumbs_html += f"""
            <div style="position:relative;display:inline-block;margin:4px;">
              <img src="{url}"
                   onclick="document.getElementById('lb_{key_prefix}_{i}').style.display='flex'"
                   style="width:80px;height:80px;object-fit:cover;border-radius:10px;
                          border:2px solid #E8F4F0;cursor:pointer;" />
              {date_badge}
            </div>"""

        st.markdown(f"""
        {lightbox_html}
        <div style="background:#F8F8F8;border-radius:12px;padding:12px 14px;margin-bottom:8px;">
          <div style="font-size:10px;color:#8A8A8A;font-weight:700;margin-bottom:8px;
                      text-transform:uppercase;letter-spacing:.08em;">
            {svg("camera",12,ACCENT)} {len(photos)} photo(s) — cliquer pour agrandir
          </div>
          <div style="display:flex;flex-wrap:wrap;">{thumbs_html}</div>
        </div>""", unsafe_allow_html=True)

        # Suppression + édition de la date, photo par photo
        for i, p in enumerate(photos):
            dcol1, dcol2 = st.columns([2,1])
            with dcol1:
                new_date = st.date_input(
                    f"Date — photo {i+1}",
                    value=date.fromisoformat(photo_date(p)) if photo_date(p) else None,
                    key=f"photo_date_{key_prefix}_{i}",
                )
                new_date_str = new_date.isoformat() if new_date else ""
                if new_date_str != photo_date(p):
                    st.session_state[state_key][i]["date"] = new_date_str
            with dcol2:
                st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
                if st.button(f"Suppr.", key=f"del_photo_{key_prefix}_{i}", use_container_width=True):
                    url_to_delete = photo_url(st.session_state[state_key][i])
                    with st.spinner("Suppression…"):
                        supa_storage.delete_photos([url_to_delete])
                    st.session_state[state_key].pop(i)
                    st.rerun()

    # ── Upload nouvelle photo ──
    st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
    label    = "Ajouter une photo" if not photos else "Ajouter une autre photo"
    upl_c1, upl_c2 = st.columns([2,1])
    with upl_c1:
        uploaded = st.file_uploader(label, type=["jpg","jpeg","png"],
                                    key=f"photo_upload_{key_prefix}")
    with upl_c2:
        upload_date = st.date_input("Date de la photo", value=date.today(),
                                     key=f"photo_upload_date_{key_prefix}")

    if uploaded is not None:
        file_bytes = uploaded.getvalue()
        import hashlib
        file_hash  = hashlib.md5(file_bytes).hexdigest()

        # Éviter double-upload si fichier déjà traité
        if st.session_state.get(hash_key) != file_hash:
            with st.spinner("Upload vers Supabase…"):
                try:
                    filename  = f"{key_prefix}_{file_hash[:8]}.jpg"
                    public_url = supa_storage.upload_photo(file_bytes, filename)
                    st.session_state[state_key].append({
                        "url": public_url,
                        "date": upload_date.isoformat() if upload_date else "",
                    })
                    st.session_state[hash_key] = file_hash
                    alert_box("Photo uploadée sur Supabase !", "success")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erreur upload Supabase : {e}")
    else:
        # Fichier retiré du uploader → reset du hash
        if hash_key in st.session_state:
            del st.session_state[hash_key]

    return st.session_state[state_key]


def animal_form():
    eid     = st.session_state.edit_id
    animals = st.session_state.animals
    ini     = next((a for a in animals if a["id"]==eid), None) if eid else None
    is_edit = ini is not None

    # ── CSS page d'ajout ──
    st.markdown(f"""
    <style>
    .add-page-wrap {{
        max-width: 960px;
        margin: 0 auto;
    }}
    .add-page-header {{
        display: flex;
        align-items: center;
        gap: 14px;
        margin-bottom: 32px;
        padding-bottom: 20px;
        border-bottom: 1px solid #EBEBEB;
    }}
    .add-page-title {{
        font-family: 'Georgia', serif;
        font-size: 26px;
        font-weight: 400;
        color: #1A1A1A;
        letter-spacing: .02em;
    }}
    .add-page-sub {{
        font-size: 12px;
        color: #8A8A8A;
        letter-spacing: .04em;
        text-transform: uppercase;
        margin-top: 2px;
    }}
    .add-section-label {{
        font-size: 10px;
        font-weight: 700;
        letter-spacing: .1em;
        text-transform: uppercase;
        color: #8A8A8A;
        margin-bottom: 8px;
        margin-top: 20px;
    }}
    .add-photo-zone {{
        background: #F5F5F0;
        border-radius: 16px;
        padding: 20px;
        min-height: 320px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        border: 1.5px dashed #DCDCDC;
        text-align: center;
    }}
    .add-photo-thumb {{
        width: 100%;
        aspect-ratio: 3/4;
        object-fit: cover;
        border-radius: 12px;
        margin-bottom: 10px;
    }}
    .add-badge {{
        display: inline-block;
        font-size: 9px;
        font-weight: 700;
        letter-spacing: .1em;
        text-transform: uppercase;
        padding: 4px 10px;
        border-radius: 4px;
        margin: 2px;
        cursor: pointer;
    }}
    .add-field-group {{
        background: #FAFAFA;
        border-radius: 12px;
        padding: 16px 18px;
        margin-bottom: 12px;
    }}
    .origin-choice {{
        display: flex;
        gap: 12px;
        margin-bottom: 8px;
    }}
    </style>
    """, unsafe_allow_html=True)

    # ── En-tête avec bouton retour ──
    st.markdown(f"""
    <div class="add-page-header">
      <div style="width:44px;height:44px;border-radius:12px;background:{ACCENT};
                  display:flex;align-items:center;justify-content:center;flex-shrink:0;">
        {svg("sheep" if not ini or ini.get("type")=="Mouton" else "cow", 24, "#fff")}
      </div>
      <div>
        <div class="add-page-title">{"Modifier l'animal" if is_edit else "Ajouter un animal"}</div>
        <div class="add-page-sub">{"Mise à jour de la fiche" if is_edit else "Nouvelle entrée dans le troupeau"}</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Deux colonnes : photos à gauche, formulaire à droite ──
    col_photo, col_form = st.columns([1, 1.6], gap="large")

    # ─── COLONNE GAUCHE : Photos ───
    with col_photo:
        st.markdown('<div class="add-section-label">Photos</div>', unsafe_allow_html=True)

        if ini is not None:
            current_photos = ini.get("photos") or ([{"url": ini["photo"], "date": ""}] if ini.get("photo") else [])
        else:
            current_photos = []

        new_photos = photo_uploader_block(f"form_{eid or 'new'}", current_photos)

        # Preview de la première photo ou placeholder
        photos_preview = new_photos or current_photos
        if photos_preview:
            st.markdown(f"""
            <img src="{photo_url(photos_preview[0])}" class="add-photo-thumb" />
            """, unsafe_allow_html=True)
            if len(photos_preview) > 1:
                st.markdown(f"""
                <div style="display:flex;gap:6px;flex-wrap:wrap;margin-top:4px;">
                  {"".join([f'<img src="{photo_url(p)}" style="width:52px;height:52px;object-fit:cover;border-radius:8px;border:2px solid {ACCENT_LIGHT};" />' for p in photos_preview[1:]])}
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="add-photo-zone">
              {svg("camera", 36, "#BDBDBD")}
              <div style="color:#BDBDBD;font-size:12px;margin-top:10px;letter-spacing:.04em;">
                AJOUTER DES PHOTOS
              </div>
              <div style="color:#D0D0D0;font-size:10px;margin-top:4px;">
                JPG, PNG — max recommandé : 5 Mo
              </div>
            </div>
            """, unsafe_allow_html=True)

        # Statut visuel (badges cliquables via selectbox ci-dessous)
        st.markdown('<div class="add-section-label" style="margin-top:20px;">Aperçu statut</div>', unsafe_allow_html=True)
        badge_colors = {
            "Disponible":    ("#E8F5E9","#2E7D32"),
            "Vendu":         ("#FFF3E0","#E65100"),
            "Malade":        ("#FFEBEE","#C62828"),
            "En quarantaine":("#E3F2FD","#1565C0"),
        }
        for s,(bg,fg) in badge_colors.items():
            st.markdown(f'<span class="add-badge" style="background:{bg};color:{fg};">{s.upper()}</span>', unsafe_allow_html=True)

    # ─── COLONNE DROITE : Formulaire ───
    with col_form:

        # Groupe Origine (Naissance ou Achat)
        st.markdown('<div class="add-section-label">Origine de l\'animal</div>', unsafe_allow_html=True)
        default_origin = ini.get("origin","Achat") if ini else "Achat"
        origin = st.radio(
            "Comment cet animal est-il arrivé dans le troupeau ? *",
            ["Achat","Naissance"],
            index=["Achat","Naissance"].index(default_origin),
            horizontal=True,
            key="af_origin",
        )
        origin_icon = svg("cart",14,"#1565C0") if origin=="Achat" else svg("birth",14,"#7B1FA2")
        origin_desc = "Animal acheté auprès d'un tiers." if origin=="Achat" else "Animal né directement dans l'exploitation."
        st.markdown(f"""
        <div style="display:flex;align-items:center;gap:8px;font-size:12px;color:#8A8A8A;margin-bottom:12px;">
          {origin_icon}<span>{origin_desc}</span>
        </div>""", unsafe_allow_html=True)

        # Groupe Identification
        st.markdown('<div class="add-section-label">Identification</div>', unsafe_allow_html=True)
        with st.container():
            f1,f2 = st.columns(2)
            with f1:
                atype = st.selectbox("Type *", ["Mouton","Vache"],
                    index=0 if not ini else ["Mouton","Vache"].index(ini["type"]),
                    key="af_type")
            with f2:
                sex = st.selectbox("Sexe *", ["Mâle","Femelle"],
                    index=0 if not ini else ["Mâle","Femelle"].index(ini["sex"]),
                    key="af_sex")

            races = st.session_state.races_mouton if atype=="Mouton" else st.session_state.races_vache
            f3,f4 = st.columns(2)
            with f3:
                dr   = races.index(ini["race"]) if ini and ini["race"] in races else 0
                race = st.selectbox("Race *", races, index=dr, key="af_race")
            with f4:
                ear_tag = st.text_input("N° de boucle *",
                    value=ini["earTag"] if ini else "", placeholder="MO-2025-001", key="af_tag")

            f5,f6 = st.columns(2)
            with f5:
                birth = st.text_input("Date de naissance *",
                    value=ini["birth"] if ini else "", placeholder="YYYY-MM-DD", key="af_birth")
            with f6:
                weight = st.number_input("Poids (kg)",
                    value=float(ini["weight"]) if ini else 0.0, min_value=0.0, key="af_weight")

            date_achat = st.text_input("Date d'achat",
                value=ini.get("date_achat","") if ini else "", placeholder="YYYY-MM-DD", key="af_date_achat")

        # Groupe Prix
        st.markdown('<div class="add-section-label">Prix</div>', unsafe_allow_html=True)
        p1,p2 = st.columns(2)
        with p1:
            buy_label = "Prix d'achat (MAD)" if origin=="Achat" else "Coût (optionnel, MAD)"
            buy_p  = st.number_input(buy_label,
                value=float(ini["buyPrice"]) if ini else 0.0, min_value=0.0, key="af_buy")
        with p2:
            sell_p = st.number_input("Prix de vente (MAD)",
                value=float(ini["sellPrice"]) if ini else 0.0, min_value=0.0, key="af_sell")

        # Bénéfice estimé live
        profit = sell_p - buy_p
        profit_c = GREEN if profit >= 0 else RED
        st.markdown(f"""
        <div style="background:#F8F8F8;border-radius:10px;padding:10px 14px;
                    display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;">
          <span style="font-size:11px;color:#8A8A8A;text-transform:uppercase;letter-spacing:.06em;">Bénéfice estimé</span>
          <span style="font-weight:700;font-size:15px;color:{profit_c}">{"+" if profit>=0 else ""}{int(profit):,} MAD</span>
        </div>
        """.replace(",", " "), unsafe_allow_html=True)

        # Groupe Statut & Notes
        st.markdown('<div class="add-section-label">Statut & Notes</div>', unsafe_allow_html=True)
        stats  = ["Disponible","Vendu","Malade","En quarantaine"]
        status = st.selectbox("Statut", stats,
            index=stats.index(ini["status"]) if ini else 0, key="af_status")
        notes  = st.text_input("Notes",
            value=ini.get("notes","") if ini else "",
            placeholder="ex: bonne laitière, vacciné…", key="af_notes")

        st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

        # Boutons d'action
        btn1, btn2 = st.columns([1,2])
        with btn1:
            if st.button("Annuler", use_container_width=True, key="cancel_form"):
                photo_key = f"photos_edit_form_{eid or 'new'}"
                if photo_key in st.session_state: del st.session_state[photo_key]
                st.session_state.show_form = False
                st.session_state.edit_id   = None
                st.rerun()
        with btn2:
            if st.button("Enregistrer l'animal", use_container_width=True, key="save_form"):
                if not ear_tag.strip() or not race or not birth.strip():
                    st.error("Remplissez les champs obligatoires (*).")
                else:
                    next_id = eid or (max([a["id"] for a in st.session_state.animals], default=0) + 1)
                    final_photos = new_photos or current_photos
                    na = {
                        "id": next_id, "type": atype, "race": race, "sex": sex,
                        "birth": birth.strip(), "earTag": ear_tag.strip(),
                        "buyPrice": buy_p, "sellPrice": sell_p,
                        "status": status, "weight": weight, "notes": notes,
                        "origin": origin, "date_achat": date_achat.strip(),
                        "photos": final_photos,
                        "photo":  photo_url(final_photos[0]) if final_photos else None,
                    }
                    if eid:
                        st.session_state.animals = [na if a["id"]==eid else a for a in st.session_state.animals]
                        alert_box("Animal modifié !", "success")
                    else:
                        st.session_state.animals.append(na)
                        alert_box(f"Animal ajouté ({origin.lower()}) !", "success")
                    sync_animals()
                    photo_key = f"photos_edit_form_{eid or 'new'}"
                    if photo_key in st.session_state: del st.session_state[photo_key]
                    st.session_state.show_form = False
                    st.session_state.edit_id   = None
                    st.rerun()



# ══════════════════════════ VENTES ════════════════════════════════════
def page_sales():
    animals=st.session_state.animals
    ta=sum(a["buyPrice"]  for a in animals)
    tv=sum(a["sellPrice"] for a in animals if a["status"]=="Vendu")
    st.markdown(f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:20px;">{svg("sales",22,ACCENT)}<span style="font-size:22px;font-weight:700">Activité des Ventes</span></div>', unsafe_allow_html=True)
    c1,c2,c3,c4=st.columns(4)
    c1.metric("Revenus ventes",fmt(tv))
    c2.metric("Coût d'achat",  fmt(ta))
    c3.metric("Marge brute",   fmt(tv-ta))
    with c4:
        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
        if st.button("Nouvelle vente",use_container_width=True):
            st.session_state.show_vente=not st.session_state.show_vente; st.rerun()

    if st.session_state.show_vente:
        dispos=[a for a in animals if a["status"]=="Disponible"]
        if not dispos: st.warning("Aucun animal disponible.")
        else:
            st.markdown(f'<div style="background:{ACCENT_DARK};border-radius:14px 14px 0 0;padding:14px 20px;color:#fff;font-weight:700;font-size:15px;display:flex;align-items:center;gap:8px;">{svg("sell",18,"#fff")}<span>Enregistrer une vente</span></div>', unsafe_allow_html=True)
            prefill=st.session_state.get("vente_prefill")
            tags=[a["earTag"] for a in dispos]
            idx=tags.index(prefill) if prefill and prefill in tags else 0
            vc1,vc2,vc3=st.columns([1.5,1.5,1])
            with vc1: v_tag=st.selectbox("N° de boucle",tags,index=idx,key="vente_tag")
            asel=next((a for a in dispos if a["earTag"]==v_tag),None)
            with vc2: v_prix=st.number_input("Prix de vente (MAD)",value=float(asel["sellPrice"]) if asel else 0.0,min_value=0.0,key="vente_prix")
            if asel:
                profit=v_prix-asel["buyPrice"]
                st.markdown(f"""
                <div style="background:{ACCENT_LIGHT};border-radius:10px;padding:12px 16px;margin:8px 0;font-size:12px;">
                  <div style="display:flex;gap:20px;flex-wrap:wrap;">
                    <span>{svg("tag",13,ACCENT)} <b>{asel["earTag"]}</b></span>
                    <span>{svg("animals",13,ACCENT)} {asel["type"]} {asel["race"]}</span>
                    <span>{svg("weight",13,ACCENT)} {asel["weight"]} kg</span>
                    <span>{svg("money",13,ACCENT)} Achat : <b>{fmt(asel["buyPrice"])}</b></span>
                    <span style="color:{GREEN if profit>=0 else RED};font-weight:700;">
                      Bénéfice : {"+" if profit>=0 else ""}{fmt(profit)}
                    </span>
                  </div>
                </div>""", unsafe_allow_html=True)
            with vc3:
                st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
                if st.button("Confirmer",use_container_width=True,key="confirm_vente"):
                    for a in st.session_state.animals:
                        if a["earTag"]==v_tag: a["status"]="Vendu"; a["sellPrice"]=v_prix; break
                    sync_animals()
                    alert_box(f"Vente : {v_tag} → {fmt(v_prix)}", "success")
                    st.session_state.show_vente=False; st.session_state.vente_prefill=None; st.rerun()
            if st.button("Annuler",key="cancel_vente"):
                st.session_state.show_vente=False; st.session_state.vente_prefill=None; st.rerun()
        st.markdown("<hr>", unsafe_allow_html=True)

    st.markdown("**Historique des ventes**")
    vendus=[a for a in animals if a["status"]=="Vendu"]
    if not vendus: st.info("Aucune vente enregistrée.")
    else:
        rows=[]
        for a in vendus:
            p=a["sellPrice"]-a["buyPrice"]
            rows.append({"N° Boucle":a["earTag"],"Type":a["type"],"Race":a["race"],
                         "Origine":a.get("origin","Achat"),"Date d'achat":a.get("date_achat",""),
                         "Prix achat":fmt(a["buyPrice"]),"Prix vente":fmt(a["sellPrice"]),
                         "Bénéfice":("+" if p>=0 else "")+fmt(p)})
        st.dataframe(pd.DataFrame(rows),use_container_width=True,hide_index=True)
    with st.expander("Voir tous les animaux"):
        rows2=[]
        for a in animals:
            p=a["sellPrice"]-a["buyPrice"]
            rows2.append({"N° Boucle":a["earTag"],"Type":a["type"],"Race":a["race"],
                          "Origine":a.get("origin","Achat"),"Date d'achat":a.get("date_achat",""),
                          "Prix achat":fmt(a["buyPrice"]),"Prix vente":fmt(a["sellPrice"]),
                          "Bénéfice":("+" if p>=0 else "")+fmt(p),"Statut":a["status"]})
        st.dataframe(pd.DataFrame(rows2),use_container_width=True,hide_index=True)

# ══════════════════════════ STOCK D'ALIMENTATION ═════════════════════
def page_stock():
    auth = st.session_state.auth
    is_obs = auth["role"] == "Observateur"
    stock = st.session_state.stock

    st.markdown(f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:20px;">{svg("cart",22,STOCK_ACCENT)}<span style="font-size:22px;font-weight:700">Stock d\'alimentation</span></div>', unsafe_allow_html=True)

    total_kg   = sum(s["quantityKg"] for s in stock)
    total_cost = sum(s["buyPrice"]   for s in stock)
    n_types    = len({s["feedType"] for s in stock})

    c1, c2, c3, c4, c5 = st.columns([1,1,1,1,1])
    c1.metric("Stock total", f"{total_kg:,.0f} kg".replace(",", " "))
    c2.metric("Valeur du stock", fmt(total_cost))
    c3.metric("Types d'aliments", n_types)
    with c4:
        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
        if not is_obs:
            if st.button("Nouvel achat", use_container_width=True, key="btn_new_stock"):
                st.session_state.show_stock_form = not st.session_state.show_stock_form
                st.session_state.show_feedtype_form = False
                st.session_state.edit_stock_id = None
                st.rerun()
    with c5:
        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
        if not is_obs:
            if st.button("Nouveau type d'aliment", use_container_width=True, key="btn_new_feedtype"):
                st.session_state.show_feedtype_form = not st.session_state.show_feedtype_form
                st.session_state.show_stock_form = False
                st.rerun()

    if st.session_state.show_feedtype_form and not is_obs:
        st.markdown(f'<div style="background:{STOCK_ACCENT};border-radius:14px 14px 0 0;padding:14px 20px;color:#fff;font-weight:700;font-size:15px;display:flex;align-items:center;gap:8px;">{svg("cart",18,"#fff")}<span>Ajouter un type d\'aliment</span></div>', unsafe_allow_html=True)
        ftc1, ftc2 = st.columns([3,1])
        with ftc1:
            new_feed_type = st.text_input("Nom du type", placeholder="ex: Tourteau de soja", key="new_feedtype_input", label_visibility="collapsed")
        with ftc2:
            if st.button("Ajouter", key="btn_add_feedtype", use_container_width=True):
                name = new_feed_type.strip()
                if name:
                    if name not in st.session_state.feed_types:
                        st.session_state.feed_types.append(name)
                        try:
                            db.add_feed_type(name)
                            alert_box(f"Type « {name} » ajouté !", "success")
                        except Exception as e:
                            st.error(f"Erreur de synchronisation : {e}")
                        st.session_state.show_feedtype_form = False
                        st.rerun()
                    else:
                        st.warning("Ce type existe déjà.")
                else:
                    st.error("Entrez un nom.")
        if st.button("Fermer", key="close_feedtype"):
            st.session_state.show_feedtype_form = False
            st.rerun()
        st.markdown("<hr>", unsafe_allow_html=True)

    eid_stock = st.session_state.edit_stock_id
    ini_stock = next((s for s in stock if s["id"]==eid_stock), None) if eid_stock else None
    is_edit_stock = ini_stock is not None

    if (st.session_state.show_stock_form or is_edit_stock) and not is_obs:
        header_label = "Modifier l'achat" if is_edit_stock else "Enregistrer un achat d'alimentation"
        st.markdown(f"""<div style="background:{STOCK_ACCENT};border-radius:14px 14px 0 0;padding:14px 20px;
                    color:#fff;font-weight:700;font-size:15px;display:flex;align-items:center;gap:8px;">
                    {svg("cart",18,"#fff")}<span>{header_label}</span></div>""",
                    unsafe_allow_html=True)

        default_date = datetime.strptime(ini_stock["date_achat"], "%Y-%m-%d").date() \
            if is_edit_stock and ini_stock.get("date_achat") else datetime.now().date()
        feed_types_list = st.session_state.feed_types
        default_type  = ini_stock["feedType"] if is_edit_stock else feed_types_list[0]
        default_qty   = float(ini_stock["quantity"]) if is_edit_stock else 0.0
        default_unit  = ini_stock.get("unit","kg") if is_edit_stock else list(UNIT_TO_KG.keys())[0]
        default_price = float(ini_stock["buyPrice"]) if is_edit_stock else 0.0
        default_notes = ini_stock.get("notes","") if is_edit_stock else ""

        with st.form("stock_form", clear_on_submit=not is_edit_stock):
            fc1, fc2 = st.columns(2)
            with fc1:
                f_date = st.date_input("Date d'achat", value=default_date)
                f_type = st.selectbox("Type d'aliment", feed_types_list,
                                       index=feed_types_list.index(default_type) if default_type in feed_types_list else 0)
            with fc2:
                f_qty  = st.number_input("Quantité", min_value=0.0, step=1.0, value=default_qty)
                unit_keys = list(UNIT_TO_KG.keys())
                f_unit = st.selectbox("Unité", unit_keys,
                                       index=unit_keys.index(default_unit) if default_unit in unit_keys else 0)
            fc3, fc4 = st.columns(2)
            with fc3:
                f_price = st.number_input("Prix d'achat (MAD)", min_value=0.0, step=1.0, value=default_price)
            with fc4:
                f_notes = st.text_input("Notes (fournisseur, remarque...)", value=default_notes)

            bc1, bc2 = st.columns([1,2]) if is_edit_stock else (None, None)
            if is_edit_stock:
                with bc1:
                    cancel = st.form_submit_button("Annuler", use_container_width=True)
                with bc2:
                    submitted = st.form_submit_button("Enregistrer les modifications", use_container_width=True)
            else:
                cancel = False
                submitted = st.form_submit_button("Enregistrer l'achat", use_container_width=True)

            if cancel:
                st.session_state.edit_stock_id = None
                st.session_state.show_stock_form = False
                st.rerun()

            if submitted:
                if f_qty <= 0:
                    alert_box("Indique une quantité valide.", "error")
                else:
                    if is_edit_stock:
                        updated = {
                            "id":         ini_stock["id"],
                            "date_achat": str(f_date),
                            "feedType":   f_type,
                            "quantity":   f_qty,
                            "unit":       f_unit,
                            "quantityKg": stock_to_kg(f_qty, f_unit),
                            "buyPrice":   f_price,
                            "notes":      f_notes,
                        }
                        st.session_state.stock = [updated if x["id"]==ini_stock["id"] else x
                                                   for x in st.session_state.stock]
                        sync_stock()
                        alert_box("Achat modifié !", "success")
                        st.session_state.edit_stock_id = None
                        st.session_state.show_stock_form = False
                        st.rerun()
                    else:
                        new_id = (max([s["id"] for s in stock], default=0) + 1)
                        entry = {
                            "id":         new_id,
                            "date_achat": str(f_date),
                            "feedType":   f_type,
                            "quantity":   f_qty,
                            "unit":       f_unit,
                            "quantityKg": stock_to_kg(f_qty, f_unit),
                            "buyPrice":   f_price,
                            "notes":      f_notes,
                        }
                        st.session_state.stock.append(entry)
                        sync_stock()
                        alert_box(f"Achat enregistré : {f_qty:g} {f_unit} de {f_type}", "success")
                        st.session_state.show_stock_form = False
                        st.rerun()
        st.markdown("<hr>", unsafe_allow_html=True)

    st.markdown("**Historique des achats**")
    if not stock:
        st.info("Aucun achat d'alimentation enregistré.")
        return

    filt_c1, filt_c2 = st.columns([2, 1])
    with filt_c1:
        filter_type = st.selectbox("Filtrer par type", ["Tous"] + st.session_state.feed_types, key="stock_filter_type")
    with filt_c2:
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)

    stock_sorted = sorted(stock, key=lambda s: s.get("date_achat",""), reverse=True)
    if filter_type != "Tous":
        stock_sorted = [s for s in stock_sorted if s["feedType"] == filter_type]

    if is_obs:
        rows = [{
            "Date d'achat": s["date_achat"],
            "Type": s["feedType"],
            "Quantité": f'{s["quantity"]:g} {s["unit"]}',
            "Équivalent kg": f'{s["quantityKg"]:,.0f} kg'.replace(",", " "),
            "Prix d'achat": fmt(s["buyPrice"]),
            "Notes": s.get("notes",""),
        } for s in stock_sorted]
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        st.caption("Modifie directement une cellule, puis clique sur *Enregistrer les modifications du tableau*.")
        edit_rows = [{
            "id":            s["id"],
            "Date d'achat":  pd.to_datetime(s.get("date_achat",""), errors="coerce"),
            "Type":          s["feedType"],
            "Quantité":      float(s["quantity"]),
            "Unité":         s.get("unit","kg"),
            "Prix d'achat (MAD)": float(s["buyPrice"]),
            "Notes":         s.get("notes",""),
        } for s in stock_sorted]
        edit_df = pd.DataFrame(edit_rows).set_index("id")

        edited_df = st.data_editor(
            edit_df,
            use_container_width=True,
            num_rows="fixed",
            key="stock_table_editor",
            column_config={
                "Date d'achat": st.column_config.DateColumn("Date d'achat", format="YYYY-MM-DD"),
                "Type":  st.column_config.SelectboxColumn("Type", options=st.session_state.feed_types),
                "Quantité": st.column_config.NumberColumn("Quantité", min_value=0.0, step=1.0),
                "Unité": st.column_config.SelectboxColumn("Unité", options=list(UNIT_TO_KG.keys())),
                "Prix d'achat (MAD)": st.column_config.NumberColumn("Prix d'achat (MAD)", min_value=0.0, step=1.0),
                "Notes": st.column_config.TextColumn("Notes"),
            },
        )

        if st.button("Enregistrer les modifications du tableau", key="save_stock_table"):
            shown_ids = set(edited_df.index.tolist())
            new_entries = []
            for sid, row in edited_df.iterrows():
                qty  = float(row["Quantité"])
                unit = row["Unité"]
                d = row["Date d'achat"]
                date_str = d.strftime("%Y-%m-%d") if pd.notna(d) else ""
                new_entries.append({
                    "id":         int(sid),
                    "date_achat": date_str,
                    "feedType":   row["Type"],
                    "quantity":   qty,
                    "unit":       unit,
                    "quantityKg": stock_to_kg(qty, unit),
                    "buyPrice":   float(row["Prix d'achat (MAD)"]),
                    "notes":      row.get("Notes","") or "",
                })
            untouched = [s for s in st.session_state.stock if s["id"] not in shown_ids]
            st.session_state.stock = new_entries + untouched
            sync_stock()
            alert_box("Tableau mis à jour !", "success")
            st.rerun()


    st.markdown("**Répartition du stock par type d'aliment**")
    by_type = {}
    for s in stock:
        by_type[s["feedType"]] = by_type.get(s["feedType"], 0) + s["quantityKg"]
    if by_type:
        fig = go.Figure(go.Bar(
            x=list(by_type.values()), y=list(by_type.keys()),
            orientation="h", marker_color=STOCK_ACCENT))
        fig.update_layout(margin=dict(t=10,b=10,l=10,r=10), height=max(180, 36*len(by_type)),
            plot_bgcolor="#fff", paper_bgcolor="#fff",
            xaxis=dict(showgrid=False, title="kg"), yaxis=dict(showgrid=False))
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    if not is_obs:
        with st.expander("Modifier / Supprimer un achat"):
            for s in stock_sorted:
                dc1, dc2, dc3 = st.columns([3, 1, 1])
                with dc1:
                    st.markdown(f"{s['date_achat']} — **{s['feedType']}** — {s['quantity']:g} {s['unit']} — {fmt(s['buyPrice'])}")
                with dc2:
                    if st.button("Modifier", key=f"edit_stock_{s['id']}", use_container_width=True):
                        st.session_state.edit_stock_id = s["id"]
                        st.session_state.show_stock_form = True
                        st.rerun()
                with dc3:
                    if st.button("Supprimer", key=f"del_stock_{s['id']}", use_container_width=True):
                        st.session_state.stock = [x for x in st.session_state.stock if x["id"] != s["id"]]
                        sync_stock()
                        alert_box("Achat supprimé.", "success")
                        st.rerun()

# ══════════════════════════ DÉPENSES ═════════════════════════════════
def page_expenses():
    auth = st.session_state.auth
    is_obs = auth["role"] == "Observateur"
    expenses = st.session_state.expenses

    st.markdown(f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:20px;">{svg("receipt",22,EXPENSE_ACCENT)}<span style="font-size:22px;font-weight:700">Suivi des dépenses</span></div>', unsafe_allow_html=True)

    today = date.today()
    total_all   = sum(e["montant"] for e in expenses)
    total_month = sum(e["montant"] for e in expenses if str(e.get("date","")).startswith(today.strftime("%Y-%m")))
    total_year  = sum(e["montant"] for e in expenses if str(e.get("date","")).startswith(today.strftime("%Y")))
    n_cats      = len({e["categorie"] for e in expenses})

    c1, c2, c3, c4, c5 = st.columns([1,1,1,1,1])
    c1.metric("Total dépenses", fmt(total_all))
    c2.metric("Ce mois-ci", fmt(total_month))
    c3.metric("Cette année", fmt(total_year))
    c4.metric("Catégories utilisées", n_cats)
    with c5:
        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
        if not is_obs:
            if st.button("Nouvelle dépense", use_container_width=True, key="btn_new_expense"):
                st.session_state.show_expense_form = not st.session_state.show_expense_form
                st.session_state.edit_expense_id = None
                st.rerun()

    eid_exp = st.session_state.edit_expense_id
    ini_exp = next((e for e in expenses if e["id"]==eid_exp), None) if eid_exp else None
    is_edit_exp = ini_exp is not None

    if (st.session_state.show_expense_form or is_edit_exp) and not is_obs:
        header_label = "Modifier la dépense" if is_edit_exp else "Enregistrer une dépense"
        st.markdown(f"""<div style="background:{EXPENSE_ACCENT};border-radius:14px 14px 0 0;padding:14px 20px;
                    color:#fff;font-weight:700;font-size:15px;display:flex;align-items:center;gap:8px;">
                    {svg("receipt",18,"#fff")}<span>{header_label}</span></div>""",
                    unsafe_allow_html=True)

        default_date  = datetime.strptime(ini_exp["date"], "%Y-%m-%d").date() \
            if is_edit_exp and ini_exp.get("date") else datetime.now().date()
        default_cat   = ini_exp["categorie"] if is_edit_exp else EXPENSE_CATEGORIES[0]
        default_desc  = ini_exp.get("description","") if is_edit_exp else ""
        default_montant = float(ini_exp["montant"]) if is_edit_exp else 0.0
        default_paye  = ini_exp.get("payePar","") if is_edit_exp else ""
        default_notes = ini_exp.get("notes","") if is_edit_exp else ""

        with st.form("expense_form", clear_on_submit=not is_edit_exp):
            fc1, fc2 = st.columns(2)
            with fc1:
                f_date = st.date_input("Date de la dépense", value=default_date)
                f_cat  = st.selectbox("Catégorie", EXPENSE_CATEGORIES,
                                       index=EXPENSE_CATEGORIES.index(default_cat) if default_cat in EXPENSE_CATEGORIES else 0)
            with fc2:
                f_montant = st.number_input("Montant (MAD)", min_value=0.0, step=1.0, value=default_montant)
                f_paye    = st.text_input("Payé par", value=default_paye, placeholder="ex: Ahmed")
            f_desc  = st.text_input("Description", value=default_desc, placeholder="ex: Vaccination du troupeau")
            f_notes = st.text_input("Notes (optionnel)", value=default_notes)

            bc1, bc2 = st.columns([1,2]) if is_edit_exp else (None, None)
            if is_edit_exp:
                with bc1:
                    cancel = st.form_submit_button("Annuler", use_container_width=True)
                with bc2:
                    submitted = st.form_submit_button("Enregistrer les modifications", use_container_width=True)
            else:
                cancel = False
                submitted = st.form_submit_button("Enregistrer la dépense", use_container_width=True)

            if cancel:
                st.session_state.edit_expense_id = None
                st.session_state.show_expense_form = False
                st.rerun()

            if submitted:
                if f_montant <= 0:
                    alert_box("Indique un montant valide.", "error")
                elif not f_desc.strip():
                    alert_box("Ajoute une description.", "error")
                else:
                    if is_edit_exp:
                        updated = {
                            "id": ini_exp["id"], "date": str(f_date), "categorie": f_cat,
                            "description": f_desc.strip(), "montant": f_montant,
                            "payePar": f_paye.strip(), "notes": f_notes.strip(),
                        }
                        st.session_state.expenses = [updated if x["id"]==ini_exp["id"] else x
                                                      for x in st.session_state.expenses]
                        sync_expenses()
                        alert_box("Dépense modifiée !", "success")
                        st.session_state.edit_expense_id = None
                        st.session_state.show_expense_form = False
                        st.rerun()
                    else:
                        new_id = (max([e["id"] for e in expenses], default=0) + 1)
                        entry = {
                            "id": new_id, "date": str(f_date), "categorie": f_cat,
                            "description": f_desc.strip(), "montant": f_montant,
                            "payePar": f_paye.strip(), "notes": f_notes.strip(),
                        }
                        st.session_state.expenses.append(entry)
                        sync_expenses()
                        alert_box(f"Dépense enregistrée : {fmt(f_montant)} — {f_cat}", "success")
                        st.session_state.show_expense_form = False
                        st.rerun()
        st.markdown("<hr>", unsafe_allow_html=True)

    st.markdown("**Historique des dépenses**")
    if not expenses:
        st.info("Aucune dépense enregistrée pour le moment.")
        return

    filt_c1, filt_c2 = st.columns([2, 1])
    with filt_c1:
        filter_cat = st.selectbox("Filtrer par catégorie", ["Toutes"] + EXPENSE_CATEGORIES, key="expense_filter_cat")

    expenses_sorted = sorted(expenses, key=lambda e: e.get("date",""), reverse=True)
    if filter_cat != "Toutes":
        expenses_sorted = [e for e in expenses_sorted if e["categorie"] == filter_cat]

    if is_obs:
        rows = [{
            "Date": e["date"], "Catégorie": e["categorie"], "Description": e["description"],
            "Montant": fmt(e["montant"]), "Payé par": e.get("payePar",""), "Notes": e.get("notes",""),
        } for e in expenses_sorted]
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        st.caption("Modifie directement une cellule, puis clique sur *Enregistrer les modifications du tableau*.")
        edit_rows = [{
            "id":          e["id"],
            "Date":        pd.to_datetime(e.get("date",""), errors="coerce"),
            "Catégorie":   e["categorie"],
            "Description": e["description"],
            "Montant (MAD)": float(e["montant"]),
            "Payé par":    e.get("payePar",""),
            "Notes":       e.get("notes",""),
        } for e in expenses_sorted]
        edit_df = pd.DataFrame(edit_rows).set_index("id")

        edited_df = st.data_editor(
            edit_df,
            use_container_width=True,
            num_rows="fixed",
            key="expenses_table_editor",
            column_config={
                "Date": st.column_config.DateColumn("Date", format="YYYY-MM-DD"),
                "Catégorie": st.column_config.SelectboxColumn("Catégorie", options=EXPENSE_CATEGORIES),
                "Description": st.column_config.TextColumn("Description"),
                "Montant (MAD)": st.column_config.NumberColumn("Montant (MAD)", min_value=0.0, step=1.0),
                "Payé par": st.column_config.TextColumn("Payé par"),
                "Notes": st.column_config.TextColumn("Notes"),
            },
        )

        if st.button("Enregistrer les modifications du tableau", key="save_expenses_table"):
            shown_ids = set(edited_df.index.tolist())
            new_entries = []
            for eid_, row in edited_df.iterrows():
                d = row["Date"]
                date_str = d.strftime("%Y-%m-%d") if pd.notna(d) else ""
                new_entries.append({
                    "id":          int(eid_),
                    "date":        date_str,
                    "categorie":   row["Catégorie"],
                    "description": row["Description"],
                    "montant":     float(row["Montant (MAD)"]),
                    "payePar":     row.get("Payé par","") or "",
                    "notes":       row.get("Notes","") or "",
                })
            untouched = [e for e in st.session_state.expenses if e["id"] not in shown_ids]
            st.session_state.expenses = new_entries + untouched
            sync_expenses()
            alert_box("Tableau mis à jour !", "success")
            st.rerun()

    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
    dc1, dc2 = st.columns(2)
    with dc1:
        st.markdown("**Répartition par catégorie**")
        by_cat = {}
        for e in expenses:
            by_cat[e["categorie"]] = by_cat.get(e["categorie"], 0) + e["montant"]
        if by_cat:
            fig = go.Figure(go.Pie(labels=list(by_cat.keys()), values=list(by_cat.values()), hole=0.55,
                                    marker_colors=[EXPENSE_ACCENT, "#C39BD3","#D2B4DE","#E8DAEF","#B983C7","#A569BD"]))
            fig.update_layout(margin=dict(t=10,b=10,l=10,r=10), height=260, showlegend=True,
                legend=dict(orientation="v", x=1, y=0.5, font=dict(size=10)))
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    with dc2:
        st.markdown("**Dépenses par mois**")
        by_month = {}
        for e in expenses:
            m = str(e.get("date",""))[:7]
            if m:
                by_month[m] = by_month.get(m, 0) + e["montant"]
        if by_month:
            months_sorted = sorted(by_month.keys())
            fig2 = go.Figure(go.Bar(x=months_sorted, y=[by_month[m] for m in months_sorted],
                                     marker_color=EXPENSE_ACCENT))
            fig2.update_layout(margin=dict(t=10,b=10,l=10,r=10), height=260,
                plot_bgcolor="#fff", paper_bgcolor="#fff",
                yaxis=dict(showgrid=False, title="MAD"), xaxis=dict(showgrid=False))
            st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

    if not is_obs:
        with st.expander("Modifier / Supprimer une dépense"):
            for e in expenses_sorted:
                ec1, ec2, ec3 = st.columns([3, 1, 1])
                with ec1:
                    st.markdown(f"{e['date']} — **{e['categorie']}** — {e['description']} — {fmt(e['montant'])}")
                with ec2:
                    if st.button("Modifier", key=f"edit_expense_{e['id']}", use_container_width=True):
                        st.session_state.edit_expense_id = e["id"]
                        st.session_state.show_expense_form = True
                        st.rerun()
                with ec3:
                    if st.button("Supprimer", key=f"del_expense_{e['id']}", use_container_width=True):
                        st.session_state.expenses = [x for x in st.session_state.expenses if x["id"] != e["id"]]
                        sync_expenses()
                        alert_box("Dépense supprimée.", "success")
                        st.rerun()

# ══════════════════════════ STATISTIQUES ═════════════════════════════
def page_stats():
    animals=st.session_state.animals
    st.markdown(f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:20px;">{svg("stats",22,ACCENT)}<span style="font-size:22px;font-weight:700">Statistiques</span></div>', unsafe_allow_html=True)
    col1,col2,col3=st.columns(3)
    charts=[
        ("Par type",  ["Moutons","Vaches"],    [sum(1 for a in animals if a["type"]=="Mouton"),      sum(1 for a in animals if a["type"]=="Vache")]),
        ("Par sexe",  ["Mâles","Femelles"],     [sum(1 for a in animals if a["sex"]=="Mâle"),         sum(1 for a in animals if a["sex"]=="Femelle")]),
        ("Par statut",["Disponibles","Vendus"], [sum(1 for a in animals if a["status"]=="Disponible"),sum(1 for a in animals if a["status"]=="Vendu")]),
    ]
    for col,(title,labels,values) in zip([col1,col2,col3],charts):
        with col:
            st.markdown(f"**{title}**")
            fig=go.Figure(go.Bar(x=labels,y=values,marker_color=ACCENT,width=0.5))
            fig.update_layout(margin=dict(t=10,b=10,l=10,r=10),height=180,
                plot_bgcolor="#fff",paper_bgcolor="#fff",
                yaxis=dict(showgrid=False),xaxis=dict(showgrid=False))
            st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})
    st.markdown("**Origine du troupeau**")
    n_naissance = sum(1 for a in animals if a.get("origin","Achat")=="Naissance")
    n_achat     = sum(1 for a in animals if a.get("origin","Achat")=="Achat")
    oc1, oc2 = st.columns(2)
    with oc1:
        fig3 = go.Figure(go.Pie(labels=["Naissance","Achat"], values=[n_naissance,n_achat], hole=0.6,
                                marker_colors=["#7B1FA2","#1565C0"], textinfo="value"))
        fig3.update_layout(margin=dict(t=10,b=10,l=10,r=10), height=180, showlegend=True,
            legend=dict(orientation="v",x=1,y=0.5,font=dict(size=11)))
        st.plotly_chart(fig3,use_container_width=True,config={"displayModeBar":False})
    with oc2:
        st.markdown(f"""
        <div style="display:flex;flex-direction:column;gap:10px;padding-top:16px;">
          <div style="display:flex;align-items:center;gap:8px;">{svg("birth",16,"#7B1FA2")}<span style="font-size:13px;">Nés dans l'exploitation : <b>{n_naissance}</b></span></div>
          <div style="display:flex;align-items:center;gap:8px;">{svg("cart",16,"#1565C0")}<span style="font-size:13px;">Achetés : <b>{n_achat}</b></span></div>
        </div>""", unsafe_allow_html=True)
    st.markdown("**Distribution par race**")
    rc={}
    for a in animals: rc[a["race"]]=rc.get(a["race"],0)+1
    tags_html="".join([f'<span style="background:{ACCENT_LIGHT};border-radius:10px;padding:8px 14px;display:inline-flex;gap:8px;align-items:center;margin:4px;"><b style="color:{ACCENT}">{cnt}</b><span style="font-size:12px">{race}</span></span>' for race,cnt in rc.items()])
    st.markdown(f'<div style="display:flex;flex-wrap:wrap;">{tags_html}</div>', unsafe_allow_html=True)

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    st.markdown("**Dépenses par catégorie**")
    expenses = st.session_state.get("expenses", [])
    by_cat = {}
    for e in expenses:
        by_cat[e["categorie"]] = by_cat.get(e["categorie"], 0) + e["montant"]
    if by_cat:
        fig4 = go.Figure(go.Bar(x=list(by_cat.values()), y=list(by_cat.keys()), orientation="h",
                                 marker_color=EXPENSE_ACCENT))
        fig4.update_layout(margin=dict(t=10,b=10,l=10,r=10), height=max(180, 34*len(by_cat)),
            plot_bgcolor="#fff", paper_bgcolor="#fff",
            xaxis=dict(showgrid=False, title="MAD"), yaxis=dict(showgrid=False))
        st.plotly_chart(fig4, use_container_width=True, config={"displayModeBar": False})
    else:
        st.caption("Aucune dépense enregistrée.")

# ══════════════════════════ UTILISATEURS ═════════════════════════════
def page_users():
    auth     = st.session_state.auth
    is_admin = auth["role"].strip() in ("Administrateur", "Admin", "Administrator")

    st.markdown(f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:20px;">'
                f'{svg("users",22,ACCENT)}'
                f'<span style="font-size:22px;font-weight:700">Gestion des Utilisateurs</span></div>',
                unsafe_allow_html=True)

    with st.spinner("Chargement des utilisateurs…"):
        users = db.load_users()
    st.session_state.users = users

    for u in users:
        u["statut"] = u.get("statut","").strip() or "Actif"
        u["role"]   = u.get("role","").strip() or "Observateur"

    en_attente = [u for u in users if u["statut"] == "En attente"]
    actifs     = [u for u in users if u["statut"] == "Actif"]
    refuses    = [u for u in users if u["statut"] == "Refusé"]

    with st.expander("Debug — statuts chargés"):
        for u in users:
            st.write(f"**{u['name']}** — statut: `{u['statut']}` — role: `{u['role']}`")
        st.write(f"is_admin = {is_admin}, en_attente = {len(en_attente)}")

    mc1,mc2,mc3 = st.columns(3)
    mc1.metric("Utilisateurs actifs", len(actifs))
    mc2.metric("En attente", len(en_attente), delta=f"+{len(en_attente)} à valider" if en_attente else None)
    mc3.metric("Refusés", len(refuses))

    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

    if is_admin:
        plaintext_count = sum(1 for u in users if u.get("password") and "$" not in u["password"])
        if plaintext_count:
            wic, wbc = st.columns([0.06, 0.94])
            with wic:
                st.markdown(f"<div style='padding-top:8px;'>{svg('lock',16,'#C62828')}</div>", unsafe_allow_html=True)
            with wbc:
                st.markdown(f"<div style='font-size:12px;color:#C62828;padding-top:8px;'>{plaintext_count} mot(s) de passe encore stocké(s) en clair.</div>", unsafe_allow_html=True)
            if st.button("Sécuriser les mots de passe en clair", key="migrate_pwd_btn"):
                with st.spinner("Chiffrement des mots de passe…"):
                    n = db.migrate_plaintext_passwords()
                st.session_state.users = db.load_users()
                alert_box(f"{n} mot(s) de passe chiffré(s) avec succès.", "success")
                st.rerun()
            st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

    if is_admin and en_attente:
        st.markdown(f"""
        <div style="background:#FFF8E1;border:1.5px solid #F59E0B;border-radius:14px;
                    padding:14px 18px;margin-bottom:16px;display:flex;align-items:flex-start;gap:10px;">
          <div style="padding-top:2px;">{svg("hourglass",18,"#92400E")}</div>
          <div>
            <div style="font-weight:700;font-size:14px;color:#92400E;margin-bottom:4px;">
              {len(en_attente)} demande(s) en attente de validation
            </div>
            <div style="font-size:12px;color:#78350F;">Acceptez ou refusez les nouvelles inscriptions ci-dessous.</div>
          </div>
        </div>""", unsafe_allow_html=True)

        for u in en_attente:
            with st.container():
                st.markdown(f"""
                <div style="background:#fff;border:1px solid #F59E0B;border-radius:14px;
                            padding:16px 20px;margin-bottom:8px;">
                  <div style="display:flex;align-items:center;gap:12px;">
                    <div style="width:42px;height:42px;border-radius:50%;background:#FFF8E1;
                                display:flex;align-items:center;justify-content:center;
                                font-weight:700;color:#92400E;font-size:16px;flex-shrink:0;">
                      {u['name'][0].upper() if u['name'] else "?"}
                    </div>
                    <div style="flex:1">
                      <div style="font-weight:600;font-size:14px">{u['name']}</div>
                      <div style="font-size:12px;color:#8A8A8A">{u['email']} · Inscrit le {u.get('date_inscription','')}</div>
                    </div>
                    <span style="background:#FFF8E1;color:#92400E;border-radius:20px;
                                 padding:3px 10px;font-size:11px;font-weight:600;">En attente</span>
                  </div>
                </div>""", unsafe_allow_html=True)

                ac1,ac2,ac3,ac4 = st.columns([2,1,1,1])
                with ac1:
                    role_sel = st.selectbox(
                        "Rôle à attribuer",
                        ["Observateur","Gestionnaire","Administrateur"],
                        key=f"role_pending_{u['email']}"
                    )
                with ac2:
                    if st.button("Accepter", key=f"accept_{u['email']}", use_container_width=True):
                        for x in users:
                            if x["email"] == u["email"]:
                                x["statut"] = "Actif"
                                x["role"]   = role_sel
                                break
                        db.save_all_users(users)
                        st.session_state.users = users
                        alert_box(f"{u['name']} accepté en tant que {role_sel}", "success")
                        st.rerun()
                with ac3:
                    if st.button("Refuser", key=f"refuse_{u['email']}", use_container_width=True):
                        for x in users:
                            if x["email"] == u["email"]:
                                x["statut"] = "Refusé"
                                break
                        db.save_all_users(users)
                        st.session_state.users = users
                        alert_box(f"{u['name']} refusé.", "warning")
                        st.rerun()
                with ac4:
                    if st.button("Supprimer", key=f"del_pending_{u['email']}", use_container_width=True):
                        users = [x for x in users if x["email"] != u["email"]]
                        db.save_all_users(users)
                        st.session_state.users = users
                        st.rerun()

        st.markdown("<hr>", unsafe_allow_html=True)

    st.markdown(f'<div style="display:flex;align-items:center;gap:8px;font-weight:700;">{svg("users",16,ACCENT)}<span>Utilisateurs actifs</span></div>', unsafe_allow_html=True)
    role_colors = {
        "Administrateur": ("badge-dispo",  "#2E7D32"),
        "Gestionnaire":   ("badge-quaran", "#1565C0"),
        "Observateur":    ("badge-vendu",  "#E65100"),
    }

    for u in actifs:
        bc, _ = role_colors.get(u["role"], ("badge-dispo","#2E7D32"))
        is_me = u["email"] == auth.get("email","") or u["name"] == auth["name"]

        st.markdown(f"""
        <div style="background:#fff;border:1px solid #EEE;border-radius:14px;
                    padding:14px 20px;margin-bottom:6px;display:flex;align-items:center;gap:14px;">
          <div style="width:40px;height:40px;border-radius:50%;background:{ACCENT_LIGHT};
                      display:flex;align-items:center;justify-content:center;
                      font-weight:700;color:{ACCENT};font-size:15px;flex-shrink:0;">
            {u['name'][0].upper() if u['name'] else "?"}
          </div>
          <div style="flex:1">
            <div style="font-weight:600;font-size:14px">{u['name']} {'<span style="font-size:10px;color:#8A8A8A">(vous)</span>' if is_me else ""}</div>
            <div style="font-size:12px;color:#8A8A8A">{u['email']}</div>
          </div>
          <span class="{bc}">{u['role']}</span>
        </div>""", unsafe_allow_html=True)

        if is_admin:
            ec1,ec2,ec3 = st.columns([2,1,1])
            with ec1:
                ROLES = ["Observateur","Gestionnaire","Administrateur"]
                role_idx = ROLES.index(u["role"]) if u["role"] in ROLES else 0
                new_role = st.selectbox(
                    "Changer le rôle",
                    ROLES,
                    index=role_idx,
                    key=f"role_{u['email']}"
                )
            with ec2:
                if st.button("Sauvegarder", key=f"saverole_{u['email']}", use_container_width=True):
                    for x in users:
                        if x["email"] == u["email"]:
                            x["role"] = new_role; break
                    db.save_all_users(users)
                    st.session_state.users = users
                    alert_box(f"Rôle mis à jour → {new_role}", "success")
                    st.rerun()
            with ec3:
                if not is_me:
                    if st.button("Supprimer", key=f"del_{u['email']}", use_container_width=True):
                        users = [x for x in users if x["email"] != u["email"]]
                        db.save_all_users(users)
                        st.session_state.users = users
                        st.rerun()

        st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

    if is_admin and refuses:
        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
        with st.expander(f"Comptes refusés ({len(refuses)})"):
            for u in refuses:
                rc1,rc2,rc3 = st.columns([3,1,1])
                with rc1:
                    st.markdown(f"""
                    <div style="display:flex;align-items:center;gap:10px;padding:6px 0;">
                      <div style="width:32px;height:32px;border-radius:50%;background:#FFEBEE;
                                  display:flex;align-items:center;justify-content:center;
                                  font-weight:700;color:#C62828;font-size:13px;">
                        {u['name'][0].upper() if u['name'] else "?"}
                      </div>
                      <div>
                        <div style="font-size:13px;font-weight:600">{u['name']}</div>
                        <div style="font-size:11px;color:#8A8A8A">{u['email']}</div>
                      </div>
                    </div>""", unsafe_allow_html=True)
                with rc2:
                    if st.button("Réactiver", key=f"reactivate_{u['email']}", use_container_width=True):
                        for x in users:
                            if x["email"] == u["email"]:
                                x["statut"] = "Actif"; break
                        db.save_all_users(users)
                        st.session_state.users = users
                        alert_box(f"{u['name']} réactivé.", "success")
                        st.rerun()
                with rc3:
                    if st.button("Supprimer", key=f"del_refused_{u['email']}", use_container_width=True):
                        users = [x for x in users if x["email"] != u["email"]]
                        db.save_all_users(users)
                        st.session_state.users = users
                        st.rerun()


# ══════════════════════════ PARAMÈTRES ═══════════════════════════════
def page_settings():
    auth=st.session_state.auth; is_obs=auth["role"]=="Observateur"
    st.markdown(f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:20px;">{svg("settings",22,ACCENT)}<span style="font-size:22px;font-weight:700">Paramètres</span></div>', unsafe_allow_html=True)
    for label,default in [("Responsable",auth["name"])]:
        st.text_input(label,value=default,disabled=is_obs)
    if not is_obs:
        if st.button("Enregistrer"): alert_box("Paramètres enregistrés.", "success")

# ══════════════════════════ MAIN ══════════════════════════════════════
def main():
    if not st.session_state.auth:
        login_page(); return
    sidebar_nav()
    auth=st.session_state.auth
    ct,cb=st.columns([4,1])
    with ct:
        st.markdown(f"### Bienvenue, {auth['name']} !")
        st.caption("Gérez votre troupeau avec des données en temps réel")
    with cb:
        if auth["role"]=="Observateur":
            st.markdown(f'<div style="background:#E3F0FF;color:#1565C0;border-radius:20px;padding:5px 14px;font-size:11px;font-weight:600;text-align:center;margin-top:10px;display:flex;align-items:center;gap:6px;justify-content:center;">{svg("eye",13,"#1565C0")}<span>Mode lecture</span></div>', unsafe_allow_html=True)
    st.markdown("<hr style='border:none;border-top:1px solid #EEE;margin:4px 0 16px'>", unsafe_allow_html=True)
    page=st.session_state.page
    if   page=="Dashboard":    page_dashboard()
    elif page=="Animaux":      page_animals()
    elif page=="Catalogue":    page_catalogue()
    elif page=="Ventes":       page_sales()
    elif page=="Stock":        page_stock()
    elif page=="Depenses":     page_expenses()
    elif page=="Statistiques": page_stats()
    elif page=="Utilisateurs": page_users()
    elif page=="Paramètres":   page_settings()
    elif page=="FicheAnimal":  page_animal_detail(st.session_state.modal_animal_id)

if __name__=="__main__":
    main()
