# development/src/ui_components.py
"""
Module chứa các UI components tùy chỉnh cho ứng dụng NotebookRunner
"""

import os
import time
from functools import partial
from PyQt6.QtWidgets import (
    QLabel,
    QFrame,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QScrollArea,
    QWidget,
    QGroupBox,
    QComboBox,
    QSpinBox,
    QTextEdit,
    QSizePolicy,
    QMessageBox,
    QApplication,
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QTime, QMimeData, QPoint, QRect
from PyQt6.QtGui import (
    QFont,
    QMouseEvent,
    QDrag,
    QDropEvent,
    QDragEnterEvent,
    QPixmap,
    QPainter,
    QColor,
    QBrush,
    QPen,
    QTextCursor,
)
import config
import functions


class ClickableLabel(QLabel):
    doubleClicked = pyqtSignal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def mouseDoubleClickEvent(self, a0: QMouseEvent | None) -> None:
        if not a0:
            return
        self.doubleClicked.emit()
        super().mouseDoubleClickEvent(a0)


class ClickableLink(QLabel):
    clicked = pyqtSignal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet("QLabel { color: #cc0000; } QLabel:hover { text-decoration: underline; }")

    def mousePressEvent(self, ev: QMouseEvent | None) -> None:
        if not ev:
            return
        self.clicked.emit()
        super().mousePressEvent(ev)


class NotebookCard(QFrame):
    clicked = pyqtSignal(str)

    def __init__(self, path, description, parent_runner, parent=None):
        super().__init__(parent)
        self.path, self.is_highlighted, self.parent_runner = path, False, parent_runner
        self.press_pos: QPoint | None = None
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setObjectName("Card")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        self.filename_label = QLabel(os.path.basename(path))
        self.filename_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self.filename_label.setObjectName("CardLabel")
        self.filename_label.setWordWrap(True)
        self.desc_label = QLabel(description)
        self.desc_label.setFont(QFont("Segoe UI", 9))
        self.desc_label.setObjectName("CardLabel")
        self.desc_label.setWordWrap(True)
        self.desc_label.setStyleSheet("color: #666666;")
        layout.addWidget(self.filename_label)
        layout.addWidget(self.desc_label)

    def mousePressEvent(self, a0: QMouseEvent | None) -> None:
        if not a0:
            return
        self.press_pos = a0.pos()
        self.clicked.emit(self.path)

    def create_transparent_drag_pixmap(self):
        pixmap = QPixmap(self.size())
        pixmap.fill(Qt.GlobalColor.transparent)
        original_autofill = self.autoFillBackground()
        self.setAutoFillBackground(False)
        self.render(pixmap, flags=QWidget.RenderFlag.DrawChildren)
        self.setAutoFillBackground(original_autofill)
        return pixmap

    def create_stacked_pixmap(self, selected_paths):
        all_cards = self.parent_runner.available_notebook_cards
        selected_cards = [all_cards[p] for p in selected_paths if p in all_cards]
        if not selected_cards:
            return self.create_transparent_drag_pixmap()
        max_cards_to_show = 4
        offset_x, offset_y = 8, 8
        base_size = selected_cards[0].size()
        card_width, card_height = base_size.width(), base_size.height()
        num_cards_in_stack = min(len(selected_cards), max_cards_to_show)
        total_width = card_width + (offset_x * (num_cards_in_stack - 1))
        total_height = card_height + (offset_y * (num_cards_in_stack - 1))
        final_pixmap = QPixmap(total_width, total_height)
        final_pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(final_pixmap)
        for i in range(num_cards_in_stack):
            index = num_cards_in_stack - 1 - i
            card_to_draw = selected_cards[index]
            card_pixmap = card_to_draw.create_transparent_drag_pixmap()
            painter.drawPixmap(offset_x * index, offset_y * index, card_pixmap)
        if len(selected_cards) > max_cards_to_show:
            badge_size = 22
            badge_rect = QRect(total_width - badge_size - 2, 2, badge_size, badge_size)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setBrush(QBrush(QColor("#0d6efd")))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(badge_rect)
            painter.setPen(QPen(Qt.GlobalColor.white))
            font = QFont("Segoe UI", 8, QFont.Weight.Bold)
            painter.setFont(font)
            painter.drawText(badge_rect, Qt.AlignmentFlag.AlignCenter, f"+{len(selected_cards) - max_cards_to_show + 1}")
        painter.end()
        return final_pixmap

    def mouseMoveEvent(self, a0: QMouseEvent | None) -> None:
        if not a0 or a0.buttons() != Qt.MouseButton.LeftButton or not self.is_highlighted:
            return
        selected_paths = self.parent_runner.highlighted_available
        if not selected_paths:
            return
        drag = QDrag(self)
        mime_data = QMimeData()
        mime_data.setText("\n".join(selected_paths))
        drag.setMimeData(mime_data)
        if len(selected_paths) <= 1:
            pixmap = self.create_transparent_drag_pixmap()
        else:
            pixmap = self.create_stacked_pixmap(selected_paths)
        drag.setPixmap(pixmap)
        drag.setHotSpot(a0.pos())
        drag.exec(Qt.DropAction.MoveAction)

    def mouseReleaseEvent(self, a0: QMouseEvent | None) -> None:
        if not a0 or self.press_pos is None:
            return
        moved_distance = (a0.pos() - self.press_pos).manhattanLength()
        if moved_distance >= QApplication.startDragDistance():
            return
        is_ctrl_pressed = bool(QApplication.keyboardModifiers() & Qt.KeyboardModifier.ControlModifier)
        if not is_ctrl_pressed and self.is_highlighted and len(self.parent_runner.highlighted_available) > 1:
            other_selected_paths = list(self.parent_runner.highlighted_available)
            for p in other_selected_paths:
                if p != self.path and p in self.parent_runner.available_notebook_cards:
                    self.parent_runner.available_notebook_cards[p].set_highlighted(False)
            self.parent_runner.highlighted_available.clear()
            self.parent_runner.highlighted_available.append(self.path)

    def set_highlighted(self, highlighted):
        self.is_highlighted = highlighted
        self.setObjectName("SelectedCard" if highlighted else "Card")
        style = self.style()
        if style:
            style.unpolish(self)
            style.polish(self)


class SectionNotebookCard(QFrame):
    run_requested = pyqtSignal(object)
    stop_requested = pyqtSignal(str)
    remove_requested = pyqtSignal(str)
    execution_truly_finished = pyqtSignal(str, bool)

    def __init__(self, path, description, parent=None):
        super().__init__(parent)
        self.path, self.description = path, description
        self.execution_mode, self.execution_count, self.execution_delay, self.current_status, self.start_time = (
            "continuous",
            1,
            0,
            "ready",
            None,
        )
        self.consecutive_error_count = 0
        self.MAX_CONSECUTIVE_ERRORS = 99
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setObjectName("SectionCard")
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.total_elapsed_timer = QTimer(self)
        self.total_elapsed_timer.timeout.connect(self.update_total_elapsed_timer)
        self.iteration_logs = {}
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        title_label = QLabel(os.path.basename(self.path))
        title_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        title_label.setWordWrap(True)
        layout.addWidget(title_label)
        desc_label = QLabel(self.description)
        desc_label.setFont(QFont("Segoe UI", 8))
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #666666;")
        layout.addWidget(desc_label)

        mode_layout = QHBoxLayout()
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Lặp lại vô hạn", "Lặp lại hữu hạn"])
        self.mode_combo.currentTextChanged.connect(self.on_mode_changed)
        mode_layout.addWidget(self.mode_combo, 1)

        self.delay_label = QLabel("Nghỉ (s):")
        self.delay_spin = QSpinBox()
        self.delay_spin.setObjectName("DelaySpinBox")
        self.delay_spin.setMinimum(0)
        self.delay_spin.setMaximum(999)
        self.delay_spin.setValue(0)
        self.delay_spin.setFixedWidth(40)
        self.delay_spin.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
        self.delay_spin.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.delay_spin.valueChanged.connect(self.on_delay_changed)
        mode_layout.addWidget(self.delay_label)
        mode_layout.addWidget(self.delay_spin)

        self.count_label = QLabel("Số lần:")
        self.count_spin = QSpinBox()
        self.count_spin.setObjectName("CountSpinBox")
        self.count_spin.setMinimum(1)
        self.count_spin.setMaximum(99)
        self.count_spin.setValue(1)
        self.count_spin.setFixedWidth(40)
        self.count_spin.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
        self.count_spin.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.count_label.setVisible(False)
        self.count_spin.setVisible(False)
        self.count_spin.valueChanged.connect(self.on_count_changed)
        mode_layout.addWidget(self.count_label)
        mode_layout.addWidget(self.count_spin)

        layout.addLayout(mode_layout)

        status_layout = QHBoxLayout()
        status_layout.addWidget(QLabel("Trạng thái:"))
        self.status_label = QLabel("Sẵn sàng")
        self.status_label.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self.status_label.setStyleSheet("color: #008000;")
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        self.timer_label = QLabel("00:00:00")
        self.timer_label.setFont(QFont("JetBrains Mono", 9))
        status_layout.addWidget(self.timer_label)
        layout.addLayout(status_layout)
        log_layout = QVBoxLayout()
        self.log_console = QTextEdit()
        self.log_console.setReadOnly(True)
        self.log_console.setObjectName("SectionConsole")
        self.log_console.setFixedHeight(60)
        log_layout.addWidget(self.log_console)
        layout.addLayout(log_layout)
        controls_layout = QHBoxLayout()
        self.run_btn = QPushButton("Chạy")
        self.run_btn.setObjectName("RunButton")
        self.run_btn.clicked.connect(self.run_notebook)
        controls_layout.addWidget(self.run_btn)
        self.stop_btn = QPushButton("Dừng")
        self.stop_btn.setObjectName("StopButton")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop_notebook)
        controls_layout.addWidget(self.stop_btn)
        self.clear_log_btn = QPushButton("Xóa")
        self.clear_log_btn.setObjectName("ClearLogButton")
        self.clear_log_btn.clicked.connect(self.clear_log)
        controls_layout.addWidget(self.clear_log_btn)
        self.remove_btn = QPushButton("Đóng")
        self.remove_btn.setObjectName("RemoveButton")
        self.remove_btn.clicked.connect(self.remove_notebook)
        controls_layout.addWidget(self.remove_btn)
        layout.addLayout(controls_layout)
        layout.addStretch()

    def on_mode_changed(self, text):
        is_count_mode = text == "Lặp lại hữu hạn"
        self.execution_mode = "count" if is_count_mode else "continuous"
        self.count_label.setVisible(is_count_mode)
        self.count_spin.setVisible(is_count_mode)
        self.delay_label.setVisible(not is_count_mode)
        self.delay_spin.setVisible(not is_count_mode)

    def on_count_changed(self, value):
        self.execution_count = value

    def on_delay_changed(self, value):
        self.execution_delay = value

    def run_notebook(self):
        self.log_console.clear()
        self.iteration_logs.clear()
        self.consecutive_error_count = 0

        if self.execution_mode == "continuous":
            log_text = "Bắt đầu: Vô hạn."
        else:
            log_text = f"Bắt đầu: {self.execution_count} lần."
        self.log_message_to_section(log_text)

        self.set_status("running")
        self.run_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.mode_combo.setEnabled(False)
        self.count_spin.setEnabled(False)
        self.delay_spin.setEnabled(False)
        self.run_requested.emit(self)

    def stop_notebook(self):
        if self.current_status == "running":
            self.set_status("stopping")
            self.stop_btn.setEnabled(False)
            QApplication.processEvents()
            self.stop_requested.emit(self.path)

    def remove_notebook(self):
        if self.current_status == "running":
            self.stop_notebook()
        self.remove_requested.emit(self.path)

    def clear_log(self):
        self.log_console.clear()

    def on_execution_finished(self):
        if self.current_status not in ["running", "stopping", "error"]:
            return

        self.stop_total_elapsed_timer()
        final_status_was_success = False

        if self.current_status == "stopping":
            self.set_status("stopped")
            self.log_message_to_section("Đã dừng bắt buộc.")
        elif self.current_status == "error":
            pass
        elif self.execution_mode == "count" and self.consecutive_error_count > 0:
            self.set_status("error")
            self.log_message_to_section("Có lỗi xảy ra.")
        else:
            self.set_status("success")
            final_status_was_success = True
            self.log_message_to_section("Hoàn thành.")

        self.run_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.mode_combo.setEnabled(True)
        self.count_spin.setEnabled(True)
        self.delay_spin.setEnabled(True)

        self.execution_truly_finished.emit(self.path, final_status_was_success)

    def set_status(self, status, message=None):
        self.current_status = status
        status_map = {
            "ready": ("Sẵn sàng", "#008000"),
            "running": ("Đang chạy...", "#0056b3"),
            "success": ("Thành công", "#008000"),
            "error": ("Lỗi", "#FF0000"),
            "stopping": ("Đang dừng...", "#fd7e14"),
            "stopped": ("Đã dừng", "#6c757d"),
        }
        if status in status_map:
            text, color = status_map[status]
            final_text = f"{text}: {message}" if message else text
            self.status_label.setText(final_text)
            self.status_label.setStyleSheet(f"color: {color}; font-weight: bold;")

    def start_total_elapsed_timer(self):
        self.start_time = time.time()
        self.total_elapsed_timer.start(10)

    def stop_total_elapsed_timer(self):
        self.total_elapsed_timer.stop()

    def update_total_elapsed_timer(self):
        if self.start_time:
            elapsed = time.time() - self.start_time
            total_ms = int(elapsed * 1000)
            minutes = total_ms // 60000
            seconds = (total_ms % 60000) // 1000
            hundredths = (total_ms % 1000) // 10
            self.timer_label.setText(f"{minutes:02d}:{seconds:02d}:{hundredths:02d}")

    def log_message_to_section(self, message):
        timestamp = time.strftime("%H:%M:%S")
        self.log_console.append(f"[{timestamp}] {message}")
        self._scroll_log_to_bottom()

    def _scroll_log_to_bottom(self):
        scrollbar = self.log_console.verticalScrollBar()
        if scrollbar:
            scrollbar.setValue(scrollbar.maximum())

    def _format_duration(self, seconds):
        if seconds < 1:
            return f"{seconds * 1000:.0f}ms"
        if seconds < 60:
            return f"{seconds:.1f}s"
        m, s = divmod(seconds, 60)
        return f"{int(m)}m {int(s)}s"

    def handle_log_message(self, msg_type, content):
        if self.current_status not in ["running", "stopping"]:
            return

        if msg_type == "RESET_TIMER":
            self.start_total_elapsed_timer()

        elif msg_type == "SECTION_LOG":
            self.log_message_to_section(content)

        elif msg_type == "ITERATION_START":
            iteration = content["iteration"]
            total = content["total"]
            log_line = f"Lần {iteration}"
            if total:
                log_line += f"/{total}"
            log_line += ":"
            self.log_message_to_section(log_line)
            cursor = self.log_console.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.StartOfLine, QTextCursor.MoveMode.KeepAnchor)
            self.iteration_logs[iteration] = cursor

        elif msg_type == "ITERATION_END":
            iteration = content["iteration"]
            cursor = self.iteration_logs.get(iteration)

            if content["success"]:
                self.consecutive_error_count = 0
                duration_str = self._format_duration(content["duration"])
                if cursor:
                    cursor.movePosition(QTextCursor.MoveOperation.EndOfLine)
                    cursor.insertText(f" {duration_str}")
            else:
                self.consecutive_error_count += 1
                error_log_text = ""
                if self.execution_mode == "count":
                    error_log_text = " [LỖI]"
                else:
                    error_log_text = f" [LỖI {self.consecutive_error_count}/{self.MAX_CONSECUTIVE_ERRORS}]"

                if cursor:
                    cursor.movePosition(QTextCursor.MoveOperation.EndOfLine)
                    cursor.insertText(f"{error_log_text}")

                if self.execution_mode == "continuous" and self.consecutive_error_count >= self.MAX_CONSECUTIVE_ERRORS:
                    self.set_status("error")
                    self.log_message_to_section(f"Dừng do lỗi {self.consecutive_error_count} lần.")
                    self.stop_requested.emit(self.path)

        elif msg_type == "EXECUTION_FINISHED":
            self.on_execution_finished()


