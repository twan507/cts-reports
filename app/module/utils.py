"""
Module tiện ích - utils.py
Chứa các hàm tiện ích để hỗ trợ xử lý file, thời gian và báo cáo
"""

import os
import json
from datetime import datetime, timedelta
import pandas as pd


def create_directory_if_not_exists(directory_path):
    """
    Tạo thư mục nếu chưa tồn tại

    Args:
        directory_path (str): Đường dẫn thư mục

    Returns:
        bool: True nếu thành công
    """
    try:
        if not os.path.exists(directory_path):
            os.makedirs(directory_path)
            print(f"📁 Đã tạo thư mục: {directory_path}")
        else:
            print(f"📁 Thư mục đã tồn tại: {directory_path}")
        return True
    except Exception as e:
        print(f"❌ Lỗi khi tạo thư mục: {e}")
        return False


def get_file_info(file_path):
    """
    Lấy thông tin chi tiết của file

    Args:
        file_path (str): Đường dẫn file

    Returns:
        dict: Thông tin file
    """
    try:
        if not os.path.exists(file_path):
            return {"error": "File không tồn tại"}

        stat = os.stat(file_path)
        info = {
            "file_name": os.path.basename(file_path),
            "file_size_bytes": stat.st_size,
            "file_size_mb": round(stat.st_size / (1024 * 1024), 2),
            "created_time": datetime.fromtimestamp(stat.st_ctime).strftime("%Y-%m-%d %H:%M:%S"),
            "modified_time": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
            "file_extension": os.path.splitext(file_path)[1],
            "absolute_path": os.path.abspath(file_path),
        }
        return info

    except Exception as e:
        return {"error": f"Lỗi khi lấy thông tin file: {e}"}


