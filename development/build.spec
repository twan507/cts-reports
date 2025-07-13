# -*- mode: python ; coding: utf-8 -*-

# =============================================================================
#  File build.spec de build ung dung theo kieu ONE-FOLDER (mot thu muc)
#  PHIÊN BẢN SỬA LỖI CUỐI CÙNG - DÙNG HOOKS CHO THƯ VIỆN CỨNG ĐẦU
# =============================================================================

import multiprocessing
import sys
import os
import re
from os.path import join, isdir

from PyInstaller.utils.hooks import collect_all, collect_submodules, collect_data_files

# =============================================================================
# KHỐI 1: LOGIC TÌM DLL CỦA CONDA (GIỮ NGUYÊN)
# =============================================================================
conda_dll_path = ''
base_python_dir = sys.base_prefix

print(f"INFO: Môi trường Python gốc (sys.base_prefix): {base_python_dir}")
print(f"INFO: Môi trường Python hiện tại (sys.prefix): {sys.prefix}")

potential_path = os.path.join(base_python_dir, 'Library', 'bin')

if os.path.isdir(potential_path):
    print(f"INFO: Phat hien moi truong goc la Conda. Them duong dan DLL: {potential_path}")
    conda_dll_path = potential_path
else:
    print("INFO: Moi truong goc khong phai la Conda, bo qua viec them DLL.")
# =============================================================================

sys.path.append(join(SPECPATH, 'src'))
import config

multiprocessing.freeze_support()

# =============================================================================
# KHỐI 2: TỰ ĐỘNG THÊM THƯ VIỆN TỪ REQUIREMENTS.TXT (GIỮ NGUYÊN)
# =============================================================================
print("--- Dang tu dong them thu vien tu requirements.txt ---")
requirements_path = join(SPECPATH, '..', 'development', 'requirements.txt')

package_to_module_map = {
    'jupyter-client': 'jupyter_client',
    'jupyter-core': 'jupyter_core',
    'beautifulsoup4': 'bs4',
    'google-generativeai': 'google.generativeai',
    'ipython': 'IPython',
    'pandas-ta': 'pandas_ta',
    'Pillow': 'PIL',
    'PyMySQL': 'pymysql',
    'python-dateutil': 'dateutil',
    'python-dotenv': 'dotenv',
    'PyYAML': 'yaml',
    'scikit-learn': 'sklearn',
    'fpdf2': 'fpdf',
}

ignore_list = {
    'setuptools', 'wheel', 'pywin32', 'pyinstaller', 'pip',
    'PyQt6', 'PyQt6-sip',
    'nbformat', 'debugpy', 'plotly',
    'pyinstaller-hooks-contrib',
    'fiinquantx',
}

imports_from_reqs = []
try:
    with open(requirements_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#') or line.startswith('--'):
            continue
        
        package_name = re.split(r'[=<>~]', line)[0].strip()
        
        if package_name and package_name not in ignore_list:
            module_name = package_to_module_map.get(package_name, package_name)
            print(f"  -> Phat hien: {package_name}, Them module: {module_name}")
            if module_name not in imports_from_reqs:
                 imports_from_reqs.append(module_name)

except FileNotFoundError:
    print(f"WARNING: Khong tim thay file '{requirements_path}'. Bo qua buoc them tu dong.")
print("--- Hoan thanh them thu vien tu dong ---\n")
# =============================================================================


block_cipher = None

# --- THU THẬP CÁC GÓI PHỨC TẠP BẰNG HOOKS ---
datas_nbformat, binaries_nbformat, hiddenimports_nbformat = collect_all('nbformat')
datas_debugpy, binaries_debugpy, hiddenimports_debugpy = collect_all('debugpy')
datas_plotly, _, _ = collect_all('plotly')

## <<< SỬA LỖI: Sửa lại cách gọi hàm cho đúng
datas_fpdf = collect_data_files('fpdf')

# TẠM THỜI VÔ HIỆU HÓA FIINQUANTX - BỎ COMMENT ĐỂ BẬT LẠI
# hiddenimports_fiinquantx = collect_submodules('fiinquantx')
# print(f"INFO: Phat hien {len(hiddenimports_fiinquantx)} module con cho 'fiinquantx' bang collect_submodules.")
hiddenimports_fiinquantx = []  # Tạm thời để rỗng


# --- ĐỊNH NGHĨA CÁC MODULE ẨN CẦN THIẾT ---
required_hiddenimports = [
    'win32gui',
    'win32console',
    'sqlalchemy.dialects.mysql',
    'cryptography.fernet',
    'alpha_vantage',
    'alpha_vantage.foreignexchange'
]

# --- TỔNG HỢP CÁC THÀNH PHẦN ---
all_hiddenimports = (
    required_hiddenimports +
    hiddenimports_nbformat +
    hiddenimports_debugpy +
    imports_from_reqs + 
    hiddenimports_fiinquantx
)

all_datas = [
    ('logo.ico', '.'),
] + datas_nbformat + datas_debugpy + datas_plotly + datas_fpdf

all_binaries = (
    binaries_nbformat + 
    binaries_debugpy
)

# =============================================================================
# KHỐI 3: THÊM CÁC DLL QUAN TRỌNG TỪ CONDA (GIỮ NGUYÊN)
# =============================================================================
if conda_dll_path:
    important_dlls = [
        'libcrypto-3-x64.dll', 'libssl-3-x64.dll', 'liblzma.dll',
        'sqlite3.dll', 'tk86t.dll', 'tcl86t.dll', 'libexpat.dll',
        'libbz2.dll', 'ffi.dll'
    ]
    
    print("INFO: Them cac file DLL quan trong tu Conda...")
    for dll in important_dlls:
        dll_path = os.path.join(conda_dll_path, dll)
        if os.path.isfile(dll_path):
            print(f"  -> Tim thay va them: {dll}")
            all_binaries.append((dll_path, '.'))
        else:
            print(f"  -> Canh bao: Khong tim thay {dll} tai {conda_dll_path}")
# =============================================================================

site_packages_path = os.path.join(sys.prefix, 'Lib', 'site-packages')

a = Analysis(
    ['src/main.py'],
    pathex=[site_packages_path],
    binaries=all_binaries,
    datas=all_datas,
    hiddenimports=list(set(all_hiddenimports)),
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