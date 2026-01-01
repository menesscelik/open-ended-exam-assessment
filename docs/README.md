# Exam Grading System - Windows Installation Guide

Bu rehber, projenin backend bağımlılıkları olan **Poppler** ve **Tesseract-OCR** araçlarının Windows üzerine kurulumunu ve PATH ayarlarını adım adım anlatır.

## 1. Poppler Kurulumu (pdf2image için)

`pdf2image` kütüphanesi, PDF sayfalarını resme dönüştürmek için Poppler aracına ihtiyaç duyar.

1. **İndirme**:
   
   * [Poppler for Windows Releases](https://github.com/oschwartz10612/poppler-windows/releases/) adresine gidin.
   * En son sürüm olan ZIP dosyasını indirin (örneğin: `Release-24.02.0-0.zip`).

2. **Kurulum**:
   
   * İndirdiğiniz ZIP dosyasını açın.
   * İçindeki klasörü (genellikle `poppler-xx.xx.xx`) güvenli bir yere taşıyın.
   * Öneri: `C:\Program Files\poppler` olarak kaydedin.

3. **PATH Ayarı**:
   
   * Windows Arama çubuğuna "Sistem ortam değişkenlerini düzenleyin" yazın ve açın.
   * Açılan pencerede **"Ortam Değişkenleri..."** butonuna tıklayın.
   * "Sistem değişkenleri" (alttaki kutu) bölümünde **"Path"** değişkenini bulun ve seçip **"Düzenle"** deyin.
   * **"Yeni"** butonuna tıklayın ve Poppler'ın `bin` klasörünün tam yolunu yapıştırın.
   * Örnek yol: `C:\Program Files\poppler\Library\bin` veya `C:\Program Files\poppler\bin` (içinde `pdfinfo.exe`, `pdftoppm.exe` gibi dosyaların olduğu klasör).
   * Hepsine "Tamam" diyerek pencereleri kapatın.

## 2. Tesseract-OCR Kurulumu (pytesseract için)

`pytesseract`, resimlerden metin okumak için Tesseract motoruna ihtiyaç duyar.

1. **İndirme**:
   
   * [UB-Mannheim/tesseract](https://github.com/UB-Mannheim/tesseract/wiki) adresine gidin.
   * `tesseract-ocr-w64-setup-v5.x.x.xxxx.exe` (64-bit) dosyasını indirin.

2. **Kurulum**:
   
   * İndirdiğiniz `.exe` dosyasını çalıştırın.
   * Kurulum sırasında "Additional script data" (dil paketleri) seçeneğini görebilirsiniz. Türkçe karakterleri daha iyi okuması için "Turkish" dil paketini seçmeniz önerilir.
   * Kurulum yerini not edin (Varsayılan: `C:\Program Files\Tesseract-OCR`).

3. **PATH Ayarı**:
   
   * Yine "Sistem ortam değişkenlerini düzenleyin" -> **"Ortam Değişkenleri..."** yolunu izleyin.
   * "Sistem değişkenleri" altındaki **"Path"** değişkenini seçip **"Düzenle"** deyin.
   * **"Yeni"** butonuna basın ve Tesseract'ın kurulu olduğu klasörün yolunu ekleyin.
   * Örnek yol: `C:\Program Files\Tesseract-OCR`.
   * Pencereleri "Tamam" diyerek kapatın.

## 3. Doğrulama

Kurulumların başarılı olup olmadığını test etmek için yeni bir terminal (komut satırı) açın:

* **Poppler testi**:
  
  ```bash
  pdfinfo -v
  ```
  
  (Sürüm bilgisi dönmeli, hata vermemeli)

* **Tesseract testi**:
  
  ```bash
  tesseract --version
  ```
  
  (Sürüm bilgisi dönmeli)

## 4. Projeyi Çalıştırma

Artık backend ve frontend sunucularını başlatabilirsiniz.

* **Backend**: ` .\.venv\Scripts\activate; uvicorn main:app --reload`
* **Frontend**: `npm run dev` in `frontend` directory.
