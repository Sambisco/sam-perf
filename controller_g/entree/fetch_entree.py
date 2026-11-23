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


def fetch_entree():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    data = []

    if "id_entree" in request.form:
        id_entree = encryptor("decrypt", request.form["id_entree"])
        query = """
            SELECT * FROM detail_entree
            INNER JOIN entree ON entree.id_entree = detail_entree.id_entree
            INNER JOIN matiere ON matiere.id_matiere = detail_entree.id_matiere
            WHERE entree.id_entree = %s
        """
        cursor.execute(query, (id_entree,))
        result = cursor.fetchall()

        for row in result:
            response = {}

            # pv_entree
            cursor.execute(
                """
                SELECT * FROM pv_entree
                INNER JOIN entree ON entree.id_entree = pv_entree.id_entree
                WHERE entree.id_entree = %s
            """,
                (id_entree,),
            )
            pv = cursor.fetchone()
            if pv is None or pv.get("id_fournisseur") is None:
                response["id_fournisseur"] = ""
            else:
                response["id_fournisseur"] = encryptor("encrypt", str(pv["id_fournisseur"]))

            response["id_entree"] = encryptor("encrypt", str(row["id_entree"]))
            response["total"] = row["total"]

            if row["pverbal"]:
                response["checked"] = True
                response["pv"] = "P.V"
            else:
                response["checked"] = ""
                response["pv"] = "Neant"

            response["pverbal"] = row["pverbal"]
            response["image"] = url_for(
                "static",
                filename=(
                    f"img/matiere/{row['image']}"
                    if row["image"]
                    else "img/image/image.jpg"
                ),
            )

            response["id_matiere"] = encryptor("encrypt", str(row["id_matiere"]))
            response["id_matiere_raw"] = row["id_matiere"]
            response["numero"] = str(row["numero"]).zfill(7)
            response["numero_bon"] = row["numero_bon"]
            response["date_entree"] = (
                row["date_entree"].strftime("%Y-%m-%d") if row["date_entree"] else ""
            )
            response["designation"] = row["designation"]
            response["prix_unitaire"] = row["prix_unitaire"]
            response["quantite"] = row["quantite"]
            response["total_entree"] = row["total_entree"]
            response["observation"] = row["observation"]
            response["nbre_unite"] = row["nbre_unite"]

            data.append(response)

    elif "id" in request.form:
        id_ref = encryptor("decrypt", request.form["id"])
        query = """
            SELECT * FROM entree
        INNER JOIN reference ON reference.id_reference = entree.id_reference
            WHERE reference.id_reference = %s
            ORDER BY entree.id_entree DESC
        """
        cursor.execute(query, (id_ref,))
        result = cursor.fetchall()

        for idx, row in enumerate(result, 1):
            id_entree =row["id_entree"]
            # pv_entree
            cursor.execute(
                """
                SELECT * FROM pv_entree
                INNER JOIN entree ON entree.id_entree = pv_entree.id_entree
                INNER JOIN fournisseur ON fournisseur.id_fournisseur=pv_entree.id_fournisseur
                WHERE entree.id_entree = %s
            """,
                (id_entree,),
            )
            pv = cursor.fetchone()

            response = {}

            if pv is None or pv.get("id_fournisseur") is None:
                response["fournisseur"] = "Pas de Fournisseur"
                response["nom_contact_f"] = "Pas de contact"
            else:
                response["fournisseur"] = pv["fournisseur"]
                response["nom_contact_f"] = pv["nom_contact_f"]
            response["count"] = idx
            response["id_entree"] = encryptor("encrypt", str(row["id_entree"]))
            response["date_entree"] = format_date_fr(row["date_entree"], style="full")
            response["numero"] = str(row["numero"]).zfill(7)
            response["numero_bon"] = row["numero_bon"]
            response["total"] = row["total"]
            response["pverbal"] = "P.V" if row["pverbal"] else "B.E"
            response["pverbal_display"] = (
                "display: block;" if row["pverbal"] else "display: none;"
            )

            data.append(response)

    else:
        return jsonify({"error": "Paramètre invalide"})

    cursor.close()
    conn.close()
    return jsonify(data)
