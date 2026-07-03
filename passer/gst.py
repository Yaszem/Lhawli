import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.graph_objects as go
import gspread
from google.oauth2.service_account import Credentials

# ─── Configuration de la page ───────────────────────────────────────────────
st.set_page_config(
    page_title="MAHAL — Gestion",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ─── Styles CSS ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=DM+Serif+Display&display=swap');
*, *::before, *::after { box-sizing: border-box; }
html, body, .stApp {
    background-color: #F7F6F2;
    color: #1C1C1C;
    font-family: 'DM Sans', sans-serif;
}
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 3rem 4rem 4rem 4rem; max-width: 1300px; }
.page-title {
    font-family: 'DM Serif Display', serif;
    font-size: 2.6rem; color: #1C1C1C;
    margin-bottom: 0.2rem; line-height: 1.1;
}
.page-subtitle {
    font-size: 0.85rem; color: #999; font-weight: 300;
    letter-spacing: 0.08em; text-transform: uppercase; margin-bottom: 2.5rem;
}
.section-title {
    font-family: 'DM Serif Display', serif;
    font-size: 1.35rem; color: #1C1C1C;
    margin-top: 2rem; margin-bottom: 1.2rem;
    padding-bottom: 0.6rem; border-bottom: 1px solid #E0DDD5;
}
.metric-row { display: flex; gap: 1rem; margin-bottom: 2rem; }
.metric-card {
    background: #FFFFFF; border: 1px solid #E8E5DE;
    border-radius: 10px; padding: 1.2rem 1.5rem; flex: 1;
}
.metric-label {
    font-size: 0.72rem; font-weight: 500; text-transform: uppercase;
    letter-spacing: 0.07em; color: #AAA; margin-bottom: 0.5rem;
}
.metric-value {
    font-family: 'DM Serif Display', serif;
    font-size: 1.55rem; color: #1C1C1C; line-height: 1;
}
.metric-value.positive { color: #2D7A3A; }
.metric-value.negative { color: #B03A2E; }
.stTextInput > div > div > input,
.stNumberInput > div > div > input,
.stDateInput > div > div > input {
    background: #F7F6F2 !important; border: 1px solid #DDDAD2 !important;
    border-radius: 8px !important; color: #1C1C1C !important;
    font-family: 'DM Sans', sans-serif !important; font-size: 0.9rem !important;
    padding: 0.55rem 0.9rem !important;
    -webkit-text-fill-color: #1C1C1C !important;
}
.stTextInput > div > div > input::placeholder,
.stNumberInput > div > div > input::placeholder {
    color: #AAAAAA !important; -webkit-text-fill-color: #AAAAAA !important; opacity: 1 !important;
}
.stTextInput > div > div > input:focus,
.stNumberInput > div > div > input:focus {
    border-color: #1C1C1C !important; box-shadow: none !important;
}
.stTextInput label, .stNumberInput label,
.stSelectbox label, .stDateInput label, .stMultiSelect label {
    font-size: 0.75rem !important; font-weight: 500 !important;
    letter-spacing: 0.06em !important; text-transform: uppercase !important;
    color: #999 !important; margin-bottom: 0.3rem !important;
}
.stSelectbox > div > div > div {
    background: #F7F6F2 !important; border: 1px solid #DDDAD2 !important;
    border-radius: 8px !important; font-family: 'DM Sans', sans-serif !important;
    font-size: 0.9rem !important; color: #1C1C1C !important;
}
.stSelectbox [data-baseweb="select"] span,
.stSelectbox [data-baseweb="select"] div { color: #1C1C1C !important; }
.stSelectbox svg, .stTextInput svg, .stNumberInput svg,
.stDateInput svg, .stMultiSelect svg {
    display: block !important; color: #1C1C1C !important; fill: #1C1C1C !important;
}
.stSelectbox input, [data-baseweb="select"] input, [data-baseweb="combobox"] input {
    color: #1C1C1C !important; -webkit-text-fill-color: #1C1C1C !important;
    caret-color: #1C1C1C !important;
}
[data-baseweb="popover"] li, [data-baseweb="menu"] li, [data-baseweb="option"] {
    color: #1C1C1C !important; background: #FFFFFF !important;
    font-family: 'DM Sans', sans-serif !important; font-size: 0.9rem !important;
}
[data-baseweb="option"]:hover { background: #F0EDE5 !important; }
.stCheckbox label, .stCheckbox label p, .stCheckbox span {
    color: #1C1C1C !important; font-size: 0.88rem !important;
}
.stButton > button {
    background: #1C1C1C !important; color: #F7F6F2 !important;
    border: none !important; border-radius: 8px !important;
    padding: 0.65rem 2.2rem !important; font-family: 'DM Sans', sans-serif !important;
    font-size: 0.88rem !important; font-weight: 500 !important;
    letter-spacing: 0.03em !important; margin-top: 1rem;
    transition: opacity 0.2s ease !important;
}
.stButton > button:hover { opacity: 0.75 !important; }
.stSuccess > div { background: #F0F7F0 !important; border: 1px solid #C3DEC3 !important;
    border-radius: 8px !important; color: #2D6A2D !important; font-size: 0.88rem !important; }
.stDataFrame { border-radius: 10px !important; overflow: hidden !important; border: 1px solid #E8E5DE !important; }
.stDataFrame table { font-size: 0.88rem !important; font-family: 'DM Sans', sans-serif !important; }
.stDataFrame thead th {
    background: #F0EDE5 !important; color: #777 !important; font-weight: 500 !important;
    font-size: 0.75rem !important; letter-spacing: 0.05em !important;
    text-transform: uppercase !important; padding: 0.75rem 1rem !important;
    border-bottom: 1px solid #DDDAD2 !important;
}
.stDataFrame tbody tr:nth-child(even) td { background: #FAFAF8 !important; }
.stDataFrame tbody td {
    padding: 0.65rem 1rem !important; border-bottom: 1px solid #F0EDE5 !important;
    color: #1C1C1C !important;
}
.stTabs [data-baseweb="tab-list"] { gap: 0; background: transparent; border-bottom: 1px solid #E0DDD5; }
.stTabs [data-baseweb="tab"] {
    font-family: 'DM Sans', sans-serif !important; font-size: 0.88rem !important;
    font-weight: 400 !important; color: #AAA !important; background: transparent !important;
    border: none !important; border-bottom: 2px solid transparent !important;
    border-radius: 0 !important; padding: 0.65rem 1.4rem !important; letter-spacing: 0.01em;
}
.stTabs [aria-selected="true"] {
    color: #1C1C1C !important; border-bottom: 2px solid #1C1C1C !important; font-weight: 500 !important;
}
.stTabs [data-baseweb="tab-panel"] { padding-top: 0 !important; }
.info-count { font-size: 0.8rem; color: #999; margin-bottom: 0.8rem; }
</style>
""", unsafe_allow_html=True)

# ─── Connexion Google Sheets ─────────────────────────────────────────────────
SPREADSHEET_ID = "1iiBU5dxAymvo6Sxl3lXpyWLvniLMdNHHSnNDw7I7avA"
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

@st.cache_resource
def get_client():
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"], scopes=SCOPES
    )
    return gspread.authorize(creds)

def load_sheet(sheet_name):
    sh = get_client().open_by_key(SPREADSHEET_ID)
    data = sh.worksheet(sheet_name).get_all_records()
    return pd.DataFrame(data)

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

# ─── Helpers ─────────────────────────────────────────────────────────────────
def add_quantity_column(df):
    if 'Quantité (pièces)' not in df.columns:
        df['Quantité (pièces)'] = 1
    return df

def to_numeric(df, cols):
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)
    return df

def compute_resume_personne(t):
    t = to_numeric(t.copy(), ['Montant (MAD)'])
    grouped = t.groupby('Personne').apply(lambda x: pd.Series({
        'Total Achats':   x.loc[x['Type (Achat/Vente/Dépense)'] == 'ACHAT',   'Montant (MAD)'].sum(),
        'Total Ventes':   x.loc[x['Type (Achat/Vente/Dépense)'] == 'VENTE',   'Montant (MAD)'].sum(),
        'Total Dépenses': x.loc[x['Type (Achat/Vente/Dépense)'] == 'DÉPENSE', 'Montant (MAD)'].sum(),
    }), include_groups=False).reset_index()
    grouped['Résultat'] = grouped['Total Ventes'] - (grouped['Total Achats'] + grouped['Total Dépenses'])
    return grouped

def compute_suivi_lot(t):
    t = to_numeric(t.copy(), ['Montant (MAD)', 'Quantité (pièces)'])
    grouped = t.groupby('Lot').apply(lambda x: pd.Series({
        'Total Achats':           x.loc[x['Type (Achat/Vente/Dépense)'] == 'ACHAT',   'Montant (MAD)'].sum(),
        'Total Ventes':           x.loc[x['Type (Achat/Vente/Dépense)'] == 'VENTE',   'Montant (MAD)'].sum(),
        'Total Dépenses':         x.loc[x['Type (Achat/Vente/Dépense)'] == 'DÉPENSE', 'Montant (MAD)'].sum(),
        'Stock Restant (pièces)': (
            x.loc[x['Type (Achat/Vente/Dépense)'] == 'ACHAT', 'Quantité (pièces)'].sum()
          - x.loc[x['Type (Achat/Vente/Dépense)'] == 'VENTE', 'Quantité (pièces)'].sum()
        ),
    }), include_groups=False).reset_index()
    grouped['Résultat'] = grouped['Total Ventes'] - (grouped['Total Achats'] + grouped['Total Dépenses'])
    return grouped

def compute_suivi_avances(t):
    t = to_numeric(t.copy(), ['Montant (MAD)'])
    grouped = t.groupby(['Lot', 'Personne']).apply(lambda x: pd.Series({
        'Total Avancé':   x.loc[x['Type (Achat/Vente/Dépense)'].isin(['ACHAT', 'DÉPENSE']), 'Montant (MAD)'].sum(),
        'Total Encaissé': x.loc[x['Type (Achat/Vente/Dépense)'] == 'VENTE', 'Montant (MAD)'].sum(),
    }), include_groups=False).reset_index()
    grouped['Solde'] = grouped['Total Encaissé'] - grouped['Total Avancé']
    return grouped

def warn(msg):
    st.markdown(
        f"<div style='background:#FFF8E1;border:1px solid #F0C040;border-radius:8px;"
        f"padding:0.65rem 1rem;color:#7A5C00;font-size:0.88rem;margin-top:0.5rem'>{msg}</div>",
        unsafe_allow_html=True
    )

# ─── Chargement ──────────────────────────────────────────────────────────────
try:
    transactions = load_sheet("Gestion globale")
except Exception as e:
    st.error(f"Impossible de charger les données : {e}")
    st.stop()

transactions = add_quantity_column(transactions)
transactions = to_numeric(transactions, ['Montant (MAD)', 'Quantité (pièces)'])

# ─── En-tête ─────────────────────────────────────────────────────────────────
st.markdown('<div class="page-title">Mahal</div>', unsafe_allow_html=True)
st.markdown('<div class="page-subtitle">Gestion de stock et transactions</div>', unsafe_allow_html=True)

# ─── Métriques globales ───────────────────────────────────────────────────────
total_achats   = transactions[transactions['Type (Achat/Vente/Dépense)'] == 'ACHAT']['Montant (MAD)'].sum()
total_ventes   = transactions[transactions['Type (Achat/Vente/Dépense)'] == 'VENTE']['Montant (MAD)'].sum()
total_depenses = transactions[transactions['Type (Achat/Vente/Dépense)'] == 'DÉPENSE']['Montant (MAD)'].sum()
resultat_net   = total_ventes - (total_achats + total_depenses)
couleur_res    = "positive" if resultat_net >= 0 else "negative"

st.markdown(f"""
<div class="metric-row">
    <div class="metric-card"><div class="metric-label">Total Achats</div>
        <div class="metric-value">{total_achats:,.0f} MAD</div></div>
    <div class="metric-card"><div class="metric-label">Total Ventes</div>
        <div class="metric-value">{total_ventes:,.0f} MAD</div></div>
    <div class="metric-card"><div class="metric-label">Total Dépenses</div>
        <div class="metric-value">{total_depenses:,.0f} MAD</div></div>
    <div class="metric-card"><div class="metric-label">Résultat net</div>
        <div class="metric-value {couleur_res}">{resultat_net:+,.0f} MAD</div></div>
</div>
""", unsafe_allow_html=True)

# ─── Onglets ──────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "Nouvelle transaction", "Recherche", "Graphiques",
    "Catalogue des lots", "Résumé par personne", "Gestion des lots", "Suivi des avances"
])

# ── Tab 1 ─────────────────────────────────────────────────────────────────────
with tab1:
    st.markdown('<div class="section-title">Nouvelle transaction</div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3, gap="large")
    with col1:
        date          = st.date_input("Date", datetime.now())
        personne      = st.text_input("Personne")
        type_trans    = st.selectbox("Type de transaction", ["ACHAT", "VENTE", "DÉPENSE"])
    with col2:
        lot           = st.text_input("Lot")
        description   = st.text_input("Description")
        montant       = st.number_input("Montant (MAD)", min_value=0.0, step=0.01)
    with col3:
        quantite      = st.number_input("Quantité (pièces)", min_value=1, step=1)
        mode_paiement = st.text_input("Mode de paiement")
        statut_lot    = st.selectbox("Statut du lot", ["Actif", "Fermé"])
    remarque = st.text_input("Remarque")

    if st.button("Enregistrer"):
        row = {
            'Date': str(date), 'Personne': personne.upper(),
            'Type (Achat/Vente/Dépense)': type_trans,
            'Description': description, 'Lot': lot.upper(),
            'Montant (MAD)': montant, 'Quantité (pièces)': quantite,
            'Mode de paiement': mode_paiement, 'Remarque': remarque,
            'Statut du lot': statut_lot,
        }
        try:
            append_row(row, "Gestion globale")
            st.success("Transaction enregistrée. Rafraichissez la page pour voir les mises à jour.")
            st.cache_resource.clear()
        except Exception as e:
            st.error(f"Erreur lors de l'enregistrement : {e}")

# ── Tab 2 : Recherche ─────────────────────────────────────────────────────────
with tab2:
    st.markdown('<div class="section-title">Recherche dans les transactions</div>', unsafe_allow_html=True)
    col_s1, col_s2, col_s3 = st.columns([2, 1, 1], gap="large")
    with col_s1:
        query = st.text_input("Rechercher", placeholder="Nom, lot, description, remarque...")
    with col_s2:
        filtre_type = st.selectbox("Type", ["Tous", "ACHAT", "VENTE", "DÉPENSE"])
    with col_s3:
        lots_dispo = ["Tous"] + sorted(transactions['Lot'].dropna().astype(str).unique().tolist())
        filtre_lot = st.selectbox("Lot", lots_dispo)

    df_f = transactions.copy()
    if query:
        mask = (
            df_f['Personne'].astype(str).str.contains(query, case=False, na=False) |
            df_f['Lot'].astype(str).str.contains(query, case=False, na=False) |
            df_f['Description'].astype(str).str.contains(query, case=False, na=False) |
            df_f['Remarque'].astype(str).str.contains(query, case=False, na=False)
        )
        df_f = df_f[mask]
    if filtre_type != "Tous":
        df_f = df_f[df_f['Type (Achat/Vente/Dépense)'] == filtre_type]
    if filtre_lot != "Tous":
        df_f = df_f[df_f['Lot'] == filtre_lot]

    st.markdown(f'<div class="info-count">{len(df_f)} transaction(s) trouvée(s)</div>', unsafe_allow_html=True)
    st.dataframe(df_f, width='stretch', hide_index=True)

# ── Tab 3 : Graphiques ────────────────────────────────────────────────────────
with tab3:
    st.markdown('<div class="section-title">Graphiques</div>', unsafe_allow_html=True)
    COLORS = {'ACHAT': '#5C85D6', 'VENTE': '#2D7A3A', 'DÉPENSE': '#C0864A'}
    PL = dict(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
              font=dict(family='DM Sans', color='#555', size=12),
              margin=dict(l=10, r=10, t=40, b=10))

    gc1, gc2 = st.columns(2, gap="large")
    with gc1:
        st.markdown('<div class="section-title" style="font-size:1rem;">Répartition globale</div>', unsafe_allow_html=True)
        fig = go.Figure(go.Pie(
            labels=['Achats', 'Ventes', 'Dépenses'],
            values=[total_achats, total_ventes, total_depenses], hole=0.55,
            marker=dict(colors=['#5C85D6', '#2D7A3A', '#C0864A'], line=dict(color='#F7F6F2', width=3)),
            hovertemplate='%{label}<br>%{value:,.0f} MAD<extra></extra>',
        ))
        fig.update_layout(**PL, showlegend=True,
            legend=dict(orientation='h', yanchor='bottom', y=-0.15, xanchor='center', x=0.5))
        st.plotly_chart(fig, use_container_width=True)

    with gc2:
        st.markdown('<div class="section-title" style="font-size:1rem;">Résultat par lot</div>', unsafe_allow_html=True)
        sl = compute_suivi_lot(transactions)
        fig2 = go.Figure(go.Bar(x=sl['Lot'], y=sl['Résultat'],
            marker_color=['#2D7A3A' if v >= 0 else '#B03A2E' for v in sl['Résultat']],
            hovertemplate='%{x}<br>%{y:,.0f} MAD<extra></extra>'))
        fig2.update_layout(**PL, xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor='#EEE', tickformat=',.0f'))
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown('<div class="section-title" style="font-size:1rem;">Evolution des montants dans le temps</div>', unsafe_allow_html=True)
    df_t = transactions.copy()
    df_t['Date'] = pd.to_datetime(df_t['Date'], errors='coerce')
    df_t = df_t.dropna(subset=['Date'])
    df_t['Mois'] = df_t['Date'].dt.to_period('M').astype(str)
    dp = df_t.groupby(['Mois', 'Type (Achat/Vente/Dépense)'])['Montant (MAD)'].sum().reset_index()
    fig3 = go.Figure()
    for tv, col in COLORS.items():
        d = dp[dp['Type (Achat/Vente/Dépense)'] == tv]
        if not d.empty:
            fig3.add_trace(go.Scatter(x=d['Mois'], y=d['Montant (MAD)'],
                mode='lines+markers', name=tv,
                line=dict(color=col, width=2), marker=dict(size=6),
                hovertemplate='%{x}<br>%{y:,.0f} MAD<extra>' + tv + '</extra>'))
    fig3.update_layout(**PL, xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor='#EEE', tickformat=',.0f'),
        legend=dict(orientation='h', yanchor='bottom', y=-0.2, xanchor='center', x=0.5))
    st.plotly_chart(fig3, use_container_width=True)

    st.markdown('<div class="section-title" style="font-size:1rem;">Résultat par personne</div>', unsafe_allow_html=True)
    rp = compute_resume_personne(transactions)
    fig4 = go.Figure(go.Bar(x=rp['Personne'], y=rp['Résultat'],
        marker_color=['#2D7A3A' if v >= 0 else '#B03A2E' for v in rp['Résultat']],
        hovertemplate='%{x}<br>%{y:,.0f} MAD<extra></extra>'))
    fig4.update_layout(**PL, xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor='#EEE', tickformat=',.0f'))
    st.plotly_chart(fig4, use_container_width=True)

# ── Tab 4 ─────────────────────────────────────────────────────────────────────
with tab4:
    st.markdown('<div class="section-title">Catalogue des lots</div>', unsafe_allow_html=True)
    st.dataframe(compute_suivi_lot(transactions), width='stretch', hide_index=True)

# ── Tab 5 ─────────────────────────────────────────────────────────────────────
with tab5:
    st.markdown('<div class="section-title">Résumé par personne</div>', unsafe_allow_html=True)
    st.dataframe(compute_resume_personne(transactions), width='stretch', hide_index=True)

# ── Tab 6 ─────────────────────────────────────────────────────────────────────
with tab6:
    st.markdown('<div class="section-title">Gestion des lots</div>', unsafe_allow_html=True)
    try:
        st.dataframe(load_sheet("Gestion des lots"), width='stretch', hide_index=True)
    except Exception as e:
        st.error(f"Impossible de charger l'onglet : {e}")

# ── Tab 7 : Avances + Suppressions ────────────────────────────────────────────
with tab7:
    st.markdown('<div class="section-title">Suivi des avances</div>', unsafe_allow_html=True)
    st.dataframe(compute_suivi_avances(transactions), width='stretch', hide_index=True)

    st.markdown('<div class="section-title">Supprimer des transactions</div>', unsafe_allow_html=True)
    del_col1, del_col2 = st.columns(2, gap="large")

    with del_col1:
        st.markdown("**Supprimer toutes les transactions d'un lot**")
        lots_ex = sorted(transactions['Lot'].dropna().astype(str).unique().tolist())
        lot_sup = st.selectbox("Choisir un lot", ["— sélectionner —"] + lots_ex, key="del_lot")
        if lot_sup != "— sélectionner —":
            nb = len(transactions[transactions['Lot'] == lot_sup])
            st.markdown(f'<div class="info-count">{nb} transaction(s) concernée(s)</div>', unsafe_allow_html=True)
        confirm_lot = st.checkbox("Je confirme la suppression du lot", key="confirm_lot")
        if st.button("Supprimer le lot", key="btn_del_lot"):
            if lot_sup == "— sélectionner —": warn("Veuillez sélectionner un lot.")
            elif not confirm_lot: warn("Cochez la case de confirmation avant de supprimer.")
            else:
                transactions = transactions[transactions['Lot'] != lot_sup]
                save_sheet(transactions, "Gestion globale")
                st.success(f"Lot « {lot_sup} » supprimé.")
                st.cache_resource.clear()

    with del_col2:
        st.markdown("**Supprimer toutes les transactions d'une personne**")
        pers_ex = sorted(transactions['Personne'].dropna().astype(str).unique().tolist())
        pers_sup = st.selectbox("Choisir une personne", ["— sélectionner —"] + pers_ex, key="del_pers")
        if pers_sup != "— sélectionner —":
            nb2 = len(transactions[transactions['Personne'] == pers_sup])
            st.markdown(f'<div class="info-count">{nb2} transaction(s) concernée(s)</div>', unsafe_allow_html=True)
        confirm_pers = st.checkbox("Je confirme la suppression de la personne", key="confirm_pers")
        if st.button("Supprimer la personne", key="btn_del_pers"):
            if pers_sup == "— sélectionner —": warn("Veuillez sélectionner une personne.")
            elif not confirm_pers: warn("Cochez la case de confirmation avant de supprimer.")
            else:
                transactions = transactions[transactions['Personne'] != pers_sup]
                save_sheet(transactions, "Gestion globale")
                st.success(f"Personne « {pers_sup} » supprimée.")
                st.cache_resource.clear()
