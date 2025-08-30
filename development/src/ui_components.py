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
    QWheelEvent,
    QIcon,
)
import config
import functions


class CustomSpinBox(QSpinBox):
    """
    QSpinBox tùy chỉnh với hai cải tiến:
    1. Ngăn chặn việc chọn văn bản (bôi đen) khi lăn chuột.
    2. Tùy chọn hiển thị số với số 0 ở đầu (ví dụ: 05, 08).
    """

    def __init__(self, padded_display=False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._padded_display = padded_display

    def textFromValue(self, value):
        """Định dạng văn bản hiển thị."""
        if self._padded_display:
            return f"{value:02d}"
        return super().textFromValue(value)

    def wheelEvent(self, event: QWheelEvent | None) -> None:
        """Xử lý sự kiện lăn chuột để ngăn chọn văn bản."""
        if event and self.lineEdit():
            self.lineEdit().deselect()
        super().wheelEvent(event)
        if self.lineEdit():
            self.lineEdit().deselect()


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
            "count",
            1,
            0,
            "ready",
            None,
        )
        self.consecutive_error_count = 0
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
        self.mode_combo.addItems(["Lặp lại hữu hạn", "Lặp lại vô hạn"])
        self.mode_combo.currentTextChanged.connect(self.on_mode_changed)
        mode_layout.addWidget(self.mode_combo, 1)

        self.delay_label = QLabel("Nghỉ (s):")
        self.delay_spin = CustomSpinBox()
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
        self.count_spin = CustomSpinBox()
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
        self.run_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.run_btn.clicked.connect(self.run_notebook)
        controls_layout.addWidget(self.run_btn)
        self.stop_btn = QPushButton("Dừng")
        self.stop_btn.setObjectName("StopButton")
        self.stop_btn.setEnabled(False)
        self.stop_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.stop_btn.clicked.connect(self.stop_notebook)
        controls_layout.addWidget(self.stop_btn)
        self.clear_log_btn = QPushButton("Xóa")
        self.clear_log_btn.setObjectName("ClearLogButton")
        self.clear_log_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.clear_log_btn.clicked.connect(self.clear_log)
        controls_layout.addWidget(self.clear_log_btn)
        self.remove_btn = QPushButton("Đóng")
        self.remove_btn.setObjectName("RemoveButton")
        self.remove_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.remove_btn.clicked.connect(self.remove_notebook)
        controls_layout.addWidget(self.remove_btn)
        layout.addLayout(controls_layout)
        layout.addStretch()

        # Thiết lập trạng thái ban đầu cho chế độ "Lặp lại hữu hạn"
        self.count_label.setVisible(True)
        self.count_spin.setVisible(True)
        self.delay_label.setVisible(False)
        self.delay_spin.setVisible(False)

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

    def on_execution_finished(self, was_stopped_by_error):
        if self.current_status not in ["running", "stopping"]:
            return

        self.stop_total_elapsed_timer()
        final_status_was_success = False

        if self.current_status == "stopping":
            self.set_status("stopped")
            self.log_message_to_section("Đã dừng bắt buộc.")
        elif was_stopped_by_error:
            self.set_status("error")
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
            log_line = f"Lần {iteration}:"
            self.log_message_to_section(log_line)
            cursor = self.log_console.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.StartOfLine, QTextCursor.MoveMode.KeepAnchor)
            self.iteration_logs[iteration] = cursor
        elif msg_type == "ITERATION_END":
            iteration = content["iteration"]
            cursor = self.iteration_logs.get(iteration)
            duration_str = self._format_duration(content["duration"])

            if content["success"]:
                self.consecutive_error_count = 0
                if cursor:
                    cursor.movePosition(QTextCursor.MoveOperation.EndOfLine)
                    cursor.insertText(f" {duration_str}")
            else:
                self.consecutive_error_count += 1
                if cursor:
                    if self.execution_mode == "continuous":
                        error_message = f" {duration_str} [LỖI {self.consecutive_error_count}/{config.MAX_CONSECUTIVE_ERRORS_CONTINOUS}]"
                    else:
                        error_message = f" {duration_str} [LỖI {self.consecutive_error_count}/{config.MAX_CONSECUTIVE_ERRORS_FINITE}]"

                    cursor.movePosition(QTextCursor.MoveOperation.EndOfLine)
                    cursor.insertText(error_message)

        elif msg_type == "EXECUTION_FINISHED":
            self.on_execution_finished(False)


