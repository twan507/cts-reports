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
    final_selection = [opt['name'] for opt in candidates]

    # Bước 5: Trích xuất tên model đã được sắp xếp
    return final_selection + select_fast_models(get_gemini_models())

def generate_content_with_model_dict(
    model_dict: Dict[str, genai.GenerativeModel], 
    prompt: str,
    retries_per_model: int = 2
) -> str:
    """
    Tạo nội dung với danh sách model, tự động fallback và thử lại.
    Hàm này được cấu hình để nới lỏng các bộ lọc an toàn.

    Args:
        model_dict: Dictionary chứa tên model và đối tượng model đã khởi tạo.
        prompt: Nội dung prompt để gửi đến model.
        retries_per_model: Số lần thử lại cho mỗi model trước khi chuyển sang model tiếp theo.

    Returns:
        Nội dung text từ model đầu tiên thành công.

    Raises:
        Exception: Nếu tất cả các model đều thất bại sau tất cả các lần thử lại.
    """
    # Cấu hình nới lỏng bộ lọc an toàn, sẽ được áp dụng cho mọi lệnh gọi API
    safety_settings = {
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
    }

    # Lặp qua từng model trong danh sách
    for model_name, model_instance in model_dict.items():
        # Thử lại nhiều lần cho cùng một model trước khi bỏ cuộc
        for attempt in range(retries_per_model):
            try:
                response = model_instance.generate_content(
                    prompt,
                    safety_settings=safety_settings
                )

                # KIỂM TRA QUAN TRỌNG: Chỉ truy cập .text nếu có nội dung trả về
                if response.parts:
                    return response.text
                else:
                    # Xử lý trường hợp phản hồi bị chặn (RECITATION, SAFETY,...)
                    reason = "Unknown"
                    if response.prompt_feedback and response.prompt_feedback.block_reason:
                        reason = response.prompt_feedback.block_reason.name
                    print(f"CẢNH BÁO: Model '{model_name}' lỗi lần {attempt+1}/{retries_per_model}. Lý do: {reason}.")
                    time.sleep(1) # Chờ một chút trước khi thử lại
            except Exception as e:
                time.sleep(1) # Chờ một chút trước khi thử lại

    # Nếu tất cả model đều thất bại sau tất cả các lần thử
    raise Exception("❌ Tất cả model trong danh sách đều đã thất bại.")

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
            result = generate_content_with_model_dict(model_dict, prompt)
            
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
    return generate_content_with_model_dict(model_dict, create_prompt())

