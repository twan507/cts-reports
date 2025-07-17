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

# ==============================================================================
# 2. CÁC HÀM TIỆN ÍCH VÀ CHUẨN BỊ DỮ LIỆU
# ==============================================================================

def _prepare_chart_data(df, config, line_columns):
    """
    Chuẩn bị các dữ liệu cần thiết cho việc vẽ biểu đồ.
    """
    max_volume = df['volume'].max()
    df['volume_color'] = np.where(df['close'] >= df['open'], config['color_up'], config['color_down'])
    return line_columns, max_volume

def _get_style_for_column(col_name):
    """Hàm hỗ trợ để lấy style cho các đường chỉ báo kỹ thuật."""
    style_mapping = {
        'SMA_20':   {'color': "#00B1EC", 'dash': 'solid', 'width': 2},
        'SMA_60':   {'color': "#006080", 'dash': 'solid', 'width': 2},
        'open':  {'color': '#C71585', 'dash': 'dash', 'width': 1.5, 'line_shape': 'hv'},
        'prev':  {'color': '#808080', 'dash': 'dash', 'width': 1.5, 'line_shape': 'hv'},
        'MFIBO': {'color': "#DFBD01", 'dash': 'dot', 'width': 1.5, 'line_shape': 'hv'},
        'QFIBO': {'color': '#FB8C00', 'dash': 'dot', 'width': 1.5, 'line_shape': 'hv'},
        'YFIBO': {'color': '#E65100', 'dash': 'dot', 'width': 1.5, 'line_shape': 'hv'}
    }
    for key, style in style_mapping.items():
        if key in col_name:
            return style
    return {'width': 1.2, 'color': 'black', 'dash': 'solid'}

# ==============================================================================
# 3. CÁC HÀM VẼ CÁC THÀNH PHẦN CỦA BIỂU ĐỒ
# ==============================================================================

def _add_candlestick_chart(fig, df, config):
    """Thêm biểu đồ nến vào subplot chính."""
    fig.add_trace(
        go.Candlestick(
            x=df['date'], open=df['open'], high=df['high'], low=df['low'], close=df['close'],
            increasing_line_color=config['color_up'], decreasing_line_color=config['color_down'],
            increasing_fillcolor=config['color_up'], decreasing_fillcolor=config['color_down'],
            line=dict(width=1), name='Giá'
        ),
        row=1, col=1, secondary_y=False
    )

def _add_volume_chart(fig, df):
    """Thêm biểu đồ khối lượng vào subplot chính."""
    fig.add_trace(
        go.Bar(x=df['date'], y=df['volume'], marker=dict(color=df['volume_color'], opacity=0.3), name='Volume'),
        row=1, col=1, secondary_y=True
    )

def _add_technical_lines(fig, df, line_columns, line_name_dict):
    """Thêm các đường chỉ báo kỹ thuật và trả về thông tin để tạo nhãn."""
    line_info = []
    for col in line_columns:
        if col in df.columns and not df[col].isnull().all():
            # Lấy toàn bộ style từ hàm hỗ trợ
            line_style_full = _get_style_for_column(col)
            
            # SỬA LỖI: Tách 'line_shape' ra khỏi dictionary chính.
            # Nó sẽ được dùng như một tham số riêng cho go.Scatter.
            line_shape_value = line_style_full.pop('line_shape', None)
            
            # Tạo dictionary các tham số cho go.Scatter
            trace_args = {
                'x': df['date'],
                'y': df[col],
                'mode': 'lines',
                'line': line_style_full, # Phần style còn lại (color, width, dash) được truyền vào đây
                'name': col
            }

            # Chỉ thêm tham số line_shape nếu nó tồn tại
            if line_shape_value:
                trace_args['line_shape'] = line_shape_value

            # Thêm trace vào biểu đồ với các tham số đã được tách đúng
            fig.add_trace(go.Scatter(**trace_args), row=1, col=1, secondary_y=False)
            
            # Xử lý thông tin cho các tag bên phải
            last_valid_idx = df[col].last_valid_index()
            if last_valid_idx is not None:
                display_name = line_name_dict.get(col, col)
                last_value = df[col].loc[last_valid_idx]
                line_info.append({
                    'name': f"{display_name}: {last_value:.2f}",
                    'value': last_value,
                    'color': _get_style_for_column(col).get('color', 'black') # Lấy lại màu để đảm bảo chính xác
                })
    return line_info


