import React, { useState } from 'react';
import { Upload, FileText, CheckCircle, AlertCircle, Loader2, ClipboardCheck, Award, BarChart3, ChevronRight, BookOpen, GraduationCap } from 'lucide-react';

const API_URL = 'http://127.0.0.1:8000';

function App() {
  // Step State: 1=AnswerKey, 2=Rubric, 3=StudentExam
  const [step, setStep] = useState(1);

  // Global Context Data
  const [answerKeyFile, setAnswerKeyFile] = useState(null);
  const [answerKeyText, setAnswerKeyText] = useState("");

  const [rubricFile, setRubricFile] = useState(null);
  const [rubricText, setRubricText] = useState("");

  // Student Exam State
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [scoring, setScoring] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  // Editable OCR results (Student)
  const [editableResults, setEditableResults] = useState([]);
  const [showConfirm, setShowConfirm] = useState(false);

  // Scoring results
  const [scoringResults, setScoringResults] = useState([]);
  const [showResults, setShowResults] = useState(false);

  const handleDragOver = (e) => {
    e.preventDefault();
  };

  const handleDrop = (e, type) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const selectedFile = e.dataTransfer.files[0];
      handleFileSelection(selectedFile, type);
    }
  };

  const handleFileChange = (e, type) => {
    if (e.target.files && e.target.files[0]) {
      const selectedFile = e.target.files[0];
      handleFileSelection(selectedFile, type);
    }
  };

  const handleFileSelection = (selectedFile, type) => {
    setError(null);
    if (type === 'answerKey') {
      setAnswerKeyFile(selectedFile);
      setAnswerKeyText(""); // Reset text to force re-upload/OCR if file changes
    } else if (type === 'rubric') {
      setRubricFile(selectedFile);
      setRubricText("");
    } else if (type === 'student') {
      setFile(selectedFile);
      setResult(null);
      setEditableResults([]);
      setScoringResults([]);
      setShowResults(false);
      setShowConfirm(false);
    }
  };

  // Generic Upload for Answer Key and Rubric using /upload-generic
  const handleGenericUpload = async (fileObj, setTextCallback) => {
    if (!fileObj) return;

    setLoading(true);
    setError(null);

    const formData = new FormData();
    formData.append("file", fileObj);

    try {
      const response = await fetch(`${API_URL}/upload-generic`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Dosya işlenemedi.");
      }

      const data = await response.json();
      setTextCallback(data.text || "");
    } catch (err) {
      setError(err.message || "Bir hata oluştu.");
    } finally {
      setLoading(false);
    }
  };

  // Upload/Process for Student Exam (Step 3)
  const handleStudentUpload = async () => {
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
      console.log("OCR Response Data:", data);

      let editable = [];

      // Process each page
      if (data.pages && data.pages.length > 0) {
        for (const page of data.pages) {
          // Check if we have structured data (multiple questions detected)
          if (page.structured_data && Array.isArray(page.structured_data) && page.structured_data.length > 0) {
            for (const item of page.structured_data) {
              editable.push({
                page: page.page,
                soru_no: item.soru_no || editable.length + 1,
                soru_metni: item.soru_metni || '',
                ogrenci_cevabi: item.ogrenci_cevabi || ''
              });
            }
          } else {
            // Fallback: One big text block per page
            // Make sure we have some text content
            const textContent = page.text || page.raw_text || '';
            console.log(`Page ${page.page} text content length:`, textContent.length);

            editable.push({
              page: page.page,
              soru_no: page.page,
              soru_metni: '',
              ogrenci_cevabi: textContent
            });
          }
        }
      }

      console.log("Editable Results Count:", editable.length);

      if (editable.length === 0) {
        throw new Error("OCR işlemi sonucunda okunabilir metin bulunamadı. Lütfen dosyanın içeriğini kontrol edin veya tekrar deneyin.");
      }

      setEditableResults(editable);
      setShowConfirm(true);
    } catch (err) {
      console.error("Upload Error:", err);
      setError(err.message || "Bir hata oluştu.");
      setShowConfirm(false); // Ensure we don't switch view on error
    } finally {
      setLoading(false);
    }
  };

  const handleConfirmAndScore = async () => {
    setScoring(true);
    setError(null);
    const results = [];

    try {
      for (const item of editableResults) {
        if (!item.ogrenci_cevabi) {
          continue; // Skip empty answers
        }

        // Use JSON body for clearer data transfer and to support large texts
        const payload = {
          ideal_cevap: "", // Not used directly, we rely on answer_key_text
          ogrenci_cevabi: item.ogrenci_cevabi,
          soru_metni: item.soru_metni || "",
          answer_key_text: answerKeyText, // Global context
          rubric_text: rubricText         // Global context
        };

        const response = await fetch(`${API_URL}/api/puanla-direkt`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(payload)
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

  // Helper to render file upload UI
  const renderUploadBox = (fileState, type, label) => (
    <div
      onDragOver={handleDragOver}
      onDrop={(e) => handleDrop(e, type)}
      className={`flex flex-col items-center justify-center w-full h-48 border-2 border-dashed rounded-xl cursor-pointer transition-colors duration-200 ${fileState ? 'border-indigo-500 bg-indigo-50' : 'border-slate-300 hover:border-indigo-400 hover:bg-slate-50'}`}
    >
      <label htmlFor={`file-upload-${type}`} className="flex flex-col items-center justify-center w-full h-full cursor-pointer">
        {fileState ? (
          <>
            <FileText className="w-12 h-12 text-indigo-600 mb-3" />
            <p className="text-lg font-medium text-slate-700">{fileState.name}</p>
            <p className="text-sm text-slate-500">{(fileState.size / 1024 / 1024).toFixed(2)} MB</p>
          </>
        ) : (
          <>
            <Upload className="w-10 h-10 text-slate-400 mb-3" />
            <p className="text-lg font-medium text-slate-600">{label} Yükle (PDF)</p>
            <p className="text-sm text-slate-400 mt-1">Sürükle bırak veya tıklayın</p>
          </>
        )}
        <input
          id={`file-upload-${type}`}
          type="file"
          className="hidden"
          accept=".pdf,.png,.jpg,.jpeg"
          onChange={(e) => handleFileChange(e, type)}
        />
      </label>
    </div>
  );

  return (
    <div className="min-h-screen bg-slate-50 py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-6xl mx-auto">

        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-extrabold text-slate-900 tracking-tight sm:text-5xl flex items-center justify-center gap-3">
            <GraduationCap className="w-12 h-12 text-indigo-600" />
            Akademik Sınav Değerlendirme
          </h1>
          <p className="mt-3 text-lg text-slate-600">
            3 Aşamalı Akıllı Değerlendirme Sistemi
          </p>
        </div>

        {/* Stepper */}
        <div className="flex justify-center mb-10">
          <div className="flex items-center space-x-4">
            <div className={`flex items-center ${step >= 1 ? 'text-indigo-600 font-bold' : 'text-slate-400'}`}>
              <div className={`w-8 h-8 rounded-full flex items-center justify-center mr-2 border-2 ${step >= 1 ? 'border-indigo-600 bg-indigo-100' : 'border-slate-300'}`}>1</div>
              Cevap Anahtarı
            </div>
            <div className="w-12 h-1 bg-slate-300"></div>
            <div className={`flex items-center ${step >= 2 ? 'text-indigo-600 font-bold' : 'text-slate-400'}`}>
              <div className={`w-8 h-8 rounded-full flex items-center justify-center mr-2 border-2 ${step >= 2 ? 'border-indigo-600 bg-indigo-100' : 'border-slate-300'}`}>2</div>
              Rubrik
            </div>
            <div className="w-12 h-1 bg-slate-300"></div>
            <div className={`flex items-center ${step >= 3 ? 'text-indigo-600 font-bold' : 'text-slate-400'}`}>
              <div className={`w-8 h-8 rounded-full flex items-center justify-center mr-2 border-2 ${step >= 3 ? 'border-indigo-600 bg-indigo-100' : 'border-slate-300'}`}>3</div>
              Öğrenci Kağıdı & Puanlama
            </div>
          </div>
        </div>

        {/* Main Content Area */}
        <div className="bg-white p-8 rounded-2xl shadow-xl border border-slate-100">

          {/* Step 1: Answer Key */}
          {step === 1 && (
            <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
              <h2 className="text-2xl font-bold mb-4 text-slate-800 flex items-center gap-2">
                <BookOpen className="w-6 h-6 text-indigo-500" />
                Adım 1: Cevap Anahtarını Belirleyin
              </h2>
              <p className="text-slate-600 mb-6">Lütfen sınavın cevap anahtarını içeren PDF dosyasını yükleyin. Yapay zeka bu metni referans alacaktır.</p>

              {renderUploadBox(answerKeyFile, 'answerKey', 'Cevap Anahtarı')}

              <div className="mt-6">
                <label className="block text-sm font-medium text-slate-700 mb-2">Çıkarılan/Düzenlenen Metin:</label>
                <textarea
                  value={answerKeyText}
                  onChange={(e) => setAnswerKeyText(e.target.value)}
                  placeholder="Dosya yükleyin veya buraya metni yapıştırın..."
                  className="w-full h-64 p-4 border rounded-lg font-mono text-sm bg-slate-50 focus:ring-2 focus:ring-indigo-500 outline-none"
                />
              </div>

              <div className="mt-6 flex justify-between">
                <button
                  onClick={() => handleGenericUpload(answerKeyFile, setAnswerKeyText)}
                  disabled={!answerKeyFile || loading}
                  className="px-6 py-2 bg-slate-200 text-slate-700 rounded-lg hover:bg-slate-300 disabled:opacity-50 font-medium"
                >
                  {loading ? <Loader2 className="w-5 h-5 animate-spin mx-auto" /> : "Metni Çıkar (OCR)"}
                </button>

                <button
                  onClick={() => setStep(2)}
                  disabled={!answerKeyText.trim()}
                  className="flex items-center px-8 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:bg-slate-300 disabled:cursor-not-allowed font-semibold"
                >
                  Sonraki Adım <ChevronRight className="w-5 h-5 ml-1" />
                </button>
              </div>
            </div>
          )}

          {/* Step 2: Rubric */}
          {step === 2 && (
            <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
              <h2 className="text-2xl font-bold mb-4 text-slate-800 flex items-center gap-2">
                <ClipboardCheck className="w-6 h-6 text-purple-500" />
                Adım 2: Değerlendirme Kriterlerini (Rubrik) Belirleyin
              </h2>
              <p className="text-slate-600 mb-6">Puanlama kriterlerini içeren dosyayı yükleyin veya manuel olarak girin.</p>

              {renderUploadBox(rubricFile, 'rubric', 'Rubrik')}

              <div className="mt-6">
                <label className="block text-sm font-medium text-slate-700 mb-2">Rubrik Metni:</label>
                <textarea
                  value={rubricText}
                  onChange={(e) => setRubricText(e.target.value)}
                  placeholder="Rubrik metnini buraya girin..."
                  className="w-full h-64 p-4 border rounded-lg font-mono text-sm bg-slate-50 focus:ring-2 focus:ring-purple-500 outline-none"
                />
              </div>

              <div className="mt-6 flex justify-between">
                <button
                  onClick={() => handleGenericUpload(rubricFile, setRubricText)}
                  disabled={!rubricFile || loading}
                  className="px-6 py-2 bg-slate-200 text-slate-700 rounded-lg hover:bg-slate-300 disabled:opacity-50 font-medium"
                >
                  {loading ? <Loader2 className="w-5 h-5 animate-spin mx-auto" /> : "Metni Çıkar (OCR)"}
                </button>

                <div className="flex gap-4">
                  <button
                    onClick={() => setStep(1)}
                    className="px-6 py-3 border border-slate-300 text-slate-600 rounded-lg hover:bg-slate-50 font-medium"
                  >
                    Geri
                  </button>
                  <button
                    onClick={() => setStep(3)}
                    disabled={!rubricText.trim()}
                    className="flex items-center px-8 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:bg-slate-300 disabled:cursor-not-allowed font-semibold"
                  >
                    Sonraki Adım <ChevronRight className="w-5 h-5 ml-1" />
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Step 3: Student Exam */}
          {step === 3 && (
            <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
              <h2 className="text-2xl font-bold mb-4 text-slate-800 flex items-center gap-2">
                <FileText className="w-6 h-6 text-indigo-600" />
                Adım 3: Öğrenci Kağıdı & Puanlama
              </h2>

              {!showConfirm && !showResults && (
                <>
                  <p className="text-slate-600 mb-6">Son olarak, değerlendirilecek öğrenci kağıdını yükleyin.</p>
                  {renderUploadBox(file, 'student', 'Öğrenci Kağıdı')}

                  <div className="mt-6 flex justify-center gap-4">
                    <button
                      onClick={() => setStep(2)}
                      className="px-6 py-3 border border-slate-300 text-slate-600 rounded-lg hover:bg-slate-50 font-medium"
                    >
                      Geri
                    </button>
                    <button
                      onClick={handleStudentUpload}
                      disabled={!file || loading}
                      className={`flex items-center gap-2 px-8 py-3 rounded-lg text-white font-semibold shadow-lg transition-all ${!file || loading
                        ? 'bg-slate-400 cursor-not-allowed'
                        : 'bg-indigo-600 hover:bg-indigo-700 hover:scale-[1.02]'
                        }`}
                    >
                      {loading ? (
                        <>
                          <Loader2 className="w-5 h-5 animate-spin" />
                          İşleniyor...
                        </>
                      ) : (
                        <>
                          <CheckCircle className="w-5 h-5" />
                          Yükle ve Analiz Et
                        </>
                      )}
                    </button>
                  </div>
                </>
              )}

              {error && (
                <div className="mt-4 p-4 bg-red-50 rounded-lg flex items-center gap-3 text-red-700">
                  <AlertCircle className="w-5 h-5" />
                  {error}
                </div>
              )}
            </div>
          )}

          {/* Results View (Inside Step 3 Context) */}
          {step === 3 && showConfirm && editableResults.length > 0 && (
            <div className="mt-8 animate-in fade-in slide-in-from-bottom-8 duration-700">
              <h2 className="text-2xl font-bold text-slate-900 mb-6 border-b pb-2">
                OCR Kontrol & Puanlama
              </h2>
              <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg text-sm text-blue-800">
                <strong>Bilgi:</strong> Puanlama için Adım 1 ve Adım 2'de yüklediğiniz Cevap Anahtarı ve Rubrik kullanılacaktır. Aşağıda sadece öğrenci cevabının doğru okunup okunmadığını kontrol edin.
              </div>

              {editableResults.map((item, index) => (
                <div key={index} className="mb-6 p-6 bg-slate-50 rounded-xl border border-slate-200 shadow-sm">
                  <div className="flex items-center justify-between mb-4">
                    <span className="bg-indigo-100 text-indigo-700 font-bold px-3 py-1 rounded-lg">
                      Soru {item.soru_no}
                    </span>
                  </div>

                  <label className="block text-sm font-semibold text-slate-700 mb-2">
                    ✍️ Öğrenci Cevabı (OCR)
                  </label>
                  <textarea
                    value={item.ogrenci_cevabi}
                    onChange={(e) => {
                      const updated = [...editableResults];
                      updated[index].ogrenci_cevabi = e.target.value;
                      setEditableResults(updated);
                    }}
                    rows={4}
                    className="w-full px-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 font-mono text-sm"
                  />
                </div>
              ))}

              <div className="flex justify-end mt-6 gap-4">
                <button
                  onClick={() => { setShowConfirm(false); setResult(null); }}
                  className="px-6 py-3 border border-slate-300 text-slate-600 rounded-lg hover:bg-slate-50 font-medium"
                >
                  İptal / Yeni Yükleme
                </button>
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
                      Puanlamayı Başlat
                    </>
                  )}
                </button>
              </div>
            </div>
          )}

          {/* Final Scores View */}
          {step === 3 && showResults && scoringResults.length > 0 && (
            <div className="mt-8 animate-in fade-in slide-in-from-bottom-8 duration-700">
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
                  <Award className="w-6 h-6 text-green-600" />
                  Puanlama Sonuçları
                </h2>
                <button
                  onClick={() => { setShowResults(false); setShowConfirm(false); setFile(null); }}
                  className="text-indigo-600 hover:text-indigo-800 font-medium"
                >
                  Yeni Öğrenci Kağıdı Yükle
                </button>
              </div>

              {scoringResults.map((res, index) => {
                const isLowScore = !res.error && res.final_puan < 40;
                return (
                  <div key={index} className={`mb-4 p-6 rounded-xl border ${res.error ? 'bg-red-50 border-red-200' : (isLowScore ? 'bg-orange-50 border-orange-200' : 'bg-green-50 border-green-200')}`}>
                    <div className="flex items-center justify-between mb-4">
                      <span className="text-lg font-semibold text-slate-800">Soru {res.soru_no}</span>
                      {!res.error && (
                        <span className={`text-3xl font-bold ${isLowScore ? 'text-orange-600' : 'text-green-600'}`}>{res.final_puan}/100</span>
                      )}
                    </div>

                    {res.error ? (
                      <p className="text-red-600">{res.error}</p>
                    ) : (
                      <>
                        <div className="grid grid-cols-2 gap-4 mb-4">
                          <div className="bg-white p-3 rounded-lg shadow-sm">
                            <div className="text-sm text-slate-500">Semantik Kontrol (SBERT)</div>
                            <div className="text-xl font-bold text-indigo-600">{(res.bert_skoru * 100).toFixed(1)}%</div>
                          </div>
                          <div className="bg-white p-3 rounded-lg shadow-sm">
                            <div className="text-sm text-slate-500">Rubrik / Mantık Puanı</div>
                            <div className="text-xl font-bold text-purple-600">{res.llm_skoru}/100</div>
                          </div>
                        </div>
                        <div className="bg-white p-4 rounded-lg shadow-sm">
                          <div className="text-sm font-medium text-slate-500 mb-1">Yapay Zeka Değerlendirmesi</div>
                          <p className="text-slate-700">{res.yorum}</p>
                        </div>
                      </>
                    )}
                  </div>
                );
              })}
            </div>
          )}

        </div>
      </div>
    </div>
  );
}

export default App;