# MODIFIED: Redesigned for two-line display
class ScheduledTaskDisplayWidget(QFrame):
    remove_requested = pyqtSignal(int)

    def __init__(self, task_id, section_name, action_text, time_text, parent=None):
        super().__init__(parent)
        self.task_id = task_id
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setObjectName("ScheduledTaskDisplayCard")

        # Main horizontal layout
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(8, 4, 4, 4)  # Reduce right margin
        main_layout.setSpacing(4)  # Reduce spacing between elements

        # Vertical layout for the two lines of text
        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)

        # Line 1: Section Name (bold)
        section_label = QLabel(f"<b>{section_name}</b>")
        section_label.setWordWrap(True)
        text_layout.addWidget(section_label)

        # Line 2: Action and Time (bold parts)
        details_label = QLabel(f"<b>{action_text}</b> lúc <b>{time_text}</b>")
        details_label.setWordWrap(True)
        text_layout.addWidget(details_label)

        main_layout.addLayout(text_layout, 1)  # Give text area flexible space

        # Remove button on the right with fixed width, aligned to bottom
        remove_label = ClickableLink("Xóa")
        remove_label.setObjectName("RemoveScheduleLink")
        remove_label.setFixedWidth(30)  # Reduce width to fit text better
        remove_label.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Center text in button
        remove_label.clicked.connect(lambda: self.remove_requested.emit(self.task_id))
        main_layout.addWidget(remove_label, 0, Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignRight)


