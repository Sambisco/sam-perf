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


def parse_amount(value):
    """Convertit une chaîne formatée (ex: '24 192') en float"""
    if value in (0, "0.000", None, ""):
        return 0.0
    try:
        return float(str(value).replace(" ", "").replace(",", "."))
    except Exception:
        return 0.0


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


def handle(encrypted_id):
    pdf_id = encryptor("decrypt", encrypted_id)
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # Requête SQL complète
    query = f"""
    SELECT * FROM salaire
    INNER JOIN contrat ON salaire.id_contrat=contrat.id_contrat
    INNER JOIN employe ON employe.id_employe=contrat.id_employe
    INNER JOIN reference ON reference.id_reference=employe.id_reference
    WHERE salaire.id_salaire = %s
    ORDER BY contrat.id_contrat DESC
    """
    cursor.execute(query, (pdf_id,))
    results = cursor.fetchall()

    html_content = """
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <title>Fiche de paie</title>
        <style>
     
        </style>
    </head>
    <body>
    """

    for row in results:
        acronym_prenom = get_acronym(row["prenom"])
        acronym_nom = get_acronym(row["nom"])

        # Formatter tous les montants
        fields_to_format = [
            "salaire_base",
            "fonction",
            "responsabilite",
            "sujetion",
            "sursalaire",
            "logement",
            "ind_sursalaire",
            "ind_fonction",
            "ind_responsabilite",
            "ind_sujetion",
            "ind_logement",
            "salaire_brute",
            "iprg_employe",
            "irprg_patronale",
            "irpc_employe",
            "irpc_patronale",
            "css_accident_travail",
            "css_allocation_familiale",
            "sum_trimf",
            "sum_irpp",
            "s_amicale",
            "s_aute_cotisation",
            "s_tabaski",
            "cfce",
            "total_retenue_employe",
            "total_retenue_patronale",
            "ind_transport",
            "ind_telephone_in",
            "ind_autre_indemnite",
            "total_prime",
            "retenue_cotisation",
            "salaire_net",
            "salaire_brute_annuel",
            "ind_indemnite_conge",
            "ind_indemnite_conge_supplementaire",
            "months",
            "nbr_conge",
            "nbr_conge_supplementaire",
        ]
        for field in fields_to_format:
            row[field] = format_amount(row.get(field))

        ipress_employe = parse_amount(row["iprg_employe"]) + parse_amount(row["irpc_employe"])
        ipress_patronale = parse_amount(row["irprg_patronale"]) + parse_amount(row["irpc_patronale"])
        # Chemin local du logo
        logo_file = row["logo"] if row.get("logo") else "image.jpg"
        logo_path = os.path.join(
            "static", "img", "logo", logo_file
        )  # chemin relatif depuis ton script
        logo_path_abs = os.path.abspath(
            logo_path
        )  # chemin absolu nécessaire pour WeasyPrint
        footer = f"""
        <div id="footer">
          <div>{row.get('ministere','')}</div>
          <div>{row.get('entreprise','')}</div>
          <div>{row.get('adresse','')}</div>
          <div>
            Téléphone : {row.get('telephone','')} |
            Email : {row.get('email','')} |
            Fax : {row.get('fax','')} |
            BP : {row.get('bp','')} |
            Site web : {row.get('web','')}
          </div>
        </div>
                  """

        # HTML complet du bulletin
        html_content += f"""
        <div class="hearder">
		    <div class="header-left">
               <div class="logo"><img src="file:///{logo_path_abs.replace(os.sep, '/')}" alt='rounded Image' class='roundedimage'></div>
               <div class="reference">
                 <div>{row.get('ministere','')}</div>
		         <div>{row.get('entreprise','')}</div>
		         <div>{row.get('adresse','')}</div>
		         <div>Tél : {row.get('telephone','')} | Fax : {row.get('fax','')} <br/> Email : {row.get('email','')} |  Site web : {row.get('web','')}</div>
		         <div></div>
               </div>
            </div>
		    <div class="header-right">
               <div class="title">Fiche de paie</div>
               <div class="periode">
				   <div>Periode :</div>
				   <div>{format_date_fr(row["date_du"], style="month")}</div>
				   <div>Paiement le :</div>
				   <div>{format_date_fr(row["date_paiement"], style="long")}</div>
			   </div>
               <div class="periode">
				   <div>Par :</div>
				   <div>{row["mode_paie"]}</div>
			   </div>
            </div>
	    </div>
        <div class="hr"></div>
        <div class="ref_employe">
		    <div class="ref_employe_1">
               <div class="ref_1">
				  <div>Prenom et nom :</div>
                  <div>{row.get('prenom','')} {row.get('nom','')}</div>
			   </div>
               <div class="ref_1">
				  <div>Adresse :</div>
                  <div>{row.get('adresse_e','')}</div>
			   </div>
               <div class="ref_1">
				  <div>Téléphone :</div>
                  <div>{row.get('telephone_e','')}</div>
			   </div>
               <div class="ref_1">
				  <div>Matricule :</div>
                  <div>{acronym_prenom}{acronym_nom}-{row['matricule']}</div>
			   </div>
                <div class="ref_1">
				  <div>Contrat :</div>
                  <div>{row.get('s_nature','')}</div>
			   </div>
                <div class="ref_1">
				  <div>Categorie :</div>
                  <div>{row.get('s_categorie','')}</div>
			   </div>
            </div>
		    <div class="ref_employe_1">
               <div class="ref_1">
				  <div>Poste occupe :</div>
                  <div>{row.get('s_poste_occupe','')}</div>
			   </div>
               <div class="ref_1">
				  <div>Date d'embauche :</div>
                  <div>{format_date_fr(row['s_date_embauche'],style="long")}</div>
			   </div>
               <div class="ref_1">
				  <div>Date fin de contrat :</div>
                  <div>{format_date_fr(row['s_date_sorti'],style="long")}</div>
			   </div>
               <div class="ref_1">
				  <div>Nationalité :</div>
                  <div>{row['nationalite']}</div>
			   </div>
               <div class="ref_1">
				  <div>C. Collective :</div>
                  <div>INTERPROFESSIONNELLE</div>
			   </div>
               <div class="ref_1">
				  <div>Situation Familiale :</div>
                  <div>{row.get('s_situation_matr','')}</div>
			   </div>
            </div>
            <div class="ref_employe_1">
               <div class="ref_1">
				  <div>Conjoint(es) :</div>
                  <div>{row.get('s_conjoint','')}</div>
			   </div>
               <div class="ref_1">
				  <div>Nombre d'enfants :</div>
                  <div>{row.get('s_enfant','')}</div>
			   </div>
               <div class="ref_1">
				  <div>Part TRIMF :</div>
                  <div>{row['s_nb_trimf']}</div>
			   </div>
               <div class="ref_1">
				  <div>Part IRPP :</div>
                  <div>{row['s_nb_irpp']}</div>
			   </div>
            </div>
	    </div>
        <table class='table' width='100%' border='1'>
				<tr class='th_color'>
				  <th rowspan='2'>Salaire</th>
				  <th>Salaire brut</th>
				  <th>Salaire Net</th>
				  <th>Net à payer</th>
				</tr>
				<tr class='td_color_row'>
				<td>{row["salaire_brute"]}</td>
				<td>{row["salaire_net"]}</td>
				<td>{row["salaire_net"]}</td>
				</tr>
				<tr class='th_color'>
				  <th rowspan='2'>VRS</th>
				  <th>IR</th>
				  <th>TRIMF</th>
				  <th>CFCE</th>
				</tr>
				<tr class='td_color_row'>
				<td>{row["sum_irpp"]}</td>
				<td>{row["sum_trimf"]}</td>
				<td>{row["cfce"]}</td>
				</tr>
				<tr class='th_color'>
				  <th rowspan='2'>IPRES</th>
				  <th>PS</th>
				  <th>PP</th>
				   <th></th>
				</tr>
				<tr class='td_color_row'>
				<td>{format_amount(ipress_employe)}</td>
				<td>{format_amount(ipress_patronale)}</td>
				<td></td>
				</tr>
				<tr class='th_color'>
				  <th rowspan='2'>CSS </th>
				  <th>PS</th>
				  <th>PP</th>
				   <th></th>
				</tr>
				<tr class='td_color_row'>
				<td>{row["css_allocation_familiale"]}</td>
				<td>{row["css_accident_travail"]}</td>
				<td></td>
				</tr>
				<tr class='th_color'>
				  <th rowspan='2'>RETENUE SOCIALES </th>
				  <th>AMICALES</th>
				  <th>AUTRES</th>
				   <th>TABASKI</th>
				</tr>
				<tr class='td_color_row'>
				<td>{row["s_amicale"]}</td>
				<td>{row["s_aute_cotisation"]}</td>
				<td>{row["s_tabaski"]}</td>
				</tr>
				<tr class='th_color'>
				  <th rowspan='2'>INDEMNITES NON IMPOSIBLES</th>
				  <th>AMICALES</th>
				  <th>AUTRES</th>
				   <th>TABASKI</th>
				</tr>
				<tr class='td_color_row'>
				<td>{row["ind_transport"]}</td>
				<td>{row["ind_telephone_in"]}</td>
				<td>{row["ind_autre_indemnite"]}</td>
				</tr>
			</table>
     
        {footer}

        <div class="page-break"></div>
        """

    html_content += "</body></html>"

    base_dir = os.path.dirname(os.path.abspath(__file__))
    css_path = os.path.abspath(
        os.path.join(base_dir, "..", "static", "css", "css", "fiche_paie2.css")
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
