import sys
import os

sys.path.append(os.path.join(os.path.dirname(os.getcwd()), "import"))

from import_default import *
from import_database import *
from import_other import *
from import_gemini import *

def weekly_news_comment_prompt(df, news_type):
    prompt = f"""
    Bạn là một chuyên viên phân tích thị trường. Dưới đây là bảng dữ liệu các tin tức ngắn, mỗi dòng gồm các trường: [title], [content], [impact], [sectors].

    Nhiệm vụ của bạn:
    - Viết một đoạn văn duy nhất, súc tích, tổng hợp toàn bộ thông tin trong bảng.
    - Đoạn văn phải tuân thủ NGHIÊM NGẶT các quy tắc sau:

    1. Độ dài:
        - Đúng 5 câu.
        - Mỗi câu dài từ 13 đến 15 từ.

    2. Cấu trúc nội dung:
        - Câu 1: Nêu nhận định hoặc xu hướng chính nổi bật nhất từ các tin tức.
        - Câu 2: Trình bày nguyên nhân, động lực hoặc yếu tố tích cực quan trọng nhất hỗ trợ xu hướng đó.
        - Câu 3: Đề cập một khó khăn, rủi ro hoặc thông tin trái ngược mang tính kìm hãm.
        - Câu 4: Mô tả kết quả, hệ quả hoặc ảnh hưởng thực tế đến một lĩnh vực/đối tượng cụ thể.
        - Câu 5: Tổng hợp các ý trên để đưa ra kết luận chung hoặc dự báo xu hướng sắp tới.

    3. Yêu cầu khác:
        - Chỉ sử dụng thông tin trong bảng, không thêm ý ngoài.
        - Tuyệt đối không đề cập đến 1 tin tức cụ thể nào.
        - Chủ đề tập trung vào kinh tế vĩ mô, không quá tập trung vào thị trường chứng khoán.
        - Văn phong khách quan, cân bằng, không cảm tính.
        - Chỉ hiển thị đoạn văn hoàn chỉnh, không lặp lại hướng dẫn.

    Bảng dữ liệu:
    {df[(df['news_type']==news_type) & (df['ai_selected']=='x')][['title', 'content', 'impact', 'sectors']].to_csv(index=False, sep='|', lineterminator='\\n')}
    """

    return prompt

