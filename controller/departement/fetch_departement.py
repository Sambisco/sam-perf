from flask import request, Response, url_for
import re
import locale
import json
from datetime import datetime, date, timedelta  # ✅ Ajout de `date`
from templates.include.connect import get_connection
from templates.include.encryptor import encryptor
from babel.dates import format_date

# Définir la locale française pour la gestion des dates
try:
    locale.setlocale(locale.LC_TIME, 'fr_FR.UTF-8')
except locale.Error:
    pass  # Locale non disponible
    locale.setlocale(locale.LC_TIME, "fr_FR.UTF-8")


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

def jsonify_utf8(data):
    def default_converter(o):
        if isinstance(o, datetime):
            return o.strftime('%Y-%m-%d %H:%M:%S')
        if isinstance(o, date):  # ✅ Ajout pour corriger l’erreur
            return o.isoformat()
        if isinstance(o, timedelta):
            return format_timedelta(o)
        raise TypeError(f"Object of type {o.__class__.__name__} is not JSON serializable")

    json_str = json.dumps(data, ensure_ascii=False, default=default_converter)
    return Response(json_str, mimetype='application/json; charset=utf-8')


def fetch_departement():
    print("🛠️ Requête entrante :", request.form)

    # Début du code à ajouter ici
    if 'id_departement' in request.form:
        # Décryptage de l'ID de la région
        encrypted_id = request.form.get('id_departement')
        try:
            # Décryptage de l'ID
            id = encryptor('decrypt', encrypted_id)
        except Exception as e:
            return jsonify_utf8({"error": f"Erreur de décryptage de l'ID de la région: {str(e)}"}), 400

        try:
            conn = get_connection()
        except Exception as e:
            return jsonify_utf8({"error": f"Erreur de connexion à la base de données: {str(e)}"}), 500

        try:
            with conn.cursor(dictionary=True) as cursor:
                # Effectuer la requête pour obtenir les données de la région
                query = "SELECT * FROM `departement` WHERE id_departement=%s"
                cursor.execute(query, (id,))
                result = cursor.fetchall()
                total_row = cursor.rowcount
        except Exception as e:
            return jsonify_utf8({"error": f"Erreur SQL lors de la récupération de la région: {str(e)}"}), 500
        finally:
            conn.close()

        if total_row > 0:
            data = []
            for row in result:
                data.append({
                    "id_departement": encryptor('encrypt', str(row["id_departement"])),
                    # Re-chiffre l'ID pour l'envoyer dans la réponse
                    "nom_departement": row["nom_departement"],
                    "batiment": row["batiment"],
                })
                print("Données envoyées:", data)  # Log avant la réponse JSON

            return jsonify_utf8(data)
        else:
            return jsonify_utf8({"error": "Aucune région trouvée"}), 404
    # Fin du code à ajouter ici

    if 'id' in request.form:
        # 📍 Traitement des régions (ID de référence)
        encrypted_id = request.form.get('id')
        try:
            id_ref = encryptor('decrypt', encrypted_id)
        except Exception as e:
            return jsonify_utf8({"error": f"Erreur de décryptage de l'ID: {str(e)}"}), 400

        try:
            conn = get_connection()
        except Exception as e:
            return jsonify_utf8({"error": f"Erreur de connexion à la base de données: {str(e)}"}), 500

        try:
            with conn.cursor(dictionary=True) as cursor:
                query = """
                    SELECT * FROM departement 
                    INNER JOIN reference ON reference.id_reference=departement.id_reference 
                    WHERE reference.id_reference = %s
                    ORDER BY departement.id_departement DESC
                """
                cursor.execute(query, (id_ref,))
                result = cursor.fetchall()
        except Exception as e:
            return jsonify_utf8({"error": f"Erreur SQL: {str(e)}"}), 500
        finally:
            conn.close()

        data = []
        for count, row in enumerate(result, 1):
            word_sanitized = re.sub(r"\b\w['`‘’]\b", "", row["nom_departement"])
            abbreviation_debut = word_sanitized.split()
            acronym_debut = "".join([w[0] for w in abbreviation_debut if w])

            data.append(
                {
                    "count": count,
                    "id_departement": encryptor("encrypt", str(row["id_departement"])),
                    "id_departement_raw": row["id_departement"],
                    "acronym_debut": acronym_debut.upper(),
                    "nom_departement": row["nom_departement"],
                    "batiment": row["batiment"],
                }
            )
        return jsonify_utf8(data)

    elif 'id_personnel' in request.form:
        # 👥 Traitement du personnel par région
        encrypted_id = request.form.get('id_personnel')
        print("🔐 id_personnel reçu :", encrypted_id)

        try:
            id_departement = encryptor('decrypt', encrypted_id)
            print("✅ id_region déchiffré :", id_departement)
        except Exception:
            return jsonify_utf8({"error": "Erreur de décryptage"}), 400

        try:
            conn = get_connection()
        except Exception as e:
            return jsonify_utf8({"error": f"Erreur de connexion à la base de données: {str(e)}"}), 500

        try:
            with conn.cursor(dictionary=True) as cursor:
                print("📡 Connexion MySQL réussie")
                query = """ 
                   SELECT * FROM contrat 
                   INNER JOIN employe ON employe.id_employe=contrat.id_employe 
                   INNER JOIN reference ON reference.id_reference=employe.id_reference 
                   INNER JOIN personnel ON contrat.id_contrat=personnel.id_contrat
                   INNER JOIN departement ON departement.id_departement=personnel.id_departement
                   INNER JOIN region ON region.id_region=personnel.id_region
                   WHERE  departement.id_departement = %s
                """
                cursor.execute(query, (id_departement,))
                rows = cursor.fetchall()
                print(f"📦 {len(rows)} lignes récupérées")
        except Exception as e:
            print("❌ Erreur SQL :", str(e))
            return jsonify_utf8({"error": str(e)}), 500
        finally:
            conn.close()

        data = []
        for count, row in enumerate(rows, 1):
            if not row['id_employe']:
                continue

            re_clean = r"\b\w['`‘’]\b"
            code_prenom = re.sub(re_clean, "", row['prenom'])
            code_nom = re.sub(re_clean, "", row['nom'])
            acronym_prenom = "".join([w[0] for w in code_prenom.split()])
            acronym_nom = "".join([w[0] for w in code_nom.split()])
            matricule_format = f"{acronym_prenom}{acronym_nom}-{row['matricule']}"

            data.append(
                {
                    "count": count,
                    "id_employe": encryptor("encrypt", str(row["id_employe"])),
                    "prenom": row["prenom"],
                    "nom": row["nom"],
                    "matricule": matricule_format,
                    "date_n": row["date_n"],
                    "date_n2": (
                        format_date_fr(row["date_n"], style="long")
                        if row.get("date_n")
                        else ""
                    ),
                    "lieu_n": row["lieu_n"],
                    "telephone_e": row["telephone_e"],
                    "adresse_e": row["adresse_e"],
                    "email_e": row["email_e"],
                    "categorie": row["categorie"],
                    "poste_occupe": row["poste_occupe"],
                    "nom_departement": row["nom_departement"],
                    "region": row["region"],
                    "heure_debut": (
                        str(row["heure_debut"]) if row["heure_debut"] else ""
                    ),
                    "heure_decente": (
                        str(row["heure_decente"]) if row["heure_decente"] else ""
                    ),
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
        return jsonify_utf8(data)

    else:
        print("🚫 Aucun paramètre POST reconnu.")
        return jsonify_utf8({"error": "Aucun paramètre reconnu"}), 400
