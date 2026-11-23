import os
from flask import request, jsonify
from templates.include.connect import get_connection
from templates.include.encryptor import encryptor


def save_depart():
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # INSERT
        if request.method == "POST" and "insert_id" in request.form:
            id_contrat = encryptor(
                "decrypt", request.form.get("id_contrat", "")
            ).strip()
            date_effet = request.form.get("date_effet", "").strip()
            motif = request.form.get("motif", "").strip()
            suspensalaire = request.form.get("suspensalaire", "").strip()
            fichier = request.files.get("fichier")

            # Vérifier si le contrat a déjà un départ
            cursor.execute("SELECT 1 FROM depart WHERE id_contrat = %s", (id_contrat,))
            if cursor.fetchone():
                return jsonify(
                    {
                        "status": "exist",
                        "message": "Départ déjà existant pour ce contrat",
                    }
                )

            if fichier and fichier.filename:
                name = fichier.filename
                type_fichier = fichier.mimetype
                fichier_data = fichier.read()
                insert_query = """
                    INSERT INTO depart(date_effet, motif, name, type, fichier, suspensalaire, id_contrat)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """
                values = (
                    date_effet,
                    motif,
                    name,
                    type_fichier,
                    fichier_data,
                    suspensalaire,
                    id_contrat,
                )
            else:
                insert_query = """
                    INSERT INTO depart(date_effet, motif, suspensalaire, id_contrat)
                    VALUES (%s, %s, %s, %s)
                """
                values = (date_effet, motif, suspensalaire, id_contrat)

            cursor.execute(insert_query, values)
            conn.commit()
            return jsonify({"status": "ok", "message": "Départ enregistré"})

        # UPDATE
        elif request.method == "POST" and "edit_id" in request.form:
            id_depart = encryptor("decrypt", request.form.get("edit_id", "")).strip()
            date_effet = request.form.get("date_effet", "").strip()
            motif = request.form.get("motif", "").strip()
            suspensalaire = request.form.get("suspensalaire", "").strip()
            fichier = request.files.get("fichier")

            if not fichier or fichier.filename == "":
                update_query = """
                    UPDATE depart SET date_effet=%s, motif=%s, suspensalaire=%s
                    WHERE id_depart=%s
                """
                values = (date_effet, motif, suspensalaire, id_depart)
            else:
                name = fichier.filename
                type_fichier = fichier.mimetype
                fichier_data = fichier.read()
                update_query = """
                    UPDATE depart SET date_effet=%s, motif=%s, name=%s, type=%s, fichier=%s, suspensalaire=%s
                    WHERE id_depart=%s
                """
                values = (
                    date_effet,
                    motif,
                    name,
                    type_fichier,
                    fichier_data,
                    suspensalaire,
                    id_depart,
                )

            cursor.execute(update_query, values)
            conn.commit()
            return jsonify({"status": "ok", "message": "Départ mis à jour"})

        # DELETE
        elif request.method == "POST" and "delete_id" in request.form:
            id_depart = encryptor("decrypt", request.form.get("delete_id", "")).strip()
            delete_query = "DELETE FROM depart WHERE id_depart = %s"
            cursor.execute(delete_query, (id_depart,))
            conn.commit()
            return jsonify({"status": "ok", "message": "Départ supprimé"})

        # Aucun cas détecté
        else:
            return jsonify({"status": "error", "message": "Requête non valide"})

    except Exception as e:
        print("Erreur :", e)
        return jsonify({"status": "error", "message": str(e)})

    finally:
        cursor.close()
        conn.close()
