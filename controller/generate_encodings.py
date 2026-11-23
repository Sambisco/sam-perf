import face_recognition
import os
import pickle

def generate_encodings(image_dir='backend/images', output_file='backend/encodings.pkl'):
    known_face_encodings = []
    known_face_names = []

    if not os.path.exists(image_dir):
        print(f"Dossier {image_dir} non trouvé")
        return

    for filename in os.listdir(image_dir):
        if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
            path = os.path.join(image_dir, filename)
            print(f"Traitement {filename}")
            image = face_recognition.load_image_file(path)
            encodings = face_recognition.face_encodings(image)
            if encodings:
                known_face_encodings.append(encodings[0])
                name = os.path.splitext(filename)[0]
                known_face_names.append(name)
                print(f"Encodage fait pour {name}")
            else:
                print(f"Aucun visage détecté dans {filename}")

    data = {'encodings': known_face_encodings, 'names': known_face_names}
    with open(output_file, 'wb') as f:
        pickle.dump(data, f)
    print(f"Encodages sauvegardés dans {output_file}")

if __name__ == "__main__":
    generate_encodings()
