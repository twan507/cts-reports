@echo off
REM start.bat - Kich hoat moi truong ao va chay main.py
chcp 65001 >nul

echo.
echo ====================================
echo  Bat dau ung dung
echo ====================================
echo.

REM Kich hoat moi truong ao
echo Kich hoat moi truong ao...
if not exist "development\venv\Scripts\activate.bat" (
    echo Loi: Moi truong ao chua duoc thiet lap. Vui long chay setup.bat truoc.
    goto :end
)
call development\venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo Loi: Khong the kich hoat moi truong ao.
    goto :end
)
echo Da kich hoat moi truong ao.

REM Chay main.py
echo Chay main.py...
python development\src\main.py
if %errorlevel% neq 0 (
    echo Loi: Ung dung main.py gap loi.
)

echo.
echo ====================================
echo  Ung dung da ket thuc.
echo ====================================
echo.

:end
REM Tat moi truong ao truoc khi thoat
if defined VIRTUAL_ENV (
    echo Tat moi truong ao...
    conda deactivate >nul 2>&1
    if errorlevel 1 (
        call deactivate >nul 2>&1
    )
)
pause
