from flask import request, jsonify
from datetime import datetime
import traceback

# Connexion DB et encryptor
from templates.include.connect import get_connection
from templates.include.encryptor import encryptor


def save_cotisation():
    conn = get_connection()
    cursor = conn.cursor()

    if "insert_id" in request.form:
        id_contrat = encryptor("decrypt", request.form["id_contrat"])
        amicale = request.form["amicale"].replace(",", ".").replace(" ", "").strip()
        tabaski = request.form["tabaski"].replace(",", ".").replace(" ", "").strip()
        autre_cotisation = (
            request.form["aute_cotisation"].replace(",", ".").replace(" ", "").strip()
        )

        cursor.execute("SELECT * FROM cotisation WHERE id_contrat = %s", (id_contrat,))
        if cursor.fetchone():
            return "true"  # existe déjà

        cursor.execute(
            """
            INSERT INTO cotisation (amicale, tabaski, aute_cotisation, id_contrat) 
            VALUES (%s, %s, %s, %s)
        """,
            (amicale, tabaski, autre_cotisation, id_contrat),
        )

        cursor.execute(
            """
            UPDATE contrat SET amicale = %s, tabaski = %s, aute_cotisation = %s 
            WHERE id_contrat = %s
        """,
            (amicale, tabaski, autre_cotisation, id_contrat),
        )

        conn.commit()
        return "inserted"

    elif "edit_id" in request.form:
        id_cotisation = encryptor("decrypt", request.form["edit_id"])
        amicale = request.form["amicale"].replace(",", ".").replace(" ", "").strip()
        tabaski = request.form["tabaski"].replace(",", ".").replace(" ", "").strip()
        autre_cotisation = (
            request.form["aute_cotisation"].replace(",", ".").replace(" ", "").strip()
        )

        cursor.execute(
            """
            UPDATE cotisation 
            SET amicale = %s, tabaski = %s, aute_cotisation = %s 
            WHERE id_cotisation = %s
        """,
            (amicale, tabaski, autre_cotisation, id_cotisation),
        )

        cursor.execute(
            "SELECT id_contrat FROM cotisation WHERE id_cotisation = %s",
            (id_cotisation,),
        )
        result = cursor.fetchone()
        if result:
            id_contrat = result[0]
            cursor.execute(
                """
                UPDATE contrat 
                SET amicale = %s, tabaski = %s, aute_cotisation = %s 
                WHERE id_contrat = %s
            """,
                (amicale, tabaski, autre_cotisation, id_contrat),
            )
            conn.commit()
        return "updated"

    elif "delete_id" in request.form:
        id_cotisation = encryptor("decrypt", request.form["delete_id"])
        id_contrat = encryptor("decrypt", request.form["id_contrat"])

        cursor.execute(
            "UPDATE contrat SET amicale = 0, tabaski = 0 WHERE id_contrat = %s",
            (id_contrat,),
        )
        cursor.execute(
            "DELETE FROM cotisation WHERE id_cotisation = %s", (id_cotisation,)
        )
        conn.commit()
        return "deleted"

    return "invalid request"
