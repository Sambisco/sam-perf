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
        elif style == "years":
            fmt = "yyyy"
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


def calculate_duration_actif(start_val, end_val):
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


def calculate_duration(start_val, end_val):
    try:
        # Vérifier et convertir la date de début
        if not start_val:
            return ""

        if isinstance(start_val, str):
            start = datetime.strptime(start_val.strip(), "%Y-%m-%d").date()
        elif isinstance(start_val, (datetime, date)):
            start = start_val
        else:
            return ""

        today = date.today()

        # Si la date de début est dans le futur
        if start > today:
            return "Pas encore active"

        # Vérifier et convertir la date de fin
        if isinstance(end_val, str) and end_val.strip():
            end = datetime.strptime(end_val.strip(), "%Y-%m-%d").date()
        elif isinstance(end_val, (datetime, date)):
            end = end_val
        else:
            end = today

        # Si la date de fin est aujourd’hui ou passée
        if end <= today:
            return "Expire : 0 jours"

        # Calcul du nombre de jours
        delta = (end - today).days
        delta -= 1 if delta > 0 else 0

        return f"Expire : {delta} jours"

    except Exception as e:
        print("Erreur dans calculate_duration_actif:", e)
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


def fetch_conge_maternite():
    # Gestion via id_contrat (détail unique)
    if "id_conge_maternite" in request.form:
        id_conge_maternite_encrypted = request.form["id_conge_maternite"]
        id_conge_maternite = encryptor("decrypt", id_conge_maternite_encrypted)

        conn = get_connection()
        cursor = conn.cursor()
        query = """
                SELECT * FROM conge_maternite
                    INNER JOIN contrat ON contrat.id_contrat=conge_maternite.id_contrat
                    INNER JOIN employe ON employe.id_employe=contrat.id_employe
                    INNER JOIN reference ON reference.id_reference=employe.id_reference
                    WHERE conge_maternite.id_conge_maternite= %s
                """
        cursor.execute(query, (id_conge_maternite,))
        row = cursor.fetchone()

        if not row:
            cursor.close()
            conn.close()

        columns = [desc[0] for desc in cursor.description]
        row_dict = dict(zip(columns, row))

        data = {
            "id_conge_maternite": encryptor(
                "encrypt", str(row_dict.get("id_conge_maternite", ""))
            ),
            "id_contrat": encryptor("encrypt", str(row_dict.get("id_contrat", ""))),
            "prenom": row_dict.get("prenom", ""),
            "nom": row_dict.get("nom", ""),
            "poste_occupe": row_dict.get("poste_occupe", ""),
            "numero_decision": row_dict.get("numero_decision", ""),
            "date_decision": (
                row_dict.get("date_decision").strftime("%Y-%m-%d")
                if row_dict.get("date_decision")
                else ""
            ),
            "date_suspension": (
                row_dict.get("date_suspension").strftime("%Y-%m-%d")
                if row_dict.get("date_suspension")
                else ""
            ),
            "date_debut": (
                row_dict.get("date_debut").strftime("%Y-%m-%d")
                if row_dict.get("date_debut")
                else ""
            ),
            "date_fin": (
                row_dict.get("date_fin").strftime("%Y-%m-%d")
                if row_dict.get("date_fin")
                else ""
            ),
            "date_reprise": (
                row_dict.get("date_reprise").strftime("%Y-%m-%d")
                if row_dict.get("date_reprise")
                else ""
            ),
            "docteur": row_dict.get("docteur", ""),
            "nbr_week": row_dict.get("nbr_week", ""),
            "document_cessation": row_dict.get("document_cessation", ""),
            "document_attestation": row_dict.get("document_attestation", ""),
            "document_decision": row_dict.get("document_decision", ""),
            "document_transmission": row_dict.get("document_transmission", ""),
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
           SELECT * FROM conge_maternite
                INNER JOIN contrat ON contrat.id_contrat=conge_maternite.id_contrat
                INNER JOIN employe ON employe.id_employe=contrat.id_employe
				INNER JOIN reference ON reference.id_reference=employe.id_reference 
                WHERE reference.id_reference = %s
                ORDER BY conge_maternite.id_conge_maternite DESC
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
                "id_conge_maternite": encryptor(
                    "encrypt", str(row_dict.get("id_conge_maternite", ""))
                ),
                "id_conge_maternite_raw": row_dict.get("id_conge_maternite", ""),
                "prenom": row_dict.get("prenom", ""),
                "nom": row_dict.get("nom", ""),
                "matricule": f"{acronym_prenom}{acronym_nom}-{matricule}",
                "date_n": format_date_fr(row_dict.get("date_n", ""), "%d %B %Y"),
                "lieu_n": row_dict.get("lieu_n", ""),
                "telephone_e": row_dict.get("telephone_e", ""),
                "adresse_e": row_dict.get("adresse_e", ""),
                "nature": row_dict.get("nature", ""),
                "poste_occupe": row_dict.get("poste_occupe", ""),
                "numero_decision": row_dict.get("numero_decision", ""),
                "date_decision": format_date_fr(
                    row_dict.get("date_decision", ""), style="full"
                ),
                "date_suspension": format_date_fr(
                    row_dict.get("date_suspension", ""), style="full"
                ),
                "date_debut": format_date_fr(
                    row_dict.get("date_debut", ""), style="full"
                ),
                "date_fin": format_date_fr(row_dict.get("date_fin", ""), style="full"),
                "date_reprise": format_date_fr(
                    row_dict.get("date_reprise", ""), style="full"
                ),
                "nombre_jours": calculate_duration(
                    row_dict.get("date_debut", ""), row_dict.get("date_fin", "")
                ),
                "docteur": row_dict.get("docteur", ""),
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

    elif "paie_conge_maternite" in request.form:
        id_reference = encryptor("decrypt", request.form["paie_conge_maternite"])

        query = """
        SELECT * FROM conge_maternite
        INNER JOIN contrat ON contrat.id_contrat=conge_maternite.id_contrat
        INNER JOIN employe ON employe.id_employe=contrat.id_employe
		INNER JOIN reference ON reference.id_reference=employe.id_reference 
        WHERE reference.id_reference = %s
        ORDER BY conge_maternite.id_conge_maternite DESC
        """

        data = []
        count = 0

        with get_connection() as conn:
            with conn.cursor(dictionary=True) as cursor:
                cursor.execute(query, (id_reference,))
                rows = cursor.fetchall()

                for row in rows:
                    if row["paye_conge_maternite"] == 0:
                        count += 1

                        # Traitement prénom
                        acronym_prenom = acronym_simple(row.get("prenom", ""))
                        acronym_nom = acronym_simple(row.get("nom", ""))
                        matricule = row.get("matricule", "")

                        response = {
                            "count": count,
                            "id_conge_maternite": encryptor(
                                "encrypt", str(row.get("id_conge_maternite", ""))
                            ),
                            "id_conge_maternite_raw": row.get(
                                "id_conge_maternite", ""
                            ),
                            "prenom": row.get("prenom", ""),
                            "nom": row.get("nom", ""),
                            "matricule": f"{acronym_prenom}{acronym_nom}-{matricule}",
                            "date_n": format_date_fr(
                                row.get("date_n", ""), "%d %B %Y"
                            ),
                            "lieu_n": row.get("lieu_n", ""),
                            "telephone_e": row.get("telephone_e", ""),
                            "adresse_e": row.get("adresse_e", ""),
                            "nature": row.get("nature", ""),
                            "poste_occupe": row.get("poste_occupe", ""),
                            "date_decision": format_date_fr(
                                row.get("date_decision", ""), style="full"
                            ),
                            "date_suspension": format_date_fr(
                                row.get("date_suspension", ""), style="full"
                            ),
                            "date_debut": format_date_fr(
                                row.get("date_debut", ""), style="full"
                            ),
                            "date_fin": format_date_fr(
                                row.get("date_fin", ""), style="full"
                            ),
                            "date_reprise": format_date_fr(
                                row.get("date_reprise", ""), style="full"
                            ),
                            "nombre_jours": calculate_duration(
                                row.get("date_debut", ""),
                                row.get("date_fin", ""),
                            ),
                            "photo": (
                                url_for(
                                    "static",
                                    filename=f"img/img_employe/{row.get('matricule','')}/{row.get('photo','')}",
                                )
                                if row.get("photo")
                                else url_for(
                                    "static", filename="img/image/image-profil.png"
                                )
                            ),
                        }

                        data.append(response)

        return jsonify(data)

    else:
        return jsonify({"error": "Paramètre id_contrat ou id manquant"}), 400
