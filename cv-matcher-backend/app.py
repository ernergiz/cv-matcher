import hashlib
import os
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import PyPDF2
import re
import pdfplumber
from groq import Groq 

# 1. KURULUM VE YAPILANDIRMA
load_dotenv()
app = Flask(__name__)
CORS(app)

# 2. DEĞİŞİKLİK: Groq İstemcisini Başlat
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# 3. DEĞİŞİKLİK: Model ismini Groq modellerinden biriyle değiştir
# 'llama-3.3-70b-versatile' şu an en güçlü ve stabil olanlardan biri.
MODEL_NAME = "llama-3.3-70b-versatile"

# Global Hafıza (Cache)
cv_cache = {}

# [Yardımcı fonksiyonlar (get_file_hash ve extract_text_from_pdf) aynı kalıyor]
def get_file_hash(file_stream):
    sha256_hash = hashlib.sha256()
    file_stream.seek(0)
    for byte_block in iter(lambda: file_stream.read(4096), b""):
        sha256_hash.update(byte_block)
    file_stream.seek(0)
    return sha256_hash.hexdigest()

def clean_text(text):

    text = re.sub(r'\s+', ' ', text)

    text = text.encode('utf-8', 'ignore').decode('utf-8')

    text = re.sub(r'[\x00-\x1F\x7F-\x9F]', '', text)

    return text.strip()


def extract_text_from_pdf(pdf_file):

    text = ""

    try:

        with pdfplumber.open(pdf_file) as pdf:

            for page in pdf.pages:

                page_text = page.extract_text()

                if page_text:
                    text += page_text + "\n"

        return clean_text(text)

    except Exception as e:

        print("PDF okuma hatası:", e)

        return ""

