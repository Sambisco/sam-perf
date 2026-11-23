from flask import Response, abort
from templates.include.connect import get_connection
from templates.include.encryptor import encryptor
from datetime import datetime, date, timedelta
import locale
import re
from weasyprint import HTML as WHTML
import os
from babel.dates import format_date

try:
    locale.setlocale(locale.LC_TIME, "fr_FR.UTF-8")
except locale.Error:
    locale.setlocale(locale.LC_TIME, "")

# ---------------------------
# Utils
# ---------------------------


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


def compute_duree(start, end):
    if not start or not end:
        return ""
    if isinstance(start, str):
        start = datetime.datetime.strptime(start, "%Y-%m-%d")
    if isinstance(end, str):
        end = datetime.datetime.strptime(end, "%Y-%m-%d")

    try:
        from dateutil.relativedelta import relativedelta

        rd = relativedelta(end, start)
        return f"{rd.years} ans {rd.months} mois {rd.days} jours"
    except ImportError:
        diff = abs((end - start).days)
        years = diff // 365
        months = (diff % 365) // 30
        days = diff % 365 % 30
        return f"{years} ans {months} mois {days} jours"


def fmt_num(val, decimals=0):
    try:
        num = float(val)
    except (TypeError, ValueError):
        return ""
    formatted = f"{num:,.{decimals}f}".replace(",", " ").replace(".", ",")
    if decimals == 0:
        formatted = formatted.replace(",00", "")
    return formatted


def apply_replacements(text, replacement_dict):
    def repl_word(match):
        word = match.group(0)  # mot capturé
        value = replacement_dict.get(word, word)  # prend la valeur sinon garde le mot
        return str(value)  # ✅ toujours une chaîne

    return re.sub(r"\w+", repl_word, text)


# ---------------------------
# Handler principal
# ---------------------------


def handle(encrypted_id):
    # 1. Décryptage de l'ID
    id_decrypte = encryptor("decrypt", encrypted_id)
    if not id_decrypte:
        abort(400, "ID invalide")

    # 2. Connexion SQL
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    query = """
          SELECT *, indemnite.fonction AS fonction, indemnite.sujetion AS sujetion,
               indemnite.responsabilite AS responsabilite, indemnite.sursalaire AS sursalaire,
               indemnite.logement AS logement, indemnite.transport AS transport,
               indemnite.telephone_in AS telephone_in, indemnite.document_lettre AS document_lettre_indemnite
        FROM indemnite
        INNER JOIN contrat ON contrat.id_contrat = indemnite.id_contrat
        INNER JOIN employe ON employe.id_employe = contrat.id_employe
        INNER JOIN reference ON reference.id_reference = employe.id_reference
        WHERE indemnite.id_indemnite = %s
    """
    cursor.execute(query, (id_decrypte,))
    rows = cursor.fetchall()

    if not rows:
        abort(404, "attestation non trouvée")

    row = rows[0]

    # 3. Dictionnaire des remplacements
    repl = {
        "nom_employe": (
            f"{row['prenom']} {row['nom']}" if row["prenom"] and row["nom"] else ""
        ),
        "poste_occupe": row["poste_occupe"] or "",
        "numero_compte": (row["compte"] or "").upper(),
        "budget_annuel": str(row["annee_budget"])[:4] if row["annee_budget"] else "",
        "date_enregistrement": format_date_fr(row["date_enregistrement"], style="full"),
        "date_effet": format_date_fr(row["date_effet"], style="full"),
        "montant_salaire_en_lettre": row.get("salaire_lettre", ""),
        "montant_salaire_en_chiffre": fmt_num(row["salaire"], 0),
        "indemnite_fonction": fmt_num(row["fonction"], 0),
        "indemnite_sujetion": fmt_num(row["sujetion"], 0),
        "indemnite_responsablilite": fmt_num(row["responsabilite"], 0),
        "indemnite_sursalaire": fmt_num(row["sursalaire"], 0),
        "indemnite_logement": fmt_num(row["logement"], 0),
        "indemnite_transport": fmt_num(row["transport"], 0),
        "indemnite_telephone": fmt_num(row["telephone_in"], 0),
    }

    # 4. Contenu TinyMCE (HTML brut)
    html_content = row.get("document_lettre_indemnite") or ""

    # ✅ Conversion des <span style="page-break-before: always;"> en <div class="page-break">
    html_content = re.sub(
        r"<span[^>]*?page-break-before\s*:\s*always;?[^>]*?></span>",
        '<div class="page-break"></div>',
        html_content,
        flags=re.IGNORECASE,
    )

    # 5. CSS global pour le PDF
    css = """
    <style>
    @page { size: A4; margin: 2cm; }
    body {
        margin: 0;
        font-family: Arial, sans-serif;
        font-size: 12pt;
    }
    img {
        width: 80px; /* limite max */
        height: auto;
        page-break-inside: avoid;
    }
    .page-break {
        display: block;
        page-break-before: always;
        height: 1px;
        margin: 0;
        border: none;
    }
    #footer {
        position: fixed;
        bottom: -1.5cm;
        border-top:1px solid #ccc;
        font-size:10px;
        color:gray;
        text-align:center;
        padding-top:5px;
        background:white;
	    width: 100%;
    }
    #footer div:nth-child(2) {
	font-weight: 600;
 }
    .page-break-after { page-break-after: always; }
    </style>
    """

    # 6. Footer avec infos entreprise
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

    # 7. Assemblage du HTML
    html_doc = f"""
    <html>
      <head>
        <meta charset="utf-8">
        {css}
      </head>
      <body>
        {html_content}
        {footer}
      </body>
    </html>
    """

    # 8. Remplacement des placeholders {{...}}
    filled_html = apply_replacements(html_doc, repl)

    # 9. base_url : pour résoudre les images TinyMCE relatives
    base_url = "https://ton-domaine.com/"
    # ou en local : base_url = os.path.join(os.getcwd(), "static")

    # 10. Génération du PDF
    pdf = WHTML(string=filled_html, base_url=base_url).write_pdf()

    # Fermeture SQL
    cursor.close()
    conn.close()

    # 11. Retour HTTP PDF
    return Response(
        pdf,
        mimetype="application/pdf",
        headers={
            "Content-Disposition": f"inline; filename=demande_indemnite_{id_decrypte}.pdf"
        },
    )
