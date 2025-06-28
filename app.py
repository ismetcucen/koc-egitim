from flask import Flask, render_template_string, request, redirect, url_for, send_file, current_app
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os
import json
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import base64
from datetime import datetime

# Türkçe karakter desteği için font kaydet
TURKISH_FONT = 'Helvetica'  # Varsayılan

# macOS'ta bulunan font yollarını dene
font_paths = [
    '/System/Library/Fonts/Supplemental/Arial Unicode MS.ttf',
    '/System/Library/Fonts/Arial.ttf',
    '/System/Library/Fonts/Helvetica.ttc',
    '/System/Library/Fonts/Supplemental/Arial.ttf',
    '/Library/Fonts/Arial.ttf'
]

for font_path in font_paths:
    try:
        if os.path.exists(font_path):
            # Normal font
            pdfmetrics.registerFont(TTFont('TurkishFont', font_path))
            # Bold font için aynı fontu kullan (ReportLab otomatik bold yapacak)
            pdfmetrics.registerFont(TTFont('TurkishFont-Bold', font_path))
            TURKISH_FONT = 'TurkishFont'
            print(f"Türkçe font başarıyla yüklendi: {font_path}")
            break
    except Exception as e:
        print(f"Font yükleme hatası {font_path}: {e}")
        continue

print(f"Kullanılacak font: {TURKISH_FONT}")

# Font kullanımı için güvenli fonksiyon
def get_font_name(is_bold=False):
    if TURKISH_FONT == 'TurkishFont':
        return 'TurkishFont-Bold' if is_bold else 'TurkishFont'
    else:
        return 'Helvetica-Bold' if is_bold else 'Helvetica'

app = Flask(__name__)

# Dinamik ders/konu ve haftalık program verileri
DERSLER = {
    "Matematik": ["Fonksiyonlar", "Kümeler", "Denklemler"],
    "Türkçe": ["Paragraf", "Dil Bilgisi", "Cümle Anlamı"],
    "Fizik": ["Hareket", "Kuvvet", "Enerji"],
    "Geometri": ["Üçgenler", "Dörtgenler", "Çember"]
}
GUNLER = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
SAATLER = [f"{h:02d}:00" for h in range(8, 25)]  # 08:00 - 00:00
# Her hücre için: ders, konu, soru_tipi, soru_adedi, youtube
weekly_plan_table = {saat: {gun: {} for gun in GUNLER} for saat in SAATLER}

# Üst bilgi (tarih ve öğrenci adı)
program_info = {"adsoyad": "", "tarih": ""}

# Konu takibi için: ders -> konu -> yayınlar (her yayın: ad, tik)
konu_takip = {d: {k: [{"ad": "", "tik": False} for _ in range(3)] for k in DERSLER[d]} for d in DERSLER}

# Deneme sınavları verisi (JSON'da saklanacak)
deneme_sinavlari = []

# Kaynak yönetimi verisi (JSON'da saklanacak)
# Format: {ders: {kaynak_adi: {tur: 'kolay/orta/zor', aciklama: '', link: ''}}}
kaynaklar = {}

