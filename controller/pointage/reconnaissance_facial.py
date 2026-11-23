import os
import io
import time
import base64
import threading
from datetime import datetime

import cv2
import numpy as np
from PIL import Image
import face_recognition
from flask import request, jsonify

from templates.include.connect import get_connection


# =========================
# CONFIG
# =========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "..", "static", "img", "img_employe"))

RELOAD_INTERVAL = 30       # sécurité VPS
POINTAGE_INTERVAL = 60     # anti spam


# =========================
# ENGINE GLOBAL SAFE
# =========================
class FaceEngine:
    def __init__(self):
        self.known_faces = {}      # matricule -> encodings
        self.cache_info = {}       # mtime cache
        self.last_pointage = {}    # anti spam
        self.lock = threading.Lock()
        self.last_reload = 0


engine = FaceEngine()


# =========================
# LOAD FACES OPTIMISÉ
# =========================
def load_faces(force=False):
    with engine.lock:
        now = time.time()
        if not force and (now - engine.last_reload) < RELOAD_INTERVAL:
            return

        for matricule_dir in os.listdir(IMG_DIR):
            path_dir = os.path.join(IMG_DIR, matricule_dir)

            if not os.path.isdir(path_dir):
                continue

            images = [
                f for f in os.listdir(path_dir)
                if f.lower().endswith((".jpg", ".jpeg", ".png"))
            ]

            if not images:
                continue

            try:
                mtime = max([
                    os.path.getmtime(os.path.join(path_dir, f))
                    for f in images
                ])
            except:
                mtime = 0

            cached = engine.cache_info.get(matricule_dir)

            if cached and cached["mtime"] == mtime:
                engine.known_faces[matricule_dir] = cached["encodings"]
                continue

            encodings = []

            for img_name in images:
                img_path = os.path.join(path_dir, img_name)

                try:
                    img = face_recognition.load_image_file(img_path)

                    # resize sécurité CPU
                    if max(img.shape) > 1024:
                        scale = 1024 / max(img.shape)
                        img = cv2.resize(img, (0, 0), fx=scale, fy=scale)

                    encs = face_recognition.face_encodings(img)

                    if encs:
                        encodings.append(encs[0])

                except:
                    continue

            if encodings:
                engine.known_faces[matricule_dir] = encodings
                engine.cache_info[matricule_dir] = {
                    "mtime": mtime,
                    "encodings": encodings
                }

        engine.last_reload = now


# =========================
# MATCH FACE
# =========================
def match_face(query_encoding, tolerance=0.55):
    best = None
    best_dist = tolerance

    for matricule, enc_list in engine.known_faces.items():
        if not enc_list:
            continue

        distances = face_recognition.face_distance(enc_list, query_encoding)

        if len(distances) == 0:
            continue

        min_dist = np.min(distances)

        if min_dist < best_dist:
            best_dist = min_dist
            best = matricule

    return best


# =========================
# POINTAGE SAFE DB
# =========================
def handle_pointage(matricule, cursor):
    now = datetime.now()
    date_now = now.strftime("%Y-%m-%d")
    time_now = now.strftime("%H:%M:%S")

    with engine.lock:
        last = engine.last_pointage.get(matricule)

        if last and (now - last).total_seconds() < POINTAGE_INTERVAL:
            return {
                "matricule": matricule,
                "action": None,
                "message": "Attendez avant de repointer"
            }

        cursor.execute(
            "SELECT id_employe, nom, prenom FROM employe WHERE matricule=%s",
            (matricule,)
        )
        emp = cursor.fetchone()
        if not emp:
            return None

        nom = f"{emp.get('prenom','')} {emp.get('nom','')}".strip()
        id_emp = emp["id_employe"]

        cursor.execute(
            "SELECT id_contrat FROM contrat WHERE id_employe=%s",
            (id_emp,)
        )
        contrat = cursor.fetchone()
        if not contrat:
            return None

        id_contrat = contrat["id_contrat"]

        cursor.execute(
            "SELECT date_heure FROM pointage WHERE date=%s AND id_contrat=%s ORDER BY date_heure DESC LIMIT 1",
            (date_now, id_contrat)
        )
        last_row = cursor.fetchone()

        if last_row:
            cursor.execute(
                "UPDATE pointage SET heure_fin=%s, date_heure=NOW() WHERE date=%s AND id_contrat=%s",
                (time_now, date_now, id_contrat)
            )
            action = "out"
        else:
            cursor.execute(
                "INSERT INTO pointage (date, heure_debut, heure_fin, id_contrat, date_heure) VALUES (%s,%s,%s,%s,NOW())",
                (date_now, time_now, "00:00:00", id_contrat)
            )
            action = "in"

        engine.last_pointage[matricule] = now

        return {
            "matricule": matricule,
            "nom_complet": nom,
            "action": action,
            "message": "OK",
        }


# =========================
# ENDPOINT FLASK
# =========================
def reconnaissance_et_pointage_hybride():

    load_faces()  # reload contrôlé (safe VPS)

    data = request.get_json(silent=True) or {}
    img_data = data.get("image")

    if not img_data:
        return jsonify({"error": "image manquante"}), 400

    try:
        _, encoded = img_data.split(",", 1) if "," in img_data else ("", img_data)
        img_bytes = base64.b64decode(encoded)
        img = np.array(Image.open(io.BytesIO(img_bytes)).convert("RGB"))

    except:
        return jsonify({"error": "image invalide"}), 400

    faces = face_recognition.face_encodings(img)

    if not faces:
        return jsonify({"error": "aucun visage détecté"}), 400

    results = []

    with get_connection() as conn:
        with conn.cursor(dictionary=True) as cursor:

            for f in faces:
                matricule = match_face(f)

                if matricule:
                    res = handle_pointage(matricule, cursor)
                    if res:
                        results.append(res)

        conn.commit()

    return jsonify({
        "status": "success",
        "results": results
    }), 200


# =========================
# FLASK ALIAS
# =========================
reconnaissance_facial = reconnaissance_et_pointage_hybride
