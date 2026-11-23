from flask import Flask, render_template, request, redirect, session, url_for, jsonify
from flask_session import Session
from flask_mail import Mail
from datetime import datetime, timezone, date
from zoneinfo import ZoneInfo  # Python 3.9+
import os
import locale
from templates.include.encryptor import encryptor

# === Import de la resoussours humaines ===
from controller.login import login
from controller.mail_recup import mail_recup_handler
from controller.update_password import update_password
from controller.login_employe import login_employe
from controller.mail_recup_portail import mail_recup_portail_handler
from controller.update_password_portail import update_password_portail
from controller.user.fetch_user import fetch_user
from controller.user.save import save_user
from controller.region.fetch_region import fetch_region
from controller.region.save import save_region
from controller.departement.fetch_departement import fetch_departement
from controller.departement.save import save_departement
from controller.employe.fetch_employe import fetch_employe
from controller.employe.fetch_portail import fetch_portail
from controller.employe.save import save_employe
from controller.import_export.upload.upload_employe import save_import_files
from controller.import_export.import_employe import save_import_employe
from controller.select_ajax.select_ajax import fetch_select_ajax
from controller.contrat.fetch_contrat import fetch_contrat
from controller.document_administratif.fetch_all_document_administratif import (
    fetch_all_document_administratif,
)
from controller.document_administratif.fetch_document_administratif import (
    fetch_document_administratif,
)
from controller.document_administratif.save import save_document_administratif
from controller.contrat.save import save_contrat
from controller.dmt.fetch_dmt import fetch_dmt
from controller.dmt.save import save_dmt
from controller.employe.fetch_show_employe import fetch_show_employe
from controller.reference.fetch_reference import fetch_reference
from controller.reference.save import save_reference
from controller.reference.fetch_reference_detailed import fetch_reference_detailed
from controller.depart.fetch_depart import fetch_depart
from controller.depart.save import save_depart
from controller.attestation_travail.fetch_attestation_travail import (
    fetch_attestation_travail,
)
from controller.attestation_travail.save import save_attestation_travail
from controller.certificat_travail.fetch_certificat_travail import (
    fetch_certificat_travail,
)
from controller.certificat_travail.save import save_certificat_travail
from controller.domiciliation_salaire.fetch_domiciliation_salaire import (
    fetch_domiciliation_salaire,
)
from controller.domiciliation_salaire.save import save_domiciliation_salaire
from controller.affectation.fetch_affectation import fetch_affectation
from controller.affectation.save import save_affectation
from controller.indemnite.fetch_indemnite import fetch_indemnite
from controller.indemnite.save import save_indemnite
from controller.conge_annuel.fetch_conge_annuel import fetch_conge_annuel
from controller.conge_annuel.save import save_conge_annuel
from controller.conge_maternite.fetch_conge_maternite import fetch_conge_maternite
from controller.conge_maternite.save import save_conge_maternite
from controller.cotisation.fetch_cotisation import fetch_cotisation
from controller.cotisation.save import save_cotisation
from controller.salaire.fetch_calcul import fetch_calcul
from controller.paie_conge_annuel.fetch_calcul_conge_annuel import (
    fetch_calcul_conge_annuel,
)
from controller.paie_conge_annuel.fetch_paie_conge_annuel import fetch_paie_conge_annuel
from controller.salaire.fetch_salaire import fetch_salaire
from controller.salaire.save import save_salaire
from controller.paie_conge_annuel.save import save_paie_conge_annuel
from controller.paie_conge_maternite.fetch_calcul_conge_maternite import (
    fetch_calcul_conge_maternite,
)
from controller.paie_conge_maternite.fetch_paie_conge_maternite import (
    fetch_paie_conge_maternite,
)
from controller.paie_conge_maternite.save import save_paie_conge_maternite
from controller.demande_absence.fetch_demande_absence import fetch_demande_absence
from controller.demande_absence.save import save_demande_absence
from controller.absence.fetch_absence import fetch_absence
from controller.absence.save import save_absence
from controller.pointage.fetch_pointage import fetch_pointage
from controller.pointage.suivi_pointage import suivi_pointage
from controller.pointage.save import save_pointage
from controller.pointage.reconnaissance_facial import reconnaissance_facial
from controller.dashboard.donnee import dashboard_rh
from controller.dashboard.statistique import statistique_rh
from controller.dashboard.tableau import tableau_rh
from controller.dashboard.notification import notification_rh
from controller.employe.enroll import enroll