def analyze_news_impact(model_dict, news_df):
    """
    Phân tích tác động của tin tức, được viết lại theo cấu trúc của hàm
    phân tích lĩnh vực để tăng độ ổn định.
    """
    num_news = len(news_df)
    if num_news == 0:
        return []
        
    VALID_IMPACTS = {"Tích cực", "Tiêu cực", "Trung lập"}
    DEFAULT_IMPACT = "Trung lập"

    # --- Prompt Engineering: Áp dụng cấu trúc prompt của hàm chạy ổn định ---
    system_prompt = """
Bạn là một chuyên gia phân tích thị trường chứng khoán (TTCK) Việt Nam.
Nhiệm vụ của bạn là phân loại tác động của mỗi tin tức sau đây.

### HƯỚNG DẪN ###
1. Phân loại mỗi tin tức vào 1 trong 3 nhóm: "Tích cực", "Tiêu cực", hoặc "Trung lập".
2. "Tích cực": Tin có lợi cho thị trường chung.
3. "Tiêu cực": Tin có hại cho thị trường chung.
4. "Trung lập": Tin không ảnh hưởng rõ ràng hoặc tin tức nhân sự, xã hội.

### QUY TẮC FORMAT ĐẦU RA (RẤT QUAN TRỌNG) ###
- Chỉ trả về kết quả theo format: Phân loại 1|Phân loại 2|Phân loại 3|...
- Mỗi tin tức được phân tách bằng dấu gạch đứng `|`.
- Tuyệt đối KHÔNG giải thích, KHÔNG thêm ghi chú, chỉ trả về chuỗi kết quả.
    """

    news_items = [
        f"Tin {idx + 1}:\nTiêu đề: {row['title']}\nNội dung: {row['content']}"
        for idx, row in news_df.iterrows()
    ]
    full_prompt = system_prompt + "\n\n--- DANH SÁCH TIN TỨC CẦN PHÂN TÍCH ---\n\n" + "\n\n".join(news_items)

    # --- Gọi API và Xử lý kết quả: Mô phỏng logic của hàm chạy ổn định ---
    try:
        # Luôn sử dụng hàm gọi API mạnh mẽ nhất
        response_text = generate_content_with_model_dict(model_dict, full_prompt)
        
        if not response_text:
            print("Lỗi: Không nhận được phản hồi từ API. Trả về giá trị mặc định.")
            return [DEFAULT_IMPACT] * num_news

        # Tách kết quả cho từng tin tức
        raw_impacts = [item.strip() for item in response_text.strip().split('|')]

        processed_impacts = []
        for i in range(num_news):
            # Lấy kết quả nếu có, nếu không thì dùng giá trị rỗng để xử lý ở bước sau
            impact_value = raw_impacts[i] if i < len(raw_impacts) else ""
            
            # Kiểm tra tính hợp lệ, nếu không hợp lệ hoặc rỗng thì dùng default
            if impact_value in VALID_IMPACTS:
                processed_impacts.append(impact_value)
            else:
                if impact_value != "": # Chỉ in cảnh báo nếu AI trả về giá trị sai
                    print(f"Giá trị không hợp lệ '{impact_value}', thay thế bằng '{DEFAULT_IMPACT}'")
                processed_impacts.append(DEFAULT_IMPACT)
                
        return processed_impacts

    except Exception as e:
        print(f"Lỗi nghiêm trọng khi gọi API hoặc xử lý dữ liệu: {e}")
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
        num_to_select = 1
        
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

