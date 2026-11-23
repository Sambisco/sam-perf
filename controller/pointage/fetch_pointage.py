from flask import Flask, request, jsonify, url_for
from templates.include.connect import get_connection
from templates.include.encryptor import encryptor
from datetime import datetime, date, timedelta
import re
from babel.dates import format_date


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


def acronyme(texte):
    texte = re.sub(r"[\u2018\u2019'`]", "", texte)
    mots = texte.split()
    return "".join([mot[0].upper() for mot in mots if mot])


def timedelta_to_hhmmss(td):
    if td is None:
        return ""
    total_seconds = int(td.total_seconds())
    heures = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secondes = total_seconds % 60
    return f"{heures:02d}:{minutes:02d}:{secondes:02d}"


def fetch_pointage():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # Cas 1 : id + date => résumé contrats et pointages mensuels
    if "id" in request.form and "date" in request.form:
        id_encrypted = request.form.get("id")
        date_str = request.form.get("date")  # format YYYY-MM
        try:
            id_decrypted = encryptor("decrypt", id_encrypted)
        except Exception:
            cursor.close()
            conn.close()
            return jsonify({"error": "ID invalide"}), 400

        try:
            annee_mois = datetime.strptime(date_str, "%Y-%m")
        except Exception:
            cursor.close()
            conn.close()
            return jsonify({"error": "Format de date invalide, attendu YYYY-MM"}), 400

        debut_mois = annee_mois.replace(day=1)
        if debut_mois.month == 12:
            debut_mois_suivant = debut_mois.replace(
                year=debut_mois.year + 1, month=1, day=1
            )
        else:
            debut_mois_suivant = debut_mois.replace(month=debut_mois.month + 1, day=1)

        query = """
            SELECT * FROM contrat
            INNER JOIN employe ON employe.id_employe = contrat.id_employe
            INNER JOIN reference ON reference.id_reference = employe.id_reference
            WHERE NOT EXISTS (SELECT * FROM depart WHERE contrat.id_contrat = depart.id_contrat)
              AND reference.id_reference = %s
            ORDER BY employe.id_employe DESC
        """
        cursor.execute(query, (id_decrypted,))
        results = cursor.fetchall()

        data = []
        count = 0

        for row in results:
            count += 1
            response = {}

            id_contrat = row["id_contrat"]

            cursor.execute(
                """
                SELECT 
                    COALESCE(SUM(HOUR(TIMEDIFF(heure_fin, heure_debut))), 0) AS heure,
                    COUNT(pointage.id_contrat) AS nbr_jour
                FROM pointage
                WHERE id_contrat = %s
                  AND date >= %s
                  AND date < %s
                """,
                (
                    id_contrat,
                    debut_mois.strftime("%Y-%m-%d"),
                    debut_mois_suivant.strftime("%Y-%m-%d"),
                ),
            )
            pointage_data = cursor.fetchone()

            response["nbr_jour"] = f"{pointage_data['nbr_jour']} Jours"
            response["heure"] = f"{pointage_data['heure']} Heures"

            # Congé annuel
            cursor.execute(
                "SELECT * FROM conge_annuel WHERE id_contrat = %s",
                (id_contrat,),
            )
            conge = cursor.fetchone()
            if conge and conge["date_debut"] and conge["date_fin"]:
                start = conge["date_debut"].strftime("%Y-%m")
                end = conge["date_fin"].strftime("%Y-%m")
                if start <= date_str <= end:
                    response["affiche"] = (
                        "<h5><span style='background:rgba(251, 54, 54, 0.1);padding:7px;border-radius:5px;'>"
                        "Congé annuel &nbsp;&nbsp;<i class='fas fa-ban fa-1x'></i></span></h5>"
                    )
                else:
                    response["affiche"] = (
                        "<h5><span style='background:rgba(11,156,49,0.1);padding:7px;border-radius:5px;'>"
                        "Actif&nbsp;&nbsp;<i class='fas fa-check fa-1x'></i></span></h5>"
                    )
            else:
                response["affiche"] = (
                    "<h5><span style='background:rgba(11,156,49,0.1);padding:7px;border-radius:5px;'>"
                    "Actif&nbsp;&nbsp;<i class='fas fa-check fa-1x'></i></span></h5>"
                )

            # Congé maternité si femme
            if row["genre"].lower() == "feminin":
                cursor.execute(
                    "SELECT * FROM conge_maternite WHERE id_contrat = %s ORDER BY id_conge_maternite DESC LIMIT 1",
                    (id_contrat,),
                )
                maternite = cursor.fetchone()
                if maternite and maternite["date_debut"] and maternite["date_fin"]:
                    start = maternite["date_debut"].strftime("%Y-%m")
                    end = maternite["date_fin"].strftime("%Y-%m")
                    if start <= date_str <= end:
                        response["affiche"] = (
                            "<h5><span style='background:rgba(251, 54, 54, 0.1);padding:7px;border-radius:5px;'>"
                            "Congé maternité &nbsp;&nbsp;<i class='fas fa-ban fa-1x'></i></span></h5>"
                        )

            response["count"] = count
            response["id_contrat"] = encryptor("encrypt", str(row["id_contrat"]))
            response["id_employe"] = encryptor("encrypt", str(row["id_employe"]))
            response["prenom"] = row["prenom"]
            response["nom"] = row["nom"]
            response["matricule"] = (
                f"{acronyme(row['prenom'])}{acronyme(row['nom'])}-{row['matricule']}"
            )
            response["poste_occupe"] = row["poste_occupe"]
            response["photo"] = (
                (
                    url_for(
                        "static",
                        filename=f"img/img_employe/{row.get('matricule','')}/{row.get('photo','')}",
                    )
                    if row.get("photo")
                    else url_for("static", filename="img/image/image-profil.png")
                ),
            )
            data.append(response)

        cursor.close()
        conn.close()
        return jsonify(data)

    # Cas 2 : id_contrat + date_pointage => détail pointages du contrat sur mois
    elif "id_contrat" in request.form and "date_pointage" in request.form:
        try:
            id_decrypted = encryptor("decrypt", request.form["id_contrat"])
        except Exception:
            cursor.close()
            conn.close()
            return jsonify({"error": "ID invalide"}), 400

        date_str = request.form.get("date_pointage")
        try:
            annee_mois = datetime.strptime(date_str, "%Y-%m")
        except Exception:
            cursor.close()
            conn.close()
            return jsonify({"error": "Format de date invalide, attendu YYYY-MM"}), 400

        debut_mois = annee_mois.replace(day=1)
        if debut_mois.month == 12:
            debut_mois_suivant = debut_mois.replace(
                year=debut_mois.year + 1, month=1, day=1
            )
        else:
            debut_mois_suivant = debut_mois.replace(month=debut_mois.month + 1, day=1)

        query = """
            SELECT 
                pointage.date,
                pointage.heure_debut,
                pointage.heure_fin,
                HOUR(TIMEDIFF(pointage.heure_fin, pointage.heure_debut)) AS heure
            FROM pointage 
            INNER JOIN contrat ON contrat.id_contrat=pointage.id_contrat 
            INNER JOIN employe ON employe.id_employe=contrat.id_employe 
            INNER JOIN reference ON reference.id_reference=employe.id_reference 
            WHERE contrat.id_contrat=%s AND pointage.date >= %s AND pointage.date < %s
            ORDER BY pointage.date ASC, pointage.heure_debut ASC
        """
        cursor.execute(
            query,
            (
                id_decrypted,
                debut_mois.strftime("%Y-%m-%d"),
                debut_mois_suivant.strftime("%Y-%m-%d"),
            ),
        )
        results = cursor.fetchall()

        data = []
        for row in results:
            data.append(
                {
                    "date": format_date_fr(row["date"], style="full"),
                    "heure_debut": timedelta_to_hhmmss(row["heure_debut"]),
                    "heure_fin": timedelta_to_hhmmss(row["heure_fin"]),
                    "heure": row["heure"] or 0,
                }
            )

        cursor.close()
        conn.close()

        return jsonify(data)

    elif "id_pointage" in request.form :
        date_str = datetime.now().strftime("%Y-%m-%d")
        try:
            id_decrypted = encryptor("decrypt", request.form["id_pointage"].strip())
        except Exception:
            return jsonify({"error": "ID invalide"}), 400

        with get_connection() as conn:
            with conn.cursor(dictionary=True) as cursor:
                query = """
                    SELECT * FROM pointage
                    INNER JOIN contrat ON contrat.id_contrat = pointage.id_contrat
                    INNER JOIN employe ON employe.id_employe = contrat.id_employe AND pointage.date = %s
                    INNER JOIN reference ON reference.id_reference = employe.id_reference
                    WHERE reference.id_reference = %s
                    ORDER BY pointage.id_pointage DESC
                """
                cursor.execute(query, (date_str, id_decrypted))
                results = cursor.fetchall()

                data = []
                for row in results:
                    # Traitement acronymes prénom et nom

                    # Formatage date en français

                    data.append(
                        {
                            "prenom": row["prenom"],
                            "nom": row["nom"],
                            "matricule": f"{acronyme(row['prenom'])}{acronyme(row['nom'])}-{row['matricule']}",
                            "poste_occupe": row["poste_occupe"],
                            "date": format_date_fr(row["date"], style="full"),
                            "heure_debut": timedelta_to_hhmmss(row["heure_debut"]),
                            "heure_fin": timedelta_to_hhmmss(row["heure_fin"]),
                            "photo": (
                                (
                                    url_for(
                                        "static",
                                        filename=f"img/img_employe/{row.get('matricule','')}/{row.get('photo','')}",
                                    )
                                    if row.get("photo")
                                    else url_for(
                                        "static", filename="img/image/image-profil.png"
                                    )
                                ),
                            ),
                        }
                    )

                return jsonify(data)

    elif "id_p" in request.form:
        date_str = datetime.now().strftime("%Y-%m-%d")
        try:
            id_decrypted = request.form["id_p"].strip()
        except Exception:
            return jsonify({"error": "ID invalide"}), 400

        with get_connection() as conn:
            with conn.cursor(dictionary=True) as cursor:
                query = """
                    SELECT * FROM pointage
                    INNER JOIN contrat ON contrat.id_contrat = pointage.id_contrat
                    INNER JOIN employe ON employe.id_employe = contrat.id_employe AND pointage.date = %s
                    INNER JOIN reference ON reference.id_reference = employe.id_reference
                    WHERE pointage.id_sub_users = %s
                    ORDER BY pointage.id_pointage DESC
                """
                cursor.execute(query, (date_str, id_decrypted))
                results = cursor.fetchall()

                data = []
                for row in results:
                    # Traitement acronymes prénom et nom

                    # Formatage date en français

                    data.append(
                        {
                            "prenom": row["prenom"],
                            "nom": row["nom"],
                            "matricule": f"{acronyme(row['prenom'])}{acronyme(row['nom'])}-{row['matricule']}",
                            "poste_occupe": row["poste_occupe"],
                            "date": format_date_fr(row["date"], style="full"),
                            "heure_debut": timedelta_to_hhmmss(row["heure_debut"]),
                            "heure_fin": timedelta_to_hhmmss(row["heure_fin"]),
                            "photo": (
                                (
                                    url_for(
                                        "static",
                                        filename=f"img/img_employe/{row.get('matricule','')}/{row.get('photo','')}",
                                    )
                                    if row.get("photo")
                                    else url_for(
                                        "static", filename="img/image/image-profil.png"
                                    )
                                ),
                            ),
                        }
                    )

                return jsonify(data)

    elif "id_pointage_scan" in request.form:
        date_str = datetime.now().strftime("%Y-%m-%d")
        try:
            id_decrypted = encryptor(
                "decrypt", request.form["id_pointage_scan"].strip()
            )
        except Exception:
            return jsonify({"error": "ID invalide"}), 400

        with get_connection() as conn:
            with conn.cursor(dictionary=True) as cursor:
                query = """
                    SELECT * FROM pointage
                    INNER JOIN contrat ON contrat.id_contrat = pointage.id_contrat
                    INNER JOIN employe ON employe.id_employe = contrat.id_employe AND pointage.date = %s
                    INNER JOIN reference ON reference.id_reference = employe.id_reference
                    WHERE reference.id_reference = %s
                    ORDER BY date_heure DESC
                """
                cursor.execute(query, (date_str, id_decrypted))
                results = cursor.fetchall()

                data = []
                for row in results:
                    # Traitement acronymes prénom et nom

                    # Formatage date en français

                    data.append(
                        {
                            "prenom": row["prenom"],
                            "nom": row["nom"],
                            "matricule": f"{acronyme(row['prenom'])}{acronyme(row['nom'])}-{row['matricule']}",
                            "poste_occupe": row["poste_occupe"],
                            "date": format_date_fr(row["date"], style="full"),
                            "heure_debut": timedelta_to_hhmmss(row["heure_debut"]),
                            "heure_fin": timedelta_to_hhmmss(row["heure_fin"]),
                            "photo": (
                                (
                                    url_for(
                                        "static",
                                        filename=f"img/img_employe/{row.get('matricule','')}/{row.get('photo','')}",
                                    )
                                    if row.get("photo")
                                    else url_for(
                                        "static", filename="img/image/image-profil.png"
                                    )
                                ),
                            ),
                        }
                    )

                return jsonify(data)

    else:
        return jsonify({"error": "Paramètres manquants"}), 400
