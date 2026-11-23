from flask import Flask, request, jsonify, url_for
from templates.include.connect import get_connection
from templates.include.encryptor import encryptor
from datetime import datetime, date
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


def fetch_paie_conge_maternite():
    try:
        data = []
        form = request.form

        # 🔹 Cas 1 : liste des salaires par id_reference (id POST)
        if "id" in form:
            id_reference = encryptor("decrypt", form["id"].strip())

            with get_connection() as conn:
                with conn.cursor(dictionary=True) as cursor:
                    cursor.execute(
                        """
                       SELECT *, salaire.date_debut AS deb FROM salaire
                       INNER JOIN contrat ON contrat.id_contrat=salaire.id_contrat
                       INNER JOIN employe ON employe.id_employe=contrat.id_employe
                       INNER JOIN reference ON reference.id_reference=employe.id_reference 
                       WHERE reference.id_reference = %s AND genre='Feminin'
                    ORDER BY salaire.id_salaire DESC
                    """,
                        (id_reference,),
                    )
                    rows = cursor.fetchall()

                    for count, row in enumerate(rows, 1):
                        if row["id_num_conge_maternite"] == 0:
                            continue

                        prenom = row["prenom"]
                        nom = row["nom"]
                        prenom = row["prenom"]
                        nom = row["nom"]
                        acronym_prenom = "".join([mot[0] for mot in prenom.split()])
                        acronym_nom = "".join([mot[0] for mot in nom.split()])
                        matricule = f"{acronym_prenom}{acronym_nom}-{row['matricule']}"

                        data.append(
                            {
                                "count": count,
                                "id_salaire": encryptor(
                                    "encrypt", str(row["id_salaire"])
                                ),
                                "id_salaire_raw": row["id_salaire"],
                                "prenom": prenom,
                                "nom": nom,
                                "matricule": matricule,
                                "poste_occupe": row["poste_occupe"],
                                "telephone_e": row["telephone_e"],
                                "annee": format_date_fr(row["date_du"], "yyyy"),
                                "periode": format_date_fr(
                                    row["date_du"], style="month"
                                ),
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
                                    else url_for(
                                        "static", filename="img/image/image-profil.png"
                                    )
                                ),
                            }
                        )

            return jsonify(data)

        # 🔹 Cas 2 : détails d’un salaire unique
        elif "id_salaire" in form:
            id_salaire = encryptor("decrypt", form["id_salaire"].strip())

            with get_connection() as conn:
                with conn.cursor(dictionary=True) as cursor:
                    cursor.execute(
                        """
                        SELECT * FROM salaire
                        INNER JOIN contrat ON contrat.id_contrat = salaire.id_contrat
                        INNER JOIN employe ON employe.id_employe = contrat.id_employe
                        INNER JOIN reference ON reference.id_reference = employe.id_reference
                        WHERE salaire.id_salaire = %s
                    """,
                        (id_salaire,),
                    )
                    row = cursor.fetchone()

            if row:

                return jsonify(
                    {
                        "id_salaire": encryptor("encrypt", str(row["id_salaire"])),
                        "prenom": row["prenom"],
                        "nom": row["nom"],
                        "date_del": format_date_fr(row["date_du"], style="month"),
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
                            else url_for(
                                "static", filename="img/image/image-profil.png"
                            )
                        ),
                    }
                )

            return jsonify({"error": "Aucun salaire trouvé"}), 404

        # 🔸 Si aucune condition
        return jsonify({"error": "Paramètre manquant"}), 400

    except Exception as e:
        return jsonify({"error": str(e)}), 500