def analyze_news_sectors(model_dict, news_df):
    """
    Phân tích tin tức để tự động xác định các lĩnh vực/ngành bị ảnh hưởng 
    mà không cần một danh sách định trước.

    Args:
        model_dict (dict): Dictionary chứa thông tin về mô hình ngôn ngữ.
        news_df (pd.DataFrame): DataFrame chứa tin tức với các cột 'title' và 'content'.

    Returns:
        list: Một danh sách các chuỗi, mỗi chuỗi chứa các lĩnh vực được phân loại 
              cho một tin tức, cách nhau bởi dấu phẩy. Trả về danh sách rỗng nếu
              không có tin tức đầu vào.
    """
    num_news = len(news_df)
    if num_news == 0:
        return []

    # --- Prompt Engineering (Linh hoạt hơn) ---
    # Prompt mới không đưa ra danh sách cứng mà hướng dẫn AI tự xác định
    system_prompt = """
    Bạn là một chuyên gia phân tích thị trường chứng khoán Việt Nam với kiến thức sâu rộng về các ngành kinh tế.
    Nhiệm vụ của bạn là xác định (các) lĩnh vực hoặc ngành nghề kinh tế chính mà mỗi tin tức sau đây đề cập đến.

    HƯỚNG DẪN:
    1. Với mỗi tin tức, hãy liệt kê tất cả các lĩnh vực/ngành nghề bị ảnh hưởng.
    2. Sử dụng thuật ngữ kinh tế phổ biến và chính xác của Việt Nam (ví dụ: 'Ngân hàng', 'Bất động sản', 'Thép', 'Năng lượng tái tạo', 'Logistics').
    3. Nếu một tin tức có ảnh hưởng rộng đến toàn bộ nền kinh tế hoặc thị trường chứng khoán, hãy sử dụng 'Toàn thị trường'.
    
    QUY TẮC FORMAT ĐẦU RA (RẤT QUAN TRỌNG):
    - Chỉ trả về kết quả theo format: Lĩnh vực A, Lĩnh vực B|Lĩnh vực C|Lĩnh vực D, Lĩnh vực E|...
    - Mỗi tin tức được phân tách bằng dấu gạch đứng `|`.
    - Trong mỗi tin tức, các lĩnh vực khác nhau được phân tách bằng dấu phẩy `,`.
    - Không giải thích, không thêm ghi chú, chỉ trả về chuỗi kết quả.
    """

    # Tạo danh sách tin tức để đưa vào prompt
    news_items = [
        f"Tin {idx + 1}:\nTiêu đề: {row['title']}\nNội dung: {row['content']}"
        for idx, row in news_df.iterrows()
    ]
    full_prompt = system_prompt + "\n\n--- DANH SÁCH TIN TỨC CẦN PHÂN TÍCH ---\n\n" + "\n\n".join(news_items)

    # --- Gọi API và Xử lý kết quả ---
    try:
        response = generate_content_with_model_dict(model_dict, full_prompt)
        
        # Tách kết quả cho từng tin tức
        raw_sectors_per_news = [item.strip() for item in response.strip().split('|')]

        processed_sectors = []
        for i in range(num_news):
            if i < len(raw_sectors_per_news) and raw_sectors_per_news[i]:
                # Tách các lĩnh vực, làm sạch khoảng trắng, và loại bỏ các mục rỗng
                sectors = [sector.strip() for sector in raw_sectors_per_news[i].split(',') if sector.strip()]
                
                # Loại bỏ các lĩnh vực trùng lặp trong cùng một tin tức nhưng vẫn giữ nguyên thứ tự
                unique_sectors = list(dict.fromkeys(sectors))
                
                processed_sectors.append(', '.join(unique_sectors))
            else:
                # Nếu AI không trả về gì cho tin tức này, hoặc không có đủ kết quả
                processed_sectors.append('') # Thêm chuỗi rỗng để chỉ ra không có lĩnh vực nào được xác định

        return processed_sectors

    except Exception as e:
        print(f"Lỗi nghiêm trọng khi gọi API hoặc xử lý dữ liệu: {e}")
        # Trả về danh sách các chuỗi rỗng có độ dài bằng số tin tức khi có lỗi
        return [''] * num_news
    
