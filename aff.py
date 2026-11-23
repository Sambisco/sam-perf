from datetime import datetime, date
from flask import request, jsonify
from templates.include.connect import get_connection
from templates.include.encryptor import encryptor
import logging


def save_salaire():
    if "insert_id" in request.form:
        data = request.form

        # Récupération des listes depuis le formulaire
        s_natures = request.form.getlist("s_nature")
        s_date_embauches = request.form.getlist("s_date_embauche")
        s_date_sortis = request.form.getlist("s_date_sorti")
        s_categories = request.form.getlist("s_categorie")
        s_poste_occupes = request.form.getlist("s_poste_occupe")
        s_situation_matrs = request.form.getlist("s_situation_matr")
        s_conjoints = request.form.getlist("s_conjoint")
        s_enfants = request.form.getlist("s_enfant")
        salaire_bases = request.form.getlist("salaire_base")
        ind_fonctions = request.form.getlist("ind_fonction")
        ind_sujetions = request.form.getlist("ind_sujetion")
        ind_responsabilites = request.form.getlist("ind_responsabilite")
        ind_sursalaires = request.form.getlist("ind_sursalaire")
        ind_logements = request.form.getlist("ind_logement")
        salaire_brutes = request.form.getlist("salaire_brute")
        s_nb_trimfs = request.form.getlist("s_nb_trimf")
        sum_trimfs = request.form.getlist("sum_trimf")
        s_nb_irpps = request.form.getlist("s_nb_irpp")
        sum_irpps = request.form.getlist("sum_irpp")
        ind_transports = request.form.getlist("ind_transport")
        ind_telephone_ins = request.form.getlist("ind_telephone_in")
        ind_autre_indemnites = request.form.getlist("ind_autre_indemnite")
        iprg_employes = request.form.getlist("iprg_employe")
        irprg_patronales = request.form.getlist("irprg_patronale")
        irpc_employes = request.form.getlist("irpc_employe")
        irpc_patronales = request.form.getlist("irpc_patronale")
        css_accident_travails = request.form.getlist("css_accident_travail")
        css_allocation_familiales = request.form.getlist("css_allocation_familiale")
        total_retenue_employes = request.form.getlist("total_retenue_employe")
        total_retenue_patronales = request.form.getlist("total_retenue_patronale")
        s_amicales = request.form.getlist("s_amicale")
        s_tabaskis = request.form.getlist("s_tabaski")
        s_aute_cotisations = request.form.getlist("s_aute_cotisation")
        retenue_cotisations = request.form.getlist("retenue_cotisation")
        cfces = request.form.getlist("cfce")
        total_primes = request.form.getlist("total_prime")
        salaire_nets = request.form.getlist("salaire_net")
        id_contrats = request.form.getlist("id_contrat")

        # Vérification de la cohérence des longueurs
        lengths = list(
            map(
                len,
                [
                    s_natures,
                    s_date_embauches,
                    s_date_sortis,
                    s_categories,
                    s_poste_occupes,
                    s_situation_matrs,
                    s_conjoints,
                    s_enfants,
                    salaire_bases,
                    ind_fonctions,
                    ind_sujetions,
                    ind_responsabilites,
                    ind_sursalaires,
                    ind_logements,
                    salaire_brutes,
                    s_nb_trimfs,
                    sum_trimfs,
                    s_nb_irpps,
                    sum_irpps,
                    ind_transports,
                    ind_telephone_ins,
                    ind_autre_indemnites,
                    iprg_employes,
                    irprg_patronales,
                    irpc_employes,
                    irpc_patronales,
                    css_accident_travails,
                    css_allocation_familiales,
                    total_retenue_employes,
                    total_retenue_patronales,
                    s_amicales,
                    s_tabaskis,
                    s_aute_cotisations,
                    retenue_cotisations,
                    cfces,
                    total_primes,
                    salaire_nets,
                    id_contrats,
                ],
            )
        )

        if len(set(lengths)) != 1:
            error_msg = f"Listes de longueurs différentes : {lengths}"
            print(error_msg)
            return jsonify({"error": error_msg}), 400

        date_du = data.get("date_du").strip() + "-01"
        date_paiement = data.get("date_paiement").strip()
        mode_paie = data.get("mode_paie")

        valeurs_validees = []

        with get_connection() as conn:
            with conn.cursor() as cursor:
                for i in range(lengths[0]):
                    ligne = [
                        date_du,
                        date_paiement,
                        mode_paie,
                        s_natures[i].strip(),
                        s_date_embauches[i].strip(),
                        s_date_sortis[i].strip(),
                        s_categories[i].strip(),
                        s_poste_occupes[i].strip(),
                        s_situation_matrs[i].strip(),
                        s_conjoints[i].strip(),
                        s_enfants[i].strip(),
                        salaire_bases[i].strip(),
                        ind_fonctions[i].strip(),
                        ind_sujetions[i].strip(),
                        ind_responsabilites[i].strip(),
                        ind_sursalaires[i].strip(),
                        ind_logements[i].strip(),
                        salaire_brutes[i].strip(),
                        s_nb_trimfs[i].strip(),
                        sum_trimfs[i].strip(),
                        s_nb_irpps[i].strip(),
                        sum_irpps[i].strip(),
                        ind_transports[i].strip(),
                        ind_telephone_ins[i].strip(),
                        ind_autre_indemnites[i].strip(),
                        iprg_employes[i].strip(),
                        irprg_patronales[i].strip(),
                        irpc_employes[i].strip(),
                        irpc_patronales[i].strip(),
                        css_accident_travails[i].strip(),
                        css_allocation_familiales[i].strip(),
                        total_retenue_employes[i].strip(),
                        total_retenue_patronales[i].strip(),
                        s_amicales[i].strip(),
                        s_tabaskis[i].strip(),
                        s_aute_cotisations[i].strip(),
                        retenue_cotisations[i].strip(),
                        cfces[i].strip(),
                        total_primes[i].strip(),
                        salaire_nets[i].strip(),
                        id_contrats[i].strip(),
                    ]

                    if len(ligne) != 41:
                        return (
                            jsonify(
                                {
                                    "error": f"Ligne invalide : {len(ligne)} valeurs au lieu de 43",
                                    "ligne": ligne,
                                }
                            ),
                            400,
                        )

                    valeurs_validees.append(tuple(ligne))

                if valeurs_validees:
                    try:
                        query = """
                            INSERT INTO salaire(
                                date_du, date_paiement, mode_paie, s_nature, s_date_embauche, s_date_sorti,
                                s_categorie, s_poste_occupe, s_situation_matr, s_conjoint, s_enfant, salaire_base,
                                ind_fonction, ind_sujetion, ind_responsabilite, ind_sursalaire, ind_logement,
                                salaire_brute, s_nb_trimf, sum_trimf, s_nb_irpp, sum_irpp, ind_transport,
                                ind_telephone_in, ind_autre_indemnite, iprg_employe, irprg_patronale,
                                irpc_employe, irpc_patronale, css_accident_travail, css_allocation_familiale,
                                total_retenue_employe, total_retenue_patronale, s_amicale, s_tabaski,
                                s_aute_cotisation, retenue_cotisation, cfce, total_prime, salaire_net, id_contrat
                            ) VALUES (
                                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                                %s, %s, %s, %s, %s, %s, %s, %s
                            )
                        """
                        cursor.executemany(query, valeurs_validees)

                        cursor.execute("""
                            DELETE t1 FROM salaire t1
                            INNER JOIN salaire t2
                            WHERE t1.id_salaire < t2.id_salaire
                            AND t1.id_contrat = t2.id_contrat
                            AND t1.date_du = t2.date_du
                        """)

                        conn.commit()
                        return jsonify(
                            {
                                "status": "success",
                                "message": f"{len(valeurs_validees)} salaires insérés avec succès.",
                            }
                        )
                    except Exception as e:
                        conn.rollback()
                        return jsonify({"error": f"Erreur insertion: {str(e)}"}), 500

    elif "edit_id" in request.form:

        data = request.form
        id_mois = datetime.strptime(data.get("edit_id"), "%Y-%m")
        date_du = data.get("date_du").strip() + "-01"
        date_paiement = data.get("date_paiement").strip()
        mode_paie = data.get("mode_paie")

        # Récupération des listes depuis le formulaire
        s_natures = request.form.getlist("s_nature")
        s_date_embauches = request.form.getlist("s_date_embauche")
        s_date_sortis = request.form.getlist("s_date_sorti")
        s_categories = request.form.getlist("s_categorie")
        s_poste_occupes = request.form.getlist("s_poste_occupe")
        s_situation_matrs = request.form.getlist("s_situation_matr")
        s_conjoints = request.form.getlist("s_conjoint")
        s_enfants = request.form.getlist("s_enfant")
        salaire_bases = request.form.getlist("salaire_base")
        ind_fonctions = request.form.getlist("ind_fonction")
        ind_sujetions = request.form.getlist("ind_sujetion")
        ind_responsabilites = request.form.getlist("ind_responsabilite")
        ind_sursalaires = request.form.getlist("ind_sursalaire")
        ind_logements = request.form.getlist("ind_logement")
        salaire_brutes = request.form.getlist("salaire_brute")
        s_nb_trimfs = request.form.getlist("s_nb_trimf")
        sum_trimfs = request.form.getlist("sum_trimf")
        s_nb_irpps = request.form.getlist("s_nb_irpp")
        sum_irpps = request.form.getlist("sum_irpp")
        ind_transports = request.form.getlist("ind_transport")
        ind_telephone_ins = request.form.getlist("ind_telephone_in")
        ind_autre_indemnites = request.form.getlist("ind_autre_indemnite")
        iprg_employes = request.form.getlist("iprg_employe")
        irprg_patronales = request.form.getlist("irprg_patronale")
        irpc_employes = request.form.getlist("irpc_employe")
        irpc_patronales = request.form.getlist("irpc_patronale")
        css_accident_travails = request.form.getlist("css_accident_travail")
        css_allocation_familiales = request.form.getlist("css_allocation_familiale")
        total_retenue_employes = request.form.getlist("total_retenue_employe")
        total_retenue_patronales = request.form.getlist("total_retenue_patronale")
        s_amicales = request.form.getlist("s_amicale")
        s_tabaskis = request.form.getlist("s_tabaski")
        s_aute_cotisations = request.form.getlist("s_aute_cotisation")
        retenue_cotisations = request.form.getlist("retenue_cotisation")
        cfces = request.form.getlist("cfce")
        total_primes = request.form.getlist("total_prime")
        salaire_nets = request.form.getlist("salaire_net")
        id_contrats = request.form.getlist("id_contrat")

        # Vérification de la cohérence des longueurs
        lengths = list(
            map(
                len,
                [
                    s_natures,
                    s_date_embauches,
                    s_date_sortis,
                    s_categories,
                    s_poste_occupes,
                    s_situation_matrs,
                    s_conjoints,
                    s_enfants,
                    salaire_bases,
                    ind_fonctions,
                    ind_sujetions,
                    ind_responsabilites,
                    ind_sursalaires,
                    ind_logements,
                    salaire_brutes,
                    s_nb_trimfs,
                    sum_trimfs,
                    s_nb_irpps,
                    sum_irpps,
                    ind_transports,
                    ind_telephone_ins,
                    ind_autre_indemnites,
                    iprg_employes,
                    irprg_patronales,
                    irpc_employes,
                    irpc_patronales,
                    css_accident_travails,
                    css_allocation_familiales,
                    total_retenue_employes,
                    total_retenue_patronales,
                    s_amicales,
                    s_tabaskis,
                    s_aute_cotisations,
                    retenue_cotisations,
                    cfces,
                    total_primes,
                    salaire_nets,
                    id_contrats,
                ],
            )
        )

        if len(set(lengths)) != 1:
            error_msg = f"Listes de longueurs différentes : {lengths}"
            print(error_msg)
            return jsonify({"error": error_msg}), 400

        valeurs_validees = []

        with get_connection() as conn:
            with conn.cursor() as cursor:
                for i in range(lengths[0]):
                    ligne = [
                        date_du,
                        date_paiement,
                        mode_paie,
                        s_natures[i].strip(),
                        s_date_embauches[i].strip(),
                        s_date_sortis[i].strip(),
                        s_categories[i].strip(),
                        s_poste_occupes[i].strip(),
                        s_situation_matrs[i].strip(),
                        s_conjoints[i].strip(),
                        s_enfants[i].strip(),
                        salaire_bases[i].strip(),
                        ind_fonctions[i].strip(),
                        ind_sujetions[i].strip(),
                        ind_responsabilites[i].strip(),
                        ind_sursalaires[i].strip(),
                        ind_logements[i].strip(),
                        salaire_brutes[i].strip(),
                        s_nb_trimfs[i].strip(),
                        sum_trimfs[i].strip(),
                        s_nb_irpps[i].strip(),
                        sum_irpps[i].strip(),
                        ind_transports[i].strip(),
                        ind_telephone_ins[i].strip(),
                        ind_autre_indemnites[i].strip(),
                        iprg_employes[i].strip(),
                        irprg_patronales[i].strip(),
                        irpc_employes[i].strip(),
                        irpc_patronales[i].strip(),
                        css_accident_travails[i].strip(),
                        css_allocation_familiales[i].strip(),
                        total_retenue_employes[i].strip(),
                        total_retenue_patronales[i].strip(),
                        s_amicales[i].strip(),
                        s_tabaskis[i].strip(),
                        s_aute_cotisations[i].strip(),
                        retenue_cotisations[i].strip(),
                        cfces[i].strip(),
                        total_primes[i].strip(),
                        salaire_nets[i].strip(),
                        id_contrats[i].strip(),
                    ]

                    if len(ligne) != 41:
                        return (
                            jsonify(
                                {
                                    "error": f"Ligne invalide : {len(ligne)} valeurs au lieu de 43",
                                    "ligne": ligne,
                                }
                            ),
                            400,
                        )

                    valeurs_validees.append(tuple(ligne))

                    cursor.execute(
                        "DELETE FROM salaire WHERE YEAR(date_du) = %s AND  MONTH(date_du) = %s",
                        (id_mois.year, id_mois.month),
                    )

                if valeurs_validees:
                    try:
                        query = """
                            INSERT INTO salaire(
                                date_du, date_paiement, mode_paie, s_nature, s_date_embauche, s_date_sorti,
                                s_categorie, s_poste_occupe, s_situation_matr, s_conjoint, s_enfant, salaire_base,
                                ind_fonction, ind_sujetion, ind_responsabilite, ind_sursalaire, ind_logement,
                                salaire_brute, s_nb_trimf, sum_trimf, s_nb_irpp, sum_irpp, ind_transport,
                                ind_telephone_in, ind_autre_indemnite, iprg_employe, irprg_patronale,
                                irpc_employe, irpc_patronale, css_accident_travail, css_allocation_familiale,
                                total_retenue_employe, total_retenue_patronale, s_amicale, s_tabaski,
                                s_aute_cotisation, retenue_cotisation, cfce, total_prime, salaire_net, id_contrat
                            ) VALUES (
                                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                                %s, %s, %s, %s, %s, %s, %s, %s
                            )
                        """
                        cursor.executemany(query, valeurs_validees)

                        cursor.execute("""
                            DELETE t1 FROM salaire t1
                            INNER JOIN salaire t2
                            WHERE t1.id_salaire < t2.id_salaire
                            AND t1.id_contrat = t2.id_contrat
                            AND t1.date_du = t2.date_du
                        """)

                        conn.commit()
                        return jsonify(
                            {
                                "status": "success",
                                "message": f"{len(valeurs_validees)} salaires insérés avec succès.",
                            }
                        )
                    except Exception as e:
                        conn.rollback()
                        return jsonify({"error": f"Erreur insertion: {str(e)}"}), 500

    elif "delete_id" in request.form:
        with get_connection() as conn:
            with conn.cursor(dictionary=True) as cursor:
                id_periode = datetime.strptime(request.form.get("delete_id"), "%Y-%m")
                id_reference = encryptor(
                    "decrypt", request.form["id_reference"].strip()
                )

                cursor.execute(
                    """
                    SELECT * FROM salaire
                    INNER JOIN contrat ON contrat.id_contrat = salaire.id_contrat
                    INNER JOIN employe ON employe.id_employe = contrat.id_employe
                    INNER JOIN reference ON reference.id_reference = employe.id_reference
                    WHERE reference.id_reference = %s
                    AND YEAR(date_du) = %s AND MONTH(date_du) = %s
                    """,
                    (id_reference, id_periode.year, id_periode.month),
                )
                result = cursor.fetchall()

                for row in result:
                    if row.get("id_num_conge"):
                        cursor.execute(
                            "UPDATE conge_annuel SET paye_conge_annuel = 0 WHERE id_conge_annuel = %s",
                            (row["id_num_conge"],),
                        )
                    cursor.execute(
                        "DELETE FROM salaire WHERE id_salaire = %s",
                        (row["id_salaire"],),
                    )

                conn.commit()
                return jsonify({"status": "all_deleted"})

    elif "delete_id2" in request.form:
        with get_connection() as conn:
            with conn.cursor(dictionary=True) as cursor:

                id_salaire = encryptor("decrypt", request.form["delete_id2"].strip())
                cursor.execute(
                    "DELETE FROM salaire WHERE id_salaire = %s", (id_salaire,)
                )
                conn.commit()
                return jsonify({"status": "deleted"})

    else:

        return jsonify({"message": "Aucune donnée supprimée."})