# === Import de la gestion des matiéres ===

from controller_g.categorie.fetch_categorie import fetch_categorie
from controller_g.categorie.save import save_categorie
from controller_g.import_export.upload.upload_gstock import save_import_files_g
from controller_g.import_export.import_categorie import save_import_categorie
from controller_g.import_export.import_matiere import save_import_matiere
from controller_g.select_ajax.select_ajax import fetch_select_ajax_g
from controller_g.matiere.fetch_matiere import fetch_matiere
from controller_g.matiere.save import save_matiere
from controller_g.fournisseur.fetch_fournisseur import fetch_fournisseur
from controller_g.fournisseur.save import save_fournisseur
from controller_g.entree.fetch_entree import fetch_entree
from controller_g.entree.save import save_entree
from controller_g.sortie.fetch_sortie import fetch_sortie
from controller_g.sortie.save import save_sortie
from controller_g.affectation.fetch_affectation import fetch_affectation_m
from controller_g.affectation.save import save_affectation_m
from controller_g.mutation.fetch_mutation import fetch_mutation
from controller_g.mutation.save import save_mutation
from controller_g.dotation.fetch_dotation import fetch_dotation
from controller_g.dotation.save import save_dotation
from controller_g.reception.fetch_reception import fetch_reception
from controller_g.reception.save import save_reception_carburant
from controller_g.dashboard.donnee import dashboard_gs
from controller_g.dashboard.statistique import statistique_gs
from controller_g.dashboard.tableau import tableau_gs
# === PDF handlers ===
from pdf import (
    bulletin_fiche_paie,
    curriculum,
    contrat,
    dmt,
    depart,
    attestation_travail,
    certificat_travail,
    domiciliation_salaire,
    affectation,
    indemnite,
    conge_annuel,
    conge_maternite,
    absence,
    bulletin,
    bulletin2,
    fiche_paie,
    fiche_paie_employe,
    demande_absence,
    document_demande,
    entree,
    pv_entree,
    entree_pv_entree,
    sortie,
    sortie_externe,
    affectation_matiere,
    mutation_matiere,
    dotation,
    pv_reception,
)

# === Flask App ===
app = Flask(__name__)

app.config["MAX_CONTENT_LENGTH"] = 200 * 1024 * 1024
# Configuration session
app.secret_key = os.urandom(24)
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_FILE_DIR"] = os.path.join(app.instance_path, "flask_session")
Session(app)

# Configuration Mail
app.config.update(
    MAIL_SERVER="smtp.hostinger.com",
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_USERNAME="",
    MAIL_PASSWORD="",
    MAIL_DEFAULT_SENDER="",
    MAIL_DEBUG=True,
)
mail = Mail(app)

# Définir la locale française
try:
    locale.setlocale(locale.LC_TIME, "fr_FR.UTF-8")
except locale.Error:
    print("⚠️ Locale fr_FR.UTF-8 non disponible")


# === VARIABLES GLOBALES INJECTÉES DANS LES TEMPLATES ===
@app.context_processor
def inject_global_vars():
    profil = session.get("profil") or None
    result = session.get("result") or {}
    image_reference = session.get("image_reference") or None
    result_reference = session.get("result_reference") or {}

    now_utc = datetime.now(timezone.utc)
    now_fr = now_utc.astimezone(ZoneInfo("Europe/Paris"))
    date_fr = now_fr.strftime("%A %d %B %Y à %Hh%M")

    current_date = date.today().isoformat()
    mois_actuel = date.today().strftime("%Y-%m")
    date_dashboard = datetime.now().year
    mois_actuel_nombre = datetime.now().month
    current_timestamp = int(datetime.now(timezone.utc).timestamp())

    return dict(
        profil=profil,
        result=result,
        result_reference=result_reference,
        image_reference=image_reference,
        current_year=now_fr.year,
        date_fr=date_fr,
        current_date=current_date,
        mois_actuel=mois_actuel,
        date_dashboard=date_dashboard,
        mois_actuel_nombre=mois_actuel_nombre,
        current_timestamp=current_timestamp,
    )