def get_filtered_news_index(model_dict, news_df, num_articles, max_retry=3):
    for _ in range(max_retry):
        prompt = f"""
            Từ dữ liệu văn bản tôi cung cấp dưới đây, hãy thực hiện quy trình phân loại và chắt lọc theo các hướng dẫn chi tiết sau:

            1. Mô tả Dữ liệu đầu vào:
            Dữ liệu đầu vào là một khối văn bản (text block). Mỗi dòng trong khối văn bản này là một tiêu đề tin tức riêng biệt, có thể nằm trong dấu ngoặc kép. Các tiêu đề được đánh chỉ số (index) theo thứ tự xuất hiện một cách tự nhiên, bắt đầu từ 0 cho dòng đầu tiên.

            2. Quy trình Thực hiện:

            Bước A: Phân loại toàn bộ các tiêu đề.
            Hãy đọc từng tiêu đề và phân chúng vào 3 nhóm sau:
            - Nhóm 1 (`trong_nuoc`): Các tin tức về kinh tế vĩ mô, chính sách, pháp luật, và các sự kiện chung trong phạm vi Việt Nam.
            - Nhóm 2 (`quoc_te`): Các tin tức về kinh tế, chính trị, tài chính diễn ra bên ngoài Việt Nam.
            - Nhóm 3 (`doanh_nghiep`): Các tin tức liên quan đến một doanh nghiệp, tập đoàn cụ thể tại Việt Nam, đặc biệt ưu tiên các doanh nghiệp có mã chứng khoán niêm yết trên sàn.

            Bước B: Loại bỏ các tin có cùng một nội dung hoặc chủ đề.
            - Nếu có nhiều tiêu đề cùng nói về một sự kiện, chính sách, doanh nghiệp, số liệu, hoặc chỉ khác nhau về cách diễn đạt, ngày tháng, số liệu chi tiết… thì chỉ giữ lại duy nhất một tiêu đề nổi bật nhất, đầy đủ, tổng quát, đại diện cho chủ đề đó.
            - Không chọn các tiêu đề chỉ khác nhau về thời gian, số liệu, hoặc chỉ là bản cập nhật/bổ sung của cùng một chủ đề.
            - Ưu tiên giữ lại tiêu đề tổng hợp, khái quát, có giá trị thông tin cao nhất. Loại bỏ các tiêu đề còn lại bị trùng lặp về nội dung hoặc chỉ là bản cập nhật/bổ sung.

            Bước C: Chắt lọc {num_articles} tin nổi bật nhất từ mỗi nhóm.
            Sau khi đã phân loại, từ mỗi nhóm hãy chọn ra đúng {num_articles} tiêu đề quan trọng và có tác động mạnh mẽ nhất dựa trên các tiêu chí ưu tiên sau:
            - Đối với nhóm `trong_nuoc`: Ưu tiên tin về chính sách tiền tệ (lãi suất, tỷ giá), chính sách tài khóa, văn bản pháp quy mới, dự báo GDP, và các sự kiện trọng yếu của thị trường chứng khoán (VN-Index lập đỉnh, thông tin nâng hạng).
            - Đối với nhóm `quoc_te`: Ưu tiên tin về quyết định của các ngân hàng trung ương lớn (Fed, ECB), kinh tế các quốc gia hàng đầu (Mỹ, Trung Quốc), căng thẳng/thỏa thuận thương mại toàn cầu.
            - Đối với nhóm `doanh_nghiep`: Ưu tiên tin về một doanh nghiệp niêm yết cụ thể có tác động lớn: dự án đầu tư ngàn tỷ, kết quả kinh doanh kỷ lục, các vụ việc pháp lý lớn (bồi thường, thanh tra). Tránh các tin nói về cùng lúc nhiều doanh nghiệp hoặc chỉ là thông tin chung chung về ngành.

            3. Định dạng Kết quả đầu ra:

            - Kết quả cuối cùng phải là một dãy số gồm đúng {num_articles*3} số nguyên, mỗi số là index (bắt đầu từ 0) của các tiêu đề nổi bật đã được chọn ở Bước B.
            - Thứ tự các số như sau: {num_articles} index của nhóm `trong_nuoc` trước, tiếp theo là {num_articles} index của nhóm `quoc_te`, cuối cùng là {num_articles} index của nhóm `doanh_nghiep`.
            - Các số cách nhau bằng dấu phẩy, không có ký tự hoặc giải thích nào khác.

            - Ví dụ về định dạng kết quả đầu ra:
            0,5,12,25,30,41,55,67,88,92,2,8,15,16,22,31,49,50,71,80,1,3,9,11,23,33,45,66,77,99

            Yêu cầu cuối cùng: Vui lòng chỉ trả về duy nhất dãy số theo đúng định dạng trên, không giải thích gì thêm.

            (Dữ liệu thô đầu vào ở phía bên dưới dòng này)
            {news_df['title'].to_csv(index=False, sep='|', lineterminator='\\n')}
        """
        news_index_string = generate_content_with_model_dict(model_dict, prompt)
        # Chuẩn hóa chuỗi trả về
        news_index_string = news_index_string.strip().replace('\n', '').replace(' ', '')
        # Regex kiểm tra đúng định dạng: đúng num_articles*3 số nguyên, phân tách bằng dấu phẩy, không ký tự thừa
        pattern = rf'^(\d+,){{{num_articles*3-1}}}\d+$'
        if re.match(pattern, news_index_string):
            index_list = [int(x) for x in news_index_string.split(',')]
            if len(index_list) == num_articles * 3:
                return {
                    "trong_nuoc": index_list[:num_articles],
                    "quoc_te": index_list[num_articles:2*num_articles],
                    "doanh_nghiep": index_list[2*num_articles:3*num_articles]
                }
    # Nếu sau max_retry lần vẫn không đúng, raise error
    raise ValueError(f"get_filtered_news_index trả về kết quả không đúng định dạng sau {max_retry} lần thử!")

