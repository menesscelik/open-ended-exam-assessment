import React, { useState } from 'react';
import { Upload, FileText, CheckCircle, AlertCircle, Loader2, BookOpen, ClipboardCheck, ArrowRight } from 'lucide-react';
import TeacherPanel from './components/TeacherPanel';

const API_URL = 'http://127.0.0.1:8000';

function App() {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('ocr'); // 'ocr' | 'teacher'

  // Editable OCR results
  const [editableResults, setEditableResults] = useState([]);
  const [showConfirm, setShowConfirm] = useState(false);

  const handleDragOver = (e) => {
    e.preventDefault();
  };

  const handleDrop = (e) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const selectedFile = e.dataTransfer.files[0];
      setFile(selectedFile);
      setError(null);
      setResult(null);
      setEditableResults([]);
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      const selectedFile = e.target.files[0];
      setFile(selectedFile);
      setError(null);
      setResult(null);
      setEditableResults([]);
    }
  };

  const handleUpload = async () => {
    if (!file) return;

    setLoading(true);
    setError(null);
    setResult(null);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await fetch(`${API_URL}/upload`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Dosya işlenemedi.");
      }

      const data = await response.json();
      setResult(data);

      // Initialize editable results with parsed question/answer structure
      const editable = data.pages.map((page) => ({
        page: page.page,
        soru_metni: '',
        ogrenci_cevabi: page.text || page.raw_text || ''
      }));
      setEditableResults(editable);
      setShowConfirm(true);
    } catch (err) {
      setError(err.message || "Bir hata oluştu.");
    } finally {
      setLoading(false);
    }
  };

  const handleTextChange = (index, field, value) => {
    const updated = [...editableResults];
    updated[index][field] = value;
    setEditableResults(updated);
  };

  const handleConfirmAndScore = () => {
    // TODO: Send to scoring API
    alert('Puanlama işlemi için Adım 3 ve 4 gerekli. Yakında aktif olacak!');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-indigo-50 py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-6xl mx-auto">

        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-extrabold text-slate-900 tracking-tight sm:text-5xl">
            📝 Otomatik Sınav Değerlendirme
          </h1>
          <p className="mt-3 text-lg text-slate-600">
            El yazısı cevap kağıtlarını yapay zeka ile değerlendirin
          </p>
        </div>

        {/* Tab Navigation */}
        <div className="flex justify-center gap-4 mb-8">
          <button
            onClick={() => setActiveTab('ocr')}
            className={`flex items-center gap-2 px-6 py-3 rounded-lg font-semibold transition-all ${activeTab === 'ocr'
                ? 'bg-indigo-600 text-white shadow-lg'
                : 'bg-white text-slate-600 hover:bg-slate-100 border border-slate-200'
              }`}
          >
            <ClipboardCheck className="w-5 h-5" />
            Kağıt Değerlendirme
          </button>
          <button
            onClick={() => setActiveTab('teacher')}
            className={`flex items-center gap-2 px-6 py-3 rounded-lg font-semibold transition-all ${activeTab === 'teacher'
                ? 'bg-indigo-600 text-white shadow-lg'
                : 'bg-white text-slate-600 hover:bg-slate-100 border border-slate-200'
              }`}
          >
            <BookOpen className="w-5 h-5" />
            Hoca Paneli
          </button>
        </div>

        {/* Content */}
        {activeTab === 'teacher' ? (
          <TeacherPanel />
        ) : (
          <div className="space-y-6">

            {/* Upload Section */}
            <div className="bg-white p-8 rounded-2xl shadow-xl border border-slate-100">
              <div
                onDragOver={handleDragOver}
                onDrop={handleDrop}
                className={`flex flex-col items-center justify-center w-full h-48 border-2 border-dashed rounded-xl cursor-pointer transition-colors duration-200 ${file ? 'border-indigo-500 bg-indigo-50' : 'border-slate-300 hover:border-indigo-400 hover:bg-slate-50'
                  }`}
              >
                <label htmlFor="file-upload" className="flex flex-col items-center justify-center w-full h-full cursor-pointer">
                  {file ? (
                    <>
                      <FileText className="w-12 h-12 text-indigo-600 mb-3" />
                      <p className="text-lg font-medium text-slate-700">{file.name}</p>
                      <p className="text-sm text-slate-500">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
                    </>
                  ) : (
                    <>
                      <Upload className="w-10 h-10 text-slate-400 mb-3" />
                      <p className="text-lg font-medium text-slate-600">PDF veya Görsel Yükleyin</p>
                      <p className="text-sm text-slate-400 mt-1">Sürükle bırak veya tıklayın</p>
                    </>
                  )}
                  <input
                    id="file-upload"
                    type="file"
                    className="hidden"
                    accept=".pdf,.png,.jpg,.jpeg"
                    onChange={handleFileChange}
                  />
                </label>
              </div>

              {error && (
                <div className="mt-4 p-4 bg-red-50 rounded-lg flex items-center gap-3 text-red-700">
                  <AlertCircle className="w-5 h-5" />
                  {error}
                </div>
              )}

              <div className="mt-6 flex justify-center">
                <button
                  onClick={handleUpload}
                  disabled={!file || loading}
                  className={`flex items-center gap-2 px-8 py-3 rounded-lg text-white font-semibold shadow-lg transition-all ${!file || loading
                      ? 'bg-slate-400 cursor-not-allowed'
                      : 'bg-indigo-600 hover:bg-indigo-700 hover:scale-[1.02]'
                    }`}
                >
                  {loading ? (
                    <>
                      <Loader2 className="w-5 h-5 animate-spin" />
                      OCR İşleniyor...
                    </>
                  ) : (
                    <>
                      <CheckCircle className="w-5 h-5" />
                      Yükle ve Analiz Et
                    </>
                  )}
                </button>
              </div>
            </div>

            {/* Two Column OCR Results */}
            {showConfirm && editableResults.length > 0 && (
              <div className="bg-white p-8 rounded-2xl shadow-xl border border-slate-100">
                <h2 className="text-2xl font-bold text-slate-900 mb-6">
                  OCR Sonuçları - Düzenle ve Onayla
                </h2>

                {editableResults.map((item, index) => (
                  <div key={index} className="mb-6 p-4 bg-slate-50 rounded-xl border border-slate-200">
                    <div className="flex items-center gap-2 mb-4">
                      <span className="bg-indigo-100 text-indigo-700 text-sm font-medium px-3 py-1 rounded-full">
                        Sayfa {item.page}
                      </span>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {/* Left Column - Question */}
                      <div>
                        <label className="block text-sm font-semibold text-slate-700 mb-2">
                          📋 Soru Metni
                        </label>
                        <textarea
                          value={item.soru_metni}
                          onChange={(e) => handleTextChange(index, 'soru_metni', e.target.value)}
                          placeholder="Soruyu buraya yazın veya OCR'dan düzenleyin..."
                          rows={6}
                          className="w-full px-4 py-3 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 font-mono text-sm"
                        />
                      </div>

                      {/* Right Column - Student Answer */}
                      <div>
                        <label className="block text-sm font-semibold text-slate-700 mb-2">
                          ✍️ Öğrenci Cevabı
                        </label>
                        <textarea
                          value={item.ogrenci_cevabi}
                          onChange={(e) => handleTextChange(index, 'ogrenci_cevabi', e.target.value)}
                          placeholder="OCR ile okunan öğrenci cevabı..."
                          rows={6}
                          className="w-full px-4 py-3 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 font-mono text-sm"
                        />
                      </div>
                    </div>
                  </div>
                ))}

                <div className="flex justify-end mt-6">
                  <button
                    onClick={handleConfirmAndScore}
                    className="flex items-center gap-2 px-8 py-3 bg-green-600 text-white font-semibold rounded-lg hover:bg-green-700 transition-colors shadow-lg"
                  >
                    <ArrowRight className="w-5 h-5" />
                    Onayla ve Puanla
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
