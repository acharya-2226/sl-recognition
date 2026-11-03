import base64
import os
from pathlib import Path

import cv2
import mediapipe as mp
import numpy as np
import tensorflow as tf
from flask import Flask, jsonify, request
from flask_cors import CORS

BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = Path(os.getenv("NSL_MODEL_PATH", BASE_DIR / "nsl_cnn_model_new.h5"))
MAPPING_TXT = Path(os.getenv("NSL_MAPPING_PATH", BASE_DIR / "nsl_label_mapping_new.txt"))
CONFIDENCE_THRESHOLD = float(os.getenv("SIGN_CONFIDENCE_THRESHOLD", "0.70"))
NEPALI_CHARACTERS = ["क", "ख", "ग", "घ", "ङ", "च", "छ", "ज", "झ", "ञ", "ट", "ठ", "ड", "ढ", "ण", "त", "थ", "द", "ध", "न", "प", "फ", "ब", "भ", "म", "य", "र", "ल", "व", "श", "ष", "स", "ह", "क्ष", "त्र", "ज्ञ"]

app = Flask(__name__)
CORS(app)
model = None
folder_to_nepali_map = {}


def load_assets():
    global model, folder_to_nepali_map
    if MODEL_PATH.exists():
        model = tf.keras.models.load_model(MODEL_PATH)
    if MAPPING_TXT.exists():
        for line in MAPPING_TXT.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or ":" not in line:
                continue
            idx, folder_name = line.split(":", 1)
            try:
                folder_idx = int(folder_name)
                folder_to_nepali_map[int(idx)] = NEPALI_CHARACTERS[folder_idx] if 0 <= folder_idx < len(NEPALI_CHARACTERS) else folder_name
            except ValueError:
                folder_to_nepali_map[int(idx)] = folder_name


hands = mp.solutions.hands.Hands(static_image_mode=True, max_num_hands=1,
                                 min_detection_confidence=0.5, min_tracking_confidence=0.5)


def decode_frame(data_url):
    encoded = data_url.split(",", 1)[-1]
    raw = base64.b64decode(encoded)
    frame = cv2.imdecode(np.frombuffer(raw, np.uint8), cv2.IMREAD_COLOR)
    return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB) if frame is not None else None


def predict_frame(frame):
    if frame is None:
        return {"label": None, "confidence": 0, "hand_detected": False}
    result = hands.process(frame)
    if not result.multi_hand_landmarks:
        return {"label": None, "confidence": 0, "hand_detected": False, "available": model is not None}
    landmarks = np.array([[v.x, v.y, v.z] for v in result.multi_hand_landmarks[0].landmark], dtype=np.float32)
    landmarks -= landmarks[0].copy()
    if model is None:
        return {"label": None, "confidence": 0, "hand_detected": True, "available": False}
    prediction = model.predict(landmarks.flatten().reshape(1, 63, 1), verbose=0)
    class_id = int(np.argmax(prediction))
    confidence = float(np.max(prediction))
    return {"label": folder_to_nepali_map.get(class_id, str(class_id)),
            "confidence": confidence, "hand_detected": True,
            "available": True, "accepted": confidence >= CONFIDENCE_THRESHOLD}


@app.get("/health")
def health():
    return jsonify({"ok": True, "track": "NSL", "model_available": model is not None})


@app.post("/predict")
def predict():
    payload = request.get_json(silent=True) or {}
    if not payload.get("image"):
        return jsonify({"error": "image is required"}), 400
    try:
        return jsonify(predict_frame(decode_frame(payload["image"])))
    except Exception as exc:
        return jsonify({"error": str(exc)}), 422


load_assets()

if __name__ == "__main__":
    app.run(host=os.getenv("HOST", "127.0.0.1"), port=int(os.getenv("PORT", "5002")), debug=False)
