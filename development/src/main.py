import sys
import os
from multiprocessing import freeze_support

# Them import cho viec an console
if sys.platform == "win32":
    try:
        import win32gui
        import win32console
    except ImportError:
        # Neu khong co pywin32, bo qua de khong gay loi khi chay tren he dieu hanh khac
        win32gui = None
        win32console = None


# Fix for zmq warning on Windows: "Proactor event loop does not implement add_reader"
if sys.platform == "win32":
    try:
        from asyncio import WindowsSelectorEventLoopPolicy, set_event_loop_policy

        set_event_loop_policy(WindowsSelectorEventLoopPolicy())
    except ImportError:
        pass


def _hide_console_window_on_windows():
    if sys.platform == "win32" and getattr(sys, "frozen", False) and win32console and win32gui:
        try:
            window = win32console.GetConsoleWindow()
            if window:
                win32gui.ShowWindow(window, 0)
        except Exception as e:
            print(f"Error hiding console: {e}")


def _initialize_environment():
    """
    Ham nay se tu dong nhan dien moi truong (dev hoac build)
    va them cac duong dan can thiet vao sys.path.
    """
    if getattr(sys, "frozen", False):
        # --- Chay o che do da build (.exe) ---
        # Duong dan goc la thu muc chua file .exe
        root_dir = os.path.dirname(sys.executable)
        modules_dir = os.path.join(root_dir, "module")
        import_dir = os.path.join(root_dir, "import")
        # print(f"INFO: Frozen mode detected. Root: {root_dir}")
    else:
        # --- Chay o che do development (start.bat) ---
        # Duong dan goc la thu muc goc cua du an
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        modules_dir = os.path.join(project_root, "app", "module")
        import_dir = os.path.join(project_root, "app", "import")
        # print(f"INFO: Development mode detected. Root: {project_root}")

    # Them thu muc module vao sys.path neu no ton tai
    if os.path.exists(modules_dir) and modules_dir not in sys.path:
        sys.path.insert(0, modules_dir)
        # print(f"INFO: Added to sys.path: {modules_dir}")

    # Them thu muc import vao sys.path neu no ton tai
    if os.path.exists(import_dir) and import_dir not in sys.path:
        sys.path.insert(0, import_dir)
        # print(f"INFO: Added to sys.path: {import_dir}")


def _launch_kernel():
    from ipykernel import kernelapp as app

    app.launch_new_instance()


