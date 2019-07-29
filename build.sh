#!/bin/bash -x 

# On MacOS, LC_ALL and LANG need to be declared
if [[ "$OSTYPE" == "darwin"* ]]; then
    export LC_ALL=en_US.UTF-8
    export LANG=en_US.UTF-8
fi

# Install all required packages
pipenv install

# Compile Qt5 user interfaces to Python code
pipenv run pyuic5 design.ui -o design.py

# Compile PyQt5 resources
pipenv run pyrcc5 resources/resources.qrc -o resources_rc.py

# Compile with pyinstaller to /tmp
pipenv run pyinstaller --clean --noupx --onefile adventshark.py --distpath /tmp --workpath /tmp/build
