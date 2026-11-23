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


def handle(encrypted_id, encrypted_id_ref):
    id_decrypte = encryptor("decrypt", encrypted_id)
    id_decrypte_id_ref = encryptor("decrypt", encrypted_id_ref)
    if not id_decrypte or not id_decrypte_id_ref:
        abort(400, "ID invalide")

    conn = get_connection()
    cursor = conn.cursor(dictionary=True, buffered=True)  # ✅ buffered=True

    # 1) Récupération des infos référence/entreprise
    query_ref = """
        SELECT * FROM sortie_externe
        INNER JOIN reference ON reference.id_reference=sortie_externe.id_reference
        WHERE sortie_externe.id_sortie_externe = %s
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
        <title>Sortie</title>
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
				<div>Art 12a, 12c, 19a</div>
			    <div>Instruction générale</div>
			    <div>Année budgétaire : {format_date_fr(result_ref["date_sortie"], style="years")}</div>
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
				<div><strong>BON DE SORTIE DEFINITIVE DE L’EXISTANT</strong></div>
			    <div>Section :</div>
                <div>Chapitre :</div>
			    <div>N° du bon de sortie :  <strong>{str(result_ref["numero"]).zfill(7)}</strong></div>
			</div>
	    </div>
     """
    query_salaire = """
        SELECT * FROM detail_sortie_externe
           INNER JOIN sortie_externe ON sortie_externe.id_sortie_externe=detail_sortie_externe.id_sortie_externe
           INNER JOIN matiere ON matiere.id_matiere=detail_sortie_externe.id_matiere
           WHERE sortie_externe.id_sortie_externe=%s
    """
    cursor.execute(query_salaire, (id_decrypte,))
    rows = cursor.fetchall()

    html_content += """
        <table class="table table_product" width="100%" border="1">
            <thead>
              <tr class="header1">
                 <td></td>
                 <td></td>
                 <td></td>
                 <td></td>
                 <td></td>
                 <td colspan="2">DESIGNATION DES MATIERES</td>
                 <td colspan="4">CHIFFRES A COMPTABILISER</td>
                 <td></td>
                 </tr>
                 <tr class="header2">
                 <td  rowspan="2">#</td>
                 <td colspan="4"> N° Compte nomenclature-2</td>
                 <td rowspan="2">Nature des Matières</td>
                 <td rowspan="2">Spécification</td>
                 <td colspan="2" style="height:20px;">Quantite</td>
                 <td rowspan="2">Prix unitaire</td>
                 <td rowspan="2">Montant</td>
                 <td rowspan="2">Observations</td>
                 </tr>
                 <tr class="header3">
                 <td style="font-size: 8pt;padding-left: 5px;padding-right: 5px;text-align: center;">Groupe</td>
                 <td style="font-size: 8pt;padding-left: 5px;padding-right: 5px;text-align: center;">Compte principal </td>
                 <td style="font-size: 8pt;padding-left: 5px;padding-right: 5px;text-align: center;">Compte divisionnaire </td>
                 <td style="font-size: 8pt;padding-left: 5px;padding-right: 5px;text-align: center;">Sous compte</td>
                 <td style="font-size: 8pt;padding-left: 5px;padding-right: 5px;text-align: center;">Nombre d’unités</td>
                 <td style="font-size: 8pt;padding-left: 5px;padding-right: 5px;text-align: center;">Nature des unités-3</td>
             </tr>
            </thead>
            <tbody>
        """
    sous_total_montant = 0
    annee = format_date_fr(result_ref["date_sortie"], style="years")
    for idx, row in enumerate(rows, 1):

        id_matiere = row["id_matiere"]
        query_salaire = """
           SELECT * FROM detail_entree 
           INNER JOIN entree ON entree.id_entree=detail_entree.id_entree 
           INNER JOIN matiere ON matiere.id_matiere=detail_entree.id_matiere 
           INNER JOIN categorie_article ON categorie_article.id_categorie_article=matiere.id_categorie_article 
           INNER JOIN reference ON reference.id_reference=categorie_article.id_reference
           WHERE reference.id_reference = %s AND matiere.id_matiere=%s  AND DATE_FORMAT(date_entree,'%Y') = %s ORDER BY detail_entree.id_detail_entree DESC LIMIT 1
        """
        cursor.execute(query_salaire, (id_decrypte_id_ref, id_matiere, annee,))
        rows_prix = cursor.fetchone()
        prix = rows_prix["prix_unitaire"] if rows_prix else 0
        montant = float(row["quantite"]) * float(prix)
        sous_total_montant += montant

        html_content += f"""
             <tr>
                 <td>{idx}</td>
                 <td></td>
                 <td></td>
                 <td></td>
                 <td></td>
                 <td>{row['designation']}</td>
                 <td></td>
                 <td>{row['quantite']}</td>
                 <td>{row['nature_unite']}</td>
                 <td>{format_amount(prix)}</td>
                 <td>{format_amount(montant)}</td>
                 <td>{row['observation']}</td>
             </tr>
           """
    html_content += f"""
            </tbody>
            <tfoot>
              <tr>
                  <td colspan="6"></td>
                  <td>TOTAUX</td>
                  <td>{format_amount(result_ref['total'])}</td>
                  <td colspan="2"></td>
                  <td>{format_amount(sous_total_montant)}</td>
                  <td></td>
              </tr>
           </tfoot>
    </table>
    <div class="certification">
			<div class="certification1">
				<div><u>CERTIFICATION</u></div>
				<div>
                  Arrêté le présent bon à {format_amount(result_ref['total'])} unité représentant une valeur de…………………………………francs dont je certifie la sortie définitive.
                 <!-- ESPACE -->
                  A Dakar  le {format_date_fr(result_ref['date_sortie'], style="long")}
                  <strong>L’Ordonnateur des matières (5)</strong>
               </div>
            </div>
			<div class="certification1">
				<div><u>DIMINUTION DES PRISES EN CHARGE</u></div>
				<div>
                    Le comptable des matières, soussigné, déclare ce jour, diminuer mes prises en charge de {format_amount(result_ref['total'])} unité représentant une valeur de .Francs.
                    <!-- ESPACE -->
                    A Dakar  le {format_date_fr(result_ref['date_sortie'], style="long")}
                    <strong>Le Comptable des matières (5)</strong>
                </div>
			</div>
			<div class="certification1">
				<div><u>RECEPISSE</u></div>
				<div>
					Je, soussigné, M.| Mme ou Mlle {result_ref['nom_complet_externe']} 
                    reconnais avoir reçu les matières portées au présent bon.
                    <!-- ESPACE -->
                    A Dakar  le {format_date_fr(result_ref['date_sortie'], style="long")}
                    <strong>Le Réceptionnaire (5)</strong>
				</div>
			</div>
            <div class="certification1">
				<div style="color:#fff;"><u>RECEPISSE</u></div>
				<div>
					(1) Numérotation ininterrompue pour la gestion 
                    (2) Dans l’ordre des articles décrits sur les pièces justificatives ou dans l’ordre des comptes de la nomenclature.
                    (3) Litre, kg, mètre, nombre etc.
                    (4) Nom et qualité
                    (5) Timbre et signature
                    <strong>Bon à établir en 03 exemplaires</strong>
				</div>
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
