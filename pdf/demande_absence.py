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


def format_amount(value):
    if value in (0, "0.000", None):
        return ""
    try:
        return "{:,.3f}".format(float(value)).replace(",", " ").replace(".", ",")
    except Exception:
        return str(value)


def handle(encrypted_id):
    """Génération du PDF DMT"""

    # Décryptage ID
    id_decrypte = encryptor("decrypt", encrypted_id)
    if not id_decrypte:
        abort(400, "ID invalide")

    # Requête SQL
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    sql = """
       SELECT *,demande_absence.motif AS de_motif FROM demande_absence
                    INNER JOIN contrat ON contrat.id_contrat=demande_absence.id_contrat
                    INNER JOIN employe ON employe.id_employe=contrat.id_employe
                    INNER JOIN reference ON reference.id_reference=employe.id_reference
                    WHERE demande_absence.id_demande_absence = %s
    """
    cur.execute(sql, (id_decrypte,))
    result = cur.fetchone()
    cur.close()
    conn.close()

    if not result:
        abort(404, "Déclaration Demande d'absence non trouvée")

    logo_file = result["logo"] if result.get("logo") else "image.jpg"
    logo_path = os.path.join("static", "img", "logo", logo_file)  # chemin relatif depuis ton script
    logo_path_abs = os.path.abspath(logo_path)  # chemin absolu nécessaire pour WeasyPrint

    drapeau_file = result["drapeau"] if result.get("drapeau") else "image.jpg"
    drapeau_path = os.path.join(
        "static", "img", "drapeau", drapeau_file
    )  # chemin relatif depuis ton script
    drapeau_path_abs = os.path.abspath(
        drapeau_path
    )  # chemin absolu nécessaire pour WeasyPrint
    if result['Imputable_sur_les_normaux']=="Oui" :
        croixOui="&times;"
    else:
        croixOui = ""

    if result["Imputable_sur_les_normaux"] == "Non":
        croixNon = "&times;"
    else:
        croixNon = ""

    if result["avis"] == "Oui":
        avisOui = "&times;"
    else:
        avisOui = ""

    if result["avis"] == "Non":
        avisNon = "&times;"
    else:
        avisNon = ""

    # Construction du HTML
    html_content = f"""
   <!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8" />

</head>
<body>
    <div class="page-container">
       <div class="entete">
           <div> <img src='file:///{drapeau_path_abs.replace(os.sep, '/')}' alt="rounded Image" class="roundedimage"></div>
           <div>{result['republique']}</div>
           <div>{result['devise']}</div>
           <div>**************</div>
           <div>{result['ministere']}</div>
           <div>**************</div>
           <div>{result['entreprise']}</div>
           <div> <img src='file:///{logo_path_abs.replace(os.sep, '/')}' alt="rounded Image" class="roundedimage"></div>
       </div>
        <div class="body-content">
            <div class="body-content1">
               <div>Nom et prénom de l’Agent : </div>
               <div>{result['prenom']} {result['nom']}</div>
	        </div>
            <div class="body-content1">
               <div>Date et lieu de naissance : </div>
               <div>{format_date_fr(result['date_n'], style="long")} à {result['lieu_n']}</div>
	        </div>
            <div class="body-content1">
               <div>Fonction : </div>
               <div>{result['poste_occupe']}</div>
	        </div>
            <div class="body-content1">
               <div>Supérieur hiérarchique : </div>
               <div>{result['superieur_hierarchique']}</div>
	        </div>
            <div class="body-content1">
               <div>Fonction : </div>
               <div>{result['fonction_superieur']}</div>
	        </div>
	    </div>
        <div class="demande">
             DEMANDE D’AUTORISATION D’ABSENCE
        </div>
        <div class="body-content">
            <div class="body-content1">
               <div>Motif de la demande : </div>
               <div>{result['de_motif']}</div>
	        </div>
            <div class="body-content2">
                <div><i>Durée de l’absence :</i> Période allant du</div>
                <div>{format_date_fr(result['periode_du'],style="long")}</div>
                <div>au</div>
                <div>{format_date_fr(result['periode_au'],style="long")}</div>
                <div>inclus</div>
	        </div>
            <div class="body-content3">
                <div><i>Imputable sur les normaux</i></div>
                <div>{croixOui}</div>
                <div>Oui</div>
                <div>{croixNon}</div>
                <div>Non</div>
	        </div>
            <div class="body-content1">
               <div>Si Non précisez : </div>
               <div>{result['precision_employe']}</div>
	        </div>
            <div class="body-content4">
               <div>Dakar le {format_date_fr(result['date_v'],style="long")}</div>
               <div>Signature</div>
	        </div>
            <div class="body-content5">
                <div>Avis et signature du Supérieur hiérarchique :</div>
                <div>{avisOui}</div>
                <div>Oui</div>
                <div>{avisNon}</div>
                <div>Non</div>
	        </div>
            <div class="body-content1">
               <div>Si Non précisez : </div>
               <div>{result['precision_superieur']}</div>
	        </div>
            <div class="body-content4">
               <div><u>Visa ou GRH</u><br>Observations éventuelles</div>
               <div><u>LA COORDONNATRICE</u></div>
	        </div>
	    </div>
    </div>
</body>
</html>

    """

    # Chemin absolu vers CSS
    base_dir = os.path.dirname(os.path.abspath(__file__))
    css_path = os.path.abspath(
        os.path.join(
            base_dir, "..", "static", "css", "css", "demande_absence.css"
        )
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
        headers={"Content-Disposition": f"inline; filename=dmt_{id_decrypte}.pdf"},
    )
