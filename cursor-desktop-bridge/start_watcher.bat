@echo off
cd /d "%~dp0"
set CURSOR_BRIDGE_DIR=%~dp0
echo Starting Cursor Desktop Bridge watcher...
python bridge\watcher.py
pause
