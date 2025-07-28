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
    function_name: str = "unknown",
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
                    print(f"✅ Model '{model_name}' thành công lần {attempt+1}/{retries_per_model} tại hàm {function_name}.")
                    return response.text
                else:
                    # Xử lý trường hợp phản hồi bị chặn (RECITATION, SAFETY,...)
                    reason = "Unknown"
                    if response.prompt_feedback and response.prompt_feedback.block_reason:
                        reason = response.prompt_feedback.block_reason.name
                    print(f"⚠️ Model '{model_name}' lỗi lần {attempt+1}/{retries_per_model} tại hàm {function_name}. Lý do: {reason}.")
                    time.sleep(1) # Chờ một chút trước khi thử lại
            except Exception as e:
                time.sleep(1) # Chờ một chút trước khi thử lại

    # Nếu tất cả model đều thất bại sau tất cả các lần thử
    raise Exception("❌ Tất cả model trong danh sách đều đã thất bại.")