def weekly_data_comment_prompt(df, type_name):
    if type_name == 'vn':
        senerio = """
            Câu 1 (Thị trường chung): Bắt đầu bằng nhận định về chỉ số chính VN-Index, trích dẫn số liệu tăng trưởng tuần (1w_change).
            Câu 2 (Nhóm Cổ phiếu Lớn): Nhận xét về nhóm cổ phiếu blue-chip qua chỉ số VN30, trích dẫn số liệu tăng trưởng tuần (1w_change), nhấn mạnh mức độ biến động và so sánh với VN-Index.
            Câu 3 (Các Chỉ Số Khác): Mô tả xu hướng chung của hai chỉ số HNXINDEX và UPINDEX, trích dẫn số liệu 1w_change của chúng.
            Câu 4 (Thị trường Phái sinh): Nhận xét về thị trường phái sinh, chỉ nhận xét VN30F1M bỏ qua VN30F2M. So sánh điểm số đóng cửa của nó với chỉ số VN30 cơ sở để nêu bật mức chênh lệch (basis).
            Câu 5 (Kết luận): Viết một câu kết luận khách quan để tổng hợp lại bức tranh chung, ví dụ như mức độ lan tỏa của đà tăng hoặc vai trò dẫn dắt của nhóm cổ phiếu nào.
        """
    elif type_name == 'international':
        senerio = """
            Câu 1: Nhận định chung về thị trường chứng khoán toàn cầu trong tuần qua.
            Câu 2: Tập trung vào thị trường Mỹ (DJI, SPX) và trích dẫn số liệu 1w_change.
            Câu 3: Tập trung vào thị trường Châu Âu (FTSE, STOXX50E) và trích dẫn số liệu 1w_change.
            Câu 4: Tập trung vào thị trường Châu Á (N225, SSEC) và trích dẫn số liệu 1w_change.
            Câu 5: Viết một câu kết luận cuối cùng. Câu này phải **hoàn toàn khách quan**, chỉ tổng hợp lại thông tin, **tuyệt đối không đưa ra quan điểm cá nhân hay dự đoán**.
        """
    elif type_name == 'other':
        senerio = """
            Câu 1: Nhận định chung về các loại thị trường trong tuần qua (Crypto, Hàng hóa, Ngoại hối).
            Câu 2: Tập trung vào thị trường Tiền điện tử (BTC, ETH) và trích dẫn số liệu 1w_change.
            Câu 3: Tập trung vào thị trường Hàng hóa (Vàng, Dầu) và trích dẫn số liệu 1w_change.
            Câu 4: Tập trung vào thị trường Ngoại hối (DXY, USD/VND) và trích dẫn số liệu 1w_change.
            Câu 5: Viết một câu kết luận cuối cùng. Câu này phải **hoàn toàn khách quan**, chỉ tổng hợp lại thông tin, **tuyệt đối không đưa ra quan điểm cá nhân hay dự đoán**.
        """

    #Tách bảng lớn ra thành nhiều bảng để AI dễ đọc
    type_df = df[df['type'] == type_name]
    type_dict = {}
    index_list = type_df['ticker'].unique().tolist()
    for index in index_list:
        temp_df = type_df[type_df['ticker'] == index]
        temp_df = temp_df.sort_values('date', ascending=False).reset_index(drop=True)
        type_dict[index] = temp_df.to_csv(index=False, sep='|', lineterminator='\n')

    prompt = f"""
        Dựa vào các bảng dữ liệu được cung cấp dưới đây, hãy viết một đoạn văn nhận xét thị trường:
        Index số 1: {type_dict[index_list[0]]}\n
        Index số 2: {type_dict[index_list[1]]}\n
        Index số 3: {type_dict[index_list[2]]}\n
        Index số 4: {type_dict[index_list[3]]}\n
        Index số 5: {type_dict[index_list[4]]}\n
        Index số 6: {type_dict[index_list[5]]}\n
        ---
        **Yêu cầu BẮT BUỘC:**

        1.  **Định dạng:** Toàn bộ nội dung phải nằm trong **một đoạn văn duy nhất**.
        2.  **Độ dài:** Mỗi câu có độ dài khoảng **20 từ**.
        3.  **Cấu trúc & Nội dung:** Đoạn văn phải có **chính xác 5 câu** theo kịch bản dưới đây.
            {senerio}
        4.  Văn phong & Sáng tạo:
            Mục tiêu: Hành văn phải chuyên nghiệp, trôi chảy và khách quan như một nhà phân tích thị trường, với các nhận định phản ánh đúng bối cảnh của dữ liệu.
            Quy tắc 1: Phân tích Bối cảnh (Rất quan trọng):
                - Việc lựa chọn từ ngữ mô tả xu hướng (ví dụ: 'phục hồi', 'tăng trưởng') phải dựa trên diễn biến giá trong lịch sử gần đây có trong dữ liệu, không chỉ dựa vào một con số của tuần gần nhất.
                - Ví dụ cụ thể: Chỉ được dùng từ "phục hồi" hoặc "hồi phục" khi thị trường vừa trải qua một đợt sụt giảm rõ rệt trước đó. Nếu thị trường vốn đang đi lên và tiếp tục tăng mạnh, phải dùng các từ như "tăng trưởng mạnh", "bứt phá", hoặc "nới rộng đà tăng".
            Quy tắc 2: Thuật ngữ Chuẩn xác:
                - Ưu tiên sử dụng các thuật ngữ tài chính khách quan, định lượng. Tránh các từ ngữ cảm tính hoặc không phù hợp (ví dụ: không dùng "sôi động", "tiến bộ").
            Quy tắc 3: Chống lặp từ:
                - Tuyệt đối không lặp lại từ ngữ, cụm từ và cấu trúc câu trong toàn bộ đoạn văn để đảm bảo sự linh hoạt và tự nhiên.
            Quy tắc 4: Từ ngữ không được sử dụng:
                - Tuyệt đối không sử dụng từ "Tóm lại" trong bất kỳ trường hợp
            Quy tắc 5: Trích xuất số liệu:
                - Các số liệu gốc ở dạng só thập phân khi trích dẫn phải ghi về dạng phần trăm, ví dụ: 0.05 phải ghi là 5%, 0.1234 phải ghi là 12.34%.
                - Không ghi số liệu dạng chữ, ví dụ: "tăng 5%" thay vì "tăng năm phần trăm".
    """
    return prompt

