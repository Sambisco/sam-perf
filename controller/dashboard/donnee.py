from flask import Flask, request, jsonify, url_for, Response
import re
import locale
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
from templates.include.connect import get_connection
from templates.include.encryptor import encryptor
import qrcode
from io import BytesIO
import base64
import json
from decimal import Decimal
from babel.dates import format_date

try:
    locale.setlocale(locale.LC_TIME, "fr_FR.UTF-8")
except locale.Error:
    pass


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


def dashboard_rh():
    data = {}
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    today = date.today().strftime("%Y-%m-%d")

    # Cas 1 : id
    if "id" in request.form:
        id_ref = encryptor("decrypt",request.form["id"])  # À adapter si besoin de décryptage
        year = request.form["date"]
        current_mois = request.form["current_mois"].strip()

        print("FORM DATA:", request.form)
        print("id_ref:", id_ref, "year:", year, "today:", today)
        # 1 - Salaire de base cette année
        if not current_mois:
            cursor.execute(
                """
                SELECT SUM(salaire_base) AS salaire_base
                FROM salaire
                INNER JOIN contrat ON contrat.id_contrat=salaire.id_contrat
                INNER JOIN employe ON employe.id_employe=contrat.id_employe
                INNER JOIN reference ON reference.id_reference=employe.id_reference
                WHERE reference.id_reference=%s AND YEAR(salaire.date_du)=%s
            """,
                (id_ref, year),
            )
        else:
            cursor.execute(
                """
                SELECT SUM(salaire_base) AS salaire_base
                FROM salaire
                INNER JOIN contrat ON contrat.id_contrat=salaire.id_contrat
                INNER JOIN employe ON employe.id_employe=contrat.id_employe
                INNER JOIN reference ON reference.id_reference=employe.id_reference
                WHERE reference.id_reference=%s AND YEAR(salaire.date_du)=%s AND MONTH(salaire.date_du)=%s
            """,
                (id_ref, year, current_mois),
            )
        result = cursor.fetchone()
        data["salaire_base"] = format_amount(result["salaire_base"]) or 0

        # 1 - Indeùnite cette
        if not current_mois:
            cursor.execute(
                """
                SELECT SUM(ind_fonction + ind_sujetion + ind_responsabilite + ind_sursalaire + ind_logement) AS indemnite_annuel
                FROM salaire
                INNER JOIN contrat ON contrat.id_contrat=salaire.id_contrat
                INNER JOIN employe ON employe.id_employe=contrat.id_employe
                INNER JOIN reference ON reference.id_reference=employe.id_reference
                WHERE reference.id_reference=%s AND YEAR(salaire.date_du)=%s
            """,
                (id_ref, year),
            )
        else:
            cursor.execute(
                """
                SELECT SUM(ind_fonction + ind_sujetion + ind_responsabilite + ind_sursalaire + ind_logement) AS indemnite_annuel
                FROM salaire
                INNER JOIN contrat ON contrat.id_contrat=salaire.id_contrat
                INNER JOIN employe ON employe.id_employe=contrat.id_employe
                INNER JOIN reference ON reference.id_reference=employe.id_reference
                WHERE reference.id_reference=%s AND YEAR(salaire.date_du)=%s AND MONTH(salaire.date_du)=%s
            """,
                (id_ref, year, current_mois),
            )

        result = cursor.fetchone()
        data["indemnite_annuel"] = format_amount(result["indemnite_annuel"]) or 0

        # 1 - charge salariale cette année
        if not current_mois:
            cursor.execute(
                """
                SELECT SUM(iprg_employe + irpc_employe + sum_trimf + sum_irpp) AS charge_salariale
                FROM salaire
                INNER JOIN contrat ON contrat.id_contrat=salaire.id_contrat
                INNER JOIN employe ON employe.id_employe=contrat.id_employe
                INNER JOIN reference ON reference.id_reference=employe.id_reference
                WHERE reference.id_reference=%s AND YEAR(salaire.date_du)=%s
            """,
                (id_ref, year),
            )
        else:
            cursor.execute(
                """
                SELECT SUM(iprg_employe + irpc_employe + sum_trimf + sum_irpp) AS charge_salariale
                FROM salaire
                INNER JOIN contrat ON contrat.id_contrat=salaire.id_contrat
                INNER JOIN employe ON employe.id_employe=contrat.id_employe
                INNER JOIN reference ON reference.id_reference=employe.id_reference
                WHERE reference.id_reference=%s AND YEAR(salaire.date_du)=%s AND MONTH(salaire.date_du)=%s
            """,
                (id_ref, year, current_mois),
            )
        result = cursor.fetchone()
        data["charge_salariale"] = format_amount(result["charge_salariale"]) or 0

        # 1 - charge patronale cette année
        if not current_mois:
            cursor.execute(
                """
                SELECT SUM(irprg_patronale + irpc_patronale + css_accident_travail + css_allocation_familiale + cfce) AS charge_patronale
                FROM salaire
                INNER JOIN contrat ON contrat.id_contrat=salaire.id_contrat
                INNER JOIN employe ON employe.id_employe=contrat.id_employe
                INNER JOIN reference ON reference.id_reference=employe.id_reference
                WHERE reference.id_reference=%s AND YEAR(salaire.date_du)=%s
            """,
                (id_ref, year),
            )
        else:
            cursor.execute(
                """
                SELECT SUM(irprg_patronale + irpc_patronale + css_accident_travail + css_allocation_familiale + cfce) AS charge_patronale
                FROM salaire
                INNER JOIN contrat ON contrat.id_contrat=salaire.id_contrat
                INNER JOIN employe ON employe.id_employe=contrat.id_employe
                INNER JOIN reference ON reference.id_reference=employe.id_reference
                WHERE reference.id_reference=%s AND YEAR(salaire.date_du)=%s AND MONTH(salaire.date_du)=%s
            """,
                (id_ref, year, current_mois),
            )
        result = cursor.fetchone()
        data["charge_patronale"] = format_amount(result["charge_patronale"]) or 0

        # 1 - Nombre d'employés sans contrat
        cursor.execute(
            """
            SELECT COUNT(employe.id_employe) AS id_employe
            FROM employe
            WHERE NOT EXISTS (
                SELECT * FROM contrat
                WHERE employe.id_employe = contrat.id_employe
            ) AND id_reference=%s
        """,
            (id_ref,),
        )
        result = cursor.fetchone()
        data["recruitement"] = result["id_employe"] or 0

        # 2 - Nombre de contrats
        cursor.execute(
            """
            SELECT COUNT(contrat.id_contrat) AS id_contrat
            FROM contrat
            INNER JOIN employe ON employe.id_employe=contrat.id_employe
            INNER JOIN reference ON reference.id_reference=employe.id_reference
            WHERE reference.id_reference=%s
        """,
            (id_ref,),
        )
        result = cursor.fetchone()
        data["contrat"] = result["id_contrat"] or 0

        # 3 - Départs
        if not current_mois:
            cursor.execute(
                """
                SELECT COUNT(depart.id_depart) AS id_depart
                FROM depart
                INNER JOIN contrat ON contrat.id_contrat=depart.id_contrat
                INNER JOIN employe ON employe.id_employe=contrat.id_employe
                INNER JOIN reference ON reference.id_reference=employe.id_reference
                WHERE reference.id_reference=%s AND YEAR(depart.date_effet)=%s
            """,
                (id_ref,year),
            )
        else:
            cursor.execute(
                """
                    SELECT COUNT(depart.id_depart) AS id_depart
                    FROM depart
                    INNER JOIN contrat ON contrat.id_contrat=depart.id_contrat
                    INNER JOIN employe ON employe.id_employe=contrat.id_employe
                    INNER JOIN reference ON reference.id_reference=employe.id_reference
                    WHERE reference.id_reference=%s AND YEAR(depart.date_effet)=%s AND MONTH(depart.date_effet)=%s
                """,
                (id_ref, year,current_mois),
            )
        result = cursor.fetchone()
        data["depart"] = result["id_depart"] or 0

        # Employés actifs
        data["employe_actif"] = data["contrat"] - data["depart"]

        # 4 - Affectations
        if not current_mois:
            cursor.execute(
                """
                SELECT COUNT(*) AS id_affectation
                FROM affectation
                INNER JOIN contrat ON contrat.id_contrat=affectation.id_contrat
                INNER JOIN employe ON employe.id_employe=contrat.id_employe
                INNER JOIN region ON region.id_region=affectation.id_region
                INNER JOIN reference ON reference.id_reference=employe.id_reference
                WHERE reference.id_reference=%s AND YEAR(date_affectation)=%s
            """,
                (id_ref, year),
            )
        else:
            cursor.execute(
                """
                SELECT COUNT(*) AS id_affectation
                FROM affectation
                INNER JOIN contrat ON contrat.id_contrat=affectation.id_contrat
                INNER JOIN employe ON employe.id_employe=contrat.id_employe
                INNER JOIN region ON region.id_region=affectation.id_region
                INNER JOIN reference ON reference.id_reference=employe.id_reference
                WHERE reference.id_reference=%s AND YEAR(date_affectation)=%s AND MONTH(date_affectation)=%s
            """,
                (id_ref, year,current_mois),
            )
        result = cursor.fetchone()
        data["affectation"] = result["id_affectation"] or 0

        # 5 - Congé annuel
        if not current_mois:
            cursor.execute(
                """
                SELECT COUNT(*) AS id_conge_annuel
                FROM conge_annuel
                INNER JOIN contrat ON contrat.id_contrat=conge_annuel.id_contrat
                INNER JOIN employe ON employe.id_employe=contrat.id_employe
                INNER JOIN reference ON reference.id_reference=employe.id_reference
                WHERE reference.id_reference=%s AND YEAR(date_debut)=%s
            """,
                (id_ref, year),
            )
        else:
            cursor.execute(
                """
                SELECT COUNT(*) AS id_conge_annuel
                FROM conge_annuel
                INNER JOIN contrat ON contrat.id_contrat=conge_annuel.id_contrat
                INNER JOIN employe ON employe.id_employe=contrat.id_employe
                INNER JOIN reference ON reference.id_reference=employe.id_reference
                WHERE reference.id_reference=%s AND YEAR(date_debut)=%s AND MONTH(date_debut)=%s
            """,
                (id_ref, year,current_mois),
            )
        result = cursor.fetchone()
        data["conge_annuel"] = result["id_conge_annuel"] or 0

        # 6 - Congé maternité
        if not current_mois:
            cursor.execute(
                """
                SELECT COUNT(*) AS id_conge_maternite
                FROM conge_maternite
                INNER JOIN contrat ON contrat.id_contrat=conge_maternite.id_contrat
                INNER JOIN employe ON employe.id_employe=contrat.id_employe
                INNER JOIN reference ON reference.id_reference=employe.id_reference
                WHERE reference.id_reference=%s AND YEAR(date_debut)=%s
            """,
                (id_ref, year),
            )
        else:
            cursor.execute(
                """
                SELECT COUNT(*) AS id_conge_maternite
                FROM conge_maternite
                INNER JOIN contrat ON contrat.id_contrat=conge_maternite.id_contrat
                INNER JOIN employe ON employe.id_employe=contrat.id_employe
                INNER JOIN reference ON reference.id_reference=employe.id_reference
                WHERE reference.id_reference=%s AND YEAR(date_debut)=%s AND MONTH(date_debut)=%s
            """,
                (id_ref, year, current_mois),
            )
        result = cursor.fetchone()
        data["conge_maternite"] = result["id_conge_maternite"] or 0

        # 7 - Pointage
        if not current_mois:
            cursor.execute(
                """
                SELECT COUNT(*) AS id_pointage
                FROM pointage
                INNER JOIN contrat ON contrat.id_contrat=pointage.id_contrat
                INNER JOIN employe ON employe.id_employe=contrat.id_employe
                INNER JOIN reference ON reference.id_reference=employe.id_reference
                WHERE reference.id_reference=%s AND YEAR(date)=%s
            """,
                (id_ref, year),
            )
        else:
            cursor.execute(
                """
                SELECT COUNT(*) AS id_pointage
                FROM pointage
                INNER JOIN contrat ON contrat.id_contrat=pointage.id_contrat
                INNER JOIN employe ON employe.id_employe=contrat.id_employe
                INNER JOIN reference ON reference.id_reference=employe.id_reference
                WHERE reference.id_reference=%s AND YEAR(date)=%s AND MONTH(date)=%s
            """,
                (id_ref, year, current_mois),
            )
        result = cursor.fetchone()
        data["pointage"] = result["id_pointage"] or 0

    # Cas 2 : id2
   

    cursor.close()
    conn.close()
    return jsonify(data)
