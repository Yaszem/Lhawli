"""
debug_users.py — Affiche le contenu brut de l'onglet Users
Usage : streamlit run debug_users.py
"""
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

st.set_page_config(page_title="Debug Users", page_icon="🔍")
st.title("🔍 Debug — Onglet Users brut")

if st.button("Charger", type="primary"):
    try:
        creds = Credentials.from_service_account_info(
            dict(st.secrets["gcp_service_account"]), scopes=SCOPES)
        client = gspread.authorize(creds)
        sh = client.open_by_key(st.secrets["gsheet"]["sheet_id"])
        ws = sh.worksheet("Users")

        all_vals = ws.get_all_values()
        st.subheader(f"{len(all_vals)} lignes trouvées (dont en-tête)")

        if all_vals:
            st.markdown("**Ligne 1 (en-têtes) :**")
            st.code(str(all_vals[0]))
            st.markdown("**Toutes les lignes :**")
            for i, row in enumerate(all_vals):
                st.code(f"Ligne {i+1}: {row}")
        else:
            st.error("Sheet vide !")

    except Exception as e:
        st.error(f"Erreur : {e}")
