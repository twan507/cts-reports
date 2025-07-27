import sys
import os

sys.path.append(os.path.join(os.path.dirname(os.getcwd()), "import"))

from import_default import *
from import_database import *
from import_other import *


def get_article_vietstock(url):
    # Set up headers for the request
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    try:
        # Get webpage content
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        # Parse HTML
        soup = BeautifulSoup(response.content, "html.parser")

        # Find article content
        content_div = soup.find("div", {"itemprop": "articleBody", "id": "vst_detail"})

        # Ensure content_div is a Tag object before proceeding
        if not isinstance(content_div, Tag):
            return "", ""

        # Find main image - CHỈ TÌM TRONG NỘI DUNG BÀI VIẾT
        main_image_url = ""

        # Strategy 1: Tìm ảnh đầu tiên trong nội dung bài viết (content_div)
        main_img = content_div.find("img")
        if main_img and main_img.get("src"):
            main_image_url = main_img.get("src")

        # Strategy 2: Nếu không có ảnh trong nội dung, kiểm tra meta og:image
        # (chỉ dùng làm backup nếu đó là ảnh thật của bài viết)
        if not main_image_url:
            meta_image = soup.find("meta", {"property": "og:image"})
            if meta_image and meta_image.get("content"):
                og_image_url = meta_image.get("content")
                # Kiểm tra xem og:image có phải là ảnh thật của bài viết không
                # (thường og:image sẽ trùng với ảnh đầu tiên trong bài)
                if "vietstock.vn" in og_image_url or "image.vietstock.vn" in og_image_url:
                    # Chỉ lấy nếu là ảnh từ domain chính của vietstock
                    main_image_url = og_image_url

        # Extract text from paragraphs
        article_content = ""
        paragraphs = content_div.find_all("p")

        for p in paragraphs:
            # Skip author and publishing info
            if p.get("class") in [["pAuthor"], ["pPublishTimeSource", "right"]]:
                continue

            text = p.get_text(strip=True)
            if text:
                article_content += f"{text}\n"

        # Make sure image URL is absolute
        if main_image_url:
            if not main_image_url.startswith(("http://", "https://")):
                if main_image_url.startswith("//"):
                    main_image_url = "https:" + main_image_url
                elif main_image_url.startswith("/"):
                    main_image_url = "https://vietstock.vn" + main_image_url
                else:
                    main_image_url = "https://vietstock.vn/" + main_image_url

        return article_content.strip(), main_image_url

    except Exception as e:
        return "", ""


