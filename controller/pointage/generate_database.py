import os
import cv2
import insightface
import numpy as np
import json

FOLDER = "static/img/img_employe"


def generate_database():
    model = insightface.app.FaceAnalysis(name="buffalo_l")
    model.prepare(ctx_id=0, nms=0.4)

    def extract_embedding(image_path):
        img = cv2.imread(image_path)
        if img is None:
            print(f"Impossible de lire l'image {image_path}")
            return None
        faces = model.get(img)
        if not faces:
            print(f"Aucun visage détecté dans {image_path}")
            return None
        return faces[0].embedding

    database = {}
    for matricule in os.listdir(FOLDER):
        matricule_path = os.path.join(FOLDER, matricule)
        if not os.path.isdir(matricule_path):
            continue

        embeddings = []
        for filename in os.listdir(matricule_path):
            if filename.lower().endswith((".jpg", ".jpeg", ".png")):
                img_path = os.path.join(matricule_path, filename)
                emb = extract_embedding(img_path)
                if emb is not None:
                    embeddings.append(emb)

        if embeddings:
            mean_emb = np.mean(embeddings, axis=0).tolist()
            database[matricule] = mean_emb
            print(f"Matricule {matricule} : {len(embeddings)} images traitées")
        else:
            print(f"Aucun visage valide trouvé pour {matricule}")

    with open("database.json", "w") as f:
        json.dump(database, f)

    print("Base de données embeddings créée dans database.json")
