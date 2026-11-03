# SignLearn recognition services

These Flask services expose one consistent JSON API for browser camera frames. Each service listens on a separate local port so the Django frontend can select the correct recognizer by learning track.

## Install

Use Python 3.11 on Windows for the pinned TensorFlow and MediaPipe combination:

```powershell
python -m pip install -r requirements.txt
```

The requirements intentionally use `mediapipe==0.10.21`, `numpy==1.26.4`, `protobuf==4.25.9`, `opencv-contrib-python==4.11.0.86`, and `tensorflow==2.15.1`. These versions provide the `mp.solutions.hands` API used by the services.

## Model files

Place these files in the same directory as the scripts:

```text
asl_cnn_model.h5
asl_label_mapping_new.txt
nsl_cnn_model_new.h5
nsl_label_mapping_new.txt
```

The services also support environment variables for alternate locations:

```powershell
$env:ASL_MODEL_PATH = "C:\path\to\asl_cnn_model.h5"
$env:ASL_MAPPING_PATH = "C:\path\to\asl_label_mapping_new.txt"
$env:NSL_MODEL_PATH = "C:\path\to\nsl_cnn_model_new.h5"
$env:NSL_MAPPING_PATH = "C:\path\to\nsl_label_mapping_new.txt"
```

## Start

Run each service in its own terminal from this directory:

```powershell
python app_webcam_asl.py       # ASL, port 5001
python app_webcam.py           # NSL, port 5002
python app_webcam_number.py    # Number, port 5003
```

Health checks are available at `/health`. Each service accepts `POST /predict` with `{ "image": "data:image/jpeg;base64,..." }` and returns a JSON result. ASL and NSL return `label`, `confidence`, `hand_detected`, and `available`; Number returns `count` and `hand_detected`.
