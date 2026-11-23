from flask import Flask, request, jsonify
import face_recognition
import numpy as np
import base64
import io
from PIL import Image
import os

app = Flask(__name__)
KNOWN_FACES_DIR = "C:/xampp/htdocs/python-facial/faces"

known_encodings = []
known_names = []

# Charger visages connus
def load_faces():
    global known_encodings, known_names
    for name in os.listdir(KNOWN_FACES_DIR):
        person_dir = os.path.join(KNOWN_FACES_DIR, name)
        if not os.path.isdir(person_dir):
            continue
        for filename in os.listdir(person_dir):
            img_path = os.path.join(person_dir, filename)
            image = face_recognition.load_image_file(img_path)
            encoding = face_recognition.face_encodings(image)
            if encoding:
                known_encodings.append(encoding[0])
                known_names.append(name)

load_faces()

@app.route('/recognize', methods=['POST'])
def recognize():
    data = request.get_json()
    if 'image' not in data:
        return jsonify({'error': 'Image manquante'}), 400

    img_data = base64.b64decode(data['image'])
    image = Image.open(io.BytesIO(img_data))
    rgb_image = np.array(image.convert('RGB'))

    encodings = face_recognition.face_encodings(rgb_image)

    if not encodings:
        return jsonify({'name': 'Inconnu'})

    matches = face_recognition.compare_faces(known_encodings, encodings[0])
    if True in matches:
        first_match_index = matches.index(True)
        name = known_names[first_match_index]
        return jsonify({'name': name})
    else:
        return jsonify({'name': 'Inconnu'})

if __name__ == '__main__':
    app.run(debug=True)
