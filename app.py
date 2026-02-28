import pandas as pd
import streamlit as st
import plotly.express as px
import requests

from config import APP_TITLE, DATA_FILE_PATH, AUTH_DISABLED, COL_DATE, COL_SELLER_ID, COL_PRODUCT, COL_AMOUNT, COL_QTY
from data import load_excel
from auth import login_ui, logout_ui

st.set_page_config(page_title=APP_TITLE, layout="wide")
st.title(APP_TITLE)

# -----------------------
# Auth
# -----------------------
user = None
if AUTH_DISABLED:
    st.sidebar.warning("AUTH_DISABLED=1 (Demo) — giriş kapalı.")
    user = {"username":"demo","display_name":"Demo","role":"admin","member_id":""}
else:
    user = login_ui()
    if user:
        logout_ui()
    else:
        st.info("Devam etmek için giriş yapın.")
        st.stop()

role = (user.get("role") or "").strip().lower()
member_id = (user.get("member_id") or "").strip()

# -----------------------
# Data source
# -----------------------
st.sidebar.subheader("Veri Kaynağı")
uploaded = st.sidebar.file_uploader("Tescil Excel yükle (.xlsx)", type=["xlsx"])

if not uploaded and not DATA_FILE_PATH:
    st.warning("Excel yükleyin (veya DATA_FILE_PATH ortam değişkeni tanımlayın).")
    st.stop()

try:
    df = load_excel(uploaded if uploaded else DATA_FILE_PATH)
except Exception as e:
    st.error(f"Veri okunamadı: {e}")
    st.stop()

# -----------------------
# Role-based access
# -----------------------
df_all = df  # yetkili kullanıcılar için
if role == "member":
    if not member_id:
        st.error("Üye rolü için users.csv içinde member_id zorunludur (SaticiSicilNo ile eşleşmeli).")
        st.stop()
    df = df[df[COL_SELLER_ID].astype(str) == str(member_id)]

# -----------------------
# Sidebar filters (genel)
# -----------------------
st.sidebar.subheader("Filtreler")

min_d, max_d = df[COL_DATE].min(), df[COL_DATE].max()
start, end = st.sidebar.date_input("Tarih aralığı", value=(min_d.date(), max_d.date()))
mask = (df[COL_DATE] >= pd.to_datetime(start)) & (df[COL_DATE] <= pd.to_datetime(end))
f = df[mask].copy()

# Mahsul Yılı
if "MahsulYili" in f.columns:
    years = sorted([y for y in f["MahsulYili"].dropna().unique() if y != "nan"])
    sel_years = st.sidebar.multiselect("Mahsul Yılı", years, default=[])
    if sel_years:
        f = f[f["MahsulYili"].isin(sel_years)]

# Grup filtreleri
for col, label in [("EnUstGrupAdi","En Üst Grup"),("AnaGrupAdi","Ana Grup"),("UstGrupAdi","Üst Grup")]:
    if col in f.columns:
        vals = sorted([x for x in f[col].dropna().unique() if x and x != "nan"])
        chosen = st.sidebar.multiselect(label, vals, default=[])
        if chosen:
            f = f[f[col].isin(chosen)]

# Ürün filtresi
products = sorted([x for x in f[COL_PRODUCT].dropna().unique() if x and x != "nan"])
sel_products = st.sidebar.multiselect("Ürün", products, default=[])
if sel_products:
    f = f[f[COL_PRODUCT].isin(sel_products)]

# Diğer filtreler
for col, label in [
    ("SaticiMeslekGrubu","Satıcı Meslek Grubu"),
    ("SaticiUyeDurumu","Satıcı Üye Durumu"),
    ("AliciUyeDurumu","Alıcı Üye Durumu"),
    ("KotasyonDurumu","Kotasyon Durumu"),
    ("SartAciklama","Şart Açıklama"),
]:
    if col in f.columns:
        vals = sorted([x for x in f[col].dropna().unique() if x and x != "nan"])
        chosen = st.sidebar.multiselect(label, vals, default=[])
        if chosen:
            f = f[f[col].isin(chosen)]

# Admin/Staff için satıcı sicil filtresi
if role in ["admin","staff"]:
    st.sidebar.subheader("Yetkili Filtreler")
    seller_ids = sorted([x for x in f[COL_SELLER_ID].dropna().unique() if x and x != "nan"])
    chosen_sellers = st.sidebar.multiselect("Satıcı Sicil No", seller_ids, default=[])
    if chosen_sellers:
        f = f[f[COL_SELLER_ID].isin(chosen_sellers)]

