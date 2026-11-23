import os
import time
from datetime import datetime
import random
from PIL import Image
from io import BytesIO
from flask import Flask, request, jsonify, current_app
from templates.include.connect import get_connection
from templates.include.encryptor import encryptor


def save_demande_absence():
    conn = get_connection()
    cursor = conn.cursor()

    try:
        if "insert_id" in request.form:
            id_contrat = encryptor("decrypt", request.form.get("id_contrat", "").strip())
            periode_du = request.form.get("periode_du", "").strip()
            periode_au = request.form.get("periode_au", "").strip()
            superieur_hierarchique = request.form.get("superieur_hierarchique", "").strip()
            fonction_superieur = request.form.get("fonction_superieur", "").strip()
            motif = request.form.get("motif", "").strip()
            Imputable_sur_les_normaux = request.form.get("Imputable_sur_les_normaux", "").strip()
            precision_employe = request.form.get("precision_employe", "").strip()
            nbr_jour = request.form.get("nbr_jour", "").strip()
            date_v = datetime.now().strftime("%Y-%m-%d")

            # === Requête INSERT ===
            query = """
               INSERT INTO demande_absence
               (periode_du, periode_au, nbr_jour, superieur_hierarchique, fonction_superieur, 
                motif, Imputable_sur_les_normaux, precision_employe, date_v, id_contrat)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
           """
            values = (
               periode_du,
               periode_au,
               nbr_jour,
               superieur_hierarchique,
               fonction_superieur,
               motif,
               Imputable_sur_les_normaux,
               precision_employe,
               date_v,
               id_contrat,
           )

            cursor.execute(query, values)
            conn.commit()

            return jsonify({"status": "success", "message": "Demande d'absence enregistrée avec succès."})

        elif "edit_id" in request.form:
            edit_id = encryptor("decrypt", request.form.get("edit_id", "").strip())

            avis_rh = request.form.get("avis_rh", "").strip()
            avis = request.form.get("avis", "").strip()
            precision_superieur = request.form.get("precision_superieur", "").strip()

            fichier = request.files.get("fichier")
            nom_file = ""
            type_file = ""
            fichier_content = None
            if fichier and fichier.filename:
                nom_file = fichier.filename
                type_file = fichier.mimetype
                fichier_content = fichier.read()

            query = """
               UPDATE demande_absence SET name = %s,type = %s,fichier = %s,avis = %s,precision_superieur = %s,avis_rh = %s WHERE id_demande_absence = %s
            """
            params = (
                nom_file,
                type_file,
                fichier_content,
                avis,
                precision_superieur,
                avis_rh,
                edit_id,
            )

            cursor.execute(query, (params))
            conn.commit()
            return jsonify(
                {"status": "success", "message": "Demande mis à jour avec succès."}
            )

        elif "edit_id_emp" in request.form:
            edit_id = encryptor("decrypt", request.form.get("edit_id_emp", "").strip())
            periode_du = request.form.get("periode_du", "").strip()
            periode_au = request.form.get("periode_au", "").strip()
            superieur_hierarchique = request.form.get("superieur_hierarchique", "").strip()
            fonction_superieur = request.form.get("fonction_superieur", "").strip()
            motif = request.form.get("motif", "").strip()
            Imputable_sur_les_normaux = request.form.get("Imputable_sur_les_normaux", "").strip()
            precision_employe = request.form.get("precision_employe", "").strip()
            nbr_jour = request.form.get("nbr_jour", "").strip()

            # === Requête UPDATE ===
            query = """
                UPDATE demande_absence 
                SET periode_du=%s, 
                    periode_au=%s, 
                    nbr_jour=%s, 
                    superieur_hierarchique=%s, 
                    fonction_superieur=%s, 
                    motif=%s, 
                    Imputable_sur_les_normaux=%s, 
                    precision_employe=%s
                WHERE id_demande_absence=%s
            """
            values = (
                periode_du,
                periode_au,
                nbr_jour,
                superieur_hierarchique,
                fonction_superieur,
                motif,
                Imputable_sur_les_normaux,
                precision_employe,
                edit_id,
            )

            cursor.execute(query, values)
            conn.commit()

            return jsonify({"status": "success", "message": "Demande d'absence mise à jour avec succès."})

        else:
            return jsonify({"status": "error", "message": "Paramètres manquants."})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

    finally:
        cursor.close()
        conn.close()
