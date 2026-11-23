import random
import datetime
from flask import request, jsonify
from templates.include.connect import get_connection
from templates.include.encryptor import encryptor


def save_import_categorie():
    data = request.form

    # Récupération des listes depuis le form
    categorie_articles = request.form.getlist("categorie_article[]")
    descriptions = request.form.getlist("description[]")

    print(f"categorie_article: {categorie_articles}")
    print(f"description: {descriptions}")

    # Vérification que toutes les listes ont la même longueur
    lengths = list(
        map(
            len,
            [
                categorie_articles,
                descriptions,
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

    valeurs_validees = []
    erreurs = {}

    with get_connection() as conn:
        with conn.cursor() as cursor:

            for i in range(lengths[0]):
                categorie_article = categorie_articles[i].strip()
                description = descriptions[i].strip()

                valeurs_validees.append(
                    (
                        categorie_article,
                        description,
                        id_reference,
                    )
                )

            if valeurs_validees:
                try:
                    query = """
                        INSERT INTO categorie_article (categorie_article, description, id_reference)
                        VALUES (%s, %s, %s)
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