def load_data():
    try:
        with open('data.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except Exception:
        return {}

def save_data():
    data = {
        'weekly_plan_table': weekly_plan_table,
        'konu_takip': konu_takip,
        'DERSLER': DERSLER,
        'program_info': program_info,
        'deneme_sinavlari': deneme_sinavlari,
        'kaynaklar': kaynaklar
    }
    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# --- Uygulama başlarken verileri yükle ---
data = load_data()
if data:
    weekly_plan_table = data.get('weekly_plan_table', weekly_plan_table)
    konu_takip = data.get('konu_takip', konu_takip)
    DERSLER = data.get('DERSLER', DERSLER)
    program_info = data.get('program_info', program_info)
    # Eski string formatını yeni dictionary formatına dönüştür
    eski_deneme_sinavlari = data.get('deneme_sinavlari', [])
    if eski_deneme_sinavlari and isinstance(eski_deneme_sinavlari[0], str):
        # Eski string formatı, yeni formatına dönüştür
        deneme_sinavlari = []
        for i, sinav in enumerate(eski_deneme_sinavlari):
            deneme_sinavlari.append({
                'tur': 'TYT',  # Varsayılan değer
                'ad': sinav,
                'tarih': datetime.now().strftime('%Y-%m-%d'),
                'net': 0.0,
                'puan': 0.0
            })
    else:
        deneme_sinavlari = eski_deneme_sinavlari
    kaynaklar = data.get('kaynaklar', {})

# --- Her değişiklikte save_data() çağrılacak ---

# Menüde aktif sayfa kontrolü için yardımcı fonksiyon
def menu_html(active):
    return f'''
    <div class="menu-bar">
        <a href="/" style="text-decoration:none;"><button class="menu-btn {'active' if active=='program' else ''}">📅 Haftalık Ders Programı</button></a>
        <a href="/konu-takip" style="text-decoration:none;"><button class="menu-btn {'active' if active=='konu' else ''}">📚 Konu Takibi</button></a>
        <a href="/deneme-takip" style="text-decoration:none;"><button class="menu-btn {'active' if active=='deneme' else ''}">📊 Deneme Takibi</button></a>
        <a href="/kaynak-yonetimi" style="text-decoration:none;"><button class="menu-btn {'active' if active=='kaynak' else ''}">📖 Kaynak Yönetimi</button></a>
        <a href="/istatistikler" style="text-decoration:none;"><button class="menu-btn {'active' if active=='istatistikler' else ''}">📈 İstatistikler</button></a>
    </div>
    '''

@app.route('/', methods=['GET', 'POST'])
def dashboard():
    global program_info
    if request.method == 'POST' and 'adsoyad' in request.form and 'tarih' in request.form:
        program_info['adsoyad'] = request.form['adsoyad']
        program_info['tarih'] = request.form['tarih']
        save_data()
    return render_template_string('''
    <html>
    <head>
        <title>İsmet ÇÜÇEN Eğitim Danışmanlığı</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        
        <!-- PWA Meta Etiketleri -->
        <meta name="theme-color" content="#764ba2">
        <meta name="apple-mobile-web-app-capable" content="yes">
        <meta name="apple-mobile-web-app-status-bar-style" content="default">
        <meta name="apple-mobile-web-app-title" content="Eğitim Takip">
        <meta name="msapplication-TileColor" content="#764ba2">
        <meta name="msapplication-config" content="/static/browserconfig.xml">
        
        <!-- Manifest -->
        <link rel="manifest" href="/static/manifest.json">
        
        <!-- Apple Touch Icons -->
        <link rel="apple-touch-icon" href="/static/logo.png">
        <link rel="apple-touch-icon" sizes="152x152" href="/static/logo.png">
        <link rel="apple-touch-icon" sizes="180x180" href="/static/logo.png">
        <link rel="apple-touch-icon" sizes="167x167" href="/static/logo.png">
        
        <!-- Favicon -->
        <link rel="icon" type="image/png" sizes="32x32" href="/static/logo.png">
        <link rel="icon" type="image/png" sizes="16x16" href="/static/logo.png">
        
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            
            body { 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                color: #333;
            }
            
            .container { 
                max-width: 1200px; 
                margin: 20px auto; 
                background: rgba(255, 255, 255, 0.95);
                backdrop-filter: blur(10px);
                border-radius: 20px; 
                box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
                padding: 30px;
                border: 1px solid rgba(255, 255, 255, 0.2);
            }
            
            .headerbox { 
                display: flex; 
                flex-direction: column; 
                align-items: center; 
                margin-bottom: 30px;
                position: relative;
            }
            
            .logo { 
                margin-bottom: 15px;
                position: relative;
            }
            
            .logo img { 
                width: 140px; 
                height: auto;
                filter: drop-shadow(0 4px 8px rgba(0, 0, 0, 0.1));
                transition: transform 0.3s ease;
            }
            
            .logo img:hover {
                transform: scale(1.05);
            }
            
            h1 { 
                color: #2d3748; 
                text-align: center; 
                font-size: 2.2em; 
                margin: 0 0 10px 0; 
                letter-spacing: 1px;
                font-weight: 700;
                background: linear-gradient(135deg, #667eea, #764ba2);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
            }
            
            .info-labels { 
                text-align: center; 
                font-size: 1.1em; 
                color: #4a5568; 
                margin-bottom: 15px;
                font-weight: 500;
            }
            
            .info-form { 
                display: flex; 
                justify-content: center; 
                gap: 15px; 
                margin-bottom: 20px;
                flex-wrap: wrap;
            }
            
            .info-form input[type="text"], 
            .info-form input[type="date"] { 
                padding: 12px 16px; 
                border-radius: 12px; 
                border: 2px solid #e2e8f0;
                font-size: 1em;
                background: rgba(255, 255, 255, 0.9);
                transition: all 0.3s ease;
                min-width: 200px;
            }
            
            .info-form input:focus {
                outline: none;
                border-color: #667eea;
                box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
                transform: translateY(-2px);
            }
            
            .info-form button { 
                padding: 12px 24px; 
                border-radius: 12px; 
                border: none; 
                background: linear-gradient(135deg, #667eea, #764ba2);
                color: #fff; 
                font-size: 1em; 
                cursor: pointer;
                font-weight: 600;
                transition: all 0.3s ease;
                box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
            }
            
            .info-form button:hover { 
                transform: translateY(-2px);
                box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
            }
            
            .menu-bar { 
                display: flex; 
                justify-content: center; 
                gap: 20px; 
                margin: 25px 0 30px 0;
                flex-wrap: wrap;
            }
            
            .menu-btn { 
                background: linear-gradient(135deg, #f7fafc, #edf2f7);
                color: #4a5568; 
                border: none; 
                border-radius: 12px; 
                padding: 12px 24px; 
                font-size: 1em; 
                cursor: pointer; 
                transition: all 0.3s ease;
                font-weight: 600;
                box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
                position: relative;
                overflow: hidden;
            }
            
            .menu-btn::before {
                content: '';
                position: absolute;
                top: 0;
                left: -100%;
                width: 100%;
                height: 100%;
                background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.4), transparent);
                transition: left 0.5s;
            }
            
            .menu-btn:hover::before {
                left: 100%;
            }
            
            .menu-btn.active, 
            .menu-btn:hover { 
                background: linear-gradient(135deg, #667eea, #764ba2);
                color: #fff;
                transform: translateY(-2px);
                box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
            }
            
            .download-btn { 
                background: linear-gradient(135deg, #48bb78, #38a169);
                color: #fff; 
                border: none; 
                border-radius: 12px; 
                padding: 12px 24px; 
                font-size: 1em; 
                cursor: pointer; 
                margin-bottom: 20px; 
                float: right;
                font-weight: 600;
                transition: all 0.3s ease;
                box-shadow: 0 4px 15px rgba(72, 187, 120, 0.3);
            }
            
            .download-btn:hover { 
                transform: translateY(-2px);
                box-shadow: 0 8px 25px rgba(72, 187, 120, 0.4);
            }
            
            .add-lesson-btn { 
                background: linear-gradient(135deg, #667eea, #764ba2);
                color: #fff; 
                border: none; 
                border-radius: 12px; 
                padding: 12px 24px; 
                font-size: 1em; 
                cursor: pointer; 
                margin-bottom: 20px;
                font-weight: 600;
                transition: all 0.3s ease;
                box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
            }
            
            .add-lesson-btn:hover { 
                transform: translateY(-2px);
                box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
            }
            
            .plan-table { 
                width: 100%; 
                border-collapse: separate;
                border-spacing: 0;
                margin-bottom: 20px; 
                font-size: 0.95em;
                border-radius: 15px;
                overflow: hidden;
                box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
            }
            
            .plan-table th, 
            .plan-table td { 
                border: none;
                padding: 12px 8px; 
                text-align: center; 
                min-width: 100px;
                position: relative;
            }
            
            .plan-table th { 
                background: linear-gradient(135deg, #667eea, #764ba2);
                color: white;
                font-size: 1em;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }
            
            .plan-table td { 
                background: rgba(255, 255, 255, 0.9);
                font-size: 0.9em; 
                vertical-align: middle; 
                cursor: pointer;
                transition: all 0.3s ease;
                border-bottom: 1px solid #f1f5f9;
            }
            
            .plan-table tr:nth-child(even) td {
                background: rgba(248, 250, 252, 0.9);
            }
            
            .plan-table td:hover { 
                background: linear-gradient(135deg, #e6fffa, #b2f5ea);
                transform: scale(1.02);
                box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
                z-index: 1;
            }
            
            .yt-label { 
                color: #e53e3e; 
                font-size: 0.9em;
                font-weight: 600;
            }
            
            .edit-form { 
                display: none; 
                position: fixed; 
                top: 50%; 
                left: 50%; 
                transform: translate(-50%, -50%); 
                background: rgba(255, 255, 255, 0.95);
                backdrop-filter: blur(10px);
                border-radius: 20px; 
                box-shadow: 0 20px 40px rgba(0, 0, 0, 0.2);
                padding: 40px; 
                z-index: 1000;
                border: 1px solid rgba(255, 255, 255, 0.2);
                min-width: 400px;
            }
            
            .edit-form label { 
                display: block; 
                margin-bottom: 12px;
                font-weight: 600;
                color: #2d3748;
            }
            
            .edit-form select, 
            .edit-form input { 
                width: 100%; 
                padding: 12px; 
                margin-bottom: 20px;
                border: 2px solid #e2e8f0;
                border-radius: 10px;
                font-size: 1em;
                transition: all 0.3s ease;
            }
            
            .edit-form select:focus,
            .edit-form input:focus {
                outline: none;
                border-color: #667eea;
                box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
            }
            
            .edit-form button { 
                margin-right: 15px;
                padding: 10px 20px;
                border-radius: 10px;
                border: none;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.3s ease;
            }
            
            .edit-form button[type="submit"] {
                background: linear-gradient(135deg, #48bb78, #38a169);
                color: white;
            }
            
            .edit-form button[type="button"] {
                background: linear-gradient(135deg, #f56565, #e53e3e);
                color: white;
            }
            
            .edit-form button:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
            }
            
            .overlay { 
                display: none; 
                position: fixed; 
                top: 0; 
                left: 0; 
                width: 100vw; 
                height: 100vh; 
                background: rgba(0, 0, 0, 0.5);
                backdrop-filter: blur(5px);
                z-index: 999; 
            }
            
            .add-lesson-form { 
                display: none; 
                position: fixed; 
                top: 50%; 
                left: 50%; 
                transform: translate(-50%, -50%); 
                background: rgba(255, 255, 255, 0.95);
                backdrop-filter: blur(10px);
                border-radius: 20px; 
                box-shadow: 0 20px 40px rgba(0, 0, 0, 0.2);
                padding: 40px; 
                z-index: 1001;
                border: 1px solid rgba(255, 255, 255, 0.2);
                min-width: 400px;
            }
            
            .add-lesson-form label { 
                display: block; 
                margin-bottom: 12px;
                font-weight: 600;
                color: #2d3748;
            }
            
            .add-lesson-form input, 
            .add-lesson-form textarea { 
                width: 100%; 
                padding: 12px; 
                margin-bottom: 20px;
                border: 2px solid #e2e8f0;
                border-radius: 10px;
                font-size: 1em;
                transition: all 0.3s ease;
            }
            
            .add-lesson-form input:focus,
            .add-lesson-form textarea:focus {
                outline: none;
                border-color: #667eea;
                box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
            }
            
            @media (max-width: 768px) {
                .container { margin: 10px; padding: 20px; }
                .info-form { flex-direction: column; align-items: center; }
                .menu-bar { flex-direction: column; align-items: center; }
                .plan-table { font-size: 0.8em; }
                .plan-table th, .plan-table td { padding: 8px 4px; }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="headerbox">
                <div class="logo">
                    <img src="{{ url_for('static', filename='logo.png') }}" alt="Logo">
                </div>
                <h1>İsmet ÇÜÇEN Eğitim Danışmanlığı</h1>
                {% if program_info['adsoyad'] or program_info['tarih'] %}
                <div class="info-labels">
                    {% if program_info['adsoyad'] %} <b>Öğrenci:</b> {{ program_info['adsoyad'] }} {% endif %}
                    {% if program_info['tarih'] %} | <b>Tarih:</b> {{ program_info['tarih'] }} {% endif %}
                </div>
                {% endif %}
                <form class="info-form" method="post" action="/">
                    <input type="text" name="adsoyad" placeholder="Öğrenci Ad Soyad" value="{{ program_info['adsoyad'] }}" required>
                    <input type="date" name="tarih" value="{{ program_info['tarih'] }}" required>
                    <button type="submit">Kaydet</button>
                </form>
            </div>
            {{ menu_html | safe }}
            <form method="get" action="/download-pdf" style="display:inline;">
                <button class="download-btn" type="submit">📄 PDF Olarak İndir</button>
            </form>
            <button class="add-lesson-btn" onclick="openAddLessonForm()">➕ Ders/Konu Ekle</button>
            <div class="tab">
                <h2 style="font-size:1.3em; margin: 15px 0 20px 0; color: #2d3748; text-align: center;">Haftalık Ders Programı</h2>
                <table class="plan-table">
                    <tr>
                        <th>Saat</th>
                        {% for g in gunler %}<th>{{g}}</th>{% endfor %}
                    </tr>
                    {% for s in saatler %}
                    <tr>
                        <td><b>{{s}}</b></td>
                        {% for g in gunler %}
                        <td onclick="openEditForm('{{s}}','{{g}}')">
                            {% set cell = plan_table[s][g] %}
                            {% if cell.ders %}
                                <b>{{cell.ders}}</b><br>
                                <span style="font-size:0.9em;color:#555">{{cell.konu}}</span>
                                {% if cell.soru_tipi %}<br><span style="font-size:0.9em;color:#667eea">{{cell.soru_tipi}}</span>{% endif %}
                                {% if cell.soru_adedi %}<br><span style="font-size:0.9em;color:#e53e3e">{{cell.soru_adedi}} soru</span>{% endif %}
                                {% if cell.youtube %}<br><span class="yt-label">🎬 {{cell.youtube}}</span>{% endif %}
                                {% if cell.kaynak %}<br><span style="font-size:0.8em;color:#059669;background:#dcfce7;padding:2px 6px;border-radius:6px;">📚 {{cell.kaynak}}</span>{% endif %}
                            {% else %}-{% endif %}
                        </td>
                        {% endfor %}
                    </tr>
                    {% endfor %}
                </table>
            </div>
        </div>
        <div class="overlay" id="overlay" onclick="closeEditForm();closeAddLessonForm();"></div>
        <form class="edit-form" id="editForm" method="post" action="/edit-cell" onsubmit="return submitEditForm()">
            <h3>Ders/Konu ve Soru Ekle</h3>
            <input type="hidden" name="hour" id="form-hour">
            <input type="hidden" name="day" id="form-day">
            <label>Ders:
                <select name="lesson" id="form-lesson" onchange="updateFormTopics()">
                    {% for d in dersler.keys() %}
                    <option value="{{d}}">{{d}}</option>
                    {% endfor %}
                </select>
            </label>
            <label>Konu:
                <select name="topic" id="form-topic">
                    {% for t in dersler[dersler.keys()|list|first] %}
                    <option value="{{t}}">{{t}}</option>
                    {% endfor %}
                </select>
            </label>
            <label>Soru Çözümü:
                <input type="text" name="soru_tipi" id="form-soru-tipi" placeholder="Test, Deneme, vb.">
            </label>
            <label>Soru Adedi:
                <input type="number" name="soru_adedi" id="form-soru-adedi" min="1" max="500">
            </label>
            <label>YouTube Video:
                <input type="text" name="youtube" id="form-youtube" placeholder="Video başlığı veya linki (isteğe bağlı)">
            </label>
            <label>Kaynak:
                <select name="kaynak" id="form-kaynak">
                    <option value="">Kaynak seçin...</option>
                </select>
            </label>
            <button type="submit">Kaydet</button>
            <button type="button" onclick="closeEditForm()">İptal</button>
        </form>
        <form class="add-lesson-form" id="addLessonForm" method="post" action="/add-lesson" onsubmit="return submitAddLessonForm()">
            <h3>Yeni Ders/Konu Ekle</h3>
            <label>Ders Adı:
                <input type="text" name="lesson_name" id="lesson_name" required>
            </label>
            <label>Konular (her satıra bir konu yaz):
                <textarea name="topics" id="topics" rows="5" required></textarea>
            </label>
            <button type="submit">Ekle</button>
            <button type="button" onclick="closeAddLessonForm()">İptal</button>
        </form>
        <script>
        // Dinamik konu güncelleme (tablo formu için)
        const dersler = {{ dersler|tojson }};
        const kaynaklar = {{ kaynaklar|tojson }};
        function updateFormTopics() {
            var lesson = document.getElementById('form-lesson').value;
            var topicSelect = document.getElementById('form-topic');
            topicSelect.innerHTML = '';
            dersler[lesson].forEach(function(topic) {
                var opt = document.createElement('option');
                opt.value = topic;
                opt.innerHTML = topic;
                topicSelect.appendChild(opt);
            });
            updateFormKaynaklar();
        }
        function updateFormKaynaklar() {
            var lesson = document.getElementById('form-lesson').value;
            var kaynakSelect = document.getElementById('form-kaynak');
            kaynakSelect.innerHTML = '<option value="">Kaynak seçin...</option>';
            if (kaynaklar[lesson]) {
                Object.keys(kaynaklar[lesson]).forEach(function(kaynakAdi) {
                    var opt = document.createElement('option');
                    opt.value = kaynakAdi;
                    opt.innerHTML = kaynakAdi + ' (' + kaynaklar[lesson][kaynakAdi].tur + ')';
                    kaynakSelect.appendChild(opt);
                });
            }
        }
        // Hücreye tıklayınca formu aç
        function openEditForm(hour, day) {
            document.getElementById('form-hour').value = hour;
            document.getElementById('form-day').value = day;
            document.getElementById('editForm').style.display = 'block';
            document.getElementById('overlay').style.display = 'block';
        }
        function closeEditForm() {
            document.getElementById('editForm').style.display = 'none';
            document.getElementById('overlay').style.display = 'none';
        }
        function openAddLessonForm() {
            document.getElementById('addLessonForm').style.display = 'block';
            document.getElementById('overlay').style.display = 'block';
        }
        function closeAddLessonForm() {
            document.getElementById('addLessonForm').style.display = 'none';
            document.getElementById('overlay').style.display = 'none';
        }
        function submitEditForm() {
            closeEditForm();
            return true;
        }
        function submitAddLessonForm() {
            closeAddLessonForm();
            return true;
        }
        
        // PWA Service Worker Kaydı
        if ('serviceWorker' in navigator) {
            window.addEventListener('load', function() {
                navigator.serviceWorker.register('/static/sw.js')
                    .then(function(registration) {
                        console.log('Service Worker başarıyla kaydedildi:', registration.scope);
                    })
                    .catch(function(error) {
                        console.log('Service Worker kaydı başarısız:', error);
                    });
            });
        }
        
        // PWA Install Prompt
        let deferredPrompt;
        window.addEventListener('beforeinstallprompt', (e) => {
            e.preventDefault();
            deferredPrompt = e;
            
            // Install butonu göster (isteğe bağlı)
            const installButton = document.createElement('button');
            installButton.textContent = '📱 Uygulamayı Yükle';
            installButton.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                background: linear-gradient(135deg, #667eea, #764ba2);
                color: white;
                border: none;
                border-radius: 10px;
                padding: 10px 15px;
                font-size: 14px;
                cursor: pointer;
                z-index: 1000;
                box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
            `;
            installButton.onclick = () => {
                deferredPrompt.prompt();
                deferredPrompt.userChoice.then((choiceResult) => {
                    if (choiceResult.outcome === 'accepted') {
                        console.log('Kullanıcı uygulamayı yükledi');
                    }
                    deferredPrompt = null;
                    installButton.remove();
                });
            };
            document.body.appendChild(installButton);
        });
        </script>
    </body>
    </html>
    ''',
    dersler=DERSLER,
    gunler=GUNLER,
    saatler=SAATLER,
    plan_table=weekly_plan_table,
    program_info=program_info,
    kaynaklar=kaynaklar,
    menu_html=menu_html('program')
    )

@app.route('/edit-cell', methods=['POST'])
def edit_cell():
    hour = request.form['hour']
    day = request.form['day']
    lesson = request.form['lesson']
    topic = request.form['topic']
    soru_tipi = request.form.get('soru_tipi', '')
    soru_adedi = request.form.get('soru_adedi', '')
    youtube = request.form.get('youtube', '')
    kaynak = request.form.get('kaynak', '')
    weekly_plan_table[hour][day] = {
        'ders': lesson,
        'konu': topic,
        'soru_tipi': soru_tipi,
        'soru_adedi': soru_adedi,
        'youtube': youtube,
        'kaynak': kaynak
    }
    save_data()
    return redirect(url_for('dashboard'))

@app.route('/add-lesson', methods=['POST'])
def add_lesson():
    lesson_name = request.form['lesson_name'].strip()
    topics = [t.strip() for t in request.form['topics'].split('\n') if t.strip()]
    if lesson_name and topics:
        DERSLER[lesson_name] = topics
        konu_takip[lesson_name] = {k: [{"ad": "", "tik": False} for _ in range(3)] for k in topics}
        save_data()
    return redirect(url_for('dashboard'))

@app.route('/download-pdf', methods=['GET'])
def download_pdf():
    # PDF oluştur
    pdf_io = BytesIO()
    doc = SimpleDocTemplate(pdf_io, pagesize=A4, leftMargin=20, rightMargin=20, topMargin=30, bottomMargin=30)
    story = []
    
    # Logo ekle
    logo_path = os.path.join('static', 'logo.png')
    if os.path.exists(logo_path):
        logo = Image(logo_path)
        logo.drawHeight = 50
        logo.drawWidth = 100
        logo.hAlign = 'CENTER'
        story.append(logo)
        story.append(Spacer(1, 8))
    
    # Başlık - Türkçe karakter desteği için
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=14,
        spaceAfter=15,
        alignment=1,  # Center
        fontName=get_font_name()
    )
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontName=get_font_name(),
        fontSize=10
    )
    heading2_style = ParagraphStyle(
        'CustomHeading2',
        parent=styles['Heading2'],
        fontName=get_font_name(),
        fontSize=12,
        spaceAfter=10
    )
    
    story.append(Paragraph("İsmet ÇÜÇEN Eğitim Danışmanlığı", title_style))
    
    # Öğrenci bilgileri
    if program_info['adsoyad'] or program_info['tarih']:
        info_text = ""
        if program_info['adsoyad']:
            info_text += f"Öğrenci: {program_info['adsoyad']} "
        if program_info['tarih']:
            info_text += f"Tarih: {program_info['tarih']}"
        story.append(Paragraph(info_text, normal_style))
        story.append(Spacer(1, 15))
    
    # Tablo başlığı
    story.append(Paragraph("Haftalık Ders Programı", heading2_style))
    story.append(Spacer(1, 10))
    
    # Tablo verisi
    table_data = []
    
    # Başlık satırı
    header_row = ['Saat'] + GUNLER
    table_data.append(header_row)
    
    # Veri satırları
    for saat in SAATLER:
        row = [saat]
        for gun in GUNLER:
            cell = weekly_plan_table[saat][gun]
            if cell.get('ders'):
                cell_text = f"{cell['ders']}\n{cell.get('konu', '')}"
                if cell.get('soru_tipi'):
                    cell_text += f"\n{cell['soru_tipi']}"
                if cell.get('soru_adedi'):
                    cell_text += f"\n{cell['soru_adedi']} soru"
                if cell.get('youtube'):
                    cell_text += f"\n🎬 {cell['youtube']}"
                if cell.get('kaynak'):
                    cell_text += f"\n📚 {cell['kaynak']}"
            else:
                cell_text = "-"
            row.append(cell_text)
        table_data.append(row)
    
    # Tablo oluştur - Sayfa genişliğine uygun sütun genişlikleri
    available_width = A4[0] - 40  # Sayfa genişliği - kenar boşlukları
    saat_width = 0.6 * inch
    gun_width = (available_width - saat_width) / len(GUNLER)
    
    table = Table(table_data, colWidths=[saat_width] + [gun_width] * len(GUNLER))
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), get_font_name(is_bold=True)),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 6),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.beige, colors.white]),
        ('LEFTPADDING', (0, 0), (-1, -1), 2),
        ('RIGHTPADDING', (0, 0), (-1, -1), 2),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 3),
        ('FONTNAME', (0, 1), (-1, -1), get_font_name()),
    ]))
    
    story.append(table)
    doc.build(story)
    
    pdf_io.seek(0)
    return send_file(pdf_io, mimetype='application/pdf', as_attachment=True, download_name='haftalik_program.pdf')

