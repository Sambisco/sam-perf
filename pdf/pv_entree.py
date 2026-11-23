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
        SELECT *, SUM(quantite) AS quantite
        FROM pv_entree
        INNER JOIN entree ON entree.id_entree = pv_entree.id_entree
        INNER JOIN detail_entree ON entree.id_entree = detail_entree.id_entree
        INNER JOIN fournisseur ON fournisseur.id_fournisseur = pv_entree.id_fournisseur
        INNER JOIN reference ON reference.id_reference = fournisseur.id_reference
        WHERE pv_entree.id_entree = %s
    """,
        (id_decrypte,),
    )
    result_ref = cursor.fetchone()
    cursor.close()
    conn.close()

    # Si aucune donnée → on ne crée PAS de PDF
    if not result_ref:
        return None

    fields_essentiels = ["fournisseur", "numero", "date_entree", "quantite"]
    if any(not result_ref.get(f) for f in fields_essentiels):
        return None  # pas de PDF si champs essentiels vides
    # Chemins CSS / static
    base_dir = os.path.dirname(os.path.abspath(__file__))
    css_path = os.path.join(base_dir, "..", "static", "css", "css", "pv.css")
    static_dir = os.path.join(base_dir, "..", "..", "static")

    # Logo
    logo_file = result_ref.get("logo") or "image.jpg"
    logo_path_abs = os.path.abspath(os.path.join("static", "img", "logo", logo_file))

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
    <head><meta charset="UTF-8"><title>PV reception</title></head>
    <body>
        <div class="header">
            <img src="file:///{logo_path_abs.replace(os.sep, '/')}" alt="">
            <div class="header1">
                <div>{result_ref.get('republique','')}</div>
                <div>{result_ref.get('devise','')}</div>
                <div>{result_ref.get('ministere','')}</div>
            </div>
            <div class="header2">
                <div><strong>N°______MFFPAI/DC/PF2E/Raf</strong></div>
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
                <div>Dakar, le</div>
                <div>N° de reception : <strong>{str(result_ref.get("numero","0")).zfill(7)}</strong></div>
            </div>
        </div>
        <div class="titre-dotation">PROCÉS VERBAL DE RÉCÉPTION</div>
        <div class="content">
            DATE DE RECEPTION : le {format_date_fr(result_ref.get("date_entree"), style="long")}<br>
            NOM ET QUALITES DU FOURNISSEUR : {result_ref.get('fournisseur','')}<br>
            NOMS ET QUALITES DES MEMBRES DE LA COMMISSION : <br><br>
            Abdoul Hamid SY Président <br><br><br><br><br><br>
            Amadou Fall Canar DIOP Membre <br><br><br><br><br><br>
            Malamine Bara SECK Membre (secrétaire de séance)<br><br><br><br><br><br>
            <i>Arrêté le présent P.V. à {result_ref.get('quantite',0)} T que nous certifions avoir réceptionnées</i><br><br><br><br><br><br>
            Visa du Coordonnatrice du PF2E<br><br><br><br><br><br><br><br>
            Enumération des pièces justificatives jointes (1)<br><br><br><br><br><br>
        </div>
        <div class="content2">
            <div><i>(1) Pièces justificatives jointes :</i></div>
            <div>
                <i>1 Facture n° BL {result_ref.get('numero_bon','')} du {format_date_fr(result_ref.get("date_entree"),style="long")}</i><br>
                <i>2 Bon de livraison N° BL {result_ref.get('numero_bon','')} du {format_date_fr(result_ref.get("date_entree"),style="long")}</i>
            </div>
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
            "Content-Disposition": f"inline; filename=pv_entree_{id_decrypte}.pdf"
        },
    )
