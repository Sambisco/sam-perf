import os
import time
import random
from PIL import Image, ExifTags
from flask import request, jsonify, current_app
from werkzeug.utils import secure_filename
from templates.include.connect import get_connection
from templates.include.encryptor import encryptor


def generate_unique_matricule(cursor):
    """Génère un matricule unique à 6 chiffres"""
    while True:
        matricule = str(random.randint(100000, 999999))
        cursor.execute("SELECT 1 FROM employe WHERE matricule = %s", (matricule,))
        if cursor.fetchone() is None:
            return matricule


def fix_image_orientation(img):
    """Corrige l’orientation EXIF des photos de téléphone."""
    try:
        for orientation in ExifTags.TAGS.keys():
            if ExifTags.TAGS[orientation] == "Orientation":
                break
        exif = img._getexif()
        if exif is None:
            return img
        orientation_value = exif.get(orientation, None)
        if orientation_value == 3:
            img = img.rotate(180, expand=True)
        elif orientation_value == 6:
            img = img.rotate(270, expand=True)
        elif orientation_value == 8:
            img = img.rotate(90, expand=True)
    except Exception:
        pass
    return img


def save_photo_file(photo_file, matricule):
    """Sauvegarde la photo sans compression et sans limitation de taille."""

    if not photo_file or not hasattr(photo_file, "filename"):
        raise ValueError("Fichier photo invalide")

    original_name = secure_filename(photo_file.filename or "")
    if not original_name:
        raise ValueError("Nom de fichier invalide")

    folder_path = os.path.join(
        current_app.root_path, "static", "img", "img_employe", str(matricule)
    )
    os.makedirs(folder_path, exist_ok=True)

    # 🔹 Crée un .gitkeep si le dossier est vide
    gitkeep_path = os.path.join(folder_path, ".gitkeep")
    if not os.listdir(folder_path):
        open(gitkeep_path, "a").close()
        os.chmod(gitkeep_path, 0o664)

    filename = f"{matricule}_{int(time.time())}.jpg"
    filepath = os.path.join(folder_path, filename)

    try:
        img = Image.open(photo_file.stream)
        img = fix_image_orientation(img)
        img = img.convert("RGB")

        # ❗ AUCUNE compression, AUCUN redimensionnement
        img.save(filepath, "JPEG", quality=100)

        os.chmod(filepath, 0o664)

    except Exception as e:
        print(f"[ERROR] Erreur lors de la sauvegarde brute : {e}")
        raise

    return filename