@app.route('/konu-takip', methods=['GET', 'POST'])
def konu_takip_sayfa():
    global konu_takip, DERSLER
    secili_ders = request.args.get('ders', list(DERSLER.keys())[0] if DERSLER else '')
    mesaj = ""
    
    # Yeni ders ekleme
    if request.method == 'POST' and 'yeni_ders' in request.form:
        yeni_ders = request.form['yeni_ders'].strip()
        if yeni_ders and yeni_ders not in DERSLER:
            DERSLER[yeni_ders] = []
            konu_takip[yeni_ders] = {}
            mesaj = f"'{yeni_ders}' dersi eklendi."
            save_data()
    
    # Yeni konu ekleme
    if request.method == 'POST' and 'yeni_konu' in request.form:
        yeni_konu = request.form['yeni_konu'].strip()
        ders_for_konu = request.form.get('ders_for_konu', secili_ders)
        if yeni_konu and ders_for_konu in DERSLER and yeni_konu not in DERSLER[ders_for_konu]:
            DERSLER[ders_for_konu].append(yeni_konu)
            konu_takip[ders_for_konu][yeni_konu] = [{"ad": "", "tik": False} for _ in range(3)]
            mesaj = f"'{yeni_konu}' konusu eklendi."
            save_data()
    
    # Yayın silme
    if request.method == 'POST' and 'sil_yayin' in request.form:
        ders = request.form['sil_ders']
        konu = request.form['sil_konu']
        yayin_index = int(request.form['sil_index'])
        if ders in konu_takip and konu in konu_takip[ders]:
            konu_takip[ders][konu][yayin_index] = {"ad": "", "tik": False}
            mesaj = "Yayın silindi."
            save_data()
    
    # Konu silme
    if request.method == 'POST' and 'sil_konu' in request.form:
        ders = request.form['sil_ders']
        konu = request.form['sil_konu_adi']
        if ders in DERSLER and konu in DERSLER[ders]:
            DERSLER[ders].remove(konu)
            if ders in konu_takip and konu in konu_takip[ders]:
                del konu_takip[ders][konu]
            mesaj = f"'{konu}' konusu silindi."
            save_data()
    
    # Yayın adları ve tikler
    if request.method == 'POST' and 'ders' in request.form and 'yeni_ders' not in request.form and 'yeni_konu' not in request.form and 'sil_yayin' not in request.form:
        secili_ders = request.form['ders']
        for idx, konu in enumerate(DERSLER[secili_ders]):
            for j in range(3):
                ad = request.form.get(f"ad_{idx}_{j}", "")
                tik = request.form.get(f"tik_{idx}_{j}") == "on"
                konu_takip[secili_ders][konu][j]['ad'] = ad
                konu_takip[secili_ders][konu][j]['tik'] = tik
        save_data()
    return render_template_string('''
    <html>
    <head>
        <title>Konu Takibi - İsmet ÇÜÇEN Eğitim Danışmanlığı</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            
            body { 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                color: #333;
            }
            
            .container { 
                max-width: 1200px; 
                margin: 20px auto; 
                background: rgba(255, 255, 255, 0.95);
                backdrop-filter: blur(10px);
                border-radius: 20px; 
                box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
                padding: 30px;
                border: 1px solid rgba(255, 255, 255, 0.2);
            }
            
            h2 { 
                text-align: center; 
                color: #2d3748; 
                margin-bottom: 25px;
                font-size: 2em;
                font-weight: 700;
                background: linear-gradient(135deg, #667eea, #764ba2);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
            }
            
            .ders-sec { 
                display: flex; 
                justify-content: center; 
                margin-bottom: 25px;
                align-items: center;
                gap: 15px;
            }
            
            .ders-sec select { 
                font-size: 1em; 
                padding: 12px 20px; 
                border-radius: 12px; 
                border: 2px solid #e2e8f0;
                background: rgba(255, 255, 255, 0.9);
                transition: all 0.3s ease;
                min-width: 200px;
            }
            
            .ders-sec select:focus {
                outline: none;
                border-color: #667eea;
                box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
            }
            
            .ders-sec label {
                font-weight: 600;
                color: #4a5568;
            }
            
            table { 
                width: 100%; 
                border-collapse: separate;
                border-spacing: 0;
                font-size: 0.95em;
                border-radius: 15px;
                overflow: hidden;
                box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
                margin-bottom: 20px;
            }
            
            th, td { 
                border: none;
                padding: 12px 8px; 
                text-align: center;
                position: relative;
            }
            
            th { 
                background: linear-gradient(135deg, #667eea, #764ba2);
                color: white;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }
            
            td { 
                background: rgba(255, 255, 255, 0.9);
                border-bottom: 1px solid #f1f5f9;
            }
            
            tr:nth-child(even) td {
                background: rgba(248, 250, 252, 0.9);
            }
            
            input[type='text'] { 
                width: 120px; 
                padding: 8px 12px; 
                border-radius: 8px; 
                border: 2px solid #e2e8f0;
                font-size: 0.9em;
                transition: all 0.3s ease;
            }
            
            input[type='text']:focus {
                outline: none;
                border-color: #667eea;
                box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
            }
            
            input[type='checkbox'] { 
                width: 20px; 
                height: 20px;
                accent-color: #667eea;
                cursor: pointer;
            }
            
            .save-btn { 
                background: linear-gradient(135deg, #667eea, #764ba2);
                color: #fff; 
                border: none; 
                border-radius: 12px; 
                padding: 12px 30px; 
                font-size: 1em; 
                cursor: pointer; 
                margin-top: 20px;
                font-weight: 600;
                transition: all 0.3s ease;
                box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
            }
            
            .save-btn:hover { 
                transform: translateY(-2px);
                box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
            }
            
            .ekle-btn { 
                background: linear-gradient(135deg, #48bb78, #38a169);
                color: #fff; 
                border: none; 
                border-radius: 10px; 
                padding: 8px 20px; 
                font-size: 0.95em; 
                cursor: pointer; 
                margin-left: 10px;
                font-weight: 600;
                transition: all 0.3s ease;
                box-shadow: 0 4px 15px rgba(72, 187, 120, 0.3);
            }
            
            .ekle-btn:hover { 
                transform: translateY(-2px);
                box-shadow: 0 8px 25px rgba(72, 187, 120, 0.4);
            }
            
            .sil-btn { 
                background: linear-gradient(135deg, #f56565, #e53e3e);
                color: #fff; 
                border: none; 
                border-radius: 8px; 
                padding: 6px 12px; 
                font-size: 0.85em; 
                cursor: pointer;
                font-weight: 600;
                transition: all 0.3s ease;
                box-shadow: 0 2px 10px rgba(245, 101, 101, 0.3);
            }
            
            .sil-btn:hover { 
                transform: translateY(-1px);
                box-shadow: 0 4px 15px rgba(245, 101, 101, 0.4);
            }
            
            .ekle-form { 
                display: inline-block; 
                margin-bottom: 15px;
                background: rgba(255, 255, 255, 0.8);
                padding: 15px;
                border-radius: 12px;
                box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
            }
            
            .ekle-form input[type="text"] {
                width: 200px;
                padding: 10px 15px;
                border-radius: 10px;
                border: 2px solid #e2e8f0;
                font-size: 1em;
                transition: all 0.3s ease;
            }
            
            .ekle-form input[type="text"]:focus {
                outline: none;
                border-color: #667eea;
                box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
            }
            
            .mesaj { 
                text-align: center; 
                color: #667eea; 
                margin-bottom: 15px;
                padding: 10px;
                background: rgba(102, 126, 234, 0.1);
                border-radius: 10px;
                font-weight: 600;
            }
            
            .back-link {
                text-align: center;
                margin-top: 25px;
            }
            
            .back-link a {
                color: #667eea;
                text-decoration: none;
                font-weight: 600;
                padding: 10px 20px;
                border-radius: 10px;
                background: rgba(102, 126, 234, 0.1);
                transition: all 0.3s ease;
            }
            
            .back-link a:hover {
                background: rgba(102, 126, 234, 0.2);
                transform: translateY(-2px);
            }
            
            @media (max-width: 768px) {
                .container { margin: 10px; padding: 20px; }
                .ders-sec { flex-direction: column; }
                .ekle-form { display: block; margin-bottom: 20px; }
                .ekle-form input[type="text"] { width: 100%; margin-bottom: 10px; }
                table { font-size: 0.8em; }
                th, td { padding: 8px 4px; }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h2>📚 Konu Takibi</h2>
            {{ menu_html | safe }}
            {% if mesaj %}<div class="mesaj">✅ {{mesaj}}</div>{% endif %}
            <form class="ekle-form" method="post" action="/konu-takip?ders={{secili_ders}}">
                <input type="text" name="yeni_ders" placeholder="Yeni Ders Adı" required>
                <button class="ekle-btn" type="submit">➕ Ders Ekle</button>
            </form>
            <form class="ders-sec" method="get" action="/konu-takip">
                <label for="ders">📖 Ders Seç:</label>
                <select name="ders" id="ders" onchange="this.form.submit()">
                    {% for d in dersler.keys() %}
                    <option value="{{d}}" {% if d==secili_ders %}selected{% endif %}>{{d}}</option>
                    {% endfor %}
                </select>
            </form>
            <form class="ekle-form" method="post" action="/konu-takip?ders={{secili_ders}}">
                <input type="hidden" name="ders_for_konu" value="{{secili_ders}}">
                <input type="text" name="yeni_konu" placeholder="Yeni Konu Adı" required>
                <button class="ekle-btn" type="submit">➕ Konu Ekle</button>
            </form>
            <form method="post" action="/konu-takip?ders={{secili_ders}}">
                <input type="hidden" name="ders" value="{{secili_ders}}">
                <table>
                    <tr>
                        <th>📝 Konu</th>
                        <th>📖 Yayın 1</th><th>✅ Bitirildi</th><th>🗑️ Sil</th>
                        <th>📖 Yayın 2</th><th>✅ Bitirildi</th><th>🗑️ Sil</th>
                        <th>📖 Yayın 3</th><th>✅ Bitirildi</th><th>🗑️ Sil</th>
                        <th>❌ Konuyu Sil</th>
                    </tr>
                    {% for konu in dersler[secili_ders] %}
                    {% set i = loop.index0 %}
                    <tr>
                        <td><strong>{{konu}}</strong></td>
                        {% for j in range(3) %}
                        <td><input type="text" name="ad_{{i}}_{{j}}" value="{{konu_takip[secili_ders][konu][j]['ad']}}" placeholder="Yayın adı"></td>
                        <td><input type="checkbox" name="tik_{{i}}_{{j}}" {% if konu_takip[secili_ders][konu][j]['tik'] %}checked{% endif %}></td>
                        <td>
                            {% if konu_takip[secili_ders][konu][j]['ad'] %}
                            <form method="post" action="/konu-takip?ders={{secili_ders}}" style="display:inline;">
                                <input type="hidden" name="sil_yayin" value="1">
                                <input type="hidden" name="sil_ders" value="{{secili_ders}}">
                                <input type="hidden" name="sil_konu" value="{{konu}}">
                                <input type="hidden" name="sil_index" value="{{j}}">
                                <button class="sil-btn" type="submit" onclick="return confirm('Bu yayını silmek istediğinizden emin misiniz?')">🗑️</button>
                            </form>
                            {% endif %}
                        </td>
                        {% endfor %}
                        <td>
                            <form method="post" action="/konu-takip?ders={{secili_ders}}" style="display:inline;">
                                <input type="hidden" name="sil_konu" value="1">
                                <input type="hidden" name="sil_ders" value="{{secili_ders}}">
                                <input type="hidden" name="sil_konu_adi" value="{{konu}}">
                                <button class="sil-btn" type="submit" onclick="return confirm('Bu konuyu ve tüm yayınlarını silmek istediğinizden emin misiniz?')" style="background: linear-gradient(135deg, #991b1b, #7f1d1d);">❌</button>
                            </form>
                        </td>
                    </tr>
                    {% endfor %}
                </table>
                <button class="save-btn" type="submit">💾 Kaydet</button>
            </form>
            <div class="back-link">
                <a href="/">← Ana Sayfa</a>
            </div>
        </div>
    </body>
    </html>
    ''', dersler=DERSLER, secili_ders=secili_ders, konu_takip=konu_takip, mesaj=mesaj, menu_html=menu_html('konu'))