# Hàm lấy danh sách bài viết từ trang danh mục CafeF (tạo feed giả)
def get_cafef_articles_list(url, max_articles):
    """
    Lấy danh sách bài viết từ trang danh mục CafeF và trả về dạng feed giống RSS
    Args:
        url: URL của trang danh mục CafeF
        max_articles: Số bài tối đa cần lấy (mặc định 2)
    Returns:
        list: Danh sách các entry giống RSS feed với title, id (URL), published
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, "html.parser")
        entries = []

        # Tìm link bài viết hiệu quả
        links = soup.find_all("a", href=True, limit=50)
        article_links = []

        for link in links:
            href = link.get("href")
            if href and ".chn" in href and "188" in href and not any(skip in href for skip in ["/su-kien/", "/video/", "/static/"]):
                text = link.get_text(strip=True)
                if text and 15 < len(text) < 150:
                    if href.startswith("/"):
                        href = "https://cafef.vn" + href

                    if href not in [a["url"] for a in article_links]:
                        article_links.append({"url": href, "title": text})

                        if len(article_links) >= max_articles * 2:
                            break

        # Chuyển đổi thành format giống RSS feed
        for article in article_links[:max_articles]:
            # Tạo entry giống feedparser
            entry = {
                "title": article["title"],
                "id": article["url"],  # Sử dụng URL làm id
                "published": "",  # Sẽ được lấy sau khi parse bài viết
            }
            entries.append(entry)

        return entries

    except Exception as e:
        return []


def get_article_cafef(url):
    """
    Lấy nội dung chi tiết một bài viết từ CafeF (cấu trúc giống get_article_vietstock)
    Args:
        url: URL của bài viết cần lấy
    Returns:
        tuple: (content, image_url) - giống như get_article_vietstock
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Connection": "keep-alive",
    }

    try:
        response = requests.get(url, headers=headers, timeout=8)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, "html.parser")

        # LOGIC LẤY ẢNH CẢI THIỆN
        main_image_url = ""

        # Strategy 1: Tìm img có data-role="cover" (ảnh chính của bài viết)
        cover_img = soup.find("img", {"data-role": "cover"})
        if cover_img and cover_img.get("src"):
            cover_src = cover_img.get("src")
            if any(domain in cover_src for domain in ["cafef.vn", "cafefcdn.com"]):
                main_image_url = cover_src

        # Strategy 2: Tìm trong meta tags
        if not main_image_url:
            meta_selectors = [{"property": "og:image"}, {"name": "twitter:image"}, {"property": "article:image"}]

            for selector in meta_selectors:
                meta_img = soup.find("meta", selector)
                if meta_img and meta_img.get("content"):
                    og_image_url = meta_img.get("content")
                    # Kiểm tra xem có phải ảnh từ domain chính không
                    if any(domain in og_image_url for domain in ["cafef.vn", "cafefcdn.com"]):
                        main_image_url = og_image_url
                        break

        # Strategy 3: Tìm ảnh đầu tiên trong trang
        if not main_image_url:
            all_imgs = soup.find_all("img", limit=15)
            for img in all_imgs:
                src = img.get("src")
                if src and any(domain in src for domain in ["cafef.vn", "cafefcdn.com"]):
                    # Bỏ qua ảnh logo, icon, avatar nhỏ, thumbnail nhỏ
                    if not any(skip in src.lower() for skip in ["logo", "icon", "avatar", "thumb_w/50", "thumb_w/100", "zoom/223_140"]):
                        # Ưu tiên ảnh có kích thước lớn hơn
                        if any(size in src for size in ["thumb_w/640", "zoom/600_", "original", "large"]):
                            main_image_url = src
                            break
                        elif not main_image_url:  # Fallback nếu chưa có ảnh nào
                            main_image_url = src

        # Strategy 4: Tìm nội dung bài viết và ảnh trong đó
        if not main_image_url:
            selectors = [{"class": "contentdetail"}, {"id": "contentdetail"}, {"class": "detail-content"}, "article"]

            content_div = None
            for selector in selectors:
                if isinstance(selector, dict):
                    content_div = soup.find("div", selector)
                else:
                    content_div = soup.find(selector)
                if content_div:
                    break

            if content_div:
                img_in_content = content_div.find("img")
                if img_in_content and img_in_content.get("src"):
                    main_image_url = img_in_content.get("src")

        # Chuẩn hóa URL ảnh
        if main_image_url:
            if not main_image_url.startswith(("http://", "https://")):
                if main_image_url.startswith("//"):
                    main_image_url = "https:" + main_image_url
                elif main_image_url.startswith("/"):
                    main_image_url = "https://cafef.vn" + main_image_url

        # Tìm nội dung bài viết
        selectors = [{"class": "contentdetail"}, {"id": "contentdetail"}, {"class": "detail-content"}, "article"]

        content_div = None
        for selector in selectors:
            if isinstance(selector, dict):
                content_div = soup.find("div", selector)
            else:
                content_div = soup.find(selector)
            if content_div:
                break

        # Fallback: Tìm div có nhiều paragraph
        if not content_div:
            divs_with_p = [(div, len(div.find_all("p"))) for div in soup.find_all("div", limit=20)]
            divs_with_p.sort(key=lambda x: x[1], reverse=True)
            if divs_with_p and divs_with_p[0][1] >= 3:
                content_div = divs_with_p[0][0]

        if not content_div:
            return "", ""

        # Lấy nội dung
        paragraphs = content_div.find_all("p")
        article_content = ""

        for p in paragraphs:
            if p.get("class") and any(cls in ["author", "source", "time", "pAuthor", "caption"] for cls in p.get("class")):
                continue

            text = p.get_text(strip=True)
            if text and len(text) > 10:
                article_content += f"{text}\n"

        # Fallback nếu không có content từ p
        if len(article_content.strip()) < 50:
            article_content = content_div.get_text(strip=True)

        return article_content.strip(), main_image_url

    except Exception as e:
        return "", ""


