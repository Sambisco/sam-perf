import locale
import regex as re_unicode  # pour support \p{L}
from datetime import datetime, date
from flask import Flask, request, jsonify, url_for
from templates.include.connect import get_connection
from templates.include.encryptor import encryptor
from babel.dates import format_date as babel_format_date

# Config locale française (différentes options selon OS)
try:
    locale.setlocale(locale.LC_TIME, "fr_FR.UTF-8")
except locale.Error:
    try:
        locale.setlocale(locale.LC_TIME, "French_France")
    except locale.Error:
        print("Locale française non disponible, dates au format par défaut")


def get_acronym(text):
    if not text:
        return ""
    # Enlève les apostrophes isolées (ex: d’)
    cleaned_text = re_unicode.sub(r"\b\p{L}[\'`‘’]\b", "", text)
    parts = cleaned_text.split()
    return "".join([w[0].upper() for w in parts if w])


def format_date_fr(date_str):
    try:
        if not date_str:
            return ""
        if isinstance(date_str, (datetime, date)):
            dt = date_str
        else:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
        return babel_format_date(
            dt, format="EEEE d MMMM yyyy", locale="fr_FR"
        ).capitalize()
    except Exception:
        return ""


def format_number(num):
    try:
        if num is None:
            return "0"
        return f"{num:,.0f}".replace(",", " ").replace(".", ",")
    except Exception:
        return "0"


def fetch_user():
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        if "id_user" in request.form:
            id_user = encryptor("decrypt", request.form["id_user"])
            query = """
                SELECT * FROM sub_users WHERE id_sub_users = %s
            """
            cursor.execute(query, (id_user,))
            row = cursor.fetchone()
            if not row:
                return jsonify("0")

            data = {
                "id_sub_users": encryptor("encrypt", str(row["id_sub_users"])),
                "nom_sub_user": row["nom_sub_user"],
                "telephone_sub_user": row["telephone_sub_user"],
                "sub_email": row["sub_email"],
                "profil": row["profil"],
                "photo": (
                    url_for(
                        "static",
                        filename=f"img/user/{row.get('photo','')}",
                    )
                    if row.get("photo")
                    else url_for("static", filename="img/image/image-profil.png")
                ),
            }
            return jsonify(data)

        elif "id" in request.form:
            id_reference = encryptor("decrypt", str(request.form["id"]))
            query = """
                SELECT * FROM sub_users 
                INNER JOIN reference ON reference.id_reference=sub_users.id_reference 
                 WHERE reference.id_reference= %s 
                 ORDER BY sub_users.id_sub_users DESC
            """
            cursor.execute(query, (id_reference,))
            rows = cursor.fetchall()

            data = []
            for i, row in enumerate(rows, start=1):

                data.append(
                    {
                        "count": i,
                        "id_sub_users": encryptor("encrypt", str(row["id_sub_users"])),
                        "nom_sub_user": row["nom_sub_user"],
                        "telephone_sub_user": row["telephone_sub_user"],
                        "sub_email": row["sub_email"],
                        "profil": row["profil"],
                        "photo": (
                            url_for(
                                "static",
                                filename=f"img/user/{row.get('photo','')}",
                            )
                            if row.get("photo")
                            else url_for(
                                "static", filename="img/image/image-profil.png"
                            )
                        ),
                    }
                )
            return jsonify(data)

        else:
            return jsonify("Aucun paramètre valide reçu.")

    except Exception as e:
        print(f"Erreur dans fetch_cotisation: {e}")
        return jsonify({"error": "Erreur serveur interne"}), 500