@app.route('/deneme-takip', methods=['GET', 'POST'])
def deneme_takip_sayfa():
    global deneme_sinavlari
    mesaj = ""
    
    # Deneme sınavı silme
    if request.method == 'POST' and 'sil_sinav' in request.form:
        sil_index = int(request.form['sil_index'])
        if 0 <= sil_index < len(deneme_sinavlari):
            silinen_sinav = deneme_sinavlari.pop(sil_index)
            save_data()
            mesaj = f"'{silinen_sinav['ad']}' deneme sınavı silindi."
    
    # Deneme sınavı ekleme
    if request.method == 'POST' and 'tur' in request.form:
        tur = request.form['tur']
        ad = request.form['ad'].strip()
        tarih = request.form['tarih']
        net = request.form['net']
        puan = request.form['puan']
        if ad and tarih and net and puan:
            deneme_sinavlari.append({
                'tur': tur,
                'ad': ad,
                'tarih': tarih,
                'net': float(net),
                'puan': float(puan)
            })
            save_data()
            mesaj = f"'{ad}' deneme sınavı eklendi."
    
    # Grafik oluştur
    grafik_base64 = ""
    if deneme_sinavlari:
        puanlar = [d['puan'] for d in deneme_sinavlari]
        tarih_labels = [d['tarih'] for d in deneme_sinavlari]
        plt.figure(figsize=(8, 4))
        plt.plot(range(len(puanlar)), puanlar, marker='o', color='#2563eb', linewidth=2, markersize=6)
        plt.title('Deneme Sınavı Puanları', fontsize=14, fontweight='bold')
        plt.xlabel('Deneme Sırası', fontsize=12)
        plt.ylabel('Puan', fontsize=12)
        plt.grid(True, alpha=0.3)
        plt.xticks(range(len(tarih_labels)), [f"{d['tur']}\n{d['tarih']}" for d in deneme_sinavlari], rotation=45, ha='right')
        plt.tight_layout()
        
        # Grafiği base64'e çevir
        buf = BytesIO()
        plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
        buf.seek(0)
        grafik_base64 = base64.b64encode(buf.read()).decode('utf-8')
        plt.close()
    
    return render_template_string('''
    <html>
    <head>
        <title>Deneme Takibi - İsmet ÇÜÇEN Eğitim Danışmanlığı</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            
            body { 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                color: #333;
            }
            
            .container { 
                max-width: 1200px; 
                margin: 20px auto; 
                background: rgba(255, 255, 255, 0.95);
                backdrop-filter: blur(10px);
                border-radius: 20px; 
                box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
                padding: 30px;
                border: 1px solid rgba(255, 255, 255, 0.2);
            }
            
            h2 { 
                text-align: center; 
                color: #2d3748; 
                margin-bottom: 25px;
                font-size: 2em;
                font-weight: 700;
                background: linear-gradient(135deg, #667eea, #764ba2);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
            }
            
            .sinav-form { 
                background: rgba(255, 255, 255, 0.8);
                padding: 25px;
                border-radius: 15px;
                margin-bottom: 25px;
                box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
            }
            
            .form-row {
                display: flex;
                gap: 15px;
                margin-bottom: 15px;
                flex-wrap: wrap;
                align-items: center;
            }
            
            .form-group {
                flex: 1;
                min-width: 150px;
            }
            
            .form-group label {
                display: block;
                margin-bottom: 8px;
                font-weight: 600;
                color: #4a5568;
            }
            
            .form-group input, .form-group select {
                width: 100%;
                padding: 12px 15px;
                border-radius: 10px;
                border: 2px solid #e2e8f0;
                font-size: 1em;
                background: rgba(255, 255, 255, 0.9);
                transition: all 0.3s ease;
            }
            
            .form-group input:focus, .form-group select:focus {
                outline: none;
                border-color: #667eea;
                box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
                transform: translateY(-2px);
            }
            
            .ekle-btn { 
                background: linear-gradient(135deg, #48bb78, #38a169);
                color: #fff; 
                border: none; 
                border-radius: 12px; 
                padding: 12px 30px; 
                font-size: 1em; 
                cursor: pointer;
                font-weight: 600;
                transition: all 0.3s ease;
                box-shadow: 0 4px 15px rgba(72, 187, 120, 0.3);
                margin-top: 10px;
            }
            
            .ekle-btn:hover { 
                transform: translateY(-2px);
                box-shadow: 0 8px 25px rgba(72, 187, 120, 0.4);
            }
            
            table { 
                width: 100%; 
                border-collapse: separate;
                border-spacing: 0;
                font-size: 0.95em;
                border-radius: 15px;
                overflow: hidden;
                box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
                margin-bottom: 25px;
            }
            
            th, td { 
                border: none;
                padding: 12px 8px; 
                text-align: center;
                position: relative;
            }
            
            th { 
                background: linear-gradient(135deg, #667eea, #764ba2);
                color: white;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }
            
            td { 
                background: rgba(255, 255, 255, 0.9);
                border-bottom: 1px solid #f1f5f9;
            }
            
            tr:nth-child(even) td {
                background: rgba(248, 250, 252, 0.9);
            }
            
            .sil-btn { 
                background: linear-gradient(135deg, #f56565, #e53e3e);
                color: #fff; 
                border: none; 
                border-radius: 8px; 
                padding: 8px 15px; 
                font-size: 0.9em; 
                cursor: pointer;
                font-weight: 600;
                transition: all 0.3s ease;
                box-shadow: 0 2px 10px rgba(245, 101, 101, 0.3);
            }
            
            .sil-btn:hover { 
                transform: translateY(-1px);
                box-shadow: 0 4px 15px rgba(245, 101, 101, 0.4);
            }
            
            .mesaj { 
                text-align: center; 
                color: #667eea; 
                margin-bottom: 20px;
                padding: 15px;
                background: rgba(102, 126, 234, 0.1);
                border-radius: 12px;
                font-weight: 600;
            }
            
            .grafik-container {
                background: rgba(255, 255, 255, 0.8);
                padding: 25px;
                border-radius: 15px;
                margin-top: 25px;
                box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
                text-align: center;
            }
            
            .grafik-container img {
                max-width: 100%;
                height: auto;
                border-radius: 10px;
                box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
            }
            
            .back-link {
                text-align: center;
                margin-top: 25px;
            }
            
            .back-link a {
                color: #667eea;
                text-decoration: none;
                font-weight: 600;
                padding: 12px 25px;
                border-radius: 12px;
                background: rgba(102, 126, 234, 0.1);
                transition: all 0.3s ease;
                display: inline-block;
            }
            
            .back-link a:hover {
                background: rgba(102, 126, 234, 0.2);
                transform: translateY(-2px);
            }
            
            .pdf-btn {
                background: linear-gradient(135deg, #667eea, #764ba2);
                color: #fff;
                border: none;
                border-radius: 12px;
                padding: 12px 25px;
                font-size: 1em;
                cursor: pointer;
                font-weight: 600;
                transition: all 0.3s ease;
                box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
                text-decoration: none;
                display: inline-block;
                margin-top: 15px;
            }
            
            .pdf-btn:hover {
                transform: translateY(-2px);
                box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
            }
            
            @media (max-width: 768px) {
                .container { margin: 10px; padding: 20px; }
                .form-row { flex-direction: column; }
                .form-group { min-width: auto; }
                table { font-size: 0.8em; }
                th, td { padding: 8px 4px; }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h2>📊 Deneme Takibi</h2>
            {{ menu_html | safe }}
            {% if mesaj %}<div class="mesaj">✅ {{mesaj}}</div>{% endif %}
            
            <div class="sinav-form">
                <h3 style="margin-bottom: 20px; color: #2d3748; text-align: center;">➕ Yeni Deneme Sınavı Ekle</h3>
            <form method="post" action="/deneme-takip">
                <div class="form-row">
                        <div class="form-group">
                            <label for="tur">📋 Tür:</label>
                            <select name="tur" id="tur" required>
                            <option value="TYT">TYT</option>
                            <option value="AYT">AYT</option>
                        </select>
                </div>
                        <div class="form-group">
                            <label for="ad">📝 Ad:</label>
                            <input type="text" name="ad" id="ad" placeholder="Deneme sınavı adı" required>
                        </div>
                        <div class="form-group">
                            <label for="tarih">📅 Tarih:</label>
                            <input type="date" name="tarih" id="tarih" required>
                        </div>
                    </div>
                    <div class="form-row">
                        <div class="form-group">
                            <label for="net">🎯 Net:</label>
                            <input type="number" name="net" id="net" step="0.1" placeholder="0.0" required>
                        </div>
                        <div class="form-group">
                            <label for="puan">📈 Puan:</label>
                            <input type="number" name="puan" id="puan" step="0.1" placeholder="0.0" required>
                        </div>
                    </div>
                    <button class="ekle-btn" type="submit">➕ Deneme Sınavı Ekle</button>
            </form>
            </div>
            
            {% if deneme_sinavlari %}
            <table>
                <tr>
                    <th>📋 Tür</th>
                    <th>📝 Ad</th>
                    <th>📅 Tarih</th>
                    <th>🎯 Net</th>
                    <th>📈 Puan</th>
                    <th>🗑️ Sil</th>
                </tr>
                {% for sinav in deneme_sinavlari %}
                <tr>
                    <td><strong>{{sinav.tur}}</strong></td>
                    <td>{{sinav.ad}}</td>
                    <td>{{sinav.tarih}}</td>
                    <td>{{sinav.net}}</td>
                    <td>{{sinav.puan}}</td>
                    <td>
                        <form method="post" action="/deneme-takip" style="display:inline;">
                            <input type="hidden" name="sil_sinav" value="1">
                            <input type="hidden" name="sil_index" value="{{loop.index0}}">
                            <button class="sil-btn" type="submit" onclick="return confirm('Bu deneme sınavını silmek istediğinizden emin misiniz?')">🗑️</button>
                        </form>
                    </td>
                </tr>
                {% endfor %}
            </table>
            
            {% if grafik_base64 %}
            <div class="grafik-container">
                <h3 style="margin-bottom: 20px; color: #2d3748;">📈 Deneme Sınavı Grafiği</h3>
                <img src="data:image/png;base64,{{grafik_base64}}" alt="Deneme Sınavı Grafiği">
            </div>
            {% endif %}
            
            <div style="text-align: center; margin-top: 20px;">
                <a href="/deneme-pdf" class="pdf-btn">📄 PDF İndir</a>
            </div>
            {% else %}
            <div style="text-align: center; padding: 40px; color: #718096;">
                <h3>📊 Henüz deneme sınavı eklenmemiş</h3>
                <p>Yukarıdaki formu kullanarak ilk deneme sınavınızı ekleyin!</p>
            </div>
            {% endif %}
            
            <div class="back-link">
                <a href="/">← Ana Sayfa</a>
            </div>
        </div>
    </body>
    </html>
    ''', deneme_sinavlari=deneme_sinavlari, grafik_base64=grafik_base64, mesaj=mesaj, menu_html=menu_html('deneme'))

