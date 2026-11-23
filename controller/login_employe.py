from flask import Flask, render_template, request, redirect, session, url_for, flash
import hashlib
from templates.include.connect import get_connection
from templates.include.encryptor import encryptor


def login_employe():
    if request.method == "POST":
        # Récupération des données du formulaire
        emailconnect = request.form["emailconnect"]
        mdpconnect = request.form["mdpconnect"]

        # Hachage du mot de passe (si nécessaire, assure-toi d'utiliser le même algorithme que dans la base de données)
        hashed_mdp = hashlib.md5(mdpconnect.encode()).hexdigest()

        # Connexion à la base de données
        conn = get_connection()
        cursor = conn.cursor()

        # Requête pour vérifier l'utilisateur dans la base de données
        query = """
        SELECT * FROM contrat
        INNER JOIN employe ON employe.id_employe = contrat.id_employe
        INNER JOIN reference ON reference.id_reference = employe.id_reference
        WHERE (employe.telephone_e = %s OR employe.email_e = %s) AND employe.password = %s
        """
        cursor.execute(query, (emailconnect, emailconnect, hashed_mdp))
        user = cursor.fetchone()

        # Si l'utilisateur existe
        if user:
            user_dict = dict(zip([column[0] for column in cursor.description], user))
            # Chiffrement des identifiants et stockage dans la session
            session["id_contrat"] = encryptor("encrypt", str(user_dict["id_contrat"]))
            session["id_employe"] = encryptor("encrypt", str(user_dict["id_employe"]))
            session["logo"] = user_dict["logo"]
            session["matricule"] = str(user_dict["matricule"])

            # Redirection vers le tableau de bord ou une autre page
            return redirect(
                url_for(
                    "dashboard_emp",
                    id=session["id_contrat"],
                    id_e=session["id_employe"],
                    my_logo=session["logo"],
                    matricule=session["matricule"],
                )
            )
        else:
            # Si les identifiants sont incorrects, afficher un message d'erreur
            session['message_delete'] = "Identifiants incorrects"
            session['msg_type_delete'] = "danger"
            return redirect(url_for("portail"))

    return render_template("portail.html")
