from flask import jsonify, url_for, request
from templates.include.connect import get_connection
from templates.include.encryptor import encryptor
from datetime import datetime, date
from babel.dates import format_date
import re

# Fonctions utilitaires
def format_date_fr(date_str, style="long"):
    try:
        if not date_str:
            return ""
        if isinstance(date_str, (datetime, date)):
            dt = date_str
        else:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
        if style == "full":
            fmt = "EEEE d MMMM yyyy"
        elif style == "month":
            fmt = "MMMM yyyy"
        elif style == "years":
            fmt = "yyyy"
        else:
            fmt = "dd MMMM yyyy"
        return format_date(dt, format=fmt, locale="fr_FR").capitalize()
    except Exception:
        return ""


def format_number(value):
    if value is None or value == 0:
        return ""
    return "{:,.0f}".format(value).replace(",", " ")


def make_acronym(word: str) -> str:
    # Supprimer caractères spéciaux style apostrophe
    cleaned = word.replace("'", "").replace("’", "").replace("`", "")
    parts = cleaned.split()
    return "".join([p[0].upper() for p in parts if p])


# --- Endpoint principal ---
def tableau_gs():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    data = []

    try:
        # === TABLEAU 1: detail_entree ===
        if "tableau1" in request.form:
            id_ref = encryptor("decrypt", request.form["tableau1"])
            date = request.form.get("date", "")
            date_du1 = request.form.get("date_du1", "")
            date_au1 = request.form.get("date_au1", "")

            if not date_du1 and not date_au1:
                query = """
                    SELECT * FROM detail_entree 
                    INNER JOIN entree ON entree.id_entree=detail_entree.id_entree 
                    INNER JOIN matiere ON matiere.id_matiere=detail_entree.id_matiere 
                    INNER JOIN categorie_article ON categorie_article.id_categorie_article=matiere.id_categorie_article 
                    INNER JOIN reference ON reference.id_reference=categorie_article.id_reference
                    WHERE reference.id_reference=%s AND DATE_FORMAT(entree.date_entree,'%Y')=%s
                """
                cursor.execute(query, (id_ref, date))
            else:
                query = """
                    SELECT * FROM detail_entree 
                    INNER JOIN entree ON entree.id_entree=detail_entree.id_entree 
                    INNER JOIN matiere ON matiere.id_matiere=detail_entree.id_matiere 
                    INNER JOIN categorie_article ON categorie_article.id_categorie_article=matiere.id_categorie_article 
                    INNER JOIN reference ON reference.id_reference=categorie_article.id_reference
                    WHERE reference.id_reference=%s AND DATE_FORMAT(entree.date_entree,'%Y-%m') BETWEEN %s AND %s
                """
                cursor.execute(query, (id_ref, date_du1, date_au1))

            result = cursor.fetchall()
            for count, row in enumerate(result, 1):
                response = {
                    "count": count,
                    "numero": str(row["numero"]).zfill(7),
                    "date_entree": format_date_fr(str(row["date_entree"])),
                    "designation": row["designation"],
                    "quantite": row["quantite"],
                    "nature_unite": row["nature_unite"],
                    "prix_unitaire": f"{row['prix_unitaire']:,.0f}".replace(",", " "),
                    "total_entree": f"{row['total_entree']:,.0f}".replace(",", " "),
                    "image": url_for(
                        "static",
                        filename=(
                            f"img/matiere/{row['image']}"
                            if row["image"]
                            else "img/image/image.jpg"
                        ),
                    ),
                }
                data.append(response)

        # === TABLEAU 2: detail_sortie ===
        elif "tableau2" in request.form:
            id_ref = encryptor("decrypt", request.form["tableau2"])
            date = request.form.get("date", "")
            date_du2 = request.form.get("date_du2", "")
            date_au2 = request.form.get("date_au2", "")

            if not date_du2 and not date_au2:
                query = """
                    SELECT * FROM detail_sortie 
                    INNER JOIN sortie ON sortie.id_sortie=detail_sortie.id_sortie
                    INNER JOIN contrat ON contrat.id_contrat=sortie.id_contrat
                    INNER JOIN employe ON employe.id_employe=contrat.id_employe
                    INNER JOIN matiere ON matiere.id_matiere=detail_sortie.id_matiere 
                    INNER JOIN categorie_article ON categorie_article.id_categorie_article=matiere.id_categorie_article 
                    INNER JOIN reference ON reference.id_reference=categorie_article.id_reference
                    WHERE reference.id_reference=%s AND DATE_FORMAT(sortie.date_sortie,'%Y')=%s
                """
                cursor.execute(query, (id_ref, date))
            else:
                query = """
                    SELECT * FROM detail_sortie 
                    INNER JOIN sortie ON sortie.id_sortie=detail_sortie.id_sortie
                    INNER JOIN contrat ON contrat.id_contrat=sortie.id_contrat
                    INNER JOIN employe ON employe.id_employe=contrat.id_employe
                    INNER JOIN matiere ON matiere.id_matiere=detail_sortie.id_matiere 
                    INNER JOIN categorie_article ON categorie_article.id_categorie_article=matiere.id_categorie_article 
                    INNER JOIN reference ON reference.id_reference=categorie_article.id_reference
                    WHERE reference.id_reference=%s AND DATE_FORMAT(sortie.date_sortie,'%Y-%m') BETWEEN %s AND %s
                """
                cursor.execute(query, (id_ref, date_du2, date_au2))

            result = cursor.fetchall()
            for count, row in enumerate(result, 1):
                acronym_prenom = make_acronym(row.get("prenom"))
                acronym_nom = make_acronym(row.get("nom"))
                response = {
                    "count": count,
                    "numero": str(row["numero"]).zfill(7),
                    "date_sortie": format_date_fr(str(row["date_sortie"])),
                    "designation": row["designation"],
                    "quantite": row["quantite"],
                    "nature_unite": row["nature_unite"],
                    "prenom": row["prenom"],
                    "nom": row["nom"],
                    "matricule": f"{acronym_prenom}{acronym_nom}-{row.get('matricule')}",
                    "poste_occupe": row["poste_occupe"],
                    "photo": (
                    url_for(
                        "static",
                        filename=f"img/img_employe/{row.get('matricule','')}/{row.get('photo','')}",
                    )
                    if row.get("photo")
                    else url_for("static", filename="img/image/image-profil.png")
                ),
                }
                data.append(response)

        # === TABLEAU 3: detail_affectation ===
        elif "tableau3" in request.form:
            id_ref = encryptor("decrypt", request.form["tableau3"])
            date = request.form.get("date", "")
            date_du3 = request.form.get("date_du3", "")
            date_au3 = request.form.get("date_au3", "")

            if not date_du3 and not date_au3:
                query = """
                    SELECT * FROM detail_affectation 
                    INNER JOIN affectation_matiere ON affectation_matiere.id_affectation_matiere=detail_affectation.id_affectation_matiere 
                    INNER JOIN contrat ON contrat.id_contrat=affectation_matiere.id_contrat
                    INNER JOIN employe ON employe.id_employe=contrat.id_employe
                    INNER JOIN matiere ON matiere.id_matiere=detail_affectation.id_matiere 
                    INNER JOIN categorie_article ON categorie_article.id_categorie_article=matiere.id_categorie_article 
                    INNER JOIN reference ON reference.id_reference=categorie_article.id_reference
                    WHERE reference.id_reference=%s AND DATE_FORMAT(affectation_matiere.date_affectation,'%Y')=%s
                """
                cursor.execute(query, (id_ref, date))
            else:
                query = """
                    SELECT * FROM detail_affectation 
                    INNER JOIN affectation_matiere ON affectation_matiere.id_affectation_matiere=detail_affectation.id_affectation_matiere 
                    INNER JOIN contrat ON contrat.id_contrat=affectation_matiere.id_contrat
                    INNER JOIN employe ON employe.id_employe=contrat.id_employe
                    INNER JOIN matiere ON matiere.id_matiere=detail_affectation.id_matiere 
                    INNER JOIN categorie_article ON categorie_article.id_categorie_article=matiere.id_categorie_article 
                    INNER JOIN reference ON reference.id_reference=categorie_article.id_reference
                    WHERE reference.id_reference=%s AND DATE_FORMAT(affectation_matiere.date_affectation,'%Y-%m') BETWEEN %s AND %s
                """
                cursor.execute(query, (id_ref, date_du3, date_au3))

            result = cursor.fetchall()
            for count, row in enumerate(result, 1):
                acronym_prenom = make_acronym(row.get("prenom"))
                acronym_nom = make_acronym(row.get("nom"))
                response = {
                    "count": count,
                    "numero": str(row["numero"]).zfill(7),
                    "date_affectation": format_date_fr(str(row["date_affectation"])),
                    "designation": row["designation"],
                    "quantite": row["quantite"],
                    "nature_unite": row["nature_unite"],
                    "prenom": row["prenom"],
                    "nom": row["nom"],
                    "matricule": f"{acronym_prenom}{acronym_nom}-{row.get('matricule')}",
                    "poste_occupe": row["poste_occupe"],
                   "photo": (
                    url_for(
                        "static",
                        filename=f"img/img_employe/{row.get('matricule','')}/{row.get('photo','')}",
                    )
                    if row.get("photo")
                    else url_for("static", filename="img/image/image-profil.png")
                ),
                }
                data.append(response)

        # === TABLEAU 4: dotation ===
        elif "tableau4" in request.form:
            id_ref = encryptor("decrypt", request.form["tableau4"])
            date = request.form.get("date", "")
            date_du4 = request.form.get("date_du4", "")
            date_au4 = request.form.get("date_au4", "")

            if not date_du4 and not date_au4:
                query = """
                    SELECT * FROM dotation 
                    INNER JOIN contrat ON contrat.id_contrat=dotation.id_contrat
                    INNER JOIN employe ON employe.id_employe=contrat.id_employe
                    INNER JOIN reference ON reference.id_reference=employe.id_reference
                    WHERE reference.id_reference=%s AND DATE_FORMAT(dotation.date_dotation,'%Y')=%s
                """
                cursor.execute(query, (id_ref, date))
            else:
                query = """
                    SELECT * FROM dotation 
                    INNER JOIN contrat ON contrat.id_contrat=dotation.id_contrat
                    INNER JOIN employe ON employe.id_employe=contrat.id_employe
                    INNER JOIN reference ON reference.id_reference=employe.id_reference
                    WHERE reference.id_reference=%s AND DATE_FORMAT(dotation.date_dotation,'%Y-%m') BETWEEN %s AND %s
                """
                cursor.execute(query, (id_ref, date_du4, date_au4))

            result = cursor.fetchall()
            for count, row in enumerate(result, 1):
                acronym_prenom = make_acronym(row.get("prenom"))
                acronym_nom = make_acronym(row.get("nom"))
                response = {
                    "count": count,
                    "numero": str(row["numero"]).zfill(7),
                    "date_dotation": format_date_fr(str(row["date_dotation"])),
                    "carburant": f"{row['carburant']:,.0f}".replace(",", " "),
                    "periode_du": format_date_fr(str(row["periode_du"])),
                    "periode_au": format_date_fr(str(row["periode_au"])),
                    "motif": row["motif"],
                    "lieu": row["lieu"],
                    "vehicule": row["vehicule"],
                    "immatriculation": row["immatriculation"],
                    "ca_dotation": row["ca_dotation"],
                    "numero_carte": row["numero_carte"],
                    "prenom": row["prenom"],
                    "nom": row["nom"],
                    "poste_occupe": row["poste_occupe"],
                    "matricule": f"{acronym_prenom}{acronym_nom}-{row.get('matricule')}",
                   "photo": (
                    url_for(
                        "static",
                        filename=f"img/img_employe/{row.get('matricule','')}/{row.get('photo','')}",
                    )
                    if row.get("photo")
                    else url_for("static", filename="img/image/image-profil.png")
                ),
                }
                data.append(response)

        # === TABLEAU 5: reception_carburant ===
        elif "tableau5" in request.form:
            id_ref = encryptor("decrypt", request.form["tableau5"])
            date = request.form.get("date", "")
            date_du5 = request.form.get("date_du5", "")
            date_au5 = request.form.get("date_au5", "")

            if not date_du5 and not date_au5:
                query = """
                    SELECT * FROM reception_carburant
                    INNER JOIN fournisseur ON fournisseur.id_fournisseur=reception_carburant.id_fournisseur
                    INNER JOIN reference ON reference.id_reference=fournisseur.id_reference 
                    WHERE reference.id_reference=%s AND DATE_FORMAT(reception_carburant.date_reception,'%Y')=%s
                """
                cursor.execute(query, (id_ref, date))
            else:
                query = """
                    SELECT * FROM reception_carburant
                    INNER JOIN fournisseur ON fournisseur.id_fournisseur=reception_carburant.id_fournisseur
                    INNER JOIN reference ON reference.id_reference=fournisseur.id_reference 
                    WHERE reference.id_reference=%s AND DATE_FORMAT(reception_carburant.date_reception,'%Y-%m') BETWEEN %s AND %s
                """
                cursor.execute(query, (id_ref, date_du5, date_au5))

            result = cursor.fetchall()
            for count, row in enumerate(result, 1):
                response = {
                    "count": count,
                    "date_reception": format_date_fr(str(row["date_reception"])),
                    "carburant_gasoil": f"{row['carburant_gasoil']} Litres Gasoil",
                    "carburant_super": f"{row['carburant_super']} Litres Super",
                    "carburant": row["carburant_gasoil"] + row["carburant_super"],
                    "numero": str(row["numero"]).zfill(7),
                    "numero_facture": row["numero_facture"],
                    "numero_bon": row["numero_bon"],
                    "fournisseur": row["fournisseur"],
                    "telephone_f": row["telephone_f"],
                    "photo": url_for(
                        "static",
                        filename=(
                            f"img/fournisseur/{row['photo']}"
                            if row["photo"]
                            else "img/image/image.jpg"
                        ),
                    ),
                }
                data.append(response)
        # === TABLEAU 6: Iventaire ===
        elif "tableau6" in request.form:
            id_ref = encryptor("decrypt", request.form["tableau6"])
            date = request.form.get("date", "")
            date_du6 = request.form.get("date_du6", "")
            date_au6 = request.form.get("date_au6", "")

            # --- 1) Récupération du stock interne (entrée / sortie interne) ---
            if not date_du6 and not date_au6:
                # Filtrer par année
                query = """
                    SELECT
                        m.id_matiere,
                        m.image,
                        m.designation,
                        m.nature_unite,
                        de_last.prix_unitaire,
                        COALESCE(de_sum.quantite_entree,0) AS quantite_entree,
                        COALESCE(ds_sum.quantite_sortie,0) AS quantite_sortie
                    FROM matiere m
                    INNER JOIN categorie_article ca ON ca.id_categorie_article = m.id_categorie_article
                    INNER JOIN reference r ON r.id_reference = ca.id_reference
                    LEFT JOIN (
                        SELECT id_matiere, SUM(quantite) AS quantite_entree
                        FROM detail_entree de
                        INNER JOIN entree e ON e.id_entree = de.id_entree
                        WHERE DATE_FORMAT(e.date_entree,'%Y') = %s
                        GROUP BY id_matiere
                    ) de_sum ON de_sum.id_matiere = m.id_matiere
                    LEFT JOIN (
                        SELECT id_matiere, SUM(quantite) AS quantite_sortie
                        FROM detail_sortie ds
                        INNER JOIN sortie s ON s.id_sortie = ds.id_sortie
                        WHERE DATE_FORMAT(s.date_sortie,'%Y') = %s
                        GROUP BY id_matiere
                    ) ds_sum ON ds_sum.id_matiere = m.id_matiere
                    LEFT JOIN (
                        SELECT de1.id_matiere, de1.prix_unitaire
                        FROM detail_entree de1
                        INNER JOIN entree e1 ON e1.id_entree = de1.id_entree
                        WHERE DATE_FORMAT(e1.date_entree,'%Y') = %s
                          AND (e1.date_entree, de1.id_detail_entree) IN (
                              SELECT MAX(e2.date_entree), MAX(de2.id_detail_entree)
                              FROM detail_entree de2
                              INNER JOIN entree e2 ON e2.id_entree = de2.id_entree
                              WHERE DATE_FORMAT(e2.date_entree,'%Y') = %s
                              GROUP BY de2.id_matiere
                          )
                    ) de_last ON de_last.id_matiere = m.id_matiere
                    WHERE r.id_reference = %s
                    ORDER BY m.designation
                """
                cursor.execute(query, (date, date, date, date, id_ref))
            else:
                # Filtrer par période
                query = """
                    SELECT
                        m.id_matiere,
                        m.image,
                        m.designation,
                        m.nature_unite,
                        de_last.prix_unitaire,
                        COALESCE(de_sum.quantite_entree,0) AS quantite_entree,
                        COALESCE(ds_sum.quantite_sortie,0) AS quantite_sortie
                    FROM matiere m
                    INNER JOIN categorie_article ca ON ca.id_categorie_article = m.id_categorie_article
                    INNER JOIN reference r ON r.id_reference = ca.id_reference
                    LEFT JOIN (
                        SELECT id_matiere, SUM(quantite) AS quantite_entree
                        FROM detail_entree de
                        INNER JOIN entree e ON e.id_entree = de.id_entree
                        WHERE DATE_FORMAT(e.date_entree,'%Y-%m') BETWEEN %s AND %s
                        GROUP BY id_matiere
                    ) de_sum ON de_sum.id_matiere = m.id_matiere
                    LEFT JOIN (
                        SELECT id_matiere, SUM(quantite) AS quantite_sortie
                        FROM detail_sortie ds
                        INNER JOIN sortie s ON s.id_sortie = ds.id_sortie
                        WHERE DATE_FORMAT(s.date_sortie,'%Y-%m') BETWEEN %s AND %s
                        GROUP BY id_matiere
                    ) ds_sum ON ds_sum.id_matiere = m.id_matiere
                    LEFT JOIN (
                        SELECT de1.id_matiere, de1.prix_unitaire
                        FROM detail_entree de1
                        INNER JOIN entree e1 ON e1.id_entree = de1.id_entree
                        WHERE DATE_FORMAT(e1.date_entree,'%Y-%m') BETWEEN %s AND %s
                          AND (e1.date_entree, de1.id_detail_entree) IN (
                              SELECT MAX(e2.date_entree), MAX(de2.id_detail_entree)
                              FROM detail_entree de2
                              INNER JOIN entree e2 ON e2.id_entree = de2.id_entree
                              WHERE DATE_FORMAT(e2.date_entree,'%Y-%m') BETWEEN %s AND %s
                              GROUP BY de2.id_matiere
                          )
                    ) de_last ON de_last.id_matiere = m.id_matiere
                    WHERE r.id_reference = %s
                    ORDER BY m.designation
                """
                cursor.execute(query, (
                    date_du6, date_au6, date_du6, date_au6,
                    date_du6, date_au6, date_du6, date_au6,
                    id_ref
                ))

            result = cursor.fetchall()

            # --- 2) Récupération des sorties externes ---
            if not date_du6 and not date_au6:
                query_externe = """
                    SELECT dse.id_matiere, SUM(dse.quantite) AS quantite_sortie_externe
                    FROM detail_sortie_externe dse
                    INNER JOIN sortie_externe se ON se.id_sortie_externe = dse.id_sortie_externe
                    WHERE se.id_reference = %s
                      AND DATE_FORMAT(se.date_sortie,'%Y') = %s
                    GROUP BY dse.id_matiere
                """
                cursor.execute(query_externe, (id_ref, date))
            else:
                query_externe = """
                    SELECT dse.id_matiere, SUM(dse.quantite) AS quantite_sortie_externe
                    FROM detail_sortie_externe dse
                    INNER JOIN sortie_externe se ON se.id_sortie_externe = dse.id_sortie_externe
                    WHERE se.id_reference = %s
                      AND DATE_FORMAT(se.date_sortie,'%Y-%m') BETWEEN %s AND %s
                    GROUP BY dse.id_matiere
                """
                cursor.execute(query_externe, (id_ref, date_du6, date_au6))

            sortie_externe_result = cursor.fetchall()
            sortie_externe_dict = {
                row["id_matiere"]: float(row["quantite_sortie_externe"] or 0)
                for row in sortie_externe_result
            }

            # --- 3) Construire la réponse finale ---
            data = []
            for count, row in enumerate(result, 1):
                quantite_entree = float(row["quantite_entree"] or 0)
                quantite_sortie_interne = float(row["quantite_sortie"] or 0)
                quantite_sortie_externe = sortie_externe_dict.get(row["id_matiere"], 0)

                quantite_sortie_totale = quantite_sortie_interne + quantite_sortie_externe
                stock_restant = quantite_entree - quantite_sortie_totale
                prix_unitaire_num = float(row["prix_unitaire"] or 0)

                response = {
                    "count": count,
                    "designation": row["designation"],
                    "nature_unite": row["nature_unite"],
                    "prix_unitaire": f"{prix_unitaire_num:,.0f}".replace(",", " "),
                    "quantite_entree": quantite_entree,
                    "quantite_sortie_interne": quantite_sortie_interne,
                    "quantite_sortie_externe": quantite_sortie_externe,
                    "quantite_sortie_totale": quantite_sortie_totale,
                    "stock_restant": stock_restant,
                    "montant_total": f"{(stock_restant * prix_unitaire_num):,.0f}".replace(",", " "),
                    "image": url_for(
                        "static",
                        filename=(f"img/matiere/{row['image']}" if row["image"] else "img/image/image.jpg")
                    ),
                }
                data.append(response)

        elif "tableau7" in request.form:
            id_ref = encryptor("decrypt", request.form["tableau7"])
            date = request.form.get("date", "")
            date_du7 = request.form.get("date_du7", "")
            date_au7 = request.form.get("date_au7", "")

            if not date_du7 and not date_au7:
                query = """
                    SELECT * FROM detail_sortie_externe
                    INNER JOIN sortie_externe ON sortie_externe.id_sortie_externe=detail_sortie_externe.id_sortie_externe
                    INNER JOIN matiere ON matiere.id_matiere=detail_sortie_externe.id_matiere
                    INNER JOIN reference ON reference.id_reference=sortie_externe.id_reference
                    WHERE reference.id_reference=%s AND DATE_FORMAT(sortie_externe.date_sortie,'%Y')=%s
                """
                cursor.execute(query, (id_ref, date))
            else:
                query = """
                    SELECT * FROM detail_sortie_externe
                    INNER JOIN sortie_externe ON sortie_externe.id_sortie_externe=detail_sortie_externe.id_sortie_externe
                    INNER JOIN matiere ON matiere.id_matiere=detail_sortie_externe.id_matiere
                    INNER JOIN reference ON reference.id_reference=sortie_externe.id_reference
                    WHERE reference.id_reference=%s AND DATE_FORMAT(sortie_externe.date_sortie,'%Y-%m') BETWEEN %s AND %s
                """
                cursor.execute(query, (id_ref, date_du7, date_au7))

            result = cursor.fetchall()
            for count, row in enumerate(result, 1):
                response = {
                    "count": count,
                    "numero": str(row["numero"]).zfill(7),
                    "date_sortie": format_date_fr(str(row["date_sortie"])),
                    "designation": row["designation"],
                    "quantite": row["quantite"],
                    "nature_unite": row["nature_unite"],
                    "nom_complet_externe": row["nom_complet_externe"],
                    "telephone_externe": row["telephone_externe"],
                    "image": url_for(
                        "static",
                        filename=(
                            f"img/matiere/{row['image']}"
                            if row["image"]
                            else "img/image/image.jpg"
                        ),
                    ),
                }
                data.append(response)

    except Exception as e:
        return jsonify({"error": str(e)})
    finally:
        cursor.close()
        conn.close()

    return jsonify(data)