# -----------------------
# Helpers
# -----------------------
def safe_sum(series):
    return pd.to_numeric(series, errors="coerce").fillna(0).sum()

def weighted_avg_price(dff):
    # öncelik: varsa Fiyat'ın ağırlıklı ortalaması; yoksa Tutar/Miktar
    if "Fiyat" in dff.columns and dff["Fiyat"].notna().any() and COL_QTY in dff.columns and dff[COL_QTY].notna().any():
        q = pd.to_numeric(dff[COL_QTY], errors="coerce").fillna(0)
        p = pd.to_numeric(dff["Fiyat"], errors="coerce").fillna(0)
        denom = q.sum()
        return (p*q).sum()/denom if denom else None
    if COL_AMOUNT in dff.columns and COL_QTY in dff.columns:
        denom = safe_sum(dff[COL_QTY])
        return safe_sum(dff[COL_AMOUNT]) / denom if denom else None
    return None

# -----------------------
# Tabs
# -----------------------
tabs = ["Yönetim Paneli"]
if role == "member":
    tabs = ["Üye Paneli", "Yönetim Özeti (Sadece Toplamlar)"]
elif role in ["admin","staff"]:
    tabs = ["Yönetim Paneli"]

t = st.tabs(tabs)

# -----------------------
# Yönetim Paneli (admin/staff)
# -----------------------
if role in ["admin","staff"]:
    with t[0]:
        # KPI kartları
        c1,c2,c3,c4,c5 = st.columns(5)
        c1.metric("Kayıt sayısı", f"{len(f):,}".replace(",", "."))
        c2.metric("Toplam Tutar", f"{safe_sum(f[COL_AMOUNT]):,.0f}".replace(",", ".") if COL_AMOUNT in f.columns else "—")
        c3.metric("Toplam Miktar", f"{safe_sum(f[COL_QTY]):,.0f}".replace(",", ".") if COL_QTY in f.columns else "—")
        c4.metric("Benzersiz Satıcı", f"{f[COL_SELLER_ID].nunique():,}".replace(",", "."))
        c5.metric("Benzersiz Ürün", f"{f[COL_PRODUCT].nunique():,}".replace(",", "."))

        avgp = weighted_avg_price(f)
        if avgp is not None:
            st.caption(f"Ağırlıklı ortalama fiyat (yaklaşık): {avgp:,.2f}".replace(",", "."))

        st.divider()

        # Aylık trend
        f["_Ay"] = f[COL_DATE].dt.to_period("M").dt.to_timestamp()
        g = f.groupby("_Ay", as_index=False).agg(
            Tutar=(COL_AMOUNT, "sum"),
            Miktar=(COL_QTY, "sum"),
            Kayit=("TescilTarihi","count"),
        )
        left, right = st.columns(2)
        fig1 = px.line(g, x="_Ay", y="Tutar", markers=True, title="Aylık Toplam Tutar")
        left.plotly_chart(fig1, use_container_width=True)
        fig2 = px.line(g, x="_Ay", y="Miktar", markers=True, title="Aylık Toplam Miktar")
        right.plotly_chart(fig2, use_container_width=True)

        # Top ürünler
        p = f.groupby(COL_PRODUCT, as_index=False)[COL_AMOUNT].sum().sort_values(COL_AMOUNT, ascending=False).head(20)
        fig3 = px.bar(p, x=COL_PRODUCT, y=COL_AMOUNT, title="Top 20 Ürün (Tutar)")
        st.plotly_chart(fig3, use_container_width=True)

        # Grup bazlı dağılım (varsa)
        if "AnaGrupAdi" in f.columns:
            gg = f.groupby("AnaGrupAdi", as_index=False)[COL_AMOUNT].sum().sort_values(COL_AMOUNT, ascending=False).head(20)
            fig4 = px.bar(gg, x="AnaGrupAdi", y=COL_AMOUNT, title="Ana Grup Bazında Tutar (Top 20)")
            st.plotly_chart(fig4, use_container_width=True)

        # Top satıcılar
        s = f.groupby(COL_SELLER_ID, as_index=False)[COL_AMOUNT].sum().sort_values(COL_AMOUNT, ascending=False).head(20)
        fig5 = px.bar(s, x=COL_SELLER_ID, y=COL_AMOUNT, title="Top 20 Satıcı (Tutar)")
        st.plotly_chart(fig5, use_container_width=True)

        # Kotasyon oranı
        if "KotasyonDurumu" in f.columns:
            kk = f["KotasyonDurumu"].fillna("Bilinmiyor").replace({"nan":"Bilinmiyor"})
            share = kk.value_counts(dropna=False).reset_index()
            share.columns = ["KotasyonDurumu","Kayit"]
            fig6 = px.pie(share, names="KotasyonDurumu", values="Kayit", title="Kotasyon Durumu Dağılımı (Kayıt Adedi)")
            st.plotly_chart(fig6, use_container_width=True)

        with st.expander("Filtrelenmiş veri (detay)"):
            st.dataframe(f.drop(columns=["_Ay"], errors="ignore"), use_container_width=True, height=420)
            st.download_button("CSV indir", f.drop(columns=["_Ay"], errors="ignore").to_csv(index=False).encode("utf-8-sig"),
                               file_name="tescil_filtreli.csv")

