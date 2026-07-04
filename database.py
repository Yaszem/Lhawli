"""
database.py — Connexion Google Sheets pour Lhawli
Gère la lecture/écriture des animaux, races et utilisateurs.
"""
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import hashlib
import hmac
import os
import binascii

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

# ── Sécurité mots de passe ──────────────────────────────────────────
PBKDF2_ITERATIONS = 100_000

def hash_password(password: str) -> str:
    """Hache un mot de passe avec un sel aléatoire (PBKDF2-HMAC-SHA256)."""
    salt = os.urandom(16)
    pwd_hash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
    return f"{binascii.hexlify(salt).decode()}${binascii.hexlify(pwd_hash).decode()}"


def verify_password(password: str, stored: str) -> bool:
    """
    Vérifie un mot de passe contre sa version stockée.
    Compatible avec d'anciens mots de passe en clair déjà présents dans le Sheet
    (comparaison directe en fallback) pour ne pas bloquer les comptes existants.
    """
    if not stored:
        return False
    if "$" in stored:
        try:
            salt_hex, hash_hex = stored.split("$", 1)
            salt = binascii.unhexlify(salt_hex)
            expected = binascii.unhexlify(hash_hex)
            pwd_hash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
            return hmac.compare_digest(pwd_hash, expected)
        except Exception:
            return False
    # Ancien format : mot de passe en clair (compatibilité ascendante)
    return hmac.compare_digest(password, stored)


# ── En-têtes ─────────────────────────────────────────────────────────
HEADERS_ANIMAUX = ["id","type","race","sex","birth","earTag","buyPrice",
                   "sellPrice","status","weight","notes","photo","photos"]
HEADERS_RACES   = ["type","race"]
HEADERS_USERS   = ["email","password","name","role","statut","date_inscription"]
#                                                    ^^^^^^^ En attente / Actif / Refusé

DEFAULT_USERS = [
    ["admin@elevio.fr",    hash_password("admin123"),   "Ahmed Benali",    "Administrateur", "Actif", "2024-01-01"],
    ["manager@elevio.fr",  hash_password("manager123"), "Fatima Zahra",    "Gestionnaire",   "Actif", "2024-01-01"],
    ["observer@elevio.fr", hash_password("obs123"),     "Karim Moussaoui", "Observateur",    "Actif", "2024-01-01"],
]

DEFAULT_RACES = [
    ["Mouton","Mérinos"],["Mouton","Lacaune"],["Mouton","Romanov"],
    ["Mouton","Suffolk"],["Mouton","Île-de-France"],["Mouton","Texel"],
    ["Vache","Holstein"],["Vache","Charolaise"],["Vache","Limousine"],
    ["Vache","Montbéliarde"],["Vache","Normande"],["Vache","Blonde d'Aquitaine"],
]

DEFAULT_ANIMALS = [
    [1,"Mouton","Mérinos","Mâle","2022-03-15","MO-2022-001",180,320,"Disponible",65,"","",""],
    [2,"Vache","Holstein","Femelle","2020-07-22","VA-2020-045",1200,2100,"Vendu",580,"","",""],
    [3,"Mouton","Lacaune","Femelle","2023-01-10","MO-2023-012",150,290,"Disponible",52,"Bonne laitière","",""],
    [4,"Vache","Charolaise","Mâle","2021-05-03","VA-2021-008",980,1850,"Disponible",720,"","",""],
    [5,"Mouton","Romanov","Mâle","2023-08-19","MO-2023-034",130,250,"Disponible",48,"","",""],
]


@st.cache_resource(show_spinner=False)
def get_client():
    creds_dict = dict(st.secrets["gcp_service_account"])
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    return gspread.authorize(creds)


@st.cache_resource(show_spinner=False)
def get_spreadsheet():
    client = get_client()
    return client.open_by_key(st.secrets["gsheet"]["sheet_id"])


def _ensure_worksheet(sh, name, headers, default_rows=None):
    """Crée l'onglet s'il n'existe pas. N'écrit les données par défaut QUE si l'onglet est vraiment vide."""
    try:
        ws = sh.worksheet(name)
    except gspread.WorksheetNotFound:
        ws = sh.add_worksheet(title=name, rows=500, cols=max(20, len(headers)))
        # Nouvel onglet → écrire les en-têtes + données par défaut
        rows_to_write = [headers]
        if default_rows:
            rows_to_write += [[str(x) for x in row] for row in default_rows]
        ws.update(rows_to_write, value_input_option="USER_ENTERED")
        return ws

    # L'onglet existe — on ne touche QUE les en-têtes manquantes
    existing = ws.get_all_values()
    if not existing:
        # Onglet vide (jamais eu de données) → écrire en-têtes uniquement, PAS les defaults
        ws.update([headers], value_input_option="USER_ENTERED")
    else:
        # Ajouter les colonnes manquantes sans toucher aux données
        current_headers = existing[0]
        for col in headers:
            if col not in current_headers:
                col_idx = len(current_headers) + 1
                ws.update_cell(1, col_idx, col)
                current_headers.append(col)
    return ws


def init_database():
    """Vérifie que les onglets existent et ont les bonnes colonnes. N'écrase jamais les données."""
    sh = get_spreadsheet()
    ws_animaux = _ensure_worksheet(sh, "Animaux", HEADERS_ANIMAUX)  # pas de default_rows ici
    ws_races   = _ensure_worksheet(sh, "Races",   HEADERS_RACES)
    ws_users   = _ensure_worksheet(sh, "Users",   HEADERS_USERS)
    return ws_animaux, ws_races, ws_users


