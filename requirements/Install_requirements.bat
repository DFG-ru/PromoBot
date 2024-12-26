@echo off

:: Активируем виртуальное окружение
call ..\venv\Scripts\activate.bat

:: Устанавливаем зависимости из requirements.txt
echo Installing dependencies from requirements.txt...
echo.
pip install -r requirements.txt

:: Деактивируем виртуальное окружение после завершения установки
call deactivate

echo.
echo Done!

:: Устанавливаем шрифт для генератора купонов
:: echo Installing Shentox-Regular (RUS by Slavchansky)_0.ttf...
:: copy "Shentox-Regular (RUS by Slavchansky)_0.ttf" "%WINDIR%\Fonts"
:: reg add "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts" /v "Shentox-Regular (TrueType)" /t REG_SZ /d Shentox-Regular (RUS by Slavchansky)_0.ttf /f

:: echo Done!

pause