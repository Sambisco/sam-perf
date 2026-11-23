from flask import request, redirect, session, url_for
from templates.include.connect import get_connection
import hashlib
from templates.include.encryptor import encryptor

def login():
    if request.method == 'POST':
        emailconnect_raw = request.form.get('emailconnect')
        if not emailconnect_raw or emailconnect_raw.strip() == '':
            session['message_delete'] = "Email manquant"
            session['msg_type_delete'] = "danger"
            return redirect("/")

        emailconnect = emailconnect_raw.strip().lower()

        mdp_raw = request.form.get('mdpconnect')
        if not mdp_raw or mdp_raw.strip() == '':
            session['message_delete'] = "Mot de passe manquant"
            session['msg_type_delete'] = "danger"
            return redirect("/")

        mdpconnect = hashlib.md5(mdp_raw.strip().encode()).hexdigest()

        conn = get_connection()
        if conn is None:
            session['message_delete'] = "Erreur de connexion à la base de données"
            session['msg_type_delete'] = "danger"
            return redirect("/")

        cursor = conn.cursor(dictionary=True)

        query = """
        SELECT 
            user.*, reference.*, sub_users.*,
            user.iduser AS iduser, 
            reference.id_reference AS id_reference, 
            reference.logo, 
            reference.entreprise
        FROM user 
        LEFT JOIN reference ON reference.iduser = user.iduser
        LEFT JOIN sub_users ON sub_users.id_reference = reference.id_reference 
        WHERE 
            (user.login = %s AND user.password = %s) OR 
            (user.telephone_user = %s AND user.password = %s) OR 
            (sub_email = %s AND sub_password = %s) OR 
            (telephone_sub_user = %s AND sub_password = %s)
        LIMIT 1
        """
        values = [emailconnect, mdpconnect] * 4
        cursor.execute(query, values)
        userinfo = cursor.fetchone()

        cursor.close()
        conn.close()

        if userinfo:
            session['email'] = emailconnect
            session['iduser'] = userinfo['iduser']
            session['id_reference'] = userinfo.get('id_reference')
            session['nomuser'] = userinfo.get('nomuser')
            session['nom_sub_user'] = userinfo.get('nom_sub_user')

            # ✅ Image + ID crypté accessibles à tous
            session['image_reference'] = userinfo.get('image_reference') or '/static/default-logo.png'
            if userinfo.get('id_reference'):
                session['id_m'] = encryptor('encrypt', str(userinfo['id_reference']))
            else:
                session['id_m'] = encryptor('encrypt', str(userinfo['iduser']))

            # ✅ Toujours stocker userinfo dans result (pour templates)
            result_dict = dict(userinfo)
            session['result'] = result_dict

            # ✅ Si sous-utilisateur → gérer le profil + redirection spécifique
            if userinfo.get('sub_email') == emailconnect or userinfo.get('telephone_sub_user') == emailconnect:
                session['sub_email'] = userinfo.get('sub_email')

                raw_profil = userinfo.get('profil')
                if raw_profil and str(raw_profil).strip().lower() not in ['none', 'null', '']:
                    profil_value = str(raw_profil).strip()
                else:
                    profil_value = None

                session['profil'] = profil_value
                result_dict['profil'] = profil_value
                session['result'] = result_dict  # mettre à jour avec le profil

                print("✅ Session['profil'] =", session['profil'])

                # Redirection en fonction du rôle
                if profil_value == "Salaire":
                    return redirect(f"/page/salaire?id={session['id_m']}")
                elif profil_value == "Ressources humaines":
                    return redirect(f"/page/dashboard?id={session['id_m']}")
                elif profil_value == "Pointage":
                    return redirect(f"/page/pointeur?id={session['id_m']}&idu={session['sub_email']}")
                elif profil_value == "Comptable matiére":
                    return redirect(f"/gstock/dashboard?id={session['id_m']}")
                elif profil_value == "Assistant(e) C. matiére":
                    return redirect(f"/gstock/sortie?id={session['id_m']}")
                elif profil_value in ["Administrateur", "Sup-administrateur"]:
                    return redirect(f"/page/reference?id={session['id_m']}")
                else:
                    session['message_delete'] = "Profil inconnu"
                    session['msg_type_delete'] = "danger"
                    return redirect("/")
            else:
                # ✅ Utilisateur principal
                return redirect(f"/page/reference?id={session['id_m']}")
        else:
            session['message_delete'] = "Identifiants incorrects"
            session['msg_type_delete'] = "danger"
            return redirect("/")
    else:
        return redirect(url_for('index'))