class ScheduleManagerWidget(QWidget):
    section_close_requested = pyqtSignal()

    def __init__(self, parent_runner=None):
        super().__init__()
        self.parent_runner = parent_runner
        self.tasks_data = {}
        self.task_counter = 0
        self.setMinimumWidth(config.SCHEDULE_MANAGER_WIDTH)
        self.setObjectName("ScheduleManagerWidget")
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(10)

        main_group = QGroupBox("🕒 Tác Vụ Hẹn Giờ")
        main_group_layout = QVBoxLayout(main_group)
        main_group_layout.setContentsMargins(5, 10, 5, 5)
        main_group_layout.setSpacing(8)

        creator_layout = QHBoxLayout()
        creator_layout.setContentsMargins(0, 0, 0, 5)

        self.section_combo = QComboBox()
        self.section_combo.setObjectName("TaskSectionCombo")
        creator_layout.addWidget(self.section_combo, 1)

        self.action_combo = QComboBox()
        self.action_combo.addItems(["Chạy Đồng Thời", "Chạy Lần Lượt", "Dừng Tất Cả"])
        self.action_combo.setFont(QFont("Segoe UI", 9))
        creator_layout.addWidget(self.action_combo, 1)

        self.hour_spin = CustomSpinBox(padded_display=True)
        self.hour_spin.setRange(0, 23)
        self.hour_spin.setValue(QTime.currentTime().hour())
        self.hour_spin.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
        self.hour_spin.setObjectName("HourSpinBox")
        self.hour_spin.setFixedWidth(35)
        self.hour_spin.setStyleSheet("QSpinBox { padding: 2px 0px; text-align: center; }")

        # Tạo layout riêng cho cụm giờ:phút với spacing nhỏ
        time_layout = QHBoxLayout()
        time_layout.setSpacing(2)  # Giảm khoảng cách xuống 2px
        time_layout.addWidget(self.hour_spin)
        time_layout.addWidget(QLabel(":"))

        self.minute_spin = CustomSpinBox(padded_display=True)
        self.minute_spin.setRange(0, 59)
        self.minute_spin.setValue(QTime.currentTime().minute())
        self.minute_spin.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
        self.minute_spin.setObjectName("MinuteSpinBox")
        self.minute_spin.setFixedWidth(35)
        self.minute_spin.setStyleSheet("QSpinBox { padding: 2px 0px; text-align: center; }")

        time_layout.addWidget(self.minute_spin)
        creator_layout.addLayout(time_layout)

        main_group_layout.addLayout(creator_layout)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setObjectName("ScheduleListScrollArea")
        self.tasks_widget = QWidget()
        self.tasks_widget.setObjectName("TasksContainer")
        self.tasks_layout = QVBoxLayout(self.tasks_widget)
        self.tasks_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.tasks_layout.setSpacing(5)
        self.scroll_area.setWidget(self.tasks_widget)
        main_group_layout.addWidget(self.scroll_area, 1)
        main_layout.addWidget(main_group, 1)

        controls_group = QGroupBox("⚙️ Điều Khiển Tác Vụ")
        controls_group.setObjectName("SectionControlsGroup")
        controls_layout = QVBoxLayout(controls_group)
        controls_layout.setContentsMargins(5, 10, 5, 5)
        controls_layout.setSpacing(8)

        add_task_btn = QPushButton("Thêm tác vụ")
        add_task_btn.setObjectName("SectionRunButton")
        add_task_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_task_btn.clicked.connect(self.add_task)
        controls_layout.addWidget(add_task_btn)

        delete_all_btn = QPushButton("Xóa Tất Cả")
        delete_all_btn.setObjectName("ClearAllLogsButton")
        delete_all_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        delete_all_btn.clicked.connect(self.delete_all_tasks)
        controls_layout.addWidget(delete_all_btn)

        close_btn = QPushButton("Đóng Section")
        close_btn.setObjectName("CloseSectionButton")
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(self.section_close_requested.emit)
        controls_layout.addWidget(close_btn)

        main_layout.addWidget(controls_group, 0)
        self.update_task_display()

    def add_task(self):
        section_id = self.section_combo.currentData()
        section_name = self.section_combo.currentText()
        if not section_id:
            QMessageBox.warning(self, "Lỗi", "Vui lòng chọn một Section hợp lệ.")
            return

        action_map = {
            "Chạy Đồng Thời": "run_all_simultaneously",
            "Chạy Lần Lượt": "run_all_sequential_wrapper",
            "Dừng Tất Cả": "stop_all_notebooks",
        }
        action_text = self.action_combo.currentText()
        time_val = QTime(self.hour_spin.value(), self.minute_spin.value())

        self.task_counter += 1
        task_id = self.task_counter

        self.tasks_data[task_id] = {
            "section_id": section_id,
            "section_name": section_name,
            "action_key": action_map.get(action_text),
            "action_text": action_text,
            "time": time_val,
        }

        self.update_task_display()
        if self.parent_runner:
            self.parent_runner.log_message_to_cmd(f"Đã thêm tác vụ: {action_text} cho {section_name} lúc {time_val.toString('HH:mm')}.")

    def remove_task(self, task_id):
        if task_id in self.tasks_data:
            task_info = self.tasks_data[task_id]
            log_message = (
                f"Đã xóa tác vụ: {task_info['action_text']} cho {task_info['section_name']} lúc {task_info['time'].toString('HH:mm')}."
            )
            del self.tasks_data[task_id]
            self.update_task_display()
            if self.parent_runner:
                self.parent_runner.log_message_to_cmd(log_message)

    def delete_all_tasks(self):
        if not self.tasks_data:
            return
        reply = QMessageBox.question(
            self,
            "Xác nhận xóa",
            "Bạn có chắc muốn xóa tất cả các tác vụ đã tạo?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.tasks_data.clear()
            self.update_task_display()
            if self.parent_runner:
                self.parent_runner.log_message_to_cmd("Đã xóa tất cả các tác vụ định kỳ.")

    def update_task_display(self):
        while self.tasks_layout.count():
            item = self.tasks_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        if not self.tasks_data:
            placeholder = QLabel("Chưa có lịch hẹn nào.")
            placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            placeholder.setStyleSheet("color: #888;")
            self.tasks_layout.addWidget(placeholder)
        else:
            # Sắp xếp theo section trước (section_name), rồi đến thời gian sau
            sorted_tasks = sorted(self.tasks_data.items(), key=lambda item: (item[1]["section_name"], item[1]["time"]))
            for task_id, task_info in sorted_tasks:
                # MODIFIED: Create new two-line widget
                task_widget = ScheduledTaskDisplayWidget(
                    task_id, task_info["section_name"], task_info["action_text"], task_info["time"].toString("HH:mm")
                )
                task_widget.remove_requested.connect(self.remove_task)
                self.tasks_layout.addWidget(task_widget)

    def update_section_list(self, sections_dict):
        current_selection = self.section_combo.currentData()
        self.section_combo.clear()
        if not sections_dict:
            self.section_combo.addItem("Chưa có section", None)
            self.section_combo.setEnabled(False)
        else:
            for section_id, section_widget in sections_dict.items():
                self.section_combo.addItem(section_widget.section_name, section_id)
            self.section_combo.setEnabled(True)
            index = self.section_combo.findData(current_selection)
            if index != -1:
                self.section_combo.setCurrentIndex(index)

    def get_tasks(self):
        return self.tasks_data.copy()

    def mark_task_as_run(self, task_id, time_str):
        if task_id in self.tasks_data:
            self.tasks_data[task_id]["last_run_time"] = time_str

    def reset_task_run_marker(self, task_id):
        if task_id in self.tasks_data and "last_run_time" in self.tasks_data[task_id]:
            del self.tasks_data[task_id]["last_run_time"]


class SectionWidget(QWidget):
    notebooks_dropped = pyqtSignal(object, list)
    notebook_remove_requested = pyqtSignal(object, list)
    section_close_requested = pyqtSignal(object)

    def __init__(self, section_name, section_id, parent_runner=None):
        super().__init__()
        self.section_name, self.section_id, self.parent_runner = section_name, section_id, parent_runner
        self.notebook_cards, self.running_processes = {}, {}

        self.is_sequence_running = False
        self.sequential_queue = []

        self.queue_checker_timer = QTimer(self)
        self.queue_checker_timer.timeout.connect(self.check_all_queues)
        self.queue_checker_timer.start(100)

        self.setMinimumWidth(config.RUN_SECTION_WIDTH)
        self.setAcceptDrops(True)
        self.setup_ui()

    def dragEnterEvent(self, a0: QDragEnterEvent | None) -> None:
        if a0 and a0.mimeData().hasText():
            a0.acceptProposedAction()
        elif a0:
            a0.ignore()

    def dropEvent(self, a0: QDropEvent | None) -> None:
        if a0 and a0.mimeData().hasText():
            self.notebooks_dropped.emit(self, a0.mimeData().text().split("\n"))
            a0.acceptProposedAction()
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

        # Chuyển đổi msg_type sang 'Output' hoặc 'ERROR'
        log_type = "ERROR" if msg_type == "EXECUTION_ERROR" else "Output"

        # Lấy nội dung thực sự từ dict (đối với lỗi)
        log_content = content.get("details", "") if isinstance(content, dict) else str(content)

        # Gọi hàm định dạng mới với đầy đủ thông tin
        formatted_log = functions.format_output_for_cmd(
            log_type=log_type, section_name=self.section_name, nb_name=nb_name, content=log_content
        )

        # Gửi chuỗi đã định dạng tới console chính
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

        controls_group = QGroupBox("⚙️ Điều Khiển Section")
        controls_group.setObjectName("SectionControlsGroup")
        controls_layout = QVBoxLayout(controls_group)
        controls_layout.setContentsMargins(5, 10, 5, 5)
        controls_layout.setSpacing(8)

        row1_layout = QHBoxLayout()
        self.run_all_btn = QPushButton("Chạy Đồng Thời")
        self.run_all_btn.setObjectName("SectionRunButton")
        self.run_all_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.run_all_btn.clicked.connect(self.run_all_simultaneously)
        row1_layout.addWidget(self.run_all_btn)
        self.run_sequential_btn = QPushButton("Chạy Lần Lượt")
        self.run_sequential_btn.setObjectName("SectionRunButton")
        self.run_sequential_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.run_sequential_btn.clicked.connect(self.run_all_sequential_wrapper)
        row1_layout.addWidget(self.run_sequential_btn)
        controls_layout.addLayout(row1_layout)

        row2_layout = QHBoxLayout()
        self.stop_all_btn = QPushButton("Dừng Tất Cả")
        self.stop_all_btn.setObjectName("SectionStopButton")
        self.stop_all_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.stop_all_btn.clicked.connect(self.stop_all_notebooks)
        row2_layout.addWidget(self.stop_all_btn)
        self.clear_all_logs_btn = QPushButton("Xóa Tất Cả")
        self.clear_all_logs_btn.setObjectName("ClearAllLogsButton")
        self.clear_all_logs_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.clear_all_logs_btn.clicked.connect(self._clear_all_logs)
        row2_layout.addWidget(self.clear_all_logs_btn)
        controls_layout.addLayout(row2_layout)

        row3_layout = QHBoxLayout()
        self.close_section_btn = QPushButton("Đóng Section")
        self.close_section_btn.setObjectName("SectionRemoveButton")
        self.close_section_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.close_section_btn.clicked.connect(self.close_section)
        row3_layout.addWidget(self.close_section_btn)
        self.close_all_notebooks_btn = QPushButton("Đóng Tất Cả")
        self.close_all_notebooks_btn.setObjectName("CloseAllNotebooksButton")
        self.close_all_notebooks_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.close_all_notebooks_btn.clicked.connect(self._close_all_notebooks)
        row3_layout.addWidget(self.close_all_notebooks_btn)
        controls_layout.addLayout(row3_layout)

        main_layout.addWidget(controls_group, 0)

    def _clear_all_logs(self):
        for card in self.notebook_cards.values():
            card.clear_log()

    def _close_all_notebooks(self):
        all_paths = list(self.notebook_cards.keys())
        if all_paths:
            self.notebook_remove_requested.emit(self, all_paths)

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
            card = self.notebook_cards.pop(path)
            card.setParent(None)
            card.deleteLater()

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
                card.on_execution_finished(was_stopped_by_error=True)

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
                self.parent_runner.import_path,
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
        if hasattr(self, "queue_checker_timer"):
            self.queue_checker_timer.stop()
        self.stop_all_notebooks()
