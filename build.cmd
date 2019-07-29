REM Install all required packages
pipenv install

REM Compile Qt5 user interfaces to Python code
pipenv run pyuic5 design.ui -o design.py

REM Compile PyQt5 resources
pipenv run pyrcc5 resources/resources.qrc -o resources_rc.py

REM Compile with pyinstaller to /tmp
pipenv run pyinstaller --name="Adventshark" --windowed --clean --noupx --icon adventshark.ico --onefile adventshark.py --distpath c:\temp --workpath c:\temp\build