@echo off

set "ROOT=%~dp0"

start "Backend Webcam" powershell -NoExit -Command "cd '%ROOT%Backend'; .\env\Scripts\activate; python app_webcam.py"

start "Backend ASL" powershell -NoExit -Command "cd '%ROOT%Backend'; .\env\Scripts\activate; python app_webcam_asl.py"

start "Backend Number" powershell -NoExit -Command "cd '%ROOT%Backend'; .\env\Scripts\activate; python app_webcam_number.py"

start "Django Frontend" powershell -NoExit -Command "cd '%ROOT%Frontend'; .\env\Scripts\activate; python manage.py runserver"

exit