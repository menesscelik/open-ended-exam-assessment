# 📝 Akademik Sınav Değerlendirme Sistemi (3 Aşamalı Akıllı Sistem)

Bu proje, açık uçlu sınav kağıtlarını akademik standartlarda değerlendiren yeni nesil bir yapay zeka sistemidir. Sistem, **Cevap Anahtarı** ve **Rubrik** belgelerini referans alarak öğrenci kağıtlarını okur (OCR) ve kriter bazlı puanlama yapar.

---

## 🚀 Yeni Özellikler (v2.0)

- **3 Aşamalı Akış:**
  1.  **Cevap Anahtarı Yükleme:** Sınavın doğru cevaplarını içeren PDF.
  2.  **Rubrik Yükleme:** Puanlama kriterlerini ve kurallarını içeren PDF.
  3.  **Öğrenci Kağıdı:** Sistemin değerlendireceği sınav kağıdı.
  
- **Rubrik Tabanlı Puanlama:**
  - Yapay zeka, öğrenci cevabını rubrikteki her kriter için (Kavramsal Doğruluk, Mantık, Terminoloji vb.) ayrı ayrı analiz eder.
  - SBERT (Semantik Benzerlik), karar verici değil **yardımcı sinyal** olarak kullanılır.
  - "Doğru ama eksik", "Kısmen doğru" gibi nüansları akademisyen hassasiyetiyle yakalar.

- **Detaylı Geri Bildirim:**
  - Puanın neden kırıldığına dair kriter bazlı açıklama.
  - "TAM", "KISMEN" veya "YOK" şeklinde kriter durumu.

---

## 🛠️ Gereksinimler

Projenin çalışması için bilgisayarınızda şunlar kurulu olmalıdır:

1.  **Python** (3.10 veya üzeri)
2.  **Node.js** (Frontend için)
3.  **Ollama** (Lokal LLM için - [İndir](https://ollama.com))

### 📦 Backend Bağımlılıkları (`backend/requirements.txt`)
- `fastapi`, `uvicorn`: API Sunucusu
- `sqlalchemy`: Veritabanı
- `sentence-transformers`: SBERT Modeli (Semantik Analiz)
- `google-genai`: Gemini 2.0 Vision OCR (Metin Okuma)
- `requests`: Ollama ile iletişim
- `pdf2image`, `pillow`: PDF işleme

---

## ⚙️ Kurulum ve Başlatma

### 1. Kurulum (İlk Sefer)
Proje klasöründeki **`0_setup_project.bat`** dosyasına çift tıklayın. Bu işlem Python ortamını kurar ve gerekli kütüphaneleri yükler.

### 2. Yapay Zeka Modelini İndirin
Terminalde (CMD) şu komutu çalıştırın (yaklaşık 9GB):
```bash
ollama pull deepseek-r1:14b
```

### 3. Sistemi Başlatın
**`start_project.bat`** dosyasına çift tıklayın. Sistem otomatik olarak:
- Backend Sunucusunu (http://127.0.0.1:8000)
- Frontend Arayüzünü (http://localhost:5173) başlatacaktır.

---

## 🖥️ Kullanım Rehberi

Sistem açıldığında sizi 3 adımlı bir süreç karşılayacaktır:

1.  **Adım 1: Cevap Anahtarı**
    - Sınavın doğru cevaplarını içeren PDF dosyasını yükleyin. Yapay zeka metni çıkaracaktır.
    
2.  **Adım 2: Rubrik (Değerlendirme Kriterleri)**
    - Hangi cevabın kaç puan olduğunu ve kriterleri (Örn: "İşlem basamağı 5 puan") içeren belgeyi yükleyin.
    
3.  **Adım 3: Öğrenci Kağıdı**
    - Puanlanacak öğrenci kağıdını yükleyin. Sistem OCR ile okuyacak, ardından **"Puanlamayı Başlat"** butonuna bastığınızda Adım 1 ve 2'deki verileri kullanarak detaylı bir rapor sunacaktır.

---

## ⚠️ Önemli Notlar

- **Google API Kotası:** Sistem OCR için Google Gemini kullanır. "429 Too Many Requests" hatası alırsanız 1-2 dakika bekleyin.
- **Ollama Performansı:** Puanlama işlemi bilgisayarınızın hızına bağlı olarak soru başına 10-30 saniye sürebilir.
- **Poppler:** PDF okuma aracı (Poppler) projenin içine gömülmüştür, ekstra kuruluma gerek yoktur.
