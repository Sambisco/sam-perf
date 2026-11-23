from flask import request, jsonify
from templates.include.encryptor import encryptor
from templates.include.connect import get_connection


def save_entree():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    response = {}

    # === INSERT / UPDATE ===
    if "insert_id" in request.form:
        id_reference = encryptor("decrypt", request.form.get("id_reference").strip())

        # id_entree optionnel
        id_entree_raw = request.form.get("id_entree")
        id_entree_update = None
        if id_entree_raw and id_entree_raw.strip() != "":
            id_entree_update = encryptor("decrypt", id_entree_raw.strip())

        date_entree = request.form.get("date_entree")
        pverbal = request.form.get("pverbal", "")
        id_fournisseur_raw = request.form.get("id_fournisseur")
        id_fournisseur = (
            encryptor("decrypt", id_fournisseur_raw.strip())
            if id_fournisseur_raw
            else None
        )
        numero_bon = (
            request.form.get("numero_bon", "").replace(" ", "").replace(",", ".")
        )
        sum_unite = request.form.get("sum_unite", "").replace(" ", "").replace(",", ".")

        # Récupérer prochain numero
        cursor.execute(
            """
            SELECT MAX(numero)+1 AS numero
            FROM entree
            INNER JOIN reference ON reference.id_reference=entree.id_reference
            WHERE reference.id_reference=%s
        """,
            (id_reference,),
        )
        result = cursor.fetchone()
        numero = result["numero"] if result["numero"] else "1"

        # === Nouvelle entrée ===
        if id_entree_update is None:
            cursor.execute(
                """
                INSERT INTO entree(numero,date_entree,numero_bon,total,pverbal,id_reference)
                VALUES (%s,%s,%s,%s,%s,%s)
            """,
                (numero, date_entree, numero_bon, sum_unite, pverbal, id_reference),
            )
            conn.commit()

            # Récupérer id_entree créé
            cursor.execute(
                """
                SELECT MAX(id_entree) AS id_entree
                FROM entree
                WHERE id_reference=%s
            """,
                (id_reference,),
            )
            result = cursor.fetchone()
            id_entree = result["id_entree"]

            # pv_entree optionnel
            if pverbal != "" and id_fournisseur:
                cursor.execute(
                    """
                    INSERT INTO pv_entree(id_entree, id_fournisseur)
                    VALUES (%s,%s)
                """,
                    (id_entree, id_fournisseur),
                )
                conn.commit()

            # Détails
            for key, obs in enumerate(request.form.getlist("observation[]")):
                id_matiere = encryptor(
                    "decrypt", request.form.getlist("id_matiere[]")[key]
                )
                prix_unitaire = request.form.getlist("prix_unitaire[]")[key].replace(
                    " ", ""
                )
                total_entree = request.form.getlist("total_entree[]")[key].replace(
                    " ", ""
                )
                nb_unite = request.form.getlist("nb_unite[]")[key].replace(" ", "")
                quantite = request.form.getlist("quantite[]")[key]
                observation = request.form.getlist("observation[]")[key]

                cursor.execute(
                    """
                    INSERT INTO detail_entree(id_matiere,prix_unitaire,quantite,total_entree,observation,id_entree)
                    VALUES (%s,%s,%s,%s,%s,%s)
                """,
                    (
                        id_matiere,
                        prix_unitaire,
                        quantite,
                        total_entree,
                        observation,
                        id_entree,
                    ),
                )
                cursor.execute(
                    "UPDATE matiere SET nbre_unite=%s WHERE id_matiere=%s",
                    (nb_unite, id_matiere),
                )
            conn.commit()

        # === Mise à jour ===
        else:
            cursor.execute(
                """
                UPDATE entree
                SET date_entree=%s, numero_bon=%s, total=%s, pverbal=%s
                WHERE id_entree=%s
            """,
                (date_entree, numero_bon, sum_unite, pverbal, id_entree_update),
            )
            conn.commit()

            # pv_entree optionnel
            if pverbal != "" and id_fournisseur:
                cursor.execute(
                    "SELECT * FROM pv_entree WHERE id_entree=%s", (id_entree_update,)
                )
                result = cursor.fetchone()
                if result is None:
                    cursor.execute(
                        "INSERT INTO pv_entree(id_entree, id_fournisseur) VALUES (%s,%s)",
                        (id_entree_update, id_fournisseur),
                    )
                else:
                    cursor.execute(
                        "UPDATE pv_entree SET id_fournisseur=%s WHERE id_entree=%s",
                        (id_fournisseur, id_entree_update),
                    )
                conn.commit()
            else:
                cursor.execute(
                    "DELETE FROM pv_entree WHERE id_entree=%s",
                    (id_entree_update,),
                )
                conn.commit()

            # Supprimer et réinsérer détails
            cursor.execute(
                "DELETE FROM detail_entree WHERE id_entree=%s", (id_entree_update,)
            )
            for key, obs in enumerate(request.form.getlist("observation[]")):
                id_matiere = encryptor(
                    "decrypt", request.form.getlist("id_matiere[]")[key]
                )
                prix_unitaire = request.form.getlist("prix_unitaire[]")[key].replace(
                    " ", ""
                )
                total_entree = request.form.getlist("total_entree[]")[key].replace(
                    " ", ""
                )
                nb_unite = request.form.getlist("nb_unite[]")[key].replace(" ", "")
                quantite = request.form.getlist("quantite[]")[key]
                observation = request.form.getlist("observation[]")[key]

                cursor.execute(
                    """
                    INSERT INTO detail_entree(id_matiere,prix_unitaire,quantite,total_entree,observation,id_entree)
                    VALUES (%s,%s,%s,%s,%s,%s)
                """,
                    (
                        id_matiere,
                        prix_unitaire,
                        quantite,
                        total_entree,
                        observation,
                        id_entree_update,
                    ),
                )
                cursor.execute(
                    "UPDATE matiere SET nbre_unite=%s WHERE id_matiere=%s",
                    (nb_unite, id_matiere),
                )
            conn.commit()

    # === DELETE ===
    if "delete_id" in request.form:
        id_val_raw = request.form.get("delete_id")
        if id_val_raw and id_val_raw.strip() != "":
            id_val = encryptor("decrypt", id_val_raw.strip())

            cursor.execute(
                """
                SELECT * FROM detail_entree
                INNER JOIN entree ON entree.id_entree=detail_entree.id_entree
                INNER JOIN matiere ON matiere.id_matiere=detail_entree.id_matiere
                WHERE entree.id_entree=%s
            """,
                (id_val,),
            )
            rows = cursor.fetchall()
            for row in rows:
                cursor.execute(
                    "UPDATE matiere SET nbre_unite=nbre_unite-%s WHERE id_matiere=%s",
                    (row["quantite"], row["id_matiere"]),
                )
            cursor.execute("DELETE FROM entree WHERE id_entree=%s", (id_val,))
            conn.commit()

    cursor.close()
    conn.close()
    response["status"] = "success"
    return jsonify(response)