@app.route('/istatistikler')
def istatistikler_sayfa():
    # İstatistikleri hesapla
    stats = {}
    
    # Ders ve konu istatistikleri
    stats['toplam_ders'] = len(DERSLER)
    stats['toplam_konu'] = sum(len(konular) for konular in DERSLER.values())
    
    # Konu takibi istatistikleri
    tamamlanan_yayinlar = 0
    toplam_yayinlar = 0
    for ders in konu_takip:
        for konu in konu_takip[ders]:
            for yayin in konu_takip[ders][konu]:
                if yayin['ad']:  # Yayın adı varsa
                    toplam_yayinlar += 1
                    if yayin['tik']:  # Tamamlanmışsa
                        tamamlanan_yayinlar += 1
    
    stats['tamamlanan_yayinlar'] = tamamlanan_yayinlar
    stats['toplam_yayinlar'] = toplam_yayinlar
    stats['tamamlanma_orani'] = round((tamamlanan_yayinlar / toplam_yayinlar * 100) if toplam_yayinlar > 0 else 0, 1)
    
    # Deneme sınavı istatistikleri
    stats['toplam_deneme'] = len(deneme_sinavlari)
    if deneme_sinavlari:
        puanlar = [d['puan'] for d in deneme_sinavlari]
        stats['ortalama_puan'] = round(sum(puanlar) / len(puanlar), 1)
        stats['en_yuksek_puan'] = max(puanlar)
        stats['en_dusuk_puan'] = min(puanlar)
        
        # TYT/AYT dağılımı
        tyt_sayisi = len([d for d in deneme_sinavlari if d['tur'] == 'TYT'])
        ayt_sayisi = len([d for d in deneme_sinavlari if d['tur'] == 'AYT'])
        stats['tyt_sayisi'] = tyt_sayisi
        stats['ayt_sayisi'] = ayt_sayisi
    
    # Haftalık program istatistikleri
    dolu_hucreler = 0
    toplam_hucreler = len(SAATLER) * len(GUNLER)
    for saat in SAATLER:
        for gun in GUNLER:
            if weekly_plan_table[saat][gun].get('ders'):
                dolu_hucreler += 1
    
    stats['dolu_hucreler'] = dolu_hucreler
    stats['toplam_hucreler'] = toplam_hucreler
    stats['doluluk_orani'] = round((dolu_hucreler / toplam_hucreler * 100), 1)
    
    return render_template_string('''
    <html>
    <head>
        <title>İstatistikler - İsmet ÇÜÇEN Eğitim Danışmanlığı</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            
            body { 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                color: #333;
            }
            
            .container { 
                max-width: 1200px; 
                margin: 20px auto; 
                background: rgba(255, 255, 255, 0.95);
                backdrop-filter: blur(10px);
                border-radius: 20px; 
                box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
                padding: 30px;
                border: 1px solid rgba(255, 255, 255, 0.2);
            }
            
            h2 { 
                text-align: center; 
                color: #2d3748; 
                margin-bottom: 25px;
                font-size: 2em;
                font-weight: 700;
                background: linear-gradient(135deg, #667eea, #764ba2);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
            }
            
            .stats-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 25px;
                margin-bottom: 30px;
            }
            
            .stat-card {
                background: rgba(255, 255, 255, 0.8);
                padding: 25px;
                border-radius: 15px;
                box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
                text-align: center;
                transition: all 0.3s ease;
            }
            
            .stat-card:hover {
                transform: translateY(-5px);
                box-shadow: 0 15px 35px rgba(0, 0, 0, 0.15);
            }
            
            .stat-card h3 {
                color: #2d3748;
                margin-bottom: 15px;
                font-size: 1.3em;
                font-weight: 600;
            }
            
            .stat-value {
                font-size: 2.5em;
                font-weight: 700;
                margin-bottom: 10px;
                background: linear-gradient(135deg, #667eea, #764ba2);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
            }
            
            .stat-label {
                color: #718096;
                font-size: 1em;
                font-weight: 500;
            }
            
            .progress-container {
                background: rgba(255, 255, 255, 0.8);
                padding: 25px;
                border-radius: 15px;
                margin-bottom: 25px;
                box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
            }
            
            .progress-item {
                margin-bottom: 20px;
                padding: 15px;
                background: rgba(255, 255, 255, 0.9);
                border-radius: 10px;
                border-left: 4px solid #667eea;
            }
            
            .progress-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 10px;
            }
            
            .progress-title {
                font-weight: 600;
                color: #2d3748;
                font-size: 1.1em;
            }
            
            .progress-percentage {
                font-weight: 700;
                color: #667eea;
                font-size: 1.2em;
            }
            
            .progress-bar {
                width: 100%;
                height: 12px;
                background: #e2e8f0;
                border-radius: 6px;
                overflow: hidden;
            }
            
            .progress-fill {
                height: 100%;
                background: linear-gradient(135deg, #667eea, #764ba2);
                border-radius: 6px;
                transition: width 0.8s ease;
            }
            
            .pdf-btn {
                background: linear-gradient(135deg, #667eea, #764ba2);
                color: #fff;
                border: none;
                border-radius: 12px;
                padding: 15px 30px;
                font-size: 1.1em;
                cursor: pointer;
                font-weight: 600;
                transition: all 0.3s ease;
                box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
                text-decoration: none;
                display: inline-block;
                margin: 20px 0;
            }
            
            .pdf-btn:hover {
                transform: translateY(-2px);
                box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
            }
            
            .back-link {
                text-align: center;
                margin-top: 25px;
            }
            
            .back-link a {
                color: #667eea;
                text-decoration: none;
                font-weight: 600;
                padding: 12px 25px;
                border-radius: 12px;
                background: rgba(102, 126, 234, 0.1);
                transition: all 0.3s ease;
                display: inline-block;
            }
            
            .back-link a:hover {
                background: rgba(102, 126, 234, 0.2);
                transform: translateY(-2px);
            }
            
            .empty-state {
                text-align: center;
                padding: 60px 20px;
                color: #718096;
            }
            
            .empty-state h3 {
                margin-bottom: 15px;
                font-size: 1.5em;
                color: #4a5568;
            }
            
            @media (max-width: 768px) {
                .container { margin: 10px; padding: 20px; }
                .stats-grid { grid-template-columns: 1fr; }
                .stat-card { padding: 20px; }
                .progress-container { padding: 20px; }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h2>📈 İstatistikler</h2>
            {{ menu_html | safe }}
            
            {% if toplam_konu > 0 or toplam_deneme > 0 %}
            <div class="stats-grid">
                <div class="stat-card">
                    <h3>📚 Toplam Konu</h3>
                    <div class="stat-value">{{toplam_konu}}</div>
                    <div class="stat-label">Tüm derslerdeki konu sayısı</div>
            </div>
            
                <div class="stat-card">
                    <h3>✅ Tamamlanan Konu</h3>
                    <div class="stat-value">{{tamamlanan_konu}}</div>
                    <div class="stat-label">Bitirilen konu sayısı</div>
                </div>
                
                <div class="stat-card">
                    <h3>📊 Tamamlanma Oranı</h3>
                    <div class="stat-value">%{{tamamlanma_orani}}</div>
                    <div class="stat-label">Genel ilerleme durumu</div>
                </div>
                
                <div class="stat-card">
                    <h3>📝 Deneme Sınavı</h3>
                    <div class="stat-value">{{toplam_deneme}}</div>
                    <div class="stat-label">Toplam deneme sayısı</div>
                    </div>
                
                {% if ortalama_puan > 0 %}
                <div class="stat-card">
                    <h3>🎯 Ortalama Puan</h3>
                    <div class="stat-value">{{ortalama_puan}}</div>
                    <div class="stat-label">Deneme sınavı ortalaması</div>
                </div>
                {% endif %}
                
                {% if en_yuksek_puan > 0 %}
                <div class="stat-card">
                    <h3>🏆 En Yüksek Puan</h3>
                    <div class="stat-value">{{en_yuksek_puan}}</div>
                    <div class="stat-label">En iyi deneme sonucu</div>
                </div>
                {% endif %}
            </div>
            
            {% if ders_istatistikleri %}
            <div class="progress-container">
                <h3 style="margin-bottom: 20px; color: #2d3748; text-align: center;">📊 Ders Bazında İlerleme</h3>
                {% for ders, istatistik in ders_istatistikleri.items() %}
                <div class="progress-item">
                    <div class="progress-header">
                        <span class="progress-title">{{ders}}</span>
                        <span class="progress-percentage">%{{istatistik.yuzde}}</span>
                    </div>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: {{istatistik.yuzde}}%"></div>
                    </div>
                    <div style="margin-top: 8px; font-size: 0.9em; color: #718096;">
                        {{istatistik.tamamlanan}} / {{istatistik.toplam}} konu tamamlandı
                </div>
                </div>
                {% endfor %}
                </div>
                {% endif %}
            
            <div style="text-align: center;">
                <a href="/istatistikler-pdf" class="pdf-btn">📄 PDF İndir</a>
            </div>
            
            {% else %}
            <div class="empty-state">
                <h3>📊 Henüz veri bulunmuyor</h3>
                <p>Konu takibi ve deneme sınavları ekleyerek istatistiklerinizi görebilirsiniz.</p>
            </div>
            {% endif %}
            
            <div class="back-link">
                <a href="/">← Ana Sayfa</a>
            </div>
        </div>
    </body>
    </html>
    ''', toplam_konu=stats['toplam_konu'], tamamlanan_konu=stats['tamamlanan_yayinlar'], tamamlanma_orani=stats['tamamlanma_orani'], 
         toplam_deneme=stats['toplam_deneme'], ortalama_puan=stats['ortalama_puan'], en_yuksek_puan=stats['en_yuksek_puan'], 
         ders_istatistikleri=stats, menu_html=menu_html('istatistikler'))

