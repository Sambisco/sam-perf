from flask import request, jsonify
from templates.include.connect import get_connection
from templates.include.encryptor import encryptor


def fetch_select_ajax_g():
    if "id" not in request.form:
        return jsonify({"error": "ID manquant"}), 400

    id_reference_encrypted = request.form["id"]
    print(f"id_reference reçu (chiffré) : {id_reference_encrypted}")

    try:
        id_reference = encryptor("decrypt", id_reference_encrypted).strip()
        print(f"id_reference déchiffré : {id_reference}")
    except Exception as e:
        print(f"Erreur déchiffrement : {e}")
        return jsonify({"error": "Erreur déchiffrement ID"}), 400

    categorie_html = "<option value=''>Choisissez catégorie</option>"
    data1 = {}

    try:
        with get_connection() as conn:
            with conn.cursor(dictionary=True) as cursor:
                # === Récupération des catégories ===
                cursor.execute(
                    """
                    SELECT * FROM categorie_article 
                    INNER JOIN reference  
                        ON reference.id_reference = categorie_article.id_reference
                    WHERE reference.id_reference = %s
                    ORDER BY id_categorie_article DESC
                    """,
                    (id_reference,),
                )
                rows_cat = cursor.fetchall()
                print(f"Catégories récupérées : {len(rows_cat)}")

                for row in rows_cat:
                    id_cat = row["id_categorie_article"]
                    nom_cat = row["categorie_article"]
                    categorie_html += f"<option value='{id_cat}'>{nom_cat}</option>"

                # === Récupération du stock carburant ===
                cursor.execute(
                    """
                    SELECT SUM(stock_carburant) AS stock_carburant
                    FROM stock_carburant
                    WHERE id_reference = %s
                    """,
                    (id_reference,),
                )
                result = cursor.fetchone()

                if result and result["stock_carburant"] is not None:
                    data1["stock_carburant"] = result["stock_carburant"]
                else:
                    data1["stock_carburant"] = 0

    except Exception as e:
        print(f"Erreur SQL : {e}")
        return jsonify({"error": "Erreur serveur"}), 500

    # Retourne à la fois les catégories + le stock
    return jsonify(
        {"categories": categorie_html, "stock_carburant": data1["stock_carburant"]}
    )