# 3. ANA ANALİZ ROUTE'U
@app.route('/analyze-cv', methods=['POST'])
def analyze_cv():
    if 'cv' not in request.files:
        return jsonify({"error": "Lütfen bir CV yükleyin."}), 400
    
    cv_file = request.files['cv']
    
    file_hash = get_file_hash(cv_file)
    if file_hash in cv_cache:
        print(f"💡 [CACHE HIT] {cv_file.filename} hafızadan getirildi.")
        return jsonify(cv_cache[file_hash])
    
    print(f"🚀 [ANALİZ] {cv_file.filename} işleniyor (Groq API çağrısı)...")
    
    try:
        cv_text = extract_text_from_pdf(cv_file)
        if not cv_text:
            return jsonify({"error": "PDF içeriği okunamadı."}), 400

        prompt = f"""
Sen üst düzey bir İnsan Kaynakları Direktörü, işe alım uzmanı ve kariyer danışmanısın.

Görevin:
Aşağıdaki CV'yi profesyonel seviyede analiz etmek ve adayın profilini detaylı şekilde değerlendirmek.

Kurallar:
- Sadece geçerli JSON döndür.
- JSON dışında hiçbir açıklama yazma.
- Markdown kullanma.
- Tüm çıktı yalnızca Türkçe olmalı.
- Analizi tamamen CV içeriğine göre yap.
- CV'deki deneyimlere, becerilere, eğitimlere ve kariyer geçmişine göre profesyonel çıkarımlarda bulun.
- Varsayım yapma.
- Genel geçer cümleler kullanma.
- Kısa cevap verme.
- Maddeler detaylı ve açıklayıcı olsun.
- Gerçek bir İK uzmanı gibi değerlendirme yap.
- Güçlü yönleri profesyonel şekilde açıkla.
- Eksik yönleri dürüst ama yapıcı şekilde belirt.
- Kariyer gelişimi için gerçekçi öneriler sun.
- İş önerilerini CV ile gerçekten uyumlu seç.
- Değerlendirmeleri adayın deneyim seviyesine göre yap.
- Analizler doğal ve insan yazımı gibi görünsün.

Aşağıdaki kriterleri CV içeriğine göre değerlendir:
- Profesyonellik
- Deneyim seviyesi
- Yetkinlikler
- Kariyer potansiyeli
- İletişim ve ifade becerisi
- Sektörel uygunluk
- Rekabet seviyesi
- Güçlü yönler
- Eksik yönler
- Gelişim alanları
- CV düzeni ve profesyonel görünüm

JSON FORMATI TAM OLARAK ŞU ŞEKİLDE OLMALI:

{{
  "analysis": {{

    "Genel Değerlendirme": [
      "Adayın genel kariyer profili hakkında profesyonel yorum",
      "CV'nin genel kalitesi hakkında değerlendirme",
      "İşe alım açısından ilk izlenim analizi",
      "Deneyim ve yeterlilik özeti"
    ],

    "Güçlü Yönler": [
      "CV'de dikkat çeken güçlü özellik",
      "Kariyer açısından avantaj sağlayan yön",
      "İşe alım sürecinde öne çıkabilecek özellik",
      "Profesyonel yeterlilik avantajı",
      "Dikkat çeken beceri veya deneyim"
    ],

    "Eksik Beceriler": [
      "Eksik görülen yetkinlik",
      "Geliştirilmesi gereken alan",
      "Rekabet açısından eksik kalan nokta",
      "Deneyim açısından zayıf bölüm",
      "Profesyonel gelişim ihtiyacı"
    ],

    "Geliştirme Önerileri": [
      "CV güçlendirme önerisi",
      "Kariyer gelişim önerisi",
      "Profesyonel görünümü artıracak öneri",
      "İş bulma ihtimalini yükseltecek tavsiye",
      "Kendini geliştirmesi gereken alan",
      "Daha güçlü bir kariyer profili için öneri"
    ],

    "Kariyer Potansiyeli": [
      "Uzun vadeli kariyer potansiyeli yorumu",
      "Profesyonel gelişim ihtimali",
      "İleride yükselebileceği alanlar",
      "Kariyer büyüme değerlendirmesi"
    ]
  }},

  "jobs": [
    {{
      "position": "CV'ye uygun iş pozisyonu",
      "reason": "Bu pozisyona neden uygun olduğunun detaylı açıklaması",
      "match_level": "Yüksek / Orta / Geliştirilebilir",
      "career_path": "Bu pozisyonun gelecekte götürebileceği kariyer yolu"
    }},
    {{
      "position": "CV'ye uygun iş pozisyonu",
      "reason": "Detaylı açıklama",
      "match_level": "Yüksek",
      "career_path": "Kariyer yolu"
    }},
    {{
      "position": "CV'ye uygun iş pozisyonu",
      "reason": "Detaylı açıklama",
      "match_level": "Orta",
      "career_path": "Kariyer yolu"
    }}
  ],

  "score": 85
}}

PUANLAMA KRİTERLERİ:
- Deneyim seviyesi
- Profesyonellik
- Yetkinlikler
- CV kalitesi
- Kariyer potansiyeli
- Rekabet gücü
- Eğitim ve sertifikalar
- Başarılar ve deneyimler
- İfade ve sunum kalitesi

PUAN ARALIĞI:
90-100 = Çok güçlü profesyonel profil
75-89 = Güçlü potansiyel
60-74 = Geliştirilebilir ama umut verici
40-59 = Eksikleri fazla
0-39 = Zayıf profil

CV METNİ:
{cv_text}
"""

        # 4. DEĞİŞİKLİK: API Çağrısı Yapısı
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "Sen profesyonel bir İK uzmanısın ve sadece JSON formatında yanıt verirsin."},
                {"role": "user", "content": prompt}
            ],
            # JSON formatını garanti altına almak için
            response_format={"type": "json_object"},
            temperature=0.2
        )

        # 5. DEĞİŞİKLİK: Yanıtı alma şekli
        result_text = response.choices[0].message.content
        result_data = json.loads(result_text)
        result_data["status"] = "success"

        cv_cache[file_hash] = result_data
        
        return jsonify(result_data)

    except Exception as e:
        print(f"❌ API veya Sistem Hatası: {str(e)}")
        return jsonify({"error": f"Sistem hatası: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)