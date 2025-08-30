import os
import sys

def get_root_dir():
    """
    Lấy thư mục gốc của dự án.
    Xử lý cả trường hợp chạy từ source code và từ file .exe đã build.
    """
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    else:
        current_file_dir = os.path.dirname(os.path.abspath(__file__))
        development_dir = os.path.dirname(current_file_dir)
        project_root = os.path.dirname(development_dir)
        return project_root


APP_NAME = "CTSReport"
EXE_FILE_NAME = "CTSReport.exe"
JUPYTER_KERNEL_NAME = f"{APP_NAME.lower().replace(' ', '-')}-venv"

ROOT_DIR = get_root_dir()
ICON_PATH = os.path.join(ROOT_DIR, "development", "logo.ico")
DEBUG = False

if getattr(sys, "frozen", False):
    MODULES_DIR = os.path.join(ROOT_DIR, "module")
    NOTEBOOKS_DIR = os.path.join(ROOT_DIR, "notebook")
    IMPORT_DIR = os.path.join(ROOT_DIR, "import")
else:
    MODULES_DIR = os.path.join(ROOT_DIR, "app", "module")
    NOTEBOOKS_DIR = os.path.join(ROOT_DIR, "app", "notebook")
    IMPORT_DIR = os.path.join(ROOT_DIR, "app", "import")

APP_BUILD_DIR = os.path.join(ROOT_DIR, "app")

# ===== CÀI ĐẶT KÍCH THƯỚC UI =====
WINDOW_MIN_HEIGHT = 500
NOTEBOOK_LIST_WIDTH = 230
RUN_SECTION_WIDTH = 270
SCHEDULE_MANAGER_WIDTH = 300
SPLITTER_INITIAL_SIZES = [NOTEBOOK_LIST_WIDTH]

# ===== CÀI ĐẶT LOGGING (MỚI) =====
LOG_TITLE_NOTEBOOK_PRINT = "Output từ '{nb_name}' tại '{section_name}'"
LOG_TITLE_NOTEBOOK_ERROR = "Lỗi khi chạy '{nb_name}' tại '{section_name}'"
MAX_CONSECUTIVE_ERRORS_CONTINOUS = 99
MAX_CONSECUTIVE_ERRORS_FINITE = 5