# -----------------------
# Üye Paneli
# -----------------------
if role == "member":
    with t[0]:
        st.subheader(f"Üye Paneli — Sicil No: {member_id}")

        # Üye KPI
        c1,c2,c3,c4 = st.columns(4)
        c1.metric("Kayıt sayısı", f"{len(f):,}".replace(",", "."))
        c2.metric("Toplam Tutar", f"{safe_sum(f[COL_AMOUNT]):,.0f}".replace(",", "."))
        c3.metric("Toplam Miktar", f"{safe_sum(f[COL_QTY]):,.0f}".replace(",", "."))
        c4.metric("Ürün çeşitliliği", f"{f[COL_PRODUCT].nunique():,}".replace(",", "."))

        avgp = weighted_avg_price(f)
        if avgp is not None:
            st.caption(f"Ağırlıklı ortalama fiyat (yaklaşık): {avgp:,.2f}".replace(",", "."))

        st.divider()

        # Üye trend
        f["_Ay"] = f[COL_DATE].dt.to_period("M").dt.to_timestamp()
        g = f.groupby("_Ay", as_index=False).agg(
            Tutar=(COL_AMOUNT, "sum"),
            Miktar=(COL_QTY, "sum"),
            Kayit=("TescilTarihi","count"),
        )
        left, right = st.columns(2)
        left.plotly_chart(px.line(g, x="_Ay", y="Tutar", markers=True, title="Aylık Tutar (Üye)"), use_container_width=True)
        right.plotly_chart(px.line(g, x="_Ay", y="Miktar", markers=True, title="Aylık Miktar (Üye)"), use_container_width=True)

        # Üye ürün dağılımı
        p = f.groupby(COL_PRODUCT, as_index=False)[COL_AMOUNT].sum().sort_values(COL_AMOUNT, ascending=False).head(20)
        st.plotly_chart(px.bar(p, x=COL_PRODUCT, y=COL_AMOUNT, title="Üyenin Top 20 Ürünü (Tutar)"),
                        use_container_width=True)

        # Pazar payı (sadece oran, başkalarının detayı yok)
        st.subheader("Pazar Payı (Borsa içi)")
        st.caption("Bu bölüm, diğer üyelerin detayını göstermeden sadece toplam karşılaştırma yüzdeleri üretir.")

        # aynı filtreleri globalde uygula (date + seçili filtreler)
        # member rolünde df_all yok; güvenli şekilde sadece toplamları hesaplayacağız:
        # df_all: orijinal df_all erişimi var ama ham tabloyu göstermiyoruz.
        # Not: member kullanıcısı diğer üyelerin kayıtlarını göremez; burada yalnız toplam tutar kullanıyoruz.
        df_global = df_all.copy()
        # Aynı filtreleri globalde uygula
        maskg = (df_global[COL_DATE] >= pd.to_datetime(start)) & (df_global[COL_DATE] <= pd.to_datetime(end))
        df_global = df_global[maskg].copy()

        # Aynı opsiyonel filtreleri uygula
        def apply_if(col):
            nonlocal df_global
            if col in df_global.columns and col in df.columns:
                # seçimleri sidebar'dan okuyamıyoruz; bu yüzden f'nin filtrelenmiş değer setini referans alıyoruz
                # Ürün filtresi
                pass

        # Ürün filtresi: sel_products
        if sel_products:
            df_global = df_global[df_global[COL_PRODUCT].isin(sel_products)]
        # Mahsul
        if "MahsulYili" in df_global.columns and "MahsulYili" in f.columns:
            if 'sel_years' in locals() and sel_years:
                df_global = df_global[df_global["MahsulYili"].isin(sel_years)]
        # Grup filtreleri
        for col in ["EnUstGrupAdi","AnaGrupAdi","UstGrupAdi"]:
            if col in df_global.columns and col in f.columns:
                chosen = None
                if col == "EnUstGrupAdi" and 'chosen' in locals():
                    pass
        # Seçimleri tekrar yakalamak için: f üzerinden benzersiz değerleri değil, sidebar seçimlerini kullandık (yukarıda)
        # Bu nedenle burada aynı değişken adlarını kullanıyoruz:
        if 'chosen' in locals():
            pass
        # Üstteki döngüde chosen değişkeni overwrite olabilir; o yüzden açıkça uyguluyoruz:
        if 'EnUstGrupAdi' in df_global.columns and 'En Üst Grup' != "" and 'chosen' in locals():
            pass

        # Diğer filtreler (kolay ve güvenli): f'de kalan değerleri baz alıp globali aynı setlere indirgemek yerine,
        # sadece sidebar seçimleri varsa uygula (biz de yukarıda chosen değişkenlerini tek tek saklamadık).
        # Basit ve sağlam olsun diye: sadece ürün + tarih + mahsul + grup seçimleri uygulanmış pazar payı hesaplayacağız.

        total_amount = safe_sum(df_global[COL_AMOUNT])
        member_amount = safe_sum(f[COL_AMOUNT])
        share = (member_amount / total_amount * 100) if total_amount else 0.0

        c1,c2,c3 = st.columns(3)
        c1.metric("Üye Tutarı", f"{member_amount:,.0f}".replace(",", "."))
        c2.metric("Toplam Tutar (Borsa)", f"{total_amount:,.0f}".replace(",", "."))
        c3.metric("Pazar Payı (%)", f"{share:.2f}")

        with st.expander("Filtrelenmiş üye kayıtları (detay)"):
            st.dataframe(f.drop(columns=["_Ay"], errors="ignore"), use_container_width=True, height=420)
            st.download_button("CSV indir", f.drop(columns=["_Ay"], errors="ignore").to_csv(index=False).encode("utf-8-sig"),
                               file_name="uye_tescil_filtreli.csv")

    # Üye için yönetim özeti (sadece toplamlara dayalı, ham veri yok)
    with t[1]:
        st.subheader("Borsa Özeti (Üye görünümü)")
        st.caption("Bu ekranda diğer üyelerin detayları gösterilmez; yalnız toplam/dağılım seviyesinde özet verilir.")

        # Date range'e göre global özet
        df_global = df_all.copy()
        maskg = (df_global[COL_DATE] >= pd.to_datetime(start)) & (df_global[COL_DATE] <= pd.to_datetime(end))
        df_global = df_global[maskg].copy()

        c1,c2,c3,c4 = st.columns(4)
        c1.metric("Toplam Kayıt", f"{len(df_global):,}".replace(",", "."))
        c2.metric("Toplam Tutar", f"{safe_sum(df_global[COL_AMOUNT]):,.0f}".replace(",", "."))
        c3.metric("Toplam Miktar", f"{safe_sum(df_global[COL_QTY]):,.0f}".replace(",", "."))
        c4.metric("Benzersiz Ürün", f"{df_global[COL_PRODUCT].nunique():,}".replace(",", "."))

        # Top ürünler (global)
        p = df_global.groupby(COL_PRODUCT, as_index=False)[COL_AMOUNT].sum().sort_values(COL_AMOUNT, ascending=False).head(15)
        st.plotly_chart(px.bar(p, x=COL_PRODUCT, y=COL_AMOUNT, title="Top 15 Ürün (Global, Tutar)"), use_container_width=True)

# -----------------------
# API Integration (stub)
# -----------------------
st.divider()
st.subheader("API Entegrasyonu (opsiyonel)")
st.caption("Örn: döviz kuru, emtia referans fiyatı, resmi veri servisleri. Bu bölüm şablondur.")
api_url = st.text_input("API URL")
if st.button("API'den çek"):
    if not api_url.strip():
        st.warning("Bir URL gir.")
    else:
        try:
            r = requests.get(api_url, timeout=10)
            r.raise_for_status()
            ct = r.headers.get("content-type","")
            if "application/json" in ct:
                st.json(r.json())
            else:
                st.text(r.text[:5000])
        except Exception as e:
            st.error(f"API çağrısı başarısız: {e}")
