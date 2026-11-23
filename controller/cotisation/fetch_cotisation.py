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


def format_number(num):
    try:
        if num is None:
            return "0"
        return f"{num:,.0f}".replace(",", " ").replace(".", ",")
    except Exception:
        return "0"


def fetch_cotisation():
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        if "id_cotisation" in request.form:
            id_attestation = encryptor("decrypt", str(request.form["id_cotisation"]))
            query = """
                SELECT * FROM cotisation 
         INNER JOIN contrat ON contrat.id_contrat=cotisation.id_contrat
         INNER JOIN employe ON employe.id_employe=contrat.id_employe 
          WHERE cotisation.id_cotisation = %s
            """
            cursor.execute(query, (id_attestation,))
            row = cursor.fetchone()
            if not row:
                return jsonify("0")

            acronym = get_acronym(row["prenom"]) + get_acronym(row["nom"])

            data = {
                "id_cotisation": encryptor("encrypt", str(row["id_cotisation"])),
                "id_contrat": encryptor("encrypt", str(row["id_contrat"])),
                "prenom": row["prenom"],
                "nom": row["nom"],
                "matricule": f"{acronym}-{row['matricule']}",
                "amicale": format_number(row.get("amicale", 0)),
                "tabaski": format_number(row.get("tabaski", 0)),
                "aute_cotisation": format_number(row.get("aute_cotisation", 0)),
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
               SELECT *,cotisation.amicale AS amicale_c,cotisation.tabaski AS tabaski_c,cotisation.aute_cotisation AS aute_cotisation_c FROM cotisation 
				INNER JOIN contrat ON contrat.id_contrat=cotisation.id_contrat 
				INNER JOIN employe ON employe.id_employe=contrat.id_employe 
				 INNER JOIN reference ON reference.id_reference=employe.id_reference
                 WHERE reference.id_reference= %s 
                 ORDER BY cotisation.id_cotisation DESC
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
                        "id_cotisation": encryptor(
                            "encrypt", str(row["id_cotisation"])
                        ),
                        "id_cotisation_raw": row["id_cotisation"],
                        "date_embauche": format_date_fr(row["date_embauche"]),
                        "prenom": row["prenom"],
                        "nom": row["nom"],
                        "matricule": f"{acronym}-{row['matricule']}",
                        "poste_occupe": row["poste_occupe"],
                        "telephone_e": row["telephone_e"],
                        "adresse_e": row["adresse_e"],
                        "email_e": row.get("email_e", ""),
                        "amicale_c": format_number(row.get("amicale_c", 0)),
                        "tabaski_c": format_number(row.get("tabaski_c", 0)),
                        "aute_cotisation_c": format_number(
                            row.get("aute_cotisation_c", 0)
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
                )
            return jsonify(data)

        else:
            return jsonify("Aucun paramètre valide reçu.")

    except Exception as e:
        print(f"Erreur dans fetch_cotisation: {e}")
        return jsonify({"error": "Erreur serveur interne"}), 500
