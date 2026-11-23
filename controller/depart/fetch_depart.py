from flask import Flask, request, jsonify, url_for, Response
import re
import locale
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
from templates.include.connect import get_connection
from templates.include.encryptor import encryptor
import qrcode
from io import BytesIO
import base64
import json
from decimal import Decimal
from babel.dates import format_date

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


def format_time(time_input):
    if not time_input:
        return ""
    if isinstance(time_input, str):
        try:
            time_obj = datetime.strptime(time_input, "%H:%M:%S").time()
        except ValueError:
            return ""
    elif isinstance(time_input, datetime):
        time_obj = time_input.time()
    elif hasattr(time_input, "hour"):
        time_obj = time_input
    else:
        return ""

    return time_obj.strftime("%H:%M")  # Toujours au bon format


def clean_time(val):
    if val in ["00:00:00", None, ""]:
        return "--:--"
    return format_time(val)


def calculate_duration(start_val, end_val):
    try:
        if not start_val:
            print("Start value is missing.")
            return ""

        # Convertir en date
        if isinstance(start_val, str):
            start = datetime.strptime(start_val, "%Y-%m-%d").date()
        elif isinstance(start_val, (datetime, date)):
            start = start_val
        else:
            return ""

        if isinstance(end_val, str) and end_val.strip():
            end = datetime.strptime(end_val, "%Y-%m-%d").date()
        elif isinstance(end_val, (datetime, date)):
            end = end_val
        else:
            end = date.today()

        # Comparer la date de fin à aujourd'hui
        if end > date.today():
            # Calcule brut comme en PHP
            date1 = datetime.combine(date.today(), datetime.min.time())
            date2 = datetime.combine(end, datetime.min.time())
            diff_seconds = abs((date2 - date1).total_seconds())

            years = int(diff_seconds // (365 * 24 * 60 * 60))
            diff_seconds -= years * 365 * 24 * 60 * 60
            months = int(diff_seconds // (30 * 24 * 60 * 60))
            diff_seconds -= months * 30 * 24 * 60 * 60
            days = int(diff_seconds // (24 * 60 * 60))

            return f"Active : {years} ans {months} mois {days} jours"
        else:
            return "Expire : 0 ans 0 mois 0 jours"

    except Exception as e:
        print("Erreur dans calculate_duration:", e)
        return ""


def acronym_simple(text):
    cleaned = re.sub(r"[`'‘’]", "", text)
    words = cleaned.split()
    return "".join(w[0] for w in words if w)


def format_number(num):
    try:
        if num is None:
            return "0"
        return f"{num:,.0f}".replace(",", " ").replace(".", ",")
    except Exception:
        return "0"


def calculer_age(date_naissance):
    if not date_naissance:
        return ""
    try:
        if isinstance(date_naissance, (datetime, date)):
            today = datetime.today()
            age = (
                today.year
                - date_naissance.year
                - (
                    (today.month, today.day)
                    < (date_naissance.month, date_naissance.day)
                )
            )
            return f"{age} ans"
        else:
            print(f"Type inattendu pour la date : {type(date_naissance)}")
            return ""
    except Exception as e:
        print(f"Erreur lors du calcul de l'âge : {e}")
        return ""


def fetch_depart():
    # Gestion via id_contrat (détail unique)
    if "id_depart" in request.form:
        id_depart_encrypted = request.form["id_depart"]
        id_depart = encryptor("decrypt", id_depart_encrypted)

        conn = get_connection()
        cursor = conn.cursor()
        query = """
            SELECT * FROM depart 
            INNER JOIN contrat ON contrat.id_contrat=depart.id_contrat
            INNER JOIN employe ON employe.id_employe=contrat.id_employe  
            WHERE depart.id_depart= %s
        """
        cursor.execute(query, (id_depart,))
        row = cursor.fetchone()

        if not row:
            cursor.close()
            conn.close()

        columns = [desc[0] for desc in cursor.description]
        row_dict = dict(zip(columns, row))

        data = {
            "id_depart": encryptor("encrypt", str(row_dict.get("id_depart", ""))),
            "date_effet": (
                row_dict.get("date_effet").strftime("%Y-%m-%d")
                if row_dict.get("date_effet")
                else ""
            ),
            "motif": row_dict.get("motif", ""),
            "suspensalaire": row_dict.get("suspensalaire", ""),
            "prenom": row_dict.get("prenom", ""),
            "nom": row_dict.get("nom", ""),
            "photo": (
                url_for(
                    "static",
                    filename=f"img/img_employe/{row_dict.get('matricule','')}/{row_dict.get('photo','')}",
                )
                if row_dict.get("photo")
                else url_for("static", filename="img/image/image-profil.png")
            ),
        }

        cursor.close()
        conn.close()
        print("✅ Contrat récupéré:", data)

        return jsonify(data)

    # Gestion via id (liste des contrats)
    elif "id" in request.form and request.form["id"].strip():
        id_decrypted = encryptor("decrypt", request.form["id"]).strip()

        conn = get_connection()
        cursor = conn.cursor()
        query = """
            SELECT * FROM depart 
                INNER JOIN contrat ON contrat.id_contrat=depart.id_contrat
                INNER JOIN employe ON employe.id_employe=contrat.id_employe
				INNER JOIN reference ON reference.id_reference=employe.id_reference 
                WHERE reference.id_reference=%s
                ORDER BY depart.id_depart DESC
        """
        cursor.execute(query, (id_decrypted,))
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]

        data = []
        for idx, row in enumerate(rows, 1):
            row_dict = dict(zip(columns, row))
            acronym_prenom = acronym_simple(row_dict.get("prenom", ""))
            acronym_nom = acronym_simple(row_dict.get("nom", ""))
            matricule = row_dict.get("matricule", "")
            if not row_dict.get("id_contrat"):
                continue
            response = {
                "count": idx,
                "id_depart": encryptor("encrypt", str(row_dict.get("id_depart", ""))),
                "id_contrat": encryptor("encrypt", str(row_dict.get("id_contrat", ""))),
                "id_depart_raw": row_dict.get("id_depart", ""),
                "id_contrat_raw": row_dict.get("id_contrat", ""),
                "prenom": row_dict.get("prenom", ""),
                "nom": row_dict.get("nom", ""),
                "matricule": f"{acronym_prenom}{acronym_nom}-{matricule}",
                "date_effet": format_date_fr(
                    row_dict.get("date_effet", ""), style="full"
                ),
                "lieu_n": row_dict.get("lieu_n", ""),
                "telephone_e": row_dict.get("telephone_e", ""),
                "adresse_e": row_dict.get("adresse_e", ""),
                "email_e": row_dict.get("email_e", ""),
                "nature": row_dict.get("nature", ""),
                "poste_occupe": row_dict.get("poste_occupe", ""),
                "motif": row_dict.get("motif", ""),
                "suspensalaire": row_dict.get("suspensalaire", ""),
                "nombre_annee": calculate_duration(
                    row_dict.get("date_embauche", ""), row_dict.get("date_sorti", "")
                ),
                "age": calculer_age(row_dict.get("date_n", "")),
                "photo": (
                    url_for(
                        "static",
                        filename=f"img/img_employe/{row_dict.get('matricule','')}/{row_dict.get('photo','')}",
                    )
                    if row_dict.get("photo")
                    else url_for("static", filename="img/image/image-profil.png")
                ),
            }
            data.append(response)

        cursor.close()
        conn.close()
        return jsonify(data)

    else:
        return jsonify({"error": "Paramètre id_contrat ou id manquant"}), 400
