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
    
    df = st.data_editor(st.session_state["haftalik_program"])

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

    ders = st.selectbox("Ders Seç", list(ders_konular.keys()))
    odev = st.text_input("Ödev Açıklaması")
    tarih = st.date_input("Teslim Tarihi", value=datetime.today())
    yapildi = st.checkbox("Yapıldı mı?")

    if "odevler" not in st.session_state:
        st.session_state["odevler"] = []

    if st.button("➕ Ödev Kaydet"):
        st.session_state["odevler"].append({
            "Ders": ders,
            "Ödev": odev,
            "Teslim Tarihi": tarih,
            "Durum": "Tamamlandı" if yapildi else "Bekliyor"
        })
        st.success("Ödev eklendi!")

    if st.session_state["odevler"]:
        df_odev = pd.DataFrame(st.session_state["odevler"])
        st.dataframe(df_odev)

elif secim == "Güncel Konu Takibi":
    st.header("📚 Güncel Konu Takibi")

    kaynaklar = st.session_state["kaynaklar"]
    with st.expander("Kaynak İsimlerini Düzenle"):
        for i in range(3):
            kaynaklar[i] = st.text_input(f"{i+1}. Kaynak Adı", kaynaklar[i])
        st.session_state["kaynaklar"] = kaynaklar

    if "konu_takip" not in st.session_state:
        st.session_state["konu_takip"] = {
            ders: {konu: [False, False, False] for konu in konular}
            for ders, konular in ders_konular.items()
        }

    for ders, konular in ders_konular.items():
        st.subheader(ders)
        cols = st.columns([4,1,1,1])
        cols[0].markdown("**Konu**")
        for i, kay in enumerate(kaynaklar):
            cols[i+1].markdown(f"**{kay}**")

        for konu in konular:
            cols = st.columns([4,1,1,1])
            cols[0].write(konu)
            for i in range(3):
                chk = cols[i+1].checkbox("", value=st.session_state["konu_takip"][ders][konu][i], key=f"{ders}_{konu}_{i}")
                st.session_state["konu_takip"][ders][konu][i] = chk

elif secim == "Grafikler":
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

# Alt bilgi
st.markdown("""<hr><center>İsmet Çüçen tarafından oluşturuldu</center>""", unsafe_allow_html=True)

