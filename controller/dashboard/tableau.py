from flask import jsonify, url_for, request
from templates.include.connect import get_connection
from templates.include.encryptor import encryptor
from datetime import datetime, date
from babel.dates import format_date
import re

# Fonctions utilitaires
def format_date_fr(date_str, style="long"):
    try:
        if not date_str:
            return ""
        if isinstance(date_str, (datetime, date)):
            dt = date_str
        else:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
        if style == "full":
            fmt = "EEEE d MMMM yyyy"
        elif style == "month":
            fmt = "MMMM yyyy"
        elif style == "years":
            fmt = "yyyy"
        else:
            fmt = "dd MMMM yyyy"
        return format_date(dt, format=fmt, locale="fr_FR").capitalize()
    except Exception:
        return ""


def format_number(value):
    if value is None or value == 0:
        return ""
    return "{:,.0f}".format(value).replace(",", " ")


def make_acronym(word: str) -> str:
    # Supprimer caractères spéciaux style apostrophe
    cleaned = word.replace("'", "").replace("’", "").replace("`", "")
    parts = cleaned.split()
    return "".join([p[0].upper() for p in parts if p])


def tableau_rh():
    db = get_connection()
    cursor = db.cursor(dictionary=True)

    for i in range(1, 7):
        key = f"tableau{i}"
        if key in request.form:
            raw_id = request.form.get(key, "").strip()
            id_ref = encryptor("decrypt", raw_id)

            date = request.form.get("date", "").strip()
            date_du = request.form.get(f"date_du{i}", "").strip()
            date_au = request.form.get(f"date_au{i}", "").strip()

            # Correction : si date_du remplie mais date_au vide → on prend date_du comme date_au
            if date_du and not date_au:
                date_au = date_du

            if not date_du and not date_au:
                # Filtre sur année uniquement
                query = """
                    SELECT * FROM salaire
                    INNER JOIN contrat ON contrat.id_contrat = salaire.id_contrat
                    INNER JOIN employe ON employe.id_employe = contrat.id_employe
                    INNER JOIN reference ON reference.id_reference = employe.id_reference
                    WHERE reference.id_reference = %s AND YEAR(salaire.date_du) = %s
                """
                cursor.execute(query, (id_ref, date))
            else:
                # Filtre BETWEEN si au moins une date présente
                query = """
                    SELECT * FROM salaire
                    INNER JOIN contrat ON contrat.id_contrat = salaire.id_contrat
                    INNER JOIN employe ON employe.id_employe = contrat.id_employe
                    INNER JOIN reference ON reference.id_reference = employe.id_reference
                    WHERE reference.id_reference = %s AND DATE_FORMAT(salaire.date_du, '%Y-%m') BETWEEN %s AND %s
                """
                cursor.execute(query, (id_ref, date_du, date_au))

            result = cursor.fetchall()
            data = []

            for count, row in enumerate(result, start=1):
                acronym_prenom = make_acronym(row.get("prenom"))
                acronym_nom = make_acronym(row.get("nom"))
                response = {
                    "count": count,
                    "prenom": row.get("prenom", ""),
                    "nom": row.get("nom", ""),
                    "matricule": f"{acronym_prenom}{acronym_nom}-{row.get('matricule')}",
                    "s_categorie": row.get("s_categorie", ""),
                    "s_poste_occupe": row.get("s_poste_occupe", ""),
                    "telephone_e": row.get("telephone_e", ""),
                    "date_du": format_date_fr(row.get("date_du"), style="month"),
                    "date_paiement": format_date_fr(
                        row.get("date_paiement"), style="full"
                    ),
                    "mode_paie": row.get("mode_paie", ""),
                    "salaire_base": format_number(row.get("salaire_base")),
                    "salaire_brute": format_number(row.get("salaire_brute")),
                    "salaire_net": format_number(row.get("salaire_net")),
                    "photo": (
                        url_for(
                            "static",
                            filename=f"img/img_employe/{row.get('matricule','')}/{row.get('photo','')}",
                        )
                        if row.get("photo")
                        else url_for("static", filename="img/image/image-profil.png")
                    ),
                    "ind_fonction": format_number(row.get("ind_fonction")),
                    "ind_sujetion": format_number(row.get("ind_sujetion")),
                    "ind_responsabilite": format_number(row.get("ind_responsabilite")),
                    "ind_sursalaire": format_number(row.get("ind_sursalaire")),
                    "ind_logement": format_number(row.get("ind_logement")),
                    "ind_transport": format_number(row.get("ind_transport")),
                    "ind_telephone_in": format_number(row.get("ind_telephone_in")),
                    "ind_autre_indemnite": format_number(
                        row.get("ind_autre_indemnite")
                    ),
                    "iprg_employe": format_number(row.get("iprg_employe")),
                    "irpc_employe": format_number(row.get("irpc_employe")),
                    "s_nb_trimf": row.get("s_nb_trimf", ""),
                    "sum_trimf": format_number(row.get("sum_trimf")),
                    "s_nb_irpp": row.get("s_nb_irpp", ""),
                    "sum_irpp": format_number(row.get("sum_irpp")),
                    "irprg_patronale": format_number(row.get("irprg_patronale")),
                    "irpc_patronale": format_number(row.get("irpc_patronale")),
                    "css_accident_travail": format_number(
                        row.get("css_accident_travail")
                    ),
                    "css_allocation_familiale": format_number(
                        row.get("css_allocation_familiale")
                    ),
                    "cfce": format_number(row.get("cfce")),
                    "s_amicale": format_number(row.get("s_amicale")),
                    "s_tabaski": format_number(row.get("s_tabaski")),
                    "s_aute_cotisation": format_number(row.get("s_aute_cotisation")),
                }
                data.append(response)

            return jsonify(data)

    return jsonify([])
