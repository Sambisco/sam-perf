from flask import request, Response
from io import BytesIO
from PyPDF2 import PdfReader, PdfWriter
from pdf import bulletin2, fiche_paie_employe


def handle(encrypted_id):
    # Liste des handlers à fusionner
    handlers = [bulletin2.handle, fiche_paie_employe.handle]

    pdf_streams = []

    for h in handlers:
        # Appelle le handler et récupère la Response PDF
        response = h(encrypted_id)  # suppose que h() retourne Response avec PDF
        pdf_bytes = BytesIO(response.get_data())  # Récupère le contenu PDF
        pdf_streams.append(pdf_bytes)

    # Fusion des PDF
    merger = PdfWriter()
    for pdf_file in pdf_streams:
        reader = PdfReader(pdf_file)
        for page in reader.pages:
            merger.add_page(page)

    output_stream = BytesIO()
    merger.write(output_stream)
    merger.close()
    output_stream.seek(0)

    return Response(
        output_stream.read(),
        mimetype="application/pdf",
        headers={"Content-Disposition": "inline; filename=bulletin_fiche_paie.pdf"},
    )
