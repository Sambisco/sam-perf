from flask import request, jsonify
from templates.include.connect import get_connection
from templates.include.encryptor import encryptor


def format_amount(value, decimals=0):
    if value in (0, "0.000", None):
        return ""
    try:
        # Arrondit à "decimals" décimales
        value = round(float(value), decimals)
        # Formate avec séparateur d'espace et virgule décimale
        format_str = "{:,.{prec}f}".format(value, prec=decimals)
        return format_str.replace(",", " ").replace(".", ",")
    except Exception:
        return str(value)


def dashboard_gs():
    data = {}

    if "id" not in request.form or "date" not in request.form:
        return jsonify({"error": "Paramètres manquants"}), 400

    try:
        id_ref = encryptor("decrypt", request.form["id"])
        date = request.form["date"].strip()
        current_mois = request.form["current_mois"].strip()
        with get_connection() as conn:
            with conn.cursor(dictionary=True) as cursor:
                # Matière
                cursor.execute(
                    """
                    SELECT COUNT(matiere.id_matiere) AS matiere 
                    FROM matiere 
                    INNER JOIN categorie_article ON categorie_article.id_categorie_article = matiere.id_categorie_article 
                    INNER JOIN reference ON reference.id_reference = categorie_article.id_reference 
                    WHERE reference.id_reference = %s
                """,
                    (id_ref,),
                )
                result = cursor.fetchone()
                data["matiere"] = (
                    format_amount(result["matiere"]) if result and result["matiere"] else 0
                )

                # Catégories
                cursor.execute(
                    """
                    SELECT COUNT(categorie_article.id_categorie_article) AS id_categorie 
                    FROM categorie_article  
                    WHERE id_reference = %s
                """,
                    (id_ref,),
                )
                result = cursor.fetchone()
                data["categorie"] = (
                    format_amount(result["id_categorie"]) if result and result["id_categorie"] else 0
                )

                # Stock matières
                cursor.execute(
                    """
                    SELECT SUM(matiere.nbre_unite) AS stock 
                    FROM matiere 
                    INNER JOIN categorie_article ON categorie_article.id_categorie_article = matiere.id_categorie_article 
                    INNER JOIN reference ON reference.id_reference = categorie_article.id_reference 
                    WHERE reference.id_reference = %s
                """,
                    (id_ref,),
                )
                result = cursor.fetchone()
                data["stock"] = format_amount(result["stock"]) if result and result["stock"] else 0

                # Affectations
                if not current_mois:
                    cursor.execute(
                    """
                    SELECT COUNT(*) AS id_affectation 
                    FROM affectation 
                    INNER JOIN contrat ON contrat.id_contrat = affectation.id_contrat
                    INNER JOIN employe ON employe.id_employe = contrat.id_employe
                    INNER JOIN region ON region.id_region = affectation.id_region
                    INNER JOIN reference ON reference.id_reference = employe.id_reference 
                    WHERE reference.id_reference = %s 
                      AND DATE_FORMAT(date_affectation,'%Y') = %s
                """,
                    (id_ref, date),
                )
                else:
                    cursor.execute(
                        """
                        SELECT COUNT(*) AS id_affectation 
                        FROM affectation 
                        INNER JOIN contrat ON contrat.id_contrat = affectation.id_contrat
                        INNER JOIN employe ON employe.id_employe = contrat.id_employe
                        INNER JOIN region ON region.id_region = affectation.id_region
                        INNER JOIN reference ON reference.id_reference = employe.id_reference 
                        WHERE reference.id_reference = %s 
                          AND DATE_FORMAT(date_affectation,'%Y') = %s AND DATE_FORMAT(date_affectation,'%m') = %s
                    """,
                        (id_ref, date, current_mois),
                    )
                result = cursor.fetchone()
                data["affectation"] = (
                    format_amount(result["id_affectation"])
                    if result and result["id_affectation"]
                    else 0
                )

                # Nombre Entrées et Somme entree
                if not current_mois:
                    cursor.execute(
                        """
                        SELECT COUNT(*) AS entree, SUM(total) AS montant_entree  
                        FROM entree
                        INNER JOIN reference ON reference.id_reference = entree.id_reference
                        WHERE reference.id_reference = %s 
                          AND DATE_FORMAT(date_entree,'%Y') = %s
                    """,
                        (id_ref, date),
                    )
                else:
                    cursor.execute(
                        """
                        SELECT COUNT(*) AS entree, SUM(total) AS montant_entree  
                        FROM entree
                        INNER JOIN reference ON reference.id_reference = entree.id_reference
                        WHERE reference.id_reference = %s 
                          AND DATE_FORMAT(date_entree,'%Y') = %s AND DATE_FORMAT(date_entree,'%m')= %s
                    """,
                        (id_ref, date, current_mois),
                    )
                result = cursor.fetchone()
                data["entree"] = format_amount(result["entree"]) if result and result["entree"] else 0
                data["montant_entree"] = (
                    format_amount(result["montant_entree"])
                    if result and result["montant_entree"]
                    else 0
                )

                # Nombre Sorties et Quantité sortie
                if not current_mois:
                    cursor.execute(
                        """
                            SELECT COUNT(*) AS sortie_interne,  SUM(total) AS quantite_annuel_interne 
                            FROM sortie 
                            INNER JOIN contrat ON contrat.id_contrat = sortie.id_contrat
                            INNER JOIN employe ON employe.id_employe = contrat.id_employe
                            INNER JOIN reference ON reference.id_reference = employe.id_reference 
                            WHERE reference.id_reference = %s 
                            AND DATE_FORMAT(date_sortie,'%Y') = %s
                        """,
                        (id_ref, date),
                    )
                    result_interne = cursor.fetchone()

                    cursor.execute(
                        """
                            SELECT COUNT(*) AS sortie_externe,  SUM(total) AS quantite_annuel_externe
                            FROM sortie_externe
                            INNER JOIN reference ON reference.id_reference=sortie_externe.id_reference
                            WHERE reference.id_reference = %s 
                            AND DATE_FORMAT(date_sortie,'%Y') = %s
                        """,
                        (id_ref, date),
                    )
                    result_externe = cursor.fetchone()
                else:
                    cursor.execute(
                        """
                        SELECT COUNT(*) AS sortie_interne,  SUM(total) AS quantite_annuel_interne 
                        FROM sortie 
                        INNER JOIN contrat ON contrat.id_contrat = sortie.id_contrat
                        INNER JOIN employe ON employe.id_employe = contrat.id_employe
                        INNER JOIN reference ON reference.id_reference = employe.id_reference 
                        WHERE reference.id_reference = %s 
                          AND DATE_FORMAT(date_sortie,'%Y') = %s AND DATE_FORMAT(date_sortie,'%m') = %s
                    """,
                        (id_ref, date, current_mois),
                    )
                    result_interne = cursor.fetchone()
                    cursor.execute(
                        """
                        SELECT COUNT(*) AS sortie_externe,  SUM(total) AS quantite_annuel_externe
                        FROM sortie_externe
                        INNER JOIN reference ON reference.id_reference=sortie_externe.id_reference
                        WHERE reference.id_reference = %s 
                          AND DATE_FORMAT(date_sortie,'%Y') = %s AND DATE_FORMAT(date_sortie,'%m') = %s
                    """,
                        (id_ref, date, current_mois),
                    )
                    result_externe = cursor.fetchone()
                sortie = (
                     float(result_interne["sortie_interne"] or 0)
                    + float(result_externe["sortie_externe"] or 0)
                )
                quantite_annuel = (
                    float(result_interne["quantite_annuel_interne"] or 0)
                    + float(result_externe["quantite_annuel_externe"] or 0)
                )
                
                data["sortie"] = format_amount(sortie) if sortie else 0
                data["quantite_annuel"] = format_amount(quantite_annuel) if quantite_annuel else 0


                # Réceptions carburant
                if not current_mois:
                    cursor.execute(
                        """
                           SELECT COUNT(*) AS reception_carbur, SUM(carburant_gasoil + carburant_super) AS reception_annuel_litre 
                           FROM reception_carburant 
                           INNER JOIN fournisseur ON fournisseur.id_fournisseur = reception_carburant.id_fournisseur
                           INNER JOIN reference ON reference.id_reference = fournisseur.id_reference  
                           WHERE reference.id_reference = %s 
                           AND DATE_FORMAT(date_reception,'%Y') = %s
                        """,
                        (id_ref, date),
                    )
                else:
                    cursor.execute(
                        """
                           SELECT COUNT(*) AS reception_carbur, SUM(carburant_gasoil + carburant_super) AS reception_annuel_litre 
                           FROM reception_carburant 
                           INNER JOIN fournisseur ON fournisseur.id_fournisseur = reception_carburant.id_fournisseur
                           INNER JOIN reference ON reference.id_reference = fournisseur.id_reference  
                           WHERE reference.id_reference = %s 
                           AND DATE_FORMAT(date_reception,'%Y') = %s AND DATE_FORMAT(date_reception,'%m') = %s
                        """,
                        (id_ref, date, current_mois),
                    )
                result = cursor.fetchone()
                data["reception_carbur"] = (
                    format_amount(result["reception_carbur"])
                    if result and result["reception_carbur"]
                    else 0
                )
                data["reception_annuel_litre"] = (
                    format_amount(result["reception_annuel_litre"])
                    if result and result["reception_annuel_litre"]
                    else 0
                )

                # Dotations
                if not current_mois:
                    cursor.execute(
                        """
                        SELECT COUNT(*) AS dotation, SUM(carburant) AS dotation_annuel_litre 
                        FROM dotation
                        INNER JOIN contrat ON contrat.id_contrat = dotation.id_contrat
                        INNER JOIN employe ON employe.id_employe = contrat.id_employe
                        INNER JOIN reference ON reference.id_reference = employe.id_reference 
                        WHERE reference.id_reference = %s 
                          AND DATE_FORMAT(date_dotation,'%Y') = %s
                        """,
                        (id_ref, date),
                    )
                else:
                    cursor.execute(
                        """
                        SELECT COUNT(*) AS dotation, SUM(carburant) AS dotation_annuel_litre 
                        FROM dotation
                        INNER JOIN contrat ON contrat.id_contrat = dotation.id_contrat
                        INNER JOIN employe ON employe.id_employe = contrat.id_employe
                        INNER JOIN reference ON reference.id_reference = employe.id_reference 
                        WHERE reference.id_reference = %s 
                          AND DATE_FORMAT(date_dotation,'%Y') = %s AND DATE_FORMAT(date_dotation,'%m') = %s
                        """,
                        (id_ref, date,current_mois),
                    )
                result = cursor.fetchone()
                data["dotation"] = (
                    format_amount(result["dotation"]) if result and result["dotation"] else 0
                )
                data["dotation_annuel_litre"] = (
                    format_amount(result["dotation_annuel_litre"])
                    if result and result["dotation_annuel_litre"]
                    else 0
                )

                # Stock carburant
                cursor.execute(
                    """
                    SELECT SUM(stock_carburant) AS stock_carburant 
                    FROM stock_carburant 
                    WHERE id_reference = %s
                """,
                    (id_ref,),
                )
                result = cursor.fetchone()
                data["stock_carburant"] = (
                    format_amount(result["stock_carburant"])
                    if result and result["stock_carburant"]
                    else 0
                )

    except Exception as e:
        print(f"Erreur fetch_dashboard_stats : {e}")
        return jsonify({"error": "Erreur serveur"}), 500

    return jsonify(data)
