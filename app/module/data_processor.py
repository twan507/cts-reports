"""
Module xử lý dữ liệu - data_processor.py
Chứa các hàm để đọc, xử lý và phân tích dữ liệu Excel
"""

import pandas as pd
import os
from datetime import datetime
from typing import Optional, Dict, Any, List, Literal


def read_excel_file(file_path: str) -> Optional[pd.DataFrame]:
    """
    Đọc file Excel và trả về DataFrame

    Args:
        file_path (str): Đường dẫn đến file Excel

    Returns:
        pd.DataFrame: Dữ liệu từ file Excel
    """
    try:
        df = pd.read_excel(file_path)
        print(f"✅ Đã đọc thành công file: {os.path.basename(file_path)}")
        print(f"📊 Số dòng: {len(df)}, Số cột: {len(df.columns)}")
        return df
    except Exception as e:
        print(f"❌ Lỗi khi đọc file {file_path}: {e}")
        return None


def analyze_data(df: Optional[pd.DataFrame], column_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Phân tích thống kê cơ bản cho DataFrame

    Args:
        df (pd.DataFrame): Dữ liệu cần phân tích
        column_name (str): Tên cột cần phân tích chi tiết (optional)

    Returns:
        dict: Kết quả phân tích
    """
    if df is None or df.empty:
        return {"error": "DataFrame rỗng hoặc không hợp lệ"}

    analysis = {
        "total_rows": len(df),
        "total_columns": len(df.columns),
        "columns": list(df.columns),
        "data_types": df.dtypes.to_dict(),
        "missing_values": df.isnull().sum().to_dict(),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    # Phân tích chi tiết cho cột cụ thể
    if column_name and column_name in df.columns:
        col_data = df[column_name]
        analysis[f"{column_name}_stats"] = {
            "count": col_data.count(),
            "unique": col_data.nunique(),
            "top_values": col_data.value_counts().head(5).to_dict(),
        }

        # Nếu là số, thêm thống kê số học
        if pd.api.types.is_numeric_dtype(col_data):
            analysis[f"{column_name}_numeric"] = {
                "mean": round(col_data.mean(), 2),
                "median": round(col_data.median(), 2),
                "std": round(col_data.std(), 2),
                "min": col_data.min(),
                "max": col_data.max(),
            }

    return analysis


def save_analysis_to_excel(analysis_data: Dict[str, Any], output_path: str) -> bool:
    """
    Lưu kết quả phân tích vào file Excel

    Args:
        analysis_data (dict): Dữ liệu phân tích
        output_path (str): Đường dẫn file output

    Returns:
        bool: True nếu lưu thành công
    """
    try:
        # Chuyển dict thành DataFrame để lưu
        summary_data = []
        for key, value in analysis_data.items():
            if isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    summary_data.append({"Category": key, "Metric": sub_key, "Value": str(sub_value)})
            else:
                summary_data.append({"Category": "General", "Metric": key, "Value": str(value)})

        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(output_path, index=False)
        print(f"💾 Đã lưu phân tích vào: {output_path}")
        return True

    except Exception as e:
        print(f"❌ Lỗi khi lưu file: {e}")
        return False


def save_to_excel(df: pd.DataFrame, output_path: str) -> bool:
    """
    Lưu DataFrame vào file Excel

    Args:
        df (pd.DataFrame): DataFrame để lưu
        output_path (str): Đường dẫn file output

    Returns:
        bool: True nếu lưu thành công
    """
    try:
        # Tạo thư mục nếu chưa tồn tại
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        df.to_excel(output_path, index=False)
        print(f"💾 Đã lưu file Excel: {output_path}")
        return True

    except Exception as e:
        print(f"❌ Lỗi khi lưu file: {e}")
        return False


def merge_dataframes(
    df1: pd.DataFrame, df2: pd.DataFrame, on: Optional[str] = None, how: Literal["outer", "inner", "left", "right"] = "outer"
) -> Optional[pd.DataFrame]:
    """
    Kết hợp 2 DataFrame

    Args:
        df1 (pd.DataFrame): DataFrame đầu tiên
        df2 (pd.DataFrame): DataFrame thứ hai
        on (str): Cột để join
        how (str): Kiểu join ('outer', 'inner', 'left', 'right')

    Returns:
        pd.DataFrame: DataFrame đã kết hợp
    """
    try:
        if on:
            merged_df = pd.merge(df1, df2, on=on, how=how)
        else:
            merged_df = pd.concat([df1, df2], ignore_index=True)

        print(f"🔄 Đã kết hợp DataFrame: {len(merged_df)} bản ghi")
        return merged_df

    except Exception as e:
        print(f"❌ Lỗi khi kết hợp DataFrame: {e}")
        return None


def process_dataframe(df: pd.DataFrame, operations: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Xử lý DataFrame với các thao tác cơ bản

    Args:
        df (pd.DataFrame): DataFrame để xử lý
        operations (list): Danh sách các thao tác ('clean', 'sort', 'dedupe')

    Returns:
        pd.DataFrame: DataFrame đã xử lý
    """
    if operations is None:
        operations = ["clean"]

    processed_df = df.copy()

    try:
        if "clean" in operations:
            # Loại bỏ các dòng trống
            processed_df = processed_df.dropna()
            print("✨ Đã làm sạch dữ liệu")

        if "sort" in operations and len(processed_df.columns) > 0:
            # Sắp xếp theo cột đầu tiên
            processed_df = processed_df.sort_values(processed_df.columns[0])
            print("📊 Đã sắp xếp dữ liệu")

        if "dedupe" in operations:
            # Loại bỏ duplicates
            processed_df = processed_df.drop_duplicates()
            print("🔄 Đã loại bỏ dữ liệu trùng lặp")

        return processed_df

    except Exception as e:
        print(f"❌ Lỗi khi xử lý DataFrame: {e}")
        return df


def merge_excel_files(file1_path: str, file2_path: str, output_path: str, merge_on: Optional[str] = None) -> bool:
    """
    Gộp 2 file Excel thành 1 file

    Args:
        file1_path (str): Đường dẫn file Excel đầu tiên
        file2_path (str): Đường dẫn file Excel thứ hai
        output_path (str): Đường dẫn file output
        merge_on (str): Cột để join (nếu có)

    Returns:
        bool: True nếu gộp thành công
    """
    try:
        df1 = read_excel_file(file1_path)
        df2 = read_excel_file(file2_path)

        if df1 is None or df2 is None:
            return False

        if merge_on and merge_on in df1.columns and merge_on in df2.columns:
            # Merge theo cột chỉ định
            merged_df = pd.merge(df1, df2, on=merge_on, how="outer")
            print(f"🔄 Đã merge 2 file theo cột: {merge_on}")
        else:
            # Concat đơn giản
            merged_df = pd.concat([df1, df2], ignore_index=True)
            print("🔄 Đã concat 2 file")

        merged_df.to_excel(output_path, index=False)
        print(f"💾 Đã lưu file gộp vào: {output_path}")
        return True

    except Exception as e:
        print(f"❌ Lỗi khi gộp file: {e}")
        return False
