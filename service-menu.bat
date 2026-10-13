@echo off
@chcp 65001 >nul

::
:: README
:: Для запуска сервиса требуется программа NSSM - the Non-Sucking Service Manager.
:: Оф. сайт: https://www.nssm.cc/
:: После установки следует добавить программу в переменную среды PATH
:: 

:: Узнаем SERVICE_NAME будущей службы из service-config.cfg
:: Если файла нет, создайте его и добавьте строку: SERVICE_NAME=ИмяВашегоБота
for /f "tokens=1* delims==" %%a in ('findstr /b "SERVICE_NAME=" "%~dp0\service-config.cfg" 2^>nul') do (
    set "SERVICE_NAME=%%b"
)

if "%SERVICE_NAME%"=="" (
    echo ОШИБКА: Не удалось найти SERVICE_NAME в service-config.cfg
    echo Создайте файл и добавьте строку: SERVICE_NAME=MyBotService
    pause
    exit /b
)

:start
cls
echo .............
echo Меню управления сервисом: %SERVICE_NAME%
echo .............
echo.
echo Выберите действие:
echo 1: Статус
echo 2: Установить
echo 3: Запустить
echo 4: Перезапустить
echo 5: Остановить
echo 6: Удалить
echo 7: Отладка (запуск вручную)
echo 0: Выйти
echo.
choice /c 12345670 /m "Ваш выбор"
echo.

:: Используем точное сравнение %errorlevel%, так как choice возвращает индекс нажатого символа (0 - это 8-й символ)
if %errorlevel%==1 goto label1
if %errorlevel%==2 goto label2
if %errorlevel%==3 goto label3
if %errorlevel%==4 goto label4
if %errorlevel%==5 goto label5
if %errorlevel%==6 goto label6
if %errorlevel%==7 goto label7
if %errorlevel%==8 goto EXIT

echo Ничего не выбрано
pause
goto start

:: Статус сервиса
:label1
echo Статус сервиса:
nssm status %SERVICE_NAME%
goto back

:: Установка сервиса
:label2
echo Запуск установки сервиса...
echo.

set "SCRIPT_DIR=%~dp0"
:: Убираем завершающий слеш — это ключ к корректным кавычкам
if "%SCRIPT_DIR:~-1%"=="\" set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

:: Проверяем существование Python в venv
if not exist "%SCRIPT_DIR%\venv\Scripts\python.exe" (
    echo ОШИБКА: Не найден Python в виртуальном окружении!
    echo Ожидался путь: %SCRIPT_DIR%\venv\Scripts\python.exe
    pause
    goto start
)

:: 1. Создаем службу, СРАЗУ указывая путь к Python
::    Это делает службу "NSSM-службой", и все nssm set будут работать
nssm install %SERVICE_NAME% "%SCRIPT_DIR%\venv\Scripts\python.exe"

:: 2. Аргументы — путь к main.py
nssm set %SERVICE_NAME% AppParameters "%SCRIPT_DIR%\bot\main.py"

:: 3. Рабочая директория
nssm set %SERVICE_NAME% AppDirectory "%SCRIPT_DIR%\bot"

:: 4. Логи
nssm set %SERVICE_NAME% AppStdout "%SCRIPT_DIR%\log\nssm_stdout.log"
nssm set %SERVICE_NAME% AppStderr "%SCRIPT_DIR%\log\nssm_stderr.log"

:: 5. Ротация логов
nssm set %SERVICE_NAME% AppRotateFiles 1
nssm set %SERVICE_NAME% AppRotateBytes 1048576

:: 6. Запускаем
nssm start %SERVICE_NAME%

echo.
echo Сервис установлен и запущен.
goto back

:: Запуск сервиса
:label3
echo Запуск сервиса...
echo.
nssm start %SERVICE_NAME%
goto back

:: Перезапуск сервиса
:label4
echo Перезапуск сервиса...
echo.
nssm restart %SERVICE_NAME%
goto back

:: Остановка сервиса
:label5
echo Остановка сервиса...
echo.
nssm stop %SERVICE_NAME%
goto back

:: Удаление сервиса
:label6
echo Удаление сервиса...
echo.
nssm stop %SERVICE_NAME%
nssm remove %SERVICE_NAME% confirm
echo Сервис удален.
goto back

:: Отладка
:label7
echo Запуск отладки...
echo.

set SCRIPT_DIR=%~dp0

:: Активируем виртуальное окружение (call нужен, чтобы выполнение батника не прервалось)
call "%SCRIPT_DIR%\venv\Scripts\activate.bat"

:: Переходим в папку bot и запускаем бота
cd /d "%SCRIPT_DIR%\bot"
python main.py

goto back

:: Вернуться в меню
:back
echo.
pause
goto start

:: Выход из скрипта
:EXIT
echo Завершение работы...
exit /b