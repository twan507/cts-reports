import sys
import os

sys.path.append(os.path.join(os.path.dirname(os.getcwd()), "import"))

from import_default import *
from import_database import *
from import_other import *

def get_gemini_models():
    """
    Lấy danh sách các model Gemini có sẵn và phân loại theo version và type.
    Chỉ lấy các model ngôn ngữ, loại bỏ tất cả model khác.
    
    Returns:
        tuple: (flash_models_list, thinking_models_list)
            - flash_models_list: Danh sách tất cả Flash models
            - thinking_models_list: Danh sách tất cả Thinking models
    """

    available_models = []
    for model in genai.list_models():
        if 'generateContent' in model.supported_generation_methods:
            model_name = model.name.replace('models/', '')
            
            # Loại bỏ tất cả các model không phải ngôn ngữ
            excluded_keywords = [
                'exp',                     # Model exp
                'image-generation',        # Model tạo ảnh
                'tts',                     # Text-to-speech
                'speech',                  # Speech models
                'audio',                   # Audio models
                'vision',                  # Vision models (nếu có)
                'embedding',               # Embedding models
                'code',                    # Code-specific models (nếu không phải chat)
                'translate',               # Translation-only models
                'search'                   # Search models
            ]
            
            # Kiểm tra xem model có chứa từ khóa loại trừ không
            should_exclude = any(keyword in model_name.lower() for keyword in excluded_keywords)
            
            # Chỉ lấy gemini-2.0 hoặc gemini-2.5 và không có từ khóa loại trừ
            if (not should_exclude and 
                ('gemini-2.0' in model_name or 'gemini-2.5' in model_name)):
                available_models.append({
                    'model_name': model_name,
                })

    # Lọc và phân loại các model
    model_list = []
    for model in available_models:
        model_list.append(model['model_name'])

    return model_list

def select_standard_models(model_list: list[str]) -> list[str]:
    candidates = []

    for model_name in model_list:
        # Bước 1: Lọc sơ bộ - chỉ giữ lại các model 'gemini-2.5-flash' không-lite
        if not model_name.startswith('gemini-2.5-flash') or 'lite' in model_name:
            continue

        # Bước 2: Phân tích các thành phần một cách linh hoạt
        has_thinking = 'thinking' in model_name
        thinking_priority = 0 if has_thinking else 1

        # Tìm kiếm các mẫu 'preview' và 'phiên bản cố định'
        preview_match = re.search(r'-preview-(\d{2}-\d{2})', model_name)
        fixed_match = re.search(r'-(\d{3})$', model_name) # $ để đảm bảo nó ở cuối chuỗi

        # Bước 3: Xác định loại model và giá trị sắp xếp
        if preview_match:
            type_priority = 3
            date_str = preview_match.group(1)
            try:
                sort_value = datetime.strptime(date_str, "%m-%d")
            except ValueError:
                continue
        elif fixed_match:
            type_priority = 2
            version_str = fixed_match.group(1)
            sort_value = -int(version_str)
        else: # Model cơ bản
            type_priority = 1
            sort_value = 0

        candidates.append({
            'name': model_name,
            'thinking_p': thinking_priority,
            'type_p': type_priority,
            'sort_v': sort_value
        })

    # Bước 4: Sắp xếp các ứng viên bằng key đa cấp
    def sort_key(option):
        # Đối với preview, sắp xếp ngày giảm dần (ngày mới nhất trước)
        if option['type_p'] == 3:
            sort_v_cmp = -option['sort_v'].toordinal()
        else:
            sort_v_cmp = option['sort_v']
        
        return (option['thinking_p'], option['type_p'], sort_v_cmp)

    candidates.sort(key=sort_key)

    # Bước 5: Trích xuất tên model đã được sắp xếp
    return [opt['name'] for opt in candidates]

def select_fast_models(model_list: list[str]) -> list[str]:
    target_families = [
        'gemini-2.0-flash',
        'gemini-2.5-flash-lite', # Đưa lên vị trí thứ 2
        'gemini-2.0-flash-lite'  # Chuyển xuống vị trí cuối
    ]
    
    candidates = {family: [] for family in target_families}
    pattern = re.compile(r"^(gemini-(?:2\.0|2\.5)-flash(?:-lite)?)(?:-(\d{3})|-preview-(\d{2}-\d{2}))?$")

    for model_name in model_list:
        match = pattern.match(model_name)
        if match:
            family, fixed_version, preview_date = match.groups()
            
            if family in target_families:
                if fixed_version is None and preview_date is None:
                    priority = 1
                    sort_value = 0
                elif fixed_version:
                    priority = 2
                    sort_value = -int(fixed_version)
                elif preview_date:
                    priority = 3
                    try:
                        sort_value = datetime.strptime(preview_date, "%m-%d")
                    except ValueError:
                        continue
                
                candidates[family].append({'priority': priority, 'sort_value': sort_value, 'name': model_name})

    final_selection = []
    for family, options in candidates.items():
        if not options:
            continue
        
        previews = [opt for opt in options if opt['priority'] == 3]
        others = [opt for opt in options if opt['priority'] != 3]

        previews.sort(key=lambda x: x['sort_value'], reverse=True)
        others.sort(key=lambda x: (x['priority'], x['sort_value']))

        sorted_options = others + previews
        
        if sorted_options:
            best_model = sorted_options[0]['name']
            final_selection.append(best_model)
            
    return final_selection

