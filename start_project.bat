@echo off
echo Proje baslatiliyor (Backend + Frontend)...

:: Backend'i yeni pencerede baslat
start "Backend Server" cmd /k "cd backend & call ..\.venv\Scripts\activate & uvicorn main:app --reload"

:: Frontend'i yeni pencerede baslat
start "Frontend Client" cmd /k "cd frontend & npm run dev"

echo.
echo Iki terminal de acildi.
echo Backend: http://127.0.0.1:8000
echo Frontend: http://localhost:5173 (Vite varsayilan portu)
echo.
