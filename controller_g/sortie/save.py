from flask import request, jsonify
from templates.include.connect import get_connection
from templates.include.encryptor import encryptor


def save_sortie():
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

            # id_sortie facultatif
            id_sortie_update = None
            if request.form.get("id_sortie"):
                id_sortie_update = encryptor(
                    "decrypt", request.form["id_sortie"].strip()
                )

            date_sortie = request.form.get("date_sortie")
            sum_unite = (
                request.form.get("sum_unite", "0")
                .replace(" ", "")
                .replace(",", ".")
                .strip()
            )

            # Trouver le numéro de sortie suivant
            cursor.execute(
                """
                SELECT MAX(numero)+1 AS numero FROM sortie
                INNER JOIN contrat ON contrat.id_contrat=sortie.id_contrat
                INNER JOIN employe ON employe.id_employe=contrat.id_employe
                INNER JOIN reference ON reference.id_reference=employe.id_reference
                WHERE reference.id_reference=%s
            """,
                (id_reference,),
            )
            result = cursor.fetchone()
            numero = result["numero"] if result and result["numero"] is not None else 1

            # === Nouveau enregistrement ===
            if not id_sortie_update:
                cursor.execute(
                    "INSERT INTO sortie(numero,date_sortie,total,id_contrat) VALUES (%s,%s,%s,%s)",
                    (numero, date_sortie, sum_unite, id_contrat),
                )
                conn.commit()

                # Récupérer dernier id_sortie
                cursor.execute(
                    """
                    SELECT MAX(sortie.id_sortie) AS id_sortie FROM sortie
                    INNER JOIN contrat ON contrat.id_contrat=sortie.id_contrat
                    INNER JOIN employe ON employe.id_employe=contrat.id_employe
                    INNER JOIN reference ON reference.id_reference=employe.id_reference
                    WHERE reference.id_reference=%s
                """,
                    (id_reference,),
                )
                result = cursor.fetchone()
                id_sortie = result["id_sortie"]

                # Détails
                for i, obs in enumerate(request.form.getlist("observation[]")):
                    id_matiere = encryptor(
                        "decrypt", request.form.getlist("id_matiere[]")[i]
                    )
                    nb_unite = (
                        (request.form.getlist("nb_unite[]")[i] or "0")
                        .replace(" ", "")
                        .replace(",", ".")
                    )
                    quantite = request.form.getlist("quantite[]")[i]

                    cursor.execute(
                        "INSERT INTO detail_sortie(id_matiere,quantite,observation,id_sortie) VALUES (%s,%s,%s,%s)",
                        (id_matiere, quantite, obs, id_sortie),
                    )
                    cursor.execute(
                        "UPDATE matiere SET nbre_unite=%s WHERE id_matiere=%s",
                        (nb_unite, id_matiere),
                    )
                conn.commit()

            # === Mise à jour ===
            else:
                cursor.execute(
                    "UPDATE sortie SET date_sortie=%s, total=%s WHERE id_sortie=%s",
                    (date_sortie,sum_unite, id_sortie_update),
                )
                cursor.execute(
                    "DELETE FROM detail_sortie WHERE id_sortie=%s", (id_sortie_update,)
                )

                for i, obs in enumerate(request.form.getlist("observation[]")):
                    id_matiere = encryptor(
                        "decrypt", request.form.getlist("id_matiere[]")[i]
                    )
                    nb_unite = (
                        (request.form.getlist("nb_unite[]")[i] or "0")
                        .replace(" ", "")
                        .replace(",", ".")
                    )
                    quantite = request.form.getlist("quantite[]")[i]

                    cursor.execute(
                        "INSERT INTO detail_sortie(id_matiere,quantite,observation,id_sortie) VALUES (%s,%s,%s,%s)",
                        (id_matiere, quantite, obs, id_sortie_update),
                    )
                    cursor.execute(
                        "UPDATE matiere SET nbre_unite=%s WHERE id_matiere=%s",
                        (nb_unite, id_matiere),
                    )
                conn.commit()

        # insert sortie externe

        if "insert_id_externe" in request.form:
            id_reference = encryptor(
                "decrypt", request.form.get("id_reference", "").strip()
            )

            # id_sortie facultatif
            id_sortie_update = None
            if request.form.get("id_sortie_externe"):
                id_sortie_update = encryptor(
                    "decrypt", request.form["id_sortie_externe"].strip()
                )

            date_sortie = request.form.get("date_sortie")
            nom_complet_externe = request.form.get("nom_complet_externe")
            telephone_externe = request.form.get("telephone_externe")
            sum_unite = (
                request.form.get("sum_unite", "0")
                .replace(" ", "")
                .replace(",", ".")
                .strip()
            )

            # Trouver le numéro de sortie suivant
            cursor.execute(
                """
                SELECT MAX(numero)+1 AS numero FROM sortie_externe
                INNER JOIN reference ON reference.id_reference=sortie_externe.id_reference
                WHERE reference.id_reference=%s
            """,
                (id_reference,),
            )
            result = cursor.fetchone()
            numero = result["numero"] if result and result["numero"] is not None else 1

            # === Nouveau enregistrement ===
            if not id_sortie_update:
                cursor.execute(
                    "INSERT INTO sortie_externe(numero,date_sortie,total,nom_complet_externe,telephone_externe,id_reference) VALUES (%s,%s,%s,%s,%s,%s)",
                    (
                        numero,
                        date_sortie,
                        sum_unite,
                        nom_complet_externe,
                        telephone_externe,
                        id_reference,
                    ),
                )
                conn.commit()

                # Récupérer dernier id_sortie
                cursor.execute(
                    """
                    SELECT MAX(sortie_externe.id_sortie_externe) AS id_sortie FROM sortie_externe
                    INNER JOIN reference ON reference.id_reference=sortie_externe.id_reference
                    WHERE reference.id_reference=%s
                """,
                    (id_reference,),
                )
                result = cursor.fetchone()
                id_sortie = result["id_sortie"]

                # Détails
                for i, obs in enumerate(request.form.getlist("observation[]")):
                    id_matiere = encryptor(
                        "decrypt", request.form.getlist("id_matiere[]")[i]
                    )
                    nb_unite = (
                        (request.form.getlist("nb_unite[]")[i] or "0")
                        .replace(" ", "")
                        .replace(",", ".")
                    )
                    quantite = request.form.getlist("quantite[]")[i]

                    cursor.execute(
                        "INSERT INTO detail_sortie_externe(id_matiere,quantite,observation,id_sortie_externe) VALUES (%s,%s,%s,%s)",
                        (id_matiere, quantite, obs, id_sortie),
                    )
                    cursor.execute(
                        "UPDATE matiere SET nbre_unite=%s WHERE id_matiere=%s",
                        (nb_unite, id_matiere),
                    )
                conn.commit()

            # === Mise à jour ===
            else:
                cursor.execute(
                    "UPDATE sortie_externe SET date_sortie=%s, total=%s,nom_complet_externe=%s,telephone_externe=%s WHERE id_sortie_externe=%s",
                    (
                        date_sortie,
                        sum_unite,
                        nom_complet_externe,
                        telephone_externe,
                        id_sortie_update,
                    ),
                )
                cursor.execute(
                    "DELETE FROM detail_sortie_externe WHERE id_sortie_externe=%s",
                    (id_sortie_update,),
                )

                for i, obs in enumerate(request.form.getlist("observation[]")):
                    id_matiere = encryptor(
                        "decrypt", request.form.getlist("id_matiere[]")[i]
                    )
                    nb_unite = (
                        (request.form.getlist("nb_unite[]")[i] or "0")
                        .replace(" ", "")
                        .replace(",", ".")
                    )
                    quantite = request.form.getlist("quantite[]")[i]

                    cursor.execute(
                        "INSERT INTO detail_sortie_externe(id_matiere,quantite,observation,id_sortie_externe) VALUES (%s,%s,%s,%s)",
                        (id_matiere, quantite, obs, id_sortie_update),
                    )
                    cursor.execute(
                        "UPDATE matiere SET nbre_unite=%s WHERE id_matiere=%s",
                        (nb_unite, id_matiere),
                    )
                conn.commit()

        # === DELETE ===
        if "delete_id" in request.form:
            id_sortie = encryptor("decrypt", request.form.get("delete_id", "").strip())

            # Récupérer tous les détails avant suppression
            cursor.execute(
                """
                SELECT * FROM detail_sortie
                INNER JOIN sortie ON sortie.id_sortie=detail_sortie.id_sortie
                INNER JOIN matiere ON matiere.id_matiere=detail_sortie.id_matiere
                WHERE sortie.id_sortie=%s
            """,
                (id_sortie,),
            )
            details = cursor.fetchall()

            for row in details:
                cursor.execute(
                    "UPDATE matiere SET nbre_unite=nbre_unite+%s WHERE id_matiere=%s",
                    (row["quantite"], row["id_matiere"]),
                )

            # Supprimer sortie (et détails si pas ON DELETE CASCADE)
            cursor.execute("DELETE FROM sortie WHERE id_sortie=%s", (id_sortie,))
            conn.commit()

        if "delete_id_externe" in request.form:
            id_sortie = encryptor(
                "decrypt", request.form.get("delete_id_externe", "").strip()
            )

            # Récupérer tous les détails avant suppression
            cursor.execute(
                """
                SELECT * FROM detail_sortie_externe
                INNER JOIN sortie_externe ON sortie_externe.id_sortie_externe=detail_sortie_externe.id_sortie_externe
                INNER JOIN matiere ON matiere.id_matiere=detail_sortie_externe.id_matiere
                WHERE sortie_externe.id_sortie_externe=%s
            """,
                (id_sortie,),
            )
            details = cursor.fetchall()

            for row in details:
                cursor.execute(
                    "UPDATE matiere SET nbre_unite=nbre_unite+%s WHERE id_matiere=%s",
                    (row["quantite"], row["id_matiere"]),
                )

            # Supprimer sortie (et détails si pas ON DELETE CASCADE)
            cursor.execute(
                "DELETE FROM sortie_externe WHERE id_sortie_externe=%s", (id_sortie,)
            )
            conn.commit()

        return jsonify({"status": "success"})

    except Exception as e:
        conn.rollback()
        return jsonify({"status": "error", "message": str(e)})

    finally:
        cursor.close()
        conn.close()
