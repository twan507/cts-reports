# development/src/styles.py


def get_stylesheet():
    """Trả về stylesheet CSS đã được tổ chức lại cho ứng dụng"""
    return """
        /* === CỬA SỔ CHÍNH & WIDGET NỀN === */
        QMainWindow, #MainWidget {
            background-color: #f8f9fa;
            color: #2c3e50;
            font-family: "Segoe UI", Arial, sans-serif;
        }

        /* === GROUP BOXES === */
        QGroupBox {
            font-family: "Segoe UI";
            font-size: 11pt;
            font-weight: bold;
            border: 2px solid #e9ecef;
            border-radius: 12px;
            margin-top: 12px;
            padding: 2px;
            background-color: #ffffff;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 0 2px;
            left: 10px;
            color: #495057;
            background-color: #ffffff;
        }
        #LogGroup, #AvailableGroup, #ControlsGroup, #SectionControlsGroup {
            border: 2px solid #dee2e6;
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #ffffff, stop:1 #f8f9fa);
        }

        /* === KHU VỰC CUỘN & VĂN BẢN === */
        QScrollArea { border: none; background-color: transparent; }
        #AvailableScrollArea, #SectionScrollArea { 
            border: 1px solid #e9ecef; 
            border-radius: 8px; 
            background-color: #ffffff; 
        }
        #CardsContainer, #ScheduleListContainer { background-color: #ffffff; border-radius: 6px; }        
        #Console, #SectionConsole {
            background-color: #1e1e1e;
            color: #d4d4d4;
            border: 1px solid #495057;
            border-radius: 8px;
            padding: 5px;
            font-family: "JetBrains Mono", "Consolas", monospace;
        }
        
        #SectionConsole {
            background-color: white;
            color: black;
            border: 1px solid #ccc;
            border-radius: 4px;
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 9pt;
        }        
        #SectionConsole QScrollBar:vertical {
            background: transparent;
            width: 4px;
            margin: 0px;
            border: none;
            right: 0px;
        }
        #SectionConsole QScrollBar::handle:vertical {
            background: #d0d0d0;
            border-radius: 2px;
            margin: 0px;
            min-height: 15px;
        }
        #SectionConsole QScrollBar::handle:vertical:hover {
            background: #b0b0b0;
        }
        #SectionConsole QScrollBar::add-line:vertical,
        #SectionConsole QScrollBar::sub-line:vertical {
            height: 0px;
            background: none;
        }
        #SectionConsole QScrollBar::add-page:vertical,
        #SectionConsole QScrollBar::sub-page:vertical {
            background: transparent;
        }
        QTextEdit { 
            background-color: #ffffff; 
            border: 2px solid #dee2e6; 
            border-radius: 8px; 
            color: #2c3e50; 
            padding: 5px; 
        }
        QComboBox {
            background-color: #f0f0f0; border: 1px solid #ccc; border-radius: 4px;
            padding: 3px 5px; color: black;
        }
        QComboBox QAbstractItemView {
            background-color: white; border: 1px solid #ccc;
            selection-background-color: #007bff; color: black;
        }

        /* --- MODIFIED: Thêm style cho QSpinBox --- */
        QSpinBox, #HourSpinBox, #MinuteSpinBox, #DelaySpinBox, #CountSpinBox {
            background-color: #f0f0f0;
            border: 1px solid #ccc;
            border-radius: 4px;
            padding: 3px 2px;
            color: black;
            font-family: "Segoe UI";
            font-size: 9pt;
        }
        QSpinBox:disabled {
            background-color: #e9ecef;
            color: #6c757d;
        }
        /* --- END MODIFIED --- */

        /* === THANH CUỘN === */
        QScrollBar:vertical {
            background-color: #f1f1f1; width: 4px; border-radius: 2px; margin: 0px;
        }
        QScrollBar::handle:vertical {
            background-color: #c1c1c1; border-radius: 2px; min-height: 7px;
        }
        QScrollBar:horizontal {
            background-color: #f1f1f1; height: 4px; border-radius: 2px; margin: 0px;
        }
        QScrollBar::handle:horizontal {
            background-color: #c1c1c1; border-radius: 2px; min-width: 7px;
        }
        QScrollBar::add-line, QScrollBar::sub-line { background: none; height: 0px; width: 0px; }
        QScrollBar::add-page, QScrollBar::sub-page { background: none; }
        
        /* === CARDS === */
        #Card, #SelectedCard { 
            border: 2px solid #e9ecef; border-radius: 10px; 
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #ffffff, stop:1 #f8f9fa); 
            margin: 2px; padding: 4px; 
        }
        #Card:hover { 
            border: 2px solid #007bff; 
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #e3f2fd, stop:1 #bbdefb); 
        }
        #SelectedCard { 
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #cce5ff, stop:1 #99d6ff); 
            border: 2px solid #007bff; 
        }
        #SectionCard { 
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #ffffff, stop:1 #f8f9fa); 
            border: 1px solid #dee2e6; border-radius: 8px; margin: 5px; 
            padding: 6px; 
        }
        QLabel, #CardLabel { background-color: transparent; border: none; color: #2c3e50; }

        /* === SPLITTER === */
        QSplitter::handle { background: transparent; } 
        QSplitter::handle:horizontal { width: 6px; } 
        QSplitter::handle:hover { background: rgba(0, 123, 255, 0.1); }
        
        /**********************************
         * STYLES CHO BUTTON              *
         **********************************/

        QPushButton {
            font-family: "Segoe UI";
            font-size: 10pt;
            font-weight: bold;
            color: #ffffff;
            border: none;
            padding: 6px 10px;
            border-radius: 8px;
            min-height: 22px;
        }
        QPushButton:disabled {
            background-color: #adb5bd;
            color: #e9ecef;
        }
        
        /* --- BUTTONS CHÍNH --- */

        /* MÀU XANH BIỂN: Thêm, Chọn tất cả */
        #AddSectionButton, #SelectAllButton {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #007bff, stop:1 #0056b3);
        }
        #AddSectionButton:hover, #SelectAllButton:hover {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #0056b3, stop:1 #004085);
        }

        /* MÀU XANH LÁ: Chạy, Làm mới, Hẹn giờ */
        #RefreshButton, #SectionRunButton, #SetScheduleButton { 
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #28a745, stop:1 #1e7e34); 
        }
        #RefreshButton:hover, #SectionRunButton:hover, #SetScheduleButton:hover { 
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #34ce57, stop:1 #28a745); 
        }
        
        /* MÀU CAM: Dừng */
        #SectionStopButton { 
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #fd7e14, stop:1 #e8590c); 
        }
        #SectionStopButton:hover { 
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #ff9a3c, stop:1 #fd7e14); 
        }

        /* MÀU ĐỎ: Đóng, Xóa */
        #SectionRemoveButton, #CloseAllNotebooksButton { 
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #dc3545, stop:1 #c82333); 
        }
        #SectionRemoveButton:hover, #CloseAllNotebooksButton:hover { 
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #e4606d, stop:1 #dc3545); 
        }

        /* MÀU TÍM: Xóa Log */
        #ClearAllLogsButton, #ClearLogButton {
             background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #6f42c1, stop:1 #5a32a3);
        }
        #ClearAllLogsButton:hover, #ClearLogButton:hover {
             background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #8a63d2, stop:1 #6f42c1);
        }
        
        /* --- BUTTONS NHỎ (TRONG CARD) --- */
        #RunButton, #StopButton, #RemoveButton, #ClearLogButton {
            border: none;
            border-radius: 6px;
            padding: 2px 4px;
            font-size: 8pt;
            color: white;
        }
        #SetScheduleButton {
            padding-top: 3px;
            padding-bottom: 3px;
        }

        #RunButton { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #28a745, stop:1 #1e7e34); }
        #RunButton:hover { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #34ce57, stop:1 #28a745); }
        #RunButton:disabled { background: #6c757d; }

        #StopButton { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #fd7e14, stop:1 #e8590c); }
        #StopButton:hover { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #ff9a3c, stop:1 #fd7e14); }
        #StopButton:disabled { background: #6c757d; }

        #RemoveButton { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #dc3545, stop:1 #c82333); }
        #RemoveButton:hover { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #e4606d, stop:1 #dc3545); }        
        
        /* === DIALOG & MESSAGE BOX === */
        QMessageBox {
            background-color: #ffffff;
            color: #2c3e50;
            border: 2px solid #dee2e6;
            border-radius: 8px;
            font-family: "Segoe UI";
        }
        QMessageBox QLabel {
            background-color: transparent;
            color: #2c3e50;
            font-family: "Segoe UI";
            font-size: 10pt;
        }
        QMessageBox QPushButton {
            border: none;
            border-radius: 6px;
            padding: 2px 4px;
            font-family: "Segoe UI";
            font-weight: bold;
            font-size: 9pt;
            color: white;
            min-width: 40px;
            min-height: 20px;
        }
        QMessageBox QPushButton[text="&Yes"], QMessageBox QPushButton[text="Có"] {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #007bff, stop:1 #0056b3);
        }
        QMessageBox QPushButton[text="&Yes"]:hover, QMessageBox QPushButton[text="Có"]:hover {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #0056b3, stop:1 #004085);
        }
        QMessageBox QPushButton[text="&No"], QMessageBox QPushButton[text="Không"] {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #dc3545, stop:1 #c82333);
        }
        QMessageBox QPushButton[text="&No"]:hover, QMessageBox QPushButton[text="Không"]:hover {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #e4606d, stop:1 #dc3545);
        }
    """