def weekly_vnindex_comment_prompt(df):
    prompt = f"""
        Đây là dữ liệu của chỉ số VNINDEX:
            {df.to_csv(index=False, sep='|', lineterminator='\n')}
        **Vai trò:** Bạn là một **nhà phân tích kỹ thuật cấp cao**, có kinh nghiệm tại một công ty chứng khoán.
        **Nhiệm vụ:** Dựa trên dữ liệu biến động giá và các chỉ báo kỹ thuật của chỉ số VNINDEX được cung cấp, hãy viết một báo cáo phân tích kỹ thuật chuyên nghiệp, súc tích và liền mạch, tuân thủ nghiêm ngặt cấu trúc 8 câu dưới đây.
        **Yêu cầu về nội dung, cấu trúc và định dạng:**
            Báo cáo phải gồm **8 câu, mỗi câu dài khoảng 20 đến 25 từ** và được chia thành **3 đoạn văn riêng biệt**. Bắt đầu thẳng vào nội dung phân tích, không có lời chào.
            **Đoạn 1 (3 câu):**
                * **Câu 1:** Nhận định tổng quan về xu hướng chính của chỉ số trong **tuần vừa qua**.
                * **Câu 2:** Phân tích vai trò của hai đường **SMA 20 và SMA 60** (hỗ trợ/kháng cự).
                * **Câu 3:** Đánh giá chỉ báo **RSI 14** và ý nghĩa của nó đối với áp lực thị trường.
            **Đoạn 2 (3 câu):**
                * **Câu 4:** Phân tích mốc hỗ trợ/kháng cự quan trọng theo **khung Tuần** (kết hợp O-H-L gần nhất và Fibonacci gần nhất).
                * **Câu 5:** Phân tích mốc hỗ trợ/kháng cự quan trọng theo **khung Tháng** (kết hợp O-H-L gần nhất và Fibonacci gần nhất).
                * **Câu 6:** Phân tích mốc hỗ trợ/kháng cự quan trọng theo **khung Quý** (kết hợp O-H-L gần nhất và Fibonacci gần nhất).
            **Đoạn 3 (2 câu):**
                * **Câu 7:** Tổng hợp và nhấn mạnh **một mốc hỗ trợ hoặc kháng cự cốt lõi nhất** cần theo dõi.
                * **Câu 8:** Đề xuất **chiến lược giao dịch** cho tuần tới một cách rõ ràng, dứt khoát.
            **Yêu cầu về ngôn ngữ và trình bày:**
                * **Bắt buộc trích dẫn số liệu cụ thể và đa dạng:**
                    * **Với mỗi ngưỡng hỗ trợ/kháng cự, hãy linh hoạt trích dẫn khoảng cách tới giá đóng cửa. Sử dụng xen kẽ giữa độ lệch phần trăm (%) và độ lệch điểm tuyệt đối để tránh nhàm chán trong văn phong.** Hãy diễn đạt một cách tự nhiên, ví dụ: "...tại 1381.12, thấp hơn 5.2% so với giá hiện tại" hoặc "...quanh 1392 điểm, cách giá đóng cửa hơn 65 điểm".
                    * Các nhận xét đưa ra đều phải kèm theo số liệu của chỉ báo.
                * **Yêu cầu về văn phong và diễn đạt:**
                    * Sử dụng văn phong **sắc bén, quyết đoán và có chiều sâu**.
                    * **Sử dụng cấu trúc câu và từ vựng đa dạng.** Tránh lặp lại một mẫu câu hoặc một từ nhiều lần.
                    * **Liên kết các câu văn một cách mượt mà** bằng các từ/cụm từ chuyển tiếp để tạo thành một dòng chảy phân tích liền mạch.
                * **Yêu cầu về định dạng và thuật ngữ:**
                    * **TUYỆT ĐỐI KHÔNG được viết tên cột dữ liệu gốc (ví dụ: `WFIBO_0382`, `month_prev_high`). BẮT BUỘC phải diễn giải chúng sang ngôn ngữ phân tích chuyên nghiệp (ví dụ: 'ngưỡng Fibonacci 38.2% của khung tuần', 'đỉnh giá của tháng trước').**
                    * **TUYỆT ĐỐI KHÔNG** bao gồm lời mở đầu như "Kính gửi Quý Khách hàng" hoặc "Dựa trên dữ liệu được cung cấp:", hãy bắt đầu ngay vào nội dung phân tích.
                    * **LUÔN LUÔN** sử dụng ngày dạng dd/mm trong bài viết, ví dụ: "ngày 03/01" thay vì "ngày 2023-01-03".
    """
    return prompt

