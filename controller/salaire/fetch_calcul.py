import logging
from flask import request, jsonify
from datetime import datetime, date
from templates.include.connect import get_connection
from templates.include.encryptor import encryptor
from controller.bareme_irpp.bareme_irpp_1 import bareme_1
from controller.bareme_irpp.bareme_irpp_1_5 import bareme_1_5
from controller.bareme_irpp.bareme_irpp_2 import bareme_2
from controller.bareme_irpp.bareme_irpp_2_5 import bareme_2_5
from controller.bareme_irpp.bareme_irpp_3 import bareme_3
from controller.bareme_irpp.bareme_irpp_3_5 import bareme_3_5
from controller.bareme_irpp.bareme_irpp_4 import bareme_4
from controller.bareme_irpp.bareme_irpp_4_5 import bareme_4_5
from controller.bareme_irpp.bareme_irpp_5 import bareme_5


def month_year(date_val):
    if not date_val:
        return None
    if isinstance(date_val, str):
        dt = datetime.strptime(date_val, "%Y-%m-%d")
    elif isinstance(date_val, date):
        dt = datetime.combine(date_val, datetime.min.time())
    else:
        return None
    return dt.strftime("%Y-%m")


def calcul_sum_trimf(salaire_brute, nb_trimf):
    if not nb_trimf:
        return 0
    if 50000 <= salaire_brute < 84000:
        return 300 * nb_trimf
    elif 84000 <= salaire_brute < 167000:
        return 400 * nb_trimf
    elif 167000 <= salaire_brute < 1000000:
        return 500 * nb_trimf
    elif 1000000 <= salaire_brute <= 5000000:
        return 1500 * nb_trimf
    return 0


def calcul_sum_irpp(salaire_brute, nb_irpp):
    baremes = {
        1: bareme_1,
        1.5: bareme_1_5,
        2: bareme_2,
        2.5: bareme_2_5,
        3: bareme_3,
        3.5: bareme_3_5,
        4: bareme_4,
        4.5: bareme_4_5,
        5: bareme_5,
    }
    tranches = baremes.get(nb_irpp)
    if not tranches:
        return 0
    for debut, fin, montant in tranches:
        if debut <= salaire_brute < fin:
            return montant
    return 0


def calcul_irpg_employe(salaire_brute):
    base = min(salaire_brute, 432000)
    return (base * 5.6) / 100


def calcul_irpg_patronale(salaire_brute):
    base = min(salaire_brute, 432000)
    return (base * 8.4) / 100


def calcul_irpc_employe(salaire_brute):
    if salaire_brute < 432000:
        return 0
    elif salaire_brute < 1296000:
        return (salaire_brute * 2.4) / 100
    else:
        return (1296000 * 2.4) / 100


def calcul_irpc_patronale(salaire_brute):
    if salaire_brute < 432000:
        return 0
    elif salaire_brute < 1296000:
        return (salaire_brute * 3.6) / 100
    else:
        return (1296000 * 3.6) / 100


def calcul_css_accident_travail(salaire_brute):
    base = min(salaire_brute, 63000)
    return (base * 1) / 100


def calcul_css_allocation_familiale(salaire_brute):
    base = min(salaire_brute, 63000)
    return (base * 7) / 100


def calcul_cfce(salaire_brute):
    return (salaire_brute * 3) / 100


