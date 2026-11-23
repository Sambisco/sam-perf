from flask import request, session, redirect, url_for, render_template
from flask_mail import Message


def mail_recup_portail_handler(mail):
    if request.method == 'POST':
        email = request.form.get('emailconnect')

        if not email:
            session['message_delete'] = "Email manquant"
            return redirect(url_for('mail_recup_portail'))

        try:
            reset_url = url_for(
                "initialise_password_portail", code=email, _external=True
            )
            msg = Message(
                subject="Lien de réinitialisation",
                recipients=[email],
                html=f"""
                    <h3>Réinitialisation de mot de passe</h3>
                    <p>Vous avez demandé la réinitialisation de votre mot de passe.</p>
                    <p><a href="{reset_url}">Cliquez ici pour réinitialiser votre mot de passe</a></p>
                """
            )
            mail.send(msg)
            session['message_sucess'] = "Email envoyé avec succès."
            return redirect(url_for("mail_recup_portail"))  # ✅ Correct
        except Exception as e:
            print("Erreur lors de l'envoi de l'e-mail :", e)
            session['message_delete'] = f"Erreur lors de l'envoi : {str(e)}"

        return redirect(url_for('mail_recup_portail'))

    # Méthode GET
    msg_delete = session.pop('message_delete', None)
    msg_succes = session.pop('message_sucess', None)
    return render_template('email_recupe_portail.html', message_delete=msg_delete, message_sucess=msg_succes)