def weekly_ms_comment_prompt(df):
    prompt = f"""
    ### **Phần 1: Bối cảnh và Diễn giải Dữ liệu (Kiến thức nền cho AI)**

    Trước khi thực hiện nhiệm vụ, hãy nghiên cứu và hiểu rõ bản chất của bộ dữ liệu dưới đây.

    #### **I. Tổng quan**
    Bộ dữ liệu này thể hiện các **đường xu hướng** thị trường qua các khung thời gian khác nhau. Mục tiêu là cung cấp một cái nhìn đa chiều, giúp xác định sức mạnh, sự bền vững của xu hướng và các vùng cần chú ý đặc biệt.

    #### **II. Cấu trúc Dữ liệu**
    * `date`: Ngày ghi nhận dữ liệu.
    * `trend_5p`: **Đường xu hướng** cho khung thời gian **tuần**.
    * `trend_20p`: **Đường xu hướng** cho khung thời gian **tháng**.
    * `trend_60p`: **Đường xu hướng** cho khung thời gian **quý**.

    #### **III. Diễn giải Giá trị của các Đường xu hướng**
    Tất cả các cột `trend_*` là giá trị thập phân từ 0 đến 1, **tương ứng với 0% đến 100%**. **Khi viết bài phân tích, bạn phải luôn chuyển đổi và sử dụng định dạng phần trăm (ví dụ: 0.62 sẽ được viết là 62%).**

    * **Tiến về 100%**: Thể hiện một **xu hướng tăng** đang mạnh dần lên.
    * **Tiến về 0%**: Thể hiện một **xu hướng giảm** đang mạnh dần lên.
    * **Ngưỡng `80%`**: Một **vùng giá trị cao**, cho thấy đà tăng đã rất mạnh. Việc mua vào tại vùng này có thể gặp bất lợi về giá (mua đuổi) và cần sự thận trọng.
    * **Ngưỡng `20%`**: Một vùng giá trị thấp và được xem là **vùng rủi ro cao**. Bán ra tại đây có rủi ro bán đúng đáy, trong khi việc mua vào cũng cần hết sức thận trọng vì xu hướng giảm có thể chưa kết thúc.

    #### **IV. Các Nguyên tắc Phân tích Chính**
    1.  **Nguyên tắc Chu kỳ:** Các đường xu hướng có xu hướng di chuyển theo chu kỳ giữa vùng giá trị thấp và cao.
    2.  **Nguyên tắc Đồng pha:** Xu hướng bền vững khi có sự đồng thuận từ nhiều đường xu hướng.
    3.  **Nguyên tắc Chi phối:** Khung thời gian lớn hơn sẽ chi phối biến động của khung nhỏ hơn, nếu xu hướng khung thời gian lớn đang tăng, khung nhỏ giảm thì đánh giá đây là nhịp giảm ngắn hạn.
    4.  **Nguyên tắc Hỗ trợ/Kháng cự:** Các ngưỡng **20%** và **80%** là các mốc tâm lý quan trọng.

    ---

    ### **Phần 2: Yêu cầu Phân tích (Nhiệm vụ cần thực hiện)**

    **Dữ liệu:**
    {df.drop(columns=['trend_240p']).to_csv(index=False, sep='|', lineterminator='\n')}

    **Vai trò**: Bạn là một nhà phân tích chiến lược thị trường cấp cao, với trách nhiệm đưa ra các phân tích và khuyến nghị cho khách hàng.
    **Nhiệm vụ:** Dựa trên kiến thức về bộ dữ liệu và bảng dữ liệu được cung cấp, hãy viết một báo cáo phân tích xu hướng thị trường cho khách hàng trong tuần tới.
    **Yêu cầu về cấu trúc và nội dung:** 
        *Báo cáo phải được trình bày chính xác trong hai đoạn văn ngắn gọn, không có lời chào hay các đề mục. 
        *Phải gồm **6 câu, mỗi câu dài khoảng 20 đến 25 từ** và được chia thành **2 đoạn văn riêng biệt**. Bắt đầu thẳng vào nội dung phân tích, không có lời chào.

        **Đoạn 1 (3 câu):**
            * **Câu 1:** Xác định thay đổi nổi bật nhất của xu hướng tuần trong phiên gần nhất và trong tuần vừa qua (5 phiên gần nhất).
            * **Câu 2:** Nêu ra sự biến động trong tuần của xu hướng tháng, đặc biệt là so sánh tương quan biến động với xu hướng tuần.
            * **Câu 3:** Xác định xem xu hướng quý đang ở vùng giá trị cao (> 70%) hãy thấp (< 30%), đưa ra nhận định xem xu hướng này đang có hỗ trợ cho xu hướng tuần hoặc xu hướng tháng hay không:
                * Nếu xu hướng quý ở vùng giá trị cao thì nó sẽ hỗ trợ cho xu hường tăng của tuần và tháng (cản trở xu hướng giảm của tuần và tháng).
                * Nếu xu hướng quý ở vùng giá trị thấp thì nó sẽ hỗ trợ cho xu hướng giảm của tuần và tháng (cản trở xu huong tăng của tuần và tháng).
                * Nếu xu huớng quý ở vùng giá trị trung tính (30% < x < 70%) thì nó sẽ không hỗ trợ cho xu hướng tuần và tháng. Trong trường hợp này chỉ liệt kê biến động của xu hươngs quý trong tuần vừa qua.

        **Đoạn 2 (3 câu):** Đoạn văn đầu tiên phải tập trung vào hiện trạng và luận giải. 
            * **Câu 4:** Luận giải về mối quan hệ giữa các xu hướng này và kết luận xem chúng đang tuần theo nguyên tắc nào (đồng thuận, phân kì, chi phối). Phải giải thích chi tiết mỗi nguyên tắc trong trường hợp cụ thể hiện tại, ko chỉ nêu ra tên.
            * **Câu 5:** Đưa ra một kết luận sắc bén về bản chất thị trường hiện tại và xu hướng ngắn hạn trong thời gian tới.
            * **Câu 6:** Đề xuất một chiến lược hành động duy nhất, rõ ràng và quyết đoán cho tuần tới, dựa trên các phân tích ở trên.

    **Yêu cầu về ngôn ngữ và trình bày:**

    * **Sử dụng thuật ngữ đa dạng:** Hạn chế lặp lại nguyên văn tên các đường xu hướng.
    * **Yêu cầu về văn phong và diễn đạt:**
        * Sử dụng văn phong **sắc bén, quyết đoán và có chiều sâu**.
        * **Sử dụng cấu trúc câu và từ vựng đa dạng.** Tránh lặp lại một mẫu câu hoặc một từ nhiều lần.
        * **Liên kết các câu văn một cách mượt mà** bằng các từ/cụm từ chuyển tiếp để tạo thành một dòng chảy phân tích liền mạch.
    * **Trích dẫn số liệu:** Các nhận xét phải kèm theo số liệu dưới **định dạng phần trăm**.
    * **Định dạng và Thuật ngữ:**
        * **TUYỆT ĐỐI KHÔNG** được viết tên cột dữ liệu gốc (ví dụ: `trend_5p`).
        * **TUYỆT ĐỐI KHÔNG SỬ DỤNG TỪ 'CHỈ BÁO' (INDICATOR).** Đây là các **'đường xu hướng' (trend lines)**. Hãy luôn sử dụng đúng thuật ngữ này.
        * **TUYỆT ĐỐI KHÔNG** bao gồm lời mở đầu hoặc kết thúc.
        * **LUÔN LUÔN** sử dụng ngày dạng dd/mm trong bài viết, ví dụ: "ngày 03/01" thay vì "ngày 2023-01-03".
        * **LUÔN LUÔN** sử dụng từ "vùng giá trị cao/thấp" thay vì "vùng cao/thấp".
        """
    return prompt