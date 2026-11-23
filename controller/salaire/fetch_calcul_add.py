import logging
from flask import request, jsonify
from datetime import datetime, date
from templates.include.connect import get_connection
from templates.include.encryptor import encryptor
from .bareme_irpp_1 import bareme_1
from .bareme_irpp_1_5 import bareme_1_5
from .bareme_irpp_2 import bareme_2
from .bareme_irpp_2_5 import bareme_2_5
from .bareme_irpp_3 import bareme_3
from .bareme_irpp_3_5 import bareme_3_5
from .bareme_irpp_4 import bareme_4
from .bareme_irpp_4_5 import bareme_4_5
from .bareme_irpp_5 import bareme_5
import re

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

def acronym(text):
    # Supprime les apostrophes seules et génère acronyme (similaire preg_replace + explode + substr en PHP)
    cleaned = re.sub(r"\b[\p{L}'`‘’]\b", "", text, flags=re.UNICODE)
    words = cleaned.split()
    return "".join(word[0] for word in words if word)


def fetch_calcul_add():
    try:
        id_contrat_enc = request.form.get("id_contrat", "").strip()
        date_du_str = request.form.get("date_du", "").strip()
        if not id_contrat_enc or not date_du_str:
            return jsonify({"error": "Données manquantes"}), 400

        id_contrat = encryptor("decrypt", id_contrat_enc)

        # Conversion date_du en YYYY-MM
        try:
            date_du = datetime.strptime(date_du_str, "%Y-%m")
        except ValueError:
            return jsonify({"error": "Format de date invalide, attendu YYYY-MM"}), 400

        date_jour = date.today().day
        date_d_str = f"{date_du_str}-{date_jour:02d}"
        date_d = datetime.strptime(date_d_str, "%Y-%m-%d")

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        data = []

        with conn:
            with conn.cursor(dictionary=True) as cursor:
                # Récupérer contrat + employé + référence
                cursor.execute(
                    """
                    SELECT contrat.*, employe.*, reference.*
                    FROM contrat
                    INNER JOIN employe ON employe.id_employe=contrat.id_employe
                    INNER JOIN reference ON reference.id_reference=employe.id_reference
                    WHERE contrat.id_contrat=%s
                    ORDER BY contrat.id_contrat DESC
                    """,
                    (id_contrat,),
                )
                result = cursor.fetchall()
                if not result:
                    return jsonify({"error": "Contrat non trouvé"}), 404

                for row in result:
                    # Générer acronymes prenom/nom (comme en PHP)
                    # Note: Python regex \p{L} non supporté nativement, on peut simplifier en supprimant apostrophes isolées avec pattern adapté
                    def clean_acronym(text):
                        # simple approximation: supprimer apostrophes isolées (ex: l', d')
                        text_clean = re.sub(r"\b['’‘`]\b", "", text)
                        words = text_clean.split()
                        return "".join(w[0] for w in words if w)

                    acronym_prenom = clean_acronym(row['prenom'])
                    acronym_nom = clean_acronym(row['nom'])

                    salaire = float(row.get('salaire') or 0)
                    fonction = float(row.get('fonction') or 0)
                    sujetion = float(row.get('sujetion') or 0)
                    responsabilite = float(row.get('responsabilite') or 0)
                    sursalaire = float(row.get('sursalaire') or 0)
                    logement = float(row.get('logement') or 0)
                    amicale = float(row.get('amicale') or 0)
                    tabaski = float(row.get('tabaski') or 0)
                    aute_cotisation = float(row.get('aute_cotisation') or 0)
                    transport = float(row.get('transport') or 0)
                    telephone_in = float(row.get('telephone_in') or 0)
                    autre_indemnite = float(row.get('autre_indemnite') or 0)
                    nb_trimf = int(row.get('nb_trimf') or 0)
                    nb_irpp = float(row.get('nb_irpp') or 0)

                    # Calcul heure pointage + nbr_jour
                    cursor.execute(
                        """
                        SELECT
                            SUM(TIME_TO_SEC(TIMEDIFF(heure_fin, heure_debut))/3600) AS heure,
                            COUNT(pointage.id_contrat) AS nbr_jour
                        FROM pointage
                        WHERE pointage.id_contrat = %s AND DATE_FORMAT(pointage.date, '%%Y-%%m') = %s
                        """,
                        (id_contrat, date_du_str),
                    )
                    pointage = cursor.fetchone()
                    heure_pointage = float(pointage['heure'] or 0)
                    nbr_jour = int(pointage['nbr_jour'] or 0)
                    total_heure_mois = heure_pointage * 4  # approximation

                    # Vérifier date_embauche future
                    date_embauche = row.get('date_embauche')
                    if date_embauche and isinstance(date_embauche, (str,)):
                        date_embauche = datetime.strptime(date_embauche, "%Y-%m-%d").date()
                    if date_embauche and date_embauche > date.today():
                        continue  # on ignore ce contrat

                    # Vérifier départ / suspension salaire
                    cursor.execute(
                        """
                        SELECT depart.*, contrat.id_contrat
                        FROM depart
                        INNER JOIN contrat ON contrat.id_contrat=depart.id_contrat
                        INNER JOIN employe ON employe.id_employe=contrat.id_employe
                        INNER JOIN reference ON reference.id_reference=employe.id_reference
                        WHERE contrat.id_contrat=%s
                        ORDER BY contrat.id_contrat DESC
                        LIMIT 1
                        """,
                        (id_contrat,),
                    )
                    depart = cursor.fetchone()

                    suspensalaire = depart.get('suspensalaire') if depart else None
                    date_effet_depart = depart.get('date_effet') if depart else None
                    if isinstance(date_effet_depart, str):
                        date_effet_depart = datetime.strptime(date_effet_depart, "%Y-%m-%d").date()

                    if date_effet_depart and suspensalaire == "Oui" and date_d.date() >= date_effet_depart:
                        # Contrat suspendu ce mois
                        continue

                    # Récupérer congé annuel (dernier)
                    cursor.execute(
                        """
                        SELECT conge_annuel.*
                        FROM conge_annuel
                        INNER JOIN contrat ON contrat.id_contrat=conge_annuel.id_contrat
                        WHERE contrat.id_contrat=%s
                        ORDER BY conge_annuel.id_conge_annuel DESC
                        LIMIT 1
                        """,
                        (id_contrat,),
                    )
                    conge_annuel = cursor.fetchone()

                    # Récupérer congé maternité (dernier)
                    cursor.execute(
                        """
                        SELECT conge_maternite.*
                        FROM conge_maternite
                        INNER JOIN contrat ON contrat.id_contrat=conge_maternite.id_contrat
                        WHERE contrat.id_contrat=%s
                        ORDER BY conge_maternite.id_conge_maternite DESC
                        LIMIT 1
                        """,
                        (id_contrat,),
                    )
                    conge_maternite = cursor.fetchone()

                    def month_year(d):
                        if not d:
                            return None
                        if isinstance(d, str):
                            return datetime.strptime(d, "%Y-%m-%d").strftime("%Y-%m")
                        if isinstance(d, (date, datetime)):
                            return d.strftime("%Y-%m")
                        return None

                    conge_annuel_debut = month_year(conge_annuel.get('date_debut') if conge_annuel else None)
                    conge_annuel_fin = month_year(conge_annuel.get('date_fin') if conge_annuel else None)
                    cong_mat_debut = month_year(conge_maternite.get('date_suspension') if conge_maternite else None)
                    cong_mat_fin = month_year(conge_maternite.get('date_fin') if conge_maternite else None)

                    # Initialiser variables
                    date_debut = ""
                    date_fin = ""
                    salaire_brute = 0
                    iprg_employe = 0
                    irprg_patronale = 0
                    irpc_employe = 0
                    irpc_patronale = 0
                    css_accident_travail = 0
                    css_allocation_familiale = 0
                    cfce = 0
                    sum_trimf = 0
                    sum_irpp = 0
                    total_retenue_employe = 0
                    total_retenue_patronale = 0
                    retenue_cotisation = 0
                    total_prime = 0
                    salaire_net = 0
                    nbr_conge = ""
                    # Cas congé annuel actif
                    if conge_annuel and conge_annuel_debut and conge_annuel_fin and date_du_str >= conge_annuel_debut and date_du_str <= conge_annuel_fin:
                        date_debut = conge_annuel.get('date_debut')
                        date_fin = conge_annuel.get('date_fin')
                        total_heure_mois = ""
                        salaire_brute = salaire + fonction + sujetion + responsabilite + sursalaire + logement
                        nbr_conge = conge_annuel.get('nbr_conge')
                        sum_trimf = calcul_sum_trimf(salaire_brute, nb_trimf)
                        sum_irpp = calcul_sum_irpp(salaire_brute, nb_irpp)
                        # salaire_net etc restent vides (comme PHP)

                    # Cas congé maternité actif
                    elif conge_maternite and cong_mat_debut and cong_mat_fin and date_du_str >= cong_mat_debut and date_du_str <= cong_mat_fin:
                        date_debut = conge_maternite.get('date_suspension')
                        date_fin = conge_maternite.get('date_fin')
                        # Ajustement salaire en fonction heure_pointage / total_heure_mois
                        if total_heure_mois and total_heure_mois != 0:
                            facteur = heure_pointage / total_heure_mois
                        else:
                            facteur = 0

                        salaire = salaire * facteur
                        fonction = fonction * facteur
                        sujetion = sujetion * facteur
                        responsabilite = responsabilite * facteur
                        sursalaire = sursalaire * facteur
                        logement = logement * facteur

                        salaire_brute = salaire + fonction + sujetion + responsabilite + sursalaire + logement
                        sum_trimf = calcul_sum_trimf(salaire_brute, nb_trimf)
                        sum_irpp = calcul_sum_irpp(salaire_brute, nb_irpp)

                        iprg_employe = calcul_irpg_employe(salaire_brute)
                        irprg_patronale = calcul_irpg_patronale(salaire_brute)
                        irpc_employe = calcul_irpc_employe(salaire_brute)
                        irpc_patronale = calcul_irpc_patronale(salaire_brute)
                        css_accident_travail = calcul_css_accident_travail(salaire_brute)
                        css_allocation_familiale = calcul_css_allocation_familiale(salaire_brute)
                        cfce = calcul_cfce(salaire_brute)

                        total_retenue_employe = iprg_employe + irpc_employe + sum_trimf + sum_irpp + amicale + tabaski + aute_cotisation
                        total_retenue_patronale = irprg_patronale + irpc_patronale + css_accident_travail + css_allocation_familiale + cfce
                        retenue_cotisation = salaire_brute - total_retenue_employe
                        total_prime = transport + telephone_in + autre_indemnite
                        salaire_net = retenue_cotisation + total_prime
                        nbr_conge = ""

                    else:
                        # Cas normal (pas de congé actif)
                        date_debut = ""
                        date_fin = ""
                        salaire_brute = salaire + fonction + sujetion + responsabilite + sursalaire + logement
                        sum_trimf = calcul_sum_trimf(salaire_brute, nb_trimf)
                        sum_irpp = calcul_sum_irpp(salaire_brute, nb_irpp)

                        iprg_employe = calcul_irpg_employe(salaire_brute)
                        irprg_patronale = calcul_irpg_patronale(salaire_brute)

                        irpc_employe = calcul_irpc_employe(salaire_brute)
                        irpc_patronale = calcul_irpc_patronale(salaire_brute)

                        css_accident_travail = calcul_css_accident_travail(salaire_brute)
                        css_allocation_familiale = calcul_css_allocation_familiale(salaire_brute)
                        cfce = calcul_cfce(salaire_brute)

                        total_retenue_employe = iprg_employe + irpc_employe + sum_trimf + sum_irpp + amicale + tabaski + aute_cotisation
                        total_retenue_patronale = irprg_patronale + irpc_patronale + css_accident_travail + css_allocation_familiale + cfce
                        retenue_cotisation = salaire_brute - total_retenue_employe
                        total_prime = transport + telephone_in + autre_indemnite
                        salaire_net = retenue_cotisation + total_prime
                        nbr_conge = ""

                    # Préparer la ligne comme en PHP dans un dictionnaire
                    data.append({
                        "id_contrat": row['id_contrat'],
                        "matricule": row.get("matricule", ""),
                        "acronym_prenom": acronym_prenom,
                        "acronym_nom": acronym_nom,
                        "prenom_nom": f"{row.get('prenom', '')} {row.get('nom', '')}",
                        "nature": row.get('nature', ''),
                        "date_embauche": row.get('date_embauche', ''),
                        "date_sorti": row.get('date_sorti', ''),
                        "categorie": row.get('categorie', ''),
                        "poste_occupe": row.get('poste_occupe', ''),
                        "situation_matr": row.get('situation_matr', ''),
                        "conjoint": row.get('conjoint', ''),
                        "enfant": row.get('enfant', ''),
                        "total_heure_mois": total_heure_mois,
                        "heure_pointage": heure_pointage,
                        "salaire_base": salaire,
                        "ind_fonction": fonction,
                        "ind_sujetion": sujetion,
                        "ind_responsabilite": responsabilite,
                        "ind_sursalaire": sursalaire,
                        "ind_logement": logement,
                        "salaire_brute": salaire_brute,
                        "nbr_conge": nbr_conge,
                        "s_nb_trimf": nb_trimf,
                        "sum_trimf": sum_trimf,
                        "s_nb_irpp": nb_irpp,
                        "sum_irpp": sum_irpp,
                        "ind_transport": transport,
                        "ind_telephone_in": telephone_in,
                        "ind_autre_indemnite": autre_indemnite,
                        "iprg_employe": iprg_employe,
                        "irprg_patronale": irprg_patronale,
                        "irpc_employe": irpc_employe,
                        "irpc_patronale": irpc_patronale,
                        "css_accident_travail": css_accident_travail,
                        "css_allocation_familiale": css_allocation_familiale,
                        "total_retenue_employe": total_retenue_employe,
                        "total_retenue_patronale": total_retenue_patronale,
                        "s_amicale": amicale,
                        "s_tabaski": tabaski,
                        "s_aute_cotisation": aute_cotisation,
                        "retenue_cotisation": retenue_cotisation,
                        "cfce": cfce,
                        "total_prime": total_prime,
                        "salaire_net": salaire_net,
                        "date_debut": date_debut,
                        "date_fin": date_fin,
                    })

        return jsonify(data)

    except Exception as e:
        logging.exception("Erreur dans fetch_salaire")
        return jsonify({"error": str(e)}), 500
