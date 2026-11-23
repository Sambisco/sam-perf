from flask import request, jsonify
from datetime import date
from templates.include.connect import get_connection
from templates.include.encryptor import encryptor

def save_domiciliation_salaire():
    try:
        conn = get_connection()
        cursor = conn.cursor()
        today = date.today().strftime("%Y-%m-%d")

        # INSERT
        if "insert_id" in request.form:
            id_contrat = encryptor(
                "decrypt", request.form.get("id_contrat", "")
            ).strip()
            date_embauche = request.form.get("date_embauche", "").strip()
            poste_occupe = request.form.get("poste_occupe", "").strip()
            duree_contrat = request.form.get("duree_contrat", "").strip()

            salaire_net_chiffre = (
                request.form.get("salaire_net_chiffre", "")
                .replace(" ", "")
                .replace(",", ".")
                .strip()
            )
            salaire_net_lettre = request.form.get("salaire_net_lettre", "").strip()
            banque = request.form.get("banque", "").strip()
            numero_compte = request.form.get("numero_compte", "").strip()
            document_lettre_domiciliation = request.form.get(
                "document_lettre_domiciliation", ""
            ).strip()

            query = """
                INSERT INTO domiciliation_salaire (
                    date, date_embauche, poste_occupe, duree_contrat,
                    salaire_net_chiffre, salaire_net_lettre,
                    banque, numero_compte, document_lettre_domiciliation, id_contrat
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(
                query,
                (
                    today,
                    date_embauche,
                    poste_occupe,
                    duree_contrat,
                    salaire_net_chiffre,
                    salaire_net_lettre,
                    banque,
                    numero_compte,
                    document_lettre_domiciliation,
                    id_contrat,
                ),
            )

        # UPDATE
        elif "edit_id" in request.form:
            id_edit = encryptor("decrypt", request.form.get("edit_id", "")).strip()
            date_embauche = request.form.get("date_embauche", "").strip()
            poste_occupe = request.form.get("poste_occupe", "").strip()
            duree_contrat = request.form.get("duree_contrat", "").strip()

            salaire_net_chiffre = (
                request.form.get("salaire_net_chiffre", "")
                .replace(" ", "")
                .replace(",", ".")
                .strip()
            )
            salaire_net_lettre = request.form.get("salaire_net_lettre", "").strip()
            banque = request.form.get("banque", "").strip()
            numero_compte = request.form.get("numero_compte", "").strip()
            document_lettre_domiciliation = request.form.get(
                "document_lettre_domiciliation", ""
            ).strip()

            query = """
                UPDATE domiciliation_salaire
                SET date=%s, date_embauche=%s, poste_occupe=%s,
                    duree_contrat=%s, salaire_net_chiffre=%s, salaire_net_lettre=%s,
                    banque=%s, numero_compte=%s, document_lettre_domiciliation=%s
                WHERE id_domiciliation_salaire=%s
            """
            cursor.execute(
                query,
                (
                    today,
                    date_embauche,
                    poste_occupe,
                    duree_contrat,
                    salaire_net_chiffre,
                    salaire_net_lettre,
                    banque,
                    numero_compte,
                    document_lettre_domiciliation,
                    id_edit,
                ),
            )

        # DELETE
        elif "delete_id" in request.form:
            id_delete = encryptor("decrypt", request.form.get("delete_id", "")).strip()
            query = (
                "DELETE FROM domiciliation_salaire WHERE id_domiciliation_salaire=%s"
            )
            cursor.execute(query, (id_delete,))

        conn.commit()
        return jsonify(
            {"status": "success", "message": "Opération effectuée avec succès"}
        )

    except Exception as e:
        print("Erreur :", e)
        return jsonify({"status": "error", "message": str(e)}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