class SectionWidget(QWidget):
    notebooks_dropped = pyqtSignal(object, list)
    notebook_remove_requested = pyqtSignal(object, list)
    section_close_requested = pyqtSignal(object)

    def __init__(self, section_name, section_id, parent_runner=None):
        super().__init__()
        self.section_name, self.section_id, self.parent_runner = section_name, section_id, parent_runner
        self.notebook_cards, self.running_processes, self.schedules = {}, {}, []
        self.schedule_counter = 0

        self.is_sequence_running = False
        self.sequential_queue = []

        self.schedule_timer = QTimer(self)
        self.schedule_timer.timeout.connect(self.check_scheduled_actions)
        self.schedule_timer.start(1000)

        self.queue_checker_timer = QTimer(self)
        self.queue_checker_timer.timeout.connect(self.check_all_queues)
        self.queue_checker_timer.start(100)

        self.setMinimumWidth(config.SECTION_MIN_WIDTH)
        self.setAcceptDrops(True)
        self.setup_ui()

    def dragEnterEvent(self, a0: QDragEnterEvent | None) -> None:
        if a0:
            mime_data = a0.mimeData()
            if mime_data and mime_data.hasText():
                a0.acceptProposedAction()
            else:
                a0.ignore()
        elif a0:
            a0.ignore()

    def dropEvent(self, a0: QDropEvent | None) -> None:
        if a0:
            mime_data = a0.mimeData()
            if mime_data and mime_data.hasText():
                self.notebooks_dropped.emit(self, mime_data.text().split("\n"))
                a0.acceptProposedAction()
            else:
                a0.ignore()
        elif a0:
            a0.ignore()

    def check_all_queues(self):
        if not self.running_processes:
            return

        for path, proc_info in list(self.running_processes.items()):
            queue = proc_info.get("queue")
            card = proc_info.get("card")
            if not queue or not card:
                continue

            while not queue.empty():
                try:
                    message = queue.get_nowait()
                    if isinstance(message, tuple) and len(message) == 2:
                        msg_type, content = message

                        if msg_type in ["NOTEBOOK_PRINT", "EXECUTION_ERROR"]:
                            self.log_to_cmd(path, msg_type, content)
                        else:
                            card.handle_log_message(msg_type, content)
                except Exception:
                    pass

    def log_to_cmd(self, notebook_path, msg_type, content):
        if not self.parent_runner:
            return

        nb_name = os.path.basename(notebook_path)

        if msg_type == "NOTEBOOK_PRINT":
            title = config.LOG_TITLE_NOTEBOOK_PRINT.format(nb_name=nb_name, section_name=self.section_name)
            formatted_log = functions.format_output_for_cmd(title, str(content))
            self.parent_runner.log_message_to_cmd(formatted_log, is_block=True)

        elif msg_type == "EXECUTION_ERROR":
            title = config.LOG_TITLE_NOTEBOOK_ERROR.format(nb_name=nb_name, section_name=self.section_name)
            formatted_log = functions.format_output_for_cmd(title, content.get("details", ""))
            self.parent_runner.log_message_to_cmd(formatted_log, is_block=True)

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(10)
        notebooks_group = QGroupBox(f"📋 {self.section_name}")
        notebooks_group_layout = QVBoxLayout(notebooks_group)
        notebooks_group_layout.setContentsMargins(5, 10, 5, 5)
        notebooks_group_layout.setSpacing(8)
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setObjectName("SectionScrollArea")
        self.cards_widget = QWidget()
        self.cards_widget.setObjectName("CardsContainer")
        self.cards_layout = QVBoxLayout(self.cards_widget)
        self.cards_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.cards_layout.setSpacing(10)
        self.scroll_area.setWidget(self.cards_widget)
        notebooks_group_layout.addWidget(self.scroll_area)
        main_layout.addWidget(notebooks_group, 1)
        schedule_group = QGroupBox("⏰ Tác vụ hẹn giờ")
        schedule_main_layout = QVBoxLayout(schedule_group)
        schedule_main_layout.setContentsMargins(5, 10, 5, 5)
        schedule_main_layout.setSpacing(10)
        add_schedule_layout = QHBoxLayout()
        self.action_combo = QComboBox()
        self.action_combo.addItems(["Chạy Đồng Thời", "Chạy Lần Lượt", "Dừng Tất Cả"])
        self.action_combo.setFont(QFont("Segoe UI", 9))
        add_schedule_layout.addWidget(self.action_combo, 1)
        add_schedule_layout.addSpacing(10)

        # --- MODIFIED: Tách giờ và phút ---
        time_layout = QHBoxLayout()
        time_layout.setSpacing(2)

        self.schedule_hour_spin = QSpinBox()
        self.schedule_hour_spin.setRange(0, 23)
        self.schedule_hour_spin.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
        self.schedule_hour_spin.setFixedWidth(40)
        self.schedule_hour_spin.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.schedule_hour_spin.setObjectName("HourSpinBox")

        self.schedule_minute_spin = QSpinBox()
        self.schedule_minute_spin.setRange(0, 59)
        self.schedule_minute_spin.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
        self.schedule_minute_spin.setFixedWidth(40)
        self.schedule_minute_spin.setSingleStep(1)
        self.schedule_minute_spin.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.schedule_minute_spin.setObjectName("MinuteSpinBox")

        current_time = QTime.currentTime()
        self.schedule_hour_spin.setValue(current_time.hour())
        self.schedule_minute_spin.setValue(current_time.minute())

        time_layout.addWidget(self.schedule_hour_spin)
        colon_label = QLabel(":")
        colon_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        colon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        time_layout.addWidget(colon_label)
        
        time_layout.addWidget(self.schedule_minute_spin)

        add_schedule_layout.addLayout(time_layout)
        # --- END MODIFIED ---

        self.add_schedule_btn = QPushButton("Thêm")
        self.add_schedule_btn.setObjectName("SetScheduleButton")
        self.add_schedule_btn.clicked.connect(self.add_schedule)
        add_schedule_layout.addWidget(self.add_schedule_btn)
        schedule_main_layout.addLayout(add_schedule_layout)
        scroll_schedules = QScrollArea()
        scroll_schedules.setWidgetResizable(True)
        scroll_schedules.setStyleSheet("QScrollArea{border:1px solid #dee2e6;border-radius:4px;}")
        scroll_schedules.setFixedHeight(60)
        self.schedule_list_widget = QWidget()
        self.schedule_list_widget.setObjectName("ScheduleListContainer")
        self.schedule_list_widget.setStyleSheet("QWidget#ScheduleListContainer{background-color:white;}")
        self.schedule_list_layout = QVBoxLayout(self.schedule_list_widget)
        self.schedule_list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.schedule_list_layout.setContentsMargins(5, 5, 5, 5)
        self.schedule_list_layout.setSpacing(5)
        scroll_schedules.setWidget(self.schedule_list_widget)
        schedule_main_layout.addWidget(scroll_schedules)
        main_layout.addWidget(schedule_group, 0)

        controls_group = QGroupBox("⚙️ Điều Khiển Section")
        controls_group.setObjectName("SectionControlsGroup")
        controls_layout = QVBoxLayout(controls_group)
        controls_layout.setContentsMargins(5, 10, 5, 5)
        controls_layout.setSpacing(8)

        row1_layout = QHBoxLayout()
        self.run_all_btn = QPushButton("Chạy Đồng Thời")
        self.run_all_btn.setObjectName("SectionRunButton")
        self.run_all_btn.clicked.connect(self.run_all_simultaneously)
        row1_layout.addWidget(self.run_all_btn)
        self.run_sequential_btn = QPushButton("Chạy Lần Lượt")
        self.run_sequential_btn.setObjectName("SectionRunButton")
        self.run_sequential_btn.clicked.connect(self.run_all_sequential_wrapper)
        row1_layout.addWidget(self.run_sequential_btn)
        controls_layout.addLayout(row1_layout)

        row2_layout = QHBoxLayout()
        self.stop_all_btn = QPushButton("Dừng Tất Cả")
        self.stop_all_btn.setObjectName("SectionStopButton")
        self.stop_all_btn.clicked.connect(self.stop_all_notebooks)
        row2_layout.addWidget(self.stop_all_btn)
        self.clear_all_logs_btn = QPushButton("Xoá Tất Cả")
        self.clear_all_logs_btn.setObjectName("ClearAllLogsButton")
        self.clear_all_logs_btn.clicked.connect(self._clear_all_logs)
        row2_layout.addWidget(self.clear_all_logs_btn)
        controls_layout.addLayout(row2_layout)

        row3_layout = QHBoxLayout()
        self.close_section_btn = QPushButton("Đóng Section")
        self.close_section_btn.setObjectName("SectionRemoveButton")
        self.close_section_btn.clicked.connect(self.close_section)
        row3_layout.addWidget(self.close_section_btn)
        self.close_all_notebooks_btn = QPushButton("Đóng Tất Cả")
        self.close_all_notebooks_btn.setObjectName("CloseAllNotebooksButton")
        self.close_all_notebooks_btn.clicked.connect(self._close_all_notebooks)
        row3_layout.addWidget(self.close_all_notebooks_btn)
        controls_layout.addLayout(row3_layout)

        main_layout.addWidget(controls_group, 0)
        self.update_schedule_display()

    def _clear_all_logs(self):
        for card in self.notebook_cards.values():
            card.clear_log()

    def _close_all_notebooks(self):
        all_paths = list(self.notebook_cards.keys())
        if all_paths:
            self.notebook_remove_requested.emit(self, all_paths)

    def add_schedule(self):
        self.schedule_counter += 1
        schedule_id = self.schedule_counter
        action_text = self.action_combo.currentText()

        # --- MODIFIED: Lấy giờ và phút từ SpinBox ---
        hour = self.schedule_hour_spin.value()
        minute = self.schedule_minute_spin.value()
        schedule_time = QTime(hour, minute)
        # --- END MODIFIED ---

        action_map = {
            "Chạy Đồng Thời": "run_all_simultaneously",
            "Chạy Lần Lượt": "run_all_sequential_wrapper",
            "Dừng Tất Cả": "stop_all_notebooks",
        }
        action_key = action_map.get(action_text)
        self.schedules.append({"id": schedule_id, "action_key": action_key, "action_text": action_text, "time": schedule_time})
        self.update_schedule_display()
        if self.parent_runner:
            self.parent_runner.log_message_to_cmd(
                f"[{self.section_name}] Đã thêm lịch hẹn: '{action_text}' lúc {schedule_time.toString('HH:mm')}"
            )

    def remove_schedule(self, schedule_id):
        self.schedules = [s for s in self.schedules if s["id"] != schedule_id]
        self.update_schedule_display()

    def update_schedule_display(self):
        while self.schedule_list_layout.count():
            item = self.schedule_list_layout.takeAt(0)
            if item is not None:
                widget = item.widget()
                if widget:
                    widget.deleteLater()

        if not self.schedules:
            placeholder = QLabel("Chưa có lịch hẹn nào.")
            placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            placeholder.setStyleSheet("color:#888;")
            self.schedule_list_layout.addWidget(placeholder)
            return

        # --- MODIFIED: Sắp xếp lịch hẹn theo thời gian ---
        self.schedules.sort(key=lambda s: s["time"])
        # --- END MODIFIED ---

        for schedule in self.schedules:
            item_frame = QFrame()
            item_layout = QHBoxLayout(item_frame)
            item_layout.setContentsMargins(8, 2, 8, 2)
            label = QLabel(f"<b>{schedule['action_text']}</b> lúc <b>{schedule['time'].toString('HH:mm')}</b>")
            item_layout.addWidget(label)
            item_layout.addStretch()
            remove_label = ClickableLink("Xóa")
            remove_label.clicked.connect(partial(self.remove_schedule, schedule["id"]))
            item_layout.addWidget(remove_label)
            self.schedule_list_layout.addWidget(item_frame)

    def check_scheduled_actions(self):
        now_str = QTime.currentTime().toString("HH:mm")
        executed_ids = []
        for schedule in self.schedules:
            if schedule["time"].toString("HH:mm") == now_str:
                if hasattr(self, schedule["action_key"]):
                    getattr(self, schedule["action_key"])()
                if self.parent_runner:
                    self.parent_runner.log_message_to_cmd(f"[{self.section_name}] Thực thi hẹn giờ: {schedule['action_text']}")
                executed_ids.append(schedule["id"])
        if executed_ids:
            self.schedules = [s for s in self.schedules if s["id"] not in executed_ids]
            self.update_schedule_display()

    def add_notebook_card(self, path, description):
        if path in self.notebook_cards:
            return
        card = SectionNotebookCard(path, description)
        card.run_requested.connect(self.on_card_run_requested)
        card.stop_requested.connect(self.on_card_stop_requested)
        card.remove_requested.connect(self.on_card_remove_requested)
        card.execution_truly_finished.connect(self._on_sequential_notebook_finished)
        card.execution_truly_finished.connect(self._cleanup_finished_process)
        self.cards_layout.addWidget(card)
        self.notebook_cards[path] = card

    def _cleanup_finished_process(self, path, success):
        """Removes the process from the running list once it's truly finished."""
        if path in self.running_processes:
            del self.running_processes[path]

        if not self.running_processes:
            self.stop_all_btn.setEnabled(True)
            if not self.is_sequence_running:
                self.run_all_btn.setEnabled(True)
                self.run_sequential_btn.setEnabled(True)

    def remove_notebook_card(self, path):
        if path in self.notebook_cards:
            if path in self.running_processes:
                self.on_card_stop_requested(path)
            self.notebook_cards.pop(path).deleteLater()

    def on_card_run_requested(self, card):
        self.run_notebook(card)
        if self.parent_runner:
            nb_name = os.path.basename(card.path)
            mode_text = "Lặp lại hữu hạn" if card.execution_mode == "count" else "Lặp lại vô hạn"
            count_text = f" (Số lần: {card.execution_count})" if mode_text == "Lặp lại hữu hạn" else ""
            self.parent_runner.log_message_to_cmd(
                f"Bắt đầu thực thi '{nb_name}' tại section '{self.section_name}' ở chế độ '{mode_text}'{count_text}."
            )

    def on_card_stop_requested(self, path):
        if self.parent_runner:
            self.parent_runner.log_message_to_cmd(
                f"Đã gửi yêu cầu dừng notebook '{os.path.basename(path)}' tại section '{self.section_name}'."
            )

        if path in self.running_processes:
            proc_info = self.running_processes[path]
            proc_info["stop_event"].set()
            proc_info["process"].join(timeout=2.0)

            if proc_info["process"].is_alive():
                proc_info["process"].terminate()
                if self.parent_runner:
                    self.parent_runner.log_message_to_cmd(f"Buộc dừng: {os.path.basename(path)}")

            card = self.notebook_cards.get(path)
            if card:
                card.on_execution_finished()

    def on_card_remove_requested(self, path):
        self.notebook_remove_requested.emit(self, [path])

    def run_notebook(self, card):
        if self.parent_runner:
            functions.run_notebook_with_individual_logging(
                card.path,
                self.running_processes,
                card,
                card.execution_mode,
                card.execution_count,
                card.execution_delay,
                self.parent_runner.modules_path,
            )

    def run_all_simultaneously(self):
        if not self.notebook_cards:
            return
        if self.parent_runner:
            self.parent_runner.log_message_to_cmd(f"[{self.section_name}] Bắt đầu chạy đồng thời...")
        for card in self.notebook_cards.values():
            if card.path not in self.running_processes:
                card.run_notebook()

    def run_all_sequential_wrapper(self):
        if self.is_sequence_running:
            if self.parent_runner:
                self.parent_runner.log_message_to_cmd(f"[{self.section_name}] Một chuỗi chạy lần lượt đã đang chạy.")
            return
        if not self.notebook_cards:
            if self.parent_runner:
                self.parent_runner.log_message_to_cmd(f"[{self.section_name}] Không có notebook nào để chạy.")
            return

        self.is_sequence_running = True
        self.run_all_btn.setEnabled(False)
        self.run_sequential_btn.setEnabled(False)

        self.sequential_queue.clear()
        for i in range(self.cards_layout.count()):
            item = self.cards_layout.itemAt(i)
            if item is not None:
                widget = item.widget()
                if widget and isinstance(widget, SectionNotebookCard):
                    self.sequential_queue.append(widget.path)

        if self.parent_runner:
            self.parent_runner.log_message_to_cmd(f"[{self.section_name}] Bắt đầu chạy lần lượt...")

        self._run_next_in_sequence()

    def _run_next_in_sequence(self):
        if not self.is_sequence_running:
            return

        if not self.sequential_queue:
            if self.parent_runner:
                self.parent_runner.log_message_to_cmd(f"[{self.section_name}] Đã hoàn thành chạy lần lượt.")
            self._stop_sequential_run()
            return

        next_path = self.sequential_queue.pop(0)
        card = self.notebook_cards.get(next_path)

        if card:
            if card.path in self.running_processes:
                self._run_next_in_sequence()
                return

            card.run_notebook()

            if card.execution_mode == "continuous":
                if self.parent_runner:
                    nb_name = os.path.basename(card.path)
                    self.parent_runner.log_message_to_cmd(
                        f"[{self.section_name}] Tuần tự: Đã bắt đầu '{nb_name}' (liên tục). Sẽ chạy notebook tiếp theo sau 60 giây."
                    )
                QTimer.singleShot(60000, self._run_next_in_sequence)
        else:
            self._run_next_in_sequence()

    def _on_sequential_notebook_finished(self, path, success):
        if not self.is_sequence_running:
            return

        card = self.notebook_cards.get(path)
        if card and card.execution_mode == "continuous":
            return

        nb_name = os.path.basename(path)
        status_text = "thành công" if success else "thất bại"
        if self.parent_runner:
            self.parent_runner.log_message_to_cmd(f"[{self.section_name}] Tuần tự: '{nb_name}' hoàn thành {status_text}.")

        if success:
            self._run_next_in_sequence()
        else:
            if self.parent_runner:
                self.parent_runner.log_message_to_cmd(f"[{self.section_name}] Dừng chạy lần lượt do có lỗi.")
            self._stop_sequential_run()

    def _stop_sequential_run(self):
        self.is_sequence_running = False
        self.sequential_queue.clear()
        self.run_all_btn.setEnabled(True)
        self.run_sequential_btn.setEnabled(True)

    def stop_all_notebooks(self):
        was_sequence_running = self.is_sequence_running
        if was_sequence_running:
            if self.parent_runner:
                self.parent_runner.log_message_to_cmd(f"[{self.section_name}] Đã dừng chuỗi chạy lần lượt.")
            self._stop_sequential_run()

        running_cards = [card for card in self.notebook_cards.values() if card.current_status == "running"]
        if not running_cards:
            return

        self.stop_all_btn.setEnabled(False)
        self.run_all_btn.setEnabled(False)
        self.run_sequential_btn.setEnabled(False)
        QApplication.processEvents()

        if self.parent_runner and not was_sequence_running:
            self.parent_runner.log_message_to_cmd(f"[{self.section_name}] Dừng tất cả notebook đang chạy...")

        for card in running_cards:
            card.stop_notebook()

    def close_section(self):
        running_count = len(self.running_processes)

        if running_count > 0:
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("Xác nhận đóng Section")
            msg_box.setText(f"Bạn có chắc muốn đóng '{self.section_name}' không?\nCó {running_count} notebook(s) đang chạy sẽ bị dừng.")
            msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            msg_box.setDefaultButton(QMessageBox.StandardButton.No)
            msg_box.setIcon(QMessageBox.Icon.Question)

            if self.parent_runner and hasattr(self.parent_runner, "styleSheet") and self.parent_runner.styleSheet():
                msg_box.setStyleSheet(self.parent_runner.styleSheet())

            reply = msg_box.exec()
            if reply != QMessageBox.StandardButton.Yes:
                return

        self.stop_all_notebooks()
        self.section_close_requested.emit(self)

    def cleanup(self):
        if hasattr(self, "schedule_timer"):
            self.schedule_timer.stop()
        if hasattr(self, "queue_checker_timer"):
            self.queue_checker_timer.stop()
        self.stop_all_notebooks()
