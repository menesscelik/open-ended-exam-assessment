@echo off
echo Backend sunucusu baslatiliyor...
echo Tarayicidan http://127.0.0.1:8000 adresine gidebilirsiniz.
echo Durdurmak icin CTRL+C yapip ardindan E (Evet) diyebilirsiniz veya pencereyi kapatabilirsiniz.
echo.

call .venv\Scripts\activate
cd backend
uvicorn main:app --reload

pause
