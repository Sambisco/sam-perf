from flask import request, jsonify, url_for
import re
import locale
from datetime import datetime, date
from decimal import Decimal
from babel.dates import format_date
from dateutil.relativedelta import relativedelta
from templates.include.connect import get_connection
from templates.include.encryptor import encryptor

locale.setlocale(locale.LC_TIME, "fr_FR.UTF-8")


def format_montant(val):
    try:
        val = Decimal(str(val))
        return "{:,.0f}".format(val).replace(",", " ").replace(".", ",")
    except Exception as e:
        print("Erreur format_montant:", e)
        return "0"


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


def get_acronyme(text):
    text_clean = re.sub(r"\b\w['`‘’]\b", "", text, flags=re.UNICODE)
    return "".join(part[0] for part in text_clean.strip().split() if part)


def fetch_indemnite():
    print("Requête POST reçue:", request.form)
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    if "id_indemnite" in request.form:
        id_indemnite = encryptor("decrypt", request.form["id_indemnite"])
        print("id_indemnite décrypté:", id_indemnite)
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
        cursor.execute(query, (id_indemnite,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            print("Aucune indemnité trouvée pour cet id_indemnite")
            return jsonify({}), 404

        matricule = f"{get_acronyme(row['prenom'])}{get_acronyme(row['nom'])}-{row['matricule']}"

        photo_url = (
            url_for(
                "static",
                filename=f"img/img_employe/{row.get('matricule','')}/{row.get('photo','')}",
            )
            if row.get("photo")
            else url_for("static", filename="img/image/image-profil.png")
        )
        if row.get("date_effet") in [None, "0000-00-00", ""]:
            date_effet_formatted = "0000-00-00"
        else:
            date_effet_formatted = row.get("date_effet").strftime("%Y-%m-%d")

        if row.get("date_enregistrement") in [None, "0000-00-00", ""]:
            date_enregistrement_formatted = "0000-00-00"
        else:
            date_enregistrement_formatted = row.get("date_enregistrement").strftime(
                "%Y-%m-%d"
            )

        data = {
            "id_indemnite": encryptor("encrypt", str(row["id_indemnite"])),
            "id_employe": encryptor("encrypt", str(row["id_employe"])),
            "id_contrat": encryptor("encrypt", str(row["id_contrat"])),
            "prenom": row["prenom"],
            "nom": row["nom"],
            "matricule": matricule,
            "poste_occupe": row.get("poste_occupe", ""),
            "compte": row.get("compte", ""),
            "annee_budget": row.get("annee_budget", ""),
            "date_enregistrement": date_enregistrement_formatted,
            "date_effet": date_effet_formatted,
            "salaire": format_montant(row.get("salaire", 0)),
            "fonction": format_montant(row.get("fonction", 0)),
            "sujetion": format_montant(row.get("sujetion", 0)),
            "responsabilite": format_montant(row.get("responsabilite", 0)),
            "sursalaire": format_montant(row.get("sursalaire", 0)),
            "logement": format_montant(row.get("logement", 0)),
            "transport": format_montant(row.get("transport", 0)),
            "telephone_in": format_montant(row.get("telephone_in", 0)),
            "document_lettre": row.get("document_lettre_indemnite", ""),
            "photo": photo_url,
        }
        print("Données détaillées envoyées:", data)
        return jsonify(data)

    elif "id" in request.form:
        id_ref = encryptor("decrypt", request.form["id"])
        print("id_reference décrypté:", id_ref)
        query = """
            SELECT indemnite.*, contrat.*, employe.prenom, employe.nom, employe.matricule, employe.date_n, employe.photo, employe.telephone_e, employe.adresse_e,
                   reference.id_reference
            FROM indemnite
            INNER JOIN contrat ON contrat.id_contrat = indemnite.id_contrat
            INNER JOIN employe ON employe.id_employe = contrat.id_employe
            INNER JOIN reference ON reference.id_reference = employe.id_reference
            WHERE reference.id_reference = %s
            ORDER BY indemnite.id_indemnite DESC
        """
        cursor.execute(query, (id_ref,))
        rows = cursor.fetchall()
        print(f"{len(rows)} lignes trouvées")
        conn.close()

        if not rows:
            print("Aucune indemnité trouvée pour cet id_reference")
            return jsonify([])

        data = []
        count = 0
        for row in rows:
            count += 1
            print(f"Traitement ligne #{count} id_indemnite={row['id_indemnite']}")
            prenom = row["prenom"]
            nom = row["nom"]
            matricule = f"{get_acronyme(prenom)}{get_acronyme(nom)}-{row['matricule']}"

            # Gestion sécurisée de date_sorti
            nombre_annee = "Expire : 0 ans 0 mois 0 jours"
            date_sorti = row.get("date_sorti")

            date_sorti_obj = None
            if date_sorti:
                if isinstance(date_sorti, str):
                    try:
                        date_sorti_obj = datetime.strptime(
                            date_sorti, "%Y-%m-%d"
                        ).date()
                    except ValueError:
                        date_sorti_obj = None
                elif isinstance(date_sorti, datetime):
                    date_sorti_obj = date_sorti.date()
                elif isinstance(date_sorti, date):
                    date_sorti_obj = date_sorti

            if date_sorti_obj and date_sorti_obj > date.today():
                delta = relativedelta(date_sorti_obj, date.today())
                nombre_annee = (
                    f"Active : {delta.years} ans {delta.months} mois {delta.days} jours"
                )

            # Calcul âge sécurisé
            age = ""
            date_n = row.get("date_n")
            birth_date = None
            try:
                if date_n:
                    if isinstance(date_n, str):
                        birth_date = datetime.strptime(date_n, "%Y-%m-%d")
                    elif isinstance(date_n, date):
                        birth_date = datetime.combine(date_n, datetime.min.time())

                    if birth_date:
                        today = datetime.now()
                        age_delta = relativedelta(today, birth_date)
                        age = f"{age_delta.years} ans"
            except Exception:
                age = ""

            photo_url = (
                url_for(
                    "static",
                    filename=f"img/img_employe/{row['matricule']}/{row['photo']}",
                )
                if row.get("photo")
                else url_for("static", filename="img/image/image-profil.png")
            )
            if row.get("date_effet") in [None, "0000-00-00", ""]:
                date_effet_formatted = "Pas encore valide"
            else:
                date_effet_formatted = format_date_fr(row.get("date_effet"), style="full")

            data.append(
                {
                    "count": count,
                    "id_indemnite": encryptor("encrypt", str(row["id_indemnite"])),
                    "id_indemnite_raw": row.get("id_indemnite", ""),
                    "date_effet": date_effet_formatted,
                    "prenom": prenom,
                    "nom": nom,
                    "matricule": matricule,
                    "poste_occupe": row.get("poste_occupe", ""),
                    "telephone_e": row.get("telephone_e", ""),
                    "adresse_e": row.get("adresse_e", ""),
                    "annee_budget": (
                        str(row.get("annee_budget", ""))
                        if row.get("annee_budget")
                        else ""
                    ),
                    "date_enregistrement": format_date_fr(
                        row.get("date_enregistrement", ""), style="full"
                    ),
                    "fonction": (
                        ""
                        if float(row.get("fonction", 0)) == 0
                        else format_montant(row["fonction"])
                    ),
                    "sujetion": (
                        ""
                        if float(row.get("sujetion", 0)) == 0
                        else format_montant(row["sujetion"])
                    ),
                    "responsabilite": (
                        ""
                        if float(row.get("responsabilite", 0)) == 0
                        else format_montant(row["responsabilite"])
                    ),
                    "sursalaire": (
                        ""
                        if float(row.get("sursalaire", 0)) == 0
                        else format_montant(row["sursalaire"])
                    ),
                    "logement": (
                        ""
                        if float(row.get("logement", 0)) == 0
                        else format_montant(row["logement"])
                    ),
                    "transport": (
                        ""
                        if float(row.get("transport", 0)) == 0
                        else format_montant(row["transport"])
                    ),
                    "telephone_in": (
                        ""
                        if float(row.get("telephone_in", 0)) == 0
                        else format_montant(row["telephone_in"])
                    ),
                    "nombre_annee": nombre_annee,
                    "age": age,
                    "photo": photo_url,
                }
            )

        print("Données liste envoyées:", data)
        return jsonify(data)

    else:
        print("Requête invalide : ni 'id_indemnite' ni 'id' dans request.form")
        return jsonify({"error": "Requête invalide"}), 400
