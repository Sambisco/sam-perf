from flask import request, jsonify
from templates.include.connect import get_connection
from templates.include.encryptor import encryptor


def save_dotation():
    response = {}

    # === INSERT ===
    if "insert_id" in request.form:
        try:
            id_contrat = encryptor("decrypt", request.form["id_contrat"]).strip()
            id_reference = encryptor("decrypt", request.form["id_reference"]).strip()
            date_dotation = request.form.get("date_dotation", "").strip()

            carburant = (
                request.form.get("carburant", "")
                .replace(" ", "")
                .replace(",", ".")
                .strip()
            )
            result_carburant = (
                request.form.get("result_carburant", "")
                .replace(" ", "")
                .replace(",", ".")
                .strip()
            )

            periode_du = request.form.get("periode_du", "").strip()
            periode_au = request.form.get("periode_au", "").strip()
            motif = request.form.get("motif", "").strip()
            lieu = request.form.get("lieu", "").strip()
            vehicule = request.form.get("vehicule", "").strip()
            immatriculation = request.form.get("immatriculation", "").strip()
            ca_dotation = request.form.get("ca_dotation", "").strip()
            numero_carte = request.form.get("numero_carte", "").strip()

            conn = get_connection()
            cursor = conn.cursor(dictionary=True)

            # Vérifier doublon
            cursor.execute(
                "SELECT * FROM dotation WHERE id_contrat=%s AND date_dotation=%s",
                (id_contrat, date_dotation),
            )
            if cursor.fetchone():
                return jsonify("true")  # Comme ton PHP

            # Récupérer prochain numéro
            cursor.execute(
                """
                SELECT MAX(numero)+1 AS numero 
                FROM dotation
                INNER JOIN contrat ON contrat.id_contrat = dotation.id_contrat
                INNER JOIN employe ON employe.id_employe = contrat.id_employe
                INNER JOIN reference ON reference.id_reference = employe.id_reference
                WHERE reference.id_reference=%s
                """,
                (id_reference,),
            )
            result = cursor.fetchone()
            numero = result["numero"] if result and result["numero"] else 1

            # Insertion
            cursor.execute(
                """
                INSERT INTO dotation(numero, date_dotation, carburant, periode_du, periode_au, motif, 
                                     lieu, vehicule, immatriculation, ca_dotation, numero_carte, id_contrat) 
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """,
                (
                    numero,
                    date_dotation,
                    carburant,
                    periode_du,
                    periode_au,
                    motif,
                    lieu,
                    vehicule,
                    immatriculation,
                    ca_dotation,
                    numero_carte,
                    id_contrat,
                ),
            )

            # Mise à jour stock
            cursor.execute(
                "UPDATE stock_carburant SET stock_carburant=%s WHERE id_reference=%s",
                (result_carburant, id_reference),
            )

            conn.commit()
            response["success"] = True

        except Exception as e:
            print(f"Erreur INSERT dotation: {e}")
            response["error"] = "Erreur lors de l'insertion"
        finally:
            cursor.close()
            conn.close()

    # === EDIT ===
    elif "edit_id" in request.form:
        try:
            id_dotation = encryptor("decrypt", request.form["edit_id"]).strip()
            id_reference = encryptor("decrypt", request.form["id_reference"]).strip()

            date_dotation = request.form.get("date_dotation", "").strip()
            carburant = (
                request.form.get("carburant", "")
                .replace(" ", "")
                .replace(",", ".")
                .strip()
            )
            result_carburant = (
                request.form.get("result_carburant", "")
                .replace(" ", "")
                .replace(",", ".")
                .strip()
            )

            periode_du = request.form.get("periode_du", "").strip()
            periode_au = request.form.get("periode_au", "").strip()
            motif = request.form.get("motif", "").strip()
            lieu = request.form.get("lieu", "").strip()
            vehicule = request.form.get("vehicule", "").strip()
            immatriculation = request.form.get("immatriculation", "").strip()
            ca_dotation = request.form.get("ca_dotation", "").strip()
            numero_carte = request.form.get("numero_carte", "").strip()

            conn = get_connection()
            cursor = conn.cursor(dictionary=True)

            cursor.execute(
                """
                UPDATE dotation 
                SET date_dotation=%s, carburant=%s, periode_du=%s, periode_au=%s, motif=%s, 
                    lieu=%s, vehicule=%s, immatriculation=%s, ca_dotation=%s, numero_carte=%s 
                WHERE id_dotation=%s
                """,
                (
                    date_dotation,
                    carburant,
                    periode_du,
                    periode_au,
                    motif,
                    lieu,
                    vehicule,
                    immatriculation,
                    ca_dotation,
                    numero_carte,
                    id_dotation,
                ),
            )

            cursor.execute(
                "UPDATE stock_carburant SET stock_carburant=%s WHERE id_reference=%s",
                (result_carburant, id_reference),
            )

            conn.commit()
            response["success"] = True

        except Exception as e:
            print(f"Erreur UPDATE dotation: {e}")
            response["error"] = "Erreur lors de la mise à jour"
        finally:
            cursor.close()
            conn.close()

    # === DELETE ===
    elif "delete_id" in request.form:
        try:
            id_dotation = encryptor("decrypt", request.form["delete_id"]).strip()
            id_reference = encryptor("decrypt", request.form["id_reference"]).strip()
            nom_del = (
                request.form.get("nom_del", "")
                .replace(" ", "")
                .replace(",", ".")
                .strip()
            )

            conn = get_connection()
            cursor = conn.cursor(dictionary=True)

            # Rendre le stock
            cursor.execute(
                "UPDATE stock_carburant SET stock_carburant = stock_carburant + %s WHERE id_reference=%s",
                (nom_del, id_reference),
            )

            # Supprimer dotation
            cursor.execute("DELETE FROM dotation WHERE id_dotation=%s", (id_dotation,))

            conn.commit()
            response["success"] = True

        except Exception as e:
            print(f"Erreur DELETE dotation: {e}")
            response["error"] = "Erreur lors de la suppression"
        finally:
            cursor.close()
            conn.close()

    return jsonify(response)
