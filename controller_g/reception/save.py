from flask import request, jsonify
from templates.include.connect import get_connection
from templates.include.encryptor import encryptor


def save_reception_carburant():
    if request.method == "POST" and "insert_id" in request.form:
        try:
            id_fournisseur = encryptor("decrypt", request.form["id_fournisseur"])
            id_reference = encryptor("decrypt", request.form["id_reference"])
            date_reception = request.form["date_reception"].strip()
            carburant_gasoil = float(
                request.form["carburant_gasoil"].replace(" ", "").replace(",", ".")
            )
            carburant_super = float(
                request.form["carburant_super"].replace(" ", "").replace(",", ".")
            )
            result_carburant = float(
                request.form["result_carburant"].replace(" ", "").replace(",", ".")
            )
            numero_facture = request.form["numero_facture"].strip()
            numero_bon = request.form["numero_bon"].strip()

            with get_connection() as conn:
                with conn.cursor(dictionary=True) as cursor:
                    # Vérifier doublon
                    cursor.execute(
                        """
                        SELECT * FROM reception_carburant 
                        WHERE id_fournisseur = %s AND date_reception = %s
                        """,
                        (id_fournisseur, date_reception),
                    )
                    if cursor.fetchone():
                        return jsonify("true")

                    # Récupérer numéro
                    cursor.execute(
                        """
                        SELECT MAX(numero)+1 AS numero 
                        FROM reception_carburant
                        INNER JOIN fournisseur ON fournisseur.id_fournisseur = reception_carburant.id_fournisseur
                        INNER JOIN reference ON reference.id_reference = fournisseur.id_reference
                        WHERE reference.id_reference = %s
                        """,
                        (id_reference,),
                    )
                    result = cursor.fetchone()
                    numero = result["numero"] if result and result["numero"] else 1

                    # Insertion réception
                    cursor.execute(
                        """
                        INSERT INTO reception_carburant(
                            numero, date_reception, carburant_gasoil, carburant_super,
                            numero_facture, numero_bon, id_fournisseur
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """,
                        (
                            numero,
                            date_reception,
                            carburant_gasoil,
                            carburant_super,
                            numero_facture,
                            numero_bon,
                            id_fournisseur,
                        ),
                    )

                    # Vérifier stock existant
                    cursor.execute(
                        "SELECT * FROM stock_carburant WHERE id_reference = %s",
                        (id_reference,),
                    )
                    stock = cursor.fetchone()
                    if not stock:
                        cursor.execute(
                            "INSERT INTO stock_carburant(stock_carburant, id_reference) VALUES (%s, %s)",
                            (result_carburant, id_reference),
                        )
                    else:
                        cursor.execute(
                            "UPDATE stock_carburant SET stock_carburant = %s WHERE id_reference = %s",
                            (result_carburant, id_reference),
                        )
                conn.commit()
        except Exception as e:
            print(f"Erreur INSERT reception_carburant: {e}")
            return jsonify({"error": "Erreur serveur"}), 500

    elif request.method == "POST" and "edit_id" in request.form:
        try:
            id_reception = encryptor("decrypt", request.form["edit_id"])
            id_reference = encryptor("decrypt", request.form["id_reference"])
            date_reception = request.form["date_reception"].strip()
            carburant_gasoil = float(
                request.form["carburant_gasoil"].replace(" ", "").replace(",", ".")
            )
            carburant_super = float(
                request.form["carburant_super"].replace(" ", "").replace(",", ".")
            )
            result_carburant = float(
                request.form["result_carburant"].replace(" ", "").replace(",", ".")
            )
            numero_facture = request.form["numero_facture"].strip()
            numero_bon = request.form["numero_bon"].strip()

            with get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        """
                        UPDATE reception_carburant
                        SET date_reception=%s, carburant_gasoil=%s, carburant_super=%s,
                            numero_facture=%s, numero_bon=%s
                        WHERE id_reception_carburant = %s
                        """,
                        (
                            date_reception,
                            carburant_gasoil,
                            carburant_super,
                            numero_facture,
                            numero_bon,
                            id_reception,
                        ),
                    )

                    cursor.execute(
                        "UPDATE stock_carburant SET stock_carburant=%s WHERE id_reference=%s",
                        (result_carburant, id_reference),
                    )
                conn.commit()
        except Exception as e:
            print(f"Erreur UPDATE reception_carburant: {e}")
            return jsonify({"error": "Erreur serveur"}), 500

    elif request.method == "POST" and "delete_id" in request.form:
        try:
            id_reception = encryptor("decrypt", request.form["delete_id"]).strip()
            id_reference = encryptor("decrypt", request.form["id_reference"])
            nom_del = float(request.form["nom_del"].replace(" ", "").replace(",", "."))

            with get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        """
                        UPDATE stock_carburant 
                        SET stock_carburant = stock_carburant - %s
                        WHERE id_reference = %s
                        """,
                        (nom_del, id_reference),
                    )

                    cursor.execute(
                        "DELETE FROM reception_carburant WHERE id_reception_carburant = %s",
                        (id_reception,),
                    )
                conn.commit()
        except Exception as e:
            print(f"Erreur DELETE reception_carburant: {e}")
            return jsonify({"error": "Erreur serveur"}), 500

    return jsonify({"success": True})
