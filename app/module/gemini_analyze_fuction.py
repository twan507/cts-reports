import sys
import os

sys.path.append(os.path.join(os.path.dirname(os.getcwd()), "import"))

from import_default import *
from import_database import *
from import_other import *
from import_gemini import *

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
        response_text = generate_content_with_model_dict(model_dict, full_prompt, 'analyze_news_impact')

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

    
def identify_major_selected(model_dict, news_df: pd.DataFrame) -> pd.DataFrame:
    news_df = news_df.copy()
    # Tạo sẵn cột mới với giá trị mặc định là chuỗi rỗng
    news_df['major_selected'] = ''
    
    # Danh sách để thu thập tất cả các index của tin tức nổi bật
    major_selected_indices = []

    # Bắt đầu gom nhóm theo 'news_type'
    for news_type, group_df in news_df.groupby('news_type'):
        if group_df.empty:
            continue

        # 1. Xác định số lượng tin cần chọn
        num_to_select = 1
        
        # Nếu số tin trong nhóm ít hơn số cần chọn, chỉ cần chọn hết
        if len(group_df) <= num_to_select:
            major_selected_indices.extend(group_df.index.tolist())
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
            response = generate_content_with_model_dict(model_dict, full_prompt, 'identify_major_selected')
            selected_ids = [int(id_str) for id_str in re.findall(r'\d+', response)]
            major_selected_indices.extend(selected_ids)

        except Exception as e:
            print(f"Lỗi khi lựa chọn tin chính của nhóm '{news_type}': {e}")

    # 4. Cập nhật DataFrame với tất cả các tin nổi bật đã thu thập
    if major_selected_indices:
        # Dùng .loc để gán giá trị tại các index đã được chọn
        news_df.loc[major_selected_indices, 'major_selected'] = 'x'
    
    return news_df['major_selected']

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
        response = generate_content_with_model_dict(model_dict, full_prompt, 'analyze_news_sectors')
        
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
    
def get_filtered_news_index(model_dict, news_df, num_articles, max_retry=5):
    news_titles_str = news_df[['title', 'content']].to_csv(index=True, sep='|', header=False, lineterminator='\\n')

    prompt = f"""
        Từ dữ liệu văn bản tôi cung cấp dưới đây, hãy thực hiện quy trình phân loại và chắt lọc theo các hướng dẫn chi tiết sau:

        1. Mô tả Dữ liệu đầu vào:
        Dữ liệu đầu vào là một khối văn bản. Mỗi dòng có định dạng "index|title|content".

        2. Quy trình Thực hiện:

        Bước A: Phân loại toàn bộ các tiêu đề vào 3 nhóm: `trong_nuoc`, `quoc_te`, `doanh_nghiep`.
        - `trong_nuoc`: Tin kinh tế vĩ mô, chính sách, pháp luật tại việt nam Việt Nam.
        - `quoc_te`: Tin kinh tế, tài chính, chính trị của các khu vực khác thế giới.
        - `doanh_nghiep`: Tin về một doanh nghiệp, tập đoàn cụ thể có niêm yết trên thị trường chứng khoán Việt Nam.

        Bước B: Loại bỏ các tin có nội dung trùng lặp. Giữ lại duy nhất một tiêu đề đại diện, tổng quát nhất cho mỗi chủ đề.

        Bước C: Chắt lọc {num_articles} tin nổi bật nhất từ mỗi nhóm sau khi đã loại trùng lặp.
        - `trong_nuoc`: Ưu tiên tin chính sách tiền tệ (lãi suất, tỷ giá), tài khóa, GDP và chỉ số chứng khoán (VNINDEX) **ở Việt Nam**. Tuyệt đối loại bỏ các tin tức không liên quan tới Việt Nam.
        - `quoc_te`: Ưu tiên tin từ Fed, ECB, kinh tế Mỹ, Trung Quốc. Tuyệt đối loại bỏ các tin tức trực tiếp nhắc tới việt nam.
        - `doanh_nghiep`: Ưu tiên tin về dự án lớn, kết quả kinh doanh kỷ lục, các vụ việc pháp lý lớn của một công ty niêm yết nổi tiếng (có cổ phiếu được nhiều sự quan tâm và thanh khoản lớn) và cụ thể (không phải nhiều công ty cùng lúc)

        3. Định dạng Kết quả đầu ra:
        - Kết quả cuối cùng BẮT BUỘC phải là một đối tượng JSON (JSON object) hợp lệ.
        - Đối tượng JSON này phải có 3 khóa (key) chính xác là: "trong_nuoc", "quoc_te", và "doanh_nghiep".
        - Giá trị (value) của mỗi khóa là một mảng (array) chứa đúng {num_articles} số nguyên là index của các bài báo đã chọn.
        - TUYỆT ĐỐI KHÔNG bao gồm bất kỳ giải thích, ghi chú, hay ký tự nào khác ngoài đối tượng JSON này.

        - Ví dụ về định dạng kết quả đầu ra mong muốn:
        ```json
        {{
         "trong_nuoc": [0, 5, 12],
         "quoc_te": [25, 30, 41],
         "doanh_nghiep": [55, 67, 88]
        }}
        ```

        Dữ liệu thô đầu vào:
        {news_titles_str}
    """
    
    # --- Bước 2: Gọi AI, xử lý và xác thực kết quả ---
    for i in range(max_retry):
        response_string = generate_content_with_model_dict(model_dict, prompt, 'get_filtered_news_index')
        match = re.search(r'\{[\s\S]*\}', response_string)
        if not match:
            continue
        json_string = match.group(0)
        data = json.loads(json_string)
        required_keys = {"trong_nuoc", "quoc_te", "doanh_nghiep"}
        if not required_keys.issubset(data.keys()):
            raise ValueError("Kết quả JSON thiếu các key bắt buộc.")

        if not all(isinstance(data[key], list) and len(data[key]) == num_articles for key in required_keys):
            raise ValueError(f"Mỗi danh sách trong JSON phải là một mảng chứa đúng {num_articles} phần tử.")
        return data

    raise ValueError(f"Không thể nhận được kết quả hợp lệ từ AI sau {max_retry} lần thử!")