def generate_content_with_model_dict(model_dict, prompt):
    """
    Thử generate content với các model từ model_dict theo thứ tự.
    Tự động fallback sang model tiếp theo nếu gặp lỗi.
    """
    for _ in range(2):
        for model_name, model_instance in model_dict.items():
            try:
                response = model_instance.generate_content(prompt)
                # print(f"✅ Model {model_name} thành công")
                return response.text
            except Exception as e:
                # print(f"❌ Model {model_name} thất bại")
                continue
    # Nếu tất cả model đều thất bại
    raise Exception("❌ Tất cả model đều thất bại")

def summary_article(model_dict, content, news_type):
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
        
        if news_type == "doanh_nghiep":
            return f"""
                Tóm tắt bài báo sau:
                {content}

                YÊU CẦU NGHIÊM NGẶT:
                {word_requirement}
                - BAO GỒM SỐ LIỆU CỤ THỂ
                - KHÔNG DÙNG CỤM TỪ GIỚI THIỆU
                
                QUY TẮC VỀ MÃ CỔ PHIẾU:
                - Nếu có mã cổ phiếu trong bài báo: Bắt đầu câu đầu tiên bằng "MÃ_CỔ_PHIẾU: Nội dung..." (VD: HPG: Doanh thu Q4 tăng 25%)
                - Nếu KHÔNG có mã cổ phiếu: Bắt đầu trực tiếp bằng nội dung chính
                - TUYỆT ĐỐI KHÔNG viết "MÃ:" hoặc sử dụng ngoặc vuông []
                - CHỈ sử dụng mã cổ phiếu thực tế có trong bài báo
                
                Ví dụ đúng:
                - Có mã cổ phiếu: "VIC: Cổ phiếu tăng trần lên 101.600 đồng. Tài sản tỷ phú Vượng tăng 12.000 tỷ. Dự án Cần Giờ được phê duyệt 2025."
                - Không có mã: "Thị trường chứng khoán tăng 2,3% tuần qua. VN-Index đạt 1.250 điểm. Thanh khoản đạt 20.000 tỷ đồng."
            """
        else:
            return f"""
                Tóm tắt bài báo sau:
                {content}

                YÊU CẦU NGHIÊM NGẶT:
                {word_requirement}
                - BAO GỒM SỐ LIỆU CỤ THỂ
                - KHÔNG DÙNG CỤM TỪ GIỚI THIỆU
                - TRÌNH BÀY THÔNG TIN CỐT LÕI NHẤT
                - BẮT ĐẦU TRỰC TIẾP BẰNG NỘI DUNG CHÍNH
                
                Ví dụ: Lạm phát tháng 12 tăng 3,2% so với cùng kỳ. Giá xăng dầu giảm 5% trong tuần qua. GDP quý 4 tăng trưởng 6,8%.
            """
    
    # Thử tối đa 3 lần để có được kết quả trong khoảng 30-40 từ
    max_attempts = 3
    
    for attempt in range(1, max_attempts + 1):
        try:
            prompt = create_prompt(attempt)
            result = generate_content_with_model_dict(model_dict, prompt)
            
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
    return generate_content_with_model_dict(model_dict, create_prompt())

