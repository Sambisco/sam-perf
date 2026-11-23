import re
import logging
from flask import request, jsonify
from datetime import datetime
from templates.include.connect import get_connection
from templates.include.encryptor import encryptor


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


# Exemple de barèmes IRPP, adapte selon tes fichiers d'origine
bareme_1 = [
    (0, 50000, 0),
    (50000, 100000, 1000),
    (100000, 150000, 2000),
    # ... ajoute ici toutes les tranches selon ton barème réel
]
# Tu dois définir les autres baremes_1_5, bareme_2, ... ou les importer si tu veux.


def calcul_sum_irpp(salaire_brute, nb_irpp):
    # Ici, comme tu n'as pas donné tous les baremes, je fais un exemple minimal.
    # À remplacer par l'import ou la définition complète comme dans ton fetch_indemnite_conge.py
    baremes = {
        1: bareme_1,
        # 1.5: bareme_1_5,
        # 2: bareme_2,
        # etc...
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


def acronym_simple(name: str) -> str:
    # Supprime les apostrophes isolées et crée un acronyme des initiales
    name_clean = re.sub(r"[\'`‘’]", "", name)
    parts = name_clean.split()
    return "".join(p[0] for p in parts if p)


def fetch_calcul_conge_maternite():
    try:
        id_conge_maternite_enc = request.form.get("id_conge_maternite", "").strip()
        date_du_str = request.form.get("date_du", "")
        if not id_conge_maternite_enc or not date_du_str:
            return jsonify({"error": "Données manquantes"}), 400

        id_conge_maternite = encryptor("decrypt", id_conge_maternite_enc)
        date_du = datetime.strptime(date_du_str, "%Y-%m").date()

        with get_connection() as conn:
            with conn.cursor(dictionary=True) as cursor:
                cursor.execute(
                    """
                    SELECT * FROM conge_maternite
                    INNER JOIN contrat ON contrat.id_contrat = conge_maternite.id_contrat
                    INNER JOIN employe ON employe.id_employe = contrat.id_employe
                    INNER JOIN reference ON reference.id_reference = employe.id_reference
                    WHERE conge_maternite.id_conge_maternite = %s
                """,
                    (id_conge_maternite,),
                )
                row = cursor.fetchone()

                if not row:
                    return jsonify({"error": "Aucun congé trouvé"}), 404

                acronym_prenom = acronym_simple(row["prenom"])
                acronym_nom = acronym_simple(row["nom"])

                id_contrat = row["id_contrat"]

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

                pointage = cursor.fetchone()
                heure_pointage = (
                    float(pointage["heure"])
                    if pointage and pointage["heure"] is not None
                    else 0
                )

                amicale = float(row.get("amicale", 0) or 0)
                tabaski = float(row.get("tabaski", 0) or 0)
                aute_cotisation = float(row.get("aute_cotisation", 0) or 0)
                transport = 0
                telephone_in = 0
                autre_indemnite = 0
                total_heure_mois = float(row.get("heure", 0) or 0) * 4

                date_debut = row.get("date_suspension")
                date_fin = row.get("date_fin")

                def prorata(val):
                    return (
                        (float(val or 0) * heure_pointage) / total_heure_mois
                        if total_heure_mois
                        else 0
                    )

                salaire = prorata(row.get("salaire"))
                fonction = prorata(row.get("fonction"))
                sujetion = prorata(row.get("sujetion"))
                responsabilite = prorata(row.get("responsabilite"))
                sursalaire = prorata(row.get("sursalaire"))
                logement = prorata(row.get("logement"))

                salaire_brute = round(
                    salaire
                    + fonction
                    + sujetion
                    + responsabilite
                    + sursalaire
                    + logement
                )

                nb_trimf = float(row.get("nb_trimf", 0) or 0)
                nb_irpp = float(row.get("nb_irpp", 0) or 0)

                iprg_employe = calcul_irpg_employe(salaire_brute)
                irprg_patronale = calcul_irpg_patronale(salaire_brute)
                irpc_employe = calcul_irpc_employe(salaire_brute)
                irpc_patronale = calcul_irpc_patronale(salaire_brute)
                css_accident_travail = calcul_css_accident_travail(salaire_brute)
                css_allocation_familiale = calcul_css_allocation_familiale(
                    salaire_brute
                )
                cfce = calcul_cfce(salaire_brute)

                sum_trimf = calcul_sum_trimf(salaire_brute, nb_trimf)
                sum_irpp = calcul_sum_irpp(salaire_brute, nb_irpp)

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

                retenue_cotisation = salaire_brute - total_retenue_employe
                total_prime = transport + telephone_in + autre_indemnite
                salaire_net = retenue_cotisation + total_prime

                date_debut_str = (
                    date_debut.strftime("%Y-%m-%d") if date_debut else None
                )
                date_fin_str = date_fin.strftime("%Y-%m-%d") if date_fin else None

                data = {
                    "id_contrat": row["id_contrat"],
                    "matricule": row["matricule"],
                    "prenom": row["prenom"],
                    "nom": row["nom"],
                    "nature": row.get("nature"),
                    "date_embauche": (
                        row.get("date_embauche").strftime("%Y-%m-%d")
                        if row.get("date_embauche")
                        else None
                    ),
                    "date_sorti": (
                        row.get("date_sorti").strftime("%Y-%m-%d")
                        if row.get("date_sorti")
                        else None
                    ),
                    "categorie": row.get("categorie"),
                    "poste_occupe": row.get("poste_occupe"),
                    "situation_matr": row.get("situation_matr"),
                    "conjoint": row.get("conjoint"),
                    "enfant": row.get("enfant"),
                    "total_heure_mois": total_heure_mois,
                    "heure_pointage": heure_pointage,
                    "salaire": salaire,
                    "fonction": fonction,
                    "sujetion": sujetion,
                    "responsabilite": responsabilite,
                    "sursalaire": sursalaire,
                    "logement": logement,
                    "salaire_brute": salaire_brute,
                    "nbr_conge": "",
                    "nb_trimf": nb_trimf,
                    "sum_trimf": sum_trimf,
                    "nb_irpp": nb_irpp,
                    "sum_irpp": sum_irpp,
                    "transport": transport,
                    "telephone_in": telephone_in,
                    "autre_indemnite": autre_indemnite,
                    "iprg_employe": iprg_employe,
                    "irprg_patronale": irprg_patronale,
                    "irpc_employe": irpc_employe,
                    "irpc_patronale": irpc_patronale,
                    "css_accident_travail": css_accident_travail,
                    "css_allocation_familiale": css_allocation_familiale,
                    "total_retenue_employe": total_retenue_employe,
                    "total_retenue_patronale": total_retenue_patronale,
                    "amicale": amicale,
                    "tabaski": tabaski,
                    "aute_cotisation": aute_cotisation,
                    "retenue_cotisation": retenue_cotisation,
                    "cfce": cfce,
                    "total_prime": total_prime,
                    "salaire_net": salaire_net,
                    "date_debut": date_debut_str,
                    "date_fin": date_fin_str,
                }

        return jsonify(data)

    except Exception as e:
        logging.exception("Erreur fetch_conge_maternite")
        return jsonify({"error": str(e)}), 500