# === ROUTES PUBLIQUES ===
@app.route("/")
def index():
    message = session.pop("message_delete", None)
    return render_template("index.html", message=message)


@app.route("/register")
def register():
    return render_template("register.html")


@app.route("/email_recupe")
def email_recupe():
    msg_delete = session.pop("message_delete", None)
    msg_succes = session.pop("message_sucess", None)
    return render_template(
        "email_recupe.html", message_delete=msg_delete, message_sucess=msg_succes
    )


@app.route("/mail_recup", methods=["GET", "POST"])
def mail_recup():
    return mail_recup_handler(mail)


@app.route("/initialise_password")
def initialise_password():
    code = request.args.get("code")
    if not code:
        return "Code manquant", 400
    message = session.pop("message_sucess", None)
    return render_template(
        "initialise_password.html", email=code, message_sucess=message
    )


@app.route("/update_password", methods=["POST"])
def update_password_route():
    return update_password()


@app.route("/login", methods=["GET", "POST"])
def login_route():
    return login()


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


# === Décorateur de protection login ===
def login_required(func):
    from functools import wraps

    @wraps(func)
    def decorated_function(*args, **kwargs):
        if not session.get("id_m"):
            return redirect(url_for("login_route"))
        return func(*args, **kwargs)

    return decorated_function


@app.route("/portail")
def portail():
    message = session.pop("message_delete", None)
    return render_template("portail.html", message=message)


@app.route("/logout_emp")
def logout_emp():
    session.clear()
    return redirect(url_for("portail"))


@app.route("/controller/login_employe", methods=["GET", "POST"])
def login_employe_route():
    return login_employe()


@app.route("/email_recupe_portail")
def email_recupe_portail():
    msg_delete = session.pop("message_delete", None)
    msg_succes = session.pop("message_sucess", None)
    return render_template(
        "email_recupe_portail.html",
        message_delete=msg_delete,
        message_sucess=msg_succes,
    )


@app.route("/mail_recup_portail", methods=["GET", "POST"])
def mail_recup_portail():
    return mail_recup_portail_handler(mail)


@app.route("/initialise_password_portail")
def initialise_password_portail():
    # Ton code pour cette page, comme afficher un formulaire pour réinitialiser le mot de passe
    code = request.args.get("code")
    if not code:
        return "Code manquant", 400
    message = session.pop("message_sucess", None)
    return render_template(
        "initialise_password_portail.html", email=code, message_sucess=message
    )


@app.route("/update_password_portail", methods=["POST"])
def update_password_portail_route():
    return update_password_portail()


@app.route("/employe/dashboard_emp")
def dashboard_emp():
    # Vérifie si l'utilisateur est connecté (si les IDs sont dans la session)
    if "id_contrat" not in session or "id_employe" not in session:
        return redirect(
            url_for("portail")
        )  # Redirige vers la page de connexion si non connecté

    # Récupère les IDs directement depuis la session
    id_contrat = session["id_contrat"]
    id_employe = session["id_employe"]
    my_logo = session["logo"]
    matricule = session["matricule"]
    # Décryptage des identifiants stockés dans la session

    # Passer ces IDs au template pour affichage
    return render_template(
        "employe/dashboard_emp.html",
        id_contrat=id_contrat,
        id_employe=id_employe,
        my_logo=my_logo,
        matricule=matricule,
    )


@app.route("/controller/employe/fetch_portail", methods=["POST"])
def fetch_portail_route():
    return fetch_portail()


# === ROUTES AJAX ===


@app.route("/controller/user/fetch_user", methods=["POST"])
def route_fetch_user():
    return fetch_user()


@app.route("/controller/user/save", methods=["POST"])
def route_save_user():
    return save_user()


