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
        
         # Cas "Pas encore active" si la date de début est future

        if start > date.today():
            return "Pas encore active"
        
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

            return f" {years} ans {months} mois {days} jours"
        else:
            return " 0 ans 0 mois 0 jours"

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


def generate_qr_code(data):
    qr = qrcode.QRCode(version=1, box_size=10, border=2)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill="black", back_color="white")
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return "data:image/png;base64," + img_str


def fetch_contrat():
    # Gestion via id_contrat (détail unique)
    if "id_contrat" in request.form:
        id_contrat_encrypted = request.form["id_contrat"]
        id_contrat = encryptor("decrypt", id_contrat_encrypted)

        conn = get_connection()
        cursor = conn.cursor()
        query = """
            SELECT * FROM contrat
            INNER JOIN personnel ON contrat.id_contrat = personnel.id_contrat
            INNER JOIN employe ON employe.id_employe = contrat.id_employe
            INNER JOIN reference ON reference.id_reference = employe.id_reference
            WHERE contrat.id_contrat = %s
        """
        cursor.execute(query, (id_contrat,))
        row = cursor.fetchone()

        if not row:
            cursor.close()
            conn.close()

        columns = [desc[0] for desc in cursor.description]
        row_dict = dict(zip(columns, row))

        data = {
            "id_contrat": encryptor("encrypt", str(row_dict.get("id_contrat", ""))),
            "id_employe": encryptor("encrypt", str(row_dict.get("id_employe", ""))),
            "prenom": row_dict.get("prenom", ""),
            "nom": row_dict.get("nom", ""),
            "poste": row_dict.get("poste", ""),
            "telephone_e": row_dict.get("telephone_e", ""),
            "adresse_e": row_dict.get("adresse_e", ""),
            "cin_e": row_dict.get("cin_e", ""),
            "nationalite": row_dict.get("nationalite", ""),
            "nom_pere": row_dict.get("nom_pere", ""),
            "nom_mere": row_dict.get("nom_mere", ""),
            "email_e": row_dict.get("email_e", ""),
            "nature": row_dict.get("nature", ""),
            "poste_occupe": row_dict.get("poste_occupe", ""),
            "date_embauche": (
                row_dict.get("date_embauche").strftime("%Y-%m-%d")
                if row_dict.get("date_embauche")
                else ""
            ),
            "date_sorti": (
                row_dict.get("date_sorti").strftime("%Y-%m-%d")
                if row_dict.get("date_sorti")
                else ""
            ),
            "id_categorie": row_dict.get("categorie", ""),
            "situation_matr": row_dict.get("situation_matr", ""),
            "conjoint": row_dict.get("conjoint", ""),
            "enfant": row_dict.get("enfant", 0),
            "heure": row_dict.get("heure", ""),
            "salaire": format_number(row_dict.get("salaire", 0)),
            "nb_trimf": row_dict.get("nb_trimf", 0),
            "nb_irpp": row_dict.get("nb_irpp", 0),
            "fonction": format_number(row_dict.get("fonction", 0)),
            "sujetion": format_number(row_dict.get("sujetion", 0)),
            "responsabilite": format_number(row_dict.get("responsabilite", 0)),
            "sursalaire": format_number(row_dict.get("sursalaire", 0)),
            "logement": format_number(row_dict.get("logement", 0)),
            "autre_indemnite": format_number(row_dict.get("autre_indemnite", 0)),
            "transport": format_number(row_dict.get("transport", 0)),
            "telephone_in": format_number(row_dict.get("telephone_in", 0)),
            "id_personnel": (
                encryptor("encrypt", str(row_dict.get("id_personnel", "")))
                if row_dict.get("id_personnel")
                else ""
            ),
            "id_departement": (
                ""
                if row_dict.get("id_departement", 0) == 0
                else row_dict.get("id_departement", "")
            ),
            "id_region": (
                ""
                if row_dict.get("id_region", 0) == 0
                else row_dict.get("id_region", "")
            ),
            "heure_debut": (
                ""
                if row_dict.get("heure_debut") in ["00:00:00", None, ""]
                else format_time(str(row_dict.get("heure_debut")))
            ),
            "heure_decente": (
                ""
                if row_dict.get("heure_decente") in ["00:00:00", None, ""]
                else format_time(str(row_dict.get("heure_decente")))
            ),
            "document_lettre": row_dict.get("document_lettre", ""),
            "nombre_annee": calculate_duration(
                row_dict.get("date_embauche", ""), row_dict.get("date_sorti", "")
            ),
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
            SELECT * FROM contrat
            INNER JOIN employe ON employe.id_employe = contrat.id_employe
            INNER JOIN reference ON reference.id_reference = employe.id_reference
            WHERE reference.id_reference = %s
            ORDER BY contrat.id_contrat DESC
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
                "id_contrat": encryptor("encrypt", str(row_dict.get("id_contrat", ""))),
                "id_contrat_raw": row_dict.get("id_contrat", ""),
                "prenom": row_dict.get("prenom", ""),
                "nom": row_dict.get("nom", ""),
                "matricule": f"{acronym_prenom}{acronym_nom}-{matricule}",
                "date_n": format_date_fr(row_dict.get("date_n", ""), style="long"),
                "lieu_n": row_dict.get("lieu_n", ""),
                "telephone_e": row_dict.get("telephone_e", ""),
                "adresse_e": row_dict.get("adresse_e", ""),
                "nature": row_dict.get("nature", ""),
                "poste_occupe": row_dict.get("poste_occupe", ""),
                "date_embauche": format_date_fr(
                    row_dict.get("date_embauche", ""), style="full"
                ),
                "date_sorti": format_date_fr(
                    row_dict.get("date_sorti", ""), style="full"
                ),
                "salaire": format_number(row_dict.get("salaire", 0)),
                "situation_matr": row_dict.get("situation_matr", ""),
                "conjoint": row_dict.get("conjoint", ""),
                "enfant": row_dict.get("enfant", 0),
                "nb_irpp": row_dict.get("nb_irpp", 0),
                "nb_trimf": row_dict.get("nb_trimf", 0),
                "genre": row_dict.get("genre", "") or "",
                "nombre_annee": calculate_duration_actif(
                    row_dict.get("date_embauche", ""), row_dict.get("date_sorti", "")
                ),
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
    elif "id_qrcode" in request.form :
        id_qrcode_encrypted = request.form["id_qrcode"]
        id_qrcode = encryptor("decrypt", id_qrcode_encrypted)

        conn = get_connection()
        cursor = conn.cursor()
        query = """
            SELECT * FROM contrat
            INNER JOIN personnel ON contrat.id_contrat = personnel.id_contrat
            INNER JOIN employe ON employe.id_employe = contrat.id_employe
            INNER JOIN reference ON reference.id_reference = employe.id_reference
            WHERE contrat.id_contrat = %s
        """
        cursor.execute(query, (id_qrcode,))
        row = cursor.fetchone()

        if not row:
            cursor.close()
            conn.close()
            return jsonify({})

        columns = [desc[0] for desc in cursor.description]
        row_dict = dict(zip(columns, row))
        acronym_prenom = acronym_simple(row_dict.get("prenom", ""))
        acronym_nom = acronym_simple(row_dict.get("nom", ""))
        matricule = row_dict.get("matricule", "")

        data = {
            "id_contrat": encryptor("encrypt", str(row_dict.get("id_contrat", ""))),
            "prenom": row_dict.get("prenom", ""),
            "nom": row_dict.get("nom", ""),
            "matricule": f"{acronym_prenom}{acronym_nom}-{matricule}",
            "photo_qr": generate_qr_code(
                encryptor("encrypt", str(row_dict.get("id_contrat", "")))
            ),
        }
        cursor.close()
        conn.close()
        print("✅ Contrat récupéré:", data)

        return jsonify(data)

    elif "indemnite" in request.form:
        id_decrypted = encryptor("decrypt", request.form["indemnite"]).strip()

        conn = get_connection()
        cursor = conn.cursor()
        query = """
            SELECT * FROM contrat
            INNER JOIN employe ON employe.id_employe = contrat.id_employe
            INNER JOIN reference ON reference.id_reference = employe.id_reference
            WHERE reference.id_reference = %s
            ORDER BY contrat.id_contrat DESC
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
                "id_contrat": encryptor("encrypt", str(row_dict.get("id_contrat", ""))),
                "id_contrat_raw": row_dict.get("id_contrat", ""),
                "prenom": row_dict["prenom"],
                "nom": row_dict["nom"],
                "matricule": f"{acronym_prenom}{acronym_nom}-{matricule}",
                "date_n": format_date_fr(row_dict.get("date_n"), "%d %B %Y"),
                "lieu_n": row_dict.get("lieu_n", ""),
                "telephone_e": row_dict.get("telephone_e", ""),
                "date_embauche": format_date_fr(
                    row_dict.get("date_embauche", ""), style="full"
                ),
                "date_sorti": format_date_fr(
                    row_dict.get("date_sorti", ""), style="full"
                ),
                "categorie": row_dict.get("categorie", ""),
                "poste_occupe": row_dict.get("poste_occupe", ""),
                "nature": row_dict.get("nature", ""),
                "situation_matr": row_dict.get("situation_matr", ""),
                "conjoint": row_dict.get("conjoint", ""),
                "nb_trimf": row_dict.get("nb_trimf", 0),
                "nb_irpp": row_dict.get("nb_irpp", 0),
                "enfant": row_dict.get("enfant", 0),
                "fonction": format_number(row_dict.get("fonction")),
                "sujetion": format_number(row_dict.get("sujetion")),
                "responsabilite": format_number(row_dict.get("responsabilite")),
                "sursalaire": format_number(row_dict.get("sursalaire")),
                "logement": format_number(row_dict.get("logement")),
                "transport": format_number(row_dict.get("transport")),
                "telephone_in": format_number(row_dict.get("telephone_in")),
                "autre_indemnite": format_number(row_dict.get("autre_indemnite")),
                "nombre_annee": calculate_duration_actif(
                    row_dict.get("date_embauche", ""), row_dict.get("date_sorti", "")
                ),
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

    elif "personnel" in request.form:
        id_decrypted = encryptor("decrypt", request.form["personnel"]).strip()

        conn = get_connection()
        cursor = conn.cursor()
        query = """
           SELECT * FROM contrat 
           INNER JOIN employe ON employe.id_employe=contrat.id_employe 
           INNER JOIN reference ON reference.id_reference=employe.id_reference 
           INNER JOIN personnel ON contrat.id_contrat=personnel.id_contrat
           INNER JOIN departement ON departement.id_departement=personnel.id_departement
           INNER JOIN region ON region.id_region=personnel.id_region
            WHERE reference.id_reference = %s
            ORDER BY contrat.id_contrat DESC
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
                "id_contrat": encryptor("encrypt", str(row_dict["id_contrat"])),
                "prenom": row_dict["prenom"],
                "nom": row_dict["nom"],
                "matricule": f"{acronym_prenom}{acronym_nom}-{matricule}",
                "date_n": format_date_fr(row_dict.get("date_n"), style="long"),
                "lieu_n": row_dict.get("lieu_n", ""),
                "telephone_e": row_dict.get("telephone_e", ""),
                "categorie": row_dict.get("categorie", ""),
                "poste_occupe": row_dict.get("poste_occupe", ""),
                "nom_departement": row_dict.get("nom_departement", ""),
                "region": row_dict.get("region", ""),
                "heure_debut": (
                    ""
                    if row_dict.get("heure_debut") in ["00:00:00", None, ""]
                    else format_time(str(row_dict.get("heure_debut")))
                ),
                "heure_decente": (
                    ""
                    if row_dict.get("heure_decente") in ["00:00:00", None, ""]
                    else format_time(str(row_dict.get("heure_decente")))
                ),
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

    elif "dmt" in request.form:
        id_decrypted = encryptor("decrypt", request.form["dmt"]).strip()

        conn = get_connection()
        cursor = conn.cursor()
        query = """
          SELECT * FROM contrat 
		 INNER JOIN employe ON employe.id_employe=contrat.id_employe 
		  INNER JOIN reference ON reference.id_reference=employe.id_reference 
		   WHERE NOT EXISTS (SELECT * FROM dmt WHERE contrat.id_contrat = dmt.id_contrat) AND reference.id_reference=%s
		 ORDER BY contrat.id_contrat DESC
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
                "id_contrat": encryptor("encrypt", str(row_dict["id_contrat"])),
                "id_contrat_raw": row_dict.get("id_contrat", ""),
                "prenom": row_dict["prenom"],
                "nom": row_dict["nom"],
                "matricule": f"{acronym_prenom}{acronym_nom}-{matricule}",
                "date_n": format_date_fr(row_dict.get("date_n"), style="full"),
                "lieu_n": row_dict.get("lieu_n", ""),
                "adresse_e": row_dict.get("adresse_e", ""),
                "telephone_e": row_dict.get("telephone_e", ""),
                "email_e": row_dict.get("email_e", ""),
                "categorie": row_dict.get("categorie", ""),
                "poste_occupe": row_dict.get("poste_occupe", ""),
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

    elif "employe_actif" in request.form:
        id_decrypted = encryptor("decrypt", request.form["employe_actif"]).strip()

        conn = get_connection()
        cursor = conn.cursor()
        query = """
         SELECT * FROM contrat 
		 INNER JOIN employe ON employe.id_employe=contrat.id_employe 
		  INNER JOIN reference ON reference.id_reference=employe.id_reference 
		   WHERE NOT EXISTS (SELECT * FROM depart WHERE contrat.id_contrat = depart.id_contrat) AND reference.id_reference=%s
		 ORDER BY employe.id_employe DESC
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
            age_fr = ""
            date_n_str = row_dict.get("date_n", "")
            try:
                if date_n_str:
                    date_n = datetime.strptime(date_n_str, '%Y-%m-%d')
                    today = datetime.today()
                    age = today.year - date_n.year - ((today.month, today.day) < (date_n.month, date_n.day))
                    age_fr = f"{age} ans"
            except Exception as e:
                print(f"Erreur lors du calcul de l'âge : {e}")
                age_fr = ""
            print("Valeur brute de date_n :", row_dict.get("date_n"))

            response = {
                "count": idx,
                "id_employe": encryptor("encrypt", str(row_dict["id_employe"])),
                "id_contrat": encryptor("encrypt", str(row_dict["id_contrat"])),
                "id_contrat_raw": row_dict.get("id_contrat", ""),
                "id_employe_raw": row_dict.get("id_employe"),
                "prenom": row_dict["prenom"],
                "nom": row_dict["nom"],
                "matricule": f"{acronym_prenom}{acronym_nom}-{matricule}",
                "date_n": format_date_fr(row_dict.get("date_n"), style="long"),
                "lieu_n": row_dict.get("lieu_n", ""),
                "adresse_e": row_dict.get("adresse_e", ""),
                "telephone_e": row_dict.get("telephone_e", ""),
                "email_e": row_dict.get("email_e", ""),
                "date_embauche": format_date_fr(
                    row_dict.get("date_embauche", ""), style="full"
                ),
                "date_sorti": format_date_fr(
                    row_dict.get("date_sorti", ""), style="full"
                ),
                "categorie": row_dict.get("categorie", ""),
                "poste_occupe": row_dict.get("poste_occupe", ""),
                "genre": row_dict.get("genre", ""),
                "photo": (
                    url_for(
                        "static",
                        filename=f"img/img_employe/{row_dict.get('matricule','')}/{row_dict.get('photo','')}",
                    )
                    if row_dict.get("photo")
                    else url_for("static", filename="img/image/image-profil.png")
                ),
                "age": calculer_age(row_dict.get("date_n", "")),
            }
            data.append(response)

        cursor.close()
        conn.close()
        return jsonify(data)

    elif "employe_actif_conge_maternite" in request.form:
        id_decrypted = encryptor(
            "decrypt", request.form["employe_actif_conge_maternite"]
        ).strip()

        conn = get_connection()
        cursor = conn.cursor()
        query = """
         SELECT * FROM contrat 
		 INNER JOIN employe ON employe.id_employe=contrat.id_employe 
		  INNER JOIN reference ON reference.id_reference=employe.id_reference 
		   WHERE NOT EXISTS (SELECT * FROM depart WHERE contrat.id_contrat = depart.id_contrat) AND reference.id_reference=%s AND genre='Feminin'
		 ORDER BY employe.id_employe DESC
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
            age_fr = ""
            date_n_str = row_dict.get("date_n", "")
            try:
                if date_n_str:
                    date_n = datetime.strptime(date_n_str, "%Y-%m-%d")
                    today = datetime.today()
                    age = (
                        today.year
                        - date_n.year
                        - ((today.month, today.day) < (date_n.month, date_n.day))
                    )
                    age_fr = f"{age} ans"
            except Exception as e:
                print(f"Erreur lors du calcul de l'âge : {e}")
                age_fr = ""
            print("Valeur brute de date_n :", row_dict.get("date_n"))

            response = {
                "count": idx,
                "id_employe": encryptor("encrypt", str(row_dict["id_employe"])),
                "id_contrat": encryptor("encrypt", str(row_dict["id_contrat"])),
                "id_contrat_raw": row_dict.get("id_contrat", ""),
                "prenom": row_dict["prenom"],
                "nom": row_dict["nom"],
                "matricule": f"{acronym_prenom}{acronym_nom}-{matricule}",
                "date_n": format_date_fr(row_dict.get("date_n"), "%d %B %Y"),
                "lieu_n": row_dict.get("lieu_n", ""),
                "adresse_e": row_dict.get("adresse_e", ""),
                "telephone_e": row_dict.get("telephone_e", ""),
                "email_e": row_dict.get("email_e", ""),
                "date_embauche": format_date_fr(
                    row_dict.get("date_embauche", ""), "%A %d %B %Y"
                ),
                "date_sorti": format_date_fr(
                    row_dict.get("date_sorti", ""), "%A %d %B %Y"
                ),
                "categorie": row_dict.get("categorie", ""),
                "poste_occupe": row_dict.get("poste_occupe", ""),
                "genre": row_dict.get("genre", ""),
                "photo": (
                    url_for(
                        "static",
                        filename=f"img/img_employe/{row_dict.get('matricule','')}/{row_dict.get('photo','')}",
                    )
                    if row_dict.get("photo")
                    else url_for("static", filename="img/image/image-profil.png")
                ),
                "age": calculer_age(row_dict.get("date_n", "")),
            }
            data.append(response)

        cursor.close()
        conn.close()
        return jsonify(data)

    elif "number_employe_masculin" in request.form:

        try:
            # Décrypter l'ID
            id_decrypted = encryptor(
               "decrypt", request.form["number_employe_masculin"]
           ).strip()

            conn = get_connection()
            cursor = conn.cursor(dictionary=True)  # ✅ Important pour récupérer un dict

            query = """
               SELECT COUNT(*) AS nbr_masculin 
               FROM contrat 
               INNER JOIN employe ON employe.id_employe = contrat.id_employe
               INNER JOIN reference ON reference.id_reference = employe.id_reference
               WHERE NOT EXISTS (
                   SELECT * FROM depart WHERE contrat.id_contrat = depart.id_contrat
               )
               AND reference.id_reference = %s
               AND genre = 'Masculin'
           """

            # ✅ On exécute la requête AVANT d'appeler fetchone()
            cursor.execute(query, (id_decrypted,))
            result = cursor.fetchone()

            # ✅ Si aucun résultat trouvé, on met 0
            data = {"nbr_masculin": result["nbr_masculin"] if result else 0}

            cursor.close()
            conn.close()

            return jsonify(data)

        except Exception as e:
            print(f"❌ Erreur fetch_contrat_masculin: {e}")
            return jsonify({"error": str(e)}), 500

    elif "number_employe_feminin" in request.form:
        try:
            # Décrypter l'ID
            id_decrypted = encryptor(
                "decrypt", request.form["number_employe_feminin"]
            ).strip()

            conn = get_connection()
            cursor = conn.cursor(dictionary=True)  # ✅ Important pour récupérer un dict

            query = """
               SELECT COUNT(*) AS nbr_feminin FROM contrat 
		 INNER JOIN employe ON employe.id_employe=contrat.id_employe 
		  INNER JOIN reference ON reference.id_reference=employe.id_reference 
		   WHERE NOT EXISTS (SELECT * FROM depart WHERE contrat.id_contrat = depart.id_contrat) AND reference.id_reference=%s AND genre='Feminin'
		 ORDER BY employe.id_employe DESC
           """

            # ✅ On exécute la requête AVANT d'appeler fetchone()
            cursor.execute(query, (id_decrypted,))
            result = cursor.fetchone()

            # ✅ Si aucun résultat trouvé, on met 0
            data = {"nbr_feminin": result["nbr_feminin"] if result else 0}

            cursor.close()
            conn.close()

            return jsonify(data)

        except Exception as e:
            print(f"❌ Erreur fetch_contrat_masculin: {e}")
            return jsonify({"error": str(e)}), 500

    elif "id_contrat_absence" in request.form:
        try:
            # Décrypter l'ID
            id_decrypted = encryptor(
                "decrypt", request.form["id_contrat_absence"]
            ).strip()

            conn = get_connection()
            cursor = conn.cursor(dictionary=True)  # ✅ Important pour récupérer un dict

            annee_en_cours = datetime.now().year

            query = """
                SELECT *,contrat.id_contrat, COUNT(id_absence) AS nbr_jour FROM contrat
                INNER JOIN employe ON employe.id_employe = contrat.id_employe 
                INNER JOIN absence ON contrat.id_contrat = absence.id_contrat 
                WHERE contrat.id_contrat = %s AND YEAR(absence.date) = %s
            """

            conn = get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(query, (id_decrypted, annee_en_cours))
            result = cursor.fetchall()
            data = {}

            for row in result:
                data["id_contrat"]= encryptor("encrypt", str(row.get("id_contrat", "")))
                data["prenom"] = row.get("prenom")
                data["nom"] = row.get("nom")
                data["nbr_jour"] = row["nbr_jour"]
                if row["genre"] == "Masculin":
                    data["nbr_enfant"] = "0"
                else:
                    data["nbr_enfant"] = row.get("enfant", "")

                data["photo"] = (
                    url_for(
                        "static",
                        filename=f"img/img_employe/{row.get('matricule','')}/{row.get('photo','')}",
                    )
                    if row.get("photo")
                    else url_for("static", filename="img/image/image-profil.png")
                )

            return jsonify(data)

        except Exception as e:
            print(f"❌ Erreur fetch_contrat_masculin: {e}")
            return jsonify({"error": str(e)}), 500

    else:
        return jsonify({"error": "Paramètre id_contrat ou id manquant"}), 400
