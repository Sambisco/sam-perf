from flask import request, jsonify
from datetime import datetime
from templates.include.connect import get_connection
from templates.include.encryptor import encryptor
import locale

locale.setlocale(locale.LC_TIME, "fr_FR.UTF-8")


def save_pointage():
    try:
        now = datetime.utcnow()
        date_now = now.strftime("%Y-%m-%d")
        time_now = now.strftime("%H:%M:%S")

        # ---------- CAS 1 : id_pointage ----------
        if "id_pointage" in request.form and "id_user" not in request.form:
            id_pointage = encryptor(
                "decrypt", request.form.get("id_pointage", "").strip()
            )
            if not id_pointage:
                return jsonify({"status": "error", "message": "id_pointage manquant"})

            with get_connection() as conn:
                with conn.cursor(dictionary=True) as cursor:
                    cursor.execute(
                        "SELECT * FROM pointage WHERE date=%s AND id_contrat=%s",
                        (date_now, id_pointage),
                    )
                    result = cursor.fetchone()

                    if result:
                        cursor.execute(
                            "UPDATE pointage SET heure_fin=%s WHERE date=%s AND id_contrat=%s",
                            (time_now, date_now, id_pointage),
                        )
                        message = "Heure de sortie enregistrée"
                    else:
                        cursor.execute(
                            "INSERT INTO pointage (date, heure_debut, heure_fin, id_contrat) VALUES (%s, %s, %s, %s)",
                            (date_now, time_now, "", id_pointage),
                        )
                        message = "Heure d’entrée enregistrée"

                conn.commit()
            return jsonify({"status": "success", "message": message})

        # ---------- CAS 2 : id_user ----------
        elif "id_user" in request.form:
            id_pointage = encryptor(
                "decrypt", request.form.get("id_pointage", "").strip()
            )
            id_user = request.form.get("id_user", "").strip()

            if not id_pointage:
                return jsonify({"status": "error", "message": "id_pointage manquant"})
            if not id_user:
                return jsonify({"status": "error", "message": "id_user manquant"})

            with get_connection() as conn:
                with conn.cursor(dictionary=True) as cursor:
                    cursor.execute(
                        "SELECT * FROM pointage WHERE date=%s AND id_contrat=%s",
                        (date_now, id_pointage),
                    )
                    result = cursor.fetchone()

                    if result:
                        cursor.execute(
                            "UPDATE pointage SET heure_fin=%s WHERE date=%s AND id_contrat=%s",
                            (time_now, date_now, id_pointage),
                        )
                        message = "Heure de sortie enregistrée"
                    else:
                        cursor.execute(
                            "INSERT INTO pointage (date, heure_debut, heure_fin, id_contrat, id_sub_users) "
                            "VALUES (%s, %s, %s, %s, %s)",
                            (date_now, time_now, "", id_pointage, id_user),
                        )
                        message = "Heure d’entrée enregistrée"

                conn.commit()
            return jsonify({"status": "success", "message": message})

        # ---------- CAS 3 : matricule ----------
        elif "matricule" in request.form:
            matricule = request.form.get("matricule", "").strip()
            if not matricule:
                return jsonify({"status": "error", "message": "Matricule manquant"})

            with get_connection() as conn:
                with conn.cursor(dictionary=True) as cursor:
                    # 1. Trouver l'employé
                    cursor.execute(
                        "SELECT id_employe FROM employe WHERE matricule=%s",
                        (matricule,),
                    )
                    employe = cursor.fetchone()
                    if not employe:
                        return jsonify(
                            {"status": "error", "message": "Matricule inconnu"}
                        )
                    id_employe = employe["id_employe"]

                    # 2. Trouver le contrat
                    cursor.execute(
                        "SELECT id_contrat FROM contrat WHERE id_employe=%s",
                        (id_employe,),
                    )
                    contrat = cursor.fetchone()
                    if not contrat:
                        return jsonify(
                            {"status": "error", "message": "Contrat introuvable"}
                        )
                    id_contrat = contrat["id_contrat"]

                    # 3. Vérifier pointage récent (<2 min)
                    cursor.execute(
                        "SELECT 1 FROM pointage WHERE id_contrat=%s AND date_heure >= NOW() - INTERVAL 2 MINUTE",
                        (id_contrat,),
                    )
                    if cursor.fetchone():
                        return jsonify(
                            {"status": "error", "message": "Déjà pointé récemment"}
                        )

                    # 4. Vérifier pointage aujourd'hui
                    cursor.execute(
                        "SELECT * FROM pointage WHERE date=%s AND id_contrat=%s",
                        (date_now, id_contrat),
                    )
                    if cursor.fetchone():
                        cursor.execute(
                            "UPDATE pointage SET heure_fin=%s, date_heure=NOW() WHERE date=%s AND id_contrat=%s",
                            (time_now, date_now, id_contrat),
                        )
                        message = "Heure de sortie enregistrée"
                    else:
                        cursor.execute(
                            "INSERT INTO pointage (date, heure_debut, heure_fin, id_contrat, date_heure) "
                            "VALUES (%s, %s, %s, %s, NOW())",
                            (date_now, time_now, "00:00:00", id_contrat),
                        )
                        message = "Heure d’entrée enregistrée"

                conn.commit()
            return jsonify({"status": "success", "message": message})

        else:
            return jsonify({"status": "error", "message": "Aucune donnée reçue"})

    except Exception as e:
        import traceback

        print(traceback.format_exc())
        return jsonify({"status": "error", "message": f"Erreur serveur : {str(e)}"})
