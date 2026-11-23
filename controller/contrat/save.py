from flask import request, jsonify
from templates.include.connect import get_connection
from templates.include.encryptor import encryptor


def decrypt(value):
    # wrapper pour ton encryptor décryptage
    return encryptor("decrypt", value)


def save_contrat():
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)  # dictionary=True pour fetchone() en dict

        # INSERT
        if "insert_id" in request.form:
            id_employe = decrypt(request.form.get("id_employe", "")).strip()
            categorie = request.form.get("categorie", "").strip()
            id_departement = request.form.get("id_departement", "").strip()
            id_region = request.form.get("id_region", "").strip()
            nature = request.form.get("nature", "").strip()
            poste_occupe = request.form.get("poste_occupe", "").strip()
            date_embauche = request.form.get("date_embauche", "").strip()
            date_sorti = request.form.get("date_sorti", "").strip()
            situation_matr = request.form.get("situation_matr", "").strip()
            conjoint = request.form.get("conjoint", "").strip()
            enfant = request.form.get("enfant", "").strip()
            heure = request.form.get("heure", "").strip()
            nb_trimf = request.form.get("nb_trimf", "").strip()
            nb_irpp = request.form.get("nb_irpp", "").strip()
            heure_debut = request.form.get("heure_debut", "").strip()
            heure_decente = request.form.get("heure_decente", "").strip()
            salaire = (
                request.form.get("salaire", "")
                .replace(" ", "")
                .replace(",", ".")
                .strip()
            )
            salaire_lettre = request.form.get("salaire_en_lettre", "").strip()
            document_lettre = request.form.get("document_lettre", "").strip()
            adresse_e = request.form.get("adresse_e", "").strip()
            cin_e = request.form.get("cin_e", "").strip()
            nationalite = request.form.get("nationalite", "").strip()
            nom_pere = request.form.get("nom_pere", "").strip()
            nom_mere = request.form.get("nom_mere", "").strip()
            email_e = request.form.get("email_e", "").strip()
            fonction = (
                request.form.get("fonction", "")
                .replace(" ", "")
                .replace(",", ".")
                .strip()
            )
            sujetion = (
                request.form.get("sujetion", "")
                .replace(" ", "")
                .replace(",", ".")
                .strip()
            )
            responsabilite = (
                request.form.get("responsabilite", "")
                .replace(" ", "")
                .replace(",", ".")
                .strip()
            )
            sursalaire = (
                request.form.get("sursalaire", "")
                .replace(" ", "")
                .replace(",", ".")
                .strip()
            )
            logement = (
                request.form.get("logement", "")
                .replace(" ", "")
                .replace(",", ".")
                .strip()
            )
            autre_indemnite = (
                request.form.get("autre_indemnite", "")
                .replace(" ", "")
                .replace(",", ".")
                .strip()
            )
            transport = (
                request.form.get("transport", "")
                .replace(" ", "")
                .replace(",", ".")
                .strip()
            )
            telephone_in = (
                request.form.get("telephone_in", "")
                .replace(" ", "")
                .replace(",", ".")
                .strip()
            )

            # Vérifier si contrat existe déjà
            cursor.execute("SELECT * FROM contrat WHERE id_employe = %s", (id_employe,))
            if cursor.fetchone():
                return jsonify({"exists": True})

            # Insert contrat
            cursor.execute(
                """
                INSERT INTO contrat (nature, poste_occupe, date_embauche, date_sorti, situation_matr, conjoint,
                    nb_trimf, nb_irpp, enfant, heure, salaire, salaire_lettre, fonction, sujetion,
                    responsabilite, sursalaire, logement, autre_indemnite, transport, telephone_in,
                    document_lettre, categorie, id_employe)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    nature,
                    poste_occupe,
                    date_embauche,
                    date_sorti,
                    situation_matr,
                    conjoint,
                    nb_trimf,
                    nb_irpp,
                    enfant,
                    heure,
                    salaire,
                    salaire_lettre,
                    fonction,
                    sujetion,
                    responsabilite,
                    sursalaire,
                    logement,
                    autre_indemnite,
                    transport,
                    telephone_in,
                    document_lettre,
                    categorie,
                    id_employe,
                ),
            )
            conn.commit()

            # Récupérer id contrat inséré via lastrowid
            id_contrat = cursor.lastrowid

            # Insert personnel
            cursor.execute(
                """
                INSERT INTO personnel (id_contrat, id_departement, id_region, heure_debut, heure_decente)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (id_contrat, id_departement, id_region, heure_debut, heure_decente),
            )

            # Update employe
            cursor.execute(
                """
                UPDATE employe SET adresse_e=%s, email_e=%s, cin_e=%s, nationalite=%s, nom_pere=%s, nom_mere=%s
                WHERE id_employe=%s
                """,
                (
                    adresse_e,
                    email_e,
                    cin_e,
                    nationalite,
                    nom_pere,
                    nom_mere,
                    id_employe,
                ),
            )
            conn.commit()

            return jsonify({"inserted": True})

        # UPDATE
        elif "edit_id" in request.form:
            id_contrat = decrypt(request.form.get("edit_id", "")).strip()
            id_employe = decrypt(request.form.get("id_employe", "")).strip()
            categorie = request.form.get("categorie", "").strip()
            id_departement = request.form.get("id_departement", "").strip()
            id_region = request.form.get("id_region", "").strip()
            nature = request.form.get("nature", "").strip()
            poste_occupe = request.form.get("poste_occupe", "").strip()
            date_embauche = request.form.get("date_embauche", "").strip()
            date_sorti = request.form.get("date_sorti", "").strip()
            situation_matr = request.form.get("situation_matr", "").strip()
            conjoint = request.form.get("conjoint", "").strip()
            enfant = request.form.get("enfant", "").strip()
            heure = request.form.get("heure", "").strip()
            nb_trimf = request.form.get("nb_trimf", "").strip()
            nb_irpp = request.form.get("nb_irpp", "").strip()
            heure_debut = request.form.get("heure_debut", "").strip()
            heure_decente = request.form.get("heure_decente", "").strip()
            salaire = (
                request.form.get("salaire", "")
                .replace(" ", "")
                .replace(",", ".")
                .strip()
            )
            salaire_lettre = request.form.get("salaire_en_lettre", "").strip()
            document_lettre = request.form.get("document_lettre", "").strip()
            adresse_e = request.form.get("adresse_e", "").strip()
            cin_e = request.form.get("cin_e", "").strip()
            nationalite = request.form.get("nationalite", "").strip()
            nom_pere = request.form.get("nom_pere", "").strip()
            nom_mere = request.form.get("nom_mere", "").strip()
            email_e = request.form.get("email_e", "").strip()
            fonction = (
                request.form.get("fonction", "")
                .replace(" ", "")
                .replace(",", ".")
                .strip()
            )
            sujetion = (
                request.form.get("sujetion", "")
                .replace(" ", "")
                .replace(",", ".")
                .strip()
            )
            responsabilite = (
                request.form.get("responsabilite", "")
                .replace(" ", "")
                .replace(",", ".")
                .strip()
            )
            sursalaire = (
                request.form.get("sursalaire", "")
                .replace(" ", "")
                .replace(",", ".")
                .strip()
            )
            logement = (
                request.form.get("logement", "")
                .replace(" ", "")
                .replace(",", ".")
                .strip()
            )
            autre_indemnite = (
                request.form.get("autre_indemnite", "")
                .replace(" ", "")
                .replace(",", ".")
                .strip()
            )
            transport = (
                request.form.get("transport", "")
                .replace(" ", "")
                .replace(",", ".")
                .strip()
            )
            telephone_in = (
                request.form.get("telephone_in", "")
                .replace(" ", "")
                .replace(",", ".")
                .strip()
            )

            cursor.execute(
                """
                UPDATE contrat SET
                    nature=%s, poste_occupe=%s, date_embauche=%s, date_sorti=%s, situation_matr=%s, conjoint=%s,
                    nb_trimf=%s, nb_irpp=%s, enfant=%s, heure=%s, salaire=%s, salaire_lettre=%s, fonction=%s, sujetion=%s,
                    responsabilite=%s, sursalaire=%s, logement=%s, autre_indemnite=%s, transport=%s, telephone_in=%s,
                    document_lettre=%s, categorie=%s
                WHERE id_contrat=%s
                """,
                (
                    nature,
                    poste_occupe,
                    date_embauche,
                    date_sorti,
                    situation_matr,
                    conjoint,
                    nb_trimf,
                    nb_irpp,
                    enfant,
                    heure,
                    salaire,
                    salaire_lettre,
                    fonction,
                    sujetion,
                    responsabilite,
                    sursalaire,
                    logement,
                    autre_indemnite,
                    transport,
                    telephone_in,
                    document_lettre,
                    categorie,
                    id_contrat,
                ),
            )

            cursor.execute(
                """
                UPDATE personnel SET id_departement=%s, id_region=%s, heure_debut=%s, heure_decente=%s
                WHERE id_contrat=%s
                """,
                (id_departement, id_region, heure_debut, heure_decente, id_contrat),
            )

            cursor.execute(
                """
                UPDATE employe SET adresse_e=%s, email_e=%s, cin_e=%s, nationalite=%s, nom_pere=%s, nom_mere=%s
                WHERE id_employe=%s
                """,
                (
                    adresse_e,
                    email_e,
                    cin_e,
                    nationalite,
                    nom_pere,
                    nom_mere,
                    id_employe,
                ),
            )
            conn.commit()
            return jsonify({"updated": True})

        elif "edit_updapte_part" in request.form:
            id_contrat = decrypt(request.form.get("edit_updapte_part", "")).strip()
            categorie = request.form.get("categorie", "").strip()
            situation_matr = request.form.get("situation_matr", "").strip()
            conjoint = request.form.get("conjoint", "").strip()
            enfant = request.form.get("enfant", "").strip()
            heure = request.form.get("heure", "").strip()
            salaire = (
                request.form.get("salaire", "")
                .replace(" ", "")
                .replace(",", ".")
                .strip()
            )
            salaire_lettre = request.form.get("salaire_en_lettre", "").strip()
            fonction = (
                request.form.get("fonction", "")
                .replace(" ", "")
                .replace(",", ".")
                .strip()
            )
            sujetion = (
                request.form.get("sujetion", "")
                .replace(" ", "")
                .replace(",", ".")
                .strip()
            )
            responsabilite = (
                request.form.get("responsabilite", "")
                .replace(" ", "")
                .replace(",", ".")
                .strip()
            )
            sursalaire = (
                request.form.get("sursalaire", "")
                .replace(" ", "")
                .replace(",", ".")
                .strip()
            )
            logement = (
                request.form.get("logement", "")
                .replace(" ", "")
                .replace(",", ".")
                .strip()
            )
            autre_indemnite = (
                request.form.get("autre_indemnite", "")
                .replace(" ", "")
                .replace(",", ".")
                .strip()
            )
            transport = (
                request.form.get("transport", "")
                .replace(" ", "")
                .replace(",", ".")
                .strip()
            )
            telephone_in = (
                request.form.get("telephone_in", "")
                .replace(" ", "")
                .replace(",", ".")
                .strip()
            )
            nb_trimf = request.form.get("nb_trimf", "").strip()
            nb_irpp = request.form.get("nb_irpp", "").strip()

            cursor.execute(
                """
               UPDATE contrat SET situation_matr=%s,conjoint=%s,nb_trimf=%s,nb_irpp=%s,enfant=%s,heure=%s,salaire=%s,salaire_lettre=%s,fonction=%s,sujetion=%s,responsabilite=%s,sursalaire=%s,logement=%s,autre_indemnite=%s,transport=%s,telephone_in=%s,categorie=%s
                WHERE id_contrat=%s
                """,
                (
                    situation_matr,conjoint,nb_trimf,nb_irpp,enfant,heure,salaire,salaire_lettre,fonction,sujetion,responsabilite,sursalaire,logement, autre_indemnite,transport,telephone_in,categorie,id_contrat
                ),
            )

            conn.commit()
            return jsonify({"updated": True})

        else:
            return jsonify({"error": "No valid action found"})

    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({"error": str(e)})

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
