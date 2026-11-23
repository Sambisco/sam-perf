from flask import request, jsonify, url_for
from templates.include.connect import get_connection
from templates.include.encryptor import encryptor


def fetch_reference_detailed():
    data = {}

    id_encrypted = request.form.get("id_reference")
    if not id_encrypted:
        return jsonify({"status": "error", "message": "id_reference manquant"}), 400

    try:
        id_decrypted = encryptor("decrypt", id_encrypted)

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        query = "SELECT * FROM reference WHERE id_reference = %s"
        cursor.execute(query, (id_decrypted,))
        result = cursor.fetchone()

        if not result:
            return jsonify("0")  # Aucun résultat

        # ✅ Champs texte
        data["id_reference"] = encryptor("encrypt", str(result["id_reference"]))
        data["republique"] = result.get("republique")
        data["devise"] = result.get("devise")
        data["ministere"] = result.get("ministere")
        data["entreprise"] = result.get("entreprise")
        data["adresse"] = result.get("adresse")
        data["telephone"] = result.get("telephone")
        data["fax"] = result.get("fax")
        data["bp"] = result.get("bp")
        data["email"] = result.get("email")
        data["web"] = result.get("web")

        # ✅ Logo avec fallback
        data["logo"] = url_for(
            "static",
            filename=(
                f"img/logo/{result['logo']}"
                if result.get("logo")
                else "img/image/image.jpg"
            ),
        )

        # ✅ Drapeau avec fallback
        data["drapeau"] = url_for(
            "static",
            filename=(
                f"img/drapeau/{result['drapeau']}"
                if result.get("drapeau")
                else "img/image/image.jpg"
            ),
        )

        cursor.close()
        conn.close()

        return jsonify(data)

    except Exception as e:
        print(f"❌ Erreur fetch_reference_detailed: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500