def get_cafef_published_time(url):
    """
    Lấy thời gian đăng bài từ URL bài viết CafeF
    """
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

    try:
        response = requests.get(url, headers=headers, timeout=5)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")

        # Thử các cách lấy thời gian đăng bài
        time_selectors = [
            {"property": "article:published_time"},
            {"name": "pubdate"},
            {"property": "og:updated_time"},
            {"name": "last-modified"},
        ]

        for selector in time_selectors:
            meta_time = soup.find("meta", selector)
            if meta_time and meta_time.get("content"):
                return meta_time.get("content")

        # Nếu không tìm thấy trong meta, tìm trong các thẻ có class time hoặc date
        time_elements = soup.find_all(
            ["span", "div", "time"], class_=lambda x: x and any(keyword in x.lower() for keyword in ["time", "date", "publish"])
        )
        for elem in time_elements:
            text = elem.get_text(strip=True)
            if text and any(char.isdigit() for char in text) and len(text) > 5:
                return text

        return ""

    except Exception as e:
        return ""


def convert_published_time(time_str):
    """
    Chuyển đổi các format thời gian khác nhau thành datetime
    """
    if pd.isna(time_str) or time_str == "":
        return pd.NaT

    try:
        # Format: "Sat, 12 Jul 2025 17:44:43 +0700"
        if "," in time_str and "+" in time_str:
            time_str_clean = time_str.split("+")[0].strip()
            return pd.to_datetime(time_str_clean, format="%a, %d %b %Y %H:%M:%S")
        # Format: "Fri, 25 Jul 2025 06:56:10 GMT"
        elif time_str.endswith("GMT"):
            time_str_clean = time_str.replace("GMT", "").strip()
            return pd.to_datetime(time_str_clean, format="%a, %d %b %Y %H:%M:%S")
        # Format: "2025-07-12T07:13:17"
        elif "T" in time_str:
            return pd.to_datetime(time_str, format="%Y-%m-%dT%H:%M:%S")
        # Format: "14:31 | 16/07/2025"
        elif "|" in time_str:
            time_part, date_part = time_str.split("|")
            time_part = time_part.strip()
            date_part = date_part.strip()
            full_datetime_str = f"{date_part} {time_part}"
            return pd.to_datetime(full_datetime_str, format="%d/%m/%Y %H:%M")
        # Thử parse tự động cho các format khác
        else:
            return pd.to_datetime(time_str)
    except Exception as e:
        print(f"Không thể chuyển đổi thời gian: {time_str}, lỗi: {e}")
        return pd.NaT


def get_data_from_av(from_symbol, to_symbol, column_name):
    """Hàm lấy dữ liệu tỷ giá từ Alpha Vantage"""
    try:
        fe = ForeignExchange(key=load_env("AV_KEY"), output_format="pandas")
        df, _ = fe.get_currency_exchange_daily(from_symbol=from_symbol, to_symbol=to_symbol, outputsize="full")
        df_clean = df[df.index >= datetime(2020, 1, 1)][["4. close"]].copy()
        df_clean.columns = [column_name]
        df_clean[column_name] = df_clean[column_name].astype(float)
        return df_clean
    except Exception as e:
        print(f"❌ LỖI khi lấy dữ liệu {column_name}: {e}")
        return None