@app.route('/istatistikler-pdf')
def istatistikler_pdf():
    # İstatistikleri hesapla
    stats = {}
    
    # Ders ve konu istatistikleri
    stats['toplam_ders'] = len(DERSLER)
    stats['toplam_konu'] = sum(len(konular) for konular in DERSLER.values())
    
    # Konu takibi istatistikleri
    tamamlanan_yayinlar = 0
    toplam_yayinlar = 0
    for ders in konu_takip:
        for konu in konu_takip[ders]:
            for yayin in konu_takip[ders][konu]:
                if yayin['ad']:  # Yayın adı varsa
                    toplam_yayinlar += 1
                    if yayin['tik']:  # Tamamlanmışsa
                        tamamlanan_yayinlar += 1
    
    stats['tamamlanan_yayinlar'] = tamamlanan_yayinlar
    stats['toplam_yayinlar'] = toplam_yayinlar
    stats['tamamlanma_orani'] = round((tamamlanan_yayinlar / toplam_yayinlar * 100) if toplam_yayinlar > 0 else 0, 1)
    
    # Deneme sınavı istatistikleri
    stats['toplam_deneme'] = len(deneme_sinavlari)
    if deneme_sinavlari:
        puanlar = [d['puan'] for d in deneme_sinavlari]
        stats['ortalama_puan'] = round(sum(puanlar) / len(puanlar), 1)
        stats['en_yuksek_puan'] = max(puanlar)
        stats['en_dusuk_puan'] = min(puanlar)
        
        # TYT/AYT dağılımı
        tyt_sayisi = len([d for d in deneme_sinavlari if d['tur'] == 'TYT'])
        ayt_sayisi = len([d for d in deneme_sinavlari if d['tur'] == 'AYT'])
        stats['tyt_sayisi'] = tyt_sayisi
        stats['ayt_sayisi'] = ayt_sayisi
    
    # Haftalık program istatistikleri
    dolu_hucreler = 0
    toplam_hucreler = len(SAATLER) * len(GUNLER)
    for saat in SAATLER:
        for gun in GUNLER:
            if weekly_plan_table[saat][gun].get('ders'):
                dolu_hucreler += 1
    
    stats['dolu_hucreler'] = dolu_hucreler
    stats['toplam_hucreler'] = toplam_hucreler
    stats['doluluk_orani'] = round((dolu_hucreler / toplam_hucreler * 100), 1)
    
    # PDF oluştur
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=30, rightMargin=30, topMargin=30, bottomMargin=30)
    elements = []
    
    # Logo ekle
    logo_path = os.path.join('static', 'logo.png')
    if os.path.exists(logo_path):
        logo = Image(logo_path)
        logo.drawHeight = 50
        logo.drawWidth = 100
        logo.hAlign = 'CENTER'
        elements.append(logo)
        elements.append(Spacer(1, 8))
    
    # Stil tanımları - Türkçe karakter desteği için
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=14,
        spaceAfter=15,
        alignment=1,  # Ortalı
        fontName=get_font_name()
    )
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=12,
        spaceAfter=10,
        spaceBefore=15,
        fontName=get_font_name()
    )
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontName=get_font_name(),
        fontSize=10
    )
    
    # Başlık
    elements.append(Paragraph("İsmet ÇÜÇEN Eğitim Danışmanlığı", title_style))
    elements.append(Paragraph("Öğrenci İstatistik Raporu", title_style))
    
    if program_info['adsoyad']:
        elements.append(Paragraph(f"Öğrenci: {program_info['adsoyad']}", normal_style))
    if program_info['tarih']:
        elements.append(Paragraph(f"Tarih: {program_info['tarih']}", normal_style))
    
    elements.append(Spacer(1, 15))
    
    # Genel İstatistikler
    elements.append(Paragraph("Genel İstatistikler", heading_style))
    
    genel_data = [
        ['Metrik', 'Değer'],
        ['Toplam Ders', str(stats['toplam_ders'])],
        ['Toplam Konu', str(stats['toplam_konu'])],
        ['Toplam Yayın', str(stats['toplam_yayinlar'])],
        ['Tamamlanan Yayın', str(stats['tamamlanan_yayinlar'])],
        ['Yayın Tamamlanma Oranı', f"%{stats['tamamlanma_orani']}"],
        ['Toplam Deneme Sınavı', str(stats['toplam_deneme'])],
        ['Program Doluluk Oranı', f"%{stats['doluluk_orani']}"]
    ]
    
    genel_table = Table(genel_data, colWidths=[2.5*inch, 1.5*inch])
    genel_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), get_font_name(is_bold=True)),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
        ('FONTNAME', (0, 1), (-1, -1), get_font_name()),
    ]))
    elements.append(genel_table)
    
    # Deneme sınavları listesi (tek bölüm olarak)
    if deneme_sinavlari:
        elements.append(Spacer(1, 15))
        elements.append(Paragraph("Deneme Sınavları", heading_style))
        
        # Özet bilgiler
        if stats['toplam_deneme'] > 0:
            ozet_data = [
                ['TYT Deneme Sayısı', str(stats['tyt_sayisi'])],
                ['AYT Deneme Sayısı', str(stats['ayt_sayisi'])],
                ['Ortalama Puan', str(stats['ortalama_puan'])],
                ['En Yüksek Puan', str(stats['en_yuksek_puan'])],
                ['En Düşük Puan', str(stats['en_dusuk_puan'])]
            ]
            
            ozet_table = Table(ozet_data, colWidths=[2*inch, 1*inch])
            ozet_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), get_font_name(is_bold=True)),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 0.3, colors.grey),
                ('FONTNAME', (1, 0), (1, -1), get_font_name()),
            ]))
            elements.append(ozet_table)
            elements.append(Spacer(1, 10))
        
        # Detaylı liste
        sinav_data = [['Tür', 'Ad', 'Tarih', 'Net', 'Puan']]
        for sinav in deneme_sinavlari:
            sinav_data.append([
                sinav['tur'],
                sinav['ad'],
                sinav['tarih'],
                str(sinav['net']),
                str(sinav['puan'])
            ])
        
        # Tablo genişliklerini ayarla
        available_width = A4[0] - 60  # Sayfa genişliği - kenar boşlukları
        col_widths = [0.8*inch, 2.5*inch, 1*inch, 0.6*inch, 0.6*inch]
        
        sinav_table = Table(sinav_data, colWidths=col_widths)
        sinav_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), get_font_name(is_bold=True)),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 7),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 2),
            ('RIGHTPADDING', (0, 0), (-1, -1), 2),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 3),
            ('FONTNAME', (0, 1), (-1, -1), get_font_name()),
        ]))
        elements.append(sinav_table)
    
    # PDF'i oluştur
    doc.build(elements)
    buffer.seek(0)
    
    # Dosya adı - Türkçe karakterleri düzelt
    ogrenci_adi = program_info['adsoyad'] if program_info['adsoyad'] else 'Ogrenci'
    # Türkçe karakterleri değiştir
    ogrenci_adi = ogrenci_adi.replace('ç', 'c').replace('ğ', 'g').replace('ı', 'i').replace('ö', 'o').replace('ş', 's').replace('ü', 'u')
    ogrenci_adi = ogrenci_adi.replace('Ç', 'C').replace('Ğ', 'G').replace('İ', 'I').replace('Ö', 'O').replace('Ş', 'S').replace('Ü', 'U')
    filename = f"{ogrenci_adi}_Istatistik_Raporu.pdf"
    
    return send_file(
        buffer,
        as_attachment=True,
        download_name=filename,
        mimetype='application/pdf'
    )

