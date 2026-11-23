from flask import request, jsonify
from templates.include.connect import get_connection
from templates.include.encryptor import encryptor


def save_mutation():
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

            id_affectation_matiere = encryptor(
                "decrypt", request.form["id_affectation_matiere"].strip()
            )

            date_mutation = request.form.get("date_mutation")
            nom_user_mutation = request.form.get("nom_user_mutation")

            id_mutation_update = None
            if request.form.get("id_mutation"):
                id_mutation_update = encryptor(
                    "decrypt", request.form["id_mutation"].strip()
                )

            # Trouver le numéro de sortie suivant
            cursor.execute(
                """
                SELECT MAX(numero_mutation)+1 AS numero FROM mutation 
                INNER JOIN affectation_matiere ON affectation_matiere.id_affectation_matiere=mutation.id_affectation_matiere
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
            if not id_mutation_update:
                cursor.execute(
                    "INSERT INTO mutation(numero_mutation,date_mutation,id_affectation_matiere,id_contrat,nom_user_mutation) VALUES (%s,%s,%s,%s,%s)",
                    (
                        numero,
                        date_mutation,
                        id_affectation_matiere,
                        id_contrat,
                        nom_user_mutation,
                    ),
                )
                conn.commit()
            else:
                cursor.execute(
                    "UPDATE mutation SET date_mutation=%s, id_contrat=%s, nom_user_mutation=%s WHERE id_mutation=%s",
                    (date_mutation, id_contrat, nom_user_mutation, id_mutation_update),
                )
                conn.commit()
            # Récupérer dernier id_affectation_matiere

        # === DELETE ===
        if "delete_id" in request.form:
            id_mutation = encryptor(
                "decrypt", request.form.get("delete_id", "").strip()
            )

            # Récupérer tous les détails avant suppression

            # Supprimer sortie (et détails si pas ON DELETE CASCADE)
            cursor.execute(
                "DELETE FROM mutation WHERE id_mutation=%s",
                (id_mutation,),
            )
            conn.commit()

        return jsonify({"status": "success"})

    except Exception as e:
        conn.rollback()
        return jsonify({"status": "error", "message": str(e)})

    finally:
        cursor.close()
        conn.close()
