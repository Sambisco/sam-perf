from flask import request, Response, url_for, jsonify
import re
import locale
import json
from datetime import datetime, date, timedelta
from templates.include.connect import get_connection
from templates.include.encryptor import encryptor
from babel.dates import format_date

# Locale française
try:
    locale.setlocale(locale.LC_TIME, "fr_FR.UTF-8")
except locale.Error:
    pass


def format_date_fr(date_str, style="long"):
    """
    Formatte une date en français avec différents styles :
    - style="full"   → "vendredi 13 décembre 2024"
    - style="long"   → "13 décembre 2024"
    - style="month"  → "décembre 2024"
    """
    try:
        if not date_str:
            return ""

        # Conversion en objet datetime/date
        if isinstance(date_str, (datetime, date)):
            dt = date_str
        else:
            dt = datetime.strptime(date_str, "%Y-%m-%d")

        # Choix du format
        if style == "full":
            fmt = "EEEE d MMMM yyyy"
        elif style == "month":
            fmt = "MMMM yyyy"
        else:  # "long" par défaut
            fmt = "dd MMMM yyyy"

        return format_date(dt, format=fmt, locale="fr_FR").capitalize()

    except Exception:
        return ""


def format_number(num):
    try:
        if num is None:
            return "0"
        return f"{num:,.0f}".replace(",", " ").replace(".", ",")
    except Exception:
        return "0"


# === Fonction utilitaire pour acronymes ===
def make_acronym(word: str) -> str:
    # Supprimer caractères spéciaux style apostrophe
    cleaned = word.replace("'", "").replace("’", "").replace("`", "")
    parts = cleaned.split()
    return "".join([p[0].upper() for p in parts if p])


def fetch_reception():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    data = []

    # === Cas 1: détails d'une sortie ===
    if "id_reception_carburant" in request.form:
        id_reception_carburant = encryptor("decrypt", request.form["id_reception_carburant"])
        query = """
            SELECT * FROM reception_carburant 
            INNER JOIN fournisseur ON fournisseur.id_fournisseur=reception_carburant.id_fournisseur
            WHERE id_reception_carburant=%s
        """
        cursor.execute(query, (id_reception_carburant,))
        result = cursor.fetchall()

        for row in result:
            response = {
                "id_reception_carburant": encryptor(
                    "encrypt", str(row["id_reception_carburant"])
                ),
                "fournisseur": row["fournisseur"],
                "telephone_f": row["telephone_f"],
                "date_reception": (
                    row["date_reception"].strftime("%Y-%m-%d")
                    if row["date_reception"]
                    else ""
                ),
                "carburant_gasoil": format_number(row["carburant_gasoil"]),
                "carburant_super": format_number(row["carburant_super"]),
                "numero_facture": row["numero_facture"],
                "carburant": (row["carburant_gasoil"] + row["carburant_super"]),
                "numero_bon": row["numero_bon"],
                "photo": (
                    url_for(
                        "static",
                        filename=f"img/fournisseur/{row.get('photo','')}",
                    )
                    if row.get("photo")
                    else url_for("static", filename="img/image/image-profil.png")
                ),
            }
            data.append(response)

    # === Cas 2: sorties par référence ===
    elif "id" in request.form:
        id_ref = encryptor("decrypt", request.form["id"])
        query = """
           SELECT * FROM reception_carburant 
           INNER JOIN fournisseur ON fournisseur.id_fournisseur=reception_carburant.id_fournisseur
       	   INNER JOIN reference ON reference.id_reference=fournisseur.id_reference 
           WHERE reference.id_reference= %s
           ORDER BY reception_carburant.id_reception_carburant DESC
        """
        cursor.execute(query, (id_ref,))
        result = cursor.fetchall()

        for idx, row in enumerate(result, 1):

            response = {
                "count": idx,
                "id_reception_carburant": encryptor(
                    "encrypt", str(row["id_reception_carburant"])
                ),
                "date_reception": format_date_fr(row["date_reception"], style="full"),
                "carburant_gasoil": format_number(row["carburant_gasoil"]),
                "carburant_super": format_number(row["carburant_super"]),
                "numero": str(row["numero"]).zfill(7),
                "numero_facture": row["numero_facture"],
                "carburant": (row["carburant_gasoil"] + row["carburant_super"]),
                "carburant_gasoil": f"{row['carburant_gasoil']} Litres Gasoil",
                "carburant_super": f"{row['carburant_super']} Litres Super",
                "numero_bon": row["numero_bon"],
                "fournisseur": row["fournisseur"],
                "telephone_f": row["telephone_f"],
                "photo": (
                    url_for(
                        "static",
                        filename=f"img/fournisseur/{row.get('photo','')}",
                    )
                    if row.get("photo")
                    else url_for("static", filename="img/image/image-profil.png")
                ),
            }
            data.append(response)

    cursor.close()
    conn.close()
    return jsonify(data)
