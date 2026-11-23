from flask import request, Response, url_for, jsonify
import re
import locale
import json
from datetime import datetime, date, timedelta
from templates.include.connect import get_connection
from templates.include.encryptor import encryptor


# Route pour récupérer une catégorie par id_categorie_article
def fetch_categorie():

    if "id_categorie_article" in request.form:
        id_cat = encryptor("decrypt", request.form["id_categorie_article"])
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
                "SELECT * FROM categorie_article WHERE id_categorie_article=%s",
                (id_cat,),
        )
        result = cursor.fetchall()
        if len(result) > 0:
            row = result[0]
            data = {
                "id_categorie_article": encryptor(
                    "encrypt", str(row["id_categorie_article"])
                ),
                "categorie_article": row["categorie_article"],
                "description": row["description"],
            }
            return jsonify(data)
        else:
            return "0"

    elif "id" in request.form:
        encrypted_id = request.form.get("id")
        id_ref = encryptor("decrypt", encrypted_id)

        try:
            conn = get_connection()
            cursor = conn.cursor(dictionary=True)
            query = """
                    SELECT * FROM categorie_article
                 INNER JOIN reference ON reference.id_reference=categorie_article.id_reference 
                WHERE reference.id_reference= %s
                 ORDER BY categorie_article.id_categorie_article DESC
            """
            cursor.execute(query, (id_ref,))
            result = cursor.fetchall()
        except Exception as e:
            return jsonify({"error": f"Erreur SQL: {str(e)}"}), 500
        finally:
            conn.close()

        data = []
        for count, row in enumerate(result, 1):
            word_sanitized = re.sub(r"\b\w['`‘’]\b", "", row["categorie_article"])
            abbreviation_debut = word_sanitized.split()
            acronym_debut = "".join([w[0] for w in abbreviation_debut if w])

            data.append(
                {
                    "count": count,
                    "id_categorie_article": encryptor(
                        "encrypt", str(row["id_categorie_article"])
                    ),
                    "acronym_debut": acronym_debut.upper(),
                    "categorie_article": row["categorie_article"],
                    "description": row["description"],
                }
            )
        return jsonify(data)

    return "Paramètre manquant", 400
