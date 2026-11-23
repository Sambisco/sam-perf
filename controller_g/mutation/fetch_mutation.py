from flask import request, Response, url_for, jsonify
import re
import locale
import json
from datetime import datetime, date, timedelta
from templates.include.connect import get_connection
from templates.include.encryptor import encryptor
from babel.dates import format_date

# Locale française
try:
    locale.setlocale(locale.LC_TIME, "fr_FR.UTF-8")
except locale.Error:
    pass


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
        else:  # "long" par défaut
            fmt = "dd MMMM yyyy"

        return format_date(dt, format=fmt, locale="fr_FR").capitalize()

    except Exception:
        return ""


def format_number(num):
    try:
        if num is None:
            return "0"
        return f"{num:,.0f}".replace(",", " ").replace(".", ",")
    except Exception:
        return "0"


# === Fonction utilitaire pour acronymes ===
def make_acronym(word: str) -> str:
    # Supprimer caractères spéciaux style apostrophe
    cleaned = word.replace("'", "").replace("’", "").replace("`", "")
    parts = cleaned.split()
    return "".join([p[0].upper() for p in parts if p])


def fetch_mutation():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    data = []

    # === Cas 1: détails d'une sortie ===
    if "id_mutation" in request.form:
        id_mutation = encryptor("decrypt", request.form["id_mutation"])
        query = """
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
        cursor.execute(query, (id_mutation,))
        result = cursor.fetchall()

        for row in result:
            response = {
                "id_mutation": encryptor("encrypt", str(row["id_mutation"])),
                "numero_mutation": str(row["numero_mutation"]).zfill(7),
                "id_affectation_matiere": encryptor(
                    "encrypt", str(row["id_affectation_matiere"])
                ),
                "image": url_for(
                    "static",
                    filename=(
                        f"img/matiere/{row['image']}"
                        if row["image"]
                        else "img/image/image.jpg"
                    ),
                ),
                "total": row["total"],
                "id_matiere": encryptor("encrypt", str(row["id_matiere"])),
                "id_matiere_raw": row["id_matiere"],
                "id_contrat": encryptor("encrypt", str(row["mutation_id_contrat"])),
                "numero": str(row["numero"]).zfill(7),
                "date_mutation": (
                    row["date_mutation"].strftime("%Y-%m-%d")
                    if row["date_mutation"]
                    else ""
                ),
                "designation": row["designation"],
                "quantite": row["quantite"],
                "observation": row["observation"],
                "nbre_unite": row["nbre_unite"],
            }
            data.append(response)

    # === Cas 2: sorties par référence ===
    elif "id" in request.form:
        id_ref = encryptor("decrypt", request.form["id"])
        query = """
            SELECT
               mutation.id_mutation,
               mutation.numero_mutation,
               mutation.date_mutation,
               mutation.nom_user_mutation,
           
               -- Employé source (qui quitte)
               employe.nom AS nom_employe_source,
               employe.prenom AS prenom_employe_source,
               employe.matricule AS matricule_source,
               
               -- Employé destination (qui reçoit)
               employe_2.nom AS nom_employe_destination,
               employe_2.prenom AS prenom_employe_destination,
               employe_2.matricule AS matricule_destination,
               
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
           
           WHERE reference.id_reference = %s
           ORDER BY  mutation.id_mutation DESC
           

        """
        cursor.execute(query, (id_ref,))
        result = cursor.fetchall()

        for idx, row in enumerate(result, 1):
            acronym_prenom_source = make_acronym(row["prenom_employe_source"])
            acronym_nom_source = make_acronym(row["nom_employe_source"])
            acronym_prenom_destination = make_acronym(row["prenom_employe_destination"])
            acronym_nom_destination = make_acronym(row["nom_employe_destination"])
            response = {
                "count": idx,
                "id_mutation": encryptor("encrypt", str(row["id_mutation"])),
                "numero_mutation": str(row["numero_mutation"]).zfill(7),
                "date_mutation": format_date_fr(row["date_mutation"], style="full"),
                "prenom_employe_source": row["prenom_employe_source"],
                "nom_employe_source": row["nom_employe_source"],
                "matricule_source": f"{acronym_prenom_source}{acronym_nom_source}-{row['matricule_source']}",
                "prenom_employe_destination": row["prenom_employe_destination"],
                "nom_employe_destination": row["nom_employe_destination"],
                "matricule_destination": f"{acronym_prenom_destination}{acronym_nom_destination}-{row['matricule_destination']}",
            }
            data.append(response)

    cursor.close()
    conn.close()
    return jsonify(data)
