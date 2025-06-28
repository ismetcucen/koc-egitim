# 🚀 Vercel'de Ücretsiz Yayınlama Rehberi

## Vercel Avantajları
- ✅ Tamamen ücretsiz
- ✅ Otomatik SSL sertifikası
- ✅ Global CDN
- ✅ Otomatik deployment
- ✅ Custom domain desteği
- ✅ Analytics
- ✅ PWA desteği

## Adım 1: Vercel CLI Kurulumu

```bash
# Vercel CLI kurulumu
npm install -g vercel

# Vercel hesabı oluştur
vercel login
```

## Adım 2: Proje Hazırlığı

### requirements.txt güncelleme
```txt
Flask==2.3.3
reportlab==4.0.4
matplotlib==3.7.2
numpy==1.24.3
```

### vercel.json oluşturma
```json
{
  "version": 2,
  "builds": [
    {
      "src": "app.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "app.py"
    }
  ]
}
```

## Adım 3: Deployment

```bash
# Proje dizininde
vercel

# Sorulara cevap ver:
# - Set up and deploy? → Y
# - Which scope? → [Hesabınızı seçin]
# - Link to existing project? → N
# - What's your project's name? → koc-egitim
# - In which directory is your code located? → ./
# - Want to override the settings? → N
```

## Adım 4: Custom Domain (İsteğe Bağlı)

1. Vercel Dashboard'a git
2. Proje seç
3. Settings → Domains
4. Domain ekle

## Adım 5: PWA Test

1. https://your-app.vercel.app adresine git
2. Chrome DevTools → Application → Manifest
3. "Add to Home Screen" test et

## Maliyet: $0/ay

## Örnek URL
https://koc-egitim.vercel.app 