def get_weekly_top_news(model_dict, news_df, news_type, num_articles, max_retry=10):
    """
    Chọn ra đúng num_articles tin nổi bật nhất toàn bộ (không phân nhóm), trả về list index.
    """
    for _ in range(max_retry):
        prompt = f"""
            Từ dữ liệu văn bản tôi cung cấp dưới đây, hãy thực hiện quy trình chọn lọc theo các hướng dẫn chi tiết sau:

            1. Dữ liệu đầu vào:
            - Là một khối văn bản, mỗi dòng gồm chỉ số index gốc, tiêu đề tin tức và đánh giá impact của tin tức, index này có thể không liên tiếp và không bắt đầu từ 0.

            2. Quy trình thực hiện:

            Bước A: Loại bỏ các tin có cùng một nội dung hoặc chủ đề.
            - Nếu có nhiều tiêu đề cùng nói về một sự kiện, chính sách, doanh nghiệp, số liệu, hoặc chỉ khác nhau về cách diễn đạt, ngày tháng, số liệu chi tiết… thì chỉ giữ lại duy nhất một tiêu đề nổi bật nhất, đầy đủ, tổng quát, đại diện cho chủ đề đó.
            - Không chọn các tiêu đề chỉ khác nhau về thời gian, số liệu, hoặc chỉ là bản cập nhật/bổ sung của cùng một chủ đề.
            - Ưu tiên giữ lại tiêu đề tổng hợp, khái quát, có giá trị thông tin cao nhất. Loại bỏ các tiêu đề còn lại bị trùng lặp về nội dung hoặc chỉ là bản cập nhật/bổ sung.

            Bước B: Chọn ra đúng {num_articles} tiêu đề tin tức nổi bật nhất so với tất cả các tin còn lại.
            - Ưu tiên các tin có tác động lớn đến kinh tế vĩ mô, chính sách, thị trường tài chính, các sự kiện quốc tế quan trọng, hoặc các doanh nghiệp lớn có ảnh hưởng mạnh.
            - Ưu tiên các tin có tính mới, độc đáo, ảnh hưởng rộng, hoặc liên quan đến các quyết định chính sách lớn, các sự kiện bất thường, các số liệu kinh tế quan trọng, hoặc các sự kiện doanh nghiệp quy mô lớn.
            - Không chọn các tin chỉ mang tính cập nhật nhỏ, lặp lại, hoặc không có tác động rõ rệt.
            - **Lưu ý quan trọng: Không được chọn quá 3 tin cùng một loại impact (Tích cực, Tiêu cực, Trung lập). Nếu có nhiều hơn 3 tin cùng loại impact, chỉ chọn tối đa 3 tin thuộc loại đó.**

            3. Định dạng kết quả đầu ra:
            - Chỉ trả về một dãy số gồm đúng {num_articles} số nguyên, mỗi số là index của các tiêu đề nổi bật nhất đã được chọn ở Bước B.
            - Các số cách nhau bằng dấu phẩy, không có ký tự hoặc giải thích nào khác.

            - Ví dụ về định dạng kết quả đầu ra:
            0,5,12,25,30

            Yêu cầu cuối cùng: Vui lòng chỉ trả về duy nhất dãy số theo đúng định dạng trên, không giải thích gì thêm.

            (Dữ liệu thô đầu vào ở phía bên dưới dòng này)
            {news_df[news_df['news_type'] == news_type][['title', 'impact']].to_csv(index=True, sep='|', lineterminator='\\n')}
        """
        news_index_string = generate_content_with_model_dict(model_dict, prompt, 'get_weekly_top_news')
        news_index_string = news_index_string.strip().replace('\n', '').replace(' ', '')
        pattern = rf'^(\d+,){{{num_articles-1}}}\d+$'
        if re.match(pattern, news_index_string):
            index_list = [int(x) for x in news_index_string.split(',')]
            if len(index_list) == num_articles:
                return index_list
    raise ValueError(f"get_weekly_top_news trả về kết quả không đúng định dạng sau {max_retry} lần thử!")

