from flask import Response, abort
from weasyprint import HTML, CSS
from templates.include.connect import get_connection
from templates.include.encryptor import encryptor
import locale
from datetime import datetime, date
import os
from babel.dates import format_date

# Locale française
try:
    locale.setlocale(locale.LC_TIME, "fr_FR.UTF-8")
except locale.Error:
    locale.setlocale(locale.LC_TIME, "")


def format_date_fr(date_str, style="long"):
    try:
        if not date_str:
            return ""

        if isinstance(date_str, (datetime, date)):
            dt = date_str
        else:
            dt = datetime.strptime(date_str, "%Y-%m-%d")

        fmt = {
            "full": "EEEE d MMMM yyyy",
            "month": "MMMM yyyy",
            "years": "yyyy",
            "long": "dd MMMM yyyy",
        }.get(style, "dd MMMM yyyy")

        return format_date(dt, format=fmt, locale="fr_FR").capitalize()
    except Exception:
        return ""


def get_acronym(name):
    import re

    name_clean = re.sub(r"\b[\w][\'`‘’]\b", "", name)
    words = name_clean.split()
    return "".join([w[0].upper() for w in words])


def format_amount(value, decimals=0):
    if value in (0, "0.000", None):
        return "-"
    try:
        value = round(float(value), decimals)
        fmt = "{:,.{prec}f}".format(value, prec=decimals)
        return fmt.replace(",", " ").replace(".", ",")
    except Exception:
        return str(value)


