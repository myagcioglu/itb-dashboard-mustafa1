import os
from dotenv import load_dotenv

load_dotenv()

APP_TITLE = "İTB Tescil Dashboard"
DATA_FILE_PATH = os.getenv("DATA_FILE_PATH", "")  # boşsa upload ile çalışır

# Demo amaçlı auth kapatma
AUTH_DISABLED = os.getenv("AUTH_DISABLED", "0") == "1"

# Beklenen kolonlar (analiz.xlsx ile uyumlu)
COL_DATE = "TescilTarihi"
COL_SELLER_ID = "SaticiSicilNo"
COL_PRODUCT = "UrunAdi"
COL_AMOUNT = "Tutar"
COL_QTY = "Miktar"
