@echo off
rem Pilotage permanent (decision du porteur du 13/11/2026) : serveur du tableau de bord et bot Telegram + boucle.
rem A lancer au demarrage de la session Windows (installation par le porteur : scripts\pilotage\installer_demarrage.py).
rem Le bot est relance automatiquement s'il s'arrete (coupure reseau prolongee, erreur).
cd /d "%~dp0"
start "MakyClimat - serveur" /min ".venv\Scripts\python.exe" -B -X utf8 scripts\pilotage\serveur_pilotage.py --sans-navigateur
:boucle
".venv\Scripts\python.exe" -B -X utf8 scripts\pilotage\telegram_bot.py >> pilotage\etat\telegram.log 2>&1
timeout /t 30 /nobreak > nul
goto boucle
