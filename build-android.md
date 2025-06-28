# Google Play Store'da Yayınlama Rehberi

## Seçenek 1: PWA'dan Android Uygulamasına Dönüştürme (Önerilen)

### 1. Bubblewrap Kullanarak (En Kolay)

```bash
# Node.js ve npm kurulu olmalı
npm install -g @bubblewrap/cli

# Proje dizininde
bubblewrap init --manifest https://your-domain.com/static/manifest.json

# Android Studio kurulu olmalı
bubblewrap build
```

### 2. PWA Builder Kullanarak (Online)

1. https://www.pwabuilder.com adresine git
2. Uygulamanızın URL'sini girin
3. "Build My PWA" butonuna tıklayın
4. Android paketini indirin

## Seçenek 2: Flutter ile Yeniden Yazma

### Avantajları:
- Daha iyi performans
- Native özellikler
- Daha profesyonel görünüm

### Dezavantajları:
- Yeniden yazma gerektirir
- Daha fazla zaman alır

## Seçenek 3: React Native ile Yeniden Yazma

### Avantajları:
- JavaScript bilgisi yeterli
- Hızlı geliştirme
- İyi performans

### Dezavantajları:
- Yeniden yazma gerektirir

## Google Play Store'da Yayınlama Adımları

### 1. Google Play Console Hesabı
- https://play.google.com/console adresine git
- $25 ödeme yap (bir kez)
- Geliştirici hesabı oluştur

### 2. Uygulama Hazırlama
- APK veya AAB dosyası hazırla
- Uygulama ikonları (512x512, 192x192)
- Ekran görüntüleri (en az 2 adet)
- Uygulama açıklaması
- Gizlilik politikası

### 3. Uygulama Bilgileri
- Uygulama adı: "KOC Eğitim Yönetimi"
- Kısa açıklama: "Eğitim kurumları için kapsamlı yönetim sistemi"
- Uzun açıklama: Detaylı özellikler
- Kategori: Eğitim
- İçerik derecelendirmesi: 3+

### 4. Teknik Gereksinimler
- Target SDK: API 33 (Android 13)
- Minimum SDK: API 21 (Android 5.0)
- Uygulama boyutu: < 150MB
- İzinler: İnternet erişimi

### 5. Yayınlama Süreci
1. "Uygulama oluştur" butonuna tıkla
2. Uygulama bilgilerini doldur
3. APK/AAB dosyasını yükle
4. Ekran görüntüleri ve açıklamaları ekle
5. İnceleme için gönder

### 6. İnceleme Süreci
- 1-7 gün sürer
- Google Play politikalarına uygunluk kontrol edilir
- Onaylandıktan sonra yayınlanır

## Önerilen Yaklaşım

1. **Kısa vadede**: PWA Builder ile APK oluştur
2. **Orta vadede**: Flutter ile yeniden yaz
3. **Uzun vadede**: Özellik geliştirme ve optimizasyon

## Gerekli Dosyalar

### Uygulama İkonları
- 512x512 PNG (ana ikon)
- 192x192 PNG (küçük ikon)
- Adaptive icon (Android 8.0+)

### Ekran Görüntüleri
- 1280x720 (yatay)
- 720x1280 (dikey)
- En az 2 adet

### Metin İçerikleri
- Uygulama adı (80 karakter)
- Kısa açıklama (80 karakter)
- Uzun açıklama (4000 karakter)
- Anahtar kelimeler
- Gizlilik politikası URL'si

## Maliyetler

- Google Play Console: $25 (bir kez)
- Sunucu hosting: Aylık $5-20
- SSL sertifikası: Ücretsiz (Let's Encrypt)
- Domain: Yıllık $10-20

## Başarı İpuçları

1. **Kaliteli ekran görüntüleri** kullan
2. **Açık ve anlaşılır açıklama** yaz
3. **Kullanıcı geri bildirimlerine** hızlı yanıt ver
4. **Düzenli güncellemeler** yap
5. **ASO (App Store Optimization)** uygula 