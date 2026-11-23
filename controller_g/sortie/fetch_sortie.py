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


def fetch_sortie():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    data = []

    # === Cas 1: détails d'une sortie ===
    if "id_sortie" in request.form:
        id_sortie = encryptor("decrypt", request.form["id_sortie"])
        query = """
            SELECT * FROM detail_sortie
            INNER JOIN sortie ON sortie.id_sortie=detail_sortie.id_sortie
            INNER JOIN contrat ON contrat.id_contrat=sortie.id_contrat
            INNER JOIN employe ON employe.id_employe=contrat.id_employe
            INNER JOIN matiere ON matiere.id_matiere=detail_sortie.id_matiere
            WHERE sortie.id_sortie=%s
        """
        cursor.execute(query, (id_sortie,))
        result = cursor.fetchall()

        for row in result:
            response = {
                "id_sortie": encryptor("encrypt", str(row["id_sortie"])),
                "prenom": row["prenom"],
                "nom": row["nom"],
                "photo": (
                    url_for(
                        "static",
                        filename=f"img/img_employe/{row.get('matricule','')}/{row.get('photo','')}",
                    )
                    if row.get("photo")
                    else url_for("static", filename="img/image/image-profil.png")
                ),
                "image": url_for(
                    "static",
                    filename=(
                        f"img/matiere/{row['image']}"
                        if row["image"]
                        else "img/image/image.jpg"
                    ),
                ),
                "total": row["total"],
                "id_matiere": encryptor("encrypt", str(row["id_matiere"])),
                "id_matiere_raw": row["id_matiere"],
                "id_contrat": encryptor("encrypt", str(row["id_contrat"])),
                "numero": str(row["numero"]).zfill(7),
                "date_sortie": (
                    row["date_sortie"].strftime("%Y-%m-%d")
                    if row["date_sortie"]
                    else ""
                ),
                "designation": row["designation"],
                "quantite": row["quantite"],
                "observation": row["observation"],
                "nbre_unite": row["nbre_unite"],
            }
            data.append(response)
    # ======== SORTIE EXTERNE
    elif "id_sortie_ext" in request.form:
        id_sortie = encryptor("decrypt", request.form["id_sortie_ext"])
        query = """
           SELECT * FROM detail_sortie_externe
           INNER JOIN sortie_externe ON sortie_externe.id_sortie_externe=detail_sortie_externe.id_sortie_externe
           INNER JOIN matiere ON matiere.id_matiere=detail_sortie_externe.id_matiere
           WHERE sortie_externe.id_sortie_externe=%s
        """
        cursor.execute(query, (id_sortie,))
        result = cursor.fetchall()

        for row in result:
            response = {
                "id_sortie_externe": encryptor(
                    "encrypt", str(row["id_sortie_externe"])
                ),
                "nom_complet_externe": row["nom_complet_externe"],
                "telephone_externe": row["telephone_externe"],
                "image": url_for(
                    "static",
                    filename=(
                        f"img/matiere/{row['image']}"
                        if row["image"]
                        else "img/image/image.jpg"
                    ),
                ),
                "total": row["total"],
                "id_matiere": encryptor("encrypt", str(row["id_matiere"])),
                "id_matiere_raw": row["id_matiere"],
                "numero": str(row["numero"]).zfill(7),
                "date_sortie": (
                    row["date_sortie"].strftime("%Y-%m-%d")
                    if row["date_sortie"]
                    else ""
                ),
                "designation": row["designation"],
                "quantite": row["quantite"],
                "observation": row["observation"],
                "nbre_unite": row["nbre_unite"],
            }
            data.append(response)
    # === Cas 2: sorties par référence ===
    elif "id" in request.form:
        id_ref = encryptor("decrypt", request.form["id"])
        query = """
            SELECT * FROM sortie
            INNER JOIN contrat ON contrat.id_contrat=sortie.id_contrat
            INNER JOIN employe ON employe.id_employe=contrat.id_employe
            INNER JOIN reference ON reference.id_reference=employe.id_reference
            WHERE reference.id_reference=%s
            ORDER BY sortie.id_sortie DESC
        """
        cursor.execute(query, (id_ref,))
        result = cursor.fetchall()

        for idx, row in enumerate(result, 1):
            acronym_prenom = make_acronym(row["prenom"])
            acronym_nom = make_acronym(row["nom"])
            response = {
              "count": idx,
                "id_sortie": encryptor("encrypt", str(row["id_sortie"])),
                "prenom": row["prenom"],
                "nom": row["nom"],
                "matricule": f"{acronym_prenom}{acronym_nom}-{row['matricule']}",
                "poste_occupe": row["poste_occupe"],
                "date_sortie": format_date_fr(row["date_sortie"], style="full"),
                "numero": str(row["numero"]).zfill(7),
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
    # === Cas 2: sorties externe par référence ===
    elif "id_sortie_externe" in request.form:
        id_ref = encryptor("decrypt", request.form["id_sortie_externe"])
        query = """
            SELECT * FROM sortie_externe
            INNER JOIN reference ON reference.id_reference=sortie_externe.id_reference
            WHERE reference.id_reference=%s
            ORDER BY sortie_externe.id_sortie_externe DESC
        """
        cursor.execute(query, (id_ref,))
        result = cursor.fetchall()

        for idx, row in enumerate(result, 1):
            acronym_prenom = make_acronym(row["nom_complet_externe"])
            response = {
                "count": idx,
                "id_sortie_externe": encryptor(
                    "encrypt", str(row["id_sortie_externe"])
                ),
                "nom_complet_externe": row["nom_complet_externe"].capitalize(),
                "telephone_externe": row["telephone_externe"],
                "matricule": f"{acronym_prenom}",
                "date_sortie": format_date_fr(row["date_sortie"], style="full"),
                "numero": str(row["numero"]).zfill(7),
                
            }
            data.append(response)

    cursor.close()
    conn.close()
    return jsonify(data)
