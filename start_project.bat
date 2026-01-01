@echo off
echo ===================================================
echo Acik Uclu Sinav Degerlendirme Sistemi Baslatiliyor...
echo ===================================================

:: 1. Ollama Kontrolu
echo [1/3] Ollama servisi kontrol ediliyor...
netstat -an | find "11434" >nul
if %errorlevel% neq 0 (
    echo Ollama calismiyor, baslatiliyor...
    start /B ollama serve
    timeout /t 5 >nul
) else (
    echo Ollama zaten calisiyor.
)

:: 2. Model Kontrolu (deepseek-r1:8b)
echo [2/3] Ollama modeli (deepseek-r1:8b) kontrol ediliyor...
ollama list | find "deepseek-r1:8b" >nul
if %errorlevel% neq 0 (
    echo Model bulunamadi, indiriliyor (Bu islem internet hizina gore surebilir)...
    ollama pull deepseek-r1:8b
) else (
    echo Model hazir.
)

:: 3. Backend Baslatma
echo [3/3] Backend ve Frontend baslatiliyor...
if not exist ".venv" (
    echo HATA: .venv klasoru bulunamadi! Lutfen "0_setup_project.bat" scriptini calistirin.
    pause
    exit
)

call .venv\Scripts\activate

:: Backend'i arka planda baslat
start "Backend API" cmd /k "uvicorn backend.main:app --reload --port 8000"

:: 4. Frontend Baslatma
cd frontend
start "Frontend UI" cmd /k "npm run dev"

echo.
echo Islem tamam! Tarayiciniz acilmazsa su adresleri kullanin:
echo Backend: http://127.0.0.1:8000
echo Frontend: http://localhost:5173
echo.
pause
