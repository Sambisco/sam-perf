from flask import request, jsonify,url_for
from templates.include.connect import get_connection
from templates.include.encryptor import encryptor
import locale
from datetime import datetime, date, time, timedelta
import re
from babel.dates import format_date

# Assure-toi que la locale française est bien installée sur ton serveur
locale.setlocale(locale.LC_TIME, "fr_FR.UTF-8")


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


def make_json_serializable(obj):
    """
    Convertit récursivement dans obj les objets non JSON-serializables
    (timedelta, datetime, date, time) en chaînes de caractères.
    """
    if isinstance(obj, dict):
        return {k: make_json_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [make_json_serializable(item) for item in obj]
    elif isinstance(obj, timedelta):
        total_seconds = int(obj.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        return f"{hours:02}:{minutes:02}:{seconds:02}"
    elif isinstance(obj, datetime):
        return obj.strftime("%Y-%m-%d %H:%M:%S")
    elif isinstance(obj, date):
        return obj.strftime("%Y-%m-%d")
    elif isinstance(obj, time):
        return obj.strftime("%H:%M:%S")
    else:
        return obj


def suivi_pointage():

    if "id" not in request.form:
        return jsonify({"error": "ID manquant"}), 400

    try:
        id_ref = encryptor("decrypt", request.form["id"])

        query = f"""
            SELECT employe.id_employe, employe.photo, employe.prenom, employe.nom, employe.matricule, contrat.poste_occupe,
                   NULL as id_absence, date, personnel.heure_debut AS heure_debut_personnel,
                   pointage.heure_debut, pointage.heure_fin,
                   NULL AS justification, NULL AS compteur
            FROM contrat
            INNER JOIN employe ON employe.id_employe = contrat.id_employe
            INNER JOIN pointage ON contrat.id_contrat = pointage.id_contrat
            INNER JOIN personnel ON contrat.id_contrat = personnel.id_contrat
            INNER JOIN reference ON reference.id_reference = employe.id_reference
            WHERE reference.id_reference = %s

            UNION

            SELECT employe.id_employe, employe.photo, employe.prenom, employe.nom, employe.matricule, contrat.poste_occupe,
                   id_absence, date, NULL, NULL, NULL, justification, compteur
            FROM contrat
            INNER JOIN employe ON employe.id_employe = contrat.id_employe
            INNER JOIN absence ON contrat.id_contrat = absence.id_contrat
            INNER JOIN reference ON reference.id_reference = employe.id_reference
            WHERE reference.id_reference = %s

            ORDER BY date DESC
        """

        with get_connection() as conn:
            with conn.cursor(dictionary=True) as cursor:
                cursor.execute(query, (id_ref, id_ref))
                rows = cursor.fetchall()

        data = []
        count = 0
        re_apostrophe = re.compile(r"\b\w[\'`‘’]\b", re.UNICODE)

        def format_time(value):
            if value is None:
                return "00:00:00"
            if isinstance(value, (time, datetime)):
                return value.strftime("%H:%M:%S")
            if isinstance(value, timedelta):
                total_seconds = int(value.total_seconds())
                hours = total_seconds // 3600
                minutes = (total_seconds % 3600) // 60
                seconds = total_seconds % 60
                return f"{hours:02}:{minutes:02}:{seconds:02}"
            return str(value)

        for row in rows:
            count += 1

            # Abréviation prénom
            code_prenom = re_apostrophe.sub("", row["prenom"] or "")
            acronym_prenom = "".join([w[0] for w in code_prenom.split() if w])

            # Abréviation nom
            code_nom = re_apostrophe.sub("", row["nom"] or "")
            acronym_nom = "".join([w[0] for w in code_nom.split() if w])

            full_matricule = f"{acronym_prenom}{acronym_nom}-{row['matricule']}"

            if row["justification"] is None or row["justification"] == "":
                    justification = "Pas de motif"
            else:
                     justification = row["justification"]

            heure_debut = format_time(row.get("heure_debut"))
            heure_fin = format_time(row.get("heure_fin"))

            if row["heure_debut"] is None:
                pointe = "<span style='color:red;background:rgba(255,0,0,0.1);padding:7px;border-radius:5px;'><strong>Absence</strong></span>"
            elif row["heure_debut"] > row["heure_debut_personnel"]:
                pointe = "<span style='color:#8b8000;background:rgba(139,128,0,0.1);padding:7px;border-radius:5px;'><strong>Retard</strong></span>"
            elif row["heure_debut"] <= row["heure_debut_personnel"]:
                pointe = "<span style='color:green;background:rgba(11,156,49,0.1);padding:7px;border-radius:5px;'><strong>A l'heure</strong></span>"
            else:
                pointe = ""

            response = {
                "count": count,
                "prenom": row["prenom"],
                "nom": row["nom"],
                "matricule": full_matricule,
                "poste_occupe": row["poste_occupe"],
                "date": format_date_fr(row.get("date"),style="full"),
                "justification": justification,
                "heure_debut": heure_debut,
                "heure_fin": heure_fin,
                "pointe": pointe,
                "photo": (
                    (
                        url_for(
                            "static",
                            filename=f"img/img_employe/{row.get('matricule','')}/{row.get('photo','')}",
                        )
                        if row.get("photo")
                        else url_for("static", filename="img/image/image-profil.png")
                    ),
                ),
            }

            data.append(response)

        data_serializable = make_json_serializable(data)
        return jsonify(data_serializable)

    except Exception as e:
        return jsonify({"error": str(e)}), 500