def get_top_news_index(model_dict, news_df, news_type, num_articles, max_retry=10):
    """
    Chọn ra đúng num_articles tin nổi bật nhất toàn bộ (không phân nhóm), trả về list index.
    """
    for _ in range(max_retry):
        prompt = f"""
            Từ dữ liệu văn bản tôi cung cấp dưới đây, hãy thực hiện quy trình chọn lọc theo các hướng dẫn chi tiết sau:

            1. Dữ liệu đầu vào:
            - Là một khối văn bản, mỗi dòng gồm chỉ số index gốc và tiêu đề tin tức, index này có thể không liên tiếp và không bắt đầu từ 0.

            2. Quy trình thực hiện:

            Bước A: Loại bỏ các tin có cùng một nội dung hoặc chủ đề.
            - Nếu có nhiều tiêu đề cùng nói về một sự kiện, chính sách, doanh nghiệp, số liệu, hoặc chỉ khác nhau về cách diễn đạt, ngày tháng, số liệu chi tiết… thì chỉ giữ lại duy nhất một tiêu đề nổi bật nhất, đầy đủ, tổng quát, đại diện cho chủ đề đó.
            - Không chọn các tiêu đề chỉ khác nhau về thời gian, số liệu, hoặc chỉ là bản cập nhật/bổ sung của cùng một chủ đề.
            - Ưu tiên giữ lại tiêu đề tổng hợp, khái quát, có giá trị thông tin cao nhất. Loại bỏ các tiêu đề còn lại bị trùng lặp về nội dung hoặc chỉ là bản cập nhật/bổ sung.

            Bước B: Chọn ra đúng {num_articles} tiêu đề tin tức nổi bật nhất so với tất cả các tin còn lại.
            - Ưu tiên các tin có tác động lớn đến kinh tế vĩ mô, chính sách, thị trường tài chính, các sự kiện quốc tế quan trọng, hoặc các doanh nghiệp lớn có ảnh hưởng mạnh.
            - Ưu tiên các tin có tính mới, độc đáo, ảnh hưởng rộng, hoặc liên quan đến các quyết định chính sách lớn, các sự kiện bất thường, các số liệu kinh tế quan trọng, hoặc các sự kiện doanh nghiệp quy mô lớn.
            - Không chọn các tin chỉ mang tính cập nhật nhỏ, lặp lại, hoặc không có tác động rõ rệt.

            3. Định dạng kết quả đầu ra:
            - Chỉ trả về một dãy số gồm đúng {num_articles} số nguyên, mỗi số là index của các tiêu đề nổi bật nhất đã được chọn ở Bước B.
            - Các số cách nhau bằng dấu phẩy, không có ký tự hoặc giải thích nào khác.

            - Ví dụ về định dạng kết quả đầu ra:
            0,5,12,25,30

            Yêu cầu cuối cùng: Vui lòng chỉ trả về duy nhất dãy số theo đúng định dạng trên, không giải thích gì thêm.

            (Dữ liệu thô đầu vào ở phía bên dưới dòng này)
            {news_df[news_df['news_type'] == news_type]['title'].to_csv(index=True, sep='|', lineterminator='\\n')}
        """
        news_index_string = generate_content_with_model_dict(model_dict, prompt)
        news_index_string = news_index_string.strip().replace('\n', '').replace(' ', '')
        pattern = rf'^(\d+,){{{num_articles-1}}}\d+$'
        if re.match(pattern, news_index_string):
            index_list = [int(x) for x in news_index_string.split(',')]
            if len(index_list) == num_articles:
                return index_list
    raise ValueError(f"get_top_news_index trả về kết quả không đúng định dạng sau {max_retry} lần thử!")