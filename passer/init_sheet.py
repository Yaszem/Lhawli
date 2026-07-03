"""
init_sheet.py — Script à lancer UNE FOIS pour créer/vérifier les colonnes
dans ton Google Sheet (onglets Animaux, Races, Users).

Usage :
    streamlit run init_sheet.py
"""
import streamlit as st
from database import init_database, load_animals, load_races, load_users

st.set_page_config(page_title="Init Élevio DB", page_icon="🔧")

st.title("🔧 Initialisation de la base Élevio")
st.write("Ce script crée les colonnes et les données par défaut dans ton Google Sheet.")

if st.button("🚀 Initialiser / Vérifier la base", type="primary"):
    with st.spinner("Connexion à Google Sheets…"):
        try:
            ws_animaux, ws_races, ws_users = init_database()
            st.success("✅ Connexion réussie ! Les onglets sont prêts.")

            st.subheader("📋 Onglet Animaux")
            animals = load_animals()
            st.dataframe(animals, use_container_width=True)
            st.caption(f"{len(animals)} animal(aux) chargé(s)")

            st.subheader("🐑 Onglet Races")
            races_mouton, races_vache = load_races()
            c1, c2 = st.columns(2)
            with c1:
                st.write("**Moutons**")
                st.write(races_mouton)
            with c2:
                st.write("**Vaches**")
                st.write(races_vache)

            st.subheader("👥 Onglet Users")
            users = load_users()
            st.dataframe(users, use_container_width=True)

            st.success("🎉 Tout est prêt ! Tu peux maintenant lancer gestion_betail.py")

        except Exception as e:
            st.error(f"❌ Erreur de connexion : {e}")
            st.info("""
            Vérifie que :
            - `.streamlit/secrets.toml` contient bien `[gcp_service_account]` et `[gsheet]`
            - Le Sheet est bien partagé avec l'email du compte de service (rôle Éditeur)
            - Les API Google Sheets + Google Drive sont activées sur Google Cloud Console
            """)
