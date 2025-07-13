import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.getcwd()), 'import'))

from import_default import *
from import_database import *
from import_env import *
from import_other import *

R2_ENDPOINT = load_env("R2_ENDPOINT")
R2_ACCESS_KEY_ID = load_env("R2_ACCESS_KEY_ID")
R2_SECRET_ACCESS_KEY = load_env("R2_SECRET_ACCESS_KEY")
BUCKET_NAME = load_env("BUCKET_NAME")
REGION = "auto"

def _aws_signature_v4(method, url, headers, payload, access_key, secret_key, region, service, timestamp):
    """Tạo AWS Signature Version 4"""
    
    # Parse URL
    parsed_url = urlparse(url)
    host = parsed_url.netloc
    path = parsed_url.path
    
    # Tạo canonical request
    canonical_uri = quote(path, safe='/')
    canonical_querystring = ''
    
    # Sắp xếp headers theo thứ tự alphabet
    canonical_headers = ''
    signed_headers = ''
    header_names = sorted(headers.keys())
    for name in header_names:
        canonical_headers += f"{name.lower()}:{headers[name]}\n"
        if signed_headers:
            signed_headers += ';'
        signed_headers += name.lower()
    
    # Tạo payload hash
    if isinstance(payload, str):
        payload_hash = hashlib.sha256(payload.encode('utf-8')).hexdigest()
    else:
        payload_hash = hashlib.sha256(payload).hexdigest()
    
    canonical_request = f"{method}\n{canonical_uri}\n{canonical_querystring}\n{canonical_headers}\n{signed_headers}\n{payload_hash}"
    
    # Tạo string to sign
    algorithm = 'AWS4-HMAC-SHA256'
    credential_scope = f"{timestamp[:8]}/{region}/{service}/aws4_request"
    string_to_sign = f"{algorithm}\n{timestamp}\n{credential_scope}\n{hashlib.sha256(canonical_request.encode('utf-8')).hexdigest()}"
    
    # Tạo signing key
    def sign(key, msg):
        return hmac.new(key, msg.encode('utf-8'), hashlib.sha256).digest()
    
    def getSignatureKey(key, dateStamp, regionName, serviceName):
        kDate = sign(('AWS4' + key).encode('utf-8'), dateStamp)
        kRegion = sign(kDate, regionName)
        kService = sign(kRegion, serviceName)
        kSigning = sign(kService, 'aws4_request')
        return kSigning
    
    signing_key = getSignatureKey(secret_key, timestamp[:8], region, service)
    signature = hmac.new(signing_key, string_to_sign.encode('utf-8'), hashlib.sha256).hexdigest()
    
    # Tạo authorization header
    authorization_header = f"{algorithm} Credential={access_key}/{credential_scope}, SignedHeaders={signed_headers}, Signature={signature}"
    
    return authorization_header

