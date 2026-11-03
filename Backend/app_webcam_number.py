import base64

import os
from pathlib import Path

import cv2
import mediapipe as mp
import numpy as np
from flask import Flask, jsonify, request
from flask_cors import CORS

BASE_DIR = Path(__file__).resolve().parent

app = Flask(__name__)
CORS(app)

mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles
hands = mp_hands.Hands(static_image_mode=True, max_num_hands=2,
                       min_detection_confidence=0.5, min_tracking_confidence=0.5)

TIP_IDS = [4, 8, 12, 16, 20]


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


def count_fingers(hand_landmarks, handedness_label, W, H):
    landmarks = [(int(lm.x * W), int(lm.y * H)) for lm in hand_landmarks.landmark]

    ys = [y for (_x, y) in landmarks]
    hand_height = max(ys) - min(ys) if ys else 0
    margin = max(10, int(hand_height * 0.08))

    fingers = []

    # Thumb: direction depends on handedness
    tip_x = landmarks[TIP_IDS[0]][0]
    ip_x = landmarks[TIP_IDS[0] - 1][0]
    if handedness_label == 'Right':
        fingers.append(1 if tip_x > ip_x + int(margin * 0.2) else 0)
    else:
        fingers.append(1 if tip_x < ip_x - int(margin * 0.2) else 0)

    # Other fingers: tip above PIP joint
    for i in range(1, 5):
        tip_y = landmarks[TIP_IDS[i]][1]
        pip_y = landmarks[TIP_IDS[i] - 2][1]
        fingers.append(1 if tip_y < pip_y - margin else 0)

    return sum(fingers)


def predict_frame(frame):
    if frame is None:
        return {"count": 0, "hand_detected": False}

    H, W = frame.shape[:2]
    result = hands.process(frame)
    annotated = frame.copy()

    if not result.multi_hand_landmarks:
        return {"count": 0, "hand_detected": False, "annotated_image": encode_frame(annotated)}

    total_fingers = 0
    for idx, hand_landmarks in enumerate(result.multi_hand_landmarks):
        handedness_label = "Right"
        if result.multi_handedness and len(result.multi_handedness) > idx:
            handedness_label = result.multi_handedness[idx].classification[0].label

        total_fingers += count_fingers(hand_landmarks, handedness_label, W, H)

        mp_drawing.draw_landmarks(
            annotated, hand_landmarks, mp_hands.HAND_CONNECTIONS,
            mp_drawing_styles.get_default_hand_landmarks_style(),
            mp_drawing_styles.get_default_hand_connections_style())

    annotated_b64 = encode_frame(annotated)
    return {"count": total_fingers, "hand_detected": True, "annotated_image": annotated_b64}


@app.get("/health")
def health():
    return jsonify({"ok": True, "track": "NUM", "model_available": True})


@app.post("/predict")
def predict():
    payload = request.get_json(silent=True) or {}
    if not payload.get("image"):
        return jsonify({"error": "image is required"}), 400
    try:
        return jsonify(predict_frame(decode_frame(payload["image"])))
    except Exception as exc:
        return jsonify({"error": str(exc)}), 422


if __name__ == "__main__":
    app.run(host=os.getenv("HOST", "127.0.0.1"), port=int(os.getenv("PORT", "5003")), debug=False)