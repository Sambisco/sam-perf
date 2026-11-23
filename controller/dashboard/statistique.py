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


def format_date_fr(date_str, style="long"):
    """
    Formatte une date en français avec différents styles :
    - style="full"   → "vendredi 13 décembre 2024"
    - style="long"   → "13 décembre 2024"
    - style="month"  → "décembre 2024"
    """
    try:
        if not date_str:
            return ""

        # Conversion en objet datetime/date
        if isinstance(date_str, (datetime, date)):
            dt = date_str
        else:
            dt = datetime.strptime(date_str, "%Y-%m-%d")

        # Choix du format
        if style == "full":
            fmt = "EEEE d MMMM yyyy"
        elif style == "month":
            fmt = "MMMM yyyy"
        elif style == "month_stat":
            fmt = "MMMM"
        else:  # "long" par défaut
            fmt = "dd MMMM yyyy"

        return format_date(dt, format=fmt, locale="fr_FR").capitalize()

    except Exception:
        return ""


def statistique_rh():

    if "id" in request.form:
        # Décrypter l'ID comme en PHP
        id_ref = encryptor("decrypt", request.form["id"])
        year = int(request.form["date"].strip())

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        query = """
            SELECT salaire.date_du AS date_du,
                SUM(salaire_base) AS salaire_base,
                SUM(salaire_brute) AS salaire_brute,
                SUM(salaire_net) AS salaire_net,
                SUM(ind_fonction) AS ind_fonction,
                SUM(ind_sujetion) AS ind_sujetion,
                SUM(ind_responsabilite) AS ind_responsabilite,
                SUM(ind_sursalaire) AS ind_sursalaire,
                SUM(ind_logement) AS ind_logement,
                SUM(iprg_employe) AS iprg_employe,
                SUM(irpc_employe) AS irpc_employe,
                SUM(salaire.sum_trimf) AS sum_trimf,
                SUM(salaire.sum_irpp) AS sum_irpp,
                SUM(irprg_patronale) AS irprg_patronale,
                SUM(irpc_patronale) AS irpc_patronale,
                SUM(css_accident_travail) AS css_accident_travail,
                SUM(css_allocation_familiale) AS css_allocation_familiale,
                SUM(cfce) AS cfce,
                SUM(salaire.s_amicale) AS amicale,
                SUM(salaire.s_aute_cotisation) AS s_aute_cotisation,
                SUM(salaire.s_tabaski) AS tabaski,
                SUM(ind_transport) AS ind_transport,
                SUM(ind_telephone_in) AS ind_telephone_in,
                SUM(ind_autre_indemnite) AS ind_autre_indemnite
            FROM salaire
            INNER JOIN contrat ON contrat.id_contrat = salaire.id_contrat
            INNER JOIN employe ON employe.id_employe = contrat.id_employe
            INNER JOIN reference ON reference.id_reference = employe.id_reference
            WHERE reference.id_reference = %s
            AND YEAR(date_du) = %s
            GROUP BY DATE_FORMAT(salaire.date_du,'%m-%Y')
        """

        cursor.execute(query, (id_ref, year))
        result = cursor.fetchall()

        data = []
        for row in result:
            data.append(
                {
                    "date_du": format_date_fr(
                        row["date_du"], style="month_stat"
                    ),  # tu peux formatter en français après
                    "salaire_base": row["salaire_base"],
                    "salaire_brute": row["salaire_brute"],
                    "salaire_net": row["salaire_net"],
                    "ind_fonction": row["ind_fonction"],
                    "ind_sujetion": row["ind_sujetion"],
                    "ind_responsabilite": row["ind_responsabilite"],
                    "ind_sursalaire": row["ind_sursalaire"],
                    "ind_logement": row["ind_logement"],
                    "iprg_employe": row["iprg_employe"],
                    "irpc_employe": row["irpc_employe"],
                    "sum_trimf": row["sum_trimf"],
                    "sum_irpp": row["sum_irpp"],
                    "irprg_patronale": row["irprg_patronale"],
                    "irpc_patronale": row["irpc_patronale"],
                    "css_accident_travail": row["css_accident_travail"],
                    "css_allocation_familiale": row["css_allocation_familiale"],
                    "cfce": row["cfce"],
                    "amicale": row["amicale"],
                    "s_aute_cotisation": row["s_aute_cotisation"],
                    "tabaski": row["tabaski"],
                    "ind_transport": row["ind_transport"],
                    "ind_telephone_in": row["ind_telephone_in"],
                    "ind_autre_indemnite": row["ind_autre_indemnite"],
                }
            )

        conn.close()
        return jsonify(data)
