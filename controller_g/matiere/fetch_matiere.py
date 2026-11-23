from flask import request, Response, url_for, jsonify
import re
import locale
import json
from datetime import datetime, date, timedelta
from templates.include.connect import get_connection
from templates.include.encryptor import encryptor
from babel.dates import format_date

# Locale française
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


def format_timedelta(td):
    if isinstance(td, timedelta):
        total_seconds = int(td.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        return f"{hours:02}:{minutes:02}:{seconds:02}"
    return str(td)


def fetch_matiere():
    print("🛠️ Requête entrante :", request.form)

    # Cas 1 : Récupérer un employé par son ID
    if "id_matiere" in request.form:
        encrypted_id = request.form.get("id_matiere")
        try:
            id = encryptor("decrypt", encrypted_id)
        except Exception as e:
            return jsonify({"error": f"Erreur de décryptage: {str(e)}"}), 400

        try:
            conn = get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM matiere WHERE id_matiere=%s", (id,))
            result = cursor.fetchall()
        except Exception as e:
            return jsonify({"error": f"Erreur SQL: {str(e)}"}), 500
        finally:
            conn.close()

        if not result:
            return jsonify({"error": "Aucun employé trouvé"}), 404

        data = []
        for row in result:
            # Construction matricule formaté

            data.append(
                {
                    "id_matiere": encryptor("encrypt", str(row["id_matiere"])),
                    "designation": row["designation"],
                    "nbre_unite": row["nbre_unite"],
                    "nature_unite": row["nature_unite"],
                    "id_categorie_article": row["id_categorie_article"],
                    "image": url_for(
                        "static",
                        filename=(
                            f"img/matiere/{row['image']}"
                            if row["image"]
                            else "img/image/image.jpg"
                        ),
                    ),
                }
            )
        return jsonify(data)

    # Cas 2 : Employés sans contrat par référence
    elif "id" in request.form:
        encrypted_id = request.form.get("id")
        try:
            id_ref = encryptor("decrypt", encrypted_id)
        except Exception as e:
            return jsonify({"error": f"Erreur de décryptage: {str(e)}"}), 400

        try:
            conn = get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                """
              SELECT * FROM matiere 
				      INNER JOIN categorie_article ON categorie_article.id_categorie_article=matiere.id_categorie_article 
				      INNER JOIN reference ON reference.id_reference=categorie_article.id_reference 
              WHERE reference.id_reference= %s
              ORDER BY matiere.id_matiere DESC
            """,
                (id_ref,),
            )
            result = cursor.fetchall()
        except Exception as e:
            return jsonify({"error": f"Erreur SQL: {str(e)}"}), 500
        finally:
            conn.close()

        data = []
        for idx, row in enumerate(result, 1):
            data.append(
                {
                    "count": idx,
                    "id_matiere": encryptor("encrypt", str(row["id_matiere"])),
                    "id_matiere_raw": row["id_matiere"],
                    "designation": row["designation"],
                    "nbre_unite": row["nbre_unite"],
                    "nature_unite": row["nature_unite"],
                    "categorie_article": row["categorie_article"],
                    "image": url_for(
                        "static",
                        filename=(
                            f"img/matiere/{row['image']}"
                            if row["image"]
                            else "img/image/image.jpg"
                        ),
                    ),
                }
            )
        return jsonify(data)

    # Cas non reconnu
    else:
        return jsonify({"error": "Aucun paramètre POST reconnu"}), 400
