from flask import request, jsonify
from datetime import datetime
import traceback

# Connexion DB et encryptor
from templates.include.connect import get_connection
from templates.include.encryptor import encryptor


def save_conge_maternite():
    conn = None
    cursor = None

    try:
        print("📥 Champs reçus :", request.form.to_dict())
        conn = get_connection()
        cursor = conn.cursor()

        # Insertion
        if "insert_id" in request.form:
            print("✅ Action : insertion")

            id_contrat = encryptor("decrypt", request.form["id_contrat"]).strip()
            print("🔐 id_contrat déchiffré :", id_contrat)

            cursor.execute("SELECT 1 FROM contrat WHERE id_contrat = %s", (id_contrat,))
            if cursor.fetchone() is None:
                print("❌ Aucun contrat trouvé avec cet ID")
                return (
                    jsonify(
                        {
                            "error": "Le contrat spécifié n'existe pas.",
                            "id_contrat": id_contrat,
                        }
                    ),
                    400,
                )

            # Extraction des champs
            numero_decision = request.form.get("numero_decision", "").strip()
            date_decision = request.form.get("date_decision", "").strip()
            date_suspension = request.form.get("date_suspension", "").strip()
            date_debut = request.form.get("date_debut", "").strip()
            date_fin = request.form.get("date_fin", "").strip()
            date_reprise = request.form.get("date_reprise", "").strip()
            nbr_week = request.form.get("nbr_week", "").strip()
            docteur = request.form.get("docteur", "").strip()
            document_cessation = request.form.get("document_cessation", "").strip()
            document_attestation = request.form.get("document_attestation", "").strip()
            document_decision = request.form.get("document_decision", "").strip()
            document_transmission = request.form.get(
                "document_transmission", ""
            ).strip()

            query_insert = """
                INSERT INTO conge_maternite( numero_decision, date_decision, date_suspension, date_debut, date_fin, date_reprise, docteur,nbr_week, document_cessation,document_attestation,document_decision,document_transmission, id_contrat) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """
            cursor.execute(
                query_insert,
                (
                    numero_decision, date_decision, date_suspension, date_debut, date_fin, date_reprise, docteur, nbr_week, document_cessation, document_attestation, document_decision, document_transmission, id_contrat
                ),
            )
            conn.commit()
            return jsonify({"inserted": True})

        # Modification
        elif "edit_id" in request.form:
            print("✅ Action : modification")

            id_conge_maternite = encryptor("decrypt", request.form["edit_id"]).strip()
            numero_decision = request.form.get("numero_decision", "").strip()
            date_decision = request.form.get("date_decision", "").strip()
            date_suspension = request.form.get("date_suspension", "").strip()
            date_debut = request.form.get("date_debut", "").strip()
            date_fin = request.form.get("date_fin", "").strip()
            date_reprise = request.form.get("date_reprise", "").strip()
            nbr_week = request.form.get("nbr_week", "").strip()
            docteur = request.form.get("docteur", "").strip()
            document_cessation = request.form.get("document_cessation", "").strip()
            document_attestation = request.form.get("document_attestation", "").strip()
            document_decision = request.form.get("document_decision", "").strip()
            document_transmission = request.form.get(
                "document_transmission", ""
            ).strip()

            query_update = """
                UPDATE conge_maternite SET numero_decision =%s,date_decision=%s,date_suspension=%s,date_debut=%s,date_fin=%s,date_reprise=%s,nbr_week=%s,docteur=%s,document_cessation=%s,document_attestation=%s,document_decision=%s,document_transmission=%s WHERE id_conge_maternite=%s
            """
            cursor.execute(
                query_update,
                (numero_decision, date_decision, date_suspension, date_debut, date_fin, date_reprise, nbr_week, docteur, document_cessation, document_attestation, document_decision, document_transmission,id_conge_maternite
                ),
            )
            conn.commit()
            return jsonify({"updated": True})

        # Suppression
        elif "delete_id" in request.form:
            print("✅ Action : suppression")

            id_conge_maternite = encryptor("decrypt", request.form["delete_id"]).strip()

            query_delete = "DELETE FROM conge_maternite WHERE id_conge_maternite = %s"
            cursor.execute(query_delete, (id_conge_maternite,))
            conn.commit()
            return jsonify({"deleted": True})

        # Si aucune action valide
        return jsonify({"error": "Requête invalide"}), 400

    except Exception as e:
        print("❌ ERREUR dans save_conge_maternite :", type(e).__name__)
        print("🧵 Détail de l'erreur :", e)
        traceback.print_exc()
        return (
            jsonify(
                {"error": "Erreur serveur", "type": type(e).__name__, "details": str(e)}
            ),
            500,
        )

    finally:
        if cursor:
            try:
                cursor.close()
            except:
                pass
        if conn:
            try:
                conn.close()
            except:
                pass
