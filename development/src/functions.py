# development/src/functions.py
"""
Module chứa các hàm xử lý chức năng cho ứng dụng NotebookRunner
"""

import os
import sys
import traceback
import time
import nbformat
from multiprocessing import Process, Queue, Event

from PyQt6.QtWidgets import QMessageBox, QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon

from nbconvert.preprocessors import ExecutePreprocessor
from nbclient.exceptions import CellExecutionError

import config


# --- CÁC HÀM TIỆN ÍCH (KHÔNG THAY ĐỔI) ---
def get_resource_path(relative_path):
    if getattr(sys, "frozen", False):
        base_path = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
        return os.path.join(base_path, relative_path)
    return os.path.join(config.ROOT_DIR, relative_path)


def setup_window_icon(window):
    try:
        icon_path = get_resource_path("logo.ico") if getattr(sys, "frozen", False) else config.ICON_PATH
        if os.path.exists(icon_path):
            window.setWindowIcon(QIcon(icon_path))
    except Exception as e:
        print(f"[ERROR] Không thể thiết lập icon: {e}")


def setup_application_icon(app):
    if hasattr(config, "ICON_PATH") and os.path.exists(config.ICON_PATH):
        app.setWindowIcon(QIcon(config.ICON_PATH))


def handle_card_click(path, available_notebook_cards, highlighted_available):
    if path not in available_notebook_cards:
        return

    card = available_notebook_cards[path]
    is_ctrl_pressed = bool(QApplication.keyboardModifiers() & Qt.KeyboardModifier.ControlModifier)

    if is_ctrl_pressed:
        if card.is_highlighted:
            card.set_highlighted(False)
            if path in highlighted_available:
                highlighted_available.remove(path)
        else:
            card.set_highlighted(True)
            if path not in highlighted_available:
                highlighted_available.append(path)
    else:
        if not card.is_highlighted:
            for p in list(highlighted_available):
                if p in available_notebook_cards:
                    available_notebook_cards[p].set_highlighted(False)

            highlighted_available.clear()
            highlighted_available.append(path)
            card.set_highlighted(True)
        else:
            pass


def refresh_notebook_list(runner_instance):
    """
    Làm mới danh sách notebook một cách thông minh.
    - Thêm các notebook mới vào danh sách chờ.
    - Xóa các notebook không còn tồn tại khỏi giao diện.
    - Không ảnh hưởng đến các notebook đã có trong sections.
    - Việc cập nhật code của notebook/module được xử lý ngầm khi chạy lại.
    """
    notebooks_path = runner_instance.notebooks_path
    log_message("Bắt đầu làm mới danh sách notebooks...")

    # 1. Lấy tất cả các notebook hiện đang được biết đến bởi ứng dụng (cả trong danh sách chờ và trong các section)
    known_paths = set(runner_instance.available_notebook_cards.keys())
    for section in runner_instance.sections.values():
        known_paths.update(section.notebook_cards.keys())

    # 2. Lấy tất cả các notebook .ipynb hiện có trên đĩa
    try:
        if not os.path.exists(notebooks_path):
            log_message(f"Lỗi làm mới: Không tìm thấy thư mục: {notebooks_path}")
            return
        disk_paths = {os.path.join(notebooks_path, f) for f in os.listdir(notebooks_path) if f.endswith(".ipynb")}
    except Exception as e:
        log_message(f"Lỗi làm mới: Không thể đọc thư mục {notebooks_path}: {e}")
        return

    # 3. Tìm các notebook mới và các notebook đã bị xóa
    new_paths = disk_paths - known_paths
    deleted_paths = known_paths - disk_paths

    # 4. Thêm các notebook mới vào danh sách chờ
    if new_paths:
        sorted_new_paths = sorted(list(new_paths), key=lambda p: os.path.basename(p))
        for path in sorted_new_paths:
            runner_instance._create_card_in_list(path, runner_instance.available_cards_layout, runner_instance.available_notebook_cards)
        log_message(f"Đã thêm {len(new_paths)} notebook mới vào danh sách.")

    # 5. Xóa các notebook không còn tồn tại khỏi giao diện
    if deleted_paths:
        for path in deleted_paths:
            # Kiểm tra và xóa khỏi danh sách chờ
            if path in runner_instance.available_notebook_cards:
                card = runner_instance.available_notebook_cards.pop(path)
                if card:
                    card.deleteLater()
                if path in runner_instance.highlighted_available:
                    runner_instance.highlighted_available.remove(path)
            # Kiểm tra và xóa khỏi các section
            else:
                for section in runner_instance.sections.values():
                    if path in section.notebook_cards:
                        section.remove_notebook_card(path)
                        break  # Giả sử notebook chỉ ở một nơi
        log_message(f"Đã xóa {len(deleted_paths)} notebook không còn tồn tại.")

    log_message("Làm mới hoàn tất. Code và module mới nhất sẽ được sử dụng trong lần chạy tiếp theo.")


