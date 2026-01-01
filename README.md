# 📝 Açık Uçlu Sınav Değerlendirme Sistemi (Automated Handwriting Assessment)

Bu proje, el yazısı sınav kağıtlarını yapay zeka ile okuyan (OCR), anlamsal (SBERT) ve mantıksal (LLM-Ollama) olarak analiz edip puanlayan bir sistemdir.

---

## 🚀 Özellikler
- **Çoklu Soru Ayıklama:** Tek sayfada birden fazla soru varsa otomatik ayırır.
- **Hibrit Puanlama (Offline):** Anlamsal benzerlik (%40) + Mantıksal doğruluk (%60).
- **Akıllı Hata Yönetimi:** Yanlış cevapları tespit edip puanı düşürür.
- **Güvenli:** Puanlama işlemi tamamen bilgisayarınızda (Local) yapılır.

---

## 🛠️ Gereksinimler

Projenin çalışması için bilgisayarınızda şunlar kurulu olmalıdır:

1.  **Python** (3.10 veya üzeri)
2.  **Node.js** (Frontend için)
3.  **Ollama** (Lokal LLM için - [İndir](https://ollama.com))

### � Backend Bağımlılıkları (`backend/requirements.txt`)
Aşağıdaki kütüphaneler kurulum sırasında otomatik yüklenir:
- `fastapi`, `uvicorn`: API Sunucusu
- `sqlalchemy`: Veritabanı
- `sentence-transformers`, `torch`, `numpy`: SBERT Modeli
- `google-generativeai`: Gemini OCR
- `requests`: Ollama ile iletişim
- `pdf2image`, `pytesseract`, `pillow`: PDF ve resim işleme
- `python-multipart`, `python-dotenv`: Yardımcı araçlar

---

## ⚙️ Kurulum Adımları (Sıfırdan)

Sistemi kurmak için aşağıdaki adımları sırasıyla uygulayın:

### 1. Kurulum Scriptini Çalıştırın
Proje klasöründeki **`0_setup_project.bat`** dosyasına çift tıklayın.

Bu script şunları otomatik yapar:
1.  Python sanal ortamı (`.venv`) oluşturur.
2.  `backend/requirements.txt` içindeki tüm kütüphaneleri yükler.
3.  `frontend` klasörüne gidip `npm install` komutuyla React paketlerini yükler.

*(Alternatif Manuel Kurulum):*
```bash
# Backend
python -m venv .venv
.venv\Scripts\activate
pip install -r backend/requirements.txt

# Frontend
cd frontend
npm install
```

### 2. Ollama Modelini İndirin
Sistemin puanlama yapabilmesi için `deepseek-r1:8b` modeline ihtiyacı vardır. Terminalde (CMD) şu komutu çalıştırın:
```bash
ollama pull deepseek-r1:8b
```
*(Not: `start_project.bat` bunu otomatik yapmaya çalışır ancak ilk kurulumda manuel yapmanız önerilir, yaklaşık 4.7 GB veri iner.)*

### 3. API Anahtarını Kontrol Edin
Verdiğiniz Google Gemini API anahtarı `backend/ocr_utils.py` dosyasına gömülüdür. Değiştirmek isterseniz `backend/.env` dosyası oluşturup içine yazabilirsiniz:
```
GOOGLE_API_KEY=AIza..........
```

---

## ▶️ Başlatma

Sistemi kullanıma hazır hale getirmek için **`start_project.bat`** dosyasına çift tıklamanız yeterlidir.

Bu script:
1.  **Ollama** servisini kontrol eder, kapalıysa başlatır.
2.  **Backend** sunucusunu açar: `http://127.0.0.1:8000`
3.  **Frontend** uygulamasını açar: `http://localhost:5173`

Tarayıcınız otomatik açılacaktır. PDF veya resim yükleyerek test etmeye başlayabilirsiniz.

---

## ⚠️ Sık Karşılaşılan Sorunlar

**"Read timed out" Hatası:**
- Bilgisayarınız yavaşsa Ollama'nın cevap vermesi uzun sürebilir. Sistem **5 dakika** bekleyecek şekilde ayarlanmıştır. Sabırlı olun.

**"Tek soru çıktı" Hatası:**
- Kağıttaki yazı çok karışıksa veya sorular birbirine girmişse OCR tek blok olarak alabilir.

**"Quota exceeded" (429) Hatası:**
- Google Gemini ücretsiz kotası dolmuş olabilir. Sistem otomatik olarak 5-10 saniye bekleyip tekrar dener. Hatayı sık alırsanız API anahtarını değiştirin.
