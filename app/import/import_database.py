import pymysql
import pyodbc
import os
from pymongo import MongoClient
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

mongo_client = MongoClient(os.environ.get("DEV_MONGO_URI"))
stock_db = mongo_client["stock_db"]
ref_db = mongo_client["ref_db"]

vsuccess_engine = create_engine(os.environ.get("VSUCCESS_URI"))
twan_engine = create_engine(os.environ.get("TWAN_URI"))
cts_engine = create_engine(os.environ.get("CTS_URI"))
t2m_engine = create_engine(os.environ.get("T2M_URI"))