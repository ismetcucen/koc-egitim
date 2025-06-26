import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

st.set_page_config(page_title="Öğrenci Takip Sistemi", layout="wide")

st.title("📘 Öğrenci Takip ve Koçluk Uygulaması")

# Öğrenci bilgisi
st.sidebar.header("👤 Öğrenci Bilgileri")
ogrenci_adi = st.sidebar.text_input("Öğrenci Adı", "Ali Yılmaz")

# Sekmeler
sekme = st.sidebar.radio("📂 Menü Seçin", ["Haftalık Plan", "Deneme Takibi", "Ödev Takibi", "Grafikler"])

# HAFTALIK PLAN
if sekme == "Haftalık Plan":
    st.header("📅 Haftalık Ders Programı")
    gunler = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
    dersler = ["Matematik", "Geometri", "Fizik", "Kimya", "Biyoloji", "Türkçe", "Tarih", "Coğrafya", "Felsefe"]

    program = []
    for gun in gunler:
        st.subheader(gun)
        ders = st.selectbox(f"{gun} - Ders", dersler, key=gun)
        konu = st.text_input(f"{gun} - Konu", key=gun + "konu")
        sure = st.slider(f"{gun} - Süre (saat)", 0, 6, 2, key=gun + "sure")
        program.append({"Gün": gun, "Ders": ders, "Konu": konu, "Süre": sure})

    df_program = pd.DataFrame(program)
    st.dataframe(df_program)

# DENEME TAKİBİ
elif sekme == "Deneme Takibi":
    st.header("📝 Deneme Sınavı Girişi")
    tarih = st.date_input("Sınav Tarihi", value=datetime.today())
    deneme_adi = st.text_input("Deneme Adı")
    net = st.number_input("Toplam Net", 0, 120, 0)

    if "denemeler" not in st.session_state:
        st.session_state["denemeler"] = []

    if st.button("➕ Deneme Ekle"):
        st.session_state["denemeler"].append({"Tarih": tarih, "Ad": deneme_adi, "Net": net})
        st.success("Deneme eklendi!")

    if st.session_state["denemeler"]:
        df_denemeler = pd.DataFrame(st.session_state["denemeler"])
        st.dataframe(df_denemeler)

# ÖDEV TAKİBİ
elif sekme == "Ödev Takibi":
    st.header("📦 Ödev Takip")
    ders = st.selectbox("Ders Seç", ["Matematik", "Türkçe", "Fizik", "Kimya", "Biyoloji"])
    odev = st.text_input("Ödev Açıklaması")
    yapildi = st.checkbox("Yapıldı mı?")

    if "odevler" not in st.session_state:
        st.session_state["odevler"] = []

    if st.button("➕ Ödev Kaydet"):
        st.session_state["odevler"].append(
            {"Ders": ders, "Ödev": odev, "Durum": "Tamamlandı" if yapildi else "Bekliyor"})
        st.success("Ödev eklendi!")

    if st.session_state["odevler"]:
        df_odev = pd.DataFrame(st.session_state["odevler"])
        st.dataframe(df_odev)

# GRAFİKLER
elif sekme == "Grafikler":
    st.header("📊 Deneme Net Gelişimi")
    if "denemeler" in st.session_state and st.session_state["denemeler"]:
        df = pd.DataFrame(st.session_state["denemeler"])
        df = df.sort_values("Tarih")
        plt.figure(figsize=(10, 5))
        plt.plot(df["Tarih"], df["Net"], marker="o")
        plt.title("Deneme Net Gelişimi")
        plt.xlabel("Tarih")
        plt.ylabel("Net")
        plt.grid(True)
        st.pyplot(plt)
    else:
        st.info("Henüz deneme verisi girilmedi.")
