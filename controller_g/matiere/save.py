from flask import request, jsonify
import os, time
from werkzeug.utils import secure_filename
from templates.include.connect import get_connection
from templates.include.encryptor import encryptor

UPLOAD_FOLDER = "static/img/matiere"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def save_photo(file):
    """Enregistre la photo et retourne le nom du fichier"""
    ext = file.filename.rsplit(".", 1)[-1].lower()
    filename = f"{int(time.time())}.png"
    path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(path)
    return filename


def save_matiere():
    try:
        # --- INSERT ---
        if "insert_id" in request.form:
            photo_filename = ""
            if "photo" in request.files and request.files["photo"].filename != "":
                photo_filename = save_photo(request.files["photo"])

            id_categorie_article = request.form["id_categorie_article"].strip()
            designation = request.form["designation"].strip()
            nbre_unite = request.form["nbre_unite"].replace(",", ".").replace(" ", "")
            nature_unite = request.form["nature_unite"].strip()

            with get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "SELECT COUNT(*) FROM matiere WHERE designation=%s",
                        (designation,),
                    )
                    if cursor.fetchone()[0] > 0:
                        return jsonify(
                            {"status": "true", "message": "Cette matière existe déjà."}
                        )

                    cursor.execute(
                        """
                        INSERT INTO matiere(image, designation, nbre_unite, nature_unite, id_categorie_article)
                        VALUES (%s, %s, %s, %s, %s)
                        """,
                        (
                            photo_filename,
                            designation,
                            nbre_unite,
                            nature_unite,
                            id_categorie_article,
                        ),
                    )
                    conn.commit()

            return jsonify(
                {"status": "success", "message": "Matière enregistrée avec succès."}
            )

        # --- EDIT ---
        elif "edit_id" in request.form:
            id_matiere = encryptor("decrypt", request.form["edit_id"]).strip()
            id_categorie_article = request.form["id_categorie_article"].strip()
            designation = request.form["designation"].strip()
            nbre_unite = request.form["nbre_unite"].replace(",", ".").replace(" ", "")
            nature_unite = request.form["nature_unite"].strip()

            photo_filename = None
            if "photo" in request.files and request.files["photo"].filename != "":
                photo_filename = save_photo(request.files["photo"])

            with get_connection() as conn:
                with conn.cursor() as cursor:
                    if photo_filename:
                        cursor.execute(
                            """
                            UPDATE matiere 
                            SET image=%s, designation=%s, nbre_unite=%s, nature_unite=%s, id_categorie_article=%s
                            WHERE id_matiere=%s
                            """,
                            (
                                photo_filename,
                                designation,
                                nbre_unite,
                                nature_unite,
                                id_categorie_article,
                                id_matiere,
                            ),
                        )
                    else:
                        cursor.execute(
                            """
                            UPDATE matiere 
                            SET designation=%s, nbre_unite=%s, nature_unite=%s, id_categorie_article=%s
                            WHERE id_matiere=%s
                            """,
                            (
                                designation,
                                nbre_unite,
                                nature_unite,
                                id_categorie_article,
                                id_matiere,
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
