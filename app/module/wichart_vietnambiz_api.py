import sys
import os

sys.path.append(os.path.join(os.path.dirname(os.getcwd()), "import"))

from import_default import *
from import_database import *
from import_other import *
from import_gemini import *

wichart_item_name_dict = {
    'tien_te': {
        'dtnh': 'Dự trữ ngoại hối',
        'ctt': 'Cung tiền tệ',
        'hd': 'Tổng tiền gửi trong nền kinh tế',
        'td': 'Tổng tín dụng vốn trong nền kinh tế',
        'lslnh': 'Lãi suất liên ngân hàng',
        'lshd': 'Lãi suất huy động',
        'lsdh': 'Lãi suất điều hành',
        'dhtg': 'Tỷ giá USD/VND'
    },
    'vi_mo': {
        'gdp': 'Tăng trưởng GDP',
        'cpi': 'Chỉ số giá tiêu dùng (CPI)',
        'iip': 'Chỉ số sản xuất công nghiệp (IIP)',
        'pmi': 'Chỉ số quản lý mua hàng (PMI)',
        'hhdv': 'Tổng mức bán lẻ hàng hóa dịch vụ',
        'cctm': 'Cán cân thương mại',
    },
    'hang_hoa': {
        'heo_hoi': 'Giá heo hơi',
        'duong': 'Giá đường',
        'soi_coton': 'Giá sợi cotton',
        'gao_tpxk': 'Giá gạo xuất khẩu',
        'quang_sat': 'Giá quặng sắt',
        'vang': 'Giá vàng trong nước',
        'hrc_trung_quoc': 'Giá thép HRC Trung Quốc',
        'nhua_pvc_trung_quoc': 'Giá nhựa PVC Trung Quốc',
        'phot_pho': 'Giá phốt pho',
        'ure_trung_dong': 'Giá Ure Trung Đông',
        'cao_su_nhat_ban': 'Giá cao su Nhật Bản'
    }
}

wichart_item_list_dict = {
    'tien_te': {
        'monthly': ['dtnh, ctt, hd, td'],
        'daily': ['lslnh, lshd, lsdh, dhtg']
    },
    'vi_mo': {
        'gdp_cpi': ['gdp, cpi'],
        'kinh_te': ['iip, pmi, hhdv'],
        'cctm': ['cctm'],
        'ncp': ['ncp'],
        'tcns': ['tcns'],
    },
    'hang_hoa': {
        'tieu_dung': ['heo_hơi, tom_the, duong', 'soi_coton, gao_tpxk'],
        'kim_loai': ['quang_sat', 'vang_the_gioi', 'vang', 'hrc_trung_quoc'],
        'hoa_chat': ['nhua_pvc_trung_quoc', 'phot_pho', 'phan_urea_trung_quoc, cao_su_nhat_ban'],
    }
}

wichart_api_url_dict = {
    'tien_te': "https://api.wichart.vn/vietnambiz/vi-mo?name=",
    'vi_mo': "https://api.wichart.vn/vietnambiz/vi-mo?name=",
    'hang_hoa': "https://api.wichart.vn/vietnambiz/vi-mo?key=hang_hoa&name="
}

def fetch_wichart_data(api_url: str):
    response = requests.get(api_url)
    response.raise_for_status()  
    json_data = response.json()

    # Kiểm tra các key cần thiết để tránh lỗi
    if 'chart' not in json_data or 'series' not in json_data['chart']:
        print("Lỗi: Cấu trúc JSON không chứa key 'chart' hoặc 'series'.")
        return None
    series_list = json_data['chart']['series']
    
    # Danh sách để chứa các DataFrame của từng series
    all_series_dfs = []
    # 1. Lặp qua từng series và tạo DataFrame riêng
    for series in series_list:
        series_name = series['name']
        data_points = series['data']
        # Tạo DataFrame cho series hiện tại
        temp_df = pd.DataFrame(data_points, columns=['timestamp', series_name])
        # Chuyển đổi timestamp (mili giây) sang kiểu datetime
        temp_df['date'] = pd.to_datetime(temp_df['timestamp'], unit='ms').dt.date
        # Chỉ giữ lại cột 'date' và cột dữ liệu của series
        all_series_dfs.append(temp_df[['date', series_name]])
    # Bắt đầu với DataFrame đầu tiên
    final_df = all_series_dfs[0]
    # Gộp các DataFrame còn lại vào final_df
    for i in range(1, len(all_series_dfs)):
        # how='outer' để giữ lại tất cả các ngày từ cả hai bảng
        final_df = pd.merge(final_df, all_series_dfs[i], on='date', how='outer')
    # 3. Sắp xếp lại theo ngày mới nhất và trả về kết quả
    final_df = final_df.sort_values(by='date', ascending=False).reset_index(drop=True)
    
    return final_df