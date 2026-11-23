from flask import Response, abort
from weasyprint import HTML, CSS
from templates.include.connect import get_connection
from templates.include.encryptor import encryptor
import locale
from datetime import datetime, date, timedelta
import os
from babel.dates import format_date

# Forcer locale FR pour les dates
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
        SELECT * FROM dmt
        INNER JOIN contrat ON contrat.id_contrat = dmt.id_contrat
        INNER JOIN employe ON employe.id_employe = contrat.id_employe
        INNER JOIN reference ON reference.id_reference = employe.id_reference
        WHERE dmt.id_dmt = %s
    """
    cur.execute(sql, (id_decrypte,))
    result = cur.fetchone()
    cur.close()
    conn.close()

    if not result:
        abort(404, "Déclaration DMT non trouvée")

    # Immatriculation fictive
    immat = "856084183678"
    output = ""
    for i in range(len(immat)):
        output += f"<div>{immat[i]}</div>"
    embauche_licencie = "embauche_licencie"
    heure_heure = " heure_heure"
    # Construction du HTML
    html_content = f"""
   <!DOCTYPE html>
<html lang="fr">
	<head>
		<meta charset="UTF-8" />
		<title>DMT</title>
	</head>
	<body>

		<div class="page-container">
			<div class="div1">
				<div class="div1-left">
					<h6>DECLARATION DE MOUVEMENT DU TRAVAILLEUR</h6>
					<div class="sous-div1-left1">
						<div>N°</div>
						<div></div>
						<div>du</div>
						<div></div>
					</div>
					<div class="sous-div1-left2">REFERENCES</div>
					<div class="sous-div1-left3">
						Article 193 (Alinéas 2, 3, 4 ) du Code du travail (loi n° 61-34 du 15 juin
						1961)<br />
						Arrêté ministériel n° 7301 du 17 mai 1963 déterminant les modalités des
						<br />
						déclarations de mouvement de travailleurs (J.O. 22 juin 1963, p 825)<br />
					</div>
				</div>
				<div class="div1-right">
					<h6>Cachet et raison sociale de l'employeur</h6>
				</div>
			</div>
            <div class="div2">
                <div class="div2-left">
                    N° d'immatriculation du travailleur au fichier <br/> de la main-d'œuvre 
				</div>
				<div class="div2-right">
			        <div class="div2-right1">
				       <div></div>
				       <div></div>
				       <div></div>
				       <div></div>
				       <div></div>
				       <div></div>
				       <div></div>
				       <div></div>
				       <div></div>
				       <div></div>
				       <div></div>
				       <div></div>
				       <div></div>
				       <div></div>
				       <div></div>
			        </div>
			        <div class="div2-right2">
				       { output}
				       <div></div>
				       <div></div>
				       <div></div>
			        </div>
                    <div class="div2-right3">
						<div>A</div>
						<div>B</div>
						<div>C</div>
						<div>D</div>
						<div>E</div>
						<div>F</div>
                    </div>
		        </div>
	        </div>
            <div class="div3">
				<div class="div3-left">
                   <div class="div3-left1"><strong>OBJET DE LA PRESENTE DECLARATION</strong></div>
                   <div class="div3-left2">
                      <div><span class="{embauche_licencie}">- Embauchage</span></div>
                      <div><span class="{""}">- Licenciement</span></div>
                    </div>
                    <div class="div3-left3">
                       - Expiration normale du contrat <br>
                       - Démission - Mutation <br>
                       - Changement de catégorie professionnelle <br>
                       - Modification du contrat de travail <br>
                       - Changement de situation de famille <br>
                       - Changement de résidence habituelle <br>
                       - Changement d'emploi - Décès
                    </div>
				</div>
				<div class="div3-right">
                   <div>(Rayer les mentions inutiles et encadrer la mention valable <br> à compléter éventuellement dans le blanc ci-dessous)</div>
                   <div><strong>IMMATRICULATION</strong></div>
                   <div>
                   <br/><br/>
                        Si le travailleur n'a pas encore été immatriculé, la mention
                        "Immatriculation" devra être portée dans le blanc ci-dessus
                   </div>
				</div>
			</div>
            <div class="div4"><strong>CONCERNANT LE TRAVAILLEUR</strong></div>
            <div class="div5">
		    	<div>Nom :</div>
		    	<div>{result["nom"]}</div>
		    	<div>Prénom :</div>
		    	<div>{result["prenom"]}</div>
		    	<div>Sexe :</div>
		    	<div>{result["genre"]}</div>
		    </div>
            <div class="div6">
		    	<div>Née le </div>
		    	<div>{format_date_fr(result["date_n"], style="long")}</div>
		    	<div>à</div>
		    	<div>{result["lieu_n"]}</div>
		    	<div>Pays</div>
		    	<div>{result["pays"]}</div>
		    	<div>Nationalité</div>
		    	<div>{result["nationalite"]}</div>
		    </div>
            <div class="div7">
		    	<div>Fils ou Fille de (père)</div>
		    	<div>{result["nom_pere"]}</div>
		    	<div>et de (mère)</div>
		    	<div>{result["nom_mere"]}</div>
		    	<div>Groupe ethnique</div>
		    	<div>{result["groupe_ethnique"]}</div>
		    </div>
            <div class="div8">
		    	<div>Adresse (très précise):</div>
		    	<div>{result["adresse_e"]}</div>
		    </div>
            <div class="div9">
			    <div>Carte d'identité n°</div>
			    <div>{result["cin_e"]}</div>
			    <div>délivrée à</div>
			    <div>{result["délivrée_cin_a"]}</div>
			    <div>le</div>
			    <div>{format_date_fr(result["délivrée_cin_le"],style="long")}</div>
		    </div>
            <div class="div10">
			    <div>Par</div>
			    <div><strong>DIRECTION GENERALE DE LA SURETE NATIONALE</strong></div>
		    </div>
            <div class="div11">
			    <div>N° d'immatriculation à la C.C.P.E. - A.T</div>
			    <div>{result["ccpe_at"]}</div>
			    <div>N° d'immatriculation à l'A.G.R.O.M</div>
			    <div>{result["agrom"]}</div>
		    </div>
            <div class="div12">
			    <div>Situation de famille ( Célibataire - marié(e) - divorcé(e) - veuf(ve) )</div>
			    <div>{result["situation_matr"]}</div>
		    </div>
            <div class="div13">
			    <div>Nombre de conjoint(es) :</div>
			    <div>{result["conjoint"]}</div>
			    <div>Nombre d'enfants à charge :</div>
			    <div>{result["enfant"]}</div>
		    </div>
            <div class="div14">
			    <div>Nom conjoint(es) :</div>
			    <div>{result["nom_conjoint"]}</div>
		    </div>
            <div class="div15">
			    <div>Noms des enfants à charge :</div>
			    <div>{result["nom_enfant"]}</div>
		    </div>
            <div class="div16">
			    <div>Date d'entrée dans l'établissement :</div>
			    <div>{format_date_fr(result["date_embauche"],style="long")}</div>
		    </div>
            <div class="div17">
			    <div>N° et date de la déclaration d'embauche effectuée lors de l'engagement :</div>
			    <div></div>
		    </div>
            <div class="div18">
			    <div>Profession :</div>
			    <div>{result["poste_occupe"]}</div>
			    <div>Emploi dans l'établissement :</div>
			    <div><strong>PF2E</strong></div>
		    </div>
            <div class="div18">
			    <div>Convention collective :</div>
			    <div><strong>INTERPROFESSIONNELLE</strong></div>
			    <div>Catégorie :</div>
			    <div>{result["categorie"]}</div>
		    </div>
            <div class="div16">
			    <div>Eventuellement date du contrat :</div>
			    <div></div>
		    </div>
            <div class="div16">
			    <div>N° et date du visa d'approbation par l'inspecteur du travail et de la sécurité sociale :</div>
			    <div></div>
		    </div>
            <div class="div18">
			    <div>N° et date du visa d'enregistrement à la section locale de :</div>
			    <div></div>
			    <div>du service de la main d'œuvre</div>
			    <div></div>
		    </div>
            <div class="div16">
			    <div>Raison sociale et adresse précise de l'établissement de l'employeur : </div>
			    <div><strong>SOTRAC MERMOZ PYROTECHNIQUE</strong></div>
		    </div>
            <div class="div16">
			    <div>Activité de l'établissement : </div>
			    <div><strong>FORMATION PROFESSIONNELLE</strong></div>
		    </div>
            <div class="separateur"> </div>
            <div class="div19">
			    <div class="left">
                   <div>Durée du contrat :</div>
                   <div><strong>- à durée déterminée</strong></div>
                   <div>- ou à durée indéterminée</div>
                   <div>(Rayer la mention inutile et encadrer la mention)</div>
                </div>
			    <div class="right">
                    <div class="right1">
                      <strong>DETERMINEE</strong>
                    </div>
                    <div class="right2">
                       <div>DU</div>
			           <div class="right2-2">{format_date_fr(result["date_embauche"],style="long")}</div>
			           <div>AU</div>
			           <div class="right2-2">{format_date_fr(result["date_sorti"],style="long")}</div>
                    </div>
                    <div class="right3">
                       <div>Chantier de</div>
			           <div class="right3-3"></div>
                    </div>
                </div>
		    </div>
             <div class="separateur"> </div>
             <br/> <br/> <br/>
             <div class="div16">
			    <div>Nom et adresse du précedent employeur </div>
			    <div></div>
		    </div>
            <div class="div16">
			    <div>Si le travailleur bénéficie de l'article 107 du Code de Travail : </div>
		    </div>
            <div class="div18">
			    <div>-Lieu de résidence habituelle du travailleur : </div>
			    <div></div>
			    <div>Date d'entrée au Sénégal :</div>
			    <div></div>
		    </div>
        </div>

		<div class="page-container page-break">
            <div class="div20">
			     <h6>STATUT MILITAIRE</h6>
			     <p>(Rayer les mentions inutiles)</p>
            </div>
            <div class="div16">
			    <div>- Classe de recrutement : </div>
			    <div></div>
		    </div>
            <div class="div16">
			    <div>- L'intéressé a-t-il effecué son service militaire ?</div>
			    <div></div>
		    </div>
            <div class="div16">
			    <div>- Armée d'appartenance : terre - air - mer :</div>
			    <div></div>
		    </div>
            <div class="div16">
			    <div>- Grade dans la réserve : Officer - Sous-officer - Troupe :</div>
			    <div></div>
		    </div>
            <div class="div21">
			     <div>DISPOSITIONS PARTICULIERES CONCERNANT L'ENGAGEMENT :</div>
			     <div>(auquelles les partie ont expressément souscrit)</div>
            </div>
            <div class="div22">
			     <div>1) - Le salaire du travailleur sera celui fixé pour la catégorie <br>  en fonction d'un horaire de travail hebdomadaire de</div>
			     <div><strong>3. 2</strong> de la Convention Collective : <strong>INTERPROFESSIONNELLE</strong></div>
            </div>
             <div class="div23">
			     <div><span class="{heure_heure}">40 heures</span></div>
			     <div><span class="{""}">42 heures</span></div>
                 <div><span class="{""}">45 heures</span></div>
                 <div><span class="{""}">48 heures</span></div>
            </div>
            <div class="div16">
			    <div>Soit :</div>
			    <div></div>
		    </div>
            <div class="div24">
			    <div>2)</div>
			    <div>3)</div>
                <div>4)</div>
                <div>5)</div>
		    </div>
            <div class="div25">
			    <div>Signature du travailleur <br/>(précédée de la mention manuscrite "pour accord")</div>
			    <div>Signature de l'employeur</div>
            </div>
            
            <div class="div26">
			    <strong>P.S. - N.B. : 1) </strong> La déclaration de mouvement du travailleur est à établir en trois exemplaires dûment signés par l'employeur et le <br>
                travailleur. Un exemplaire est remis au travailleur. Le second est conservé par l'employeur. Le troisième est déposé : <br>
                dans l'intérieur de la section locale du Service de la Main-d'œuvre à l'Inspection du Travail et de la Sécurité Sociale du ressort <br>
                à DAKAR au Bureau central du Service de la Main-d'oeuvre <br>
                2) L'employeur doit OBLIGATOIREMENT délivrer une ampliation de la déclaration du mouvement du travailleur <br>
                3) Sont provisoirement exemptes de la déclaration de mouvement <br>
                - Les travailleurs journaliers effectivement payés tous les jours <br>
                - Les manœuvres ordinaires dans toutes les branches d'activité
            </div>
		</div>

	</body>
</html>

    """

    # Chemin absolu vers CSS
    base_dir = os.path.dirname(os.path.abspath(__file__))
    css_path = os.path.abspath(
        os.path.join(base_dir, "..", "static", "css", "css", "dmt.css")
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