@app.route('/deneme-pdf')
def deneme_pdf():
    # PDF oluştur
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=30, rightMargin=30, topMargin=30, bottomMargin=30)
    elements = []
    
    # Logo ekle
    logo_path = os.path.join('static', 'logo.png')
    if os.path.exists(logo_path):
        logo = Image(logo_path)
        logo.drawHeight = 50
        logo.drawWidth = 100
        logo.hAlign = 'CENTER'
        elements.append(logo)
        elements.append(Spacer(1, 8))
    
    # Stil tanımları
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=14,
        spaceAfter=15,
        alignment=1,  # Ortalı
        fontName=TURKISH_FONT
    )
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=12,
        spaceAfter=10,
        spaceBefore=15,
        fontName=TURKISH_FONT
    )
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontName=TURKISH_FONT,
        fontSize=10
    )
    
    # Başlık
    elements.append(Paragraph("İsmet ÇÜÇEN Eğitim Danışmanlığı", title_style))
    elements.append(Paragraph("Deneme Sınavları Raporu", title_style))
    
    if program_info['adsoyad']:
        elements.append(Paragraph(f"Öğrenci: {program_info['adsoyad']}", normal_style))
    if program_info['tarih']:
        elements.append(Paragraph(f"Tarih: {program_info['tarih']}", normal_style))
    
    elements.append(Spacer(1, 15))
    
    # İstatistikler
    if deneme_sinavlari:
        puanlar = [d['puan'] for d in deneme_sinavlari]
        tyt_sayisi = len([d for d in deneme_sinavlari if d['tur'] == 'TYT'])
        ayt_sayisi = len([d for d in deneme_sinavlari if d['tur'] == 'AYT'])
        
        elements.append(Paragraph("Deneme Sınavı İstatistikleri", heading_style))
        
        istatistik_data = [
            ['Toplam Deneme Sınavı', str(len(deneme_sinavlari))],
            ['TYT Deneme Sayısı', str(tyt_sayisi)],
            ['AYT Deneme Sayısı', str(ayt_sayisi)],
            ['Ortalama Puan', f"{round(sum(puanlar) / len(puanlar), 1)}"],
            ['En Yüksek Puan', str(max(puanlar))],
            ['En Düşük Puan', str(min(puanlar))]
        ]
        
        istatistik_table = Table(istatistik_data, colWidths=[2.5*inch, 1.5*inch])
        istatistik_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), get_font_name(is_bold=True)),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.3, colors.grey),
            ('FONTNAME', (1, 0), (1, -1), get_font_name()),
        ]))
        elements.append(istatistik_table)
        elements.append(Spacer(1, 15))
    
    # Deneme sınavları listesi
    if deneme_sinavlari:
        elements.append(Paragraph("Deneme Sınavları Listesi", heading_style))
        
        sinav_data = [['#', 'Tür', 'Ad', 'Tarih', 'Net', 'Puan']]
        for i, sinav in enumerate(deneme_sinavlari, 1):
            sinav_data.append([
                str(i),
                sinav['tur'],
                sinav['ad'],
                sinav['tarih'],
                str(sinav['net']),
                str(sinav['puan'])
            ])
        
        # Tablo genişliklerini ayarla
        col_widths = [0.4*inch, 0.6*inch, 2.5*inch, 1*inch, 0.6*inch, 0.6*inch]
        
        sinav_table = Table(sinav_data, colWidths=col_widths)
        sinav_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), get_font_name(is_bold=True)),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 7),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 2),
            ('RIGHTPADDING', (0, 0), (-1, -1), 2),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 3),
        ]))
        elements.append(sinav_table)
        
        # Grafik ekle
        elements.append(Spacer(1, 15))
        elements.append(Paragraph("Puan Grafiği", heading_style))
        
        # Grafik oluştur
        puanlar = [d['puan'] for d in deneme_sinavlari]
        plt.figure(figsize=(8, 4))
        plt.plot(range(len(puanlar)), puanlar, marker='o', color='#2563eb', linewidth=2, markersize=6)
        plt.title('Deneme Sınavı Puanları', fontsize=14, fontweight='bold')
        plt.xlabel('Deneme Sırası', fontsize=12)
        plt.ylabel('Puan', fontsize=12)
        plt.grid(True, alpha=0.3)
        plt.xticks(range(len(puanlar)), [f"{d['tur']}\n{d['tarih']}" for d in deneme_sinavlari], rotation=45, ha='right')
        plt.tight_layout()
        
        # Grafiği PDF'e ekle
        buf = BytesIO()
        plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
        buf.seek(0)
        
        # ReportLab ile grafik ekle
        img = Image(buf)
        img.drawHeight = 180
        img.drawWidth = 360
        elements.append(img)
        plt.close()
    
    # PDF'i oluştur
    doc.build(elements)
    buffer.seek(0)
    
    # Dosya adı
    ogrenci_adi = program_info['adsoyad'] if program_info['adsoyad'] else 'Ogrenci'
    # Türkçe karakterleri değiştir
    ogrenci_adi = ogrenci_adi.replace('ç', 'c').replace('ğ', 'g').replace('ı', 'i').replace('ö', 'o').replace('ş', 's').replace('ü', 'u')
    ogrenci_adi = ogrenci_adi.replace('Ç', 'C').replace('Ğ', 'G').replace('İ', 'I').replace('Ö', 'O').replace('Ş', 'S').replace('Ü', 'U')
    filename = f"{ogrenci_adi}_Deneme_Sinavlari.pdf"
    
    return send_file(
        buffer,
        as_attachment=True,
        download_name=filename,
        mimetype='application/pdf'
    )