def get_vietnambiz_articles_list(url, max_articles):
    """
    Lấy danh sách bài viết từ trang danh mục VietnamBiz và trả về dạng feed giống RSS
    Args:
        url: URL của trang danh mục VietnamBiz
        max_articles: Số bài tối đa cần lấy
    Returns:
        list: Danh sách các entry giống RSS feed với title, id (URL), published
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, "html.parser")
        entries = []
        article_links = []

        # Tìm các bài viết trong list-news
        list_news = soup.find("div", class_="list-news")
        if list_news:
            # Tìm tất cả các item trong list-news
            news_items = list_news.find_all("div", class_="item")

            for item in news_items:
                # Tìm title trong h3.title > a
                title_element = item.find("h3", class_="title")
                if title_element:
                    title_link = title_element.find("a")
                    if title_link and title_link.get("href"):
                        href = title_link.get("href")
                        title = title_link.get_text(strip=True)

                        # Chuẩn hóa URL
                        if href.startswith("/"):
                            href = "https://vietnambiz.vn" + href

                        # Kiểm tra URL không trùng lặp
                        if href not in [a["url"] for a in article_links]:
                            article_links.append({"url": href, "title": title})

                            # Dừng khi đã đủ số lượng cần thiết
                            if len(article_links) >= max_articles:
                                break

        # Nếu chưa đủ bài viết, tìm thêm từ các nguồn khác
        if len(article_links) < max_articles:
            # Tìm các bài viết trong zone-pin-1 (bài nổi bật)
            main_articles = soup.find_all("div", class_="zone-pin-1")
            for article_div in main_articles:
                if len(article_links) >= max_articles:
                    break

                title_link = article_div.find("h2", class_="title")
                if title_link:
                    link = title_link.find("a")
                    if link and link.get("href"):
                        href = link.get("href")
                        title = link.get_text(strip=True)

                        # Chuẩn hóa URL
                        if href.startswith("/"):
                            href = "https://vietnambiz.vn" + href

                        if href not in [a["url"] for a in article_links]:
                            article_links.append({"url": href, "title": title})

        # Chuyển đổi thành format giống RSS feed
        for article in article_links[:max_articles]:
            entry = {
                "title": article["title"],
                "id": article["url"],  # Sử dụng URL làm id
                "published": "",  # Sẽ được lấy sau khi parse bài viết
            }
            entries.append(entry)

        return entries

    except Exception as e:
        print(f"Lỗi khi lấy danh sách bài viết từ VietnamBiz: {e}")
        return []


def get_article_vietnambiz(url):
    """
    Lấy nội dung chi tiết một bài viết từ VietnamBiz (cấu trúc giống get_article_cafef)
    Args:
        url: URL của bài viết cần lấy
    Returns:
        tuple: (content, image_url) - giống như get_article_cafef
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Connection": "keep-alive",
    }

    try:
        response = requests.get(url, headers=headers, timeout=8)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, "html.parser")

        # LOGIC LẤY ẢNH CẢI THIỆN
        main_image_url = ""

        # Strategy 1: Tìm ảnh trong div có class="VnBizPreviewMode" (ảnh chính trong nội dung)
        preview_img = soup.find("div", class_="VnBizPreviewMode")
        if preview_img:
            img_tag = preview_img.find("img")
            if img_tag and img_tag.get("src"):
                img_src = img_tag.get("src")
                if any(domain in img_src for domain in ["vietnambiz.vn", "cdn.vietnambiz.vn"]):
                    main_image_url = img_src

        # Strategy 2: Tìm trong meta tags
        if not main_image_url:
            meta_selectors = [{"property": "og:image"}, {"name": "twitter:image"}, {"property": "article:image"}]

            for selector in meta_selectors:
                meta_img = soup.find("meta", selector)
                if meta_img and meta_img.get("content"):
                    og_image_url = meta_img.get("content")
                    # Kiểm tra xem có phải ảnh từ domain chính không
                    if any(domain in og_image_url for domain in ["vietnambiz.vn", "cdn.vietnambiz.vn"]):
                        main_image_url = og_image_url
                        break

        # Strategy 3: Tìm ảnh đầu tiên trong vnbcbc-body (nội dung bài viết)
        if not main_image_url:
            content_body = soup.find("div", class_="vnbcbc-body")
            if content_body:
                all_imgs = content_body.find_all("img", limit=10)
                for img in all_imgs:
                    src = img.get("src")
                    if src and any(domain in src for domain in ["vietnambiz.vn", "cdn.vietnambiz.vn"]):
                        # Bỏ qua ảnh logo, icon, avatar nhỏ
                        if not any(skip in src.lower() for skip in ["logo", "icon", "avatar", "thumb", "small"]):
                            # Ưu tiên ảnh có kích thước lớn hơn
                            if any(size in src for size in ["width=700", "width=600", "original", "large"]) or "?" not in src:
                                main_image_url = src
                                break
                            elif not main_image_url:  # Fallback nếu chưa có ảnh nào
                                main_image_url = src

        # Strategy 4: Tìm ảnh đầu tiên trong trang
        if not main_image_url:
            all_imgs = soup.find_all("img", limit=15)
            for img in all_imgs:
                src = img.get("src")
                if src and any(domain in src for domain in ["vietnambiz.vn", "cdn.vietnambiz.vn"]):
                    # Bỏ qua ảnh logo, icon, avatar nhỏ, thumbnail nhỏ
                    if not any(skip in src.lower() for skip in ["logo", "icon", "avatar", "93x60", "215x144"]):
                        # Ưu tiên ảnh có kích thước lớn hơn
                        if any(size in src for size in ["width=700", "width=600", "original", "large"]):
                            main_image_url = src
                            break
                        elif not main_image_url:  # Fallback nếu chưa có ảnh nào
                            main_image_url = src

        # Chuẩn hóa URL ảnh
        if main_image_url:
            if not main_image_url.startswith(("http://", "https://")):
                if main_image_url.startswith("//"):
                    main_image_url = "https:" + main_image_url
                elif main_image_url.startswith("/"):
                    main_image_url = "https://vietnambiz.vn" + main_image_url

        # Tìm nội dung bài viết
        # Strategy 1: Tìm trong vnbcbc-body (nội dung chính)
        content_div = soup.find("div", class_="vnbcbc-body")

        # Strategy 2: Fallback - tìm trong article-body-content
        if not content_div:
            content_div = soup.find("div", class_="article-body-content")

        # Strategy 3: Fallback - tìm trong post-body-content
        if not content_div:
            content_div = soup.find("div", class_="post-body-content")

        # Fallback: Tìm div có nhiều paragraph
        if not content_div:
            divs_with_p = [(div, len(div.find_all("p"))) for div in soup.find_all("div", limit=20)]
            divs_with_p.sort(key=lambda x: x[1], reverse=True)
            if divs_with_p and divs_with_p[0][1] >= 3:
                content_div = divs_with_p[0][0]

        if not content_div:
            return "", ""

        # Lấy nội dung từ thẻ p và h2, h3
        article_content = ""

        # Lấy sapo (mô tả ngắn) nếu có
        sapo_div = soup.find("div", class_="vnbcbc-sapo")
        if sapo_div:
            sapo_text = sapo_div.get_text(strip=True)
            if sapo_text and len(sapo_text) > 10:
                article_content += f"{sapo_text}\n\n"

        # Lấy nội dung từ các thẻ h2, h3, p
        content_elements = content_div.find_all(["h2", "h3", "p"])

        for element in content_elements:
            # Bỏ qua các thẻ có class không mong muốn
            if element.get("class"):
                element_classes = element.get("class")
                if any(cls in ["author", "source", "time", "caption", "PhotoCMS_Caption"] for cls in element_classes):
                    continue

            # Bỏ qua nội dung trong figcaption
            if element.find_parent("figcaption"):
                continue

            text = element.get_text(strip=True)
            if text and len(text) > 10:
                # Thêm heading với định dạng đặc biệt
                if element.name in ["h2", "h3"]:
                    article_content += f"\n{text}\n"
                else:
                    article_content += f"{text}\n"

        # Fallback nếu không có content từ các thẻ trên
        if len(article_content.strip()) < 50:
            article_content = content_div.get_text(strip=True)

        return article_content.strip(), main_image_url

    except Exception as e:
        print(f"Lỗi khi lấy bài viết từ VietnamBiz: {e}")
        return "", ""


