from flask import request, jsonify
from templates.include.connect import get_connection
from templates.include.encryptor import encryptor
from datetime import datetime


def save_attestation_travail():
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Insertion
        if "insert_id" in request.form:
            id_contrat = encryptor("decrypt", request.form["id_contrat"].strip())
            date_embauche = request.form["date_embauche"].strip()
            poste_occupe = request.form["poste_occupe"].strip()
            document_lettre_attestation = request.form[
                "document_lettre_attestation"
            ].strip()
            date_now = datetime.now().strftime("%Y-%m-%d")

            query = """
                INSERT INTO attestation_travail (
                    date, date_embauche, poste_occupe, document_lettre_attestation, id_contrat
                ) VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(
                query,
                (
                    date_now,
                    date_embauche,
                    poste_occupe,
                    document_lettre_attestation,
                    id_contrat,
                ),
            )
            conn.commit()
            return jsonify({"success": True, "message": "Ajout effectué avec succès."})

        # Suppression
        elif "delete_id" in request.form:
            id_attestation = encryptor("decrypt", request.form["delete_id"].strip())
            query = "DELETE FROM attestation_travail WHERE id_attestation_travail = %s"
            cursor.execute(query, (id_attestation,))
            conn.commit()
            return jsonify(
                {"success": True, "message": "Suppression effectuée avec succès."}
            )

        # Édition (à implémenter si nécessaire)
        elif "edit_id" in request.form:
            # À compléter
            return jsonify(
                {"success": False, "message": "Édition non encore implémentée."}
            )

        else:
            return jsonify({"success": False, "message": "Aucune action valide reçue."})

    except Exception as e:
        print("Erreur dans handle_attestation_travail:", e)
        return jsonify({"success": False, "error": "Erreur serveur interne"}), 500