def _add_rsi_chart(fig, df, config):
    """Thêm biểu đồ RSI hoàn chỉnh, giữ lại logic tiêu đề từ code gốc."""
    rsi_col = 'RSI_14'
    if rsi_col not in df.columns or df[rsi_col].isnull().all(): return

    # Vẽ các thành phần chính
    fig.add_trace(go.Scatter(x=df['date'], y=df[rsi_col], mode='lines',
                           line=dict(color=config['color_rsi_line'], width=1.5), name='RSI'), row=2, col=1)
    fig.add_hline(y=config['rsi_upper_bound'], line_dash="dash", line_color=config['color_rsi_bound_line'], line_width=1.5, row=2, col=1)
    fig.add_hline(y=config['rsi_lower_bound'], line_dash="dash", line_color=config['color_rsi_bound_line'], line_width=1.5, row=2, col=1)
    fig.add_hrect(y0=config['rsi_lower_bound'], y1=config['rsi_upper_bound'],
                  fillcolor=config['color_rsi_bound_fill'], opacity=1, layer="below", line_width=0, row=2, col=1)

    # PHỤC HỒI LOGIC TIÊU ĐỀ GỐC: Thêm nhãn tiêu đề ở góc trên-trái
    last_rsi = df[rsi_col].iloc[-1]
    fig.add_annotation(
        x=0.01, y=0.98, xref='x domain', yref='y domain',
        text=f"RSI 14: <b style='color:{config['color_rsi_line']};'>{last_rsi:.2f}</b>" , showarrow=False,
        xanchor='left', yanchor='top',
        font=dict(size=config['font_size_subplot_title'], family=config['font_family'], color='black'),
        xshift=-13,                # Tạo khoảng đệm nhỏ từ lề trái
        yshift=18,               # Tạo khoảng đệm nhỏ từ lề trên
        row=2, col=1
    )
    
    # Logic vẽ các tag giá trị bên phải (giữ nguyên)
    y_axis_range = df[rsi_col].max() - df[rsi_col].min()
    if y_axis_range == 0: y_axis_range = 20 # Tránh lỗi chia cho 0
    min_spacing = config['rsi_label_min_spacing_ratio'] * y_axis_range
    
    y_upper_pos = float(config['rsi_upper_bound'])
    y_lower_pos = float(config['rsi_lower_bound'])

    if abs(last_rsi - y_upper_pos) < min_spacing: y_upper_pos = last_rsi + min_spacing
    if abs(last_rsi - y_lower_pos) < min_spacing: y_lower_pos = last_rsi - min_spacing
        
    tag_font = dict(size=config['font_size_tag'], family=config['font_family'])
    annotations = [
        {'y': y_upper_pos,
         'text': f"<b>RSI {config['rsi_upper_bound']:.2f}</b>", # Sửa định dạng text
         'font_color': config['color_rsi_bound_tag'],             # Dùng màu xám đậm
         'bgcolor': config['tag_bgcolor'],
         'bordercolor': config['color_rsi_bound_tag']},          # Dùng màu xám đậm
        {'y': y_lower_pos,
         'text': f"<b>RSI {config['rsi_lower_bound']:.2f}</b>", # Sửa định dạng text
         'font_color': config['color_rsi_bound_tag'],             # Dùng màu xám đậm
         'bgcolor': config['tag_bgcolor'],
         'bordercolor': config['color_rsi_bound_tag']},          # Dùng màu xám đậm
        {'y': last_rsi,
         'text': f"<b>RSI {last_rsi:.2f}</b>", # Giữ nguyên định dạng cho giá trị hiện tại
         'font_color': 'white',
         'bgcolor': config['color_rsi_line'],
         'bordercolor': config['color_rsi_line']},
    ]

    # Thêm các nhãn vào biểu đồ
    for anno in annotations:
        fig.add_annotation(
            x=config['label_x_position'], y=anno['y'], xref='x domain', yref='y',
            text=anno['text'],
            ax=-10,
            ay=0,
            xanchor='left', yanchor='middle',
            font={**tag_font, 'color': anno['font_color']},
            bgcolor=anno['bgcolor'], bordercolor=anno['bordercolor'],
            borderwidth=1, row=2, col=1
        )

# ==============================================================================
# 4. CÁC HÀM XỬ LÝ NHÃN GIÁ (ANNOTATIONS)
# ==============================================================================

