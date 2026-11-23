from webauthn import generate_registration_options
from webauthn.helpers import bytes_to_base64url

# Stockage temporaire en mémoire
EMPLOYEES = {}


def enroll():
    from flask import request, jsonify

    id_employe = request.form.get("id_employe")
    if not id_employe:
        return jsonify({"error": "id_employe manquant"}), 400

    try:
        options = generate_registration_options(
            rp_id="192.168.43.160",  # ton IP locale
            rp_name="EntrepriseTest",
            user_id=id_employe.encode(),
            user_name=f"user{id_employe}",
            attestation="none",
        )

        EMPLOYEES[id_employe] = bytes_to_base64url(options.challenge)
        return jsonify(options.json)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