def generate_timestamp_filename(base_name, extension=".xlsx"):
    """
    Tạo tên file với timestamp

    Args:
        base_name (str): Tên file gốc
        extension (str): Phần mở rộng file

    Returns:
        str: Tên file với timestamp
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{base_name}_{timestamp}{extension}"


def create_summary_report(data_dict, output_path):
    """
    Tạo báo cáo tổng hợp từ dictionary

    Args:
        data_dict (dict): Dữ liệu để tạo báo cáo
        output_path (str): Đường dẫn file output

    Returns:
        bool: True nếu thành công
    """
    try:
        # Tạo thư mục nếu chưa tồn tại
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Xác định loại file từ extension
        file_extension = os.path.splitext(output_path)[1].lower()

        if file_extension == ".txt":
            # Tạo báo cáo text
            report_content = "BÁO CÁO TỔNG HỢP\n"
            report_content += f"Thời gian tạo: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            report_content += "=" * 50 + "\n\n"

            def format_dict_to_text(d, indent=0):
                text = ""
                for key, value in d.items():
                    if isinstance(value, dict):
                        text += "  " * indent + f"{key}:\n"
                        text += format_dict_to_text(value, indent + 1)
                    else:
                        text += "  " * indent + f"{key}: {value}\n"
                return text

            report_content += format_dict_to_text(data_dict)

            with open(output_path, "w", encoding="utf-8") as f:
                f.write(report_content)

        elif file_extension in [".xlsx", ".xls"]:
            # Tạo DataFrame từ dictionary cho Excel
            report_data = []

            def flatten_dict(d, parent_key="", sep="_"):
                items = []
                for k, v in d.items():
                    new_key = f"{parent_key}{sep}{k}" if parent_key else k
                    if isinstance(v, dict):
                        items.extend(flatten_dict(v, new_key, sep=sep).items())
                    else:
                        items.append((new_key, v))
                return dict(items)

            flat_data = flatten_dict(data_dict)

            for key, value in flat_data.items():
                report_data.append({"Mục": key, "Giá trị": str(value), "Thời gian tạo": datetime.now().strftime("%Y-%m-%d %H:%M:%S")})

            df = pd.DataFrame(report_data)
            df.to_excel(output_path, index=False)

        elif file_extension == ".csv":
            # Tạo DataFrame từ dictionary cho CSV
            report_data = []

            def flatten_dict(d, parent_key="", sep="_"):
                items = []
                for k, v in d.items():
                    new_key = f"{parent_key}{sep}{k}" if parent_key else k
                    if isinstance(v, dict):
                        items.extend(flatten_dict(v, new_key, sep=sep).items())
                    else:
                        items.append((new_key, v))
                return dict(items)

            flat_data = flatten_dict(data_dict)

            for key, value in flat_data.items():
                report_data.append({"Mục": key, "Giá trị": str(value), "Thời gian tạo": datetime.now().strftime("%Y-%m-%d %H:%M:%S")})

            df = pd.DataFrame(report_data)
            df.to_csv(output_path, index=False, encoding="utf-8")

        else:
            # Mặc định: lưu dưới dạng text cho các định dạng khác
            report_content = "BÁO CÁO TỔNG HỢP\n"
            report_content += f"Thời gian tạo: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            report_content += "=" * 50 + "\n\n"

            def format_dict_to_text(d, indent=0):
                text = ""
                for key, value in d.items():
                    if isinstance(value, dict):
                        text += "  " * indent + f"{key}:\n"
                        text += format_dict_to_text(value, indent + 1)
                    else:
                        text += "  " * indent + f"{key}: {value}\n"
                return text

            report_content += format_dict_to_text(data_dict)

            with open(output_path, "w", encoding="utf-8") as f:
                f.write(report_content)

        print(f"📊 Đã tạo báo cáo tại: {output_path}")
        return True

    except Exception as e:
        print(f"❌ Lỗi khi tạo báo cáo: {e}")
        return False


def save_json_report(data, output_path):
    """
    Lưu dữ liệu dưới dạng JSON

    Args:
        data: Dữ liệu cần lưu
        output_path (str): Đường dẫn file JSON

    Returns:
        bool: True nếu thành công
    """
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        print(f"💾 Đã lưu JSON tại: {output_path}")
        return True
    except Exception as e:
        print(f"❌ Lỗi khi lưu JSON: {e}")
        return False


def calculate_date_range(start_date_str, days_ahead=30):
    """
    Tính toán khoảng thời gian

    Args:
        start_date_str (str): Ngày bắt đầu (YYYY-MM-DD)
        days_ahead (int): Số ngày tính từ ngày bắt đầu

    Returns:
        dict: Thông tin khoảng thời gian
    """
    try:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
        end_date = start_date + timedelta(days=days_ahead)

        return {
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "total_days": days_ahead,
            "weekdays": sum(1 for i in range(days_ahead) if (start_date + timedelta(days=i)).weekday() < 5),
            "weekends": sum(1 for i in range(days_ahead) if (start_date + timedelta(days=i)).weekday() >= 5),
        }
    except Exception as e:
        return {"error": f"Lỗi khi tính toán ngày: {e}"}


def print_processing_status(step_name, total_steps=None, current_step=None):
    """
    In trạng thái xử lý

    Args:
        step_name (str): Tên bước hiện tại
        total_steps (int): Tổng số bước
        current_step (int): Bước hiện tại
    """
    timestamp = datetime.now().strftime("%H:%M:%S")

    if total_steps and current_step:
        progress = f"[{current_step}/{total_steps}]"
        print(f"🔄 {timestamp} {progress} {step_name}")
    else:
        print(f"🔄 {timestamp} {step_name}")


def list_files_in_directory(directory_path, extension=None):
    """
    Liệt kê các file trong thư mục

    Args:
        directory_path (str): Đường dẫn thư mục
        extension (str): Phần mở rộng file cần lọc (vd: '.xlsx')

    Returns:
        list: Danh sách file
    """
    try:
        if not os.path.exists(directory_path):
            return []

        files = os.listdir(directory_path)

        if extension:
            files = [f for f in files if f.endswith(extension)]

        file_paths = [os.path.join(directory_path, f) for f in files]
        print(f"📂 Tìm thấy {len(file_paths)} file trong {directory_path}")

        return file_paths

    except Exception as e:
        print(f"❌ Lỗi khi liệt kê file: {e}")
        return []
