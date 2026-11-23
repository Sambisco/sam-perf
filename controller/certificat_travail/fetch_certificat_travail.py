import locale
import regex as re_unicode  # pour support \p{L}
from datetime import datetime, date
from flask import Flask, request, jsonify, url_for
from templates.include.connect import get_connection
from templates.include.encryptor import encryptor
from babel.dates import format_date as babel_format_date

# Config locale française (différentes options selon OS)
try:
    locale.setlocale(locale.LC_TIME, "fr_FR.UTF-8")
except locale.Error:
    try:
        locale.setlocale(locale.LC_TIME, "French_France")
    except locale.Error:
        print("Locale française non disponible, dates au format par défaut")


def get_acronym(text):
    if not text:
        return ""
    # Enlève les apostrophes isolées (ex: d’)
    cleaned_text = re_unicode.sub(r"\b\p{L}[\'`‘’]\b", "", text)
    parts = cleaned_text.split()
    return "".join([w[0].upper() for w in parts if w])


def format_date_fr(date_str):
    try:
        if not date_str:
            return ""
        if isinstance(date_str, (datetime, date)):
            dt = date_str
        else:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
        return babel_format_date(
            dt, format="EEEE d MMMM yyyy", locale="fr_FR"
        ).capitalize()
    except Exception:
        return ""


def fetch_certificat_travail():
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        if "id_certificat_travail" in request.form:
            id_certificat = encryptor(
                "decrypt", str(request.form["id_certificat_travail"])
            )
            query = """
               SELECT  *,certificat_travail.poste_occupe AS poste_occupe_certificat_travail FROM certificat_travail 
               INNER JOIN contrat ON contrat.id_contrat=certificat_travail.id_contrat
			   INNER JOIN employe ON employe.id_employe=contrat.id_employe
               INNER JOIN reference ON reference.id_reference=employe.id_reference 
               WHERE certificat_travail.id_certificat_travail = %s
            """
            cursor.execute(query, (id_certificat,))
            row = cursor.fetchone()
            if not row:
                return jsonify("0")

            acronym = get_acronym(row["prenom"]) + get_acronym(row["nom"])
            duree = "0 ans 0 mois 0 jours"
            try:
                    diff_days = (
                        datetime.strptime(row["date_sorti"], "%Y-%m-%d").date()
                        - date.today()
                    ).days
                    if diff_days > 0:
                        years = diff_days // 365
                        months = (diff_days % 365) // 30
                        days = (diff_days % 365) % 30
                        duree = f" {years} ans {months} mois {days} jours"
            except Exception:
                    pass
            data = {
                "id_certificat_travail": encryptor(
                    "encrypt", str(row["id_certificat_travail"])
                ),
                "prenom": row["prenom"],
                "nom": row["nom"],
                "matricule": f"{acronym}-{row['matricule']}",
                "date_n2": format_date_fr(row["date_n"]),
                "poste_occupe": row["poste_occupe"],
                "photo": (
                    url_for(
                        "static",
                        filename=f"img/img_employe/{row.get('matricule','')}/{row.get('photo','')}",
                    )
                    if row.get("photo")
                    else url_for("static", filename="img/image/image-profil.png")
                ),
            }
            return jsonify(data)

        elif "id" in request.form:
            id_reference = encryptor("decrypt", str(request.form["id"]))
            query = """
                SELECT  * FROM certificat_travail 
              INNER JOIN contrat ON contrat.id_contrat=certificat_travail.id_contrat
			  INNER JOIN employe ON employe.id_employe=contrat.id_employe
              INNER JOIN reference ON reference.id_reference=employe.id_reference 
              WHERE reference.id_reference=%s
				ORDER BY certificat_travail.id_certificat_travail DESC
            """
            cursor.execute(query, (id_reference,))
            rows = cursor.fetchall()

            data = []
            for i, row in enumerate(rows, start=1):
                acronym = get_acronym(row["prenom"]) + get_acronym(row["nom"])
                try:
                    year_birth = int(
                        datetime.strptime(row["date_n"], "%Y-%m-%d").strftime("%Y")
                    )
                    age = f"{date.today().year - year_birth} ans"
                except Exception:
                    age = ""

                duree = "Expire : 0 ans 0 mois 0 jours"
                try:
                    diff_days = (
                        datetime.strptime(row["date_sorti"], "%Y-%m-%d").date()
                        - date.today()
                    ).days
                    if diff_days > 0:
                        years = diff_days // 365
                        months = (diff_days % 365) // 30
                        days = (diff_days % 365) % 30
                        duree = f"Active : {years} ans {months} mois {days} jours"
                except Exception:
                    pass

                data.append(
                    {
                        "count": i,
                        "id_certificat_travail": encryptor(
                            "encrypt", str(row["id_certificat_travail"])
                        ),
                        "id_certificat_travail_raw": row["id_certificat_travail"],
                        "date_embauche": format_date_fr(row["date_embauche"]),
                        "prenom": row["prenom"],
                        "nom": row["nom"],
                        "matricule": f"{acronym}-{row['matricule']}",
                        "poste_occupe": row["poste_occupe"],
                        "telephone_e": row["telephone_e"],
                        "adresse_e": row["adresse_e"],
                        "nombre_annee": duree,
                        "age": age,
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
                )
            return jsonify(data)

        else:
            return jsonify("Aucun paramètre valide reçu.")

    except Exception as e:
        print(f"Erreur dans fetch_attestation_travail: {e}")
        return jsonify({"error": "Erreur serveur interne"}), 500
