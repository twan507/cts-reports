import sys
import os

sys.path.append(os.path.join(os.path.dirname(os.getcwd()), "import"))

from import_default import *
from import_database import *
from import_other import *

def analyze_news_impact(news_df, model):
    # Tạo prompt hướng dẫn cho AI
    system_prompt = """
    Bạn là một chuyên gia phân tích thị trường chứng khoán Việt Nam. 
    Nhiệm vụ của bạn là đánh giá tác động của tin tức đến thị trường chứng khoán Việt Nam.
    
    Hãy phân loại mỗi tin tức thành 1 trong 3 loại:
    - "Tích cực": Tin tức có tác động tích cực đến thị trường chứng khoán VN (tăng trưởng kinh tế, chính sách hỗ trợ, kết quả kinh doanh tốt, đầu tư nước ngoài, cải cách tích cực...)
    - "Tiêu cực": Tin tức có tác động tiêu cực đến thị trường chứng khoán VN (suy thoái, lạm phát, xung đột thương mại, khủng hoảng tài chính, chính sách thắt chặt...)
    - "Trung lập": Tin tức không có tác động rõ ràng hoặc tác động cân bằng đến thị trường chứng khoán VN
    
    Chỉ trả về kết quả theo format: Tích cực|Tiêu cực|Trung lập|...
    Không giải thích, chỉ trả về danh sách phân loại cách nhau bởi dấu |
    """
    
    # Tạo danh sách tin tức để gửi cho AI
    news_list = []
    for idx, row in news_df.iterrows():
        news_item = f"Tin {idx + 1}:\nTiêu đề: {row['title']}\nNội dung: {row['content']}\n"
        news_list.append(news_item)
    
    # Ghép tất cả tin tức thành 1 prompt
    full_prompt = system_prompt + "\n\nDanh sách tin tức cần phân tích:\n\n" + "\n".join(news_list)
    
    try:
        # Gọi API Gemini
        response = model.generate_content(full_prompt)
        
        # Xử lý kết quả trả về
        result_text = response.text.strip()
        
        # Tách kết quả thành list
        impact_list = [item.strip() for item in result_text.split('|')]
        
        # Kiểm tra số lượng kết quả có khớp với số tin tức không
        if len(impact_list) != len(news_df):
            print(f"Cảnh báo: Số lượng kết quả ({len(impact_list)}) không khớp với số tin tức ({len(news_df)})")
            # Nếu không khớp, điền 'trung lập' cho các tin thiếu
            while len(impact_list) < len(news_df):
                impact_list.append('trung lập')
            # Cắt bớt nếu thừa
            impact_list = impact_list[:len(news_df)]
        
        # Validate kết quả - chỉ chấp nhận 3 giá trị hợp lệ
        valid_values = ['Tích cực', 'Tiêu cực', 'Trung lập']
        cleaned_impact_list = []
        for impact in impact_list:
            if impact in valid_values:
                cleaned_impact_list.append(impact)
            else:
                print(f"Giá trị không hợp lệ '{impact}', thay thế bằng 'trung lập'")
                cleaned_impact_list.append('trung lập')
        
        return cleaned_impact_list
        
    except Exception as e:
        print(f"Lỗi khi gọi API Gemini: {e}")
        # Trả về list 'trung lập' cho tất cả tin nếu có lỗi
        return ['trung lập'] * len(news_df)