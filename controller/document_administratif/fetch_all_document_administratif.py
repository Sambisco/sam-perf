from flask import Flask, request, jsonify
from templates.include.connect import get_connection
from templates.include.encryptor import encryptor


def fetch_all_document_administratif():
    # Vérifie si un identifiant crypté a été transmis
    if "id_lettre_contrat" in request.form:
        id_encrypted = request.form["id_lettre_contrat"]
        id_dencrypted = encryptor("decrypt", id_encrypted)

        conn = get_connection()
        cursor = conn.cursor()

        # Requête sur la table lettre_contrat
        query = """
            SELECT * FROM lettre_contrat WHERE id_reference = %s
        """
        cursor.execute(query, (id_dencrypted,))
        row = cursor.fetchone()

        if not row:
            cursor.close()
            conn.close()
            return jsonify({})  # Aucun résultat trouvé

        columns = [desc[0] for desc in cursor.description]
        row_dict = dict(zip(columns, row))

        data = {
            "id_lettre_contrat": encryptor(
                "encrypt", str(row_dict.get("id_lettre_contrat", ""))
            ),
            "corps_text": row_dict.get("corps_text", ""),
        }

        cursor.close()
        conn.close()

        print("✅ Lettre contrat récupérée:", data)
        return jsonify(data)

    elif "id_lettre_attestation" in request.form:
        id_encrypted = request.form["id_lettre_attestation"]
        id_dencrypted = encryptor("decrypt", id_encrypted)

        conn = get_connection()
        cursor = conn.cursor()

        # Requête sur la table lettre_contrat
        query = """
            SELECT * FROM lettre_attestation WHERE id_reference = %s
        """
        cursor.execute(query, (id_dencrypted,))
        row = cursor.fetchone()

        if not row:
            cursor.close()
            conn.close()
            return jsonify({})  # Aucun résultat trouvé

        columns = [desc[0] for desc in cursor.description]
        row_dict = dict(zip(columns, row))

        data = {
            "id_lettre_attestation": encryptor(
                "encrypt", str(row_dict.get("id_lettre_attestation", ""))
            ),
            "corps_attestation": row_dict.get("corps_text", ""),
        }

        cursor.close()
        conn.close()

        print("✅ Lettre attestation récupérée:", data)
        return jsonify(data)

    elif "id_lettre_certificat" in request.form:

        id_encrypted = request.form["id_lettre_certificat"]
        id_dencrypted = encryptor("decrypt", id_encrypted)

        conn = get_connection()
        cursor = conn.cursor()

        # Requête sur la table lettre_contrat
        query = """
            SELECT * FROM lettre_certificat_travail WHERE id_reference = %s
        """
        cursor.execute(query, (id_dencrypted,))
        row = cursor.fetchone()

        if not row:
            cursor.close()
            conn.close()
            return jsonify({})  # Aucun résultat trouvé

        columns = [desc[0] for desc in cursor.description]
        row_dict = dict(zip(columns, row))

        data = {
            "id_lettre_certificat_travail": encryptor(
                "encrypt", str(row_dict.get("id_lettre_certificat_travail", ""))
            ),
            "corps_certificat_travail": row_dict.get("corps_text", ""),
        }

        cursor.close()
        conn.close()

        print("✅ Lettre certificat travail récupérée:", data)
        return jsonify(data)

    elif "id_lettre_domiciliation" in request.form:

        id_encrypted = request.form["id_lettre_domiciliation"]
        id_dencrypted = encryptor("decrypt", id_encrypted)

        conn = get_connection()
        cursor = conn.cursor()

        # Requête sur la table lettre_contrat
        query = """
            SELECT * FROM lettre_domiciliation_salaire WHERE id_reference = %s
        """
        cursor.execute(query, (id_dencrypted,))
        row = cursor.fetchone()

        if not row:
            cursor.close()
            conn.close()
            return jsonify({})  # Aucun résultat trouvé

        columns = [desc[0] for desc in cursor.description]
        row_dict = dict(zip(columns, row))

        data = {
            "id_lettre_domiciliation_salaire": encryptor(
                "encrypt", str(row_dict.get("id_lettre_domiciliation_salaire", ""))
            ),
            "corps_domiciliation_salaire": row_dict.get("corps_text", ""),
        }

        cursor.close()
        conn.close()

        print("✅ Lettre domiciliation salaire récupérée:", data)
        return jsonify(data)

    elif "id_lettre_affectation" in request.form:

        id_encrypted = request.form["id_lettre_affectation"]
        id_dencrypted = encryptor("decrypt", id_encrypted)

        conn = get_connection()
        cursor = conn.cursor()

        # Requête sur la table lettre_contrat
        query = """
            SELECT * FROM lettre_affectation WHERE id_reference = %s
        """
        cursor.execute(query, (id_dencrypted,))
        row = cursor.fetchone()

        if not row:
            cursor.close()
            conn.close()
            return jsonify({})  # Aucun résultat trouvé

        columns = [desc[0] for desc in cursor.description]
        row_dict = dict(zip(columns, row))

        data = {
            "id_lettre_affectation": encryptor(
                "encrypt", str(row_dict.get("id_lettre_affectation", ""))
            ),
            "corps_affectation": row_dict.get("corps_text", ""),
        }

        cursor.close()
        conn.close()

        print("✅ Lettre affectation récupérée:", data)
        return jsonify(data)

    elif "id_lettre_indemnite" in request.form:

        id_encrypted = request.form["id_lettre_indemnite"]
        id_dencrypted = encryptor("decrypt", id_encrypted)

        conn = get_connection()
        cursor = conn.cursor()

        # Requête sur la table lettre_contrat
        query = """
            SELECT * FROM lettre_indemnite WHERE id_reference = %s
        """
        cursor.execute(query, (id_dencrypted,))
        row = cursor.fetchone()

        if not row:
            cursor.close()
            conn.close()
            return jsonify({})  # Aucun résultat trouvé

        columns = [desc[0] for desc in cursor.description]
        row_dict = dict(zip(columns, row))

        data = {
            "id_lettre_indemnite": encryptor(
                "encrypt", str(row_dict.get("id_lettre_indemnite", ""))
            ),
            "corps_indemnite": row_dict.get("corps_text", ""),
        }

        cursor.close()
        conn.close()

        print("✅ Lettre demande indémnité récupérée:", data)
        return jsonify(data)

    elif "id_lettre_conge_annuel" in request.form:

        id_encrypted = request.form["id_lettre_conge_annuel"]
        id_dencrypted = encryptor("decrypt", id_encrypted)

        conn = get_connection()
        cursor = conn.cursor()

        # Requête sur la table lettre_contrat
        query = """
            SELECT * FROM lettre_conge_annuel WHERE id_reference = %s
        """
        cursor.execute(query, (id_dencrypted,))
        row = cursor.fetchone()

        if not row:
            cursor.close()
            conn.close()
            return jsonify({})  # Aucun résultat trouvé

        columns = [desc[0] for desc in cursor.description]
        row_dict = dict(zip(columns, row))

        data = {
            "id_lettre_conge_annuel": encryptor(
                "encrypt", str(row_dict.get("id_lettre_conge_annuel", ""))
            ),
            "corps_conge_annuel": row_dict.get("corps_text", ""),
        }

        cursor.close()
        conn.close()

        print("✅ Lettre congé annuel récupérée:", data)
        return jsonify(data)

    elif "id_lettre_cessation" in request.form:

        id_encrypted = request.form["id_lettre_cessation"]
        id_dencrypted = encryptor("decrypt", id_encrypted)

        conn = get_connection()
        cursor = conn.cursor()

        # Requête sur la table lettre_contrat
        query = """
            SELECT * FROM lettre_cessation WHERE id_reference = %s
        """
        cursor.execute(query, (id_dencrypted,))
        row = cursor.fetchone()

        if not row:
            cursor.close()
            conn.close()
            return jsonify({})  # Aucun résultat trouvé

        columns = [desc[0] for desc in cursor.description]
        row_dict = dict(zip(columns, row))

        data = {
            "id_lettre_cessation": encryptor(
                "encrypt", str(row_dict.get("id_lettre_cessation", ""))
            ),
            "corps_cessation": row_dict.get("corps_text", ""),
        }

        cursor.close()
        conn.close()

        print("✅ Lettre cessation récupérée:", data)
        return jsonify(data)

    elif "id_lettre_decision" in request.form:

        id_encrypted = request.form["id_lettre_decision"]
        id_dencrypted = encryptor("decrypt", id_encrypted)

        conn = get_connection()
        cursor = conn.cursor()

        # Requête sur la table lettre_contrat
        query = """
            SELECT * FROM lettre_decision WHERE id_reference = %s
        """
        cursor.execute(query, (id_dencrypted,))
        row = cursor.fetchone()

        if not row:
            cursor.close()
            conn.close()
            return jsonify({})  # Aucun résultat trouvé

        columns = [desc[0] for desc in cursor.description]
        row_dict = dict(zip(columns, row))

        data = {
            "id_lettre_decision": encryptor(
                "encrypt", str(row_dict.get("id_lettre_decision", ""))
            ),
            "corps_decision": row_dict.get("corps_text", ""),
        }

        cursor.close()
        conn.close()

        print("✅ Lettre decision récupérée:", data)
        return jsonify(data)

    elif "id_lettre_transmission" in request.form:

        id_encrypted = request.form["id_lettre_transmission"]
        id_dencrypted = encryptor("decrypt", id_encrypted)

        conn = get_connection()
        cursor = conn.cursor()

        # Requête sur la table lettre_contrat
        query = """
            SELECT * FROM lettre_transmission WHERE id_reference = %s
        """
        cursor.execute(query, (id_dencrypted,))
        row = cursor.fetchone()

        if not row:
            cursor.close()
            conn.close()
            return jsonify({})  # Aucun résultat trouvé

        columns = [desc[0] for desc in cursor.description]
        row_dict = dict(zip(columns, row))

        data = {
            "id_lettre_transmission": encryptor(
                "encrypt", str(row_dict.get("id_lettre_transmission", ""))
            ),
            "corps_transmission": row_dict.get("corps_text", ""),
        }

        cursor.close()
        conn.close()

        print("✅ Lettre transmission récupérée:", data)
        return jsonify(data)

    else:
        # Erreur : aucun identifiant fourni
        return jsonify({"error": "Paramètre id_lettre_contrat manquant"}), 400
