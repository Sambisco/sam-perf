from flask import Flask, request, jsonify, url_for, Response, session
import re
import locale
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
from templates.include.connect import get_connection
from templates.include.encryptor import encryptor
import qrcode
from io import BytesIO
import base64
import json
from decimal import Decimal
from babel.dates import format_date

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


def notification_rh():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    notifications = []

    if "view" in request.form:
        view = request.form.get("view", "")

        if view != "":
            cursor.execute(
                "UPDATE demande_absence SET comment_status = 1 WHERE comment_status=0"
            )
            conn.commit()

        id_ref = encryptor("decrypt", request.form.get("id", "").strip())

        query = """
            SELECT * FROM demande_absence
            INNER JOIN contrat ON contrat.id_contrat = demande_absence.id_contrat
            INNER JOIN employe ON employe.id_employe = contrat.id_employe
            INNER JOIN reference ON reference.id_reference = employe.id_reference
            WHERE reference.id_reference = %s
            ORDER BY id_demande_absence DESC LIMIT 5
        """
        cursor.execute(query, (id_ref,))
        rows = cursor.fetchall()

        for row in rows:
            photo = (
                url_for(
                    "static",
                    filename=f"img/img_employe/{row.get('matricule','')}/{row.get('photo','')}",
                )
                if row.get("photo")
                else url_for("static", filename="img/image/image-profil.png")
            )
            id_m = request.form.get("id", "")
            profil = session.get("profil")

            if profil in ["Sup-administrateur", "Administrateur"]:
                link_notification = f"../page/demande_absence?id={id_m}&add"
            elif profil:
                link_notification = f"../page/demande_absence?id={id_m}"
            else:
                link_notification = f"../page/demande_absence?id={id_m}&add"

            notifications.append(
                {
                    "link_notification": link_notification,
                    "photo": photo,
                    "prenom": row["prenom"],
                    "nom": row["nom"],
                    "poste_occupe": row["poste_occupe"],
                    "date_v": format_date_fr(row["date_v"], style="full"),
                }
            )

        cursor.execute(
            "SELECT COUNT(*) AS rowcount FROM demande_absence WHERE comment_status=0"
        )
        count_result = cursor.fetchone()

        return jsonify({
            "notifications": notifications,
            "unseen_notification": count_result["rowcount"]
        })

    return jsonify({"notifications": [], "unseen_notification": 0})
