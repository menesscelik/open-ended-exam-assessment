# 📝 Açık Uçlu Sınav Değerlendirme Sistemi (Automated Handwriting Assessment)

Bu proje, el yazısı sınav kağıtlarını yapay zeka ile okuyan (OCR), verilen cevap anahtarı ve rubriğe göre analiz edip puanlayan ve detaylı PDF raporları üreten gelişmiş bir sistemdir.

---

## 🚀 Özellikler

- **Gelişmiş OCR (Google Gemini Vision):** El yazısı metinleri yüksek doğrulukla dijitalleştirir. Türkçe karakter desteği tamdır.
- **Akıllı Soru Ayrıştırma:** Sınav kağıdındaki soruları ve cevapları otomatik olarak birbirinden ayırır.
- **Yapay Zeka Destekli Puanlama (Google Gemini):** 
    - Cevapları sadece kelime bazlı değil, anlamsal olarak analiz eder.
    - **Dinamik Puanlama:** Rubrikte belirtilen puan ölçeğini (örn. 15 puan) otomatik algılar ve buna göre puanlar (Asla keyfi olarak 100 üzerinden değerlendirmez).
- **PDF Raporlama:** Her öğrenci için, soru bazlı detaylı analizlerin ve puanların yer aldığı profesyonel bir PDF karnesi oluşturur.
- **Hata Toleransı:** API kesintilerine (429 Kota Aşımı veya 500 Sunucu Hatası) karşı akıllı "yeniden deneme" (retry) mekanizması ile kesintisiz çalışır.

---

## 🔒 Öğrenci Gizliliği ve KVKK Uyumluluğu

Bu sistem **"Privacy by Design"** (Tasarımda Gizlilik) ilkesiyle geliştirilmiştir:

1.  **Yerel Anonimleştirme:** Öğrenci isimleri ve numaraları, sınav kağıdı buluta gönderilmeden **önce**, tamamen kendi bilgisayarınızda (Localhost) tespit edilir ve görüntü üzerinde siyah şeritle kapatılır (Redaction).
2.  **Veri Güvenliği:** Google Gemini API'sine gönderilen görüntülerde kişisel veriler (Ad, Soyad, Okul No) **bulunmaz**. Sadece anonimleştirilmiş sınav içeriği işlenir.
3.  **PDF Raporları:** Orijinal kimlik bilgileri sadece yerel bilgisayarınızda rapor oluşturulurken kullanılır ve PDF içine işlenir.

---

## 🛠️ Gereksinimler

Projenin çalışması için bilgisayarınızda şunlar kurulu olmalıdır:

1.  **Python** (3.10 veya üzeri)
2.  **Node.js** (Frontend arayüzü için)
3.  **Google Gemini API Anahtarı** (Ücretsiz temin edilebilir)

###   Backend Bağımlılıkları (`backend/requirements.txt`)
Aşağıdaki kütüphaneler kurulum sırasında otomatik yüklenir:
- `fastapi`, `uvicorn`: API Sunucusu
- `google-generativeai`: Gemini OCR ve Puanlama
- `reportlab`: PDF Rapor Üretimi
- `sentence-transformers`: Ek metin analizi (Opsiyonel)
- `opencv-python`: Görüntü işleme ve anonimleştirme
- `pdf2image`: PDF formatındaki sınavları işlemek için

---

## ⚙️ Kurulum Adımları (Sıfırdan)

Sistemi kurmak için aşağıdaki adımları sırasıyla uygulayın:

### 1. Kurulum Scriptini Çalıştırın
Proje klasöründeki **`0_setup_project.bat`** dosyasına çift tıklayın.

Bu script şunları otomatik yapar:
1.  Python sanal ortamı (`.venv`) oluşturur.
2.  Gerekli tüm Python kütüphanelerini yükler.
3.  React (Frontend) bağımlılıklarını yükler.

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

### 2. API Anahtarını Tanımlayın
Google AI Studio'dan alacağınız API anahtarını sisteme tanıtmanız gerekir.
`backend` klasörü içinde `.env` adında bir dosya oluşturun ve içine şunu yazın:

```
GOOGLE_API_KEY=AIzaSy... (Kendi anahtarınızı yapıştırın)
```

---

## ▶️ Başlatma

Sistemi kullanıma hazır hale getirmek için **`start_project.bat`** dosyasına çift tıklamanız yeterlidir.

Bu script:
1.  **Backend** sunucusunu açar: `http://127.0.0.1:8000`
2.  **Frontend** uygulamasını açar: `http://localhost:5173`

Tarayıcınız otomatik açılacaktır. PDF sınav kağıdı, Cevap Anahtarı ve Rubrik yükleyerek test etmeye başlayabilirsiniz.

---

## ⚠️ Sık Karşılaşılan Sorunlar ve Çözümleri

**"Resource Exhausted" (429) Hatası:**
- Google Gemini ücretsiz kotanızın dolduğunu gösterir (Dakikada ~15 istek).
- **Çözüm:** Sistem otomatik olarak bekleyip (5-10 sn) tekrar deneyecektir. Müdahale etmenize gerek yoktur.

**"Internal Server Error" (500) Hatası:**
- Google sunucularında geçici bir sorun olduğunu belirtir.
- **Çözüm:** Sistem bu hatayı algılar ve **20 saniye** bekleyip işlemi otomatik olarak tekrar eder.

**"Puanlama 100 üzerinden görünüyor" Sorunu:**
- Sistem artık rubrikte belirtilen puan neyse (örneğin 15 puan) onun üzerinden değerlendirme yapmaya zorlanmıştır. PDF raporunda "12 / 15" formatında göreceksiniz.
