import os
import sys
import shutil
import py_compile
from dotenv import load_dotenv
from cryptography.fernet import Fernet

def main():
    # --- 1. Thiết lập các đường dẫn ---
    try:
        dev_dir = os.path.dirname(os.path.abspath(__file__))
        root_dir = os.path.abspath(os.path.join(dev_dir, '..', '..'))
        
        env_file_path = os.path.join(dev_dir, '.env')
        template_path = os.path.join(dev_dir, 'decode_env.py')
        
        app_dir = os.path.join(root_dir, 'app')
        encrypted_output_path = os.path.join(app_dir, 'data', 'env.encrypted')
        import_dir = os.path.join(app_dir, 'import')
        
        temp_py_file = os.path.join(import_dir, '_temp_import_env.py')
        final_pyc_file = os.path.join(import_dir, 'import_env.pyc')
    except Exception as e:
        print(f"❌ ERROR setting up paths: {e}")
        sys.exit(1)

    # --- 2. Mã hóa file .env ---
    try:
        load_dotenv(dotenv_path=env_file_path)
        master_key = os.getenv("MASTER_KEY")
        if not master_key:
            raise ValueError("MASTER_KEY not found in .env file.")

        with open(env_file_path, 'rb') as f:
            env_content_raw = f.read()
        
        fernet = Fernet(master_key.encode())
        encrypted_content = fernet.encrypt(env_content_raw)
        
        os.makedirs(os.path.dirname(encrypted_output_path), exist_ok=True)
        with open(encrypted_output_path, 'wb') as f:
            f.write(encrypted_content)
    except Exception as e:
        print(f"❌ ERROR during encryption: {e}")
        sys.exit(1)

    # --- 3. Ghi key vào file Python tạm thời ---
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()
        
        final_script_content = template_content.replace("###MASTER_KEY_PLACEHOLDER###", master_key)
        
        os.makedirs(import_dir, exist_ok=True)
        with open(temp_py_file, 'w', encoding='utf-8') as f:
            f.write(final_script_content)
    except Exception as e:
        print(f"❌ ERROR injecting key: {e}")
        sys.exit(1)

    # --- 4. Biên dịch sang .pyc ---
    try:
        py_compile.compile(temp_py_file, cfile=final_pyc_file, dfile=temp_py_file, doraise=True)
    except Exception as e:
        print(f"❌ ERROR during compilation: {e}")
        sys.exit(1)
        
    # --- 5. Dọn dẹp ---
    try:
        if os.path.exists(temp_py_file):
            os.remove(temp_py_file)
        # Đôi khi thư mục __pycache__ được tạo, cũng xóa luôn cho sạch
        cache_dir = os.path.join(import_dir, '__pycache__')
        if os.path.exists(cache_dir):
            shutil.rmtree(cache_dir)
    except Exception as e:
        print(f"⚠️ WARNING during cleanup: {e}")
        
    print("\n--- ✅ Thành công mã hoá env.encryted ---")

if __name__ == "__main__":
    main()