def _process_and_add_annotations(fig, df, line_info, symbol_name, config):
    """Hàm tổng hợp xử lý và thêm tất cả các nhãn giá vào biểu đồ chính."""
    last_close = df['close'].iloc[-1]
    last_open = df['open'].iloc[-1]
    price_color = config['color_up'] if last_close >= last_open else config['color_down']
    
    line_info.append({
        'name': f"{symbol_name}: {last_close:.2f}", 'value': last_close, 'is_price_tag': True,
        'bgcolor': price_color, 'font_color': 'white', 'color': price_color
    })
    fig.add_hline(y=last_close, line_color=price_color, line_width=1, line_dash='dash', row=1, col=1)

    price_tag = next((info for info in line_info if info.get('is_price_tag')), None)
    other_tags = sorted([info for info in line_info if not info.get('is_price_tag')], key=lambda x: x['value'], reverse=True)
    
    used_y_positions = []
    if price_tag:
        fig.add_annotation(
            x=config['label_x_position'], y=price_tag['value'], xref='x domain', yref='y',
            text=f"<b>{price_tag['name']}</b>", xanchor='left', yanchor='middle',
            font=dict(size=config['font_size_price_tag'], color=price_tag['font_color'], family=config['font_family']),
            bgcolor=price_tag['bgcolor'], bordercolor=price_tag['color'], borderwidth=1,
            ax=-10, ay=0, row=1, col=1
        )
        used_y_positions.append(price_tag['value'])

    visible_y_range = df['high'].max() - df['low'].min()
    min_spacing = visible_y_range * config['label_min_spacing_ratio']

    for info in other_tags:
        y_pos = _calculate_safe_position(info['value'], used_y_positions, min_spacing, df)
        used_y_positions.append(y_pos)
        fig.add_annotation(
            x=config['label_x_position'], y=y_pos, xref='x domain', yref='y',
            text=f"<b>{info['name']}</b>", xanchor='left', yanchor='middle',
            font=dict(size=config['font_size_tag'], color=info['color'], family=config['font_family']),
            bgcolor=config['tag_bgcolor'], bordercolor=info['color'], borderwidth=1,
            ax=-10, ay=0, row=1, col=1
        )

def _calculate_safe_position(y_position, used_y_positions, min_spacing, df):
    """Tính toán vị trí y an toàn cho nhãn để tránh chồng chéo."""
    used_y_positions.sort(reverse=True)
    for used_pos in used_y_positions:
        if abs(y_position - used_pos) < min_spacing:
            y_position = used_pos - min_spacing
    
    visible_y_range = df['high'].max() - df['low'].min()
    chart_bottom = df['low'].min() - (visible_y_range * 0.05)
    chart_top = df['high'].max() + (visible_y_range * 0.05)
    return min(max(y_position, chart_bottom), chart_top)

# ==============================================================================
# 5. CÁC HÀM CẤU HÌNH LAYOUT VÀ TRỤC
# ==============================================================================

def _configure_layout_and_axes(fig, df, max_volume, config, width, height):
    """Cấu hình layout tổng thể, các trục X, Y và tiêu đề."""
    last_day = df.iloc[-1]
    o, h, l, c = last_day.get('open', 0), last_day.get('high', 0), last_day.get('low', 0), last_day.get('close', 0)
    diff, pct_change = last_day.get('diff', 0), last_day.get('pct_change', 0)
    value_color = config['color_up'] if c >= o else config['color_down']
    sign = '+' if diff >= 0 else ''
    title_text = (
        f"{config['symbol_name']} {config['time_frame']}   "
        f"<span style='color:black;'>O:</span><b style='color:{value_color};'>{o:.2f}</b> "
        f"<span style='color:black;'>H:</span><b style='color:{value_color};'>{h:.2f}</b> "
        f"<span style='color:black;'>L:</span><b style='color:{value_color};'>{l:.2f}</b> "
        f"<span style='color:black;'>C:</span><b style='color:{value_color};'>{c:.2f}</b>  "
        f"<span style='color:{value_color}; font-weight:bold;'>{sign}{diff:.2f} ({sign}{pct_change:.2%})</span>"
    )

    fig.update_layout(
        height=height,
        width=width, 
        xaxis_rangeslider_visible=False, showlegend=False,
        margin=config['margin'], plot_bgcolor=config['plot_bgcolor'], paper_bgcolor=config['paper_bgcolor'],
        hovermode='x unified', font=dict(family=config['font_family']),
        title={
            'text': title_text, 'y': 0.98, 'x': 0.027,
            'xanchor': 'left', 'yanchor': 'top',
                        'font': dict(size=config['font_size_title'], family=config['font_family'], color='black')
        }
    )

    tick_labels, tick_vals = _generate_xaxis_ticks(df)
    fig.update_xaxes(
        showgrid=False, type='category', tickmode='array', tickvals=tick_vals, ticktext=tick_labels,
        tickfont=dict(size=config['font_size_axis'], color=config['tick_color'])
    )

    fig.update_yaxes(row=1, col=1, secondary_y=False, showgrid=True, gridcolor=config['grid_color'],
                     tickfont=dict(size=config['font_size_axis'], color=config['tick_color']))
    
    fig.update_yaxes(row=1, col=1, secondary_y=True, showgrid=False, showticklabels=False,
                     range=[0, max_volume * config['volume_yaxis_range_multiplier']])
    
    # PHỤC HỒI LOGIC: Bật autorange để trục Y của RSI tự động co dãn
    fig.update_yaxes(row=2, col=1, showgrid=True, gridcolor=config['grid_color'],
                     autorange=True, fixedrange=False, # Tự động co dãn
                     tickfont=dict(size=config['font_size_axis'], color=config['tick_color']))

    # PHỤC HỒI LOGIC: Vẽ các đường lưới dọc
    for i in range(10, len(df), 10):
        fig.add_shape(
            type='line', x0=i, x1=i, y0=0, y1=1, xref='x', yref='paper',
            line=dict(color=config['grid_color'], width=1), layer='below'
        )