@app.route("/controller/reference/fetch_reference", methods=["POST"])
def route_fetch_reference():
    return fetch_reference()


@app.route("/controller/reference/fetch_reference_detailed", methods=["POST"])
def route_fetch_reference_detailed():
    return fetch_reference_detailed()


@app.route("/controller/reference/save", methods=["POST"])
def route_save_reference():
    return save_reference()


@app.route("/controller/region/fetch_region", methods=["POST"])
def route_fetch_region():
    return fetch_region()


@app.route("/controller/region/save", methods=["POST"])
def route_save_region():
    return save_region()


@app.route("/controller/departement/fetch_departement", methods=["POST"])
def route_fetch_departement():
    return fetch_departement()


@app.route("/controller/departement/save", methods=["POST"])
def route_save_departement():
    return save_departement()


@app.route("/controller/employe/fetch_employe", methods=["POST"])
def route_fetch_employe():
    return fetch_employe()


@app.route("/controller/employe/save", methods=["POST"])
def route_save_employe():
    return save_employe()


@app.route("/controller/import_export/upload/upload_employe", methods=["POST"])
def route_save_import_files():
    return save_import_files()


@app.route("/controller/import_export/import_employe", methods=["POST"])
def route_save_import_employe():
    return save_import_employe()


@app.route("/controller/select_ajax/select_ajax", methods=["POST"])
def route_fetch_select_ajax():
    return fetch_select_ajax()


@app.route(
    "/controller/document_administratif/fetch_all_document_administratif",
    methods=["POST"],
)
def route_fetch_all_document_administratif():
    return fetch_all_document_administratif()


@app.route(
    "/controller/document_administratif/fetch_document_administratif", methods=["POST"]
)
def route_fetch_document_administratif():
    return fetch_document_administratif()


@app.route("/controller/document_administratif/save", methods=["POST"])
def route_save_document_administratif():
    return save_document_administratif()


@app.route("/controller/contrat/fetch_contrat", methods=["POST"])
def route_fetch_contrat():
    return fetch_contrat()


@app.route("/controller/contrat/save", methods=["POST"])
def route_save_contrat():
    return save_contrat()


@app.route("/controller/dmt/fetch_dmt", methods=["POST"])
def route_fetch_dmt():
    return fetch_dmt()


@app.route("/controller/dmt/save", methods=["POST"])
def route_save_dmt():
    return save_dmt()


@app.route("/controller/depart/fetch_depart", methods=["POST"])
def route_fetch_depart():
    return fetch_depart()


@app.route("/controller/depart/save", methods=["POST"])
def route_save_depart():
    return save_depart()


@app.route(
    "/controller/attestation_travail/fetch_attestation_travail", methods=["POST"]
)
def route_fetch_attestation_travail():
    return fetch_attestation_travail()


@app.route("/controller/attestation_travail/save", methods=["POST"])
def route_save_attestation_travail():
    return save_attestation_travail()


@app.route("/controller/certificat_travail/fetch_certificat_travail", methods=["POST"])
def route_fetch_certificat_travail():
    return fetch_certificat_travail()


@app.route("/controller/certificat_travail/save", methods=["POST"])
def route_save_certificat_travail():
    return save_certificat_travail()


@app.route(
    "/controller/domiciliation_salaire/fetch_domiciliation_salaire", methods=["POST"]
)
def route_fetch_domiciliation_salaire():
    return fetch_domiciliation_salaire()


@app.route("/controller/domiciliation_salaire/save", methods=["POST"])
def route_save_domiciliation_salaire():
    return save_domiciliation_salaire()


@app.route("/controller/affectation/fetch_affectation", methods=["POST"])
def route_fetch_affectation():
    return fetch_affectation()


@app.route("/controller/affectation/save", methods=["POST"])
def route_save_affectation():
    return save_affectation()


@app.route("/controller/indemnite/fetch_indemnite", methods=["POST"])
def route_fetch_indemnite():
    return fetch_indemnite()


@app.route("/controller/indemnite/save", methods=["POST"])
def route_save_indemnite():
    return save_indemnite()