def upload_to_r2(data_bytes: bytes, filename: str, content_type: str = 'image/png', folder_name: str = None):
    """
    Upload file to R2 storage
    
    Args:
        data_bytes: File data as bytes
        filename: Name of the file
        content_type: MIME type of the file
        folder_name: Optional folder name (will be created if doesn't exist)
    
    Returns:
        Public URL of uploaded file or None if failed
    """
    
    # Tạo đường dẫn file với thư mục nếu có
    if folder_name:
        # Loại bỏ dấu / ở đầu và cuối folder_name
        folder_name = folder_name.strip('/')
        file_path = f"{folder_name}/{filename}"
    else:
        file_path = filename
    
    upload_url = f"{R2_ENDPOINT}/{BUCKET_NAME}/{file_path}"
    max_retries = 3

    for attempt in range(max_retries):
        try:
            now = datetime.now(timezone.utc)
            amz_date = now.strftime('%Y%m%dT%H%M%SZ')
            content_hash = hashlib.sha256(data_bytes).hexdigest()

            headers = {
                'Host': R2_ENDPOINT.replace('https://', ''),
                'Content-Type': content_type,
                'Content-Length': str(len(data_bytes)),
                'x-amz-content-sha256': content_hash,
                'x-amz-date': amz_date,
                'x-amz-acl': 'public-read'
            }

            authorization = _aws_signature_v4(
                'PUT', upload_url, headers, data_bytes,
                R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY,
                REGION, 's3', amz_date
            )
            headers['Authorization'] = authorization

            session = requests.Session()
            adapter = requests.adapters.HTTPAdapter(
                max_retries=requests.packages.urllib3.util.retry.Retry(
                    total=3, backoff_factor=0.3, status_forcelist=[500, 502, 503, 504]
                )
            )
            session.mount('https://', adapter)

            response = session.put(
                upload_url, data=data_bytes, headers=headers,
                timeout=(30, 60), verify=True
            )

            if response.status_code in [200, 201]:
                public_url = f"https://pub-196e071ed6aa4a6a80cd72afba5ebd53.r2.dev/{file_path}"
                print(f"✅ Tạo thành công biểu đồ: {filename} -> {public_url}")
                return public_url
            else:
                print(f"❌ Upload thất bại. Status code: {response.status_code}")
                print(f"Response: {response.text}")
                if attempt < max_retries - 1:
                    time.sleep(2)
                else:
                    return None

        except requests.exceptions.SSLError as e:
            print(f"🔒 SSL Error: {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(1)
            else:
                print("❌ Không thể kết nối SSL sau nhiều lần thử.")
                return None

        except requests.exceptions.ConnectionError as e:
            print(f"🌐 Connection Error: {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(2)
            else:
                print("❌ Không thể kết nối sau nhiều lần thử.")
                return None

        except Exception as e:
            print(f"❌ Lỗi khác trong quá trình upload: {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(2)
            else:
                return None
    
    return None

def create_ticker_chart(df, height, width, path, png_name='chart.png'):
   
    # Tạo thư mục nếu chưa tồn tại
    os.makedirs(path, exist_ok=True)
    
    # Chuẩn bị dữ liệu
    df_chart = df.copy()
    df_chart = df_chart.sort_values('date')
    df_chart['date_label'] = df_chart['date'].dt.strftime('%d-%m')

    # Tự động tính toán step cho trục y
    y_data_min = df_chart['close'].min()
    y_data_max = df_chart['close'].max()
    y_range = y_data_max - y_data_min

    if y_range <= 10:
        y_step = 1
    elif y_range <= 50:
        y_step = 5
    elif y_range <= 100:
        y_step = 10
    elif y_range <= 500:
        y_step = 50
    elif y_range <= 1000:
        y_step = 100
    else:
        y_step = math.ceil(y_range / 10)

    # Tính toán y_min và y_max để luôn là tick marks
    y_min = math.floor(y_data_min / y_step) * y_step
    y_max = math.ceil(y_data_max / y_step) * y_step

    # Lấy số lượng điểm dữ liệu để xác định phạm vi trục x
    num_points = len(df_chart)

    # Vẽ biểu đồ với fill area
    fig = px.line(
        df_chart,
        x='date_label',
        y='close',
        markers=True
    )

    # Tùy chỉnh giao diện với fill area
    fig.update_traces(
        line_shape='spline',
        line_color='#005BAA',
        marker=dict(color='#005BAA', size=6.5),
        fill='tonexty',  # Tô màu từ đường line xuống trục x
        fillcolor='rgba(0, 91, 170, 0.2)'  # Màu xanh với độ trong suốt 20%
    )

    # Thêm một trace ẩn ở y=y_min để tạo baseline cho fill
    fig.add_scatter(
        x=df_chart['date_label'],
        y=[y_min] * len(df_chart),
        mode='lines',
        line=dict(color='rgba(0,0,0,0)'),  # Đường ẩn
        showlegend=False,
        hoverinfo='skip'
    )

    # Đảo ngược thứ tự traces để fill hoạt động đúng
    fig.data = fig.data[::-1]

    # Tùy chỉnh layout
    fig.update_layout(
        title=None,
        xaxis_title=None,
        yaxis_title=None,
        plot_bgcolor='white',
        font=dict(family="Arial, sans-serif"),
        width=width,
        height=height,
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis=dict(
            type='category',
            showline=True,
            showgrid=False,
            linecolor='black',
            ticks='outside',
            range=[-0.2, num_points - 0.8],
            tickangle=-45,
            tickfont=dict(size=12)
        ),
        yaxis=dict(
            showline=True,
            showgrid=False,
            linecolor='black',
            ticks='outside',
            range=[y_min, y_max],
            dtick=y_step,
            tickformat=',d',
            tickfont=dict(size=12)
        )
    )
    full_path = os.path.join(path, png_name)
    fig.write_image(full_path, width=width, height=height, scale=4)
    
    return fig.to_image(format="png", width=width, height=height, scale=4)