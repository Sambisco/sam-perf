from flask import Flask, render_template, request, redirect, url_for, flash, session
import hashlib
from templates.include.connect import get_connection


def update_password_portail():
    if "emailconnect" in request.form and "mdpconnect" in request.form:
        emailconnect = request.form["emailconnect"]
        mdpconnect = hashlib.md5(
            request.form["mdpconnect"].encode()
        ).hexdigest()  # MD5 du mot de passe

        # Connexion à la base de données
        conn = get_connection()
        cursor = conn.cursor()

        # Vérification de l'existence de l'email
        cursor.execute("SELECT * FROM employe WHERE email_e = %s", (emailconnect,))
        user = cursor.fetchone()

        if user:
            # Mise à jour du mot de passe
            cursor.execute(
                "UPDATE employe SET password = %s WHERE email_e = %s",
                (mdpconnect, emailconnect),
            )
            conn.commit()

            # Utilisation de f-string pour intégrer l'URL générée
            success_message = f"Le mot de passe a été modifié avec succès ! <a href='{url_for('portail')}'>Se connecter</a>"

            # Flash message
            flash(success_message, "success")

            # Message dans la session
            session["message_sucess"] = success_message

            # Stocker les informations dans la session
            session["emailconnect"] = emailconnect
            session["mdpconnect"] = mdpconnect

            # Redirection vers la page de réinitialisation du mot de passe
            return redirect(url_for("initialise_password_portail", code=emailconnect))
        else:
            # Message d'erreur si l'email n'est pas trouvé
            session["message_error"] = "L'email fourni n'existe pas."
            return redirect(url_for("portail"))

    return redirect(url_for("portail"))
