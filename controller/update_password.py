from flask import request, session, redirect, url_for, flash
import hashlib
from templates.include.connect import get_connection

def update_password():
    if request.method == 'POST':
        email = request.form.get('emailconnect')
        new_password = request.form.get('mdpconnect')

        if not email or not new_password:
            flash("Tous les champs doivent être remplis.", "danger")
            return redirect(url_for('initialise_password', code=email))

        # Hachage en md5 (comme en PHP)
        hashed_password = hashlib.md5(new_password.encode()).hexdigest()

        db = get_connection()
        cursor = db.cursor()

        # Requête pour récupérer un utilisateur ou un sous-utilisateur
        query = """
            SELECT user.iduser, sub_users.sub_email 
            FROM user 
            LEFT JOIN reference ON reference.iduser = user.iduser
            LEFT JOIN sub_users ON sub_users.id_reference = reference.id_reference
            WHERE user.login = %s OR sub_users.sub_email = %s
            LIMIT 1
        """
        cursor.execute(query, (email, email))
        user_info = cursor.fetchone()

        # Debug : afficher le résultat de la requête
        print("user_info:", user_info, type(user_info))

        # Gestion sécurisée du contenu de user_info
        sub_email = None
        if user_info:
            # Si user_info est un dictionnaire (ex: DictCursor)
            if isinstance(user_info, dict):
                sub_email = user_info.get('sub_email')
            # Si c'est un tuple classique
            elif isinstance(user_info, tuple) and len(user_info) > 1:
                sub_email = user_info[1]

        if sub_email == email:
            # Mise à jour du mot de passe dans sub_users
            update_query = "UPDATE sub_users SET sub_password = %s WHERE sub_email = %s"
            cursor.execute(update_query, (hashed_password, email))
        else:
            # Mise à jour du mot de passe dans user
            update_query = "UPDATE user SET password = %s WHERE login = %s"
            cursor.execute(update_query, (hashed_password, email))

        db.commit()
        cursor.close()
        db.close()

        flash("Le mot de passe a été modifié avec succès ! <a href='/'>Se connecter</a>", "success")
        session['message_sucess'] = "Le mot de passe a été modifié avec succès ! <a href='/'>Se connecter</a>"
        return redirect(url_for('initialise_password', code=email))
