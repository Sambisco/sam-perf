from flask import Flask, request, jsonify
from templates.include.connect import get_connection
from templates.include.encryptor import encryptor
import re


def fetch_document_administratif():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        if "id_document_administratif" in request.form:
            count_id = encryptor("decrypt", request.form["id_document_administratif"])
            query = """
            SELECT count_id, corps_text FROM lettre_affectation
            INNER JOIN reference ON reference.id_reference = lettre_affectation.id_reference
            WHERE count_id = %s
            UNION
            SELECT count_id, corps_text FROM lettre_attestation
            INNER JOIN reference ON reference.id_reference = lettre_attestation.id_reference
            WHERE count_id = %s
            UNION
            SELECT count_id, corps_text FROM lettre_cessation
            INNER JOIN reference ON reference.id_reference = lettre_cessation.id_reference
            WHERE count_id = %s
            UNION
            SELECT count_id, corps_text FROM lettre_conge_annuel
            INNER JOIN reference ON reference.id_reference = lettre_conge_annuel.id_reference
            WHERE count_id = %s
            UNION
            SELECT count_id, corps_text FROM lettre_contrat
            INNER JOIN reference ON reference.id_reference = lettre_contrat.id_reference
            WHERE count_id = %s
            UNION
            SELECT count_id, corps_text FROM lettre_decision
            INNER JOIN reference ON reference.id_reference = lettre_decision.id_reference
            WHERE count_id = %s
            UNION
            SELECT count_id, corps_text FROM lettre_indemnite
            INNER JOIN reference ON reference.id_reference = lettre_indemnite.id_reference
            WHERE count_id = %s
            UNION
            SELECT count_id, corps_text FROM lettre_transmission
            INNER JOIN reference ON reference.id_reference = lettre_transmission.id_reference
            WHERE count_id = %s
            UNION
            SELECT count_id, corps_text FROM lettre_certificat_travail
            INNER JOIN reference ON reference.id_reference = lettre_certificat_travail.id_reference
            WHERE count_id = %s
            UNION
            SELECT count_id, corps_text FROM lettre_domiciliation_salaire
            INNER JOIN reference ON reference.id_reference = lettre_domiciliation_salaire.id_reference
            WHERE count_id = %s
            """
            values = [count_id] * 10
            print("id_document_administratif décrypté:", count_id)
            print("Paramètres passés:", values)
            cursor.execute(query, values)
            result = cursor.fetchall()

            if result:
                row = result[0]
                data = {
                    "id_document_administratif": encryptor(
                        "encrypt", str(row["count_id"])
                    ),
                    "corps_text": row["corps_text"],
                }
                return jsonify(data)
            else:
                return jsonify("0")

        elif "id" in request.form:
            id_reference = encryptor("decrypt", request.form["id"])
            query = """
            SELECT count_id, affectation AS texte FROM lettre_affectation
            INNER JOIN reference ON reference.id_reference = lettre_affectation.id_reference
            WHERE reference.id_reference = %s
            UNION
            SELECT count_id, attestation AS texte FROM lettre_attestation
            INNER JOIN reference ON reference.id_reference = lettre_attestation.id_reference
            WHERE reference.id_reference = %s
            UNION
            SELECT count_id, cessation AS texte FROM lettre_cessation
            INNER JOIN reference ON reference.id_reference = lettre_cessation.id_reference
            WHERE reference.id_reference = %s
            UNION
            SELECT count_id, conge_annuel AS texte FROM lettre_conge_annuel
            INNER JOIN reference ON reference.id_reference = lettre_conge_annuel.id_reference
            WHERE reference.id_reference = %s
            UNION
            SELECT count_id, contrat_corpes AS texte FROM lettre_contrat
            INNER JOIN reference ON reference.id_reference = lettre_contrat.id_reference
            WHERE reference.id_reference = %s
            UNION
            SELECT count_id, conge_maternite AS texte FROM lettre_decision
            INNER JOIN reference ON reference.id_reference = lettre_decision.id_reference
            WHERE reference.id_reference = %s
            UNION
            SELECT count_id, indemnite AS texte FROM lettre_indemnite
            INNER JOIN reference ON reference.id_reference = lettre_indemnite.id_reference
            WHERE reference.id_reference = %s
            UNION
            SELECT count_id, transmission AS texte FROM lettre_transmission
            INNER JOIN reference ON reference.id_reference = lettre_transmission.id_reference
            WHERE reference.id_reference = %s
            UNION
            SELECT count_id, certificat AS texte FROM lettre_certificat_travail
            INNER JOIN reference ON reference.id_reference = lettre_certificat_travail.id_reference
            WHERE reference.id_reference = %s
            UNION
            SELECT count_id, domiciliation_salaire AS texte FROM lettre_domiciliation_salaire
            INNER JOIN reference ON reference.id_reference = lettre_domiciliation_salaire.id_reference
            WHERE reference.id_reference = %s
            """
            values = [id_reference] * 10
            print("id_reference décrypté:", id_reference)
            print("Paramètres passés:", values)
            cursor.execute(query, values)
            results = cursor.fetchall()

            data = []
            for row in results:
                texte = row.get("texte", "")
                # Nettoyage simple (sans regex complexe)
                words = texte.split()
                acronym = "".join(word[0] for word in words if word)
                data.append(
                    {
                        "count_id": encryptor("encrypt", str(row["count_id"])),
                        "affectation": texte,
                        "acronym_prenom": acronym.upper(),
                    }
                )
            return jsonify(data)

        else:
            return jsonify({"error": "Aucune donnée valide reçue"})

    except Exception as e:
        print("Erreur fetch_document_administratif:", e)
        return jsonify({"error": str(e)})

    finally:
        cursor.close()
        conn.close()