def handle(encrypted_id):
    id_decrypte = encryptor("decrypt", encrypted_id)
    if not id_decrypte:
        abort(400, "ID invalide")

    conn = get_connection()
    cursor = conn.cursor(dictionary=True, buffered=True)  # ✅ buffered=True

    # 1) Récupération des infos référence/entreprise
    query_ref = """
        SELECT * FROM detail_affectation 
        INNER JOIN affectation_matiere ON affectation_matiere.id_affectation_matiere=detail_affectation.id_affectation_matiere 
        INNER JOIN contrat ON contrat.id_contrat=affectation_matiere.id_contrat
        INNER JOIN employe ON employe.id_employe=contrat.id_employe
        INNER JOIN matiere ON matiere.id_matiere=detail_affectation.id_matiere 
        INNER JOIN categorie_article ON categorie_article.id_categorie_article=matiere.id_categorie_article 
        INNER JOIN reference ON reference.id_reference=categorie_article.id_reference
        WHERE affectation_matiere.id_affectation_matiere = %s
    """
    cursor.execute(query_ref, (id_decrypte,))
    result_ref = cursor.fetchone()

    if not result_ref:
        cursor.close()
        conn.close()
        return "Aucune donnée trouvée", 404

    logo_file = result_ref.get("logo") or "image.jpg"
    logo_path_abs = os.path.abspath(os.path.join("static", "img", "logo", logo_file))

    # 2) Récupération des salaires
    if result_ref["genre"] == "Masculin":
        abreg = "M."
    else:
        abreg = "Mme ou Mlle"

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
    # 3) Préparation HTML
    html_content = f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <title>Affectation</title>
    </head>
    <body>
        <div class="header">
			<img src="file:///{logo_path_abs.replace(os.sep, '/')}" alt="">
			<div class="header1">
               <div>{result_ref['republique']}</div>
			   <div>{result_ref['devise']}</div>
			   <div>{result_ref['ministere']}</div>
			</div>
			<div class="header2">
				<div>Art ,52b, 69</div>
			    <div>Instruction générale</div>
			    <div>Année budgetaire : {format_date_fr(result_ref["date_affectation"], style="years")}</div>
			</div>
	    </div>
        <div class="sous-header">
			<div class="sous-header1">
               <div>{result_ref['entreprise']}</div>
               <div>{result_ref['adresse']}</div>
			   <div>Tel : {result_ref['telephone']} | Fax : {result_ref['fax']} | BP : {result_ref['bp']}</div>
			   <div>Site web : {result_ref['web']} | Email: {result_ref['email']}</div>
			</div>
			<div class="sous-header2">
				<div><strong>BORDEREAU D’AFFECTATION</strong></div>
                <div>Chapitre :</div>
			    <div>N° du bon de sortie :  <strong>{str(result_ref["numero"]).zfill(7)}</strong></div>
			</div>
	    </div>
     """
    query_salaire = """
        SELECT * FROM detail_affectation 
        INNER JOIN affectation_matiere ON affectation_matiere.id_affectation_matiere=detail_affectation.id_affectation_matiere 
        INNER JOIN contrat ON contrat.id_contrat=affectation_matiere.id_contrat
        INNER JOIN employe ON employe.id_employe=contrat.id_employe
        INNER JOIN matiere ON matiere.id_matiere=detail_affectation.id_matiere 
        INNER JOIN categorie_article ON categorie_article.id_categorie_article=matiere.id_categorie_article 
        INNER JOIN reference ON reference.id_reference=categorie_article.id_reference
        WHERE affectation_matiere.id_affectation_matiere = %s
    """
    cursor.execute(query_salaire, (id_decrypte,))
    rows = cursor.fetchall()

    html_content += """
        <table class="table table_product" width="100%" border="1">
            <thead>
                <tr class="header1">
                   <td></td>
                   <td></td>
                   <td colspan="2">DESIGNATION DES MATIERES</td>
                   <td colspan="4">CHIFFRES A COMPTABILISER</td>
                   <td></td>
               </tr>
                <tr class="header2">
                    <td  rowspan="2">#</td>
                    <td rowspan="2"> N° Compte nomenclature</td>
                    <td rowspan="2">Nature des Matières</td>
                    <td rowspan="2">Code d’immatriculation</td>
                    <td colspan="2" style="height:20px;">Quantite</td>
                    <td rowspan="2">Prix unitaire</td>
                    <td rowspan="2">Montant</td>
                    <td rowspan="2">Observations</td>
                </tr>
                <tr class="header3">
                    <td style="width: 8%;font-size: 8pt;">Nombre d’unités</td>
                    <td style="width: 9%;font-size: 8pt;">Nature des unités-3</td>
                </tr>
            </thead>
            <tbody>
        """

    for idx, row in enumerate(rows, 1):
        html_content += f"""
            <tr>
                <td>{idx}</td>
                <td></td>
                <td>{row['designation']}</td>
                <td></td>
                <td>{row['quantite']}</td>
                <td>{row['nature_unite']}</td>
                <td></td>
                <td></td>
                <td style="font-size: 8pt;">{row['observation']}</td>
            </tr>
           """
    html_content += f"""
            </tbody>
            <tfoot>
              <tr>
                  <td colspan="3"></td>
                  <td>TOTAUX</td>
                  <td>{format_amount(result_ref['total'])}</td>
                  <td colspan="4" style="border-right: solid 1px #fff;"></td>
              </tr>
           </tfoot>
    </table>
    <div class="certification">
			<div class="certification1">
				<div><u>L’ORDONNATEUR DES MATIÈRES</u></div>
				<div>
                   Vu et approuvé,
                   A Dakar  le {format_date_fr(result_ref['date_affectation'], style="long")}
                    <!-- ESPACE -->
                   <strong>Prénoms et nom de l’ordonnateur des matières</strong>
               </div>
               <div><strong><u>Signature</u></strong></div>
            </div>
			<div class="certification1">
				<div><u>LE COMPTABLE DES MATIÈRES</u></div>
				<div>
                    Vu
                    A Dakar  le {format_date_fr(result_ref['date_affectation'], style="long")}
                     <!-- ESPACE -->
                    <strong>{result_ref['nom_user_affectation']}</strong>
                    <strong>Comptable des matières (5)</strong>
                </div>
                <div><strong><u>Signature</u></strong></div>
			</div>
			<div class="certification1">
				<div><u>LE COMPTABLE DES MATIÉRES</u></div>
				<div>
					Je, soussigné, reconnais avoir diminué mes prises en charge des matières  portées au présent bordereau d’affectation de  unités représentant une valeur de  F CFA 
                    A Dakar  le {format_date_fr(result_ref['date_affectation'], style="long")}
				</div>
                <div><strong><u>Signature du Comptable des Matiéres</u></strong></div>
			</div>
            <div class="certification1">
				<div><u>LE RÉCEPTIONNAIRE</u></div>
				<div>
					Je, soussigné, {abreg} {result_ref['prenom']} {result_ref['nom']} {result_ref['poste_occupe']}
                    reconnais avoir reçu les matières portées au présent bordereau d’affectation
                    A Dakar  le {format_date_fr(result_ref['date_affectation'], style="long")}
                    {abreg} {result_ref['prenom']} {result_ref['nom']} {result_ref['poste_occupe']} réceptionnaire détenteur de  matières
				</div>
                <div><strong><u>Signature du réceptionnaire détenteur de matières</u></strong></div>
			</div>
		</div>
        {footer}
    <div class="page-break"></div>
    </body>
    </html>
    """

    cursor.close()
    conn.close()

    base_dir = os.path.dirname(os.path.abspath(__file__))
    css_path = os.path.abspath(
        os.path.join(base_dir, "..", "static", "css", "css", "style_gs_s.css")
    )
    static_dir = os.path.abspath(os.path.join(base_dir, "..", "..", "static"))

    pdf = HTML(string=html_content, base_url=static_dir).write_pdf(
        stylesheets=[CSS(css_path)]
    )

    return Response(
        pdf,
        mimetype="application/pdf",
        headers={
            "Content-Disposition": f"inline; filename=bon_sortie_{id_decrypte}.pdf"
        },
    )
