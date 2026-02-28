# İTB Tescil Dashboard (Streamlit)

## Kurulum
```bash
cd itb_dashboard
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
# source .venv/bin/activate

pip install -r requirements.txt
```

## Çalıştırma
Varsayılan olarak uygulama Excel dosyasını sizden yüklemenizi ister.

```bash
streamlit run app.py
```

İsterseniz sabit dosya yolu ile çalıştırın:
```bash
# Windows PowerShell örnek
$env:DATA_FILE_PATH="C:\\path\\analiz.xlsx"
streamlit run app.py
```

## Giriş / Yetkilendirme
- `users.csv` içinde kullanıcılar bulunur.
- Roller: `admin`, `staff`, `member`
- `member_id` alanı **SaticiSicilNo** ile eşleşmelidir.

Şifre hash üretmek için:
```bash
python create_user.py --username uye_9484 --display "Firma Adı" --role member --member-id 9484
```
Bu komut size `users.csv` için bir satır üretir.

> Demo için auth kapatma: `AUTH_DISABLED=1` (ortam değişkeni)
