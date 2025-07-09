@echo off
REM setup.bat - Thiet lap moi truong ao, cai dat thu vien, va dang ky kernel voi Jupyter

echo.
echo ====================================
echo  Bat dau thiet lap moi truong ao
echo ====================================
echo.

REM Kiem tra xem Python da duoc cai dat va co trong PATH chua
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo Loi: Python khong tim thay trong PATH.
    echo Vui long cai dat Python phien ban 3.x va them no vao bien moi truong PATH.
    goto :end
)

REM Tao moi truong ao neu chua ton tai
if not exist "development\venv" (
    echo Tao moi truong ao tai development\venv...
    python -m venv development\venv
    if %errorlevel% neq 0 (
        echo Loi: Khong the tao moi truong ao.
        goto :end
    )
    echo Da tao moi truong ao thanh cong.
) else (
    echo Moi truong ao development\venv da ton tai. Bo qua buoc tao.
)

REM Kich hoat moi truong ao
echo Kich hoat moi truong ao...
call development\venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo Loi: Khong the kich hoat moi truong ao.
    goto :end
)
echo Da kich hoat moi truong ao.

REM Cai dat cac thu vien tu requirements.txt trong thu muc development
echo Cai dat cac thu vien tu development/requirements.txt...
pip install --upgrade pip
pip install -r development\requirements.txt
if %errorlevel% neq 0 (
    echo Loi: Khong the cai dat cac thu vien.
    goto :deactivate_and_end
)
echo Da cai dat tat ca thu vien thanh cong.

REM ========================================================================
REM == BUOC QUAN TRONG NHAT DE SUA LOI "KERNEL DIED" TRONG MOI TRUONG DEV ==
REM ========================================================================
echo.
echo Dang ky moi truong ao nay voi Jupyter...

REM Doc ten APP_NAME va KERNEL_NAME tu config.py
for /f "tokens=*" %%a in ('python -c "import sys; sys.path.append('development\\src'); import config; print(config.APP_NAME)"') do set APP_NAME=%%a
for /f "tokens=*" %%a in ('python -c "import sys; sys.path.append('development\\src'); import config; print(config.JUPYTER_KERNEL_NAME)"') do set KERNEL_NAME=%%a

echo Dang ky kernel duy nhat cho du an voi ten: %KERNEL_NAME%
python -m ipykernel install --user --name=%KERNEL_NAME% --display-name="Python (%APP_NAME%)"
if %errorlevel% neq 0 (
    echo Loi: Khong the dang ky kernel voi Jupyter.
    goto :deactivate_and_end
)
echo Da dang ky kernel '%KERNEL_NAME%' thanh cong.
echo.
REM ========================================================================

echo.
echo ==========================================
echo  Thiet lap hoan tat. San sang de phat trien.
echo ==========================================
echo.
goto :deactivate_and_end

:deactivate_and_end
REM Tat moi truong ao truoc khi thoat
if defined VIRTUAL_ENV (
    echo Tat moi truong ao...
    conda deactivate >nul 2>&1
    if errorlevel 1 (
        call deactivate >nul 2>&1
    )
)
pause
exit /b %errorlevel%

:end
pause
exit /b %errorlevel%
