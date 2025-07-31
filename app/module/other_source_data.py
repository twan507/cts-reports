import sys
import os

sys.path.append(os.path.join(os.path.dirname(os.getcwd()), "import"))

from import_default import *
from import_database import *
from import_other import *
from import_gemini import *

wichart_item_name_dict = {
    "tien_te": {
        "dtnh": "Dự trữ ngoại hối",
        "ctt": "Cung tiền tệ",
        "hd": "Tổng tiền gửi trong nền kinh tế",
        "td": "Tổng tín dụng vốn trong nền kinh tế",
        "lslnh": "Lãi suất liên ngân hàng",
        "lshd": "Lãi suất huy động",
        "lsdh": "Lãi suất điều hành",
        "dhtg": "Tỷ giá USD/VND",
    },
    "vi_mo": {
        "gdp": "Tăng trưởng GDP",
        "cpi": "Chỉ số giá tiêu dùng (CPI)",
        "iip": "Chỉ số sản xuất công nghiệp (IIP)",
        "pmi": "Chỉ số quản lý mua hàng (PMI)",
        "hhdv": "Tổng mức bán lẻ hàng hóa dịch vụ",
        "cctm": "Cán cân thương mại",
    },
    "hang_hoa": {
        "heo_hoi": "Giá heo hơi",
        "duong": "Giá đường",
        "soi_coto ngày": "Giá sợi cotto ngày",
        "gao_tpxk": "Giá gạo xuất khẩu",
        "quang_sat": "Giá quặng sắt",
        "vang": "Giá vàng trong nước",
        "hrc_trung_quoc": "Giá thép HRC Trung Quốc",
        "nhua_pvc_trung_quoc": "Giá nhựa PVC Trung Quốc",
        "phot_pho": "Giá phốt pho",
        "ure_trung_dong": "Giá Ure Trung Đông",
        "cao_su_nhat_ba ngày": "Giá cao su Nhật Bả ngày",
    },
}

wichart_item_list_dict = {
    "tien_te": {"monthly": ["dtnh, ctt, hd, td"], "daily": ["lslnh, lshd, lsdh, dhtg"]},
    "vi_mo": {
        "gdp_cpi": ["gdp, cpi"],
        "kinh_te": ["iip, pmi, hhdv"],
        "cctm": ["cctm"],
        "ncp": ["ncp"],
        "tcns": ["tcns"],
    },
    "hang_hoa": {
        "tieu_dung": ["heo_hơi, tom_the, duong", "soi_coton, gao_tpxk"],
        "kim_loai": ["quang_sat", "vang_the_gioi", "vang", "hrc_trung_quoc"],
        "hoa_chat": ["nhua_pvc_trung_quoc", "phot_pho", "phan_urea_trung_quoc, cao_su_nhat_ba ngày"],
    },
}

wichart_api_url_dict = {
    "tien_te": "https://api.wichart.vn/vietnambiz/vi-mo?name=",
    "vi_mo": "https://api.wichart.vn/vietnambiz/vi-mo?name=",
    "hang_hoa": "https://api.wichart.vn/vietnambiz/vi-mo?key=hang_hoa&name=",
}


def fetch_wichart_data(api_url: str):
    response = requests.get(api_url)
    response.raise_for_status()
    json_data = response.json()

    # Kiểm tra các key cần thiết để tránh lỗi
    if "chart" not in json_data or "series" not in json_data["chart"]:
        print("Lỗi: Cấu trúc JSON không chứa key 'chart' hoặc 'series'.")
        return None
    series_list = json_data["chart"]["series"]

    # Danh sách để chứa các DataFrame của từng series
    all_series_dfs = []
    # 1. Lặp qua từng series và tạo DataFrame riêng
    for series in series_list:
        series_name = series["name"]
        data_points = series["data"]
        # Tạo DataFrame cho series hiện tại
        temp_df = pd.DataFrame(data_points, columns=["timestamp", series_name])
        # Chuyển đổi timestamp (mili giây) sang kiểu datetime
        temp_df["date"] = pd.to_datetime(temp_df["timestamp"], unit="ms").dt.date
        # Chỉ giữ lại cột 'date' và cột dữ liệu của series
        all_series_dfs.append(temp_df[["date", series_name]])
    # Bắt đầu với DataFrame đầu tiên
    final_df = all_series_dfs[0]
    # Gộp các DataFrame còn lại vào final_df
    for i in range(1, len(all_series_dfs)):
        # how='outer' để giữ lại tất cả các ngày từ cả hai bảng
        final_df = pd.merge(final_df, all_series_dfs[i], on="date", how="outer")
    # 3. Sắp xếp lại theo ngày mới nhất và trả về kết quả
    final_df = final_df.sort_values(by="date", ascending=False).reset_index(drop=True)

    return final_df


