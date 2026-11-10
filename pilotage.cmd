@echo off
rem Ouvre le tableau de bord de pilotage avec ses commandes (demarrer ou arreter le surveillant).
rem Laisser cette fenetre ouverte ; la fermer arrete le serveur local.
cd /d "%~dp0"
".venv\Scripts\python.exe" -B -X utf8 scripts\pilotage\serveur_pilotage.py %*
if errorlevel 1 pause