def get_daily_top_news(model_dict, news_df, news_type, num_articles, max_retry=10):
    """
    Chọn ra đúng num_articles tin nổi bật nhất toàn bộ (không phân nhóm), trả về list index.
    """
    for _ in range(max_retry):
        prompt = f"""
            Từ dữ liệu văn bản tôi cung cấp dưới đây, hãy thực hiện quy trình chọn lọc theo các hướng dẫn chi tiết sau:

            1. Dữ liệu đầu vào:
            - Là một khối văn bản, mỗi dòng gồm chỉ số index gốc, tiêu đề tin tức và đánh giá impact của tin tức, index này có thể không liên tiếp và không bắt đầu từ 0.

            2. Quy trình thực hiện:

            Bước A: Loại bỏ các tin có cùng một nội dung hoặc chủ đề.
            - Nếu có nhiều tiêu đề cùng nói về một sự kiện, chính sách, doanh nghiệp, số liệu, hoặc chỉ khác nhau về cách diễn đạt, ngày tháng, số liệu chi tiết… thì chỉ giữ lại duy nhất một tiêu đề nổi bật nhất, đầy đủ, tổng quát, đại diện cho chủ đề đó.
            - Không chọn các tiêu đề chỉ khác nhau về thời gian, số liệu, hoặc chỉ là bản cập nhật/bổ sung của cùng một chủ đề.
            - Ưu tiên giữ lại tiêu đề tổng hợp, khái quát, có giá trị thông tin cao nhất. Loại bỏ các tiêu đề còn lại bị trùng lặp về nội dung hoặc chỉ là bản cập nhật/bổ sung.

            Bước B: Chọn ra đúng {num_articles} tiêu đề tin tức nổi bật nhất so với tất cả các tin còn lại.
            - Ưu tiên các tin có tác động lớn đến kinh tế vĩ mô, chính sách, thị trường tài chính, các sự kiện quốc tế quan trọng, hoặc các doanh nghiệp lớn có ảnh hưởng mạnh.
            - Ưu tiên các tin có tính mới, độc đáo, ảnh hưởng rộng, hoặc liên quan đến các quyết định chính sách lớn, các sự kiện bất thường, các số liệu kinh tế quan trọng, hoặc các sự kiện doanh nghiệp quy mô lớn.
            - Không chọn các tin chỉ mang tính cập nhật nhỏ, lặp lại, hoặc không có tác động rõ rệt.
            - **Lưu ý quan trọng: Không được chọn quá 2 tin cùng một loại impact (Tích cực, Tiêu cực, Trung lập). Nếu có nhiều hơn 3 tin cùng loại impact, chỉ chọn tối đa 3 tin thuộc loại đó.**

            3. Định dạng kết quả đầu ra:
            - Chỉ trả về một dãy số gồm đúng {num_articles} số nguyên, mỗi số là index của các tiêu đề nổi bật nhất đã được chọn ở Bước B.
            - Các số cách nhau bằng dấu phẩy, không có ký tự hoặc giải thích nào khác.

            - Ví dụ về định dạng kết quả đầu ra:
            12,25,30

            Yêu cầu cuối cùng: Vui lòng chỉ trả về duy nhất dãy số theo đúng định dạng trên, không giải thích gì thêm.

            (Dữ liệu thô đầu vào ở phía bên dưới dòng này)
            {news_df[(news_df['news_type'] == news_type) & (news_df['major_selected'] != 'x')][['title', 'impact']].to_csv(index=True, sep='|', lineterminator='\\n')}
        """
        news_index_string = generate_content_with_model_dict(model_dict, prompt, 'get_daily_top_news')
        news_index_string = news_index_string.strip().replace('\n', '').replace(' ', '')
        pattern = rf'^(\d+,){{{num_articles-1}}}\d+$'
        if re.match(pattern, news_index_string):
            index_list = [int(x) for x in news_index_string.split(',')]
            if len(index_list) == num_articles:
                return index_list
    raise ValueError(f"get_daily_top_news trả về kết quả không đúng định dạng sau {max_retry} lần thử!")