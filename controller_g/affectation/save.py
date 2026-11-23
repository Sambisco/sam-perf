from flask import request, jsonify
from templates.include.connect import get_connection
from templates.include.encryptor import encryptor


def save_affectation_m():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # === INSERT / UPDATE ===
        if "insert_id" in request.form:
            id_reference = encryptor(
                "decrypt", request.form.get("id_reference", "").strip()
            )
            id_contrat = encryptor(
                "decrypt", request.form.get("id_contrat", "").strip()
            )

            # id_affectation_matiere facultatif
            id_affectation_matiere_update = None
            if request.form.get("id_affectation_matiere"):
                id_affectation_matiere_update = encryptor(
                    "decrypt", request.form["id_affectation_matiere"].strip()
                )

            date_affectation = request.form.get("date_affectation")
            nom_user_affectation = request.form.get("nom_user_affectation")
            sum_unite = (
                request.form.get("sum_unite", "0")
                .replace(" ", "")
                .replace(",", ".")
                .strip()
            )

            # Trouver le numéro de sortie suivant
            cursor.execute(
                """
                SELECT  MAX(numero)+1 AS numero FROM affectation_matiere
                INNER JOIN contrat ON contrat.id_contrat=affectation_matiere.id_contrat 
                INNER JOIN employe ON employe.id_employe=contrat.id_employe
                INNER JOIN reference ON reference.id_reference=employe.id_reference
                WHERE reference.id_reference=%s
            """,
                (id_reference,),
            )
            result = cursor.fetchone()
            numero = result["numero"] if result and result["numero"] is not None else 1

            # === Nouveau enregistrement ===
            if not id_affectation_matiere_update:
                cursor.execute(
                    "INSERT INTO affectation_matiere(numero,date_affectation,total,nom_user_affectation,id_contrat) VALUES (%s,%s,%s,%s,%s)",
                    (numero, date_affectation, sum_unite,nom_user_affectation, id_contrat),
                )
                conn.commit()

                # Récupérer dernier id_affectation_matiere
                cursor.execute(
                    """
                    SELECT  MAX(affectation_matiere.id_affectation_matiere) AS id_affectation_matiere FROM affectation_matiere
                    INNER JOIN contrat ON contrat.id_contrat=affectation_matiere.id_contrat 
                    INNER JOIN employe ON employe.id_employe=contrat.id_employe
                    INNER JOIN reference ON reference.id_reference=employe.id_reference
                    WHERE reference.id_reference=%s
                """,
                    (id_reference,),
                )
                result = cursor.fetchone()
                id_affectation_matiere = result["id_affectation_matiere"]

                # Détails
                for i, obs in enumerate(request.form.getlist("observation[]")):
                    id_matiere = encryptor(
                        "decrypt", request.form.getlist("id_matiere[]")[i]
                    )

                    quantite = request.form.getlist("quantite[]")[i]

                    cursor.execute(
                        "INSERT INTO detail_affectation(id_matiere,quantite,observation,id_affectation_matiere) VALUES (%s,%s,%s,%s)",
                        (id_matiere, quantite, obs, id_affectation_matiere),
                    )

                conn.commit()

            # === Mise à jour ===
            else:
                cursor.execute(
                    "UPDATE affectation_matiere SET total=%s WHERE id_affectation_matiere=%s",
                    (sum_unite, id_affectation_matiere_update),
                )
                cursor.execute(
                    "DELETE FROM detail_affectation WHERE id_affectation_matiere=%s",
                    (id_affectation_matiere_update,),
                )

                for i, obs in enumerate(request.form.getlist("observation[]")):
                    id_matiere = encryptor(
                        "decrypt", request.form.getlist("id_matiere[]")[i]
                    )

                    quantite = request.form.getlist("quantite[]")[i]

                    cursor.execute(
                        "INSERT INTO detail_affectation(id_matiere,quantite,observation,id_affectation_matiere) VALUES (%s,%s,%s,%s)",
                        (id_matiere, quantite, obs, id_affectation_matiere_update),
                    )

                conn.commit()

        # === DELETE ===
        if "delete_id" in request.form:
            id_affectation_matiere = encryptor("decrypt", request.form.get("delete_id", "").strip())

            # Récupérer tous les détails avant suppression

            # Supprimer sortie (et détails si pas ON DELETE CASCADE)
            cursor.execute(
                "DELETE FROM affectation_matiere WHERE id_affectation_matiere=%s",
                (id_affectation_matiere,),
            )
            conn.commit()

        return jsonify({"status": "success"})

    except Exception as e:
        conn.rollback()
        return jsonify({"status": "error", "message": str(e)})

    finally:
        cursor.close()
        conn.close()
