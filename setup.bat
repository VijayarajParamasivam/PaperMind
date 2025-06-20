@echo off
setlocal

REM Set Python install directory inside the repo
set PYDIR=%CD%\python

REM Download Python installer if not present
if not exist "%CD%\python-installer.exe" (
    echo Downloading Python installer...
    powershell -Command "Invoke-WebRequest -Uri https://www.python.org/ftp/python/3.11.5/python-3.11.5-amd64.exe -OutFile python-installer.exe"
)

REM Install Python locally if not already installed
if not exist "%PYDIR%\python.exe" (
    echo Installing Python locally...
    python-installer.exe /quiet InstallAllUsers=0 TargetDir="%PYDIR%" PrependPath=0 Include_test=0
)

REM Create venv using local Python
"%PYDIR%\python.exe" -m venv venv

REM Activate venv and install requirements
call venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt

REM Create run_papermind.bat to launch the app
echo @echo off > run_papermind.bat
echo call venv\Scripts\activate >> run_papermind.bat
echo streamlit run app.py >> run_papermind.bat
echo exit >> run_papermind.bat

REM Create desktop shortcut named PaperMind
set SHORTCUT="%USERPROFILE%\Desktop\PaperMind.lnk"
powershell "$s=(New-Object -COM WScript.Shell).CreateShortcut(%SHORTCUT%);$s.TargetPath='%CD%\run_papermind.bat';$s.WorkingDirectory='%CD%';$s.Save()"

echo Setup complete! Use the PaperMind shortcut on your desktop to launch the app.