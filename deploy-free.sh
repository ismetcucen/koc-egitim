#!/bin/bash

echo "🚀 Ücretsiz Web Uygulaması Deployment Rehberi"
echo "============================================="

echo ""
echo "📋 Platform Seçenekleri:"
echo "1. Vercel (Önerilen) - Tamamen ücretsiz"
echo "2. Netlify - Tamamen ücretsiz"
echo "3. Render - Sınırlı ücretsiz"
echo "4. Railway - $5 kredi/ay"
echo "5. Fly.io - 3 uygulama ücretsiz"

echo ""
echo "🎯 Önerilen: Vercel"
echo "Neden Vercel?"
echo "✅ Tamamen ücretsiz"
echo "✅ Otomatik SSL"
echo "✅ Global CDN"
echo "✅ PWA desteği"
echo "✅ Kolay deployment"

echo ""
echo "📦 Gerekli paketler kontrol ediliyor..."

# Node.js kontrolü
if ! command -v node &> /dev/null; then
    echo "❌ Node.js bulunamadı"
    echo "📥 Node.js kurulumu: https://nodejs.org/"
    exit 1
fi

# npm kontrolü
if ! command -v npm &> /dev/null; then
    echo "❌ npm bulunamadı"
    exit 1
fi

echo "✅ Node.js ve npm kurulu"

echo ""
echo "🔧 Vercel CLI kuruluyor..."
npm install -g vercel

echo ""
echo "🌐 Vercel hesabı oluşturuluyor..."
vercel login

echo ""
echo "📤 Deployment başlatılıyor..."
vercel

echo ""
echo "✅ Deployment tamamlandı!"
echo ""
echo "📱 PWA Test Adımları:"
echo "1. Verilen URL'ye git"
echo "2. Chrome DevTools aç (F12)"
echo "3. Application → Manifest"
echo "4. 'Add to Home Screen' test et"
echo ""
echo "📚 Detaylı rehberler:"
echo "- Vercel: deploy-vercel.md"
echo "- Netlify: deploy-netlify.md"
echo "- Diğer: deploy-heroku.md" 