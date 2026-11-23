import random
import datetime
from flask import request, jsonify
from templates.include.connect import get_connection
from templates.include.encryptor import encryptor


def save_import_matiere():
    data = request.form

    # Récupération des listes depuis le form
    designations = request.form.getlist("designation[]")
    nbre_unites = request.form.getlist("nbre_unite[]")
    nature_unites = request.form.getlist("nature_unite[]")
    print(f"categorie_article: {designations}")
    print(f"nbre_unite: {nbre_unites}")
    print(f"nature_unite: {nature_unites}")

    # Vérification que toutes les listes ont la même longueur
    lengths = list(
        map(
            len,
            [designations, nbre_unites, nature_unites],
        )
    )
    if len(set(lengths)) != 1:
        error_msg = f"Listes de longueurs différentes : {lengths}"
        print(error_msg)
        return jsonify({"error": error_msg}), 400

    id_categorie_article =  data.get("id_categorie_article", "")
    if not id_categorie_article:
        return jsonify({"error": "id_categorie_article invalide ou manquant."}), 400

    valeurs_validees = []
    erreurs = {}

    with get_connection() as conn:
        with conn.cursor() as cursor:

            for i in range(lengths[0]):
                categorie_article = designations[i].strip()
                nbre_unite = nbre_unites[i].strip()
                nature_unite = nature_unites[i].strip()
                valeurs_validees.append(
                    (
                        categorie_article,
                        nbre_unite,
                        nature_unite,
                        id_categorie_article,
                    )
                )

            if valeurs_validees:
                try:
                    query = """
                       INSERT INTO matiere(designation,nbre_unite,nature_unite,id_categorie_article)
                        VALUES (%s, %s, %s, %s)
                    """
                    cursor.executemany(query, valeurs_validees)
                    conn.commit()
                    print(f"{len(valeurs_validees)} categorie_article insérés.")
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
            "message": f"{len(valeurs_validees)} categorie importés avec succès.",
            "errors": erreurs,
        }
    )
