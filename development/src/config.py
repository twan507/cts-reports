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


ROOT_DIR = get_root_dir()
DEBUG = False
APP_NAME = "Report Generator"
EXE_FILE_NAME = "ReportGenerator.exe"
ICON_PATH = os.path.join(ROOT_DIR, "development", "logo.ico")

if getattr(sys, "frozen", False):
    MODULES_DIR = os.path.join(ROOT_DIR, "module")
    NOTEBOOKS_DIR = os.path.join(ROOT_DIR, "notebook")
else:
    MODULES_DIR = os.path.join(ROOT_DIR, "app", "module")
    NOTEBOOKS_DIR = os.path.join(ROOT_DIR, "app", "notebook")

APP_BUILD_DIR = os.path.join(ROOT_DIR, "app")

# ===== CÀI ĐẶT KÍCH THƯỚC UI =====
WINDOW_MIN_HEIGHT = 600

NOTEBOOK_LIST_INITIAL_WIDTH = 300
NOTEBOOK_LIST_MIN_WIDTH = 300

SECTION_MIN_WIDTH = 400
SECTION_DISPLAY_WIDTH = 400

SPLITTER_INITIAL_SIZES = [NOTEBOOK_LIST_INITIAL_WIDTH]

# ===== CÀI ĐẶT LOGGING (MỚI) =====
LOG_TITLE_NOTEBOOK_PRINT = "Output từ '{nb_name}' tại '{section_name}'"
LOG_TITLE_NOTEBOOK_ERROR = "Lỗi khi chạy '{nb_name}' tại '{section_name}'"
