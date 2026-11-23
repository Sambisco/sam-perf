from flask import request, jsonify
from datetime import datetime
from templates.include.connect import get_connection
from templates.include.encryptor import encryptor


def save_salaire():

    data = request.get_json()

    if not data:
        return jsonify({"error": "Données invalides"}), 400

    # =====================================================
    # INSERT
    # =====================================================
    if "insert_id" in data:

        lignes = data.get("lignes", [])
        date_du = data.get("date_du", "").strip() + "-01"
        date_paiement = data.get("date_paiement", "").strip()
        mode_paie = data.get("mode_paie")

        valeurs = []

        for item in lignes:
            valeurs.append(
                (
                    date_du,
                    date_paiement,
                    mode_paie,
                    item.get("s_nature", ""),
                    item.get("s_date_embauche", ""),
                    item.get("s_date_sorti", ""),
                    item.get("s_categorie", ""),
                    item.get("s_poste_occupe", ""),
                    item.get("s_situation_matr", ""),
                    item.get("s_conjoint", ""),
                    item.get("s_enfant", ""),
                    item.get("salaire_base", 0),
                    item.get("ind_fonction", 0),
                    item.get("ind_sujetion", 0),
                    item.get("ind_responsabilite", 0),
                    item.get("ind_sursalaire", 0),
                    item.get("ind_logement", 0),
                    item.get("salaire_brute", 0),
                    item.get("s_nb_trimf", 0),
                    item.get("sum_trimf", 0),
                    item.get("s_nb_irpp", 0),
                    item.get("sum_irpp", 0),
                    item.get("ind_transport", 0),
                    item.get("ind_telephone_in", 0),
                    item.get("ind_autre_indemnite", 0),
                    item.get("iprg_employe", 0),
                    item.get("irprg_patronale", 0),
                    item.get("irpc_employe", 0),
                    item.get("irpc_patronale", 0),
                    item.get("css_accident_travail", 0),
                    item.get("css_allocation_familiale", 0),
                    item.get("total_retenue_employe", 0),
                    item.get("total_retenue_patronale", 0),
                    item.get("s_amicale", 0),
                    item.get("s_tabaski", 0),
                    item.get("s_aute_cotisation", 0),
                    item.get("retenue_cotisation", 0),
                    item.get("cfce", 0),
                    item.get("total_prime", 0),
                    item.get("salaire_net", 0),
                    item.get("id_contrat", 0),
                )
            )

        try:
            with get_connection() as conn:
                with conn.cursor() as cursor:

                    query = """
                        INSERT INTO salaire(
                            date_du, date_paiement, mode_paie,
                            s_nature, s_date_embauche, s_date_sorti,
                            s_categorie, s_poste_occupe, s_situation_matr,
                            s_conjoint, s_enfant,
                            salaire_base, ind_fonction, ind_sujetion,
                            ind_responsabilite, ind_sursalaire, ind_logement,
                            salaire_brute, s_nb_trimf, sum_trimf,
                            s_nb_irpp, sum_irpp,
                            ind_transport, ind_telephone_in, ind_autre_indemnite,
                            iprg_employe, irprg_patronale,
                            irpc_employe, irpc_patronale,
                            css_accident_travail, css_allocation_familiale,
                            total_retenue_employe, total_retenue_patronale,
                            s_amicale, s_tabaski, s_aute_cotisation,
                            retenue_cotisation, cfce, total_prime,
                            salaire_net, id_contrat
                        ) VALUES (
                            %s,%s,%s,
                            %s,%s,%s,%s,%s,%s,%s,%s,
                            %s,%s,%s,%s,%s,%s,
                            %s,%s,%s,%s,%s,
                            %s,%s,%s,
                            %s,%s,%s,%s,
                            %s,%s,
                            %s,%s,
                            %s,%s,%s,
                            %s,%s,%s,
                            %s,%s
                        )
                    """

                    cursor.executemany(query, valeurs)
                    conn.commit()

            return jsonify({"status": "success"})

        except Exception as e:
            return jsonify({"error": str(e)}), 500

    # =====================================================
    # EDIT
    # =====================================================
    elif "edit_id" in data:

        try:
            id_mois = datetime.strptime(data.get("edit_id"), "%Y-%m")
            date_du = data.get("date_du", "").strip() + "-01"
            date_paiement = data.get("date_paiement", "").strip()
            mode_paie = data.get("mode_paie")
            lignes = data.get("lignes", [])

            with get_connection() as conn:
                with conn.cursor() as cursor:

                    # supprimer ancien mois
                    cursor.execute(
                        """
                        DELETE FROM salaire
                        WHERE YEAR(date_du)= %s AND MONTH(date_du)= %s
                    """,
                        (id_mois.year, id_mois.month),
                    )

                    valeurs = []

                    for item in lignes:
                        valeurs.append(
                            (
                                date_du,
                                data.get("date_paiement"),
                                data.get("mode_paie"),
                                item.get("s_nature", ""),
                                item.get("s_date_embauche", ""),
                                item.get("s_date_sorti", ""),
                                item.get("s_categorie", ""),
                                item.get("s_poste_occupe", ""),
                                item.get("s_situation_matr", ""),
                                item.get("s_conjoint", ""),
                                item.get("s_enfant", ""),
                                item.get("salaire_base", 0),
                                item.get("ind_fonction", 0),
                                item.get("ind_sujetion", 0),
                                item.get("ind_responsabilite", 0),
                                item.get("ind_sursalaire", 0),
                                item.get("ind_logement", 0),
                                item.get("salaire_brute", 0),
                                item.get("s_nb_trimf", 0),
                                item.get("sum_trimf", 0),
                                item.get("s_nb_irpp", 0),
                                item.get("sum_irpp", 0),
                                item.get("ind_transport", 0),
                                item.get("ind_telephone_in", 0),
                                item.get("ind_autre_indemnite", 0),
                                item.get("iprg_employe", 0),
                                item.get("irprg_patronale", 0),
                                item.get("irpc_employe", 0),
                                item.get("irpc_patronale", 0),
                                item.get("css_accident_travail", 0),
                                item.get("css_allocation_familiale", 0),
                                item.get("total_retenue_employe", 0),
                                item.get("total_retenue_patronale", 0),
                                item.get("s_amicale", 0),
                                item.get("s_tabaski", 0),
                                item.get("s_aute_cotisation", 0),
                                item.get("retenue_cotisation", 0),
                                item.get("cfce", 0),
                                item.get("total_prime", 0),
                                item.get("salaire_net", 0),
                                item.get("id_contrat", 0),
                            )
                        )

                    query = """
                            INSERT INTO salaire(
                            date_du, date_paiement, mode_paie,
                            s_nature, s_date_embauche, s_date_sorti,
                            s_categorie, s_poste_occupe, s_situation_matr,
                            s_conjoint, s_enfant,
                            salaire_base, ind_fonction, ind_sujetion,
                            ind_responsabilite, ind_sursalaire, ind_logement,
                            salaire_brute, s_nb_trimf, sum_trimf,
                            s_nb_irpp, sum_irpp,
                            ind_transport, ind_telephone_in, ind_autre_indemnite,
                            iprg_employe, irprg_patronale,
                            irpc_employe, irpc_patronale,
                            css_accident_travail, css_allocation_familiale,
                            total_retenue_employe, total_retenue_patronale,
                            s_amicale, s_tabaski, s_aute_cotisation,
                            retenue_cotisation, cfce, total_prime,
                            salaire_net, id_contrat
                        ) VALUES (
                            %s,%s,%s,
                            %s,%s,%s,%s,%s,%s,%s,%s,
                            %s,%s,%s,%s,%s,%s,
                            %s,%s,%s,%s,%s,
                            %s,%s,%s,
                            %s,%s,%s,%s,
                            %s,%s,
                            %s,%s,
                            %s,%s,%s,
                            %s,%s,%s,
                            %s,%s
                        )
                    """
                    cursor.executemany(query, valeurs)

                    conn.commit()

            return jsonify({"status": "updated"})

        except Exception as e:
            return jsonify({"error": str(e)}), 500

    # =====================================================
    # DELETE MOIS
    # =====================================================
    elif "delete_id" in data:

        id_periode = datetime.strptime(data.get("delete_id"), "%Y-%m")
        id_reference = encryptor("decrypt", data.get("id_reference", "").strip())
    
        with get_connection() as conn:
            with conn.cursor(dictionary=True) as cursor:
    
                cursor.execute("""
                    SELECT * FROM salaire
                    INNER JOIN contrat ON contrat.id_contrat = salaire.id_contrat
                    INNER JOIN employe ON employe.id_employe = contrat.id_employe
                    INNER JOIN reference ON reference.id_reference = employe.id_reference
                    WHERE reference.id_reference = %s
                    AND YEAR(date_du) = %s AND MONTH(date_du) = %s
                """, (id_reference, id_periode.year, id_periode.month))
    
                result = cursor.fetchall()
    
                for row in result:
                    if row.get("id_num_conge"):
                        cursor.execute("""
                            UPDATE conge_annuel
                            SET paye_conge_annuel = 0
                            WHERE id_conge_annuel = %s
                        """, (row["id_num_conge"],))
    
                    cursor.execute(
                        "DELETE FROM salaire WHERE id_salaire = %s",
                        (row["id_salaire"],)
                    )
    
                conn.commit()
    
        return jsonify({"status": "all_deleted"})

    elif "delete_id2" in data:

        id_salaire = encryptor("decrypt", data.get("delete_id2"))
    
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "DELETE FROM salaire WHERE id_salaire = %s",
                    (id_salaire,)
                )
                conn.commit()
    
        return jsonify({"status": "deleted"})
