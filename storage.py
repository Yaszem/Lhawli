"""
storage.py — Gestion des photos via Supabase Storage pour Élevio
Upload, suppression et récupération d'URLs publiques.
"""
import streamlit as st
from supabase import create_client
import uuid
from PIL import Image
import io
@st.cache_resource(show_spinner=False)
def get_supabase():
    """Retourne le client Supabase authentifié (mis en cache)."""
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["service_key"]
    return create_client(url, key)
def get_bucket():
    return st.secrets["supabase"]["bucket"]
def upload_photo(file_bytes: bytes, filename: str = None) -> str:
    """
    Upload une photo vers Supabase Storage.
    Compresse automatiquement l'image avant upload.
    Retourne l'URL publique de la photo.
    """
    supabase = get_supabase()
    bucket   = get_bucket()
    # Compression intelligente
    img = Image.open(io.BytesIO(file_bytes)).convert("RGB")
    max_dim = 1200
    quality = 85
    while max_dim >= 400:
        buf = io.BytesIO()
        resized = img.copy()
        resized.thumbnail((max_dim, max_dim), Image.LANCZOS)
        resized.save(buf, format="JPEG", quality=quality)
        size_kb = len(buf.getvalue()) / 1024
        if size_kb <= 800:  # max 800 Ko
            break
        if quality > 50:
            quality -= 15
        else:
            max_dim = int(max_dim * 0.75)
    buf.seek(0)
    # Nom de fichier unique
    if not filename:
        filename = f"{uuid.uuid4().hex}.jpg"
    elif not filename.endswith(".jpg"):
        filename = filename.rsplit(".", 1)[0] + ".jpg"
    path = f"animaux/{filename}"
    # Upload vers Supabase
    supabase.storage.from_(bucket).upload(
        path=path,
        file=buf.getvalue(),
        file_options={"content-type": "image/jpeg", "upsert": "true"},
    )
    # Récupérer l'URL publique
    public_url = supabase.storage.from_(bucket).get_public_url(path)
    return public_url
def delete_photos(urls):
    """
    Supprime plusieurs photos en une seule requête.
    """
    try:
        supabase = get_supabase()
        bucket = get_bucket()
        paths = []
        for url in urls or []:
            marker = f"/object/public/{bucket}/"
            if marker in url:
                paths.append(url.split(marker, 1)[1])
        if paths:
            supabase.storage.from_(bucket).remove(paths)
    except Exception as e:
        print(f"Avertissement suppression photos : {e}")
def list_photos(prefix: str = "animaux/") -> list:
    """Liste les photos dans le bucket (utile pour debug)."""
    supabase = get_supabase()
    bucket   = get_bucket()
    try:
        files = supabase.storage.from_(bucket).list(prefix.rstrip("/"))
        return [f["name"] for f in files if f.get("name")]
    except Exception:
        return []