def _generate_xaxis_ticks(df):
    """Tạo các nhãn và vị trí cho trục X một cách thông minh."""
    dates = pd.to_datetime(df['date'])
    labels = [''] * len(df)
    indices = []
    current_month = None

    def add_day_labels(day_indices, tick_labels):
        n = len(day_indices)
        if n >= 15: num = 3
        elif 8 <= n < 15: num = 2
        elif 4 <= n < 8: num = 1
        else: return
        pos = [(n * (j + 1)) // (num + 1) for j in range(num)]
        for p in pos:
            if p < len(day_indices):
                idx = day_indices[p]
                tick_labels[idx] = str(dates.iloc[idx].day)
    
    for i, date in enumerate(dates):
        if date.month != current_month:
            if indices: add_day_labels(indices, labels)
            current_month, indices = date.month, [i]
            if date.day < 8: labels[i] = date.strftime('%b')
        else:
            indices.append(i)
    if indices: add_day_labels(indices, labels)
    return labels, list(range(len(df)))

# ==============================================================================
# 6. HÀM CHÍNH TỔNG HỢP (ORCHESTRATION FUNCTION)
# ==============================================================================
def create_chart_config(
    title_font_size,
    axis_font_size,
    tag_font_size,
    price_tag_font_size,
    min_spacing_ratio,
    margin
):
    return {
        # ---- Font Family ----
        'font_family': "Calibri",

        # ---- Font Sizes ----
        'font_size_title': title_font_size,
        'font_size_subplot_title': title_font_size,
        'font_size_axis': axis_font_size,
        'font_size_tag': tag_font_size,
        'font_size_price_tag': price_tag_font_size,

        # ---- Colors ----
        'color_up': '#00A040',
        'color_down': '#E53935',
        'tick_color': '#5E5E5E',
        'grid_color': 'rgba(230, 230, 230, 0.8)',
        'plot_bgcolor': 'white',
        'paper_bgcolor': 'white',
        'tag_bgcolor': 'rgba(255, 255, 255, 0.85)',
        
        # ---- RSI Colors ----
        'color_rsi_line': '#8c68c8',
        'color_rsi_bound_line': '#c3c5ca',
        'color_rsi_bound_fill': '#f2eef9',
        'color_rsi_bound_tag': '#7f7f7f',

        # ---- Chart Constants & Layout ----
        'label_x_position': 1.02,
        'label_min_spacing_ratio': min_spacing_ratio,
        'volume_yaxis_range_multiplier': 4.0,
        'rsi_upper_bound': 70,
        'rsi_lower_bound': 30,
        'rsi_label_min_spacing_ratio': min_spacing_ratio,
        'margin': margin, # Tăng margin trái (l) để tạo khoảng đệm
    }

def create_financial_chart(
    df: pd.DataFrame,
    width,
    height,
    line_name_dict: dict,
    line_columns: list,
    chart_config: dict,
    path: str,
    image_name: str,
    symbol_name: str = "VNINDEX",
    time_frame: str = "1D",
):
    """
    Hàm chính để tạo biểu đồ tài chính hoàn chỉnh.
    """
    if df.empty:
        print("DataFrame is empty. Cannot create chart.")
        return go.Figure()

    chart_config['symbol_name'] = symbol_name
    chart_config['time_frame'] = time_frame

    line_columns, max_volume = _prepare_chart_data(df, chart_config, line_columns)
    
    fig = make_subplots(
        rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03,
        row_heights=[0.8, 0.2], specs=[[{"secondary_y": True}], [{"secondary_y": False}]]
    )
    
    line_info = _add_technical_lines(fig, df, line_columns, line_name_dict)
    _add_volume_chart(fig, df)
    _add_candlestick_chart(fig, df, chart_config)
    _add_rsi_chart(fig, df, chart_config)
    _process_and_add_annotations(fig, df, line_info, symbol_name, chart_config)
    _configure_layout_and_axes(fig, df, max_volume, chart_config, width, height)

    full_path = os.path.join(path, image_name)
    fig.write_image(full_path, width=width, height=height, scale=2)

    return fig, fig.to_image(format="png", width=width, height=height, scale=2)