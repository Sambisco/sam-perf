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
       SELECT
               *,mutation.id_mutation,
               mutation.numero_mutation,
               mutation.date_mutation,
               mutation.nom_user_mutation,
           
               -- Employé source (qui quitte)
               employe.nom AS nom_employe_source,
               employe.prenom AS prenom_employe_source,
               employe.genre AS genre_source,
               contrat.poste_occupe AS poste_occupe_source,
               
               -- Employé destination (qui reçoit)
               employe_2.nom AS nom_employe_destination,
               employe_2.prenom AS prenom_employe_destination,
               employe_2.genre AS genre_destination,
               contrat_destination.poste_occupe AS poste_occupe_destination,
               -- Entreprise de l'employé source
               reference.entreprise AS entreprise_source
           
           FROM mutation
           
           -- Employé source
           INNER JOIN affectation_matiere
               ON affectation_matiere.id_affectation_matiere = mutation.id_affectation_matiere
           INNER JOIN contrat
               ON contrat.id_contrat = affectation_matiere.id_contrat
           INNER JOIN employe
               ON employe.id_employe = contrat.id_employe
           INNER JOIN reference
               ON reference.id_reference = employe.id_reference
           
           -- Employé destination
           INNER JOIN contrat AS contrat_destination
               ON contrat_destination.id_contrat = mutation.id_contrat
           INNER JOIN employe AS employe_2
               ON employe_2.id_employe = contrat_destination.id_employe
           
           WHERE mutation.id_mutation = %s
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
    if result_ref["genre_source"] == "Masculin":
        abreg_source = "M."
    else:
        abreg_source = "Mme ou Mlle"

    if result_ref["genre_destination"] == "Masculin":
        abreg_destination = "M."
    else:
        abreg_destination = "Mme ou Mlle"

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
        <title>Mutation</title>
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
				<div><strong>BORDEREAU DE MUTATION</strong></div>
                <div>Chapitre :</div>
			    <div>N° du bon de sortie :  <strong>{str(result_ref["numero"]).zfill(7)}</strong></div>
			</div>
	    </div>
     """
    query_salaire = """
        SELECT *,mutation.id_contrat AS mutation_id_contrat FROM mutation 
                INNER JOIN affectation_matiere ON affectation_matiere.id_affectation_matiere=mutation.id_affectation_matiere
                INNER JOIN detail_affectation ON affectation_matiere.id_affectation_matiere=detail_affectation.id_affectation_matiere
                INNER JOIN matiere ON matiere.id_matiere=detail_affectation.id_matiere 
                INNER JOIN categorie_article ON categorie_article.id_categorie_article=matiere.id_categorie_article 
                INNER JOIN contrat ON contrat.id_contrat=affectation_matiere.id_contrat
                INNER JOIN employe ON employe.id_employe=contrat.id_employe
                INNER JOIN reference ON reference.id_reference=employe.id_reference 
                WHERE mutation.id_mutation= %s
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
                  <td colspan="4"></td>
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
                   <strong>Prénoms et nom de l’ordonnateur des matières</strong><br><br><br><br>
               </div>
               <div><center><strong><u>Signature</u></strong></center></div>
            </div>
			<div class="certification1">
				<div><u>LE COMPTABLE DES MATIÈRES</u></div>
				<div>
                    Vu
                    A Dakar  le {format_date_fr(result_ref['date_affectation'], style="long")}
                    <!-- ESPACE -->
                    <strong>{result_ref['nom_user_affectation']}</strong>
                    <!-- ESPACE -->
                    <strong>Comptable des matières (5)</strong>
                </div>
                <div><center><strong><u>Signature</u></strong></center></div>
			</div>
			<div class="certification1">
				<div><u>LE COMPTABLE DES MATIÉRES</u></div>
				<div>
					Je, soussigné, reconnais avoir diminué mes prises en charge des matières  portées au présent bordereau d’affectation de  unités représentant une valeur de  F CFA 
                   <!-- ESPACE -->
                    A Dakar  le {format_date_fr(result_ref['date_affectation'], style="long")}
				</div>
                <div><center><strong><u>Signature du Comptable des Matiéres</u></strong></center></div>
			</div>
           <div class="certification1">
                <div><u>LE RÉCEPTIONNAIRE / MUTATION</u></div>
                <div>
                    Je, soussigné, {abreg_source} {result_ref['prenom_employe_source']} {result_ref['nom_employe_source']} 
                    {result_ref['poste_occupe_source']}, reconnais avoir remis les matières et responsabilités portées au présent bon de mutation.
                    <!-- Employé destination -->
                    Je, soussigné, {abreg_destination} {result_ref['prenom_employe_destination']} {result_ref['nom_employe_destination']} 
                    {result_ref['poste_occupe_destination']}, reconnais avoir reçu les matières et responsabilités portées au présent bon de mutation.
                    <!-- ESPACE -->
                    A Dakar, le {format_date_fr(result_ref['date_mutation'], style="long")}
                </div>
                <div> <center><strong><u>Signatures</u></strong></center></div>
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
