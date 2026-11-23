import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
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
    return (min(salaire_brute, 432000) * 5.6) / 100


def calcul_irpg_patronale(salaire_brute):
    return (min(salaire_brute, 432000) * 8.4) / 100


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
    return (min(salaire_brute, 63000) * 1) / 100


def calcul_css_allocation_familiale(salaire_brute):
    return (min(salaire_brute, 63000) * 7) / 100


def calcul_cfce(salaire_brute):
    return (salaire_brute * 3) / 100


def fetch_calcul_conge_annuel():
    try:
        id_conge_annuel = encryptor(
            "decrypt", request.form.get("id_conge_annuel", "").strip()
        )

        date_du_str = request.form.get("date_du", "").strip()
        date_conge_actuel_str = request.form.get("date_conge_actuel", "").strip()
        date_conge_precedent_str = request.form.get("date_conge_precedent", "").strip()

        if not date_du_str or not date_conge_actuel_str or not date_conge_precedent_str:
            return (
                jsonify(
                    {
                        "error": "Les champs date_du, date_conge_actuel et date_conge_precedent sont requis"
                    }
                ),
                400,
            )

        try:
            date_du = datetime.strptime(date_du_str, "%Y-%m").date()
            date_conge_actuel = datetime.strptime(
                date_conge_actuel_str, "%Y-%m-%d"
            ).date()
            date_conge_precedent = datetime.strptime(
                date_conge_precedent_str, "%Y-%m-%d"
            ).date()
        except ValueError as ve:
            return jsonify({"error": f"Format de date invalide: {str(ve)}"}), 400

        formule = request.form.get("formule")

        with get_connection() as conn:
            with conn.cursor(dictionary=True) as cursor:
                cursor.execute(
                    """
                    SELECT * FROM conge_annuel
                    INNER JOIN contrat ON contrat.id_contrat = conge_annuel.id_contrat
                    INNER JOIN employe ON employe.id_employe = contrat.id_employe
                    INNER JOIN reference ON reference.id_reference = employe.id_reference
                    WHERE conge_annuel.id_conge_annuel = %s
                """,
                    (id_conge_annuel,),
                )
                row = cursor.fetchone()

        if not row:
            return jsonify({"error": "Aucun congé trouvé"}), 404

        salaire = float(row["salaire"] or 0)
        fonction = float(row["fonction"] or 0)
        sujetion = float(row["sujetion"] or 0)
        responsabilite = float(row["responsabilite"] or 0)
        sursalaire = float(row["sursalaire"] or 0)
        logement = float(row["logement"] or 0)

        salaire_brute_conge = (
            salaire + fonction + sujetion + responsabilite + sursalaire + logement
        )
        salaire_brute_annuel = salaire_brute_conge * 12

        months = max(
            1,
            (date_conge_actuel.year - date_conge_precedent.year) * 12
            + (date_conge_actuel.month - date_conge_precedent.month),
        )

        nbr_conge = int(row["nbr_conge"] or 0)
        nbr_conge_supplementaire = int(row["nbr_conge_supplementaire"] or 0)
        nb_trimf = float(row["nb_trimf"] or 0)
        nb_irpp = float(row["nb_irpp"] or 0)

        if formule == "Formulemois":
            ind_indemnite_conge = (salaire_brute_annuel / months) * (
                (nbr_conge + nbr_conge_supplementaire) / 24
            )
            ind_indemnite_conge_supplementaire = 0
        else:
            salaire_brute_reference = salaire_brute_conge * months
            remboursement_frais = (
                fonction + sujetion + responsabilite + sursalaire + logement
            ) * months
            brute_conge = salaire_brute_reference - remboursement_frais
            ind_indemnite_conge = brute_conge / 12

            if nbr_conge > 0:
                ind_indemnite_conge_supplementaire = (
                    nbr_conge_supplementaire * ind_indemnite_conge
                ) / nbr_conge
            else:
                ind_indemnite_conge_supplementaire = 0

        salaire_brute = ind_indemnite_conge + ind_indemnite_conge_supplementaire

        sum_trimf = calcul_sum_trimf(salaire_brute, nb_trimf)
        sum_irpp = calcul_sum_irpp(salaire_brute, nb_irpp)

        iprg_employe = calcul_irpg_employe(salaire_brute)
        irprg_patronale = calcul_irpg_patronale(salaire_brute)
        irpc_employe = calcul_irpc_employe(salaire_brute)
        irpc_patronale = calcul_irpc_patronale(salaire_brute)
        css_accident_travail = calcul_css_accident_travail(salaire_brute)
        css_allocation_familiale = calcul_css_allocation_familiale(salaire_brute)
        cfce = calcul_cfce(salaire_brute)

        amicale = float(row.get("amicale", 0))
        tabaski = float(row.get("tabaski", 0))
        aute_cotisation = float(row.get("aute_cotisation", 0))

        total_retenue_employe = (
            iprg_employe
            + irpc_employe
            + sum_trimf
            + sum_irpp
            + amicale
            + tabaski
            + aute_cotisation
        )
        total_retenue_patronale = (
            irprg_patronale
            + irpc_patronale
            + css_accident_travail
            + css_allocation_familiale
            + cfce
        )

        salaire_net = salaire_brute - total_retenue_employe

        return jsonify(
            {
                "id_contrat": row["id_contrat"],
                "matricule": row["matricule"],
                "prenom": row["prenom"],
                "nom": row["nom"],
                "nature": row["nature"],
                "categorie": row["categorie"],
                "poste_occupe": row["poste_occupe"],
                "situation_matr": row["situation_matr"],
                "conjoint": row["conjoint"],
                "enfant": row["enfant"],
                "salaire": salaire,
                "fonction": fonction,
                "sujetion": sujetion,
                "responsabilite": responsabilite,
                "sursalaire": sursalaire,
                "logement": logement,
                "salaire_brute": salaire_brute,
                "salaire_brute_annuel": salaire_brute_annuel,
                "ind_indemnite_conge": ind_indemnite_conge,
                "ind_indemnite_conge_supplementaire": ind_indemnite_conge_supplementaire,
                "nb_trimf": nb_trimf,
                "sum_trimf": sum_trimf,
                "nb_irpp": nb_irpp,
                "sum_irpp": sum_irpp,
                "iprg_employe": iprg_employe,
                "irprg_patronale": irprg_patronale,
                "irpc_employe": irpc_employe,
                "irpc_patronale": irpc_patronale,
                "css_accident_travail": css_accident_travail,
                "css_allocation_familiale": css_allocation_familiale,
                "cfce": cfce,
                "amicale": amicale,
                "tabaski": tabaski,
                "aute_cotisation": aute_cotisation,
                "total_retenue_employe": total_retenue_employe,
                "total_retenue_patronale": total_retenue_patronale,
                "salaire_net": salaire_net,
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
                "date_debut": (
                    row["date_suspension"].strftime("%Y-%m-%d")
                    if row.get("date_suspension")
                    else None
                ),
                "date_fin": (
                    row["date_fin"].strftime("%Y-%m-%d")
                    if row.get("date_fin")
                    else None
                ),
                "months": months,
                "nbr_conge": nbr_conge,
                "nbr_conge_supplementaire": nbr_conge_supplementaire,
            }
        )

    except Exception as e:
        logging.exception("Erreur lors du calcul de l'indemnité de congé")
        return jsonify({"error": str(e)}), 500