@app.route('/kaynak-yonetimi', methods=['GET', 'POST'])
def kaynak_yonetimi_sayfa():
    global kaynaklar
    secili_ders = request.args.get('ders', list(DERSLER.keys())[0] if DERSLER else '')
    mesaj = ""
    
    # Yeni kaynak ekleme
    if request.method == 'POST' and 'kaynak_adi' in request.form:
        kaynak_adi = request.form['kaynak_adi'].strip()
        ders = request.form['ders']
        tur = request.form['tur']
        aciklama = request.form['aciklama'].strip()
        link = request.form['link'].strip()
        
        if kaynak_adi and ders:
            if ders not in kaynaklar:
                kaynaklar[ders] = {}
            kaynaklar[ders][kaynak_adi] = {
                'tur': tur,
                'aciklama': aciklama,
                'link': link
            }
            save_data()
            mesaj = f"'{kaynak_adi}' kaynağı eklendi."
    
    # Kaynak silme
    if request.method == 'POST' and 'sil_kaynak' in request.form:
        ders = request.form['sil_ders']
        kaynak_adi = request.form['sil_kaynak_adi']
        if ders in kaynaklar and kaynak_adi in kaynaklar[ders]:
            del kaynaklar[ders][kaynak_adi]
            save_data()
            mesaj = f"'{kaynak_adi}' kaynağı silindi."
    
    return render_template_string('''
    <html>
    <head>
        <title>Kaynak Yönetimi - İsmet ÇÜÇEN Eğitim Danışmanlığı</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            
            body { 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                color: #333;
            }
            
            .container { 
                max-width: 1200px; 
                margin: 20px auto; 
                background: rgba(255, 255, 255, 0.95);
                backdrop-filter: blur(10px);
                border-radius: 20px; 
                box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
                padding: 30px;
                border: 1px solid rgba(255, 255, 255, 0.2);
            }
            
            h2 { 
                text-align: center; 
                color: #2d3748; 
                margin-bottom: 25px;
                font-size: 2em;
                font-weight: 700;
                background: linear-gradient(135deg, #667eea, #764ba2);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
            }
            
            .kaynak-form { 
                background: rgba(255, 255, 255, 0.8);
                padding: 25px;
                border-radius: 15px;
                margin-bottom: 25px;
                box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
            }
            
            .form-row {
                display: flex;
                gap: 15px;
                margin-bottom: 15px;
                flex-wrap: wrap;
                align-items: center;
            }
            
            .form-group {
                flex: 1;
                min-width: 200px;
            }
            
            .form-group label {
                display: block;
                margin-bottom: 8px;
                font-weight: 600;
                color: #4a5568;
            }
            
            .form-group input, .form-group select, .form-group textarea {
                width: 100%;
                padding: 12px 15px;
                border-radius: 10px;
                border: 2px solid #e2e8f0;
                font-size: 1em;
                background: rgba(255, 255, 255, 0.9);
                transition: all 0.3s ease;
                font-family: inherit;
            }
            
            .form-group textarea {
                resize: vertical;
                min-height: 80px;
            }
            
            .form-group input:focus, .form-group select:focus, .form-group textarea:focus {
                outline: none;
                border-color: #667eea;
                box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
                transform: translateY(-2px);
            }
            
            .ekle-btn { 
                background: linear-gradient(135deg, #48bb78, #38a169);
                color: #fff; 
                border: none; 
                border-radius: 12px; 
                padding: 12px 30px; 
                font-size: 1em; 
                cursor: pointer;
                font-weight: 600;
                transition: all 0.3s ease;
                box-shadow: 0 4px 15px rgba(72, 187, 120, 0.3);
                margin-top: 10px;
            }
            
            .ekle-btn:hover { 
                transform: translateY(-2px);
                box-shadow: 0 8px 25px rgba(72, 187, 120, 0.4);
            }
            
            .ders-sec { 
                display: flex; 
                justify-content: center; 
                margin-bottom: 25px;
                align-items: center;
                gap: 15px;
            }
            
            .ders-sec select { 
                font-size: 1em; 
                padding: 12px 20px; 
                border-radius: 12px; 
                border: 2px solid #e2e8f0;
                background: rgba(255, 255, 255, 0.9);
                transition: all 0.3s ease;
                min-width: 200px;
            }
            
            .ders-sec select:focus {
                outline: none;
                border-color: #667eea;
                box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
            }
            
            .ders-sec label {
                font-weight: 600;
                color: #4a5568;
            }
            
            .kaynak-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
                gap: 20px;
                margin-bottom: 25px;
            }
            
            .kaynak-card {
                background: rgba(255, 255, 255, 0.8);
                padding: 20px;
                border-radius: 15px;
                box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
                transition: all 0.3s ease;
                border-left: 4px solid #667eea;
            }
            
            .kaynak-card:hover {
                transform: translateY(-5px);
                box-shadow: 0 15px 35px rgba(0, 0, 0, 0.15);
            }
            
            .kaynak-header {
                display: flex;
                justify-content: space-between;
                align-items: flex-start;
                margin-bottom: 15px;
            }
            
            .kaynak-title {
                font-size: 1.2em;
                font-weight: 700;
                color: #2d3748;
                margin-bottom: 5px;
            }
            
            .kaynak-tur {
                background: linear-gradient(135deg, #667eea, #764ba2);
                color: white;
                padding: 4px 12px;
                border-radius: 20px;
                font-size: 0.8em;
                font-weight: 600;
                text-transform: uppercase;
            }
            
            .kaynak-aciklama {
                color: #4a5568;
                margin-bottom: 15px;
                line-height: 1.5;
            }
            
            .kaynak-link {
                color: #667eea;
                text-decoration: none;
                font-weight: 600;
                display: inline-block;
                margin-bottom: 15px;
                transition: all 0.3s ease;
            }
            
            .kaynak-link:hover {
                color: #764ba2;
                transform: translateX(5px);
            }
            
            .sil-btn { 
                background: linear-gradient(135deg, #f56565, #e53e3e);
                color: #fff; 
                border: none; 
                border-radius: 8px; 
                padding: 8px 15px; 
                font-size: 0.9em; 
                cursor: pointer;
                font-weight: 600;
                transition: all 0.3s ease;
                box-shadow: 0 2px 10px rgba(245, 101, 101, 0.3);
            }
            
            .sil-btn:hover { 
                transform: translateY(-1px);
                box-shadow: 0 4px 15px rgba(245, 101, 101, 0.4);
            }
            
            .mesaj { 
                text-align: center; 
                color: #667eea; 
                margin-bottom: 20px;
                padding: 15px;
                background: rgba(102, 126, 234, 0.1);
                border-radius: 12px;
                font-weight: 600;
            }
            
            .back-link {
                text-align: center;
                margin-top: 25px;
            }
            
            .back-link a {
                color: #667eea;
                text-decoration: none;
                font-weight: 600;
                padding: 12px 25px;
                border-radius: 12px;
                background: rgba(102, 126, 234, 0.1);
                transition: all 0.3s ease;
                display: inline-block;
            }
            
            .back-link a:hover {
                background: rgba(102, 126, 234, 0.2);
                transform: translateY(-2px);
            }
            
            .empty-state {
                text-align: center;
                padding: 60px 20px;
                color: #718096;
            }
            
            .empty-state h3 {
                margin-bottom: 15px;
                font-size: 1.5em;
                color: #4a5568;
            }
            
            @media (max-width: 768px) {
                .container { margin: 10px; padding: 20px; }
                .form-row { flex-direction: column; }
                .form-group { min-width: auto; }
                .ders-sec { flex-direction: column; }
                .kaynak-grid { grid-template-columns: 1fr; }
                .kaynak-card { padding: 15px; }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h2>📖 Kaynak Yönetimi</h2>
            {{ menu_html | safe }}
            {% if mesaj %}<div class="mesaj">✅ {{mesaj}}</div>{% endif %}
            
            <div class="kaynak-form">
                <h3 style="margin-bottom: 20px; color: #2d3748; text-align: center;">➕ Yeni Kaynak Ekle</h3>
                <form method="post" action="/kaynak-yonetimi?ders={{secili_ders}}">
                <div class="form-row">
                        <div class="form-group">
                            <label for="kaynak_adi">📚 Kaynak Adı:</label>
                            <input type="text" name="kaynak_adi" id="kaynak_adi" placeholder="Kaynak adı" required>
                        </div>
                        <div class="form-group">
                            <label for="ders">📖 Ders:</label>
                            <select name="ders" id="ders" required>
                        {% for d in dersler.keys() %}
                        <option value="{{d}}" {% if d==secili_ders %}selected{% endif %}>{{d}}</option>
                        {% endfor %}
                    </select>
                </div>
                        <div class="form-group">
                            <label for="tur">📋 Tür:</label>
                            <select name="tur" id="tur" required>
                                <option value="Kitap">📚 Kitap</option>
                                <option value="Video">🎬 Video</option>
                                <option value="PDF">📄 PDF</option>
                                <option value="Web Sitesi">🌐 Web Sitesi</option>
                                <option value="Uygulama">📱 Uygulama</option>
                                <option value="Diğer">📌 Diğer</option>
                    </select>
                </div>
                </div>
                <div class="form-row">
                        <div class="form-group">
                            <label for="aciklama">📝 Açıklama:</label>
                            <textarea name="aciklama" id="aciklama" placeholder="Kaynak hakkında açıklama"></textarea>
                </div>
                        <div class="form-group">
                            <label for="link">🔗 Link (İsteğe bağlı):</label>
                            <input type="url" name="link" id="link" placeholder="https://...">
                        </div>
                    </div>
                    <button class="ekle-btn" type="submit">➕ Kaynak Ekle</button>
            </form>
            </div>
            
            <form class="ders-sec" method="get" action="/kaynak-yonetimi">
                <label for="ders_filter">📖 Ders Seç:</label>
                <select name="ders" id="ders_filter" onchange="this.form.submit()">
                    {% for d in dersler.keys() %}
                    <option value="{{d}}" {% if d==secili_ders %}selected{% endif %}>{{d}}</option>
                    {% endfor %}
                </select>
            </form>
            
            {% if secili_ders in kaynaklar and kaynaklar[secili_ders] %}
            <div class="kaynak-grid">
                {% for kaynak_adi, kaynak in kaynaklar[secili_ders].items() %}
                <div class="kaynak-card">
                    <div class="kaynak-header">
                        <div>
                            <div class="kaynak-title">{{kaynak_adi}}</div>
                        </div>
                        <span class="kaynak-tur">{{kaynak.tur}}</span>
                    </div>
                    {% if kaynak.aciklama %}
                    <div class="kaynak-aciklama">{{kaynak.aciklama}}</div>
                    {% endif %}
                    {% if kaynak.link %}
                    <a href="{{kaynak.link}}" target="_blank" class="kaynak-link">🔗 Linke Git</a>
                    {% endif %}
                        <form method="post" action="/kaynak-yonetimi?ders={{secili_ders}}" style="display:inline;">
                            <input type="hidden" name="sil_kaynak" value="1">
                            <input type="hidden" name="sil_ders" value="{{secili_ders}}">
                            <input type="hidden" name="sil_kaynak_adi" value="{{kaynak_adi}}">
                        <button class="sil-btn" type="submit" onclick="return confirm('Bu kaynağı silmek istediğinizden emin misiniz?')">🗑️ Sil</button>
                        </form>
                </div>
                {% endfor %}
            </div>
            {% else %}
            <div class="empty-state">
                <h3>📖 Henüz kaynak eklenmemiş</h3>
                <p>Yukarıdaki formu kullanarak ilk kaynağınızı ekleyin!</p>
            </div>
            {% endif %}
            
            <div class="back-link">
                <a href="/">← Ana Sayfa</a>
            </div>
        </div>
    </body>
    </html>
    ''', dersler=DERSLER, secili_ders=secili_ders, kaynaklar=kaynaklar, mesaj=mesaj, menu_html=menu_html('kaynak'))
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    app.run(host="0.0.0.0", port=port, debug=False)
