from flask import Flask, request, jsonify, url_for
from templates.include.connect import get_connection
from templates.include.encryptor import encryptor
from datetime import datetime,date
import locale
from babel.dates import format_date
from dateutil.relativedelta import relativedelta

try:
    locale.setlocale(locale.LC_TIME, "fr_FR.UTF-8")
except locale.Error:
    locale.setlocale(locale.LC_TIME, "")

# ---------------------------
# Utils
# ---------------------------


def format_date_fr(date_str, style="long"):
    """
    Formatte une date en français avec différents styles :
    - style="full"   → "vendredi 13 décembre 2024"
    - style="long"   → "13 décembre 2024"
    - style="month"  → "décembre 2024"
    - style="years"  → "2024"
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


def fetch_salaire():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    if "id_salaire" in request.form:
        id_salaire = datetime.strptime(request.form["id_salaire"], "%Y-%m")
        id_ref = encryptor("decrypt", request.form["id_s"]).strip()

        query = """
            SELECT *, salaire.date_du AS date_du
            FROM salaire
            INNER JOIN contrat ON contrat.id_contrat=salaire.id_contrat
            INNER JOIN employe ON employe.id_employe=contrat.id_employe
            INNER JOIN reference ON reference.id_reference=employe.id_reference
            WHERE reference.id_reference=%s 
            AND YEAR(salaire.date_du) = %s AND MONTH(salaire.date_du) = %s
            GROUP BY MONTH(salaire.date_du), YEAR(salaire.date_du)
        """
        cursor.execute(query, (id_ref, id_salaire.year, id_salaire.month))
        result = cursor.fetchall()

        if result:
            row = result[0]
            data = {
                "id_reference": encryptor("encrypt", str(row["id_reference"])),
                "date_du": row["date_du"].strftime("%Y-%m"),
                "date_del": format_date_fr(row["date_du"], style="month"),
                "date_paiement": row["date_paiement"].strftime("%Y-%m-%d"),
                "mode_paie": row["mode_paie"],
                "email": row["email"],
            }
            print(data)
            return jsonify(data)
        return "0"

    elif "id_salaire_employe" in request.form:
        id_salaire = encryptor("decrypt", request.form["id_salaire_employe"]).strip()
        query = """
            SELECT *, salaire.date_du AS date_du,
                     DATE_FORMAT(salaire.date_du,'%%M-%%Y') AS date_del
            FROM salaire
            INNER JOIN contrat ON contrat.id_contrat=salaire.id_contrat
            INNER JOIN employe ON employe.id_employe=contrat.id_employe
            INNER JOIN reference ON reference.id_reference=employe.id_reference
            WHERE salaire.id_salaire=%s
        """
        cursor.execute(query, (id_salaire,))
        result = cursor.fetchall()

        if result:
            row = result[0]
            prenom = row["prenom"]
            nom = row["nom"]
            acronym_prenom = "".join([mot[0] for mot in prenom.split()])
            acronym_nom = "".join([mot[0] for mot in nom.split()])

            data = {
                "id_salaire": encryptor("encrypt", str(row["id_salaire"])),
                "prenom": prenom,
                "nom": nom,
                "matricule": f"{acronym_prenom}{acronym_nom}-{row['matricule']}",
                "date_del": format_date_fr(row["date_du"], style="month"),
                "date_du": row["date_du"],
                "date_paiement": row["date_paiement"],
                "mode_paie": row["mode_paie"],
                "date_conge_actuel": row["date_conge_actuel"],
                "date_conge_precedent": row["date_conge_precedent"],
                "formule": row["formule"],
                "id_num_conge": encryptor("encrypt", str(row["id_num_conge"])),
                "id_num_conge_maternite": encryptor(
                    "encrypt", str(row["id_num_conge_maternite"])
                ),
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
        return "0"

    elif "date" in request.form:
        id_ref = encryptor("decrypt", request.form["id"])
        year = request.form["date"]
        query = """
            SELECT *,
            salaire.date_du AS date_du_add,
            salaire.date_paiement AS date_paiement_format
            FROM salaire
            INNER JOIN contrat ON contrat.id_contrat = salaire.id_contrat
            INNER JOIN employe ON employe.id_employe = contrat.id_employe
            INNER JOIN reference ON reference.id_reference = employe.id_reference
            WHERE reference.id_reference = %s
            AND YEAR(salaire.date_du) = %s
            GROUP BY MONTH(salaire.date_du), YEAR(salaire.date_du)
            ORDER BY salaire.date_du DESC
        """
        cursor.execute(query, (id_ref, year))
        results = cursor.fetchall()

        data = []
        for count, row in enumerate(results, 1):
            data.append(
                {
                    "count": count,
                    "date_du_add": row["date_du_add"].strftime("%Y-%m"),
                    "annee": format_date_fr(row["date_du_add"], style="years"),
                    "periode": format_date_fr(row["date_du_add"], style="month"),
                    "date_paiement": format_date_fr(
                        row["date_paiement_format"], style="full"
                    ),
                    "mode_paie": row["mode_paie"].capitalize(),
                }
            )
        return jsonify(data)

    elif "employe_date" in request.form:
        id_ref = encryptor("decrypt", request.form["id"]).strip()
        year = request.form["employe_date"].strip()

        query = """
            SELECT *, salaire.date_du AS date_du, salaire.date_debut AS deb
            FROM salaire
            INNER JOIN contrat ON contrat.id_contrat=salaire.id_contrat
            INNER JOIN employe ON employe.id_employe=contrat.id_employe
            INNER JOIN reference ON reference.id_reference=employe.id_reference
            WHERE reference.id_reference = %s  AND YEAR(salaire.date_du) = %s
            ORDER BY salaire.date_du DESC
        """
        cursor.execute(query, (id_ref, year))
        results = cursor.fetchall()

        data = []
        for count, row in enumerate(results, 1):
            prenom = row["prenom"]
            nom = row["nom"]
            acronym_prenom = "".join([mot[0] for mot in prenom.split()])
            acronym_nom = "".join([mot[0] for mot in nom.split()])

            data.append(
                {
                    "count" :count,
                    "id_salaire": encryptor("encrypt", str(row["id_salaire"])),
                    "id_salaire_raw": row["id_salaire"],
                    "prenom": prenom,
                    "nom": nom,
                    "matricule": f"{acronym_prenom}{acronym_nom}-{row['matricule']}",
                    "poste_occupe": row["poste_occupe"],
                    "telephone_e": row["telephone_e"],
                    "annee": format_date_fr(row["date_du"], style="years"),
                    "periode": format_date_fr(row["date_du"], style="month"),
                    "date_paiement": format_date_fr(
                        row["date_paiement"], style="full"
                    ),
                    "mode_paie": row["mode_paie"],
                    "photo": (
                        url_for(
                            "static",
                            filename=f"img/img_employe/{row.get('matricule','')}/{row.get('photo','')}",
                        )
                        if row.get("photo")
                        else url_for("static", filename="img/image/image-profil.png")
                    ),
                }
            )

        return jsonify(data)


    # Ajoute ici d'autres blocs POST si nécessaire comme:
    # - conge_annuel_id_salaire
    # - employe_date
    # - etc.

    return jsonify({"error": "Aucune action reconnue"}), 400
