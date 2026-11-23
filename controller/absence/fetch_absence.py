from flask import Flask, request, jsonify, url_for
import re
from datetime import datetime, date
from templates.include.connect import get_connection
from templates.include.encryptor import encryptor
from babel.dates import format_date


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


def generate_acronym(nom_complet):
    # Supprime apostrophes isolées, récupère initiales en majuscule
    try:
        cleaned = re.sub(r"['`‘’]", "", nom_complet)
        parts = cleaned.split()
        return "".join(part[0].upper() for part in parts if part)
    except Exception as e:
        print("Erreur generate_acronym:", e)
        return ""


def fetch_absence():
    data = request.form
    try:
        print("Données reçues:", data)
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        if "id_absence" in data:
            id_absence = encryptor("decrypt", data["id_absence"])
            print("id_absence décrypté:", id_absence)
            cursor.execute(
                """
                SELECT * FROM absence
                INNER JOIN contrat ON contrat.id_contrat = absence.id_contrat
                INNER JOIN employe ON employe.id_employe = contrat.id_employe
                INNER JOIN reference ON reference.id_reference = employe.id_reference
                WHERE id_absence = %s
            """,
                (id_absence,),
            )
            row = cursor.fetchone()
            if row:
                response = {
                    "id_absence": encryptor("encrypt", str(row["id_absence"])),
                    "date": row.get("date").strftime("%Y-%m-%d"),
                    "justification": row["justification"],
                    "Imputable_sur_les_normaux": row["Imputable_sur_les_normaux"],
                    "prenom": row["prenom"],
                    "nom": row["nom"],
                    "photo": (
                        url_for(
                            "static",
                            filename=f"img/img_employe/{row.get('matricule','')}/{row.get('photo','')}",
                        )
                        if row.get("photo")
                        else url_for("static", filename="img/image/image-profil.png")
                    ),
                }
                return jsonify(response)
            return jsonify(0)

        elif "id" in data:
            id_reference = encryptor("decrypt", data["id"])
            print("id_reference décrypté:", id_reference)
            cursor.execute(
                """
                SELECT * FROM absence
                INNER JOIN contrat ON contrat.id_contrat = absence.id_contrat
                INNER JOIN employe ON employe.id_employe = contrat.id_employe
                INNER JOIN reference ON reference.id_reference = employe.id_reference
                WHERE reference.id_reference = %s
                ORDER BY absence.id_absence DESC
            """,
                (id_reference,),
            )
            results = cursor.fetchall()
            data_list = []
            for count, row in enumerate(results, 1):
                acronym_prenom = generate_acronym(row["prenom"])
                acronym_nom = generate_acronym(row["nom"])
                response = {
                    "count": count,
                    "id_absence": encryptor("encrypt", str(row["id_absence"])),
                    "date": format_date_fr(row.get("date", ""),style="full"),
                    "justification": row["justification"] or "Pas de motif",
                    "Imputable_sur_les_normaux": row["Imputable_sur_les_normaux"],
                    "prenom": row["prenom"],
                    "nom": row["nom"],
                    "matricule": acronym_prenom
                    + acronym_nom
                    + "-"
                    + str(row["matricule"]),
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
                data_list.append(response)

            return jsonify(data_list)

        elif "date_nbr_absence" in data:
            id_reference = encryptor("decrypt", data["id_r"])
            date_str = data["date_nbr_absence"]
            print(
                "Calcul absences pour id_reference:",
                id_reference,
                "à la date:",
                date_str,
            )

            cursor.execute(
                """
                SELECT * FROM contrat
                INNER JOIN employe ON employe.id_employe = contrat.id_employe
                INNER JOIN reference ON reference.id_reference = employe.id_reference
                WHERE NOT EXISTS (
                    SELECT * FROM pointage 
                    WHERE contrat.id_contrat = pointage.id_contrat AND pointage.date = %s
                ) AND reference.id_reference = %s
            """,
                (date_str, id_reference),
            )

            result = cursor.fetchall()
            count = 0
            for row in result:
                id_contrat = row["id_contrat"]
                cursor.execute(
                    """
                    SELECT * FROM depart
                    INNER JOIN contrat ON contrat.id_contrat = depart.id_contrat
                    INNER JOIN employe ON employe.id_employe = contrat.id_employe
                    INNER JOIN reference ON reference.id_reference = employe.id_reference
                    WHERE contrat.id_contrat = %s AND reference.id_reference = %s
                    ORDER BY contrat.id_contrat DESC LIMIT 1
                """,
                    (id_contrat, id_reference),
                )

                depart_row = cursor.fetchone()
                if depart_row:
                    date_effet = datetime.strptime(
                        str(depart_row["date_effet"]), "%Y-%m-%d"
                    )
                    if date_effet < datetime.strptime(date_str, "%Y-%m-%d"):
                        continue
                count += 1
            return jsonify({"nbre_absence": count})

        else:
            return jsonify({"error": "Paramètre POST invalide"}), 400

    except Exception as e:
        print("Erreur attrapée dans fetch_absence:", e)
        return jsonify({"error": str(e)}), 500

    finally:
        if "cursor" in locals():
            cursor.close()
        if "conn" in locals():
            conn.close()
