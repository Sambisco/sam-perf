from datetime import datetime
from flask import request, jsonify
from templates.include.connect import get_connection
from templates.include.encryptor import encryptor
import logging


def save_paie_conge_annuel():

    data = request.form

    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                if "insert_id" in data:
                    date_du = f"{data['date_du']}-01"
                    id_conge_annuel = encryptor("decrypt", data["id_conge_annuel"])
                    id_contrat =  data["id_contrat"]

                    values = (
                            date_du,
                            data["date_paiement"],
                            data["mode_paie"],
                            data["s_nature"],
                            data["s_date_embauche"],
                            data["s_date_sorti"],
                            data["s_categorie"],
                            data["s_poste_occupe"],
                            data["s_situation_matr"],
                            data["s_conjoint"],
                            data["s_enfant"],
                            data["salaire_base"],
                            data["ind_fonction"],
                            data["ind_sujetion"],
                            data["ind_responsabilite"],
                            data["ind_sursalaire"],
                            data["ind_logement"],
                            data["salaire_brute"],
                            data["s_nb_trimf"],
                            data["sum_trimf"],
                            data["s_nb_irpp"],
                            data["sum_irpp"],
                            data["ind_transport"],
                            data["ind_telephone_in"],
                            data["ind_autre_indemnite"],
                            data["iprg_employe"],
                            data["irprg_patronale"],
                            data["irpc_employe"],
                            data["irpc_patronale"],
                            data["css_accident_travail"],
                            data["css_allocation_familiale"],
                            data["total_retenue_employe"],
                            data["total_retenue_patronale"],
                            data["s_amicale"],
                            data["s_tabaski"],
                            data["s_aute_cotisation"],
                            data["retenue_cotisation"],
                            data["cfce"],
                            data["total_prime"],
                            data["salaire_net"],
                            data["salaire_brute_annuel"],
                            data["ind_indemnite_conge"],
                            data["ind_indemnite_conge_supplementaire"],
                            data["date_conge_actuel"],
                            data["date_conge_precedent"],
                            data["months"],
                            data["date_debut"],
                            data["date_fin"],
                            data["nbr_conge"],
                            data["nbr_conge_supplementaire"],
                            data["formule"],
                            id_conge_annuel,
                            id_contrat,
                        )

                    query = """
                        INSERT INTO salaire (
                            date_du, date_paiement, mode_paie, s_nature, s_date_embauche, s_date_sorti, s_categorie, 
                            s_poste_occupe, s_situation_matr, s_conjoint, s_enfant, salaire_base, ind_fonction, 
                            ind_sujetion, ind_responsabilite, ind_sursalaire, ind_logement, salaire_brute, s_nb_trimf, 
                            sum_trimf, s_nb_irpp, sum_irpp, ind_transport, ind_telephone_in, ind_autre_indemnite, 
                            iprg_employe, irprg_patronale, irpc_employe, irpc_patronale, css_accident_travail, 
                            css_allocation_familiale, total_retenue_employe, total_retenue_patronale, s_amicale, s_tabaski, 
                            s_aute_cotisation, retenue_cotisation, cfce, total_prime, salaire_net, salaire_brute_annuel, 
                            ind_indemnite_conge, ind_indemnite_conge_supplementaire, date_conge_actuel, date_conge_precedent, 
                            months, date_debut, date_fin, nbr_conge, nbr_conge_supplementaire, formule, id_num_conge, id_contrat
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 
                                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 
                                %s, %s, %s, %s)
                    """

                    cursor.execute(query, values)
                    cursor.execute(
                            "UPDATE conge_annuel SET paye_conge_annuel = 1 WHERE id_conge_annuel = %s",
                            (id_conge_annuel,),
                        )
                    
                    conn.commit()  # ✅ N'oublie pas d'enregistrer
                    return jsonify({"success": True})  # ✅ Retour obligatoire

                elif "delete_id" in data:
                    id_salaire = encryptor("decrypt", data["delete_id"])
                    del_id_conge_annuel = encryptor("decrypt", data["del_id_conge_annuel"])

                    cursor.execute(
                        "DELETE FROM salaire WHERE id_salaire = %s", (id_salaire,)
                    )
                    cursor.execute(
                        "UPDATE conge_annuel SET paye_conge_annuel = 0 WHERE id_conge_annuel = %s",
                        (del_id_conge_annuel,),
                    )
                    
                    conn.commit()
                    return jsonify({"success": True})

    except Exception as e:
        logging.error(f"Erreur lors de l'enregistrement du congé annuel : {e}")
        return jsonify({"error": str(e)}), 500