def analyze_news_impact(model_dict, news_df):
    # --- Cấu hình ---
    VALID_IMPACTS = {"Tích cực", "Tiêu cực", "Trung lập"} # Dùng set để kiểm tra nhanh hơn (O(1))
    DEFAULT_IMPACT = "Trung lập"
    num_news = len(news_df)

    if num_news == 0:
        return []

    # --- Prompt Engineering ---
    system_prompt = """
    Bạn là một chuyên gia phân tích thị trường chứng khoán Việt Nam.
    Nhiệm vụ của bạn là đánh giá tác động của tin tức đến thị trường chứng khoán Việt Nam.

    Hãy phân loại mỗi tin tức thành 1 trong 3 loại:
    - "Tích cực": Tin tức có tác động tích cực đến thị trường chứng khoán VN.
    - "Tiêu cực": Tin tức có tác động tiêu cực đến thị trường chứng khoán VN.
    - "Trung lập": Tin tức không có tác động rõ ràng hoặc cân bằng.

    Chỉ trả về kết quả theo format: Tích cực|Tiêu cực|Trung lập|...
    Không giải thích, chỉ trả về danh sách phân loại cách nhau bởi dấu |
    """

    # Dùng list comprehension để tạo danh sách tin tức ngắn gọn hơn
    news_items = [
        f"Tin {idx + 1}:\nTiêu đề: {row['title']}\nNội dung: {row['content']}"
        for idx, row in news_df.iterrows()
    ]
    full_prompt = system_prompt + "\n\nDanh sách tin tức cần phân tích:\n\n" + "\n\n".join(news_items)

    # --- Gọi API và Xử lý kết quả ---
    try:
        response = generate_content_with_model_dict(model_dict, full_prompt)
        raw_impacts = [item.strip() for item in response.strip().split('|')]

        # Cảnh báo nếu số lượng không khớp
        if len(raw_impacts) != num_news:
            print(f"Cảnh báo: Số lượng kết quả ({len(raw_impacts)}) không khớp với số tin tức ({num_news})")

        # Hợp nhất việc kiểm tra độ dài và xác thực giá trị vào một vòng lặp
        cleaned_impacts = []
        for i in range(num_news):
            # Lấy kết quả từ AI nếu có, ngược lại dùng giá trị mặc định
            impact = raw_impacts[i] if i < len(raw_impacts) else DEFAULT_IMPACT
            
            # Xác thực giá trị, nếu không hợp lệ thì dùng giá trị mặc định
            if impact not in VALID_IMPACTS:
                if i < len(raw_impacts): # Chỉ in cảnh báo cho giá trị thực sự không hợp lệ
                    print(f"Giá trị không hợp lệ '{impact}', thay thế bằng '{DEFAULT_IMPACT}'")
                impact = DEFAULT_IMPACT
            
            cleaned_impacts.append(impact)
            
        return cleaned_impacts

    except Exception as e:
        print(f"Lỗi khi gọi API Gemini: {e}")
        return [DEFAULT_IMPACT] * num_news
    
def identify_major_news(model_dict, news_df: pd.DataFrame) -> pd.DataFrame:
    # Tạo sẵn cột mới với giá trị mặc định là chuỗi rỗng
    news_df['major_news'] = ''
    
    # Danh sách để thu thập tất cả các index của tin tức nổi bật
    major_news_indices = []

    # Bắt đầu gom nhóm theo 'news_type'
    for news_type, group_df in news_df.groupby('news_type'):
        if group_df.empty:
            continue

        # 1. Xác định số lượng tin cần chọn
        num_to_select = 2 if news_type == 'doanh_nghiep' else 1
        
        # Nếu số tin trong nhóm ít hơn số cần chọn, chỉ cần chọn hết
        if len(group_df) <= num_to_select:
            major_news_indices.extend(group_df.index.tolist())
            continue

        # 2. Tối ưu hóa Prompt cho từng nhóm
        # Yêu cầu AI đóng vai một biên tập viên tài chính
        prompt_header = f"""
        Bạn là một biên tập viên tin tức tài chính kinh tế giàu kinh nghiệm tại Việt Nam.
        Nhiệm vụ của bạn là chọn ra {num_to_select} tin tức quan trọng và có ảnh hưởng nhất từ danh sách dưới đây, thuộc chuyên mục '{news_type}'.

        Tiêu chí để lựa chọn tin nổi bật:
        - Tác động vĩ mô, ảnh hưởng rộng đến thị trường chung hoặc một ngành lớn.
        - Thông tin về chính sách quan trọng của chính phủ, Ngân hàng Nhà nước.
        - Sự kiện lớn của các doanh nghiệp đầu ngành (blue-chip), M&A, kết quả kinh doanh đột biến.
        - Các xu hướng đầu tư mới, dòng tiền lớn.

        Dưới đây là danh sách các tin tức. Mỗi tin có một ID duy nhất.
        """

        # Tạo danh sách tin tức kèm ID (là index của DataFrame)
        news_list_str = []
        for idx, row in group_df.iterrows():
            news_item = (
                f"[Tin tức ID: {idx}]\n"
                f"Tiêu đề: {row['title']}\n"
                f"Nội dung: {row['content']}\n"
            )
            news_list_str.append(news_item)

        prompt_footer = f"""
        ---
        YÊU CẦU: Dựa trên các tiêu chí trên, hãy đọc và so sánh tất cả các tin tức.
        Sau đó, chỉ trả về DUY NHẤT ID của {num_to_select} tin tức nổi bật nhất.
        
        Format trả về: Chỉ gồm các con số ID, cách nhau bởi dấu phẩy, không có bất kỳ giải thích hay ký tự nào khác.
        Ví dụ: 4,25
        """
        
        full_prompt = prompt_header + "\n".join(news_list_str) + prompt_footer

        # 3. Gọi AI và xử lý kết quả
        try:
            response = generate_content_with_model_dict(model_dict, full_prompt)
            selected_ids = [int(id_str) for id_str in re.findall(r'\d+', response)]
            major_news_indices.extend(selected_ids)

        except Exception as e:
            print(f"Lỗi khi lựa chọn tin chính của nhóm '{news_type}': {e}")

    # 4. Cập nhật DataFrame với tất cả các tin nổi bật đã thu thập
    if major_news_indices:
        # Dùng .loc để gán giá trị tại các index đã được chọn
        news_df.loc[major_news_indices, 'major_news'] = 'x'
    
    return news_df['major_news']