# === Web Scraping & Parsing ===
import requests
import feedparser
from bs4 import BeautifulSoup, Tag

# === Data Handling & Analysis ===
from alpha_vantage.foreignexchange import ForeignExchange

# === AI & Generative ===
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

# === Data Analysis & Visualization ===
from fpdf import FPDF
from fpdf.enums import XPos, YPos
import plotly.express as px
from plotly import graph_objects as go
from plotly.subplots import make_subplots