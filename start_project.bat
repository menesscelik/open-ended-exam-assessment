@echo off
echo Proje baslatiliyor...

REM 1. Ollama Kontrolu (Port 11434)
echo Ollama servisi kontrol ediliyor (Port 11434)...
netstat -ano | find "11434" | find "LISTENING" >nul
if "%ERRORLEVEL%"=="0" (
    echo [BILGI] Ollama portu (11434) zaten aktif. Servis calisiyor.
) else (
    echo [BILGI] Ollama portu aktif degil. Servis baslatiliyor...
    start "Ollama Server" cmd /k "ollama serve"
    REM Servisin tam başlamasi icin bekle
    timeout /t 5
)

REM Model Kontrolu (deepseek-r1:8b)
echo Model kontrolu yapiliyor...
ollama list | findstr "deepseek-r1:8b" >nul
if errorlevel 1 (
    echo [UYARI] 'deepseek-r1:8b' modeli bulunamadi!
    echo Arka planda indiriliyor (bu islem internet hiziniza gore surebilir)...
    start "Model Indiriliyor" cmd /k "ollama pull deepseek-r1:8b"
) else (
    echo [BILGI] Model hazir: deepseek-r1:8b
)

echo.
echo Backend ve Frontend baslatiliyor...

REM 2. Backend'i yeni pencerede baslat
start "Backend Server" cmd /k "cd backend & call ..\.venv\Scripts\activate & uvicorn main:app --reload"

REM 3. Frontend'i yeni pencerede baslat
start "Frontend Client" cmd /k "cd frontend & npm run dev"

echo.
echo Tum servisler baslatildi!
echo Backend:   http://127.0.0.1:8000
echo Frontend:  http://localhost:5173
echo Ollama:    http://127.0.0.1:11434
echo.
echo [NOT] Puanlama yapabilmek icin 'Ollama Server' penceresinin acik kalmasi gerekir (eger yeni acildiysa).
echo.

REM Hata goruntulemek icin beklet
pause
