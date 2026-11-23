from flask import request, jsonify
from werkzeug.utils import secure_filename
from datetime import datetime
from templates.include.connect import get_connection
from templates.include.encryptor import encryptor


def save_absence():
    try:
        date_str = request.form.get("date", "").strip()
        if not date_str:
            return jsonify({"error": "Date manquante"}), 400

        # Convertir en objet date Python pour comparaisons
        date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()

        with get_connection() as conn:
            with conn.cursor(dictionary=True) as cursor:

                if "insert_id" in request.form:
                    # Vérifier si absences déjà générées à cette date
                    cursor.execute("SELECT 1 FROM absence WHERE date = %s", (date_str,))
                    if cursor.fetchone():
                        return jsonify({"already_inserted": True})

                    # Récupérer les contrats sans pointage à cette date
                    cursor.execute(
                        """
                        SELECT * FROM contrat 
                        INNER JOIN employe ON employe.id_employe = contrat.id_employe
                        WHERE NOT EXISTS (
                            SELECT 1 FROM pointage 
                            WHERE pointage.id_contrat = contrat.id_contrat 
                            AND pointage.date = %s
                        )
                    """,
                        (date_str,),
                    )
                    contrats = cursor.fetchall()

                    for contrat in contrats:
                        id_contrat = contrat["id_contrat"]

                        # Vérifier départ effectif
                        cursor.execute(
                            """
                            SELECT date_effet FROM depart 
                            WHERE id_contrat = %s
                            ORDER BY id_depart DESC LIMIT 1
                        """,
                            (id_contrat,),
                        )
                        depart = cursor.fetchone()
                        if depart:
                            date_effet = depart.get("date_effet")
                            if date_effet and isinstance(date_effet, datetime):
                                date_effet = date_effet.date()
                            if date_effet and date_effet < date_obj:
                                # Employé parti, ne pas enregistrer absence
                                continue

                        # Vérifier congé annuel
                        cursor.execute(
                            """
                            SELECT date_debut, date_fin FROM conge_annuel 
                            WHERE id_contrat = %s
                            ORDER BY id_conge_annuel DESC LIMIT 1
                        """,
                            (id_contrat,),
                        )
                        conge = cursor.fetchone()
                        if conge:
                            date_debut = conge.get("date_debut")
                            date_fin = conge.get("date_fin")
                            if isinstance(date_debut, datetime):
                                date_debut = date_debut.date()
                            if isinstance(date_fin, datetime):
                                date_fin = date_fin.date()
                            if (
                                date_debut
                                and date_fin
                                and date_debut <= date_obj <= date_fin
                            ):
                                # En congé annuel, ne pas enregistrer absence
                                continue

                        # Vérifier congé maternité
                        cursor.execute(
                            """
                            SELECT date_debut, date_fin FROM conge_maternite
                            WHERE id_contrat = %s
                            ORDER BY id_conge_maternite DESC LIMIT 1
                        """,
                            (id_contrat,),
                        )
                        mater = cursor.fetchone()
                        if mater:
                            date_debut = mater.get("date_debut")
                            date_fin = mater.get("date_fin")
                            if isinstance(date_debut, datetime):
                                date_debut = date_debut.date()
                            if isinstance(date_fin, datetime):
                                date_fin = date_fin.date()
                            if (
                                date_debut
                                and date_fin
                                and date_debut <= date_obj <= date_fin
                            ):
                                # En congé maternité, ne pas enregistrer absence
                                continue

                        # Insérer absence car aucune condition précédente n’a stoppé la boucle
                        cursor.execute(
                            "INSERT INTO absence (date, id_contrat) VALUES (%s, %s)",
                            (date_str, id_contrat),
                        )

                    # Mettre à jour les absences avec les motifs des demandes
                    cursor.execute(
                        """
                        SELECT demande_absence.*, demande_absence.motif AS demande_motif 
                        FROM demande_absence
                        INNER JOIN contrat ON contrat.id_contrat = demande_absence.id_contrat
                        WHERE periode_au >= %s
                    """,
                        (date_str,),
                    )
                    demandes = cursor.fetchall()

                    for demande in demandes:
                        cursor.execute(
                            """
                            UPDATE absence 
                            SET justification = %s, Imputable_sur_les_normaux = %s 
                            WHERE id_contrat = %s AND date = %s
                        """,
                            (
                                demande["demande_motif"],
                                demande["Imputable_sur_les_normaux"],
                                demande["id_contrat"],
                                date_str,
                            ),
                        )

                    conn.commit()
                    return jsonify({"success": True})

                elif "edit_id" in request.form:
                    # Décryptage de l'id
                    try:
                        edit_id = encryptor("decrypt", request.form["edit_id"].strip())
                    except Exception:
                        return jsonify({"error": "ID invalide"}), 400

                    justification = request.form.get("justification", "").strip()
                    imputable = request.form.get(
                        "Imputable_sur_les_normaux", ""
                    ).strip()

                    # Fichier fourni ?
                    if (
                        "fichier" in request.files
                        and request.files["fichier"].filename != ""
                    ):
                        fichier = request.files["fichier"]
                        filename = secure_filename(fichier.filename)
                        fichier_data = fichier.read()
                        mimetype = fichier.mimetype

                        cursor.execute(
                            """
                            UPDATE absence
                            SET justification = %s, name = %s, type = %s, fichier = %s, Imputable_sur_les_normaux = %s
                            WHERE id_absence = %s
                        """,
                            (
                                justification,
                                filename,
                                mimetype,
                                fichier_data,
                                imputable,
                                edit_id,
                            ),
                        )
                    else:
                        cursor.execute(
                            """
                            UPDATE absence
                            SET justification = %s, Imputable_sur_les_normaux = %s
                            WHERE id_absence = %s
                        """,
                            (justification, imputable, edit_id),
                        )

                    conn.commit()
                    return jsonify({"success": True})

                else:
                    return jsonify({"error": "Requête invalide"}), 400

    except Exception as e:
        print("Erreur dans save_absence:", e)
        return jsonify({"error": str(e)}), 500
