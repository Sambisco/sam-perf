from flask import Response, abort
from weasyprint import HTML, CSS
from templates.include.connect import get_connection
from templates.include.encryptor import encryptor
from datetime import datetime, date
import locale, os
from babel.dates import format_date

# Locale française
try:
    locale.setlocale(locale.LC_TIME, "fr_FR.UTF-8")
except locale.Error:
    locale.setlocale(locale.LC_TIME, "")


def format_date_fr(date_obj, style="long"):
    """Formate une date en français"""
    if not date_obj:
        return ""
    if isinstance(date_obj, str):
        try:
            date_obj = datetime.strptime(date_obj, "%Y-%m-%d")
        except Exception:
            return ""
    fmt = {
        "full": "EEEE d MMMM yyyy",
        "month": "MMMM yyyy",
        "years": "yyyy",
        "long": "dd MMMM yyyy",
    }.get(style, "dd MMMM yyyy")
    return format_date(date_obj, format=fmt, locale="fr_FR").capitalize()


def handle(encrypted_id):
    id_decrypte = encryptor("decrypt", encrypted_id)
    if not id_decrypte:
        abort(400, "ID invalide")

    # Connexion DB
    conn = get_connection()
    cursor = conn.cursor(dictionary=True, buffered=True)

    # Requête principale
    cursor.execute(
        """
        SELECT * FROM dotation 
        INNER JOIN contrat ON contrat.id_contrat=dotation.id_contrat
        INNER JOIN employe ON employe.id_employe=contrat.id_employe
        INNER JOIN reference ON reference.id_reference=employe.id_reference
        WHERE dotation.id_dotation = %s
    """,
        (id_decrypte,),
    )
    result_ref = cursor.fetchone()
    cursor.close()
    conn.close()

    # Si aucune donnée → on ne crée PAS de PDF
    if not result_ref:
        return None

    # Chemins CSS / static
    base_dir = os.path.dirname(os.path.abspath(__file__))
    css_path = os.path.join(base_dir, "..", "static", "css", "css", "pv.css")
    static_dir = os.path.join(base_dir, "..", "..", "static")

    # Logo
    logo_file = result_ref.get("logo") or "image.jpg"
    logo_path_abs = os.path.abspath(os.path.join("static", "img", "logo", logo_file))

    if result_ref["genre"] == "Masculin":
        abreg = "M."
    else:
        abreg = "Mme ou Mlle"

    # Footer
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

    # HTML PDF
    html_content = f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head><meta charset="UTF-8"><title>PV dotation</title></head>
    <body>
        <div class="header">
            <img src="file:///{logo_path_abs.replace(os.sep, '/')}" alt="">
            <div class="header1">
                <div>{result_ref.get('republique','')}</div>
                <div>{result_ref.get('devise','')}</div>
                <div>{result_ref.get('ministere','')}</div>
            </div>
            <div class="header2">
                <div><strong>N°______MFPAI/DC/PF2E/cm</strong></div>
                <div>Instruction générale</div>
                <div>Année financière : {format_date_fr(result_ref.get("date_entree"), style="years")}</div>
            </div>
        </div>
        <div class="sous-header">
            <div class="sous-header1">
                <div>{result_ref.get('entreprise','')}</div>
                <div>{result_ref.get('adresse','')}</div>
                <div>Tel : {result_ref.get('telephone','')} | Fax : {result_ref.get('fax','')} | BP : {result_ref.get('bp','')}</div>
                <div>Site web : {result_ref.get('web','')} | Email: {result_ref.get('email','')}</div>
            </div>
            <div class="sous-header2">
                <div style="font-size:8pt;"><strong>COMPTABILITE DES MATIERES</strong></div>
                <div>Dakar, le</div>
                <div>N° de dotation : <strong>{str(result_ref.get("numero","0")).zfill(7)}</strong></div>
            </div>
        </div>
        <div class="titre-dotation">DOTATION DE CARBURANT</div>
        <div class="content">
            Je soussigné(e) : {abreg} {result_ref['prenom']} {result_ref['nom']} <br><br>
            Fonction : {result_ref['poste_occupe']} <br><br>
            Véhicule : {result_ref['vehicule']} <br><br>
            Immatriculation : {result_ref['immatriculation']} <br><br>
            Date : {format_date_fr(result_ref.get("date_dotation"), style="long")}<br><br>
            Période du : {format_date_fr(result_ref.get("periode_du"), style="long")}<br><br>
            Période au : {format_date_fr(result_ref.get("periode_au"), style="long")}<br><br>
            Motif : {result_ref.get('motif','')}<br><br>
            Lieu : {result_ref.get('lieu','')}<br><br>
            Quantité : {result_ref['carburant']} Litres
        </div>
        <br><br><br><br><br><br><br><br><br>
        <div class="content2">
           En foi de quoi, le présent PV est délivré pour servir et valoir ce que de droit.
        </div>
        <br><br><br><br><br><br><br><br><br>
        <div class="content3">
			<div>Le Bénéficiaire</div>
			<div>Agent comptable des matières</div>
		</div>

        {footer}
        <div class="page-break"></div>
    </body>
    </html>
    """

    # Génération PDF
    pdf = HTML(string=html_content, base_url=static_dir).write_pdf(
        stylesheets=[CSS(css_path)]
    )

    return Response(
        pdf,
        mimetype="application/pdf",
        headers={
            "Content-Disposition": f"inline; filename=pv_dotation_{id_decrypte}.pdf"
        },
    )
