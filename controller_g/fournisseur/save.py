from flask import request, jsonify
import os, time
from werkzeug.utils import secure_filename
from templates.include.connect import get_connection
from templates.include.encryptor import encryptor

UPLOAD_FOLDER = "static/img/fournisseur"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def save_photo(file):
    """Enregistre la photo et retourne le nom du fichier"""
    ext = file.filename.rsplit(".", 1)[-1].lower()
    filename = f"{int(time.time())}.png"
    path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(path)
    return filename


def save_fournisseur():
    try:
        # --- INSERT ---
        if "insert_id" in request.form:
            photo_filename = ""
            if "photo" in request.files and request.files["photo"].filename != "":
                photo_filename = save_photo(request.files["photo"])

            id_reference = encryptor("decrypt", request.form["id_reference"]).strip()
            fournisseur = request.form["fournisseur"].strip()
            adresse_f = request.form["adresse_f"].strip()
            telephone_f = request.form["telephone_f"].strip()
            email_f = request.form["email_f"].strip()
            ninea_f = request.form["ninea_f"].strip()
            nom_contact_f = request.form["nom_contact_f"].strip()

            with get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "SELECT COUNT(*) FROM fournisseur WHERE fournisseur=%s",
                        (fournisseur,),
                    )
                    if cursor.fetchone()[0] > 0:
                        return jsonify(
                            {"status": "true", "message": "Ce fournisseur existe déjà."}
                        )

                    cursor.execute(
                        """
                        INSERT INTO fournisseur(photo, fournisseur, adresse_f, telephone_f,email_f,ninea_f,nom_contact_f, id_reference)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        (
                            photo_filename,
                            fournisseur,
                            adresse_f,
                            telephone_f,
                            email_f,
                            ninea_f,
                            nom_contact_f,
                            id_reference,
                        ),
                    )
                    conn.commit()

            return jsonify(
                {"status": "success", "message": "Matière enregistrée avec succès."}
            )

        # --- EDIT ---
        elif "edit_id" in request.form:
            id = encryptor("decrypt", request.form["edit_id"]).strip()
            fournisseur = request.form["fournisseur"].strip()
            adresse_f = request.form["adresse_f"].strip()
            telephone_f = request.form["telephone_f"].strip()
            email_f = request.form["email_f"].strip()
            ninea_f = request.form["ninea_f"].strip()
            nom_contact_f = request.form["nom_contact_f"].strip()

            photo_filename = None
            if "photo" in request.files and request.files["photo"].filename != "":
                photo_filename = save_photo(request.files["photo"])

            with get_connection() as conn:
                with conn.cursor() as cursor:
                    if photo_filename:
                        cursor.execute(
                            """
                           UPDATE fournisseur SET photo= %s,fournisseur= %s,adresse_f= %s,telephone_f= %s,email_f= %s,ninea_f= %s,nom_contact_f= %s WHERE id_fournisseur= %s
                            """,
                            (
                                photo_filename,
                                fournisseur,
                                adresse_f,
                                telephone_f,
                                email_f,
                                ninea_f,
                                nom_contact_f,
                                id,
                            ),
                        )
                    else:
                        cursor.execute(
                            """
                            UPDATE fournisseur SET fournisseur= %s,adresse_f= %s,telephone_f= %s,email_f= %s,ninea_f= %s,nom_contact_f= %s WHERE id_fournisseur= %s
                            """,
                            (
                                fournisseur,
                                adresse_f,
                                telephone_f,
                                email_f,
                                ninea_f,
                                nom_contact_f,
                                id,
                            ),
                        )
                    conn.commit()

            return jsonify(
                {"status": "success", "message": "Matière modifiée avec succès."}
            )

        # --- DELETE ---
        elif "delete_id" in request.form:
            id_matiere = encryptor("decrypt", request.form["delete_id"]).strip()
            with get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "DELETE FROM matiere WHERE id_matiere=%s", (id_matiere,)
                    )
                    conn.commit()

            return jsonify(
                {"status": "success", "message": "Matière supprimée avec succès."}
            )

        else:
            return (
                jsonify({"status": "error", "message": "Aucun paramètre valide reçu."}),
                400,
            )

    except Exception as e:
        print("Erreur save_matiere:", e)
        return (
            jsonify(
                {"status": "error", "message": "Erreur serveur, réessayez plus tard."}
            ),
            500,
        )