def simple_kmeans_1d(data, k=2, max_iterations=100):
    """Phân cụm K-Means đơn giản cho dữ liệu 1 chiều."""
    # 1. Khởi tạo tâm cụm ngẫu nhiên từ dữ liệu
    centroids = random.sample(data, k)

    for _ in range(max_iterations):
        clusters = [[] for _ in range(k)]

        # 2. Phân mỗi điểm vào cụm gần nhất
        for point in data:
            # Khoảng cách trong 1D chỉ là giá trị tuyệt đối của hiệu
            distances = [abs(point - c) for c in centroids]
            closest_index = distances.index(min(distances))
            clusters[closest_index].append(point)

        # 3. Cập nhật lại tâm cụm
        new_centroids = []
        for i, cluster in enumerate(clusters):
            if cluster:
                new_centroids.append(sum(cluster) / len(cluster))
            else:
                # Nếu cụm rỗng, giữ lại tâm cũ
                new_centroids.append(centroids[i])

        # 4. Dừng nếu tâm cụm không thay đổi
        if new_centroids == centroids:
            break
        centroids = new_centroids

    # Gán nhãn cuối cùng cho các điểm dữ liệu
    labels = [min(range(k), key=lambda i: abs(p - centroids[i])) for p in data]
    return labels, centroids


def clasify_omo_rate_df(term_dict):
    """
    Phân loại file thành 'bill' và 'repo' từ một dict {file_path: mean_term}.
    """
    if not term_dict or len(term_dict) < 2:
        print("Lỗi: Cần ít nhất 2 file để phân cụm.")
        return [], []

    # --- Bước 1: Chuẩn bị dữ liệu ---
    file_paths = list(term_dict.keys())
    mean_terms = list(term_dict.values())

    # --- Bước 2: Chạy K-Means 1D ---
    labels, centroids = simple_kmeans_1d(mean_terms, k=2)

    # --- Bước 3: Gán nhãn cho cụm ---
    # Tâm cụm có giá trị lớn hơn là của Tín phiếu (Bill)
    if centroids[0] > centroids[1]:
        bill_cluster_label = 1
    else:
        bill_cluster_label = 0

    # --- Bước 4: Phân loại file vào danh sách cuối cùng ---
    bill_files, repo_files = [], []
    for i, path in enumerate(file_paths):
        if labels[i] == bill_cluster_label:
            bill_files.append(path)
        else:
            repo_files.append(path)

    return bill_files, repo_files


import pandas as pd

import pandas as pd


def transform_rate_omo_data(df: pd.DataFrame) -> pd.DataFrame:
    # Sửa lại tên sản phẩm để nhất quán (dùng "ngày" thay vì "N")
    products = [
        "Tín phiếu 7 ngày",
        "Tín phiếu 14 ngày",
        "Tín phiếu 28 ngày",
        "Reversed Repo 7 ngày",
        "Reversed Repo 14 ngày",
        "Reversed Repo 21 ngày",
        "Reversed Repo 28 ngày",
        "Reversed Repo 35 ngày",
        "Reversed Repo 91 ngày",
    ]

    # 1. Lấy 5 ngày giao dịch gần nhất (thứ tự: mới nhất -> cũ nhất)
    unique_dates = sorted(df["date"].unique(), reverse=True)
    dates_to_process = unique_dates[:5]

    # --- THAY ĐỔI: Đảo ngược danh sách ngày ---
    # Sắp xếp lại để xử lý từ ngày cũ nhất -> mới nhất, đảo ngược thứ tự cột output
    dates_to_process.reverse()

    # 2. Tạo tên cột động từ ngày thực tế (thứ tự giờ đã là: cũ nhất -> mới nhất)
    final_columns = []
    for date in dates_to_process:
        date_str = str(date.date()) if hasattr(date, "date") else str(date)
        final_columns.append(f"rate-{date_str}")
        final_columns.append(f"value-{date_str}")

    # 3. Tạo DataFrame rỗng để chứa kết quả
    result_df = pd.DataFrame(index=products, columns=final_columns)

    # 4. Lặp qua dữ liệu gốc và điền vào bảng kết quả
    for index, row in df.iterrows():
        if row["date"] not in dates_to_process:
            continue

        product_type = "Reversed Repo" if row["type"] == "repo" else "Tín phiếu"
        # Sửa lại cách tạo tên để khớp với danh sách 'products'
        target_product = f"{product_type} {row['term']} ngày"

        if target_product in result_df.index:
            date_str = str(row["date"].date()) if hasattr(row["date"], "date") else str(row["date"])
            value_col = f"value-{date_str}"
            rate_col = f"rate-{date_str}"

            result_df.loc[target_product, value_col] = row["value"]
            result_df.loc[target_product, rate_col] = row["rate"]

    return result_df
