@echo off
echo ===================================================
echo [1/2] Backend (Python) gereksinimleri yukleniyor...
echo ===================================================

if not exist ".venv" (
    echo Sanal ortam (.venv) bulunamadi, olusturuluyor...
    python -m venv .venv
)

call .venv\Scripts\activate
pip install -r backend\requirements.txt

echo.
echo ===================================================
echo [2/2] Frontend (React) gereksinimleri yukleniyor...
echo ===================================================

cd frontend
call npm install
cd ..

echo.
echo ===================================================
echo KURULUM TAMAMLANDI!
echo Artik "start_project.bat" ile projeyi baslatabilirsiniz.
echo ===================================================
pause