@app.route("/controller/conge_annuel/fetch_conge_annuel", methods=["POST"])
def route_fetch_conge_annuel():
    return fetch_conge_annuel()


@app.route("/controller/conge_annuel/save", methods=["POST"])
def route_save_conge_annuel():
    return save_conge_annuel()


@app.route("/controller/conge_maternite/fetch_conge_maternite", methods=["POST"])
def route_fetch_conge_maternite():
    return fetch_conge_maternite()


@app.route("/controller/conge_maternite/save", methods=["POST"])
def route_save_conge_maternite():
    return save_conge_maternite()


@app.route("/controller/cotisation/fetch_cotisation", methods=["POST"])
def route_fetch_cotisation():
    return fetch_cotisation()


@app.route("/controller/cotisation/save", methods=["POST"])
def route_save_cotisation():
    return save_cotisation()


@app.route("/controller/salaire/fetch_calcul", methods=["POST"])
def route_fetch_calcul():
    return fetch_calcul()


@app.route("/controller/salaire/fetch_salaire", methods=["POST"])
def route_fetch_salaire():
    return fetch_salaire()


@app.route("/controller/salaire/save", methods=["POST"])
def route_save_salaire():
    return save_salaire()


@app.route("/controller/paie_conge_annuel/fetch_calcul_conge_annuel", methods=["POST"])
def route_fetch_calcul_conge_annuel():
    return fetch_calcul_conge_annuel()


@app.route("/controller/paie_conge_annuel/fetch_paie_conge_annuel", methods=["POST"])
def route_fetch_paie_conge_annuel():
    return fetch_paie_conge_annuel()


@app.route("/controller/paie_conge_annuel/save", methods=["POST"])
def route_save_paie_conge_annuel():
    return save_paie_conge_annuel()


@app.route(
    "/controller/paie_conge_maternite/fetch_calcul_conge_maternite", methods=["POST"]
)
def route_fetch_calcul_conge_maternite():
    return fetch_calcul_conge_maternite()


@app.route(
    "/controller/paie_conge_maternite/fetch_paie_conge_maternite", methods=["POST"]
)
def route_fetch_paie_conge_maternite():
    return fetch_paie_conge_maternite()


@app.route("/controller/paie_conge_maternite/save", methods=["POST"])
def route_save_paie_conge_maternite():
    return save_paie_conge_maternite()


@app.route("/controller/demande_absence/fetch_demande_absence", methods=["POST"])
def route_demande_absence():
    return fetch_demande_absence()


@app.route("/controller/demande_absence/save", methods=["POST"])
def route_save_demande_absence():
    return save_demande_absence()


@app.route("/controller/absence/fetch_absence", methods=["POST"])
def route_fetch_absence():
    return fetch_absence()


@app.route("/controller/absence/save", methods=["POST"])
def route_save_absence():
    return save_absence()


@app.route("/controller/pointage/fetch_pointage", methods=["POST"])
def route_fetch_pointage():
    return fetch_pointage()


@app.route("/controller/pointage/suivi_pointage", methods=["POST"])
def route_suivi_pointage():
    return suivi_pointage()


@app.route("/controller/pointage/save", methods=["POST"])
def route_save_pointage():
    return save_pointage()


@app.route("/controller/pointage/reconnaissance_facial", methods=["POST"])
def route_reconnaissance_facial():
    return reconnaissance_facial()


@app.route("/controller/employe/fetch_show_employe", methods=["POST"])
def route_fetch_show_employe():
    return fetch_show_employe()


@app.route("/controller/dashboard/donnee", methods=["POST"])
def route_dashboard_rh():
    return dashboard_rh()


@app.route("/controller/dashboard/statistique", methods=["POST"])
def route_statistique_rh():
    return statistique_rh()


@app.route("/controller/dashboard/tableau", methods=["POST"])
def route_tableau_rh():
    return tableau_rh()


@app.route("/controller/dashboard/notification", methods=["POST"])
def route_notification_rh():
    return notification_rh()

# ==== ROUTE POUR LA GESTION DES MATIERES ====


