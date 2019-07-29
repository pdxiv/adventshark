# adventshark

GUI text adventure editor, compatible with Scott Adams/Adventure International

## Requirements

### For Running

Python 3.7, Pipenv and Qt 5.

### For building with Pyinstaller

Python 3.7, Pipenv, Qt 5 and Pyinstaller.

## How to run

### Preparation

```bash
# Install all required packages
pipenv install

# Compile Qt5 user interfaces to Python code
pipenv run pyuic5 design.ui -o design.py

# Compile PyQt5 resources
pipenv run pyrcc5 resources/resources.qrc -o resources_rc.py
```

### Running

```bash
pipenv run python adventshark.py 
```

## How to build executable with Pyinstaller

Linux/MacOSX `./build.sh`
Windows: `build.cmd`

## How to convert .DAT files to .json

Since adventshark currently doesn't have file import functionality, old data files will first need to be converted to adventshark's `.json` format with an included Perl script: `scott2json.pl`.

### Basic scott2json usage example (Linux/MacOSX)

`./scott2json.pl adv01.dat > adv01.json`

### Usage example with many files at once (Linux/MacOSX)

This example assumes that the `rename` utility is installed. It will convert all the `.dat` files in the directory at once to `.json` format.

`ls -1 *.dat | xargs -i bash -c "./scott2json.pl {} | python -m json.tool > {}.json" ; rename -f 's/.dat.json$/.json/' *.dat.json`

## Files

- `README.md`: This document
- `adventshark_hires.png`: High resolution version of the "adventshark" icon
- `adventshark.ico`: Windows program icon, for pyinstaller
- `adventshark.py`: Main program
- `build.cmd`: Windows build script
- `build.sh`: Build script for Linux and MacOSX
- `design.ui`: Qt Designer UI file for the user interface
- `json2dat.py`: Routines for converting 
- `Pipfile`: Pipenv data file
- `Pipfile.lock`: Pipenv data file
- `resources`: Directory containing tool button icons
- `scott2json.pl`: Perl script for converting TRS-80 `.DAT` files into `.json`
- `.gitignore`: Which files or folders to ignore in the project