def get_vietnambiz_published_time(url):
    """
    Lấy thời gian đăng bài từ URL bài viết VietnamBiz
    Args:
        url: URL của bài viết VietnamBiz
    Returns:
        str: Thời gian đăng bài hoặc chuỗi rỗng nếu không tìm thấy
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Connection": "keep-alive",
    }

    try:
        response = requests.get(url, headers=headers, timeout=5)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")

        # Strategy 1: Tìm trong span có class vnbcbat-data (cấu trúc chính của VietnamBiz)
        time_span = soup.find("span", class_="vnbcbat-data")
        if time_span:
            time_text = time_span.get_text(strip=True)
            if time_text and any(char.isdigit() for char in time_text):
                return time_text

        # Strategy 2: Tìm trong data-role="publishdate"
        publish_date = soup.find(attrs={"data-role": "publishdate"})
        if publish_date:
            time_text = publish_date.get_text(strip=True)
            if time_text and any(char.isdigit() for char in time_text):
                return time_text

        # Strategy 3: Thử các meta tags thông thường
        time_selectors = [
            {"property": "article:published_time"},
            {"name": "pubdate"},
            {"property": "og:updated_time"},
            {"name": "last-modified"},
            {"property": "article:modified_time"},
        ]

        for selector in time_selectors:
            meta_time = soup.find("meta", selector)
            if meta_time and meta_time.get("content"):
                return meta_time.get("content")

        # Strategy 4: Tìm trong các thẻ có class liên quan đến time/date
        time_elements = soup.find_all(
            ["span", "div", "time"],
            class_=lambda x: x and any(keyword in x.lower() for keyword in ["time", "date", "publish", "vnbcba-time"]),
        )
        for elem in time_elements:
            text = elem.get_text(strip=True)
            if text and any(char.isdigit() for char in text) and len(text) > 5:
                # Ưu tiên format có dạng "HH:MM | DD/MM/YYYY"
                if "|" in text or "/" in text:
                    return text

        # Strategy 5: Tìm trong title attribute
        title_elements = soup.find_all(attrs={"title": True})
        for elem in title_elements:
            title_text = elem.get("title", "")
            if title_text and any(char.isdigit() for char in title_text) and "/" in title_text:
                return title_text

        return ""

    except Exception as e:
        print(f"Lỗi khi lấy thời gian đăng bài từ VietnamBiz: {e}")
        return ""


def get_article_vneconomy(rss_url, num_articles):
    articles_list = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    response = None
    for attempt in range(3):
        try:
            response = requests.get(rss_url, headers=headers, timeout=10)
            response.raise_for_status()
            break
        except requests.exceptions.RequestException as e:
            if attempt < 2:
                time.sleep(2)
            else:
                return []
    if response is None:
        return []

    try:
        feed = feedparser.parse(response.text)
        if feed.bozo:
            print(f"Lỗi: RSS feed không hợp lệ hoặc không thể truy cập: {feed.bozo_exception}")
            return []

        # Lặp qua các bài báo trong feed
        for entry in feed.entries[:num_articles]:
            content_html = entry.get("content", [{}])[0].get("value", "") or entry.get("summary", "")
            soup = BeautifulSoup(content_html, "html.parser")
            content_text = "\n".join(p.get_text(strip=True) for p in soup.find_all("p"))

            # Lấy URL hình ảnh
            image_url = None
            if "media_content" in entry and entry.media_content:
                image_url = entry.media_content[0].get("url")
            else:
                img_tag = soup.find("img")
                if img_tag:
                    image_url = img_tag.get("src")

            article_dict = {
                "source": 'VnEconomy',
                "title": entry.get("title", "Không có tiêu đề"),
                "content": content_text.strip(),
                "image_url": image_url,
                "article_url": entry.get("link", ""),
                "published_time": getattr(entry, "published", ""),
            }
            articles_list.append(article_dict)
    except Exception as e:
        print(f"Đã có lỗi xảy ra khi xử lý RSS: {e}")
        return []

    return articles_list
