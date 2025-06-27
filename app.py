import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

# Sayfa ayarları
st.set_page_config(page_title="Öğrenci Takip Sistemi", layout="wide")

# ÖSYM müfredatına uygun ders ve konular
ders_konular = {
    "Türkçe": ["Paragraf", "Cümle Anlamı", "Sözcükte Anlam", "Dil Bilgisi", "Yazım Kuralları"],
    "Matematik": ["Sayılar", "Bölme ve Bölünebilme", "Üslü ve Köklü Sayılar", "Çarpanlar ve Katlar", "Rasyonel Sayılar", "Eşitsizlikler", "Problemler"],
    "Fizik": ["Kuvvet ve Hareket", "Enerji", "Elektrik", "Modern Fizik"],
    "Kimya": ["Atomun Yapısı", "Periyodik Sistem", "Kimyasal Türler", "Kimyasal Tepkimeler", "Organik Kimya"],
    "Biyoloji": ["Hücre", "Canlılar ve Enerji İlişkileri", "İnsan Fizyolojisi", "Genetik", "Ekoloji"],
    "Tarih": ["İlk Çağ Uygarlıkları", "Osmanlı Devleti", "Türkiye Cumhuriyeti Tarihi", "Modern Tarih"],
    "Coğrafya": ["Harita Bilgisi", "Doğa ve İnsan", "Türkiye’nin Fiziki Özellikleri", "Ekonomik Coğrafya"],
    "Felsefe": ["Mantık", "Ahlak", "Din Felsefesi", "Etik"],
    "Din Kültürü": ["İslamın Temel Kaynakları", "İslamın İbadetleri", "Dinler Tarihi"]
}

# Kaynak isimleri (manuel değiştirilebilir)
if "kaynaklar" not in st.session_state:
    st.session_state["kaynaklar"] = ["Kaynak 1", "Kaynak 2", "Kaynak 3"]

st.title("📘 Öğrenci Takip ve Koçluk Uygulaması")

# Menü üstte
menu = ["Haftalık Plan", "Deneme Takibi", "Ödev Takibi", "Güncel Konu Takibi", "Grafikler"]
secim = st.selectbox("Menü", menu, index=0, label_visibility="visible")

if secim == "Haftalık Plan":
    st.header("📅 Haftalık Ders Programı (Saat Görünür)")

    gunler = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
    saatler = [f"{s}:00" for s in range(9, 24)]  # 09:00 - 23:00 saatleri

    if "haftalik_program" not in st.session_state:
        st.session_state["haftalik_program"] = pd.DataFrame("", index=saatler, columns=gunler)

    st.markdown("### Ders Programını Düzenleyin")
    df = st.data_editor(st.session_state["haftalik_program"], num_rows="dynamic")
    st.session_state["haftalik_program"] = df

elif secim == "Deneme Takibi":
    st.header("📝 Deneme Sınavı Girişi")

    deneme_tur = st.selectbox("Deneme Türü", ["TYT", "AYT"])
    tarih = st.date_input("Sınav Tarihi", value=datetime.today())
    deneme_adi = st.text_input("Deneme Adı")
    net = st.number_input("Toplam Net", 0, 120, 0)
    toplam_puan = st.number_input("Toplam Puan", 0, 500, 0)

    if "denemeler" not in st.session_state:
        st.session_state["denemeler"] = []

    if st.button("➕ Deneme Ekle"):
        st.session_state["denemeler"].append({
            "Tarih": tarih,
            "Ad": deneme_adi,
            "Net": net,
            "Tür": deneme_tur,
            "Toplam Puan": toplam_puan
        })
        st.success("Deneme eklendi!")

    if st.session_state["denemeler"]:
        df_denemeler = pd.DataFrame(st.session_state["denemeler"])
        st.dataframe(df_denemeler)

elif secim == "Ödev Takibi":
    st.header("📦 Ödev Takip")

import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Yetkilendirme
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("service_account.json", scope)
client = gspread.authorize(creds)

# Google Sheet dosyasına bağlan
sheet = client.open("ogrenci_takip").sheet1

# Streamlit arayüzü
st.title("🧑‍🎓 Öğrenci Not Takip Sistemi")

isim = st.text_input("Öğrenci Adı")
ders = st.text_input("Ders Adı")
notu = st.text_input("Notu")

if st.button("✅ Kaydet"):
    if isim and ders and notu:
        sheet.append_row([isim, ders, notu])
        st.success("✅ Veri Google Sheets'e kaydedildi!")
    else:
        st.warning("Lütfen tüm alanları doldurun.")

