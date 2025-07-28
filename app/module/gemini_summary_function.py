import sys
import os

sys.path.append(os.path.join(os.path.dirname(os.getcwd()), "import"))

from import_default import *
from import_database import *
from import_other import *
from import_gemini import *

def summary_daily_article(model_dict, content):
    def count_words(text):
        """Đếm số từ trong văn bản tiếng Việt"""
        # Loại bỏ ký tự xuống dòng và khoảng trắng thừa
        clean_text = ' '.join(text.strip().split())
        # Đếm từ bằng cách tách theo khoảng trắng
        return len(clean_text.split())
    
    def create_prompt(attempt=1):
        """Tạo prompt với điều chỉnh dựa trên số lần thử"""
        word_requirement = ""
        if attempt == 1:
            word_requirement = "- ĐÚNG 5 CÂU VĂN, mỗi câu khoảng 13-16 từ"
        elif attempt == 2:
            word_requirement = "- ĐÚNG 5 CÂU VĂN, mỗi câu CHÍNH XÁC 14 từ"
        else:
            word_requirement = "- NGHIÊM NGẶT: 5 CÂU VĂN, mỗi câu ĐÚNG 14 từ, không nhiều hơn, không ít hơn"
        
        return f"""
            Tóm tắt bài báo sau:
            {content}

            YÊU CẦU NGHIÊM NGẶT:
            {word_requirement}
            - BAO GỒM SỐ LIỆU CỤ THỂ
            - KHÔNG DÙNG CỤM TỪ GIỚI THIỆU
            - TRÌNH BÀY THÔNG TIN CỐT LÕI NHẤT
            - BẮT ĐẦU TRỰC TIẾP BẰNG NỘI DUNG CHÍNH
            - **ĐẶC BIỆT QUAN TRỌNG**: Viết thành 1 đoạn văn duy nhất
        """
    
    # Thử tối đa 5 lần để có được kết quả trong khoảng 30-40 từ
    max_attempts = 5
    
    for attempt in range(1, max_attempts + 1):
        try:
            prompt = create_prompt(attempt)
            result = generate_content_with_model_dict(model_dict, prompt, 'summary_daily_article')
            
            # Đếm số từ
            word_count = count_words(result)
            
            # Kiểm tra xem có nằm trong khoảng 30-40 từ không
            if 70 <= word_count <= 90:
                return result
            else:
                if attempt == max_attempts:
                    return result
                
        except Exception as e:
            print(f"❌ Lỗi lần thử {attempt}: {e}")
            if attempt == max_attempts:
                raise e
    
    # Fallback (không bao giờ đến đây nhưng để đảm bảo)
    return generate_content_with_model_dict(model_dict, create_prompt(), 'summary_daily_article')

def summary_weekly_article(model_dict, content):
    def count_words(text):
        """Đếm số từ trong văn bản tiếng Việt"""
        # Loại bỏ ký tự xuống dòng và khoảng trắng thừa
        clean_text = ' '.join(text.strip().split())
        # Đếm từ bằng cách tách theo khoảng trắng
        return len(clean_text.split())
    
    def create_prompt(attempt=1):
        """Tạo prompt với điều chỉnh dựa trên số lần thử"""
        word_requirement = ""
        if attempt == 1:
            word_requirement = "- ĐÚNG 3 CÂU VĂN, mỗi câu khoảng 13-16 từ"
        elif attempt == 2:
            word_requirement = "- ĐÚNG 3 CÂU VĂN, mỗi câu CHÍNH XÁC 14 từ"
        else:
            word_requirement = "- NGHIÊM NGẶT: 3 CÂU VĂN, mỗi câu ĐÚNG 14 từ, không nhiều hơn, không ít hơn"
        
        return f"""
            Tóm tắt bài báo sau:
            {content}

            YÊU CẦU NGHIÊM NGẶT:
            {word_requirement}
            - BAO GỒM SỐ LIỆU CỤ THỂ
            - KHÔNG DÙNG CỤM TỪ GIỚI THIỆU
            - TRÌNH BÀY THÔNG TIN CỐT LÕI NHẤT
            - BẮT ĐẦU TRỰC TIẾP BẰNG NỘI DUNG CHÍNH
            - **ĐẶC BIỆT QUAN TRỌNG**: Viết thành 1 đoạn văn duy nhất
            
            Ví dụ: Lạm phát tháng 12 tăng 3,2% so với cùng kỳ. Giá xăng dầu giảm 5% trong tuần qua. GDP quý 4 tăng trưởng 6,8%.
        """
    
    # Thử tối đa 5 lần để có được kết quả trong khoảng 30-40 từ
    max_attempts = 5
    
    for attempt in range(1, max_attempts + 1):
        try:
            prompt = create_prompt(attempt)
            result = generate_content_with_model_dict(model_dict, prompt, 'summary_weekly_article')
            
            # Đếm số từ
            word_count = count_words(result)
            
            # Kiểm tra xem có nằm trong khoảng 30-40 từ không
            if 40 <= word_count <= 60:
                return result
            else:
                if attempt == max_attempts:
                    return result
                
        except Exception as e:
            print(f"❌ Lỗi lần thử {attempt}: {e}")
            if attempt == max_attempts:
                raise e
    
    # Fallback (không bao giờ đến đây nhưng để đảm bảo)
    return generate_content_with_model_dict(model_dict, create_prompt(), 'summary_weekly_article')