# ══════════════════════════════════════════════════════════════════════
# LECTURE
# ══════════════════════════════════════════════════════════════════════
def load_animals():
    import json
    sh = get_spreadsheet()
    ws = sh.worksheet("Animaux")
    records = ws.get_all_records()
    animals = []
    for r in records:
        if not r.get("earTag"):
            continue
        raw_photos = r.get("photos","")
        try:
            photos = json.loads(raw_photos) if raw_photos else []
        except Exception:
            photos = [raw_photos] if raw_photos else []
        if not photos and r.get("photo"):
            photos = [r["photo"]]
        animals.append({
            "id":        int(r["id"]) if str(r["id"]).strip() else 0,
            "type":      str(r["type"]), "race": str(r["race"]), "sex": str(r["sex"]),
            "birth":     str(r["birth"]), "earTag": str(r["earTag"]),
            "buyPrice":  float(r["buyPrice"])  if str(r["buyPrice"]).strip()  else 0.0,
            "sellPrice": float(r["sellPrice"]) if str(r["sellPrice"]).strip() else 0.0,
            "status":    str(r["status"]),
            "weight":    float(r["weight"]) if str(r["weight"]).strip() else 0.0,
            "notes":     str(r.get("notes","")),
            "photo":     photos[0] if photos else None,
            "photos":    photos,
        })
    return animals


def load_races():
    sh = get_spreadsheet()
    ws = sh.worksheet("Races")
    records = ws.get_all_records()
    races_mouton, races_vache = [], []
    for r in records:
        if r["type"] == "Mouton" and r["race"] not in races_mouton:
            races_mouton.append(r["race"])
        elif r["type"] == "Vache" and r["race"] not in races_vache:
            races_vache.append(r["race"])
    return races_mouton, races_vache


def load_users():
    sh = get_spreadsheet()
    ws = sh.worksheet("Users")

    all_vals = ws.get_all_values()
    if not all_vals:
        return []

    headers = [h.strip() for h in all_vals[0]]
    rows    = all_vals[1:]

    # S'assurer que les colonnes statut et date_inscription existent
    # Si absentes dans le header, on les ajoute automatiquement
    if "statut" not in headers:
        # Ajouter la colonne dans le Sheet
        col_idx = len(headers) + 1
        ws.update_cell(1, col_idx, "statut")
        headers.append("statut")
        # Remplir toutes les lignes existantes avec "Actif"
        for i, _ in enumerate(rows):
            ws.update_cell(i + 2, col_idx, "Actif")

    if "date_inscription" not in headers:
        col_idx = len(headers) + 1
        ws.update_cell(1, col_idx, "date_inscription")
        headers.append("date_inscription")
        for i, _ in enumerate(rows):
            ws.update_cell(i + 2, col_idx, "2024-01-01")

    users = []
    for row in rows:
        # Étendre la ligne si elle a moins de colonnes que les headers
        while len(row) < len(headers):
            row.append("")

        def get(col):
            try:
                return row[headers.index(col)].strip() if col in headers else ""
            except Exception:
                return ""

        email = get("email")
        if not email:
            continue

        role_raw = (get("role") or "Observateur").strip()
        role_normalized = "Administrateur" if role_raw in ("Admin","Administrator") else role_raw
        users.append({
            "email":            email,
            "password":         get("password"),
            "name":             get("name"),
            "role":             role_normalized,
            "statut":           (get("statut") or "Actif").strip(),
            "date_inscription": get("date_inscription"),
        })
    return users


# ══════════════════════════════════════════════════════════════════════
# ÉCRITURE
# ══════════════════════════════════════════════════════════════════════
def save_all_animals(animals):
    import json
    if not animals:
        raise ValueError("Refus d'écrire : liste vide. Opération annulée.")
    sh = get_spreadsheet()
    ws = sh.worksheet("Animaux")
    rows = [HEADERS_ANIMAUX]
    for a in animals:
        photos = a.get("photos") or ([a["photo"]] if a.get("photo") else [])
        # Filtrer les éventuels base64 résiduels (ne garder que les URLs http)
        photos = [p for p in photos if p and str(p).startswith("http")]
        first_photo = photos[0] if photos else ""
        rows.append([
            a["id"], a["type"], a["race"], a["sex"], a["birth"], a["earTag"],
            a["buyPrice"], a["sellPrice"], a["status"], a["weight"],
            a.get("notes",""),
            first_photo,
            json.dumps(photos, ensure_ascii=False),
        ])
    ws.clear()
    ws.update(rows, value_input_option="USER_ENTERED")


def save_all_users(users):
    """Réécrit entièrement l'onglet Users."""
    sh = get_spreadsheet()
    ws = sh.worksheet("Users")
    rows = [HEADERS_USERS]
    for u in users:
        rows.append([
            u["email"], u["password"], u["name"], u["role"],
            u.get("statut","Actif"), u.get("date_inscription",""),
        ])
    ws.clear()
    ws.update(rows, value_input_option="USER_ENTERED")


def register_user(email, password, name):
    """Ajoute un nouvel utilisateur avec statut 'En attente'. Le mot de passe est haché avant stockage."""
    sh = get_spreadsheet()
    ws = sh.worksheet("Users")
    date_now = datetime.now().strftime("%Y-%m-%d %H:%M")
    hashed_pwd = hash_password(password)
    # Ordre : email | password | name | role | statut | date_inscription
    ws.append_row(
        [email.strip(), hashed_pwd, name.strip(), "Observateur", "En attente", date_now],
        value_input_option="USER_ENTERED"
    )


def add_race(race_type, race_name):
    sh = get_spreadsheet()
    ws = sh.worksheet("Races")
    ws.append_row([race_type, race_name], value_input_option="USER_ENTERED")