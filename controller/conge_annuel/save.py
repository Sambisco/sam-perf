from flask import request, jsonify
from datetime import datetime
import traceback

# Connexion DB et encryptor
from templates.include.connect import get_connection
from templates.include.encryptor import encryptor


def save_conge_annuel():
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
            date_debut = request.form.get("date_debut", "").strip()
            date_fin = request.form.get("date_fin", "").strip()
            nbr_conge = request.form.get("nbr_conge", "").strip()
            nbr_conge_supplementaire = request.form.get(
                "nbr_conge_supplementaire", ""
            ).strip()
            document_conge = request.form.get("document_conge", "").strip()
            annee_annee = f"{datetime.now().year - 1}-{datetime.now().year}"

            query_insert = """
                INSERT INTO conge_annuel (
                    date_debut, date_fin, nbr_conge, nbr_conge_supplementaire,
                    annee_annee, document_conge, id_contrat
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(
                query_insert,
                (
                    date_debut,
                    date_fin,
                    nbr_conge,
                    nbr_conge_supplementaire,
                    annee_annee,
                    document_conge,
                    id_contrat,
                ),
            )
            conn.commit()
            return jsonify({"inserted": True})

        # Modification
        elif "edit_id" in request.form:
            print("✅ Action : modification")

            id_conge_annuel = encryptor("decrypt", request.form["edit_id"]).strip()

            date_debut = request.form.get("date_debut", "").strip()
            date_fin = request.form.get("date_fin", "").strip()
            nbr_conge = request.form.get("nbr_conge", "").strip()
            nbr_conge_supplementaire = request.form.get(
                "nbr_conge_supplementaire", ""
            ).strip()
            document_conge = request.form.get("document_conge", "").strip()

            query_update = """
                UPDATE conge_annuel
                SET date_debut = %s, date_fin = %s, nbr_conge = %s,
                    nbr_conge_supplementaire = %s, document_conge = %s
                WHERE id_conge_annuel = %s
            """
            cursor.execute(
                query_update,
                (
                    date_debut,
                    date_fin,
                    nbr_conge,
                    nbr_conge_supplementaire,
                    document_conge,
                    id_conge_annuel,
                ),
            )
            conn.commit()
            return jsonify({"updated": True})

        # Suppression
        elif "delete_id" in request.form:
            print("✅ Action : suppression")

            id_conge_annuel = encryptor("decrypt", request.form["delete_id"]).strip()

            query_delete = "DELETE FROM conge_annuel WHERE id_conge_annuel = %s"
            cursor.execute(query_delete, (id_conge_annuel,))
            conn.commit()
            return jsonify({"deleted": True})

        # Si aucune action valide
        return jsonify({"error": "Requête invalide"}), 400

    except Exception as e:
        print("❌ ERREUR dans save_conge_annuel :", type(e).__name__)
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
