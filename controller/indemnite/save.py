from flask import Flask, request, jsonify
from templates.include.connect import get_connection
from templates.include.encryptor import encryptor


def clean_number(value: str) -> float:
    """Nettoie une chaîne formatée en nombre (ex: '1 234,56') et convertit en float."""
    if not value:
        return 0.0
    value = value.replace(" ", "").replace(",", ".")
    try:
        return float(value)
    except ValueError:
        return 0.0


def save_indemnite():
    conn = get_connection()
    cursor = conn.cursor()

    # INSERT
    if "insert_id" in request.form:
        try:
            id_contrat = encryptor("decrypt", request.form["id_contrat"].strip())
            compte = request.form["compte"].strip()
            annee_budget = request.form["annee_budget"].strip()
            date_enregistrement = request.form["date_enregistrement"].strip()
            date_effet = request.form["date_effet"].strip()
            salaire = clean_number(request.form.get("salaire", "").strip())
            fonction = clean_number(request.form.get("fonction", "").strip())
            sujetion = clean_number(request.form.get("sujetion", "").strip())
            responsabilite = clean_number(
                request.form.get("responsabilite", "").strip()
            )
            sursalaire = clean_number(request.form.get("sursalaire", "").strip())
            logement = clean_number(request.form.get("logement", "").strip())
            transport = clean_number(request.form.get("transport", "").strip())
            telephone_in = clean_number(request.form.get("telephone_in", "").strip())
            document_lettre = request.form.get("document_lettre", "")

            query = """
                INSERT INTO indemnite(compte, annee_budget, date_enregistrement, date_effet, fonction, sujetion, responsabilite, sursalaire, logement, transport, telephone_in, document_lettre, id_contrat)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(
                query,
                (
                    compte,
                    annee_budget,
                    date_enregistrement,
                    date_effet,
                    fonction,
                    sujetion,
                    responsabilite,
                    sursalaire,
                    logement,
                    transport,
                    telephone_in,
                    document_lettre,
                    id_contrat,
                ),
            )
            conn.commit()
            return jsonify({"message": "Insertion réussie"}), 201
        except Exception as e:
            conn.rollback()
            return jsonify({"error": str(e)}), 400

    # UPDATE
    elif "edit_id" in request.form:
        try:
            id_indemnite = encryptor("decrypt", request.form["edit_id"].strip())
            id_contrat = encryptor("decrypt", request.form["id_contrat"].strip())
            compte = request.form["compte"].strip()
            annee_budget = request.form["annee_budget"].strip()
            date_enregistrement = request.form["date_enregistrement"].strip()
            date_effet = request.form["date_effet"].strip()
            salaire = clean_number(request.form.get("salaire", "").strip())
            fonction = clean_number(request.form.get("fonction", "").strip())
            sujetion = clean_number(request.form.get("sujetion", "").strip())
            responsabilite = clean_number(
                request.form.get("responsabilite", "").strip()
            )
            sursalaire = clean_number(request.form.get("sursalaire", "").strip())
            logement = clean_number(request.form.get("logement", "").strip())
            transport = clean_number(request.form.get("transport", "").strip())
            telephone_in = clean_number(request.form.get("telephone_in", "").strip())
            document_lettre = request.form.get("document_lettre", "")

            query = """
                UPDATE indemnite
                SET compte=%s, annee_budget=%s, date_enregistrement=%s, date_effet=%s, fonction=%s, sujetion=%s, responsabilite=%s, sursalaire=%s, logement=%s, transport=%s, telephone_in=%s, document_lettre=%s
                WHERE id_indemnite=%s
            """
            cursor.execute(
                query,
                (
                    compte,
                    annee_budget,
                    date_enregistrement,
                    date_effet,
                    fonction,
                    sujetion,
                    responsabilite,
                    sursalaire,
                    logement,
                    transport,
                    telephone_in,
                    document_lettre,
                    id_indemnite,
                ),
            )
            conn.commit()
            return jsonify({"message": "Mise à jour réussie"}), 200
        except Exception as e:
            conn.rollback()
            return jsonify({"error": str(e)}), 400

    # DELETE
    elif "delete_id" in request.form:
        try:
            id_indemnite = encryptor("decrypt", request.form["delete_id"].strip())
            query = "DELETE FROM indemnite WHERE id_indemnite=%s"
            cursor.execute(query, (id_indemnite,))
            conn.commit()
            return jsonify({"message": "Suppression réussie"}), 200
        except Exception as e:
            conn.rollback()
            return jsonify({"error": str(e)}), 400

    else:
        return jsonify({"error": "Paramètre manquant"}), 400

    cursor.close()
    conn.close()
