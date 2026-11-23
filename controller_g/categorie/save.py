from flask import request, jsonify
from templates.include.connect import (
    get_connection,
)  # On utilise get_connection ici pour la connexion à la DB
from templates.include.encryptor import encryptor


def save_categorie():
    try:
        # Vérifie si les données nécessaires sont envoyées dans la requête
        if "insert_id" in request.form:
            # Déchiffre l'ID de référence
            id_reference = encryptor("decrypt", request.form["id_reference"])
            categorie_article = request.form["categorie_article"].strip()
            description = request.form["description"].strip()

            # Connexion à la base de données MySQL
            conn = get_connection()
            cursor = conn.cursor()

            # Vérification si la région existe déjà dans la base de données
            cursor.execute("SELECT * FROM categorie_article WHERE categorie_article = %s", (categorie_article,))
            existing_categorie_article = cursor.fetchone()

            if existing_categorie_article:
                # La région existe déjà
                conn.close()
                return jsonify({"status": "true", "message": "La région existe déjà."})

            # Si la région n'existe pas, on l'ajoute à la base de données
            try:
                cursor.execute(
                    "INSERT INTO categorie_article (categorie_article, description, id_reference) VALUES (%s, %s, %s)",
                    (categorie_article, description, id_reference),
                )
                conn.commit()
                conn.close()
                return jsonify(
                    {"status": "success", "message": "Région ajoutée avec succès."}
                )
            except Exception as e:
                conn.close()
                return jsonify(
                    {"status": "error", "message": f"Erreur MySQL : {str(e)}"}
                )

        elif "edit_id" in request.form:
            # Si l'ID de la région à modifier est envoyé
            edit_id = encryptor(
                "decrypt", request.form["edit_id"]
            )  # Déchiffre l'ID de la région
            categorie_article = request.form["categorie_article"].strip()
            description = request.form["description"].strip()

            # Connexion à la base de données MySQL
            conn = get_connection()
            cursor = conn.cursor()

            # Mettre à jour les informations de la région
            try:
                cursor.execute(
                    """
                    UPDATE categorie_article
                    SET categorie_article = %s, description = %s
                    WHERE id_categorie_article = %s
                """,
                    (categorie_article, description,  edit_id),
                )

                conn.commit()
                conn.close()
                return jsonify(
                    {"status": "success", "message": "Région mise à jour avec succès."}
                )
            except Exception as e:
                conn.close()
                return jsonify(
                    {"status": "error", "message": f"Erreur MySQL : {str(e)}"}
                )

        else:
            return jsonify({"status": "error", "message": "Paramètres manquants."})

    except Exception as e:
        # Si une autre erreur se produit, retour d'une erreur générique
        return jsonify({"status": "error", "message": f"Erreur : {str(e)}"})
