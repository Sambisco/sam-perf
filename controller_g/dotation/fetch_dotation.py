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


def fetch_dotation():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    data = []

    # === Cas 1: détails d'une sortie ===
    if "id_dotation" in request.form:
        id_dotation = encryptor("decrypt", request.form["id_dotation"])
        query = """
            SELECT * FROM dotation
            INNER JOIN contrat ON contrat.id_contrat=dotation.id_contrat
            INNER JOIN employe ON employe.id_employe=contrat.id_employe
            INNER JOIN reference ON reference.id_reference=employe.id_reference
            WHERE dotation.id_dotation=%s
        """
        cursor.execute(query, (id_dotation,))
        result = cursor.fetchall()

        for row in result:
            response = {
                "id_dotation": encryptor("encrypt", str(row["id_dotation"])),
                "prenom": row["prenom"],
                "nom": row["nom"],
                "poste_occupe": row["poste_occupe"],
                "date_dotation": (
                    row["date_dotation"].strftime("%Y-%m-%d")
                    if row["date_dotation"]
                    else ""
                ),
                "periode_du": (
                    row["periode_du"].strftime("%Y-%m-%d") if row["periode_du"] else ""
                ),
                "periode_au": (
                    row["periode_au"].strftime("%Y-%m-%d") if row["periode_au"] else ""
                ),
                "carburant": format_number(row["carburant"]),
                "motif": row["motif"],
                "lieu": row["lieu"],
                "vehicule": row["vehicule"],
                "immatriculation": row["immatriculation"],
                "ca_dotation": row["ca_dotation"],
                "numero_carte": row["numero_carte"],
                "photo": (
                    url_for(
                        "static",
                        filename=f"img/img_employe/{row.get('matricule','')}/{row.get('photo','')}",
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
           SELECT * FROM dotation
           INNER JOIN contrat ON contrat.id_contrat=dotation.id_contrat
           INNER JOIN employe ON employe.id_employe=contrat.id_employe
           INNER JOIN reference ON reference.id_reference=employe.id_reference
           WHERE reference.id_reference= %s
           ORDER BY dotation.id_dotation DESC
        """
        cursor.execute(query, (id_ref,))
        result = cursor.fetchall()

        for idx, row in enumerate(result, 1):
            acronym_prenom = make_acronym(row["prenom"])
            acronym_nom = make_acronym(row["nom"])
            response = {
                "count": idx,
                "id_dotation": encryptor("encrypt", str(row["id_dotation"])),
                "prenom": row["prenom"],
                "nom": row["nom"],
                "matricule": f"{acronym_prenom}{acronym_nom}-{row['matricule']}",
                "poste_occupe": row["poste_occupe"],
                "date_dotation": format_date_fr(row["date_dotation"], style="full"),
                "periode_du": format_date_fr(row["periode_du"], style="full"),
                "periode_au": format_date_fr(row["periode_au"], style="full"),
                "carburant": row["carburant"],
                "motif": row["motif"],
                "lieu": row["lieu"],
                "vehicule": row["vehicule"],
                "immatriculation": row["immatriculation"],
                "ca_dotation": row["ca_dotation"],
                "photo": (
                    url_for(
                        "static",
                        filename=f"img/img_employe/{row.get('matricule','')}/{row.get('photo','')}",
                    )
                    if row.get("photo")
                    else url_for("static", filename="img/image/image-profil.png")
                ),
            }
            data.append(response)

    cursor.close()
    conn.close()
    return jsonify(data)
