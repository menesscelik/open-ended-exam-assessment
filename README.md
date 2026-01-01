# 📝 Açık Uçlu Sınav Değerlendirme Sistemi (Automated Handwriting Assessment)

Bu proje, el yazısı ile yazılmış sınav kağıtlarını yapay zeka destekli olarak okuyan (OCR), analiz eden ve puanlayan tam kapsamlı bir değerlendirme sistemidir.

Proje, **Hibrit Puanlama Mimarisi** kullanarak öğrenci cevaplarını hem anlamsal (Semantic) hem de mantıksal (Logical) açıdan değerlendirir.

---

## 🚀 Öne Çıkan Özellikler

### 1. Akıllı OCR ve Soru Ayrıştırma (Google Gemini Vision)
- **El Yazısı Tanıma:** Google Gemini Vision API kullanılarak el yazısı metne dökülür.
- **Çoklu Soru Tespiti:** Tek bir sınav kağıdında birden fazla soru varsa (örn: Soru 1, Soru 2...), sistem bunları otomatik algılar ve ayrı kartlar halinde listeler.
- **Regex Ayrıştırma:** Gemini'nin çıktısı saf JSON olmasa bile, Python regex katmanı ile veriler güvenli bir şekilde ayrıştırılır.
- **Hata Yönetimi:** API kota aşımlarında (429 Error) otomatik bekleme ve tekrar deneme mekanizması vardır.

### 2. Hibrit Puanlama Sistemi (Offline & Secure)
Sistem iki farklı yapay zeka modelinin gücünü birleştirir:

*   **SBERT (Sentence-BERT):** `paraphrase-multilingual-MiniLM-L12-v2` modeli ile öğrenci cevabı ve ideal cevap arasındaki **anlamsal benzerliği** ölçer. Kelime avcılığı yapmaz, anlamı yakalar.
*   **Ollama (DeepSeek-R1:8b):** Yerel (Local) olarak çalışan büyük dil modeli, cevabın **mantıksal doğruluğunu** kontrol eder. "Eksik bilgi" ve "Yanlış bilgi" analizi yapar.

#### 🛡️ Puanlama Mantığı (Logic Gate)
Yanlış cevapların "benzer kelimeler" yüzünden yüksek puan almasını engellemek için özel bir algoritma kullanılır:
- Eğer Ollama, cevabın **YANLIŞ** (Puan < 40) olduğuna karar verirse, SBERT skoru **devre dışı bırakılır**.
- **Formül:** `Final = (SBERT * %40) + (Ollama * %60)` (Sadece cevap doğruysa geçerli).

### 3. Modern Kullanıcı Arayüzü (Frontend)
- **Teknolojiler:** React, Tailwind CSS, Lucide Icons.
- **Görsel Geri Bildirim:**
    - Puanı 40'ın altında olan cevaplar **Kırmızı Kart** ile uyarılır.
    - Başarılı cevaplar **Yeşil Kart** ile gösterilir.
- **Düzenlenebilir Yapı:** OCR hatası durumunda öğretmen, "Öğrenci Cevabı"nı manuel düzeltebilir.

---

## 🛠️ Teknoloji Yığını (Tech Stack)

| Bileşen | Teknoloji | Açıklama |
|---|---|---|
| **Backend** | FastApi (Python) | REST API, Asenkron mimari |
| **Veritabanı** | SQLite + SQLAlchemy | Soru ve sonuçların saklanması |
| **OCR** | Google Gemini Vision | Görüntü işleme ve metin çıkarma |
| **NLP (Lokal)** | SBERT (Sentence-Transformers) | Anlamsal benzerlik ölçümü |
| **LLM (Lokal)** | Ollama + DeepSeek-R1:8b | Mantıksal analiz ve geri bildirim |
| **Frontend** | React + Vite | Kullanıcı arayüzü |

---

## ⚙️ Kurulum ve Çalıştırma

### Gereksinimler
1.  **Python 3.10+**
2.  **Node.js & npm**
3.  **Ollama:** Bilgisayarınızda kurulu olmalı.
    - İndir: [ollama.com](https://ollama.com)
    - Model: `ollama pull deepseek-r1:8b` (Otomatik başlangıç scripti bunu kontrol eder).

### Adım 1: Kurulum
Projeyi klonlayın ve kök dizinde kalın.

### Adım 2: API Anahtarı
`backend/.env` dosyası veya `ocr_utils.py` içinde Google Gemini API anahtarının tanımlı olduğundan emin olun.

### Adım 3: Başlatma
Tek bir komutla tüm sistemi (Backend, Frontend ve Ollama) başlatabilirsiniz:

```bash
start_project.bat
```

Bu script:
1.  Gerekli Python kütüphanelerini yükler.
2.  Ollama servisinin çalışıp çalışmadığını kontrol eder, çalışmıyorsa başlatır.
3.  `deepseek-r1:8b` modelinin varlığını kontrol eder, yoksa indirir.
4.  Backend sunucusunu (Port 8000) başlatır.
5.  Frontend sunucusunu (Port 5173) başlatır.

---

## 📂 Proje Yapısı

```
open-ended-exam-assessment/
├── backend/
│   ├── main.py            # API Endpointleri
│   ├── ocr_utils.py       # Gemini OCR ve Regex işlemleri
│   ├── scoring.py         # Hibrit Puanlama (SBERT + Ollama)
│   ├── similarity.py      # SBERT Motoru
│   ├── database.py        # Veritabanı bağlantısı
│   └── models.py          # Veritabanı tabloları
├── frontend/
│   ├── src/
│   │   ├── App.jsx        # Ana Arayüz (Upload & Sonuçlar)
│   │   └── index.css      # Tailwind stilleri
│   └── package.json
├── start_project.bat      # Tek tıkla başlatma scripti
└── requirements.txt       # Python bağımlılıkları (FastAPI, torch, vb.)
```

## ⚠️ Notlar
- **Offline Çalışma:** Puanlama aşaması (SBERT ve Ollama) tamamen bilgisayarınızda (offline) çalışır. Verileriniz dışarı gitmez.
- **Sadece OCR Online:** Sadece kağıt okuma işlemi için Google sunucularına gidilir.

---
**Geliştirici:** Enes Çelik (Antigravity Agent desteğiyle)
