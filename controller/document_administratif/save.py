from flask import request, jsonify
from templates.include.connect import get_connection
from templates.include.encryptor import encryptor


def save_document_administratif():
    try:
        count_id = int(encryptor("decrypt", request.form.get("count_id", "")))
        corps_text = request.form.get("corps_text", "")
        id_reference = int(encryptor("decrypt", request.form.get("id_reference", "")))

        table_map = {
            1: "lettre_affectation",
            2: "lettre_attestation",
            3: "lettre_cessation",
            4: "lettre_conge_annuel",
            5: "lettre_contrat",
            6: "lettre_decision",
            7: "lettre_indemnite",
            8: "lettre_transmission",
            9: "lettre_certificat_travail",
            10: "lettre_domiciliation_salaire",
        }

        table_name = table_map.get(count_id)
        if not table_name:
            return jsonify({"error": "count_id invalide"}), 400

        conn = get_connection()
        cursor = conn.cursor()
        query = f"UPDATE {table_name} SET corps_text = %s WHERE count_id = %s AND id_reference = %s"
        cursor.execute(query, (corps_text, count_id, id_reference))
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"success": True, "message": "Mise à jour effectuée."})

    except Exception as e:
        return jsonify({"error": str(e)}), 500
