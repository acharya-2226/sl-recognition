# SignLearn

This project contains the Django learning frontend for Number, ASL, and NSL sign recognition. The browser requests camera permission and sends small JPEG frames to the matching local recognition service.

## Frontend setup

From this directory, create or activate a Python environment and install the frontend dependencies:

```powershell
python -m venv env
.\env\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py seed_data
python manage.py runserver 127.0.0.1:8000
```

If an environment is already active, skip the activation command. Open `http://127.0.0.1:8000/` after the server starts.

## Recognition services

Start the services from the backend directory in separate terminals. Install their pinned dependencies once:

```powershell
python -m pip install -r requirements.txt
```

Run the services as follows:

| Track | Command | Health endpoint |
|---|---|---|
| ASL | `python app_webcam_asl.py` | `http://127.0.0.1:5001/health` |
| NSL | `python app_webcam.py` | `http://127.0.0.1:5002/health` |
| Number | `python app_webcam_number.py` | `http://127.0.0.1:5003/health` |

The frontend uses the Django track codes `ASL`, `NSL`, and `NUM`. The Number backend therefore reports `NUM` even though the UI displays “Number”.

The model and mapping files must be beside the backend scripts:

```text
asl_cnn_model.h5
asl_label_mapping_new.txt
nsl_cnn_model_new.h5
nsl_label_mapping_new.txt
```

The ASL and NSL services also accept `ASL_MODEL_PATH`, `ASL_MAPPING_PATH`, `NSL_MODEL_PATH`, and `NSL_MAPPING_PATH` environment variables when the files are stored elsewhere.

## Verification flow

Learning shows the reference image beside the live camera. A sign is marked learned only after the matching backend response reaches the configured confidence threshold. Testing is unlocked for every category, randomizes the active items once per cycle, and requires every prompt to pass exactly once.
