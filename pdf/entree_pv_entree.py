from flask import Response
from io import BytesIO
from PyPDF2 import PdfReader, PdfWriter
from pdf import entree, pv_entree  # tes modules PDF existants


def handle(encrypted_id):
    """
    Fusionne le PDF d'entree avec celui de pv_entree si ce dernier existe et n'est pas vide.
    Retourne un PDF unique en Response.
    """
    pdf_streams = []

    # 1️⃣ PDF principal : entrée
    pdf_entree_resp = entree.handle(encrypted_id)
    if pdf_entree_resp is None:
        # impossible normalement, entrée doit exister
        return Response("Aucune donnée d'entrée trouvée", status=404)

    pdf_streams.append(BytesIO(pdf_entree_resp.get_data()))

    # 2️⃣ PDF optionnel : pv_entree
    pdf_pv_resp = pv_entree.handle(encrypted_id)
    if pdf_pv_resp is not None:
        temp_io = BytesIO(pdf_pv_resp.get_data())
        reader = PdfReader(temp_io)
        if len(reader.pages) > 0:  # seulement si le PDF contient au moins 1 page
            pdf_streams.append(temp_io)

    # 3️⃣ Fusion des PDFs
    merger = PdfWriter()
    for pdf_file in pdf_streams:
        reader = PdfReader(pdf_file)
        for page in reader.pages:
            merger.add_page(page)

    # 4️⃣ Sortie
    output_stream = BytesIO()
    merger.write(output_stream)
    merger.close()
    output_stream.seek(0)

    return Response(
        output_stream.read(),
        mimetype="application/pdf",
        headers={"Content-Disposition": "inline; filename=entree_pv_entree.pdf"},
    )