@app.route("/controller_g/select_ajax/select_ajax", methods=["POST"])
def route_fetch_select_ajax_g():
    return fetch_select_ajax_g()


@app.route("/controller_g/import_export/upload/upload_gstock", methods=["POST"])
def route_save_import_files_g():
    return save_import_files_g()


@app.route("/controller_g/import_export/import_categorie", methods=["POST"])
def route_save_import_categorie():
    return save_import_categorie()


@app.route("/controller_g/import_export/import_matiere", methods=["POST"])
def route_save_import_matiere():
    return save_import_matiere()


@app.route("/controller_g/categorie/fetch_categorie", methods=["POST"])
def route_fetch_categorie():
    return fetch_categorie()


@app.route("/controller_g/categorie/save", methods=["POST"])
def route_save_categorie():
    return save_categorie()


@app.route("/controller_g/matiere/fetch_matiere", methods=["POST"])
def route_fetch_matiere():
    return fetch_matiere()


@app.route("/controller_g/matiere/save", methods=["POST"])
def route_save_matiere():
    return save_matiere()


@app.route("/controller_g/fournisseur/fetch_fournisseur", methods=["POST"])
def route_fetch_fournisseur():
    return fetch_fournisseur()


@app.route("/controller_g/fournisseur/save", methods=["POST"])
def route_save_fournisseur():
    return save_fournisseur()


@app.route("/controller_g/entree/fetch_entree", methods=["POST"])
def route_fetch_entree():
    return fetch_entree()


@app.route("/controller_g/entree/save", methods=["POST"])
def route_save_entree():
    return save_entree()

@app.route("/controller_g/sortie/fetch_sortie", methods=["POST"])
def route_fetch_sortie():
    return fetch_sortie()


@app.route("/controller_g/sortie/save", methods=["POST"])
def route_save_sortie():
    return save_sortie()


@app.route("/controller_g/affectation/fetch_affectation", methods=["POST"])
def route_fetch_affectation_m():
    return fetch_affectation_m()


@app.route("/controller_g/affectation/save", methods=["POST"])
def route_save_affectation_m():
    return save_affectation_m()


@app.route("/controller_g/mutation/fetch_mutation", methods=["POST"])
def route_fetch_mutation():
    return fetch_mutation()


@app.route("/controller_g/mutation/save", methods=["POST"])
def route_save_mutation():
    return save_mutation()


@app.route("/controller_g/dotation/fetch_dotation", methods=["POST"])
def route_fetch_dotation():
    return fetch_dotation()


@app.route("/controller_g/dotation/save", methods=["POST"])
def route_save_dotation():
    return save_dotation()


@app.route("/controller_g/reception/fetch_reception", methods=["POST"])
def route_fetch_reception():
    return fetch_reception()


@app.route("/controller_g/reception/save", methods=["POST"])
def route_save_reception_carburant():
    return save_reception_carburant()


@app.route("/controller_g/dashboard/donnee", methods=["POST"])
def route_dashboard_gs():
    return dashboard_gs()


@app.route("/controller_g/dashboard/statistique", methods=["POST"])
def route_statistique_gs():
    return statistique_gs()


@app.route("/controller_g/dashboard/tableau", methods=["POST"])
def route_tableau_gs():
    return tableau_gs()


@app.route("/controller_g/employe/enroll", methods=["POST"])
def route_enroll():
    return enroll()


# === ROUTES PDF ===
pdf_handlers = {
    "curriculum": curriculum.handle,
    "contrat": contrat.handle,
    "dmt": dmt.handle,
    "depart": depart.handle,
    "attestation_travail": attestation_travail.handle,
    "certificat_travail": certificat_travail.handle,
    "domiciliation_salaire": domiciliation_salaire.handle,
    "affectation": affectation.handle,
    "indemnite": indemnite.handle,
    "conge_annuel": conge_annuel.handle,
    "conge_maternite": conge_maternite.handle,
    "absence": absence.handle,
    "bulletin": bulletin.handle,
    "bulletin2": bulletin2.handle,
    "fiche_paie": fiche_paie.handle,
    "fiche_paie_employe": fiche_paie_employe.handle,
    "demande_absence": demande_absence.handle,
    "document_demande": document_demande.handle,
    "bulletin_fiche_paie": bulletin_fiche_paie.handle,
    "entree": entree.handle,
    "pv_entree": pv_entree.handle,
    "entree_pv_entree": entree_pv_entree.handle,
    "sortie": sortie.handle,
    "sortie_externe": sortie_externe.handle,
    "affectation_matiere": affectation_matiere.handle,
    "mutation_matiere" : mutation_matiere.handle,
    "dotation": dotation.handle,
    "pv_reception": pv_reception.handle,
}

