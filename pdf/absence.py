# controller/pdf/curriculum.py

from flask import Response, abort
from templates.include.connect import get_connection
from templates.include.encryptor import encryptor


def handle(encrypted_id):
    try:
        id_employe = encryptor("decrypt", encrypted_id)
    except Exception:
        return "Code invalide", 400

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM absence WHERE id_absence = %s", (id_employe,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()

    if not result:
        abort(404, description="Employé non trouvé")

    if not result["fichier"]:
        return Response(
            """
            <html><head><meta charset="UTF-8"><title>Absence</title></head>
            <body style="background:#000;">
            <div style="background:#fff;margin:200px auto;border:solid 1px #000;width:700px;height:400px;display:flex;align-items:center;justify-content:center;font-size:50px;">
                Pas de document justificatif
            </div>
            </body></html>
            """,
            mimetype="text/html",
        )

    return Response(result["fichier"], mimetype=result["type"])
