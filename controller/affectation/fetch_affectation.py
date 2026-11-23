import locale
import regex as re_unicode  # pour support \p{L}
from datetime import datetime, date
from flask import Flask, request, jsonify, url_for
from templates.include.connect import get_connection
from templates.include.encryptor import encryptor
from babel.dates import format_date

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


def fmt_num(val, decimals=0):
    try:
        num = float(val)
    except (TypeError, ValueError):
        return ""
    formatted = f"{num:,.{decimals}f}".replace(",", " ").replace(".", ",")
    if decimals == 0:
        formatted = formatted.replace(",00", "")
    return formatted


def fetch_affectation():
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        if "id_affectation" in request.form:
            id_affectation = encryptor(
                "decrypt", str(request.form["id_affectation"])
            )
            query = """
               SELECT  *,affectation.document_lettre AS document_lettre_affectation FROM affectation 
              INNER JOIN contrat ON contrat.id_contrat=affectation.id_contrat
			        INNER JOIN employe ON employe.id_employe=contrat.id_employe
               INNER JOIN region ON region.id_region= affectation.id_region
               INNER JOIN reference ON reference.id_reference=employe.id_reference
               WHERE affectation.id_affectation = %s
            """
            cursor.execute(query, (id_affectation,))
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
                    duree = f"{years} ans {months} mois {days} jours"
            except Exception:
                pass
            data = {
                "id_affectation": encryptor("encrypt", str(row["id_affectation"])),
                "id_contrat": encryptor("encrypt", str(row["id_contrat"])),
                "prenom": row["prenom"],
                "nom": row["nom"],
                "matricule": f"{acronym}-{row['matricule']}",
                "date_affectation": row["date_affectation"].strftime("%Y-%m-%d"),
                "document_lettre": row["document_lettre_affectation"],
                "id_region": row["id_region"],
                "region": row["region"],
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
                SELECT  * FROM affectation 
               INNER JOIN contrat ON contrat.id_contrat=affectation.id_contrat
			         INNER JOIN employe ON employe.id_employe=contrat.id_employe
               INNER JOIN region ON region.id_region= affectation.id_region
               INNER JOIN reference ON reference.id_reference=employe.id_reference 
               WHERE reference.id_reference=%s
				       ORDER BY affectation.id_affectation DESC
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
                        "id_affectation": encryptor(
                            "encrypt", str(row["id_affectation"])
                        ),
                        "id_affectation_raw": row["id_affectation"],
                        "date_embauche": format_date_fr(row["date_embauche"]),
                        "date_affectation": format_date_fr(row["date_affectation"],style="full"),
                        "prenom": row["prenom"],
                        "nom": row["nom"],
                        "matricule": f"{acronym}-{row['matricule']}",
                        "poste_occupe": row["poste_occupe"],
                        "telephone_e": row["telephone_e"],
                        "genre": row["genre"],
                        "region": row["region"],
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
