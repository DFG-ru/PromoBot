@echo off
@chcp 65001

::
:: README
:: Для запуска сервиса требуется программа NSSM - the Non-Sucking Service Manager.
:: Оф. сайт: https://www.nssm.cc/
:: После установки следует добавить программу в переменную среды PATH
:: 


:: Узнаем SERVICE_NAME будущей службы из service-config.cfg
:: Если файла service-config.txt нет, то создайте его и добавьте строку SERVICE_NAME=<имя сервиса>
for /f "tokens=1* delims==" %%a in ('findstr /b "SERVICE_NAME=" %~dp0\service-config.cfg') do (
    set "SERVICE_NAME=%%b"
)

:start
cls
echo .............
echo Меню
echo .............
echo.
echo Выберите действие для сервиса:
echo.   
echo 1: Статус
echo 2: Установить
echo 3: Запустить
echo 4: Перезапустить
echo 5: Остановить
echo 6: Удалить
echo 0: Выйти
echo.
choice /c:1234560
set m=%errorlevel%
echo.

if errorlevel 1 goto lable%m%
if errorlevel 2 goto lable%m%
if errorlevel 3 goto lable%m%
if errorlevel 4 goto lable%m%
if errorlevel 5 goto lable%m%
if errorlevel 6 goto lable%m%
if errorlevel 0 goto EXIT

echo Ничего не выбрано
pause
goto start


:: Статус сервиса
:lable1

nssm status %SERVICE_NAME%

goto back


:: Установка сервиса
:lable2
echo Запуск установки сервиса...
echo.

:: Записываем директорию от куда запускается скрипт сервиса
set SCRIPT_DIR=%~dp0

:: Создаем службу
nssm install %SERVICE_NAME% "%SCRIPT_DIR%\venv\Scripts\python.exe" "%SCRIPT_DIR%\bot\main.py" %SCRIPT_DIR%

:: Устанавливаем директорию от куда запускает скрипт .py
nssm set %SERVICE_NAME% AppDirectory %SCRIPT_DIR%\bot

:: Устанавливаем куда будет сохраняться лог
nssm set %SERVICE_NAME% AppStdout "%SCRIPT_DIR%\service_log.log"
nssm set %SERVICE_NAME% AppStderr "%SCRIPT_DIR%\service_log.log"

:: Запускаем службу
nssm start %SERVICE_NAME%

echo.
echo Сервис установлен и запущен.
goto back


:: Запуск сервиса
:lable3
echo Запуск сервиса...
echo.

nssm start %SERVICE_NAME%

goto back


:: Перезапуск сервиса
:lable4
echo Перезапуск сервиса...
echo.

nssm restart %SERVICE_NAME%

goto back


:: Остановка сервиса
:lable5
echo Остановка сервиса...
echo.

nssm stop %SERVICE_NAME%

goto back


:: Удаление сервиса
:lable6
echo Удаление сервиса...
echo.

nssm stop %SERVICE_NAME%
nssm remove %SERVICE_NAME% confirm

goto back


:: Вернуться на start
:back
echo.
pause
goto start



:: Выход из скрипта
:EXIT
pause
exit