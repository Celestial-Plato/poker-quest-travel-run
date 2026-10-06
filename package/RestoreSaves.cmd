@echo off
setlocal
set "TR_BACKUP=%~1"
if not defined TR_BACKUP set /p "TR_BACKUP=Paste the backup folder path: "
if not defined TR_BACKUP exit /b 1
"%~dp0InstallTravelRun.exe" --restore-saves "%TR_BACKUP%" --no-pause
pause
