from flask import request, jsonify
from templates.include.connect import get_connection
from templates.include.encryptor import encryptor
from datetime import datetime


def save_certificat_travail():
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Insertion
        if "insert_id" in request.form:
            id_contrat = encryptor("decrypt", request.form["id_contrat"].strip())
            duree_contrat = request.form["duree_contrat"].strip()
            poste_occupe = request.form["poste_occupe"].strip()
            document_lettre_certificat = request.form[
                "document_lettre_certificat"
            ].strip()
            date_now = datetime.now().strftime("%Y-%m-%d")

            query = """
                INSERT INTO certificat_travail(date, poste_occupe, duree_contrat, document_lettre_certificat, id_contrat) VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(
                query,
                (
                    date_now,
                    poste_occupe,
                    duree_contrat,
                    document_lettre_certificat,
                    id_contrat,
                ),
            )
            conn.commit()
            return jsonify({"success": True, "message": "Ajout effectué avec succès."})

        # Suppression
        elif "delete_id" in request.form:
            id_attestation = encryptor("decrypt", request.form["delete_id"].strip())
            query = "DELETE FROM certificat_travail WHERE id_certificat_travail = %s"
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
        print("Erreur dans handle_certificat_travail:", e)
        return jsonify({"success": False, "error": "Erreur serveur interne"}), 500
