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


def statistique_gs():
    if "id" not in request.form or "date" not in request.form:
        return jsonify({"error": "Paramètres manquants"}), 400

    try:
        id_ref = encryptor("decrypt", request.form["id"])
        year = request.form["date"].strip()
        current_mois = request.form["current_mois"].strip()

        data1, data2, data3, data4, data5, data6, data7 = [], [], [], [], [], [], []

        # Forcer locale FR pour les mois
        try:
            locale.setlocale(locale.LC_TIME, "fr_FR.UTF-8")
        except:
            locale.setlocale(locale.LC_TIME, "fr_FR")

        with get_connection() as conn:
            with conn.cursor(dictionary=True) as cursor:

                # Entrées
                if not current_mois:
                    cursor.execute(
                        """
                            SELECT entree.date_entree AS date_entree,
                                   SUM(quantite) AS quantite_entree,
                                   SUM(total_entree) AS total_entree
                            FROM detail_entree 
                            INNER JOIN entree ON entree.id_entree = detail_entree.id_entree 
                            INNER JOIN reference ON reference.id_reference = entree.id_reference
                            WHERE reference.id_reference = %s 
                            AND DATE_FORMAT(entree.date_entree,'%Y') = %s
                            GROUP BY DATE_FORMAT(entree.date_entree,'%m-%Y')
                        """,
                        (id_ref, year),
                    )
                    format_style = "month_stat"  # ← car GROUP BY
                else:
                    cursor.execute(
                        """
                            SELECT entree.date_entree AS date_entree,
                                   SUM(quantite) AS quantite_entree,
                                   SUM(total_entree) AS total_entree
                            FROM detail_entree 
                            INNER JOIN entree ON entree.id_entree = detail_entree.id_entree 
                            INNER JOIN reference ON reference.id_reference = entree.id_reference
                            WHERE reference.id_reference = %s 
                            AND DATE_FORMAT(entree.date_entree,'%Y') = %s AND DATE_FORMAT(entree.date_entree,'%m') = %s 
                             GROUP BY DATE_FORMAT(entree.date_entree,'%d-%m-%Y')
                        """,
                        (id_ref, year, current_mois),
                    )
                    format_style = "long"  # ← car pas de GROUP BY
                for row in cursor.fetchall():
                    data1.append(
                        {
                            "date_entree": format_date_fr(
                                row["date_entree"], style=format_style
                            ),
                            "quantite_entree": row["quantite_entree"],
                            "total_entree": row["total_entree"],
                        }
                    )

                # Sorties interne
                cursor.execute(
                    """
                    SELECT sortie.date_sortie AS date_sortie,
                           SUM(sortie.total) AS total_sortie
                    FROM sortie
                    INNER JOIN contrat ON contrat.id_contrat = sortie.id_contrat 
                    INNER JOIN employe ON employe.id_employe = contrat.id_employe 
                    INNER JOIN reference ON reference.id_reference = employe.id_reference 
                    WHERE reference.id_reference = %s 
                      AND DATE_FORMAT(sortie.date_sortie,'%Y') = %s
                    GROUP BY DATE_FORMAT(sortie.date_sortie,'%m-%Y')
                """,
                    (id_ref, year),
                )
                for row in cursor.fetchall():
                    data2.append(
                        {
                            "date_sortie_interne": format_date_fr(
                                row["date_sortie"], style="month_stat"
                            ),
                            "total_sortie_interne": row["total_sortie"],
                        }
                    )

                # Sorties externe
                cursor.execute(
                    """
                    SELECT sortie_externe.date_sortie AS date_sortie,
                           SUM(sortie_externe.total) AS total_sortie
                    FROM sortie_externe
                        INNER JOIN reference ON reference.id_reference=sortie_externe.id_reference
                    WHERE reference.id_reference = %s 
                      AND DATE_FORMAT(sortie_externe.date_sortie,'%Y') = %s
                    GROUP BY DATE_FORMAT(sortie_externe.date_sortie,'%m-%Y')
                """,
                    (id_ref, year),
                )
                for row in cursor.fetchall():
                    data7.append(
                        {
                            "date_sortie_externe": format_date_fr(
                                row["date_sortie"], style="month_stat"
                            ),
                            "total_sortie_externe": row["total_sortie"],
                        }
                    )

                # Affectations
                cursor.execute(
                    """
                    SELECT affectation_matiere.date_affectation AS date_affectation,
                           SUM(affectation_matiere.total) AS total_affectation
                    FROM affectation_matiere
                    INNER JOIN contrat ON contrat.id_contrat = affectation_matiere.id_contrat
                    INNER JOIN employe ON employe.id_employe = contrat.id_employe
                    INNER JOIN reference ON reference.id_reference = employe.id_reference
                    WHERE reference.id_reference = %s 
                      AND DATE_FORMAT(affectation_matiere.date_affectation,'%Y') = %s
                    GROUP BY DATE_FORMAT(affectation_matiere.date_affectation,'%m-%Y')
                """,
                    (id_ref, year),
                )
                for row in cursor.fetchall():

                    data3.append(
                        {
                            "date_affectation": format_date_fr(
                                row["date_affectation"], style="month_stat"
                            ),
                            "total_affectation": row["total_affectation"],
                        }
                    )

                # Dotations
                cursor.execute(
                    """
                    SELECT dotation.date_dotation AS date_dotation,
                           SUM(dotation.carburant) AS carburant
                    FROM dotation
                    INNER JOIN contrat ON contrat.id_contrat = dotation.id_contrat
                    INNER JOIN employe ON employe.id_employe = contrat.id_employe
                    INNER JOIN reference ON reference.id_reference = employe.id_reference
                    WHERE reference.id_reference = %s 
                      AND DATE_FORMAT(dotation.date_dotation,'%Y') = %s
                    GROUP BY DATE_FORMAT(dotation.date_dotation,'%m-%Y')
                """,
                    (id_ref, year),
                )
                for row in cursor.fetchall():
                    data4.append(
                        {
                            "date_dotation": format_date_fr(
                                row["date_dotation"], style="month_stat"
                            ),
                            "carburant": row["carburant"],
                        }
                    )

                # Immobilisations

                # Réceptions carburant
                cursor.execute(
                    """
                    SELECT reception_carburant.date_reception AS date_reception,
                           SUM(reception_carburant.carburant_gasoil + reception_carburant.carburant_super) AS recept_carburant
                    FROM reception_carburant
                    INNER JOIN fournisseur ON fournisseur.id_fournisseur = reception_carburant.id_fournisseur
                    INNER JOIN reference ON reference.id_reference = fournisseur.id_reference
                    WHERE reference.id_reference = %s 
                      AND DATE_FORMAT(reception_carburant.date_reception,'%Y') = %s
                    GROUP BY DATE_FORMAT(reception_carburant.date_reception,'%m-%Y')
                """,
                    (id_ref, year),
                )
                for row in cursor.fetchall():
                    data5.append(
                        {
                            "date_reception": format_date_fr(
                                row["date_reception"], style="month_stat"
                            ),
                            "recept_carburant": row["recept_carburant"],
                        }
                    )

                cursor.execute(
                    """
                    SELECT 
                        mois,
                        MAX(date_entree) AS date_entree,
                        MAX(date_sortie) AS date_sortie,
                        SUM(quantite_entree) AS quantite_entree,
                        SUM(total_sortie) AS total_sortie
                    FROM (
                        -- Entrées
                        SELECT 
                            DATE_FORMAT(entree.date_entree, '%m') AS mois,
                            entree.date_entree,
                            NULL AS date_sortie,
                            SUM(detail_entree.quantite) AS quantite_entree,
                            0 AS total_sortie
                        FROM detail_entree
                        INNER JOIN entree ON entree.id_entree = detail_entree.id_entree
                        INNER JOIN reference ON reference.id_reference = entree.id_reference
                        WHERE reference.id_reference = %s
                          AND DATE_FORMAT(entree.date_entree, '%Y') = %s
                        GROUP BY DATE_FORMAT(entree.date_entree, '%m')

                        UNION ALL

                        -- Sorties
                        SELECT 
                            DATE_FORMAT(sortie.date_sortie, '%m') AS mois,
                            NULL AS date_entree,
                            sortie.date_sortie,
                            0 AS quantite_entree,
                            SUM(sortie.total) AS total_sortie
                        FROM sortie
                        INNER JOIN contrat ON contrat.id_contrat = sortie.id_contrat
                        INNER JOIN employe ON employe.id_employe = contrat.id_employe
                        INNER JOIN reference ON reference.id_reference = employe.id_reference
                        WHERE reference.id_reference = %s
                          AND DATE_FORMAT(sortie.date_sortie, '%Y') = %s
                        GROUP BY DATE_FORMAT(sortie.date_sortie, '%m')
                    ) AS fusion
                    GROUP BY mois
                    ORDER BY mois
                """,
                    (id_ref, year, id_ref, year),
                )
                for row in cursor.fetchall():
                    mois = f"{year}-{row['mois']}-01"
                    data6.append(
                        {
                            "mois": format_date_fr(mois, style="month_stat"),
                            "quantite_entree": float(row["quantite_entree"] or 0),
                            "total_sortie": float(row["total_sortie"] or 0),
                            "date_entree": (
                                format_date_fr(row["date_entree"])
                                if row["date_entree"]
                                else ""
                            ),
                            "date_sortie": (
                                format_date_fr(row["date_sortie"])
                                if row["date_sortie"]
                                else ""
                            ),
                        }
                    )

        return jsonify([data1, data2, data3, data4, data5, data6, data7])

    except Exception as e:
        print(f"Erreur fetch_dashboard_monthly : {e}")
        return jsonify({"error": "Erreur serveur"}), 500
