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
        <title>Bulletin de salaire</title>
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
               <div class="title">bulletin de paie</div>
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
				<th rowspan='2' class='th_color1' style='border-left:solid 1px #000;'>N°</th>
				<th rowspan='2' class='th_color2'>LIBELLE RUBRIQUE</th>
				<th rowspan='2' class='th_color3'>BASE</th>
				<th colspan='3' class='th_color4'>Part salarié</th>
				<th colspan='2' class='th_color4' style='border-right:solid 1px #000;'>Part Patronale</th>
			</tr>
			<tr class='th_color'>
				<td class='th_sous_color1'>Taux</td>
				<td class='th_sous_color2'>Gains</td>
				<td class='th_sous_color3'>Retenues</td>
				<td class='th_sous_color4'>Taux</td>
				<td class='th_sous_color5' style='border-right:solid 1px #000;'>Cotisations</td>
			</tr>
            <tr>
				<td class='border'></td>
				<td class='border' style='padding-left:5px'>Salaire de base</td>
				<td class='border' style='text-align:center'>{row['salaire_base']}</td>
				<td class='border'></td>
				<td class='border' style='text-align:center'>{row['salaire_base']}</td>
				<td class='border'></td>
				<td class='border'></td>
				<td class='border'></td>
			</tr>
			<tr class='td_color'>
				<td class='border'></td>
				<td class='border' style='padding-left:5px'>Heures Supplementaires 15%</td>
				<td class='border'></td>
				<td class='border'></td>
				<td class='border'></td>
				<td class='border'></td>
				<td class='border'></td>
				<td class='border'></td>
			</tr>
				<tr>
					<td class='border'></td>
					<td class='border' style='padding-left:5px'>Heures Supplementaires 40%</td>
					<td class='border'></td>
					<td class='border'></td>
					<td class='border'></td>
					<td class='border'></td>
					<td class='border'></td>
					<td class='border'></td>
				</tr>
				<tr class='td_color'>
					<td class='border'></td>
					<td class='border' style='padding-left:5px'>Heures Supplementaires 60%</td>
					<td class='border'></td>
					<td class='border'></td>
					<td class='border'></td>
					<td class='border'></td>
					<td class='border'></td>
					<td class='border'></td>
				</tr>
				<tr>
					<td class='border'></td>
					<td class='border' style='padding-left:5px'>Heures Supplementaires 100%</td>
					<td class='border'></td>
					<td class='border'></td>
					<td class='border'></td>
					<td class='border'></td>
					<td class='border'></td>
					<td class='border'></td>
				</tr>
				<tr class='td_color'>
					<td class='border'></td>
					<td class='border' style='padding-left:5px'>Sursalaire</td>
					<td class='border' style='text-align:center'>{row["ind_sursalaire"]}</td>
					<td class='border'></td>
					<td class='border' style='text-align:center'>{row["ind_sursalaire"]}</td>
					<td class='border'></td>
					<td class='border'></td>
					<td class='border'></td>
				</tr>
				<tr>
					<td class='border'></td>
					<td class='border' style='padding-left:5px'>Indemnite de fonction</td>
					<td class='border' style='text-align:center'>{row["ind_fonction"]}</td>
					<td class='border'></td>
					<td class='border' style='text-align:center'>{row["ind_fonction"]}</td>
					<td class='border'></td>
					<td class='border'></td>
					<td class='border'></td>
				</tr>
				<tr class='td_color'>
					<td class='border'></td>
					<td class='border' style='padding-left:5px'>Retenue pour absence (Heures)</td>
					<td class='border'></td>
					<td class='border'></td>
					<td class='border'></td>
					<td class='border'></td>
					<td class='border'></td>
					<td class='border'></td>
				</tr>
				<tr>
					<td class='border'></td>
					<td class='border' style='padding-left:5px'>Indemnite de responsabilites</td>
					<td class='border' style='text-align:center'>{row["ind_responsabilite"]}</td>
					<td class='border'></td>
					<td class='border' style='text-align:center'>{row["ind_responsabilite"]}</td>
					<td class='border'></td>
					<td class='border'></td>
					<td class='border'></td>
				</tr>
				<tr class='td_color'>
					<td class='border'></td>
					<td class='border' style='padding-left:5px'>Indemnite de sujetion</td>
					<td class='border' style='text-align:center'>{row["ind_sujetion"]}</td>
					<td class='border'></td>
					<td class='border' style='text-align:center'>{row["ind_sujetion"]}</td>
					<td class='border'></td>
					<td class='border'></td>
					<td class='border'></td>
				</tr>
				<tr>
					<td class='border'></td>
					<td class='border' style='padding-left:5px'>Indemnites de logements</td>
					<td class='border' style='text-align:center'>{row["ind_logement"]}</td>
					<td class='border'></td>
					<td class='border' style='text-align:center'>{row["ind_logement"]}</td>
					<td class='border'></td>
					<td class='border'></td>
					<td class='border'></td>
				</tr>
				<tr class='th_color'>
					<td class='border' style='border-left:solid 1px #000'></td>
					<td class='border' style='padding-left:5pxfont-weight: 600'>Salaire Brut</td>
					<td class='border'></td>
					<td class='border'></td>
					<td class='border' style='text-align:center;font-weight: 600;'>{row["salaire_brute"]}</td>
					<td class='border'></td>
					<td class='border'></td>
					<td class='border' style='border-right:solid 1px #000'></td>
				</tr>
				<tr>
					<td class='border' style='text-align:center'>IP RG</td>
					<td class='border' style='padding-left:5px'>IPRES Régime Général</td>
					<td class='border'></td>
					<td class='border' style='text-align:center'>5,6%</td>
					<td class='border'></td>
					<td class='border' style='text-align:center'>{row["iprg_employe"]}</td>
					<td class='border' style='text-align:center'>8,4%</td>
					<td class='border' style='text-align:center'>{row["irprg_patronale"]}</td>
				</tr>
				<tr class='td_color'>
					<td class='border' style='text-align:center'>IP RC</td>
					<td class='border' style='padding-left:5px'>IPRES Régime Cadre</td>
					<td class='border'></td>
					<td class='border' style='text-align:center'>2,4%</td>
					<td class='border' style='text-align:center'></td>
					<td class='border' style='text-align:center'>{row["irpc_employe"]}</td>
					<td class='border' style='text-align:center'>3,6%</td>
					<td class='border' style='text-align:center'>{row["irpc_patronale"]}</td>
				</tr>
				<tr>
					<td class='border' style='text-align:center'>CSS</td>
					<td class='border' style='padding-left:5px'>CSS - Accident travail</td>
					<td class='border'></td>
					<td class='border'></td>
					<td class='border'></td>
					<td class='border'></td>
					<td class='border' style='text-align:center'>1,0%</td>
					<td class='border' style='text-align:center'>{row["css_accident_travail"]}</td>
				</tr>
				<tr class='td_color'>
					<td class='border' style='text-align:center'>CSS</td>
					<td class='border' style='padding-left:5px'>CSS - Allocation familiale</td>
					<td class='border'></td>
					<td class='border' style='text-align:center'></td>
					<td class='border' style='text-align:center'></td>
					<td class='border'></td>
					<td class='border' style='text-align:center'>7,0%</td>
					<td class='border' style='text-align:center'>{row["css_allocation_familiale"]}</td>
				</tr>
				<tr>
					<td class='border' style='text-align:center'>TRIMF</td>
					<td class='border' style='padding-left:5px'>TRIMF (Impôt du minimum fiscal)</td>
					<td class='border'></td>
					<td class='border' style='text-align:center'> {row["s_nb_trimf"]}</td>
					<td class='border'></td>
					<td class='border' style='text-align:center'>{row["sum_trimf"]}</td>
					<td class='border'></td>
					<td class='border'></td>
				</tr>
				<tr class='td_color'>
					<td class='border' style='text-align:center'>IRPP</td>
					<td class='border' style='padding-left:5px'>IRPP (Impôt sur le revenu)</td>
					<td class='border'></td>
					<td class='border' style='text-align:center'>{row["s_nb_irpp"]}</td>
					<td class='border' style='text-align:center'></td>
					<td class='border' style='text-align:center'>{row["sum_irpp"]}</td>
					<td class='border'></td>
					<td class='border'></td>
				</tr>
				<tr>
					<td class='border'></td>
					<td class='border' style='padding-left:5px'>Cotisation amicale</td>
					<td class='border'></td>
					<td class='border'></td>
					<td class='border'></td>
					<td class='border' style='text-align:center'>{row["s_amicale"]}</td>
					<td class='border'></td>
					<td class='border'></td>
				</tr>
				<tr class='td_color'>
					<td class='border'></td>
					<td class='border' style='padding-left:5px'>Autre</td>
					<td class='border'></td>
					<td class='border'></td>
					<td class='border'></td>
					<td class='border' style='text-align:center'>{row["s_aute_cotisation"]}</td>
					<td class='border'></td>
					<td class='border'></td>
				</tr>
				<tr >
					<td class='border'></td>
					<td class='border' style='padding-left:5px'>Retenue Tabaski</td>
					<td class='border'></td>
					<td class='border'></td>
					<td class='border'></td>
					<td class='border' style='text-align:center'>{row["s_tabaski"]}</td>
					<td class='border'></td>
					<td class='border'></td>
				</tr>
				<tr class='td_color'>
					<td class='border'></td>
					<td class='border' style='padding-left:5px'>CFCE</td>
					<td class='border'></td>
					<td class='border'></td>
					<td class='border'></td>
					<td class='border'></td>
					<td class='border' style='text-align:center'>3%</td>
					<td class='border' style='text-align:center'>{row["cfce"]}</td>
				</tr>
				<tr>
					<td class='border'></td>
					<td class='border' style='padding-left:5px'>Assurance Complément</td>
					<td class='border'></td>
					<td class='border'></td>
					<td class='border'></td>
					<td class='border'></td>
					<td class='border' style='text-align:center'></td>
					<td class='border' style='text-align:center'></td>
				</tr>
				<tr class='td_color'>
					<td class='border'></td>
					<td class='border' style='padding-left:5px'>IPM</td>
					<td class='border'></td>
					<td class='border'></td>
					<td class='border'></td>
					<td class='border'></td>
					<td class='border' style='text-align:center'></td>
					<td class='border' style='text-align:center'></td>
				</tr>
				<tr>
					<td class='border'></td>
					<td class='border' style='padding-left:5px'>Acompte / Avance</td>
					<td class='border'></td>
					<td class='border'></td>
					<td class='border' style='text-align:center'></td>
					<td class='border'></td>
					<td class='border'></td>
					<td class='border'></td>
				</tr>
				<tr class='td_color'>
					<td class='border'></td>
					<td class='border' style='padding-left:5px'>Remboursement sur prêt</td>
					<td class='border'></td>
					<td class='border'></td>
					<td class='border'></td>
					<td class='border'></td>
					<td class='border'></td>
					<td class='border'></td>
				</tr>
				<tr>
					<td class='border'></td>
					<td class='border' style='padding-left:5px'>Avantages en nature</td>
					<td class='border'></td>
					<td class='border'></td>
					<td class='border' style='text-align:center'></td>
					<td class='border'></td>
					<td class='border'></td>
					<td class='border'></td>
				</tr>
				<tr class='td_color'>
					<td class='border'></td>
					<td class='border' style='padding-left:5px'>Divers</td>
					<td class='border'></td>
					<td class='border'></td>
					<td class='border'></td>
					<td class='border'></td>
					<td class='border'></td>
					<td class='border'></td>
				</tr>
				<tr class='th_color'>
					<td class='border' style='border-left:solid 1px #000'></td>
					<td class='border' style='padding-left:5pxfont-weight: 600'>Total des retenues</td>
					<td class='border'></td>
					<td class='border'></td>
					<td class='border'></td>
					<td class='border' style='text-align:center;font-weight: 600;'>{row["total_retenue_employe"]}</td>
					<td class='border'></td>
					<td class='border' style='border-right:solid 1px #000;text-align:center;font-weight: 600'>{row["total_retenue_patronale"]}</td>
				</tr>
				<tr>
					<td class='border'></td>
					<td class='border' style='padding-left:5px'>Décision n°</td>
					<td class='border'></td>
					<td class='border'></td>
					<td class='border'></td>
					<td class='border'></td>
					<td class='border'></td>
					<td class='border'></td>
				</tr>
				<tr class='td_color'>
					<td class='border'></td>
					<td class='border' style='padding-left:5px'>Indemnités de Transport</td>
					<td class='border'></td>
					<td class='border'></td>
					<td class='border' style='text-align:center'>{row["ind_transport"]}</td>
					<td class='border'></td>
					<td class='border'></td>
					<td class='border'></td>
				</tr>
				<tr>
					<td class='border'></td>
					<td class='border' style='padding-left:5px'>Indemnités pour frais telephonique</td>
					<td class='border'></td>
					<td class='border'></td>
					<td class='border' style='text-align:center'>{row["ind_telephone_in"]}</td>
					<td class='border'></td>
					<td class='border'></td>
					<td class='border'></td>
				</tr>
				<tr class='td_color'>
					<td class='border'></td>
					<td class='border' style='padding-left:5px'>Autres</td>
					<td class='border'></td>
					<td class='border'></td>
					<td class='border' style='text-align:center'>{row["ind_autre_indemnite"]}</td>
					<td class='border'></td>
					<td class='border'></td>
					<td class='border'></td>
				</tr>
				<tr class='th_color'>
					<td class='border' style='border-left:solid 1px #000;'></td>
					<td class='border' style='padding-left:5pxfont-weight: 600'>Total des primes</td>
					<td class='border'></td>
					<td class='border'></td>
					<td class='border' style='text-align:center;font-weight: 600'>{row["total_prime"]}</td>
					<td class='border'></td>
					<td class='border'></td>
					<td class='border' style='border-right:solid 1px #000;text-align:center;font-weight: 600'></td>
				</tr>
				<tr>
					<td class=noleftnoright colspan='8' ' style='height:2px'></td>
				</tr>
				<tr class='th_color'>
					<td class='border' style='border-left:solid 1px #000;text-align:center;'>Cumuls</td>
					<td class='border' style='padding-left:5px;text-align:center'>TOTAL BRUT</td>
					<td class='border' style='text-align:center'>Salaire Net	</td>
					<td class='border'  style='text-align:center' colspan='2' >Charges salariales</td>
					<td class='border' style='text-align:center' colspan='2'>
						Charges Patronales	
					</td>
					<td class='border'  style='text-align:center;border-right:solid 1px #000;'>NET A PAYER</td>
				</tr>
				<tr>
					<td class='border' style='text-align:center'>Mois</td>
					<td class='border'  style='text-align:center'>{row["salaire_brute"]}</td>
					<td class='border'  style='text-align:center'>{row["retenue_cotisation"]}</td>
					<td class='border'  style='text-align:center'   colspan='2'>{row["total_retenue_employe"]}</td>
					<td class='border' style='text-align:center'  colspan='2'>{row["total_retenue_patronale"]}</td>
					<td class='border'  style='text-align:center'>{row["salaire_net"]}</td>
				</tr>
				<tr class='td_color'>
					<td class='border' style='text-align:center'>Année</td>
					<td class='border' style='padding-left:5px;text-align:center'>{row["salaire_brute_annuel"]}</td>
					<td class='border'></td>
					<td class='border'   colspan='2'></td>
					<td class='border' style='text-align:center'  colspan='2'></td>
					<td class='border'></td>
				</tr>
				<tr>
					<td class='border th_color' style='text-align:center;border-left:solid 1px #000;border-bottom:solid 1px #fff;'></td>
					<td class='border th_color'  style='text-align:center;border-bottom:solid 1px #fff;'>Indemnité de conge</td>
					<td class='border th_color'  style='text-align:center;border-bottom:solid 1px #fff;border-right:solid 1px #444;'>{row["ind_indemnite_conge"]}</td>
					<td class='border'  style='text-align:center'   colspan='2'></td>
					<td class='border th_color' style='text-align:center;border-bottom:solid 1px #fff;'  colspan='2'>Intervalle congé en mois</td>
					<td class='border th_color'  style='text-align:center;border-bottom:solid 1px #fff;border-right:solid 1px #000;'>{row["months"]}</td>
				</tr>
				<tr class='td_color'>
					<td class='border th_color' style='text-align:center;border-left:solid 1px #000;border-bottom:solid 1px #fff;'></td>
					<td class='border th_color' style='text-align:center;border-bottom:solid 1px #fff;'>Indemnité de conge supplém.</td>
					<td class='border th_color'  style='text-align:center;border-bottom:solid 1px #fff;border-right:solid 1px #444;'>{row["ind_indemnite_conge_supplementaire"]}</td>
					<td class='border'   colspan='2'></td>
					<td class='border th_color' style='text-align:center;border-bottom:solid 1px #fff;'  colspan='2'>Jours de congé </td>
					<td class='border th_color' style='text-align:center;border-right:solid 1px #000;border-bottom:solid 1px #fff;'>{row["nbr_conge"]}</td>
				</tr>
				<tr>
					<td class='border th_color' style='text-align:center;border-left:solid 1px #000;border-bottom:solid 1px #000;'></td>
					<td class='border th_color'  style='text-align:center;border-bottom:solid 1px #000;'>Indemnité fin de contrat</td>
					<td class='border th_color'  style='text-align:center;border-bottom:solid 1px #000;border-right:solid 1px #444;'></td>
					<td class='border'  style='text-align:center'   colspan='2'></td>
					<td class='border th_color' style='text-align:center;border-bottom:solid 1px #000;'  colspan='2'>Jours de congé supplém.</td>
					<td class='border th_color'  style='text-align:center;border-bottom:solid 1px #000;border-right:solid 1px #000;'>{row["nbr_conge_supplementaire"]}</td>
				</tr>
        </table>
       <div class='emegerment'>
			<div>Ce bulletin de paie doit être conservé sans limitation de durée</div>
			<div>Emargement</div>
		</div>
        {footer}

        <div class="page-break"></div>
        """

    html_content += "</body></html>"

    base_dir = os.path.dirname(os.path.abspath(__file__))
    css_path = os.path.abspath(
        os.path.join(base_dir, "..", "static", "css", "css", "bulletin_pdf.css")
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
