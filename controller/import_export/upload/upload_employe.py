from flask import Flask, request
import os

app = Flask(__name__)

# Dossier de destination pour les fichiers uploadés
UPLOAD_FOLDER = os.path.join("static", "files")
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Assure-toi que le dossier existe au démarrage
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def save_import_files():
    if "file-import" not in request.files:
        return "Aucun fichier trouvé", 400

    file = request.files["file-import"]

    if file.filename == "":
        return "Nom de fichier vide", 400

    # Extraire l'extension
    filename = file.filename
    file_extension = filename.rsplit(".", 1)[-1].lower()

    # Sauvegarder le fichier
    file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(file_path)

    return f"Fichier sauvegardé : {filename}"

