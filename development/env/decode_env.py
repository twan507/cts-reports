import os
import io
from cryptography.fernet import Fernet

# Placeholder này sẽ được thay thế
MASTER_KEY = "###MASTER_KEY_PLACEHOLDER###"

_ENV_VARS = None

def _initialize_env(): # Đổi tên hàm nội bộ cho rõ ràng hơn
    global _ENV_VARS
    if _ENV_VARS is not None:
        return
    _ENV_VARS = {}
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        app_dir = os.path.abspath(os.path.join(script_dir, '..'))
        encrypted_file_path = os.path.join(app_dir, 'data', 'env.encrypted')
        if not os.path.exists(encrypted_file_path):
            return
        with open(encrypted_file_path, 'rb') as f:
            encrypted_content = f.read()
        fernet = Fernet(MASTER_KEY.encode())
        decrypted_content = fernet.decrypt(encrypted_content).decode('utf-8')
        file_like_object = io.StringIO(decrypted_content)
        for line in file_like_object:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                _ENV_VARS[key.strip()] = value.strip().strip("'\"")
    except Exception:
        pass

# --- THAY ĐỔI Ở ĐÂY ---
def load_env(key: str, default: str = None) -> str:
    """
    Hàm chính để các module khác gọi và lấy giá trị của biến môi trường.
    """
    if _ENV_VARS is None:
        _initialize_env() # Gọi hàm nội bộ
    return _ENV_VARS.get(key, default)

_initialize_env() # Tự động nạp các biến ngay khi module được import