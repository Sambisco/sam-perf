from flask import request, Response, url_for, jsonify
import re
import locale
import json
from datetime import datetime, date, time, timedelta
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


def format_timedelta(td):
    if isinstance(td, timedelta):
        total_seconds = int(td.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        return f"{hours:02}:{minutes:02}:{seconds:02}"
    return str(td)


def format_number(num):
    try:
        if num is None:
            return "0"
        return f"{num:,.0f}".replace(",", " ").replace(".", ",")
    except Exception:
        return "0"


def make_json_serializable(obj):
    """
    Convertit récursivement dans obj les objets non JSON-serializables
    (timedelta, datetime, date, time) en chaînes de caractères.
    """
    if isinstance(obj, dict):
        return {k: make_json_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [make_json_serializable(item) for item in obj]
    elif isinstance(obj, timedelta):
        total_seconds = int(obj.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        return f"{hours:02}:{minutes:02}:{seconds:02}"
    elif isinstance(obj, datetime):
        return obj.strftime("%Y-%m-%d %H:%M:%S")
    elif isinstance(obj, date):
        return obj.strftime("%Y-%m-%d")
    elif isinstance(obj, time):
        return obj.strftime("%H:%M:%S")
    else:
        return obj


def fetch_show_employe():

    print("🛠️ Requête entrante :", request.form)

    # Cas 1 : Récupérer un employé par son ID
    if "id_employe" in request.form:
        encrypted_id = request.form.get("id_employe")
        try:
            id = encryptor("decrypt", encrypted_id)
        except Exception as e:
            return jsonify({"error": f"Erreur de décryptage: {str(e)}"}), 400

        try:
            conn = get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                """
                     SELECT * FROM contrat
                     INNER JOIN employe ON employe.id_employe = contrat.id_employe
                     INNER JOIN reference ON reference.id_reference = employe.id_reference 
                     WHERE employe.id_employe = %s
                """,
                (id,),
            )
            result = cursor.fetchall()
        except Exception as e:
            return jsonify({"error": f"Erreur SQL: {str(e)}"}), 500
        finally:
            conn.close()

        if not result:
            return jsonify({"error": "Aucun employé trouvé"}), 404

        data = []
        for row in result:
            # Construction matricule formaté
            re_clean = r"\b\w['`‘’]\b"
            code_prenom = re.sub(re_clean, "", row["prenom"])
            code_nom = re.sub(re_clean, "", row["nom"])
            acronym_prenom = "".join([w[0] for w in code_prenom.split()])
            acronym_nom = "".join([w[0] for w in code_nom.split()])
            matricule_format = f"{acronym_prenom}{acronym_nom}-{row['matricule']}"

            data.append(
                {
                    "prenom": row["prenom"],
                    "nom": row["nom"],
                    "matricule": matricule_format,
                    "date_n": row["date_n"].strftime("%Y-%m-%d"),
                    "date_n2": format_date_fr(row.get("date_n"), style="long"),
                    "lieu_n": row["lieu_n"],
                    "telephone_e": row["telephone_e"],
                    "adresse_e": row["adresse_e"],
                    "email_e": row["email_e"],
                    "genre": row["genre"],
                    "nom_pere": row["nom_pere"],
                    "nom_mere": row["nom_mere"],
                    "poste_occupe": row["poste_occupe"],
                    "nature": row["nature"],
                    "nationalite": row["nationalite"],
                    "cin_e": row["cin_e"],
                    "email_e": row["email_e"],
                    "categorie": row["categorie"],
                    "date_embauche": format_date_fr(row["date_embauche"], style="full"),
                    "date_sorti": format_date_fr(row["date_sorti"], style="full"),
                    "situation_matr": row["situation_matr"],
                    "salaire": format_number(row.get("salaire", 0)),
                    "conjoint": row["conjoint"],
                    "enfant": row["enfant"],
                    "nb_trimf": row["nb_trimf"],
                    "nb_irpp": row["nb_irpp"],
                    "sursalaire": format_number(row.get("sursalaire", 0)),
                    "fonction": format_number(row.get("fonction", 0)),
                    "sujetion": format_number(row.get("sujetion", 0)),
                    "responsabilite": format_number(row.get("responsabilite", 0)),
                    "logement": format_number(row.get("logement", 0)),
                    "transport": format_number(row.get("transport", 0)),
                    "telephone_in": format_number(row.get("telephone_in", 0)),
                    "autre_indemnite": format_number(row.get("autre_indemnite", 0)),
                    "entreprise": row["entreprise"],
                    "photo": url_for(
                        "static",
                        filename=(
                            f"img/img_employe/{row['matricule']}/{row['photo']}"
                            if row["photo"]
                            else "img/image/image-profil.png"
                        ),
                    ),
                    "logo": url_for(
                        "static",
                        filename=(
                            f"img/logo/{row['logo']}"
                            if row["logo"]
                            else "img/image/image.jpg"
                        ),
                    ),
                }
            )
        return jsonify(data)

    # Cas 2 : Employés sans contrat par référence
    elif "id_affectation" in request.form:
        encrypted_id = request.form.get("id_affectation")
        try:
            id_ref = encryptor("decrypt", encrypted_id)
        except Exception as e:
            return jsonify({"error": f"Erreur de décryptage: {str(e)}"}), 400

        try:
            conn = get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT * FROM affectation
				INNER JOIN contrat ON contrat.id_contrat=affectation.id_contrat
				INNER JOIN employe ON employe.id_employe=contrat.id_employe
				INNER JOIN region ON region.id_region= affectation.id_region
				WHERE employe.id_employe = %s 
            """,
                (id_ref,),
            )
            result = cursor.fetchall()
        except Exception as e:
            return jsonify({"error": f"Erreur SQL: {str(e)}"}), 500
        finally:
            conn.close()

        data = []
        for idx, row in enumerate(result, 1):
            data.append(
                {
                    "count": idx,
                    "date_affectation": format_date_fr(
                        row.get("date_affectation"), style="full"
                    ),
                    "region": row["region"],
                }
            )
        return jsonify(data)

    # Cas 3 : Liste des employés avec leur statut "activite"
    elif "id_conge_annuel" in request.form:
        encrypted_id = request.form.get("id_conge_annuel")
        print(f"Activite demandé pour id (chiffré): {encrypted_id}")
        try:
            id_ref = encryptor("decrypt", encrypted_id)
            print(f"ID décrypté: {id_ref}")
        except Exception as e:
            print("Erreur décryptage ID activite:", e)
            return jsonify({"error": f"ID invalide: {str(e)}"}), 400

        try:
            conn = get_connection()
            cursor = conn.cursor(dictionary=True)

            cursor.execute(
                """
                SELECT * FROM conge_annuel
				INNER JOIN contrat ON contrat.id_contrat=conge_annuel.id_contrat
				INNER JOIN employe ON employe.id_employe=contrat.id_employe
				INNER JOIN reference ON reference.id_reference=employe.id_reference
				WHERE employe.id_employe = %s
            """,
                (id_ref,),
            )
            result = cursor.fetchall()

            data = []

            for idx, row in enumerate(result, 1):

                data.append(
                    {
                        "count": idx,
                        "date_debut": format_date_fr(row["date_debut"], style="full"),
                        "date_fin": format_date_fr(row["date_fin"], style="full"),
                        "nbr_conge": row["nbr_conge"],
                    }
                )

            print(f"Envoi de {len(data)} employés")
            return jsonify(data)

        except Exception as e:
            print("Erreur SQL:", e)
            return jsonify({"error": f"Erreur SQL: {str(e)}"}), 500
        finally:
            conn.close()

    elif "id_conge_maternite" in request.form:
        encrypted_id = request.form.get("id_conge_maternite")
        print(f"Activite demandé pour id (chiffré): {encrypted_id}")
        try:
            id_ref = encryptor("decrypt", encrypted_id)
            print(f"ID décrypté: {id_ref}")
        except Exception as e:
            print("Erreur décryptage ID activite:", e)
            return jsonify({"error": f"ID invalide: {str(e)}"}), 400

        try:
            conn = get_connection()
            cursor = conn.cursor(dictionary=True)

            cursor.execute(
                """
                SELECT * FROM conge_maternite
				INNER JOIN contrat ON contrat.id_contrat=conge_maternite.id_contrat
				INNER JOIN employe ON employe.id_employe=contrat.id_employe
				INNER JOIN reference ON reference.id_reference=employe.id_reference
				WHERE employe.id_employe = %s
            """,
                (id_ref,),
            )
            result = cursor.fetchall()

            data = []

            for idx, row in enumerate(result, 1):

                data.append(
                    {
                        "count": idx,
                        "numero_decision": row["numero_decision"],
                        "date_decision": format_date_fr(
                            row["date_decision"], style="full"
                        ),
                        "date_suspension": format_date_fr(
                            row["date_suspension"], style="full"
                        ),
                        "date_debut": format_date_fr(row["date_debut"], style="full"),
                        "date_fin": format_date_fr(row["date_fin"], style="full"),
                        "date_reprise": format_date_fr(
                            row["date_reprise"], style="full"
                        ),
                        "docteur": row["docteur"],
                    }
                )

            print(f"Envoi de {len(data)} employés")
            return jsonify(data)

        except Exception as e:
            print("Erreur SQL:", e)
            return jsonify({"error": f"Erreur SQL: {str(e)}"}), 500
        finally:
            conn.close()

    elif "id_absence_pointage" in request.form:
        encrypted_id = request.form.get("id_absence_pointage")
        print(f"Activite demandé pour id (chiffré): {encrypted_id}")
        try:
            id_ref = encryptor("decrypt", encrypted_id)
            print(f"ID décrypté: {id_ref}")
        except Exception as e:
            print("Erreur décryptage ID activite:", e)
            return jsonify({"error": f"ID invalide: {str(e)}"}), 400

        try:

            query = f"""
                     SELECT employe.id_employe, employe.photo, employe.prenom, employe.nom, employe.matricule, contrat.poste_occupe,
                            NULL as id_absence, date, personnel.heure_debut AS heure_debut_personnel,
                            pointage.heure_debut, pointage.heure_fin,
                            NULL AS justification,NULL AS Imputable_sur_les_normaux, NULL AS compteur
                     FROM contrat
                     INNER JOIN employe ON employe.id_employe = contrat.id_employe
                     INNER JOIN pointage ON contrat.id_contrat = pointage.id_contrat
                     INNER JOIN personnel ON contrat.id_contrat = personnel.id_contrat
                     INNER JOIN reference ON reference.id_reference = employe.id_reference
                     WHERE employe.id_employe = %s

                     UNION

                     SELECT employe.id_employe, employe.photo, employe.prenom, employe.nom, employe.matricule, contrat.poste_occupe,
                            id_absence, date, NULL, NULL, NULL, justification,Imputable_sur_les_normaux, compteur
                     FROM contrat
                     INNER JOIN employe ON employe.id_employe = contrat.id_employe
                     INNER JOIN absence ON contrat.id_contrat = absence.id_contrat
                     INNER JOIN reference ON reference.id_reference = employe.id_reference
                     WHERE employe.id_employe = %s

                     ORDER BY date DESC
                 """

            with get_connection() as conn:
                with conn.cursor(dictionary=True) as cursor:
                    cursor.execute(query, (id_ref, id_ref))
                    rows = cursor.fetchall()

            data = []
            count = 0
            re_apostrophe = re.compile(r"\b\w[\'`‘’]\b", re.UNICODE)

            def format_time(value):
                if value is None:
                    return "00:00:00"
                if isinstance(value, (time, datetime)):
                    return value.strftime("%H:%M:%S")
                if isinstance(value, timedelta):
                    total_seconds = int(value.total_seconds())
                    hours = total_seconds // 3600
                    minutes = (total_seconds % 3600) // 60
                    seconds = total_seconds % 60
                    return f"{hours:02}:{minutes:02}:{seconds:02}"
                return str(value)

            for row in rows:
                count += 1

                # Abréviation prénom
                code_prenom = re_apostrophe.sub("", row["prenom"] or "")
                acronym_prenom = "".join([w[0] for w in code_prenom.split() if w])

                # Abréviation nom
                code_nom = re_apostrophe.sub("", row["nom"] or "")
                acronym_nom = "".join([w[0] for w in code_nom.split() if w])

                full_matricule = f"{acronym_prenom}{acronym_nom}-{row['matricule']}"

                if row["justification"] is None or row["justification"] == "":
                    justification = "Pas de motif"
                else:
                    justification = row["justification"]

                if row["Imputable_sur_les_normaux"] is None or row["justification"] == "":
                    Imputable_sur_les_normaux = ""
                else:
                    Imputable_sur_les_normaux = row.get("Imputable_sur_les_normaux")

                heure_debut = format_time(row.get("heure_debut"))
                heure_fin = format_time(row.get("heure_fin"))

                if row["heure_debut"] is None:
                    pointe = "<span style='color:red;background:rgba(255,0,0,0.1);padding:7px;border-radius:5px;'><strong>Absence</strong></span>"
                elif row["heure_debut"] > row["heure_debut_personnel"]:
                    pointe = "<span style='color:#8b8000;background:rgba(139,128,0,0.1);padding:7px;border-radius:5px;'><strong>Retard</strong></span>"
                elif row["heure_debut"] <= row["heure_debut_personnel"]:
                    pointe = "<span style='color:green;background:rgba(11,156,49,0.1);padding:7px;border-radius:5px;'><strong>A l'heure</strong></span>"
                else:
                    pointe = ""

                response = {
                    "count": count,
                    "poste_occupe": row["poste_occupe"],
                    "date": format_date_fr(row.get("date"), style="full"),
                    "justification": justification,
                    "heure_debut": heure_debut,
                    "heure_fin": heure_fin,
                    "pointe": pointe,
                    "Imputable_sur_les_normaux": Imputable_sur_les_normaux,
                }

                data.append(response)

            data_serializable = make_json_serializable(data)
            return jsonify(data_serializable)

        except Exception as e:
            return jsonify({"error": str(e)}), 500

    elif "id_salaire" in request.form:
        encrypted_id = request.form.get("id_salaire")
        print(f"Activite demandé pour id (chiffré): {encrypted_id}")
        try:
            id_ref = encryptor("decrypt", encrypted_id)
            print(f"ID décrypté: {id_ref}")
        except Exception as e:
            print("Erreur décryptage ID activite:", e)
            return jsonify({"error": f"ID invalide: {str(e)}"}), 400

        try:
            conn = get_connection()
            cursor = conn.cursor(dictionary=True)

            cursor.execute(
                """
               SELECT * FROM salaire
			   INNER JOIN contrat ON contrat.id_contrat=salaire.id_contrat
			   INNER JOIN employe ON employe.id_employe=contrat.id_employe
			   WHERE employe.id_employe = %s
            """,
                (id_ref,),
            )
            result = cursor.fetchall()

            data = []

            for idx, row in enumerate(result, 1):

                data.append(
                    {
                        "count": idx,
                        "date_du": format_date_fr(row["date_du"], style="month"),
                        "date_paiement": format_date_fr(
                            row["date_paiement"], style="full"
                        ),
                        "mode_paie": row["mode_paie"],
                      
                    }
                )

            print(f"Envoi de {len(data)} employés")
            return jsonify(data)

        except Exception as e:
            print("Erreur SQL:", e)
            return jsonify({"error": f"Erreur SQL: {str(e)}"}), 500
        finally:
            conn.close()
    # Cas non reconnu
    else:
        return jsonify({"error": "Aucun paramètre POST reconnu"}), 400
