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


def fetch_fournisseur():
    print("🛠️ Requête entrante :", request.form)

    # Cas 1 : Récupérer un employé par son ID
    if "id_fournisseur" in request.form:
        encrypted_id = request.form.get("id_fournisseur")
        try:
            id = encryptor("decrypt", encrypted_id)
        except Exception as e:
            return jsonify({"error": f"Erreur de décryptage: {str(e)}"}), 400

        try:
            conn = get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM fournisseur WHERE id_fournisseur=%s", (id,))
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
                    "id_fournisseur": encryptor("encrypt", str(row["id_fournisseur"])),
                    "id_fournisseur_raw": row["id_fournisseur"],
                    "fournisseur": row["fournisseur"],
                    "adresse_f": row["adresse_f"],
                    "telephone_f": row["telephone_f"],
                    "email_f": row["email_f"],
                    "ninea_f": row["ninea_f"],
                    "nom_contact_f": row["nom_contact_f"],
                    "photo": url_for(
                        "static",
                        filename=(
                            f"img/fournisseur/{row['photo']}"
                            if row["photo"]
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
                SELECT * FROM fournisseur 
				        INNER JOIN reference ON reference.id_reference=fournisseur.id_reference 
                WHERE reference.id_reference= %s
                ORDER BY fournisseur.id_fournisseur DESC
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
                    "id_fournisseur": encryptor("encrypt", str(row["id_fournisseur"])),
                    "id_fournisseur_raw": row["id_fournisseur"],
                    "fournisseur": row["fournisseur"],
                    "adresse_f": row["adresse_f"],
                    "telephone_f": row["telephone_f"],
                    "email_f": row["email_f"],
                    "ninea_f": row["ninea_f"],
                    "nom_contact_f": row["nom_contact_f"],
                    "photo": url_for(
                        "static",
                        filename=(
                            f"img/fournisseur/{row['photo']}"
                            if row["photo"]
                            else "img/image/image.jpg"
                        ),
                    ),
                }
            )
        return jsonify(data)

    # Cas non reconnu
    else:
        return jsonify({"error": "Aucun paramètre POST reconnu"}), 400
