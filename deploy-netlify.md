# 🌐 Netlify'de Ücretsiz Yayınlama

## Netlify Avantajları
- ✅ Tamamen ücretsiz
- ✅ Otomatik SSL
- ✅ Global CDN
- ✅ Form handling
- ✅ Analytics
- ✅ Git entegrasyonu

## Adım 1: GitHub'a Yükleme

```bash
# Git repository oluştur
git init
git add .
git commit -m "Initial commit"
git branch -M main

# GitHub'da repository oluştur
# Sonra:
git remote add origin https://github.com/username/koc-egitim.git
git push -u origin main
```

## Adım 2: Netlify Deployment

1. https://netlify.com adresine git
2. "Sign up" → GitHub ile giriş yap
3. "New site from Git" → GitHub
4. Repository seç
5. Build settings:
   - Build command: `pip install -r requirements.txt && python app.py`
   - Publish directory: `.`

## Adım 3: Custom Domain

1. Site settings → Domain management
2. "Add custom domain"
3. Domain adını gir

## Maliyet: $0/ay

## Örnek URL
https://koc-egitim.netlify.app 