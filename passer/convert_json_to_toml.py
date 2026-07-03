"""
convert_json_to_toml.py
Convertit automatiquement ton fichier credentials.json (téléchargé depuis
Google Cloud) en secrets.toml valide, sans risque d'erreur de copier-coller.

Usage :
    python convert_json_to_toml.py credentials.json TON_SHEET_ID
"""
import json
import sys
import os

def main():
    if len(sys.argv) < 3:
        print("Usage : python convert_json_to_toml.py credentials.json SHEET_ID")
        sys.exit(1)

    json_path = sys.argv[1]
    sheet_id  = sys.argv[2]

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    lines = ["[gcp_service_account]"]
    for key, value in data.items():
        # Échapper les retours à la ligne réels en \n littéral pour le TOML
        if isinstance(value, str):
            value_escaped = value.replace("\\", "\\\\").replace("\n", "\\n").replace('"', '\\"')
            # On annule le double-échappement du \n qu'on veut garder littéral
            value_escaped = value.replace("\n", "\\n").replace('"', '\\"')
            lines.append(f'{key} = "{value_escaped}"')
        else:
            lines.append(f'{key} = "{value}"')

    lines.append("")
    lines.append("[gsheet]")
    lines.append(f'sheet_id = "{sheet_id}"')

    out_dir = ".streamlit"
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "secrets.toml")

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print(f"✅ Fichier généré avec succès : {out_path}")
    print("Tu peux maintenant lancer : streamlit run init_sheet.py")

if __name__ == "__main__":
    main()