pdf_requires_two_params = {
    "sortie": True,
    "sortie_externe": True,
}


@app.route("/pdf/<page_pdf>")
def pdf(page_pdf):
    handler = pdf_handlers.get(page_pdf)
    if not handler:
        return "Page PDF non trouvée", 404

    encrypted_id = request.args.get("pdf")
    encrypted_id_ref = request.args.get("id_ref")

    # Vérifier paramètre obligatoire "pdf"
    if not encrypted_id:
        return "Paramètre 'pdf' manquant", 400

    # Si la page doit recevoir 2 paramètres
    if pdf_requires_two_params.get(page_pdf, False):
        if not encrypted_id_ref:
            return "Paramètre 'id_ref' manquant", 400
        return handler(encrypted_id, encrypted_id_ref)

    # Sinon : page simple → 1 seul paramètre
    return handler(encrypted_id)


# === ROUTES PROTÉGÉES (pages web) ===
@app.route("/page/<page_name>")
@login_required
def page(page_name):
    valid_pages = [
        "dashboard",
        "region",
        "departement",
        "employe",
        "contrat",
        "dmt",
        "employe_actif",
        "show_employe",
        "depart",
        "document_administratif",
        "attestation_travail",
        "certificat_travail",
        "domiciliation_salaire",
        "affectation",
        "indemnite",
        "conge_annuel",
        "conge_maternite",
        "indemnite_part",
        "heure_jour",
        "cotisation",
        "salaire",
        "paie_conge_annuel",
        "paie_conge_maternite",
        "statistique_salaire",
        "gestion_pointage",
        "demande_absence",
        "absence",
        "pointage",
        "pointeur",
        "face_scan",
        "user",
        "reference",
        "enroll",
    ]

    # Vérifie si la page demandée est valide
    if page_name not in valid_pages:
        return "Page non trouvée", 404

    id_encrypted = request.args.get("id") or session.get("id_m_encrypted")

    # CAS SPÉCIAL : page "reference" → on récupère ses données
    result_reference = fetch_reference(id_encrypted)

    if result_reference and "id_reference" in result_reference:
        session["id_m_encrypted"] = encryptor(
            "encrypt", str(result_reference["id_reference"])
        )
        session["result_reference"] = result_reference  # sauvegarde pour includes

    return render_template(
        f"page/{page_name}.html",
        result_reference=result_reference,
        id_m=session.get("id_m_encrypted"),
    )


@app.route("/gstock/<page_name>")
@login_required
def gstock(page_name):
    valid_pages = [
        "dashboard",
        "categorie",
        "matiere",
        "entree",
        "sortie_interne",
        "sortie_externe",
        "affectation",
        "mutation",
        "fournisseur",
        "dotation",
        "reception",
    ]

    if page_name not in valid_pages:
        return "Page non trouvée", 404

    id_encrypted = request.args.get("id") or session.get("id_m_encrypted")

    # CAS SPÉCIAL : page "reference" → on récupère ses données
    result_reference = fetch_reference(id_encrypted)

    if result_reference and "id_reference" in result_reference:
        session["id_m_encrypted"] = encryptor(
            "encrypt", str(result_reference["id_reference"])
        )
        session["result_reference"] = result_reference  # sauvegarde pour includes

    return render_template(
        f"gstock/{page_name}.html",
        result_reference=result_reference,
        id_m=session.get("id_m_encrypted"),
    )


# === MAIN ===
if __name__ == "__main__":
        app.run(host="0.0.0.0", port=5000, debug=True)
