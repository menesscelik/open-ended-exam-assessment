import React, { useState } from 'react';
import { Upload, FileText, CheckCircle, AlertCircle, Loader2, ClipboardCheck, Award, BarChart3 } from 'lucide-react';

const API_URL = 'http://127.0.0.1:8000';

function App() {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [scoring, setScoring] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  // Editable OCR results
  const [editableResults, setEditableResults] = useState([]);
  const [showConfirm, setShowConfirm] = useState(false);

  // Scoring results
  const [scoringResults, setScoringResults] = useState([]);
  const [showResults, setShowResults] = useState(false);

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
      setScoringResults([]);
      setShowResults(false);
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      const selectedFile = e.target.files[0];
      setFile(selectedFile);
      setError(null);
      setResult(null);
      setEditableResults([]);
      setScoringResults([]);
      setShowResults(false);
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

      let editable = [];

      // Process each page
      if (data.pages && data.pages.length > 0) {
        for (const page of data.pages) {
          // Check if we have structured data (multiple questions detected)
          if (page.structured_data && Array.isArray(page.structured_data) && page.structured_data.length > 0) {
            // Add each detected question as a separate item
            for (const item of page.structured_data) {
              editable.push({
                page: page.page,
                soru_no: item.soru_no || editable.length + 1,
                soru_metni: item.soru_metni || '',
                ideal_cevap: '',
                ogrenci_cevabi: item.ogrenci_cevabi || ''
              });
            }
          } else {
            // Fallback: One big text block per page
            editable.push({
              page: page.page,
              soru_no: page.page, // Just use page number as question number
              soru_metni: '',
              ideal_cevap: '',
              ogrenci_cevabi: page.text || page.raw_text || ''
            });
          }
        }
      }

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

  const handleConfirmAndScore = async () => {
    setScoring(true);
    setError(null);
    const results = [];

    try {
      for (const item of editableResults) {
        if (!item.ogrenci_cevabi || !item.ideal_cevap) {
          results.push({
            soru_no: item.soru_no,
            error: 'İdeal cevap veya öğrenci cevabı boş.'
          });
          continue;
        }

        const params = new URLSearchParams({
          ideal_cevap: item.ideal_cevap,
          ogrenci_cevabi: item.ogrenci_cevabi,
          soru_metni: ''
        });

        const response = await fetch(`${API_URL}/api/puanla-direkt?${params}`, {
          method: 'POST'
        });

        if (response.ok) {
          const data = await response.json();
          results.push({
            soru_no: item.soru_no,
            ...data
          });
        } else {
          const errorData = await response.json();
          results.push({
            soru_no: item.soru_no,
            error: errorData.detail || 'Puanlama hatası'
          });
        }
      }

      setScoringResults(results);
      setShowResults(true);
      setShowConfirm(false);
    } catch (err) {
      setError(err.message || 'Puanlama sırasında hata oluştu.');
    } finally {
      setScoring(false);
    }
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

          {/* Scoring Results */}
          {showResults && scoringResults.length > 0 && (
            <div className="bg-white p-8 rounded-2xl shadow-xl border border-green-200">
              <h2 className="text-2xl font-bold text-slate-900 mb-6 flex items-center gap-2">
                <Award className="w-6 h-6 text-green-600" />
                Puanlama Sonuçları
              </h2>

              {scoringResults.map((res, index) => {
                const isLowScore = !res.error && res.final_puan < 40;
                return (
                  <div key={index} className={`mb-4 p-6 rounded-xl border ${res.error ? 'bg-red-50 border-red-200' : (isLowScore ? 'bg-red-50 border-red-200' : 'bg-green-50 border-green-200')}`}>
                    <div className="flex items-center justify-between mb-4">
                      <span className="text-lg font-semibold text-slate-800">Soru {res.soru_no}</span>
                      {!res.error && (
                        <span className={`text-3xl font-bold ${isLowScore ? 'text-red-600' : 'text-green-600'}`}>{res.final_puan}/100</span>
                      )}
                    </div>

                    {res.error ? (
                      <p className="text-red-600">{res.error}</p>
                    ) : (
                      <>
                        <div className="grid grid-cols-2 gap-4 mb-4">
                          <div className="bg-white p-3 rounded-lg">
                            <div className="text-sm text-slate-500">SBERT Cümlesel Benzerlik</div>
                            <div className="text-xl font-bold text-indigo-600">{(res.bert_skoru * 100).toFixed(1)}%</div>
                          </div>
                          <div className="bg-white p-3 rounded-lg">
                            <div className="text-sm text-slate-500">LLM Mantık Puanı</div>
                            <div className="text-xl font-bold text-purple-600">{res.llm_skoru}/100</div>
                          </div>
                        </div>
                        <div className="bg-white p-4 rounded-lg">
                          <div className="text-sm font-medium text-slate-500 mb-1">Değerlendirme</div>
                          <p className="text-slate-700">{res.yorum}</p>
                        </div>
                      </>
                    )}
                  </div>
                );
              })}
            </div>
          )}

          {/* Two Column OCR Results */}
          {showConfirm && editableResults.length > 0 && (
            <div className="bg-white p-8 rounded-2xl shadow-xl border border-slate-100">
              <h2 className="text-2xl font-bold text-slate-900 mb-6">
                OCR Sonuçları - Düzenle ve Puanla
              </h2>

              <p className="text-slate-600 mb-6 p-4 bg-amber-50 rounded-lg border border-amber-200">
                ⚠️ Her soru için <strong>İdeal Cevap</strong> alanına doğru cevabı yazın, ardından puanlayın.
              </p>

              {editableResults.map((item, index) => (
                <div key={index} className="mb-6 p-4 bg-slate-50 rounded-xl border border-slate-200">
                  <div className="flex items-center gap-2 mb-4">
                    <span className="bg-indigo-100 text-indigo-700 text-sm font-medium px-3 py-1 rounded-full">
                      Soru {item.soru_no}
                    </span>
                    {item.soru_metni && (
                      <span className="text-slate-600 text-sm italic border-l-2 border-indigo-200 pl-2">
                        "{item.soru_metni}"
                      </span>
                    )}
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {/* Left Column - Ideal Answer */}
                    <div>
                      <label className="block text-sm font-semibold text-green-700 mb-2">
                        ✅ İdeal Cevap (Doğru Cevap)
                      </label>
                      <textarea
                        value={item.ideal_cevap}
                        onChange={(e) => handleTextChange(index, 'ideal_cevap', e.target.value)}
                        placeholder="Bu sorunun doğru/beklenen cevabını yazın..."
                        rows={6}
                        className="w-full px-4 py-3 border border-green-300 rounded-lg focus:ring-2 focus:ring-green-500 font-mono text-sm bg-green-50"
                      />
                    </div>

                    {/* Right Column - Student Answer */}
                    <div>
                      <label className="block text-sm font-semibold text-slate-700 mb-2">
                        ✍️ Öğrenci Cevabı (OCR'dan)
                      </label>
                      <textarea
                        value={item.ogrenci_cevabi}
                        onChange={(e) => handleTextChange(index, 'ogrenci_cevabi', e.target.value)}
                        placeholder="OCR ile okunan öğrenci cevabı..."
                        rows={6}
                        className="w-full px-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 font-mono text-sm"
                      />
                    </div>
                  </div>
                </div>
              ))}

              <div className="flex justify-end mt-6">
                <button
                  onClick={handleConfirmAndScore}
                  disabled={scoring}
                  className={`flex items-center gap-2 px-8 py-3 font-semibold rounded-lg shadow-lg transition-colors ${scoring
                    ? 'bg-slate-400 cursor-not-allowed text-white'
                    : 'bg-green-600 text-white hover:bg-green-700'
                    }`}
                >
                  {scoring ? (
                    <>
                      <Loader2 className="w-5 h-5 animate-spin" />
                      Puanlanıyor...
                    </>
                  ) : (
                    <>
                      <BarChart3 className="w-5 h-5" />
                      Puanla
                    </>
                  )}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;
