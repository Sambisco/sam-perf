from flask import Flask, request, jsonify
import os, time, hashlib
from templates.include.connect import get_connection
from templates.include.encryptor import encryptor


UPLOAD_LOGO_FOLDER = os.path.join("static", "img", "user")
os.makedirs(UPLOAD_LOGO_FOLDER, exist_ok=True)


def save_user():
    response = {"status": "error", "message": "Action non reconnue"}
    db = get_connection()
    cursor = db.cursor(dictionary=True)

    try:
        # ===================== INSERT =====================
        if "insert_id" in request.form:
            photo_file = request.files.get("photo")
            photo_filename = None
            timestamp = int(time.time())

            if photo_file and photo_file.filename:
                photo_filename = f"{timestamp}_photo.jpg"
                photo_file.save(os.path.join(UPLOAD_LOGO_FOLDER, photo_filename))

            photo_filename = photo_filename or ""
            nom_sub_user = request.form.get("nom_sub_user", "").strip()
            telephone_sub_user = request.form.get("telephone_sub_user", "").strip()
            sub_email = request.form.get("sub_email", "").strip().lower()
            profil = request.form.get("profil", "").strip()
            sub_password = hashlib.md5(
                request.form.get("sub_password", "").encode()
            ).hexdigest()
            id_reference = encryptor(
                "decrypt", request.form.get("id_reference", "").strip()
            )

            # Vérification doublon
            query = """
                SELECT * FROM user
                LEFT JOIN reference ON reference.iduser=user.iduser
                LEFT JOIN sub_users ON sub_users.id_reference=reference.id_reference
                WHERE sub_email=%s OR telephone_sub_user=%s OR login=%s OR telephone_user=%s
                LIMIT 1
            """
            cursor.execute(
                query, (sub_email, telephone_sub_user, sub_email, telephone_sub_user)
            )
            result = cursor.fetchall()
            if result:
                response["status"] = "exists"
                response["message"] = "L'utilisateur existe déjà."
                return jsonify(response)

            insert_query = """
                INSERT INTO sub_users(nom_sub_user, telephone_sub_user, sub_email, profil, sub_password, photo, id_reference)
                VALUES (%s,%s,%s,%s,%s,%s,%s)
            """
            cursor.execute(
                insert_query,
                (
                    nom_sub_user,
                    telephone_sub_user,
                    sub_email,
                    profil,
                    sub_password,
                    photo_filename,
                    id_reference,
                ),
            )
            db.commit()

            response["status"] = "success"
            response["message"] = "Enregistrement effectué avec succès."
            return jsonify(response)

        # ===================== EDIT =====================
        if "edit_id" in request.form:
            id_sub = encryptor("decrypt", request.form.get("edit_id", "").strip())
            nom_sub_user = request.form.get("nom_sub_user", "").strip()
            telephone_sub_user = request.form.get("telephone_sub_user", "").strip()
            sub_email = request.form.get("sub_email", "").strip().lower()
            profil = request.form.get("profil", "").strip()
            sub_password_raw = request.form.get("sub_password", "")
            sub_password = (
                hashlib.md5(sub_password_raw.encode()).hexdigest()
                if sub_password_raw
                else None
            )

            photo_file = request.files.get("photo")
            photo_filename = None
            timestamp = int(time.time())

            if photo_file and photo_file.filename:
                photo_filename = f"{timestamp}_photo.jpg"
                photo_file.save(os.path.join(UPLOAD_LOGO_FOLDER, photo_filename))

            update_fields = [
                "nom_sub_user=%s",
                "telephone_sub_user=%s",
                "sub_email=%s",
                "profil=%s",
            ]
            values = [nom_sub_user, telephone_sub_user, sub_email, profil]

            if sub_password:
                update_fields.append("sub_password=%s")
                values.append(sub_password)
            if photo_filename:
                update_fields.append("photo=%s")
                values.append(photo_filename)

            values.append(id_sub)
            update_query = (
                f"UPDATE sub_users SET {', '.join(update_fields)} WHERE id_sub_users=%s"
            )
            cursor.execute(update_query, tuple(values))
            db.commit()

            response["status"] = "success"
            response["message"] = "Modification effectuée avec succès."
            return jsonify(response)

        # ===================== DELETE =====================
        if "delete_id" in request.form:
            id_sub = encryptor("decrypt", request.form.get("delete_id", "").strip())
            delete_query = "DELETE FROM sub_users WHERE id_sub_users=%s"
            cursor.execute(delete_query, (id_sub,))
            db.commit()

            response["status"] = "success"
            response["message"] = "Utilisateur supprimé avec succès."
            return jsonify(response)

    except Exception as e:
        response["status"] = "error"
        response["message"] = str(e)
        return jsonify(response)

    return jsonify(response)