def log_message(message):
    timestamp = time.strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}")


def format_output_for_cmd(title, content, width=100):
    separator = "=" * width
    formatted_title = f" {title} ".center(width, "=")

    return f"""{formatted_title}
{content.strip()}
{separator}"""


def handle_close_event(running_count, parent_widget=None):
    if running_count > 0:
        msg_box = QMessageBox(parent_widget)
        msg_box.setWindowTitle("Xác nhận thoát ứng dụng")
        msg_box.setText(f"Bạn có chắc muốn thoát ứng dụng không?\nCó {running_count} notebook(s) đang chạy sẽ bị dừng.")
        msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg_box.setDefaultButton(QMessageBox.StandardButton.No)
        msg_box.setIcon(QMessageBox.Icon.Question)

        # Apply stylesheet if parent has one
        if parent_widget and hasattr(parent_widget, "styleSheet") and parent_widget.styleSheet():
            msg_box.setStyleSheet(parent_widget.styleSheet())

        reply = msg_box.exec()
        return reply == QMessageBox.StandardButton.Yes
    return True


def get_notebook_description(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            notebook = nbformat.read(f, as_version=4)
        for cell in notebook.cells:
            if cell.cell_type == "markdown":
                for line in cell.source.split("\n"):
                    if line.strip().startswith("# "):
                        return line.strip()[2:].strip()
        return "Không có mô tả"
    except Exception:
        return "Không thể đọc mô tả."


def _execute_notebook_process(
    notebook_path, log_queue, stop_event, execution_mode, execution_count, execution_delay, modules_path, import_path
):
    notebook_dir = os.path.dirname(notebook_path)

    code_to_inject = f"""
        import sys
        import os

        # Khối mã này cực kỳ quan trọng để file .exe hoạt động.
        # Nó đảm bảo tiến trình kernel có thể tìm thấy tất cả các thư viện đã được đóng gói (như pandas).
        if getattr(sys, 'frozen', False):
            # Trong ứng dụng đã build, thư mục gốc là thư mục chứa file .exe
            # Tất cả thư viện được PyInstaller đóng gói vào thư mục '_internal'.
            root_dir = os.path.dirname(sys.executable)
            internal_libs_path = os.path.join(root_dir, '_internal')
            
            # Thêm đường dẫn thư viện đã đóng gói vào sys.path
            if os.path.exists(internal_libs_path) and internal_libs_path not in sys.path:
                sys.path.insert(0, internal_libs_path)
                print(f"NBRunner (Frozen): Added bundled libs path: {{internal_libs_path}}")

        # Khối mã này đảm bảo các module tùy chỉnh của người dùng được tìm thấy.
        # Nó nhận các đường dẫn tuyệt đối từ ứng dụng chính.
        modules_path = {repr(modules_path)}
        import_path = {repr(import_path)}

        # Thêm thư mục 'module' vào sys.path
        if os.path.exists(modules_path) and modules_path not in sys.path:
            sys.path.insert(0, modules_path)

        # Thêm thư mục 'import' vào sys.path
        if os.path.exists(import_path) and import_path not in sys.path:
            sys.path.insert(0, import_path)
        """

    def run_single_notebook():
        nb = None
        try:
            with open(notebook_path, "r", encoding="utf-8") as f:
                nb = nbformat.read(f, as_version=4)
            injected_cell = nbformat.v4.new_code_cell(code_to_inject)
            nb.cells.insert(0, injected_cell)

            ep = ExecutePreprocessor(timeout=3600)
            ep.preprocess(nb, {"metadata": {"path": notebook_dir}})

            for cell in nb.cells:
                if "outputs" in cell:
                    for output in cell.outputs:
                        if output.output_type == "stream" and output.text.strip():
                            log_queue.put(("NOTEBOOK_PRINT", output.text))
            return True, nb
        except CellExecutionError as e:
            error_details = f"Lỗi trong cell:\n{e.ename}: {e.evalue}\n--- Traceback ---\n{traceback.format_exc()}"
            log_queue.put(("EXECUTION_ERROR", {"details": error_details}))
            return False, nb
        except Exception as e:
            error_details = f"Lỗi không mong muốn: {e}\n{traceback.format_exc()}"
            log_queue.put(("EXECUTION_ERROR", {"details": error_details}))
            return False, nb

    # Chạy lặp vô hạn
    if execution_mode == "continuous":
        iteration = 1
        consecutive_errors = 0
        while not stop_event.is_set():
            log_queue.put(("RESET_TIMER", None))
            log_queue.put(("ITERATION_START", {"iteration": iteration, "total": None}))
            start_time = time.time()
            success, final_nb = run_single_notebook()
            duration = time.time() - start_time

            if success:
                consecutive_errors = 0
            else:
                consecutive_errors += 1

            log_queue.put(
                (
                    "ITERATION_END",
                    {"iteration": iteration, "success": success, "duration": duration, "consecutive_errors": consecutive_errors},
                )
            )

            if not success and consecutive_errors >= config.MAX_CONSECUTIVE_ERRORS_CONTINOUS:
                log_queue.put(("SECTION_LOG", f"Dừng do lỗi {consecutive_errors} lần liên tiếp."))
                break

            if stop_event.is_set():
                break

            if execution_delay > 0 and not stop_event.is_set():
                log_queue.put(("SECTION_LOG", f"Nghỉ {execution_delay}s..."))
                time.sleep(execution_delay)
            iteration += 1

    # Chạy lặp hữu hạn (chỉ tính lần thành công)
    else:
        successful_runs = 0
        total_runs = 0
        consecutive_errors = 0

        while successful_runs < execution_count:
            if stop_event.is_set():
                log_queue.put(("SECTION_LOG", "Đã hủy các lần chạy còn lại."))
                break

            total_runs += 1
            log_queue.put(("RESET_TIMER", None))
            log_queue.put(("ITERATION_START", {"iteration": total_runs, "total": execution_count, "success_count": successful_runs}))

            start_time = time.time()
            success, final_nb = run_single_notebook()
            duration = time.time() - start_time

            if success:
                successful_runs += 1
                consecutive_errors = 0
            else:
                consecutive_errors += 1

            log_queue.put(
                (
                    "ITERATION_END",
                    {"iteration": total_runs, "success": success, "duration": duration, "consecutive_errors": consecutive_errors},
                )
            )

            if not success and consecutive_errors >= config.MAX_CONSECUTIVE_ERRORS_FINITE:
                log_queue.put(("SECTION_LOG", f"Dừng do lỗi {consecutive_errors} lần liên tiếp."))
                break

    log_queue.put(("EXECUTION_FINISHED", True))


def run_notebook_with_individual_logging(
    notebook_path, running_processes, card, execution_mode, execution_count, execution_delay, modules_path, import_path
):
    if notebook_path in running_processes:
        return

    log_queue = Queue()
    stop_event = Event()
    process_args = (notebook_path, log_queue, stop_event, execution_mode, execution_count, execution_delay, modules_path, import_path)
    process = Process(target=_execute_notebook_process, args=process_args, daemon=True)
    running_processes[notebook_path] = {"process": process, "stop_event": stop_event, "queue": log_queue, "card": card}

    process.start()
