from flask import request, jsonify
from templates.include.connect import get_connection
from templates.include.encryptor import encryptor


def fetch_select_ajax():
    # Vérifier que 'id' est bien dans le formulaire POST
    if "id" not in request.form:
        return jsonify({"error": "ID manquant"}), 400

    # Récupérer et afficher la valeur reçue
    id_reference_encrypted = request.form["id"]
    print(f"id_reference reçu (chiffré) : {id_reference_encrypted}")

    try:
        # Déchiffrer l'id si tu utilises encryptor
        id_reference = encryptor("decrypt", id_reference_encrypted).strip()
        print(f"id_reference déchiffré : {id_reference}")
    except Exception as e:
        print(f"Erreur déchiffrement : {e}")
        return jsonify({"error": "Erreur déchiffrement ID"}), 400

    departement_html = "<option value=''>Choisissez département</option>"
    region_html = "<option value=''>Choisissez antenne régionale</option>"

    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                # Récupérer les départements
                cursor.execute(
                    """
                    SELECT id_departement, nom_departement
                    FROM departement
                    WHERE id_reference = %s
                    ORDER BY id_departement DESC
                    """,
                    (id_reference,),
                )
                rows_dept = cursor.fetchall()
                print(f"Départements récupérés : {len(rows_dept)}")
                for id_dept, nom in rows_dept:
                    # Si besoin, crypte les ids pour la sortie (sinon juste id_dept)
                    departement_html += f"<option value='{id_dept}'>{nom}</option>"

                # Récupérer les régions
                cursor.execute(
                    """
                    SELECT id_region, region
                    FROM region
                    WHERE id_reference = %s
                    ORDER BY id_region DESC
                    """,
                    (id_reference,),
                )
                rows_reg = cursor.fetchall()
                print(f"Régions récupérées : {len(rows_reg)}")
                for id_reg, nom in rows_reg:
                    region_html += f"<option value='{id_reg}'>{nom}</option>"

    except Exception as e:
        print(f"Erreur SQL : {e}")
        return jsonify({"error": "Erreur serveur"}), 500

    # Retourne le HTML complet pour les selects
    return jsonify({"departements": departement_html, "regions": region_html})