def main():
    from PyQt6.QtWidgets import (
        QApplication,
        QMainWindow,
        QWidget,
        QVBoxLayout,
        QPushButton,
        QScrollArea,
        QGroupBox,
        QSplitter,
    )
    from PyQt6.QtCore import Qt, QTimer, QTime
    from PyQt6.QtGui import QCloseEvent
    import time

    sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__))))
    import config
    import functions
    import styles
    from ui_components import NotebookCard, SectionWidget, ScheduleManagerWidget

    class NotebookRunner(QMainWindow):
        def __init__(self):
            super().__init__()
            self.setWindowTitle(config.APP_NAME)
            self.notebooks_path = config.NOTEBOOKS_DIR
            self.modules_path = config.MODULES_DIR
            self.import_path = config.IMPORT_DIR
            self.available_notebook_cards = {}
            self.highlighted_available = []
            self.sections = {}
            self.section_counter = 0
            self.available_container = None
            self.schedule_manager_widget = None
            self.set_window_icon()
            self.running_processes = {}
            self.setup_ui()
            self.apply_stylesheet()
            self._update_window_minimum_size()

            self.central_schedule_timer = QTimer(self)
            self.central_schedule_timer.timeout.connect(self.check_recurring_tasks)
            self.central_schedule_timer.start(1000)

        def set_window_icon(self):
            functions.setup_window_icon(self)

        # MODIFIED: Updated to account for the schedule manager's visibility
        def _calculate_minimum_window_size(self):
            # Start with the width of the notebook list
            min_width = config.NOTEBOOK_LIST_WIDTH

            # Add width for the schedule manager if it is visible
            if self.schedule_manager_widget and self.schedule_manager_widget.isVisible():
                min_width += config.SCHEDULE_MANAGER_WIDTH

            # Add width for all active sections
            if hasattr(self, "sections"):
                min_width += len(self.sections) * config.RUN_SECTION_WIDTH

            # Add some padding
            min_width += 50

            min_height = config.WINDOW_MIN_HEIGHT
            return (min_width, min_height)

        def _update_window_minimum_size(self):
            min_width, min_height = self._calculate_minimum_window_size()
            self.setMinimumSize(min_width, min_height)

        def setup_ui(self):
            main_widget = QWidget()
            main_widget.setObjectName("MainWidget")
            self.setCentralWidget(main_widget)
            main_layout = QVBoxLayout(main_widget)
            main_layout.setContentsMargins(5, 5, 5, 5)
            self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
            self.main_splitter.setObjectName("MainSplitter")
            self.main_splitter.setHandleWidth(8)

            self.schedule_manager_widget = ScheduleManagerWidget(self)
            self.schedule_manager_widget.section_close_requested.connect(self.toggle_schedule_manager)
            self.schedule_manager_widget.setVisible(False)
            self.main_splitter.addWidget(self.schedule_manager_widget)

            self.available_container = QWidget()
            available_container_layout = QVBoxLayout(self.available_container)
            available_container_layout.setContentsMargins(0, 0, 0, 0)
            available_container_layout.setSpacing(10)
            available_group = QGroupBox("📚 Danh sách Notebooks")
            available_group.setObjectName("AvailableGroup")
            available_layout = QVBoxLayout(available_group)
            available_layout.setContentsMargins(5, 10, 5, 5)
            available_layout.setSpacing(8)
            self.available_scroll_area = QScrollArea()
            self.available_scroll_area.setWidgetResizable(True)
            self.available_scroll_area.setObjectName("AvailableScrollArea")
            self.available_cards_widget = QWidget()
            self.available_cards_widget.setObjectName("CardsContainer")
            self.available_cards_layout = QVBoxLayout(self.available_cards_widget)
            self.available_cards_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
            self.available_cards_layout.setSpacing(6)
            self.available_scroll_area.setWidget(self.available_cards_widget)
            available_layout.addWidget(self.available_scroll_area)
            controls_group = QGroupBox("⚙️ Điều Khiển Chung")
            controls_group.setObjectName("ControlsGroup")
            controls_layout = QVBoxLayout(controls_group)
            controls_layout.setContentsMargins(5, 10, 5, 5)
            controls_layout.setSpacing(8)

            refresh_button = QPushButton("Làm Mới NoteBooks")
            refresh_button.setObjectName("RefreshButton")
            refresh_button.setCursor(Qt.CursorShape.PointingHandCursor)
            refresh_button.clicked.connect(self.refresh_notebook_list)

            manage_tasks_button = QPushButton("Tác Vụ Hẹn Giờ")
            manage_tasks_button.setObjectName("ManageTasksButton")
            manage_tasks_button.setCursor(Qt.CursorShape.PointingHandCursor)
            manage_tasks_button.clicked.connect(self.toggle_schedule_manager)

            add_section_button = QPushButton("Thêm Section Mới")
            add_section_button.setObjectName("AddSectionButton")
            add_section_button.setCursor(Qt.CursorShape.PointingHandCursor)
            add_section_button.clicked.connect(self.create_new_section)

            controls_layout.addWidget(refresh_button)
            controls_layout.addWidget(manage_tasks_button)
            controls_layout.addWidget(add_section_button)

            available_container_layout.addWidget(available_group)
            available_container_layout.addWidget(controls_group)
            self.available_container.setMinimumWidth(config.NOTEBOOK_LIST_WIDTH)
            self.main_splitter.addWidget(self.available_container)

            self.main_splitter.setStretchFactor(0, 0)
            self.main_splitter.setStretchFactor(1, 1)

            main_layout.addWidget(self.main_splitter)
            self.refresh_notebook_list()
            self._update_window_minimum_size()
            self.update()
            QApplication.processEvents()
            self.create_new_section()

        def apply_stylesheet(self):
            self.setStyleSheet(styles.get_stylesheet())

        def _create_card_in_list(self, path, parent_layout, card_dict):
            description = functions.get_notebook_description(path)
            card = NotebookCard(path, description, self)
            card.clicked.connect(self._on_card_click)

            new_name = os.path.basename(path)
            insert_pos = 0
            for i in range(parent_layout.count()):
                item = parent_layout.itemAt(i)
                widget = item.widget()
                if widget and isinstance(widget, NotebookCard):
                    if os.path.basename(widget.path) > new_name:
                        break
                insert_pos += 1

            parent_layout.insertWidget(insert_pos, card)
            card_dict[path] = card

        def _on_card_click(self, path):
            functions.handle_card_click(path, self.available_notebook_cards, self.highlighted_available)

        def refresh_notebook_list(self):
            functions.refresh_notebook_list(self)

        def log_message_to_cmd(self, message, is_block=False):
            if is_block:
                print(message)
            else:
                functions.log_message(message)

        def closeEvent(self, a0: QCloseEvent | None) -> None:
            total_running = sum(len(s.running_processes) for s in self.sections.values())
            reply = functions.handle_close_event(total_running, self)
            if reply:
                if a0:
                    a0.accept()
            else:
                if a0:
                    a0.ignore()

        def create_new_section(self):
            self.section_counter += 1
            section_name = f"Section {self.section_counter}"
            section_id = f"section_{self.section_counter}"
            section_widget = SectionWidget(section_name, section_id, self)
            section_widget.notebooks_dropped.connect(self.move_notebooks_to_section)
            section_widget.notebook_remove_requested.connect(self.remove_notebooks_from_section)
            section_widget.section_close_requested.connect(self.close_section)
            self.main_splitter.addWidget(section_widget)
            self.sections[section_id] = section_widget
            self._update_window_minimum_size()
            self.log_message_to_cmd(f"Đã tạo section mới: {section_name}")
            if self.schedule_manager_widget:
                self.schedule_manager_widget.update_section_list(self.sections)

        def move_notebooks_to_section(self, section_widget, paths_to_move):
            for path in paths_to_move:
                if path in self.available_notebook_cards:
                    old_card = self.available_notebook_cards[path]
                    description = old_card.desc_label.text()
                    self.available_cards_layout.removeWidget(old_card)
                    old_card.deleteLater()
                    del self.available_notebook_cards[path]
                    section_widget.add_notebook_card(path, description)

                    nb_name = os.path.basename(path)
                    self.log_message_to_cmd(f"Đã thêm notebook '{nb_name}' vào section '{section_widget.section_name}'.")

            self.highlighted_available.clear()

        def remove_notebooks_from_section(self, section_widget, paths):
            for path in paths:
                if path in section_widget.notebook_cards:
                    section_widget.remove_notebook_card(path)
                    self._create_card_in_list(path, self.available_cards_layout, self.available_notebook_cards)

                    nb_name = os.path.basename(path)
                    self.log_message_to_cmd(f"Đã loại bỏ notebook '{nb_name}' khỏi section '{section_widget.section_name}'.")

        def close_section(self, section_widget):
            section_id = section_widget.section_id
            if section_widget.notebook_cards:
                self.remove_notebooks_from_section(section_widget, list(section_widget.notebook_cards.keys()))
            section_widget.cleanup()
            section_widget.setParent(None)
            section_widget.deleteLater()
            if section_id in self.sections:
                del self.sections[section_id]
            self._update_window_minimum_size()
            self.log_message_to_cmd(f"Đã đóng section: {section_widget.section_name}")
            if self.schedule_manager_widget:
                self.schedule_manager_widget.update_section_list(self.sections)

        # MODIFIED: Logic now also updates the window's minimum size
        def toggle_schedule_manager(self):
            if self.schedule_manager_widget:
                is_visible = self.schedule_manager_widget.isVisible()
                self.schedule_manager_widget.setVisible(not is_visible)
                if not is_visible:
                    self.schedule_manager_widget.update_section_list(self.sections)
                # Recalculate and set the new minimum window size
                self._update_window_minimum_size()

        def check_recurring_tasks(self):
            if not self.schedule_manager_widget or not self.schedule_manager_widget.isVisible():
                return

            tasks = self.schedule_manager_widget.get_tasks()
            now = QTime.currentTime()

            for task_id, task_info in list(tasks.items()):
                if task_info["time"].hour() == now.hour() and task_info["time"].minute() == now.minute():
                    if task_info.get("last_run_time") == now.toString("HH:mm"):
                        continue

                    target_section_id = task_info["section_id"]
                    target_section = self.sections.get(target_section_id)

                    if target_section:
                        action_key = task_info["action_key"]
                        if hasattr(target_section, action_key):
                            getattr(target_section, action_key)()
                            log_message = (
                                f"Tác vụ định kỳ: Thực thi '{task_info['action_text']}' "
                                f"cho '{target_section.section_name}' lúc {now.toString('HH:mm')}"
                            )
                            self.log_message_to_cmd(log_message)

                            self.schedule_manager_widget.mark_task_as_run(task_id, now.toString("HH:mm"))
                else:
                    if task_info.get("last_run_time"):
                        self.schedule_manager_widget.reset_task_run_marker(task_id)

    app = QApplication(sys.argv)
    functions.setup_application_icon(app)
    window = NotebookRunner()
    try:
        screen = app.primaryScreen()
        if screen:
            screen_geometry = screen.availableGeometry()
            window_geometry = window.frameGeometry()
            window_geometry.moveCenter(screen_geometry.center())
            final_x = max(0, window_geometry.topLeft().x() - 300)
            final_y = max(0, window_geometry.topLeft().y())
            window.move(final_x, final_y)
    except Exception as e:
        print(f"Lỗi khi định vị cửa sổ: {e}")
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    freeze_support()
    _initialize_environment()

    if "-f" in sys.argv:
        _launch_kernel()
    else:
        _hide_console_window_on_windows()
        main()
