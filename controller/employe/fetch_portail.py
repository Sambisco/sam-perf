from flask import Flask, request, jsonify, url_for
import re
import os
from datetime import datetime, date
from templates.include.connect import get_connection
from templates.include.encryptor import encryptor
from babel.dates import format_date
import qrcode
from io import BytesIO
import base64

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


def generate_acronym(nom_complet):
    # Supprime apostrophes isolées, récupère initiales en majuscule
    try:
        cleaned = re.sub(r"['`‘’]", "", nom_complet)
        parts = cleaned.split()
        return "".join(part[0].upper() for part in parts if part)
    except Exception as e:
        print("Erreur generate_acronym:", e)
        return ""


def calculate_duration_actif(start_val, end_val):
    try:
        if not start_val:
            print("Start value is missing.")
            return ""

        # Convertir en date
        if isinstance(start_val, str):
            start = datetime.strptime(start_val, "%Y-%m-%d").date()
        elif isinstance(start_val, (datetime, date)):
            start = start_val
        else:
            return ""

        # Cas "Pas encore active" si la date de début est future

        if start > date.today():
            return "Pas encore active"

        if isinstance(end_val, str) and end_val.strip():
            end = datetime.strptime(end_val, "%Y-%m-%d").date()
        elif isinstance(end_val, (datetime, date)):
            end = end_val
        else:
            end = date.today()

        # Comparer la date de fin à aujourd'hui
        if end > date.today():
            # Calcule brut comme en PHP
            date1 = datetime.combine(date.today(), datetime.min.time())
            date2 = datetime.combine(end, datetime.min.time())
            diff_seconds = abs((date2 - date1).total_seconds())

            years = int(diff_seconds // (365 * 24 * 60 * 60))
            diff_seconds -= years * 365 * 24 * 60 * 60
            months = int(diff_seconds // (30 * 24 * 60 * 60))
            diff_seconds -= months * 30 * 24 * 60 * 60
            days = int(diff_seconds // (24 * 60 * 60))

            return f"Active : {years} ans {months} mois {days} jours"
        else:
            return "Expire : 0 ans 0 mois 0 jours"

    except Exception as e:
        print("Erreur dans calculate_duration:", e)
        return ""


def generate_qr_code(data):
    qr = qrcode.QRCode(version=1, box_size=10, border=2)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill="black", back_color="white")
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return "data:image/png;base64," + img_str


def fetch_portail():
    data = request.form
    try:
        print("Données reçues:", data)
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        if "id_contrat" in data:
            id_contrat = encryptor("decrypt", data["id_contrat"])
            print("id_contrat décrypté:", id_contrat)
            cursor.execute(
                """
                SELECT * FROM contrat
                INNER JOIN employe ON employe.id_employe = contrat.id_employe
                INNER JOIN reference ON reference.id_reference = employe.id_reference
                WHERE contrat.id_contrat = %s
            """,
                (id_contrat,),
            )
            row = cursor.fetchone()
            acronym_prenom = generate_acronym(row["prenom"])
            acronym_nom = generate_acronym(row["nom"])
            if row:
                response = {
                    "prenom": row["prenom"],
                    "nom": row["nom"],
                    "matricule": acronym_prenom
                    + acronym_nom
                    + "-"
                    + str(row["matricule"]),
                    "date_n": format_date_fr(row["date_n"], style="long"),
                    "lieu_n": row["lieu_n"],
                    "telephone_e": row["telephone_e"],
                    "adresse_e": row["adresse_e"],
                    "poste_occupe": row["poste_occupe"],
                    "nom_pere": row["nom_pere"],
                    "nom_mere": row["nom_mere"],
                    "entreprise": (
                        row["entreprise"] if row["entreprise"] else "Entreprise"
                    ),
                    "photo": (
                        url_for(
                            "static",
                            filename=f"img/img_employe/{row.get('matricule','')}/{row.get('photo','')}",
                        )
                        if row.get("photo")
                        else url_for("static", filename="img/image/image-profil.png")
                    ),
                    "logo": url_for(
                        "static",
                        filename=(
                            f"img/logo/{row['logo']}"
                            if row.get("logo")
                            else "img/image/image.jpg"
                        ),
                    ),
                    "nature": row["nature"],
                    "date_embauche": format_date_fr(row["date_embauche"], style="full"),
                    "date_sorti": format_date_fr(row["date_sorti"], style="full"),
                    "nombre_annee": calculate_duration_actif(
                        row["date_embauche"],
                        row["date_sorti"],
                    ),
                    "photo_qr": generate_qr_code(
                        encryptor("encrypt", str(row["id_contrat"]))
                    ),
                }
                return jsonify(response)
            return jsonify(0)
        elif (
            "id_demande_absence" in request.form
            and request.form["id_demande_absence"].strip()
        ):
            id_decrypted = encryptor(
                "decrypt", request.form["id_demande_absence"]
            ).strip()

            conn = get_connection()
            cursor = conn.cursor()
            query = """
               SELECT * FROM contrat
               INNER JOIN employe ON employe.id_employe=contrat.id_employe 
               INNER JOIN demande_absence ON contrat.id_contrat=demande_absence.id_contrat 
               INNER JOIN reference ON reference.id_reference=employe.id_reference 
               WHERE contrat.id_contrat = %s
               ORDER BY demande_absence.id_demande_absence DESC
            """
            cursor.execute(query, (id_decrypted,))
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]

            data = []
            for idx, row in enumerate(rows, 1):
                row_dict = dict(zip(columns, row))
                acronym_prenom = generate_acronym(row_dict.get("prenom", ""))
                acronym_nom = generate_acronym(row_dict.get("nom", ""))
                matricule = row_dict.get("matricule", "")
                if not row_dict.get("id_contrat"):
                    continue
                if row_dict.get("avis_rh") == "":
                    avis_rh = "<span style='color:red;background:rgba(255,0,0,0.1);padding:7px;border-radius:5px;'><strong>En attente</strong></span>"
                elif row_dict.get("avis_rh") == "Non":
                    avis_rh = "<span style='color:red;background:rgba(255,0,0,0.1);padding:7px;border-radius:5px;'><strong>Rejetter</strong></span>"
                elif row_dict.get("avis_rh") == "Oui":
                    avis_rh = "<span style='color:green;background:rgba(11,156,49,0.1);padding:7px;border-radius:5px;'><strong>Accepter</strong></span>"

                response = {
                    "count": idx,
                    "id_demande_absence": encryptor(
                        "encrypt", str(row_dict.get("id_demande_absence", ""))
                    ),
                    "id_demande_absence_raw": row_dict.get("id_demande_absence", ""),
                    "id_demande_absence_raw": row_dict.get("id_demande_absence", ""),
                    "prenom": row_dict.get("prenom", ""),
                    "nom": row_dict.get("nom", ""),
                    "matricule": f"{acronym_prenom}{acronym_nom}-{matricule}",
                    "poste_occupe": row_dict.get("poste_occupe", ""),
                    "periode_du": format_date_fr(
                        row_dict.get("periode_du", ""), style="full"
                    ),
                    "periode_au": format_date_fr(
                        row_dict.get("periode_au", ""), style="full"
                    ),
                    "nbr_jour": row_dict.get("nbr_jour", ""),
                    "superieur_hierarchique": row_dict.get("superieur_hierarchique", ""),
                    "fonction_superieur": row_dict.get("fonction_superieur", ""),
                    "Imputable_sur_les_normaux": row_dict.get(
                        "Imputable_sur_les_normaux", ""
                    ),
                    "precision_employe": row_dict.get("precision_employe", ""),
                    "motif": row_dict.get("motif", ""),
                    "avis": row_dict.get("avis", ""),
                    "avis_rh": avis_rh,
                    "avis": row_dict.get("avis", ""),
                    "date_v": format_date_fr(row_dict.get("date_v", ""), style="full"),
                    "precision_superieur": row_dict.get("precision_superieur", ""),
                    "photo": (
                        url_for(
                            "static",
                            filename=f"img/img_employe/{row_dict.get('matricule','')}/{row_dict.get('photo','')}",
                        )
                        if row_dict.get("photo")
                        else url_for("static", filename="img/image/image-profil.png")
                    ),
                }
                data.append(response)

            cursor.close()
            conn.close()
            return jsonify(data)

        elif "id_salaire" in request.form:
            id_ref = encryptor("decrypt", request.form["id_salaire"]).strip()
            query = """
                 SELECT * FROM salaire
                 INNER JOIN contrat ON contrat.id_contrat=salaire.id_contrat
                 INNER JOIN employe ON employe.id_employe=contrat.id_employe
                 WHERE contrat.id_contrat = %s  
                 ORDER BY salaire.date_du DESC
             """
            cursor.execute(query, (id_ref, ))
            results = cursor.fetchall()

            data = []
            for count, row in enumerate(results, 1):
                prenom = row["prenom"]
                nom = row["nom"]
                acronym_prenom = "".join([mot[0] for mot in prenom.split()])
                acronym_nom = "".join([mot[0] for mot in nom.split()])

                data.append(
                     {
                         "count" :count,
                         "id_salaire": encryptor("encrypt", str(row["id_salaire"])),
                         "id_salaire_raw": row["id_salaire"],
                         "prenom": prenom,
                         "nom": nom,
                         "matricule": f"{acronym_prenom}{acronym_nom}-{row['matricule']}",
                         "poste_occupe": row["poste_occupe"],
                         "telephone_e": row["telephone_e"],
                         "annee": format_date_fr(row["date_du"], style="years"),
                         "periode": format_date_fr(row["date_du"], style="month"),
                         "date_paiement": format_date_fr(
                             row["date_paiement"], style="full"
                         ),
                         "mode_paie": row["mode_paie"],
                         "photo": (
                             url_for(
                                 "static",
                                 filename=f"img/img_employe/{row.get('matricule','')}/{row.get('photo','')}",
                             )
                             if row.get("photo")
                             else url_for("static", filename="img/image/image-profil.png")
                         ),
                     }
                 )

            return jsonify(data)

        elif "id_galerie" in request.form:
            id_ref = encryptor("decrypt", request.form["id_galerie"]).strip()

            # Récupération des infos employé/contrat
            query = """
            SELECT * FROM contrat
            INNER JOIN employe ON employe.id_employe = contrat.id_employe
            INNER JOIN reference ON reference.id_reference = employe.id_reference
            WHERE contrat.id_contrat = %s
            """
            cursor.execute(query, (id_ref,))
            result = cursor.fetchall()  # on suppose plusieurs lignes possibles

            all_images = []

            for idx, row in enumerate(result, 1):
                matricule = str(row.get("matricule", ""))
                folder_path = os.path.join("static", "img", "img_employe", matricule)

                images = []
                if os.path.exists(folder_path):
                    for file in os.listdir(folder_path):
                        if file.lower().endswith((".png", ".jpg", ".jpeg", ".gif")):
                            img_url = url_for(
                               "static",
                               filename=f"img/img_employe/{matricule}/{file}",
                               _external=False
                           )
                            images.append({
                               "filename": file,   # 🔥 nom du fichier
                               "url": img_url      # 🔥 URL utilisable dans <img src="">
                           })

                all_images.append({
                   "index": idx,
                   "matricule": matricule,
                   "nom": row.get("nom"),
                   "prenom": row.get("prenom"),
                   "images": images
               })

            return jsonify(all_images)

        else:
            return jsonify({"error": "Paramètre POST invalide"}), 400

    except Exception as e:
        print("Erreur attrapée dans fetch_portail:", e)
        return jsonify({"error": str(e)}), 500

    finally:
        if "cursor" in locals():
            cursor.close()
        if "conn" in locals():
            conn.close()
