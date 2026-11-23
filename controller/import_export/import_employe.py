import random
import datetime
from flask import request, jsonify
from templates.include.connect import get_connection
from templates.include.encryptor import encryptor


def save_import_employe():
    data = request.form

    # Récupération des listes depuis le form
    prenoms = request.form.getlist("prenom[]")
    noms = request.form.getlist("nom[]")
    dates_n = request.form.getlist("date_n[]")
    lieus_n = request.form.getlist("lieu_n[]")
    adresses = request.form.getlist("adresse_e[]")
    telephones = request.form.getlist("telephone_e[]")
    emails = request.form.getlist("email_e[]")
    genres = request.form.getlist("genre[]")
    postes = request.form.getlist("poste[]")

    print(f"prenoms: {prenoms}")
    print(f"noms: {noms}")
    print(f"dates_n: {dates_n}")
    print(f"postes: {postes}")

    # Vérification que toutes les listes ont la même longueur
    lengths = list(
        map(
            len,
            [
                prenoms,
                noms,
                dates_n,
                lieus_n,
                adresses,
                telephones,
                emails,
                genres,
                postes,
            ],
        )
    )
    if len(set(lengths)) != 1:
        error_msg = f"Listes de longueurs différentes : {lengths}"
        print(error_msg)
        return jsonify({"error": error_msg}), 400

    id_reference = encryptor("decrypt", data.get("id_reference", ""))
    if not id_reference:
        return jsonify({"error": "id_reference invalide ou manquant."}), 400

    now = datetime.datetime.now()
    valeurs_validees = []
    erreurs = {}

    with get_connection() as conn:
        with conn.cursor() as cursor:

            def generate_unique_matricule():
                while True:
                    matricule_r = random.randint(100000, 999999)
                    cursor.execute(
                        "SELECT matricule FROM employe WHERE matricule = %s",
                        (matricule_r,),
                    )
                    if not cursor.fetchone():
                        return matricule_r

            for i in range(lengths[0]):
                prenom = prenoms[i].strip()
                nom = noms[i].strip()
                date_str = dates_n[i].strip()
                lieu = lieus_n[i].strip()
                adresse = adresses[i].strip()
                tel = telephones[i].strip()
                email = emails[i].strip()
                genre = genres[i].strip()
                poste = postes[i].strip()

                # Validation date de naissance
                try:
                    date_naissance = datetime.datetime.strptime(date_str, "%Y-%m-%d")
                except Exception as e:
                    erreurs[i] = f"Date invalide: {date_str}"
                    print(f"Ligne {i} erreur date: {e}")
                    continue

                # Validation âge >= 15 ans
                age = (now - date_naissance).days // 365
                if age < 15:
                    erreurs[i] = f"Âge < 15 ans ({age})"
                    print(f"Ligne {i} ignorée: âge {age} < 15")
                    continue

                matricule = generate_unique_matricule()

                valeurs_validees.append(
                    (
                        matricule,
                        prenom.capitalize(),
                        nom.capitalize(),
                        date_str,
                        lieu,
                        adresse,
                        tel,
                        email,
                        genre.capitalize(),
                        poste,
                        id_reference,
                    )
                )

            if valeurs_validees:
                try:
                    query = """
                        INSERT INTO employe (matricule, prenom, nom, date_n, lieu_n, adresse_e, telephone_e, email_e, genre, poste, id_reference)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    cursor.executemany(query, valeurs_validees)
                    conn.commit()
                    print(f"{len(valeurs_validees)} employés insérés.")
                except Exception as e:
                    conn.rollback()
                    error_msg = f"Erreur insertion: {str(e)}"
                    print(error_msg)
                    return jsonify({"error": error_msg}), 500
            else:
                print("Aucune donnée valide à insérer.")

    # Retourne succès avec détails erreurs éventuelles
    return jsonify(
        {
            "message": f"{len(valeurs_validees)} employés importés avec succès.",
            "errors": erreurs,
        }
    )
