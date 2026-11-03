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
MODEL_PATH = Path(os.getenv("ASL_MODEL_PATH", BASE_DIR / "asl_cnn_model.h5"))
MAPPING_TXT = Path(os.getenv("ASL_MAPPING_PATH", BASE_DIR / "asl_label_mapping_new.txt"))
CONFIDENCE_THRESHOLD = float(os.getenv("SIGN_CONFIDENCE_THRESHOLD", "0.70"))

app = Flask(__name__)
CORS(app)
model = None
class_id_to_letter = {}


def load_assets():
    global model, class_id_to_letter
    if MODEL_PATH.exists():
        model = tf.keras.models.load_model(MODEL_PATH)
    if MAPPING_TXT.exists():
        for line in MAPPING_TXT.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and ":" in line:
                class_id, label = line.split(":", 1)
                class_id_to_letter[int(class_id)] = label.strip()


mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles
hands = mp_hands.Hands(static_image_mode=True, max_num_hands=1,
                       min_detection_confidence=0.5, min_tracking_confidence=0.5)


def decode_frame(data_url):
    encoded = data_url.split(",", 1)[-1]
    raw = base64.b64decode(encoded)
    frame = cv2.imdecode(np.frombuffer(raw, np.uint8), cv2.IMREAD_COLOR)
    return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB) if frame is not None else None


def encode_frame(frame_rgb):
    frame_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)
    success, buffer = cv2.imencode(".jpg", frame_bgr)
    if not success:
        return None
    return "data:image/jpeg;base64," + base64.b64encode(buffer).decode("utf-8")


def predict_frame(frame):
    if frame is None:
        return {"label": None, "confidence": 0, "hand_detected": False}

    result = hands.process(frame)
    annotated = frame.copy()

    if not result.multi_hand_landmarks:
        return {"label": None, "confidence": 0, "hand_detected": False,
                "available": model is not None, "annotated_image": encode_frame(annotated)}

    for hand_landmarks in result.multi_hand_landmarks:
        mp_drawing.draw_landmarks(
            annotated, hand_landmarks, mp_hands.HAND_CONNECTIONS,
            mp_drawing_styles.get_default_hand_landmarks_style(),
            mp_drawing_styles.get_default_hand_connections_style())

    landmarks = np.array([[v.x, v.y, v.z] for v in result.multi_hand_landmarks[0].landmark], dtype=np.float32)
    landmarks -= landmarks[0].copy()
    annotated_b64 = encode_frame(annotated)

    if model is None:
        return {"label": None, "confidence": 0, "hand_detected": True,
                "available": False, "annotated_image": annotated_b64}

    prediction = model.predict(landmarks.flatten().reshape(1, 63, 1), verbose=0)
    class_id = int(np.argmax(prediction))
    confidence = float(np.max(prediction))
    return {"label": class_id_to_letter.get(class_id, str(class_id)),
            "confidence": confidence, "hand_detected": True,
            "available": True, "accepted": confidence >= CONFIDENCE_THRESHOLD,
            "annotated_image": annotated_b64}


@app.get("/health")
def health():
    return jsonify({"ok": True, "track": "ASL", "model_available": model is not None})


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
    app.run(host=os.getenv("HOST", "127.0.0.1"), port=int(os.getenv("PORT", "5001")), debug=False)