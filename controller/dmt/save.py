from flask import request, jsonify
from templates.include.connect import get_connection
from templates.include.encryptor import encryptor


def save_dmt():
    """
    Équivalent du script PHP pour insérer, modifier ou supprimer dans dmt.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # ✅ Récupération des données POST
    post = request.form  # ou request.json si en JSON

    # ✅ Insertion
    if "insert_id" in post:
        id_contrat = encryptor("decrypt", post.get("id_contrat", "").strip())
        data = (
            post.get("groupe_ethnique", "").strip(),
            post.get("pays", "").strip(),
            post.get("délivrée_cin_a", "").strip(),
            post.get("délivrée_cin_le", "").strip(),
            post.get("ccpe_at", "").strip(),
            post.get("agrom", "").strip(),
            post.get("nom_conjoint", "").strip(),
            post.get("nom_enfant", "").strip(),
            id_contrat,
        )

        sql = """
        INSERT INTO dmt (groupe_ethnique, pays, délivrée_cin_a, délivrée_cin_le,
                         ccpe_at, agrom, nom_conjoint, nom_enfant, id_contrat)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """
        cursor.execute(sql, data)
        conn.commit()
        return jsonify({'status': 'success', 'message': 'DMT ajouté avec succès.'})

    # ✅ Mise à jour
    elif "edit_id" in post:
        id_dmt = encryptor("decrypt", post.get("edit_id", "").strip())
        data = (
            post.get("groupe_ethnique", "").strip(),
            post.get("pays", "").strip(),
            post.get("délivrée_cin_a", "").strip(),
            post.get("délivrée_cin_le", "").strip(),
            post.get("ccpe_at", "").strip(),
            post.get("agrom", "").strip(),
            post.get("nom_conjoint", "").strip(),
            post.get("nom_enfant", "").strip(),
            id_dmt,
        )

        sql = """
        UPDATE dmt
        SET groupe_ethnique=%s,
            pays=%s,
            délivrée_cin_a=%s,
            délivrée_cin_le=%s,
            ccpe_at=%s,
            agrom=%s,
            nom_conjoint=%s,
            nom_enfant=%s
        WHERE id_dmt=%s
        """
        cursor.execute(sql, data)
        conn.commit()
        return jsonify({'status': 'success', 'message': 'DMT mis à jour avec succès.'})

    # ✅ Suppression
    elif "delete_id" in post:
        id_dmt = encryptor("decrypt", post.get("delete_id", "").strip())
        sql = "DELETE FROM dmt WHERE id_dmt=%s"
        cursor.execute(sql, (id_dmt,))
        conn.commit()
        return jsonify({'status': 'success', 'message': 'DMT supprimé avec succès.'})

    else:
        return jsonify({"error": "Aucune action valide (insert/edit/delete)"}), 400

    # ✅ Fermeture connexion
    cursor.close()
    conn.close()

    return jsonify({"status": "success", "action": action_done})
