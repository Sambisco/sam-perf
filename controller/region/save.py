from flask import request, jsonify
from templates.include.connect import get_connection  # On utilise get_connection ici pour la connexion à la DB
from templates.include.encryptor import encryptor

def save_region():
    try:
        # Vérifie si les données nécessaires sont envoyées dans la requête
        if 'insert_id' in request.form:
            # Déchiffre l'ID de référence
            id_reference = encryptor('decrypt', request.form['id_reference'])
            region = request.form['region'].strip()
            telephone = request.form['telephone'].strip()
            email = request.form['email'].strip()

            # Connexion à la base de données MySQL
            conn = get_connection()
            cursor = conn.cursor()

            # Vérification si la région existe déjà dans la base de données
            cursor.execute("SELECT * FROM region WHERE region = %s", (region,))
            existing_region = cursor.fetchone()

            if existing_region:
                # La région existe déjà
                conn.close()
                return jsonify({'status': 'true', 'message': 'La région existe déjà.'})

            # Si la région n'existe pas, on l'ajoute à la base de données
            try:
                cursor.execute(
                    "INSERT INTO region (region, telephone, email, id_reference) VALUES (%s, %s, %s, %s)",
                    (region, telephone, email, id_reference)
                )
                conn.commit()
                conn.close()
                return jsonify({'status': 'success', 'message': 'Région ajoutée avec succès.'})
            except Exception as e:
                conn.close()
                return jsonify({'status': 'error', 'message': f'Erreur MySQL : {str(e)}'})

        elif 'edit_id' in request.form:
            # Si l'ID de la région à modifier est envoyé
            edit_id = encryptor('decrypt', request.form['edit_id'])  # Déchiffre l'ID de la région
            region = request.form['region'].strip()
            telephone = request.form['telephone'].strip()
            email = request.form['email'].strip()

            # Connexion à la base de données MySQL
            conn = get_connection()
            cursor = conn.cursor()

            # Mettre à jour les informations de la région
            try:
                cursor.execute("""
                    UPDATE region
                    SET region = %s, telephone = %s, email = %s
                    WHERE id_region = %s
                """, (region, telephone, email, edit_id))

                conn.commit()
                conn.close()
                return jsonify({'status': 'success', 'message': 'Région mise à jour avec succès.'})
            except Exception as e:
                conn.close()
                return jsonify({'status': 'error', 'message': f'Erreur MySQL : {str(e)}'})

        else:
            return jsonify({'status': 'error', 'message': 'Paramètres manquants.'})

    except Exception as e:
        # Si une autre erreur se produit, retour d'une erreur générique
        return jsonify({'status': 'error', 'message': f'Erreur : {str(e)}'})
