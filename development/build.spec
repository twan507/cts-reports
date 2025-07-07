# -*- mode: python ; coding: utf-8 -*-

# =============================================================================
#  File build.spec de build ung dung theo kieu ONE-FOLDER (mot thu muc)
# =============================================================================

import multiprocessing
import sys
from os.path import join
import os
import re

# Su dung hook 'collect_all' de thu thap toan bo du lieu cua cac goi phuc tap
from PyInstaller.utils.hooks import collect_all

# =============================================================================
# === KHỐI 1 ĐÃ ĐƯỢC THAY THẾ BẰNG LOGIC "THÔNG MINH" HƠN ===
# =============================================================================
# Khởi tạo một biến để lưu đường dẫn DLL của Conda nếu tìm thấy
conda_dll_path = ''

# Sử dụng sys.base_prefix để luôn tham chiếu đến môi trường Python gốc,
# kể cả khi đang chạy từ bên trong một môi trường ảo (venv).
base_python_dir = sys.base_prefix

print(f"INFO: Môi trường Python gốc (sys.base_prefix): {base_python_dir}")
print(f"INFO: Môi trường Python hiện tại (sys.prefix): {sys.prefix}")

# Từ môi trường gốc, xây dựng đường dẫn tới thư mục Library/bin của Conda
potential_path = os.path.join(base_python_dir, 'Library', 'bin')

# Kiểm tra xem đường dẫn đó có thực sự tồn tại và là một thư mục hay không.
if os.path.isdir(potential_path):
    print(f"INFO: Phat hien moi truong goc la Conda. Them duong dan DLL: {potential_path}")
    conda_dll_path = potential_path
else:
    print("INFO: Moi truong goc khong phai la Conda, bo qua viec them DLL.")
# =============================================================================

sys.path.append(join(SPECPATH, 'src'))
import config

multiprocessing.freeze_support()

# <<< BẮT ĐẦU ĐOẠN CODE ĐÃ SỬA LỖI >>>
# =============================================================================
print("--- Dang tu dong them thu vien tu requirements.txt ---")
requirements_path = join(SPECPATH, '..', 'development', 'requirements.txt')

# TAO MOT BANG ANH XA DE "DICH" TEN GOI THANH TEN MODULE
package_to_module_map = {
    'jupyter-client': 'jupyter_client',
    'jupyter-core': 'jupyter_core',
    'pandas-ta': 'pandas_ta',
    'beautifulsoup4': 'bs4',
    'pymysQL': 'pymysql',
    'google-generativeai': 'google.generativeai',
    'python-dateutil': 'dateutil',
    'python-dotenv': 'dotenv'
    # Cac goi khac co the them vao day neu can
}

# Cac goi nay khong can them vao hidden-imports vi da duoc xu ly theo cach khac
# hoac la goi dung cho moi truong build, khong phai runtime.
ignore_list = {
    'setuptools', 'wheel', 'pywin32', 'PyQt6-sip', 'send2trash', 
    'pyyaml', 'tabulate', 'traitlets', 'pyinstaller', 
    'nbformat', 'debugpy' # nbformat va debugpy da duoc xu ly boi collect_all
}

imports_from_reqs = []
try:
    with open(requirements_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        package_name = re.split(r'[=<>~]', line)[0].strip()
        if package_name and package_name not in ignore_list:
            # SU DUNG BANG ANH XA: Neu ten goi co trong map, lay ten module.
            # Neu khong, mac dinh ten module = ten goi.
            module_name = package_to_module_map.get(package_name, package_name)
            print(f"  -> Phat hien: {package_name}, Them module: {module_name}")
            imports_from_reqs.append(module_name)
except FileNotFoundError:
    print(f"WARNING: Khong tim thay file '{requirements_path}'. Bo qua buoc them tu dong.")
print("--- Hoan thanh them thu vien tu dong ---\n")
# =============================================================================
# <<< KẾT THÚC ĐOẠN CODE ĐÃ SỬA LỖI >>>


block_cipher = None

# --- THU THAP CAC GOI CAN THIET ---

# 1. Thu thap toan bo du lieu va module an cua nbformat
nbformat_datas, nbformat_binaries, nbformat_hiddenimports = collect_all('nbformat')

# 2. Thu thap toan bo goi 'debugpy'
debugpy_datas, debugpy_binaries, debugpy_hiddenimports = collect_all('debugpy')

# 3. Dinh nghia cac module an can thiet khac mot cach chinh xac
required_hiddenimports = [
    'xml.parsers.expat',
    'xml.etree.ElementTree',
    'plistlib',
]

# 4. Tong hop lai cac thong tin
all_hiddenimports = required_hiddenimports + nbformat_hiddenimports + debugpy_hiddenimports + imports_from_reqs

all_datas = [('logo.ico', '.')] + nbformat_datas + debugpy_datas
all_binaries = nbformat_binaries + debugpy_binaries

# === THÊM CÁC DLL QUAN TRỌNG TỪ CONDA (NẾU CÓ) ===
if conda_dll_path:
    # Danh sách các DLL thường gây lỗi trong môi trường Conda
    # Dựa trên lỗi pyexpat và các lỗi tiềm ẩn khác
    important_dlls = [
        'libcrypto-3-x64.dll', 
        'libssl-3-x64.dll',  
        'liblzma.dll',      # Phụ thuộc của lzma
        'sqlite3.dll',      # Phụ thuộc của sqlite3
        'tk86t.dll',        # Phụ thuộc của tkinter
        'tcl86t.dll',       # Phụ thuộc của tkinter
        'libexpat.dll',    # Phụ thuộc của pyexpat (gây ra lỗi của bạn)
        'libbz2.dll',       # Phụ thuộc của _bz2.pyd (tên file trên Windows có thể là libbz2.dll)
        'ffi.dll'           # Phụ thuộc của _ctypes.pyd (cực kỳ quan trọng)
    ]
    
    print("INFO: Them cac file DLL quan trong tu Conda...")
    for dll in important_dlls:
        dll_path = os.path.join(conda_dll_path, dll)
        if os.path.isfile(dll_path):
            print(f"  -> Tim thay va them: {dll}")
            all_binaries.append((dll_path, '.'))
        else:
            print(f"  -> Canh bao: Khong tim thay {dll}")
# ====================================================

a = Analysis(
    ['src/main.py'],
    pathex=[],
    binaries=all_binaries,
    datas=all_datas,
    hiddenimports=all_hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=config.EXE_FILE_NAME,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    icon='logo.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name=config.APP_NAME,
)