def fetch_calcul():
    try:
        logging.debug(f"POST form data: {request.form}")

        id_reference_enc = request.form.get("id_reference", "")
        date_du_str = request.form.get("date_du", "")

        if not id_reference_enc or not date_du_str:
            return jsonify({"error": "Données manquantes"}), 400

        # Déchiffrement id_reference
        id_reference = encryptor("decrypt", id_reference_enc).strip()

        # Conversion date_du en datetime (année-mois)
        try:
            date_du = datetime.strptime(date_du_str, "%Y-%m")
        except ValueError:
            return jsonify({"error": "Format de date invalide, attendu YYYY-MM"}), 400

        conn = get_connection()
        data = []

        with conn:
            with conn.cursor(dictionary=True) as cursor:
                cursor.execute(
                    """
                    SELECT contrat.*, employe.*, reference.*
                    FROM contrat
                    JOIN employe ON employe.id_employe = contrat.id_employe
                    JOIN reference ON reference.id_reference = employe.id_reference
                    WHERE reference.id_reference = %s
                    ORDER BY contrat.id_contrat DESC
                """,
                    (id_reference,),
                )
                contrats = cursor.fetchall()

                for row in contrats:
                    # date_embauche est déjà un date (MySQL DATE)
                    date_embauche = row.get("date_embauche")
                    if date_embauche and isinstance(date_embauche, str):
                        date_embauche = datetime.strptime(
                            date_embauche, "%Y-%m-%d"
                        ).date()

                    if date_embauche and date_embauche > date.today():
                        continue  # Embauche dans le futur, on ignore ce contrat

                    id_contrat = row["id_contrat"]

                    # Heures pointées et nombre jours

                    cursor.execute(
                        """
                        SELECT
                            SUM(hour(timediff(heure_fin,heure_debut))) AS heure,
                            COUNT(pointage.id_contrat) AS nbr_jours
                        FROM pointage
                        WHERE pointage.id_contrat = %s
                        AND YEAR(pointage.date) = %s AND MONTH(pointage.date) = %s
                        """,
                        (id_contrat, date_du.year, date_du.month),
                    )

                    result_pointage = cursor.fetchone()
                    print("Résultat pointage:", result_pointage)
                    heure_pointage = result_pointage["heure"] or 0
                    nbr_jours = result_pointage["nbr_jours"] or 0
                    total_heure_mois = heure_pointage * 4  # approximatif

                    # Vérification départ (suspension salaire)
                    cursor.execute(
                        """
                        SELECT depart.*
                        FROM depart
                        INNER JOIN contrat ON contrat.id_contrat = depart.id_contrat
                        INNER JOIN employe ON employe.id_employe = contrat.id_employe
                        INNER JOIN reference ON reference.id_reference = employe.id_reference
                        WHERE contrat.id_contrat = %s AND reference.id_reference = %s
                        ORDER BY contrat.id_contrat DESC LIMIT 1
                        """,
                        (id_contrat, id_reference),
                    )
                    depart = cursor.fetchone()

                    suspensalaire = depart.get("suspensalaire") if depart else None
                    date_effet_depart = depart.get("date_effet") if depart else None

                    # Ici on n'a PAS besoin de parser date_effet_depart, c'est déjà un date
                    if (
                        date_effet_depart
                        and suspensalaire == "Oui"
                        and date_du.date() >= date_effet_depart
                    ):
                        continue  # Contrat suspendu ce mois

                    # Congé annuel
                    cursor.execute(
                        """
                        SELECT conge_annuel.*
                        FROM conge_annuel
                        INNER JOIN contrat ON contrat.id_contrat = conge_annuel.id_contrat
                        INNER JOIN employe ON employe.id_employe = contrat.id_employe
                        INNER JOIN reference ON reference.id_reference = employe.id_reference
                        WHERE contrat.id_contrat = %s
                        ORDER BY conge_annuel.id_conge_annuel DESC
                        LIMIT 1
                        """,
                        (id_contrat,),
                    )
                    conge_annuel = cursor.fetchone()

                    # Congé maternité
                    cursor.execute(
                        """
                        SELECT conge_maternite.*
                        FROM conge_maternite
                        INNER JOIN contrat ON contrat.id_contrat = conge_maternite.id_contrat
                        INNER JOIN employe ON employe.id_employe = contrat.id_employe
                        INNER JOIN reference ON reference.id_reference = employe.id_reference
                        WHERE contrat.id_contrat = %s
                        ORDER BY conge_maternite.id_conge_maternite DESC
                        LIMIT 1
                        """,
                        (id_contrat,),
                    )
                    conge_maternite = cursor.fetchone()

                    conge_annuel_debut = month_year(
                        conge_annuel.get("date_debut") if conge_annuel else None
                    )
                    conge_annuel_fin = month_year(
                        conge_annuel.get("date_fin") if conge_annuel else None
                    )
                    cong_mat_debut = month_year(
                        conge_maternite.get("date_suspension")
                        if conge_maternite
                        else None
                    )
                    cong_mat_fin = month_year(
                        conge_maternite.get("date_fin") if conge_maternite else None
                    )

                    date_du_str = date_du.strftime("%Y-%m")

                    if (
                        conge_annuel_debut
                        and conge_annuel_fin
                        and conge_annuel_debut <= date_du_str <= conge_annuel_fin
                    ) or (
                        cong_mat_debut
                        and cong_mat_fin
                        and cong_mat_debut <= date_du_str <= cong_mat_fin
                    ):
                        continue  # Congé ce mois, on ignore

                    # Calculs salaires / cotisations
                    salaire = float(row.get("salaire") or 0)
                    fonction = float(row.get("fonction") or 0)
                    sujetion = float(row.get("sujetion") or 0)
                    responsabilite = float(row.get("responsabilite") or 0)
                    sursalaire = float(row.get("sursalaire") or 0)
                    logement = float(row.get("logement") or 0)

                    salaire_brute = (
                        salaire
                        + fonction
                        + sujetion
                        + responsabilite
                        + sursalaire
                        + logement
                    )

                    nb_trimf = int(row.get("nb_trimf") or 0)
                    nb_irpp = float(row.get("nb_irpp") or 0)

                    sum_trimf = calcul_sum_trimf(salaire_brute, nb_trimf)
                    sum_irpp = calcul_sum_irpp(salaire_brute, nb_irpp)
                    iprg_employe = calcul_irpg_employe(salaire_brute)
                    irprg_patronale = calcul_irpg_patronale(salaire_brute)
                    irpc_employe = calcul_irpc_employe(salaire_brute)
                    irpc_patronale = calcul_irpc_patronale(salaire_brute)
                    css_accident_travail = calcul_css_accident_travail(salaire_brute)
                    css_allocation_familiale = calcul_css_allocation_familiale(
                        salaire_brute
                    )
                    cfce = calcul_cfce(salaire_brute)

                    total_retenue_employe = (
                        iprg_employe
                        + irpc_employe
                        + sum_trimf
                        + sum_irpp
                        + float(row.get("amicale") or 0)
                        + float(row.get("tabaski") or 0)
                        + float(row.get("aute_cotisation") or 0)
                    )

                    total_retenue_patronale = (
                        irprg_patronale
                        + irpc_patronale
                        + css_accident_travail
                        + css_allocation_familiale
                        + cfce
                    )

                    retenue_cotisation = salaire_brute - total_retenue_employe

                    total_prime = (
                        float(row.get("transport") or 0)
                        + float(row.get("telephone_in") or 0)
                        + float(row.get("autre_indemnite") or 0)
                    )

                    salaire_net = retenue_cotisation + total_prime

                    acronym_prenom = "".join(
                        [mot[0] for mot in row["prenom"].split() if mot]
                    )
                    acronym_nom = "".join([mot[0] for mot in row["nom"].split() if mot])

                    data.append(
                        {
                            "id_contrat": row["id_contrat"],
                            "matricule": row["matricule"],
                            "prenom": row["prenom"],
                            "nom": row["nom"],
                            "nature": row["nature"],
                            "date_embauche": (
                                row["date_embauche"].strftime("%Y-%m-%d")
                                if row.get("date_embauche")
                                else ""
                            ),
                            "date_sorti": (
                                row["date_sorti"].strftime("%Y-%m-%d")
                                if row.get("date_sorti")
                                else ""
                            ),
                            "categorie": row["categorie"],
                            "poste_occupe": row["poste_occupe"],
                            "situation_matr": row["situation_matr"],
                            "conjoint": row["conjoint"],
                            "enfant": row["enfant"],
                            "nbr_jours": nbr_jours,
                            "total_heure_mois": total_heure_mois,
                            "heure_pointage": heure_pointage,
                            "salaire": salaire,
                            "fonction": fonction,
                            "sujetion": sujetion,
                            "responsabilite": responsabilite,
                            "sursalaire": sursalaire,
                            "logement": logement,
                            "salaire_brute": salaire_brute,
                            "nb_trimf": nb_trimf,
                            "sum_trimf": sum_trimf,
                            "nb_irpp": nb_irpp,
                            "sum_irpp": sum_irpp,
                            "transport": row["transport"],
                            "telephone_in": row["telephone_in"],
                            "autre_indemnite": row["autre_indemnite"],
                            "iprg_employe": iprg_employe,
                            "irprg_patronale": irprg_patronale,
                            "irpc_employe": irpc_employe,
                            "irpc_patronale": irpc_patronale,
                            "css_accident_travail": css_accident_travail,
                            "css_allocation_familiale": css_allocation_familiale,
                            "total_retenue_employe": total_retenue_employe,
                            "total_retenue_patronale": total_retenue_patronale,
                            "amicale": row["amicale"],
                            "tabaski": row["tabaski"],
                            "aute_cotisation": row["aute_cotisation"],
                            "retenue_cotisation": retenue_cotisation,
                            "cfce": cfce,
                            "total_prime": total_prime,
                            "salaire_net": salaire_net,
                            # ajoute ici les autres champs nécessaires
                        }
                    )

        return jsonify(data)

    except Exception as e:
        logging.exception("Erreur dans fetch_calcul")
        return jsonify({"error": str(e)}), 500
