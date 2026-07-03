"""
migrate_users.py — À lancer UNE FOIS pour ajouter les colonnes
statut et date_inscription dans l'onglet Users du Google Sheet.

Usage :
    streamlit run migrate_users.py
"""
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

st.set_page_config(page_title="Migration Users", page_icon="🔧")
st.title("🔧 Migration — Onglet Users")
st.write("Ajoute les colonnes `statut` et `date_inscription` et met tous les utilisateurs existants en `Actif`.")

if st.button("🚀 Lancer la migration", type="primary"):
    with st.spinner("En cours…"):
        try:
            creds = Credentials.from_service_account_info(
                dict(st.secrets["gcp_service_account"]), scopes=SCOPES)
            client = gspread.authorize(creds)
            sh = client.open_by_key(st.secrets["gsheet"]["sheet_id"])
            ws = sh.worksheet("Users")

            all_vals = ws.get_all_values()
            if not all_vals:
                st.error("L'onglet Users est vide.")
                st.stop()

            headers = all_vals[0]
            rows    = all_vals[1:]

            st.write(f"En-têtes actuels : `{headers}`")
            st.write(f"{len(rows)} utilisateur(s) trouvé(s)")

            # Ajouter colonnes manquantes
            if "statut" not in headers:
                headers.append("statut")
            if "date_inscription" not in headers:
                headers.append("date_inscription")

            statut_idx = headers.index("statut")
            date_idx   = headers.index("date_inscription")

            # Mettre à jour chaque ligne
            new_rows = [headers]
            for row in rows:
                # Étendre la ligne si trop courte
                while len(row) < len(headers):
                    row.append("")
                # Remplir statut si vide
                if not row[statut_idx].strip():
                    row[statut_idx] = "Actif"
                # Remplir date si vide
                if not row[date_idx].strip():
                    row[date_idx] = "2024-01-01"
                new_rows.append(row)

            # Réécrire tout
            ws.clear()
            ws.update(new_rows, value_input_option="USER_ENTERED")

            st.success("✅ Migration terminée !")
            st.write("**Nouvelles en-têtes :**", headers)
            st.dataframe(new_rows[1:], column_config={i: headers[i] for i in range(len(headers))})
            st.info("Tu peux maintenant lancer `streamlit run gestion_betail.py`")

        except Exception as e:
            st.error(f"❌ Erreur : {e}")
