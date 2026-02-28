import pandas as pd
import streamlit as st
from config import COL_DATE, COL_SELLER_ID, COL_PRODUCT

REQUIRED_COLS = [
    COL_DATE,
    COL_SELLER_ID,
    COL_PRODUCT,
    "Tutar",
    "Miktar",
]

def _ensure_cols(df: pd.DataFrame):
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"Eksik kolon(lar): {missing}. Mevcut kolonlar: {list(df.columns)}")

def normalize(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [c.strip() for c in df.columns]
    _ensure_cols(df)

    df[COL_DATE] = pd.to_datetime(df[COL_DATE], errors="coerce")
    df = df.dropna(subset=[COL_DATE])

    df[COL_SELLER_ID] = df[COL_SELLER_ID].astype(str).str.strip()
    df[COL_PRODUCT] = df[COL_PRODUCT].astype(str).str.strip()

    # numeric
    for c in ["Tutar", "Miktar", "Fiyat", "Tescil", "Gecikme", "TopTescil"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    # kategorikler
    cat_cols = [
        "SaticiUyeDurumu","SaticiMeslekGrubu","SaticiUyeModu",
        "AliciUyeDurumu","AliciMeslekGrubu","AliciUyeModu",
        "KotasyonDurumu","BirimAdi","SartAciklama",
        "AnaGrupAdi","UstGrupAdi","EnUstGrupAdi","MahsulYili"
    ]
    for c in cat_cols:
        if c in df.columns:
            df[c] = df[c].astype(str).str.strip()

    return df

@st.cache_data
def load_excel(uploaded_file_or_path) -> pd.DataFrame:
    df = pd.read_excel(uploaded_file_or_path)
    return normalize(df)
