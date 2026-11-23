import os
import time
from flask import request, jsonify
from templates.include.connect import get_connection
from templates.include.encryptor import encryptor

UPLOAD_LOGO_FOLDER = os.path.join("static", "img", "logo")
UPLOAD_DRAPEAU_FOLDER = os.path.join("static", "img", "drapeau")

os.makedirs(UPLOAD_LOGO_FOLDER, exist_ok=True)
os.makedirs(UPLOAD_DRAPEAU_FOLDER, exist_ok=True)


def save_reference():
    conn = None
    cursor = None
    try:
        print("Form reçu:", request.form)
        print("Fichiers reçus:", request.files)

        conn = get_connection()
        cursor = conn.cursor()

        republique = request.form.get("republique", "")
        devise = request.form.get("devise", "")
        ministere = request.form.get("ministere", "")
        entreprise = request.form.get("entreprise", "")
        adresse = request.form.get("adresse", "")
        telephone = request.form.get("telephone", "")
        fax = request.form.get("fax", "")
        bp = request.form.get("bp", "")
        email = request.form.get("email", "")
        web = request.form.get("web", "")

        logo_file = request.files.get("logo")
        drapeau_file = request.files.get("drapeau")

        logo_filename = None
        drapeau_filename = None

        timestamp = int(time.time())

        if logo_file and logo_file.filename:
            logo_filename = f"{timestamp}_logo.jpg"
            logo_file.save(os.path.join(UPLOAD_LOGO_FOLDER, logo_filename))

        if drapeau_file and drapeau_file.filename:
            drapeau_filename = f"{timestamp}_drapeau.jpg"
            drapeau_file.save(os.path.join(UPLOAD_DRAPEAU_FOLDER, drapeau_filename))

        if "insert_id" in request.form:
            iduser_enc = request.form.get("iduser")
            iduser = encryptor("decrypt", iduser_enc) if iduser_enc else None

            query = """
                INSERT INTO reference
                (logo, republique, devise, ministere, entreprise, adresse, telephone, fax, bp, email, web, drapeau, iduser)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """
            cursor.execute(
                query,
                (
                    logo_filename,
                    republique,
                    devise,
                    ministere,
                    entreprise,
                    adresse,
                    telephone,
                    fax,
                    bp,
                    email,
                    web,
                    drapeau_filename,
                    iduser,
                ),
            )
            new_id = cursor.lastrowid
            conn.commit()

            return jsonify(
                {
                    "status": "success",
                    "message": "Référence insérée",
                    "new_id_encrypted": encryptor("encrypt", str(new_id)),
                }
            )

        elif "edit_id" in request.form:
            id_ref_enc = request.form.get("edit_id")
            id_reference = encryptor("decrypt", id_ref_enc)

            update_fields = []
            params = []

            if logo_filename:
                update_fields.append("logo=%s")
                params.append(logo_filename)
            if drapeau_filename:
                update_fields.append("drapeau=%s")
                params.append(drapeau_filename)

            update_fields.extend(
                [
                    "republique=%s",
                    "devise=%s",
                    "ministere=%s",
                    "entreprise=%s",
                    "adresse=%s",
                    "telephone=%s",
                    "fax=%s",
                    "bp=%s",
                    "email=%s",
                    "web=%s",
                ]
            )
            params.extend(
                [
                    republique,
                    devise,
                    ministere,
                    entreprise,
                    adresse,
                    telephone,
                    fax,
                    bp,
                    email,
                    web,
                ]
            )

            params.append(id_reference)

            query = (
                "UPDATE reference SET "
                + ", ".join(update_fields)
                + " WHERE id_reference=%s"
            )
            cursor.execute(query, tuple(params))
            conn.commit()

            return jsonify(
                {
                    "status": "success",
                    "message": "Référence mise à jour",
                    "id_reference_encrypted": id_ref_enc,
                }
            )

        else:
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": "Aucune action (insert_id ou edit_id)",
                    }
                ),
                400,
            )

    except Exception as e:
        print("Erreur save_reference:", e)
        return jsonify({"status": "error", "message": str(e)}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
