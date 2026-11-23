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
    locale.setlocale(locale.LC_TIME, 'fr_FR.UTF-8')
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


def fetch_employe():
    print("🛠️ Requête entrante :", request.form)

    # Cas 1 : Récupérer un employé par son ID
    if 'id_employe' in request.form:
        encrypted_id = request.form.get('id_employe')
        try:
            id = encryptor('decrypt', encrypted_id)
        except Exception as e:
            return jsonify({"error": f"Erreur de décryptage: {str(e)}"}), 400

        try:
            conn = get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM `employe` WHERE id_employe=%s", (id,))
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
            code_prenom = re.sub(re_clean, "", row['prenom'])
            code_nom = re.sub(re_clean, "", row['nom'])
            acronym_prenom = "".join([w[0] for w in code_prenom.split()])
            acronym_nom = "".join([w[0] for w in code_nom.split()])
            matricule_format = f"{acronym_prenom}{acronym_nom}-{row['matricule']}"

            data.append(
                {
                    "id_employe": encryptor("encrypt", str(row["id_employe"])),
                    "id_reference": encryptor("encrypt", str(row["id_reference"])),
                    "prenom": row["prenom"],
                    "nom": row["nom"],
                    "matricule_photo": row["matricule"],
                    "matricule": matricule_format,
                    "date_n": row["date_n"].strftime("%Y-%m-%d"),
                    "date_n2": format_date_fr(row.get("date_n")),
                    "lieu_n": row["lieu_n"],
                    "telephone_e": row["telephone_e"],
                    "adresse_e": row["adresse_e"],
                    "email_e": row["email_e"],
                    "genre": row["genre"],
                    "poste": row["poste"],
                    "commission": row["commission"],
                    "photo": url_for(
                        "static",
                        filename=(
                            f"img/img_employe/{row['matricule']}/{row['photo']}"
                            if row["photo"]
                            else "img/image/image-profil.png"
                        ),
                    ),
                }
            )
        return jsonify(data)

    # Cas 2 : Employés sans contrat par référence
    elif 'id' in request.form:
        encrypted_id = request.form.get('id')
        try:
            id_ref = encryptor('decrypt', encrypted_id)
        except Exception as e:
            return jsonify({"error": f"Erreur de décryptage: {str(e)}"}), 400

        try:
            conn = get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT * FROM employe 
                WHERE NOT EXISTS (SELECT * FROM contrat WHERE employe.id_employe = contrat.id_employe) 
                AND id_reference = %s ORDER BY id_employe DESC
            """, (id_ref,))
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
                    "id_employe": encryptor("encrypt", str(row["id_employe"])),
                    "id_employe_raw": row["id_employe"],
                    "prenom": row["prenom"],
                    "nom": row["nom"],
                    "date_n": row["date_n"],
                    "date_n2": format_date_fr(row.get("date_n"), style="long"),
                    "lieu_n": row["lieu_n"],
                    "telephone_e": row["telephone_e"],
                    "adresse_e": row["adresse_e"],
                    "email_e": row["email_e"],
                    "genre": row["genre"],
                    "poste": row["poste"],
                    "commission": row["commission"],
                    "photo": url_for(
                        "static",
                        filename=(
                            f"img/img_employe/{row['matricule']}/{row['photo']}"
                            if row["photo"]
                            else "img/image/image-profil.png"
                        ),
                    ),
                }
            )
        return jsonify(data)

    # Cas 3 : Liste des employés avec leur statut "activite"
    elif  'activite' in request.form:
        encrypted_id = request.form.get("activite")
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

            cursor.execute("""
                SELECT * FROM employe
                INNER JOIN reference ON reference.id_reference = employe.id_reference
                WHERE reference.id_reference = %s
                ORDER BY employe.id_employe DESC
            """, (id_ref,))
            employes = cursor.fetchall()

            data = []

            for row in employes:
                id_employe = row["id_employe"]

                # Vérifier contrat
                cursor.execute("""
                    SELECT * FROM contrat
                    WHERE id_employe = %s
                    ORDER BY id_contrat DESC
                    LIMIT 1
                """, (id_employe,))
                contrat = cursor.fetchone()

                statut = "<h5 style='margin-top:10px;'><span style='color:red;background:rgba(255,0,0,0.1);padding:7px;border-radius:5px;'><strong>En attente</strong></span></h5>"
                if contrat:
                    statut = "<h5 style='margin-top:10px;'><span style='color:green;background:rgba(11,156,49,0.1);padding:7px;border-radius:5px;'><strong>Contractuel</strong></span></h5>"

                data.append(
                    {
                        "id_employe": encryptor("encrypt", str(row["id_employe"])),
                        "prenom": f"{row['prenom']} {row['nom']}",
                        "nom": row["nom"],
                        "date_n": row["date_n"],
                        "date_n2": format_date_fr(row["date_n"], style="long"),
                        "lieu_n": row["lieu_n"],
                        "telephone_e": row["telephone_e"],
                        "adresse_e": row["adresse_e"],
                        "email_e": row["email_e"],
                        "genre": row["genre"] if row["genre"] else "",
                        "poste": row["poste"],
                        "commission": row["commission"],
                        "photo": url_for(
                            "static",
                            filename=(
                                f"img/img_employe/{row['matricule']}/{row['photo']}"
                                if row["photo"]
                                else "img/image/image-profil.png"
                            ),
                        ),
                        "activite": statut,
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
