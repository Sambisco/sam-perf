from flask import request, redirect, session, url_for
from templates.include.connect import get_connection
import hashlib
from templates.include.encryptor import encryptor


def fetch_reference(id_encrypted):
    result_reference = {}

    if not id_encrypted:
        return result_reference

    try:
        id_decrypted = encryptor("decrypt", id_encrypted)

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT 
                reference.*,
                reference.email AS email_r,
                COUNT(region.id_region) AS id_region
            FROM reference
            LEFT JOIN region ON reference.id_reference = region.id_reference
            WHERE reference.id_reference = %s
            GROUP BY reference.id_reference
            """,
            (id_decrypted,),
        )

        result_reference = cursor.fetchone() or {}

        print("DEBUG result_reference:", result_reference)
        print("Clés récupérées :", list(result_reference.keys()))

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"❌ Erreur récupération reference: {e}")
        result_reference = {}

    return result_reference
