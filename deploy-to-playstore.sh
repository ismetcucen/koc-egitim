#!/bin/bash

echo "🚀 KOC Eğitim Uygulaması - Google Play Store Hazırlık Scripti"
echo "=========================================================="

# Gerekli paketleri kontrol et
echo "📦 Gerekli paketler kontrol ediliyor..."

if ! command -v node &> /dev/null; then
    echo "❌ Node.js bulunamadı. Lütfen Node.js kurun: https://nodejs.org/"
    exit 1
fi

if ! command -v npm &> /dev/null; then
    echo "❌ npm bulunamadı. Lütfen npm kurun."
    exit 1
fi

echo "✅ Node.js ve npm kurulu"

# Bubblewrap kurulumu
echo "🔧 Bubblewrap kuruluyor..."
npm install -g @bubblewrap/cli

# Uygulama URL'sini al
echo "🌐 Uygulama URL'sini girin (örn: https://your-domain.com):"
read APP_URL

if [ -z "$APP_URL" ]; then
    echo "❌ URL gerekli!"
    exit 1
fi

# Manifest URL'sini oluştur
MANIFEST_URL="$APP_URL/static/manifest.json"

echo "📱 Bubblewrap ile Android uygulaması oluşturuluyor..."
echo "Manifest URL: $MANIFEST_URL"

# Bubblewrap init
bubblewrap init --manifest "$MANIFEST_URL"

echo "🔨 Android uygulaması derleniyor..."
bubblewrap build

echo "✅ Android uygulaması oluşturuldu!"
echo ""
echo "📋 Sonraki adımlar:"
echo "1. Android Studio'yu açın"
echo "2. Oluşturulan projeyi açın"
echo "3. Build > Generate Signed Bundle/APK"
echo "4. APK veya AAB dosyasını oluşturun"
echo "5. Google Play Console'a yükleyin"
echo ""
echo "🌐 Alternatif olarak PWA Builder kullanabilirsiniz:"
echo "https://www.pwabuilder.com"
echo "URL: $APP_URL"
echo ""
echo "📚 Detaylı rehber için build-android.md dosyasını okuyun" 