from flask import Response, abort, url_for
from weasyprint import HTML, CSS
from templates.include.connect import get_connection
from templates.include.encryptor import encryptor
import locale
from datetime import datetime, date, timedelta
import os
from babel.dates import format_date

try:
    locale.setlocale(locale.LC_TIME, "fr_FR.UTF-8")
except locale.Error:
    locale.setlocale(locale.LC_TIME, "")


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
        elif style == "years":
            fmt = "yyyy"
        else:  # "long" par défaut
            fmt = "dd MMMM yyyy"

        return format_date(dt, format=fmt, locale="fr_FR").capitalize()

    except Exception:
        return ""


# Fonctions utilitaires
def get_acronym(name):
    import re

    name_clean = re.sub(r"\b[\w][\'`‘’]\b", "", name)
    words = name_clean.split()
    return "".join([w[0].upper() for w in words])


def format_amount(value, decimals=0):
    if value in (0, "0.000", None):
        return "-"
    try:
        # Arrondit à "decimals" décimales
        value = round(float(value), decimals)
        # Formate avec séparateur d'espace et virgule décimale
        format_str = "{:,.{prec}f}".format(value, prec=decimals)
        return format_str.replace(",", " ").replace(".", ",")
    except Exception:
        return str(value)


def handle(encrypted_id):
    pdf_id = datetime.strptime(encrypted_id, "%Y-%m")
    if not pdf_id:
        return "Paramètre 'pdf' manquant", 400

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # 1) Récupération des infos référence/entreprise
    query_ref = """
        SELECT * FROM salaire
        INNER JOIN contrat ON salaire.id_contrat = contrat.id_contrat
        INNER JOIN employe ON employe.id_employe = contrat.id_employe
        INNER JOIN reference ON reference.id_reference = employe.id_reference
        WHERE YEAR(salaire.date_du) = %s AND MONTH(salaire.date_du) = %s
        LIMIT 1
    """
    cursor.execute(query_ref, (pdf_id.year,pdf_id.month))
    result_ref = cursor.fetchone()

    if not result_ref:
        return "Aucune donnée trouvée", 404
    logo_file = result_ref["logo"] if result_ref.get("logo") else "image.jpg"
    logo_path = os.path.join("static", "img", "logo", logo_file)  # chemin relatif depuis ton script
    logo_path_abs = os.path.abspath(logo_path)  # chemin absolu nécessaire pour WeasyPrint

    drapeau_file = result_ref["drapeau"] if result_ref.get("drapeau") else "image.jpg"
    drapeau_path = os.path.join(
        "static", "img", "drapeau", drapeau_file
    )  # chemin relatif depuis ton script
    drapeau_path_abs = os.path.abspath(
        drapeau_path
    )  # chemin absolu nécessaire pour WeasyPrint

    # 2) Récupération des salaires
    query_salaire = """
        SELECT * FROM salaire
        INNER JOIN contrat ON salaire.id_contrat = contrat.id_contrat
        INNER JOIN employe ON employe.id_employe = contrat.id_employe
        INNER JOIN reference ON reference.id_reference = employe.id_reference
        WHERE YEAR(salaire.date_du) = %s AND MONTH(salaire.date_du) = %s

    """
    cursor.execute(query_salaire, (pdf_id.year, pdf_id.month))
    rows = cursor.fetchall()

    # 3) Préparation HTML
    html_content = f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <title>Fiche de paie</title>
        <link rel="stylesheet" href="css/fiche_paie.css">
    </head>
    <body>
        <div id="header">
            <div class="logo"><img src="file:///{drapeau_path_abs.replace(os.sep, '/')}" alt=""></div>
            <div class="header1">
              <div><strong>{result_ref['republique']}</strong></div>
              <div><i>{result_ref['devise']}</i></div>
              <div>{result_ref['ministere']}</div>
            </div>
		    <div class="header2">
                <div><strong>{result_ref['entreprise']}</strong></div>
                <div>{result_ref['adresse']}</div>
                <div>Tel : {result_ref['telephone']} | Fax: {result_ref['fax']} | BP : {result_ref['bp']}</div>
                <div>Site web : {result_ref['web']} | Email: {result_ref['email']}</div>
            </div>
		    <div class="logo"><img src="file:///{logo_path_abs.replace(os.sep, '/')}" alt=""></div>
        </div>
    """
    footer = f"""
        <div id="footer">
          <div>{result_ref.get('ministere','')}</div>
          <div>{result_ref.get('entreprise','')}</div>
          <div>{result_ref.get('adresse','')}</div>
          <div>
            Téléphone : {result_ref.get('telephone','')} |
            Email : {result_ref.get('email','')} |
            Fax : {result_ref.get('fax','')} |
            BP : {result_ref.get('bp','')} |
            Site web : {result_ref.get('web','')}
          </div>
        </div>
        """
    # Mois en lettres
    mois_txt = format_date_fr(result_ref["date_du"], style="month")
    vowel = ["a", "e", "i", "o", "u"]
    acronym_mois = mois_txt[0].lower()  # première lettre du mois en minuscule
    if acronym_mois in vowel:
        approstrof = "D'"
    else:
        approstrof = "DE"

    html_content += (
        f"<div class='container'><div class='title-h3'>ETAT DES SALAIRES {approstrof} {mois_txt.upper()}</div><div></div></div>"
    )

    # Table
    html_content += """
    <table class="table2" border="1" cellspacing="0" cellpadding="4">
        <thead>
            <tr class="th_color">
              <th class="th_colorth th_colorth1"  rowspan="2" style="	border-left: #000 1px solid;">Matricule</th>
              <th class="th_colorth th_colorth2"  rowspan="2">NOM & PRENOM</th>
              <th class="th_colorth th_colorth3"  rowspan="2"><div id="vertical">SALAIRE BRUT</div></th>
              <th class="th_colorth th_colorth4" colspan="3">VRS</th>
              <th class="th_colorth th_colorth5" colspan="2">IPRES</th>
              <th class="th_colorth th_colorth6" colspan="2">CSS</th>
              <th class="th_colorth th_colorth7" colspan="3">RETENUE SOCIALES</th>
              <th class="th_colorth th_colorth8" colspan="3">INDEMNITES NON IMPOSIBLES</th>
              <th class="th_colorth th_colorth9"  rowspan="2"  style="border-bottom: #000 1px solid;"><div id="vertical">SALAIRE NET</div></th>
              <th class="th_colorth th_colorth10"  rowspan="2" style="border-right: #000 1px solid;border-bottom: #000 1px solid;"><div id="vertical">MONTANT A PAYER</div></th>
              </tr>
              <tr class="th_color">
              <td class="th_sous_colorth">IR</td>
              <td class="th_sous_colorth">TRIMF</td>
              <td class="th_sous_colorth">CFCE</td>
              <td class="th_sous_colorth">PS</td>
              <td class="th_sous_colorth">PP</td>
              <td class="th_sous_colorth">PF</td>
              <td class="th_sous_colorth">AT</td>
              <td class="th_sous_colorth">AMICALES</td>
              <td class="th_sous_colorth">AUTRES</td>
              <td class="th_sous_colorth">TABASKI</td>
              <td class="th_sous_colorth">TRANSPORT</td>
              <td class="th_sous_colorth">TELEPHONE</td>
              <td class="th_sous_colorth" style="border-right: #fff 2px solid;">AUTRES</td>
            </tr>
        </thead>
        <tbody>
    """

    # Totaux
    totaux = {
        "salaire_brute": 0,
        "sum_irpp": 0,
        "sum_trimf": 0,
        "cfce": 0,
        "ipress_employe": 0,
        "ipress_patronale": 0,
        "css_af": 0,
        "css_at": 0,
        "amicale": 0,
        "autre_cotisation": 0,
        "tabaski": 0,
        "transport": 0,
        "telephone": 0,
        "autres_indemnites": 0,
        "salaire_net": 0,
    }

    for row in rows:
        ipress_employe = row["iprg_employe"] + row["irpc_employe"]
        ipress_patronale = row["irprg_patronale"] + row["irpc_patronale"]

        html_content += f"""
        <tr class="td_content">
            <td class="td_content1">{row['prenom'][0]}{row['nom'][0]}-{row['matricule']}</td>
            <td class="td_content2">{row['prenom']} {row['nom']}</td>
            <td class="td_content3">{format_amount(row['salaire_brute'])}</td>
            <td class="td_content4">{format_amount(row['sum_irpp'])}</td>
            <td class="td_content5">{format_amount(row['sum_trimf'])}</td>
            <td class="td_content6">{format_amount(row['cfce'])}</td>
            <td class="td_content7">{format_amount(ipress_employe)}</td>
            <td class="td_content8">{format_amount(ipress_patronale)}</td>
            <td class="td_content9">{format_amount(row['css_allocation_familiale'])}</td>
            <td class="td_content10">{format_amount(row['css_accident_travail'])}</td>
            <td class="td_content11">{format_amount(row['s_amicale'])}</td>
            <td class="td_content12">{format_amount(row['s_aute_cotisation'])}</td>
            <td class="td_content13">{format_amount(row['s_tabaski'])}</td>
            <td class="td_content14">{format_amount(row['ind_transport'])}</td>
            <td class="td_content15">{format_amount(row['ind_telephone_in'])}</td>
            <td class="td_content16">{format_amount(row['ind_autre_indemnite'])}</td>
            <td class="td_content17">{format_amount(row['salaire_net'])}</td>
            <td class="td_content18">{format_amount(row['salaire_net'])}</td>
        </tr>
        """

        # Incrément totaux
        totaux["salaire_brute"] += row["salaire_brute"]
        totaux["sum_irpp"] += row["sum_irpp"]
        totaux["sum_trimf"] += row["sum_trimf"]
        totaux["cfce"] += row["cfce"]
        totaux["ipress_employe"] += ipress_employe
        totaux["ipress_patronale"] += ipress_patronale
        totaux["css_af"] += row["css_allocation_familiale"]
        totaux["css_at"] += row["css_accident_travail"]
        totaux["amicale"] += row["s_amicale"]
        totaux["autre_cotisation"] += row["s_aute_cotisation"]
        totaux["tabaski"] += row["s_tabaski"]
        totaux["transport"] += row["ind_transport"]
        totaux["telephone"] += row["ind_telephone_in"]
        totaux["autres_indemnites"] += row["ind_autre_indemnite"]
        totaux["salaire_net"] += row["salaire_net"]

    # Ligne totaux
    html_content += f"""
    <tr class="td_content td_content_totaux">
        <td colspan="2">TOTAUX</td>
        <td>{format_amount(totaux['salaire_brute'])}</td>
        <td>{format_amount(totaux['sum_irpp'])}</td>
        <td>{format_amount(totaux['sum_trimf'])}</td>
        <td>{format_amount(totaux['cfce'])}</td>
        <td>{format_amount(totaux['ipress_employe'])}</td>
        <td>{format_amount(totaux['ipress_patronale'])}</td>
        <td>{format_amount(totaux['css_af'])}</td>
        <td>{format_amount(totaux['css_at'])}</td>
        <td>{format_amount(totaux['amicale'])}</td>
        <td>{format_amount(totaux['autre_cotisation'])}</td>
        <td>{format_amount(totaux['tabaski'])}</td>
        <td>{format_amount(totaux['transport'])}</td>
        <td>{format_amount(totaux['telephone'])}</td>
        <td>{format_amount(totaux['autres_indemnites'])}</td>
        <td>{format_amount(totaux['salaire_net'])}</td>
        <td>{format_amount(totaux['salaire_net'])}</td>
    </tr>
    </tbody>
    </table>
     {footer}

        <div class="page-break"></div>
    </body>
    </html>
    """

    cursor.close()
    conn.close()

    # 4) Génération PDF avec WeasyPrint
    base_dir = os.path.dirname(os.path.abspath(__file__))
    css_path = os.path.abspath(
        os.path.join(base_dir, "..", "static", "css", "css", "fiche_paie.css")
    )
    static_dir = os.path.abspath(os.path.join(base_dir, "..", "..", "static"))

    # Génération PDF avec CSS, base_url = dossier static pour résolution relative
    pdf = HTML(string=html_content, base_url=static_dir).write_pdf(
        stylesheets=[CSS(css_path)]
    )

    # Retour HTTP inline PDF
    return Response(
        pdf,
        mimetype="application/pdf",
        headers={"Content-Disposition": f"inline; filename=dmt_{pdf_id}.pdf"},
    )
