@echo off
title TikTok Tracking - Startup
color 0A

echo ========================================
echo   TikTok Live Tracking - Demarrage
echo ========================================
echo.

echo [1/4] Demarrage de Redis...
start "Redis Server" cmd /k "redis-server"
timeout /t 3 /nobreak >nul

echo [2/4] Demarrage de Django...
start "Django Server" cmd /k "cd /d %~dp0 && .\venv\Scripts\activate && py manage.py runserver"
timeout /t 5 /nobreak >nul

echo [3/4] Demarrage de Celery Worker...
start "Celery Worker" cmd /k "cd /d %~dp0 && .\venv\Scripts\activate && celery -A core worker --loglevel=info --pool=solo"
timeout /t 3 /nobreak >nul

echo [4/4] Demarrage de Celery Beat...
start "Celery Beat" cmd /k "cd /d %~dp0 && .\venv\Scripts\activate && celery -A core beat --loglevel=info"

echo.
echo ========================================
echo   Tous les services sont demarres !
echo ========================================
echo.
echo Services actifs:
echo - Redis: localhost:6379
echo - Django: http://127.0.0.1:8000
echo - Celery Worker: Traitement des taches
echo - Celery Beat: Verification toutes les 2 min
echo.
echo Appuie sur une touche pour fermer cette fenetre...
pause >nul