# NBRunner - Jupyter Notebook Runner

🚀 Ứng dụng Python nhỏ gọn để chạy và quản lý Jupyter Notebooks với giao diện **PyQt6**.

## 🔧 Hướng dẫn nhanh

### Setup (Thiết lập lần đầu)
```cmd
setup.bat
```
*Tạo môi trường ảo và cài đặt dependencies từ `development/requirements.txt`.*

### Start (Chạy thử nghiệm)
```cmd
start.bat
```
*Khởi chạy ứng dụng trong chế độ development.*

### Build (Đóng gói thành .exe)
```cmd
build.bat
```
*Sử dụng `development/build.spec` để tạo ứng dụng standalone trong thư mục `app/`.*

### Kích hoạt và thoát môi trường ảo
```cmd
development\venv\Scripts\activate.bat
deactivate
```

## 📁 Cấu trúc
```
/nbrunner
├── app/                  # 🎯 Thư mục ứng dụng đã build
│   ├── nbrunner.exe      #  ↳🚀 File thực thi chính của ứng dụng NBRunner (Windows)
│   ├── module/           #  ↳📦 Chứa các module Python mở rộng, tiện ích, xử lý dữ liệu
│   └── notebook/         #  ↳📓 Lưu trữ các file Jupyter Notebook để chạy và phân tích
│   └── data/             #  ↳📁 Dữ liệu đầu vào, file nguồn (Excel, CSV, v.v.)
│   └── output/           #  ↳📤 Kết quả xuất ra từ notebook: báo cáo, file tổng hợp, v.v.
│
├── development/          # 💻 Mã nguồn và tài nguyên phát triển
│   ├── src/              #  ↳📝 Mã nguồn chính của ứng dụng
│   ├── venv/             #  ↳🐍 Môi trường ảo Python
│   ├── build.spec        #  ↳⚙️ Cấu hình build của PyInstaller
│   ├── logo.ico          #  ↳🖼️ Biểu tượng ứng dụng (icon)
│   ├── README.md         #  ↳📄 Tài liệu hướng dẫn, mô tả dự án
│   └── requirements.txt  #  ↳📦 Danh sách các thư viện/phụ thuộc Python
│
├── .gitignore            # 🛡️ Danh sách file/thư mục bị loại trừ khỏi git
├── build.bat             # 📦 Chạy để đóng gói ứng dụng
├── setup.bat             # 🔧 Chạy để cài đặt môi trường
└── start.bat             # ▶️ Chạy ứng dụng ở chế độ dev
```

## ✨ Tính năng chính
- ✅ Chạy và quản lý nhiều notebook
- ⚡ Thực thi đa tiến trình (multi-processing)
- 🔄 Lập lịch chạy tự động
- 📊 Hiển thị log và output thời gian thực
- 📦 Hỗ trợ import module tùy chỉnh
- 💾 Quản lý log và trạng thái chạy

## 🎯 Sử dụng
1.  Đặt các file notebook (`.ipynb`) vào thư mục `app/notebook/`.
2.  Đặt các module Python tùy chỉnh (`.py`) vào thư mục `app/module/`.
3.  Chạy file `app/nbrunner.exe`.

## 📋 Yêu cầu
-   Windows OS
-   Python 3.7+ (chỉ cần khi phát triển)