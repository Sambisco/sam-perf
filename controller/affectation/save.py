from flask import request, jsonify
from templates.include.connect import get_connection
from templates.include.encryptor import encryptor


def save_affectation():
    conn = get_connection()
    cursor = conn.cursor()

    if "insert_id" in request.form:
        id_contrat = encryptor("decrypt", request.form["id_contrat"]).strip()
        id_region =  request.form["id_region"].strip()
        date_affectation = request.form["date_affectation"].strip()
        document_lettre = request.form.get("document_lettre", "")

        # Vérification si une affectation existe déjà à cette date pour cette région
        
        # Insertion
        cursor.execute(
            """
            INSERT INTO affectation (date_affectation, document_lettre, id_contrat, id_region)
            VALUES (%s, %s, %s, %s)
        """,
            (date_affectation, document_lettre, id_contrat, id_region),
        )

        cursor.execute(
            """
            UPDATE personnel SET id_region = %s WHERE id_contrat = %s
        """,
            (id_region, id_contrat),
        )

        conn.commit()
        return "inserted"

    elif "edit_id" in request.form:
        id_affectation = encryptor("decrypt", request.form["edit_id"]).strip()
        id_region =  request.form["id_region"].strip()
        id_contrat = encryptor("decrypt", request.form["id_contrat"]).strip()
        date_affectation = request.form["date_affectation"].strip()
        document_lettre = request.form.get("document_lettre", "")

        # Mise à jour de l'affectation
        cursor.execute(
            """
            UPDATE affectation 
            SET date_affectation = %s, document_lettre = %s, id_region = %s 
            WHERE id_affectation = %s
        """,
            (date_affectation, document_lettre, id_region, id_affectation),
        )

        cursor.execute(
            """
            UPDATE personnel SET id_region = %s WHERE id_contrat = %s
        """,
            (id_region, id_contrat),
        )

        conn.commit()
        return "updated"

    elif "delete_id" in request.form:
        id_affectation = encryptor("decrypt", request.form["delete_id"]).strip()

        cursor.execute(
            "DELETE FROM affectation WHERE id_affectation = %s", (id_affectation,)
        )
        conn.commit()
        return "deleted"

    return jsonify({"error": "Requête invalide"}), 400
