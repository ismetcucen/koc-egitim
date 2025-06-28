# 🏗️ Heroku Alternatifleri

## Heroku Free Plan Kaldırıldı
Heroku artık ücretsiz plan sunmuyor. İşte alternatifler:

## 1. Railway.app
- ✅ Ücretsiz plan: $5 kredi/ay
- ✅ Otomatik deployment
- ✅ PostgreSQL desteği

### Deployment:
```bash
# Railway CLI kurulumu
npm install -g @railway/cli

# Login
railway login

# Deploy
railway init
railway up
```

## 2. Render.com
- ✅ Ücretsiz plan mevcut
- ✅ Otomatik SSL
- ✅ PostgreSQL (ücretsiz)

### Deployment:
1. https://render.com adresine git
2. "New Web Service"
3. GitHub repository bağla
4. Build command: `pip install -r requirements.txt`
5. Start command: `gunicorn app:app`

## 3. Fly.io
- ✅ Ücretsiz plan: 3 uygulama
- ✅ Global deployment
- ✅ PostgreSQL

### Deployment:
```bash
# Fly CLI kurulumu
curl -L https://fly.io/install.sh | sh

# Login
fly auth login

# Deploy
fly launch
fly deploy
```

## Maliyet Karşılaştırması

| Platform | Ücretsiz Plan | Ücretli Plan |
|----------|---------------|--------------|
| Vercel | ✅ Tamamen ücretsiz | $20/ay |
| Netlify | ✅ Tamamen ücretsiz | $19/ay |
| Railway | $5 kredi/ay | $5/ay |
| Render | ✅ Sınırlı ücretsiz | $7/ay |
| Fly.io | ✅ 3 uygulama | $1.94/ay |

## Önerilen: Vercel
En kolay ve tamamen ücretsiz seçenek. 