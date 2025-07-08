import pymysql
import pyodbc
from pymongo import MongoClient
from sqlalchemy import create_engine, text

# Import module giải mã an toàn của chúng ta
from import_env import load_env

# --- THAY ĐỔI Ở ĐÂY ---
# Sử dụng hàm load_env() để lấy các biến môi trường đã được giải mã

# Kết nối MongoDB
mongo_client = MongoClient(load_env("DEV_MONGO_URI"))
stock_db = mongo_client["stock_db"]
ref_db = mongo_client["ref_db"]

# Tạo các engine kết nối đến các database khác nhau
vsuccess_engine = create_engine(load_env("VSUCCESS_URI"))
twan_engine = create_engine(load_env("TWAN_URI"))
cts_engine = create_engine(load_env("CTS_URI"))
t2m_engine = create_engine(load_env("T2M_URI"))