def save_employe():
    conn = get_connection()
    cursor = conn.cursor()

    try:
        from datetime import datetime

        # ================= INSERT EMPLOYE =================
        if "insert_id" in request.form:
            date_n_str = request.form.get("date_n", "").strip()
            if date_n_str:
                date_n = datetime.strptime(date_n_str, "%Y-%m-%d")
                age = (datetime.now() - date_n).days / 365.25
                if age < 15:
                    return jsonify(
                        {
                            "status": "error",
                            "message": "L'âge doit être au moins 15 ans.",
                        }
                    )

            matricule = generate_unique_matricule(cursor)
            photo_file = request.files.get("photo")
            photo_path = (
                save_photo_file(photo_file, matricule)
                if photo_file and photo_file.filename.strip()
                else ""
            )

            prenom = request.form.get("prenom", "").strip()
            nom = request.form.get("nom", "").strip()
            lieu_n = request.form.get("lieu_n", "").strip()
            adresse_e = request.form.get("adresse_e", "").strip()
            telephone_e = request.form.get("telephone_e", "").strip()
            email_e = request.form.get("email_e", "").strip()
            genre = request.form.get("genre", "").strip()
            poste = request.form.get("poste", "").strip()
            commission = request.form.get("commission", "").strip()
            id_reference = encryptor(
                "decrypt", request.form.get("id_reference", "").strip()
            )

            # CV
            cv_file = request.files.get("cv")
            nom_file = ""
            type_file = ""
            cv_content = None
            if cv_file and cv_file.filename.strip():
                nom_file = cv_file.filename
                type_file = cv_file.mimetype
                cv_content = cv_file.read()

            query = """
                INSERT INTO employe (photo, matricule, prenom, nom, date_n, lieu_n, adresse_e, telephone_e, email_e,
                genre, poste, nom_file, type_file, cv, commission, id_reference)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """
            cursor.execute(
                query,
                (
                    photo_path,
                    matricule,
                    prenom,
                    nom,
                    date_n_str,
                    lieu_n,
                    adresse_e,
                    telephone_e,
                    email_e,
                    genre,
                    poste,
                    nom_file,
                    type_file,
                    cv_content,
                    commission,
                    id_reference,
                ),
            )
            conn.commit()
            return jsonify(
                {"status": "success", "message": "Employé ajouté avec succès."}
            )

        # ================= EDIT EMPLOYE =================
        elif "edit_id" in request.form:
            edit_id = encryptor("decrypt", request.form.get("edit_id", "").strip())
            matricule = request.form.get("matricule", "").strip()
            photo_file = request.files.get("photo")
            photo_path = (
                save_photo_file(photo_file, matricule)
                if photo_file and photo_file.filename.strip()
                else None
            )

            prenom = request.form.get("prenom", "").strip()
            nom = request.form.get("nom", "").strip()
            date_n_str = request.form.get("date_n", "").strip()
            lieu_n = request.form.get("lieu_n", "").strip()
            adresse_e = request.form.get("adresse_e", "").strip()
            telephone_e = request.form.get("telephone_e", "").strip()
            email_e = request.form.get("email_e", "").strip()
            genre = request.form.get("genre", "").strip()
            poste = request.form.get("poste", "").strip()
            commission = request.form.get("commission", "").strip()

            cv_file = request.files.get("cv")
            nom_file = ""
            type_file = ""
            cv_content = None
            if cv_file and cv_file.filename.strip():
                nom_file = cv_file.filename
                type_file = cv_file.mimetype
                cv_content = cv_file.read()

            # Construction query selon la présence de photo et CV
            if photo_path and cv_content:
                query = """
                    UPDATE employe SET photo=%s, prenom=%s, nom=%s, date_n=%s, lieu_n=%s, adresse_e=%s, telephone_e=%s, email_e=%s,
                    genre=%s, poste=%s, nom_file=%s, type_file=%s, cv=%s, commission=%s WHERE id_employe=%s
                """
                params = (
                    photo_path,
                    prenom,
                    nom,
                    date_n_str,
                    lieu_n,
                    adresse_e,
                    telephone_e,
                    email_e,
                    genre,
                    poste,
                    nom_file,
                    type_file,
                    cv_content,
                    commission,
                    edit_id,
                )
            elif photo_path:
                query = """
                    UPDATE employe SET photo=%s, prenom=%s, nom=%s, date_n=%s, lieu_n=%s, adresse_e=%s, telephone_e=%s, email_e=%s,
                    genre=%s, poste=%s, commission=%s WHERE id_employe=%s
                """
                params = (
                    photo_path,
                    prenom,
                    nom,
                    date_n_str,
                    lieu_n,
                    adresse_e,
                    telephone_e,
                    email_e,
                    genre,
                    poste,
                    commission,
                    edit_id,
                )
            elif cv_content:
                query = """
                    UPDATE employe SET prenom=%s, nom=%s, date_n=%s, lieu_n=%s, adresse_e=%s, telephone_e=%s, email_e=%s,
                    genre=%s, poste=%s, nom_file=%s, type_file=%s, cv=%s, commission=%s WHERE id_employe=%s
                """
                params = (
                    prenom,
                    nom,
                    date_n_str,
                    lieu_n,
                    adresse_e,
                    telephone_e,
                    email_e,
                    genre,
                    poste,
                    nom_file,
                    type_file,
                    cv_content,
                    commission,
                    edit_id,
                )
            else:
                query = """
                    UPDATE employe SET prenom=%s, nom=%s, date_n=%s, lieu_n=%s, adresse_e=%s, telephone_e=%s, email_e=%s,
                    genre=%s, poste=%s, commission=%s WHERE id_employe=%s
                """
                params = (
                    prenom,
                    nom,
                    date_n_str,
                    lieu_n,
                    adresse_e,
                    telephone_e,
                    email_e,
                    genre,
                    poste,
                    commission,
                    edit_id,
                )

            cursor.execute(query, params)
            conn.commit()
            return jsonify(
                {"status": "success", "message": "Employé mis à jour avec succès."}
            )

        # ================= DELETE EMPLOYE =================
        elif "delete_id" in request.form:
            delete_id = encryptor("decrypt", request.form.get("delete_id", "").strip())
            cursor.execute("DELETE FROM employe WHERE id_employe = %s", (delete_id,))
            conn.commit()
            return jsonify(
                {"status": "success", "message": "Employé supprimé avec succès."}
            )

        # ================= UPDATE EMPLOYE ACTIF =================
        elif "update_employe_actif" in request.form:
            update_id = encryptor(
                "decrypt", request.form.get("update_employe_actif", "").strip()
            )
            matricule = request.form.get("matricule", "").strip()
            photo_file = request.files.get("photo")
            photo_path = (
                save_photo_file(photo_file, matricule)
                if photo_file and photo_file.filename.strip()
                else None
            )

            prenom = request.form.get("prenom", "").strip()
            nom = request.form.get("nom", "").strip()
            date_n_str = request.form.get("date_n", "").strip()
            lieu_n = request.form.get("lieu_n", "").strip()
            adresse_e = request.form.get("adresse_e", "").strip()
            telephone_e = request.form.get("telephone_e", "").strip()
            email_e = request.form.get("email_e", "").strip()
            genre = request.form.get("genre", "").strip()

            if photo_path:
                query = """
                    UPDATE employe SET photo=%s, prenom=%s, nom=%s, date_n=%s, lieu_n=%s, adresse_e=%s,
                    telephone_e=%s, email_e=%s, genre=%s WHERE id_employe=%s
                """
                params = (
                    photo_path,
                    prenom,
                    nom,
                    date_n_str,
                    lieu_n,
                    adresse_e,
                    telephone_e,
                    email_e,
                    genre,
                    update_id,
                )
            else:
                query = """
                    UPDATE employe SET prenom=%s, nom=%s, date_n=%s, lieu_n=%s, adresse_e=%s,
                    telephone_e=%s, email_e=%s, genre=%s WHERE id_employe=%s
                """
                params = (
                    prenom,
                    nom,
                    date_n_str,
                    lieu_n,
                    adresse_e,
                    telephone_e,
                    email_e,
                    genre,
                    update_id,
                )

            cursor.execute(query, params)
            conn.commit()
            return jsonify(
                {"status": "success", "message": "Employé actif mis à jour."}
            )

        # ================= PHOTO DELETE =================
        elif "photo_delete" in request.form:
            matricule = request.form.get("matricule")
            filename = request.form.get("photo_delete")
            if not matricule or not filename:
                return (
                    jsonify(
                        {"status": "error", "message": "Matricule ou fichier manquant"}
                    ),
                    400,
                )

            folder_path = os.path.join(
                current_app.root_path, "static", "img", "img_employe", matricule
            )
            file_path = os.path.join(folder_path, filename)

            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    return jsonify(
                        {
                            "status": "success",
                            "message": f"Fichier {filename} supprimé.",
                        }
                    )
                else:
                    return (
                        jsonify({"status": "error", "message": "Fichier introuvable"}),
                        404,
                    )
            except Exception as e:
                return jsonify({"status": "error", "message": str(e)}), 500

        # ================= PHOTO UPDATE PROFIL =================
        elif "photo_update_profil" in request.form:
            id_employe = encryptor("decrypt", request.form.get("id_employe")).strip()
            photo = request.form.get("photo_update_profil")
            query = "UPDATE employe SET photo=%s WHERE id_employe=%s"
            cursor.execute(query, (photo, id_employe))
            conn.commit()
            return jsonify(
                {"status": "success", "message": "Photo profil mise à jour."}
            )

        # ================= INSERT PHOTO PROFIL =================
        elif "insert_photo_profil" in request.form:
            id_employe = encryptor("decrypt", request.form.get("id_employe")).strip()
            matricule = request.form.get("matricule").strip()
            photo_file = request.files.get("photo")
            photo_path = (
                save_photo_file(photo_file, matricule)
                if photo_file and photo_file.filename.strip()
                else None
            )

            query = "UPDATE employe SET photo=%s WHERE id_employe=%s"
            cursor.execute(query, (photo_path, id_employe))
            conn.commit()
            return jsonify({"status": "success", "message": "Photo profil ajoutée."})

        else:
            return jsonify({"status": "error", "message": "Paramètres manquants."})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

    finally:
        cursor.close()
        conn.close()
