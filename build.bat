@echo off
REM build.bat - Dong goi ung dung theo kieu ONE-FOLDER tu file .spec

echo.
echo =========================================
echo  Bat dau qua trinh dong goi ONE-FOLDER
echo =========================================
echo.

REM Kich hoat moi truong ao
echo Kich hoat moi truong ao...
if not exist "development\venv\Scripts\activate.bat" (
    echo Loi: Moi truong ao chua duoc thiet lap. Vui long chay setup.bat truoc.
    goto :end
)
call development\venv\Scripts\activate.bat
echo Da kich hoat moi truong ao.

REM Doc ten thu muc build tu config de phuc vu viec sao chep
echo Doc cau hinh tu config.py...
for /f "tokens=*" %%a in ('python -c "import sys; sys.path.append('development\\src'); import config; print(config.APP_NAME)"') do set APP_NAME=%%a
for /f "tokens=*" %%a in ('python -c "import sys; sys.path.append('development\\src'); import config; print(config.APP_BUILD_DIR)"') do set APP_BUILD_DIR=%%a
for /f "tokens=*" %%a in ('python -c "import sys; sys.path.append('development\\src'); import config; print(config.EXE_FILE_NAME)"') do set EXE_FILE_NAME=%%a


REM Don dep cac thu muc build va dist cu, va cac file exe + _internal cu trong app
echo Don dep cac thu muc cu...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"

REM Chi xoa file .exe va thu muc _internal cu trong thu muc dich
if exist "%APP_BUILD_DIR%\%EXE_FILE_NAME%" del /f /q "%APP_BUILD_DIR%\%EXE_FILE_NAME%"
if exist "%APP_BUILD_DIR%\_internal" rmdir /s /q "%APP_BUILD_DIR%\_internal"

REM Lenh PyInstaller build tu file .spec
echo Bat dau dong goi voi PyInstaller tu development/build.spec...
pyinstaller development/build.spec --noconfirm --distpath dist --workpath build

if %errorlevel% neq 0 (
    echo Loi: Qua trinh dong goi voi PyInstaller gap van de.
    goto :deactivate_and_end
)
echo PyInstaller da tao thu muc ung dung thanh cong.

REM *** LOGIC MOI: Kiem tra loi truoc khi don dep ***
echo Chuan bi thu muc phan phoi cuoi cung...

REM Tao thu muc app neu chua ton tai
if not exist "%APP_BUILD_DIR%" mkdir "%APP_BUILD_DIR%"

REM Di chuyen file .exe tu 'dist\%APP_NAME%' vao thu muc app
if not exist "dist\%APP_NAME%\%EXE_FILE_NAME%" (
    echo Loi: Khong tim thay file executable 'dist\%APP_NAME%\%EXE_FILE_NAME%'.
    goto :deactivate_and_end
)
move /Y "dist\%APP_NAME%\%EXE_FILE_NAME%" "%APP_BUILD_DIR%\" > nul
if %errorlevel% neq 0 (
    echo Loi: Khong the di chuyen file '%EXE_FILE_NAME%'. Giu lai thu muc 'dist' de kiem tra.
    goto :deactivate_and_end
)
echo Da di chuyen file '%EXE_FILE_NAME%' vao thu muc '%APP_BUILD_DIR%'.


REM Di chuyen thu muc _internal tu 'dist\%APP_NAME%' vao thu muc app
if not exist "dist\%APP_NAME%\_internal" (
    echo Loi: Khong tim thay thu muc '_internal' trong 'dist\%APP_NAME%'.
    goto :deactivate_and_end
)
move /Y "dist\%APP_NAME%\_internal" "%APP_BUILD_DIR%\_internal" > nul
if %errorlevel% neq 0 (
    echo Loi: Khong the di chuyen thu muc '_internal'. Giu lai thu muc 'dist' de kiem tra.
    goto :deactivate_and_end
)
echo Da di chuyen thu muc '_internal' vao '%APP_BUILD_DIR%'.


REM Don dep cac file va thu muc tam CHI KHI THANH CONG
echo Don dep...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"

echo.
echo =========================================
echo  Qua trinh dong goi hoan tat!
echo  File executable va thu muc _internal da duoc cap nhat tai: %APP_BUILD_DIR%
echo  File executable: %APP_BUILD_DIR%\%EXE_FILE_NAME%
echo  Thu muc _internal: %APP_BUILD_DIR%\_internal
echo =========================================
echo.

:deactivate_and_end
REM Tat moi truong ao truoc khi thoat
if defined VIRTUAL_ENV (
    echo Tat moi truong ao...
    call deactivate >nul 2>&1
)
pause
exit /b %errorlevel%

:end
pause
exit /b 1