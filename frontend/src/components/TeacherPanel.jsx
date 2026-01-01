import React, { useState, useEffect } from 'react';
import { Plus, Trash2, Save, BookOpen, FileText, Key, Loader2, CheckCircle, AlertCircle } from 'lucide-react';

const API_URL = 'http://127.0.0.1:8000';

function TeacherPanel({ onClose }) {
    const [sorular, setSorular] = useState([]);
    const [loading, setLoading] = useState(false);
    const [saving, setSaving] = useState(false);
    const [message, setMessage] = useState(null);

    // Form state
    const [form, setForm] = useState({
        sinav_id: '',
        soru_no: 1,
        soru_metni: '',
        ideal_cevap: '',
        anahtar_kelimeler: ''
    });

    // Fetch existing questions
    useEffect(() => {
        fetchSorular();
    }, []);

    const fetchSorular = async () => {
        setLoading(true);
        try {
            const response = await fetch(`${API_URL}/api/sinav-sorulari`);
            if (response.ok) {
                const data = await response.json();
                setSorular(data);
            }
        } catch (error) {
            console.error('Sorular yüklenemedi:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();

        if (!form.sinav_id || !form.soru_metni || !form.ideal_cevap) {
            setMessage({ type: 'error', text: 'Lütfen zorunlu alanları doldurun.' });
            return;
        }

        setSaving(true);
        setMessage(null);

        try {
            const response = await fetch(`${API_URL}/api/sinav-sorulari`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(form)
            });

            if (response.ok) {
                setMessage({ type: 'success', text: 'Soru başarıyla kaydedildi!' });
                setForm({
                    sinav_id: form.sinav_id,
                    soru_no: form.soru_no + 1,
                    soru_metni: '',
                    ideal_cevap: '',
                    anahtar_kelimeler: ''
                });
                fetchSorular();
            } else {
                const error = await response.json();
                setMessage({ type: 'error', text: error.detail || 'Kayıt başarısız.' });
            }
        } catch (error) {
            setMessage({ type: 'error', text: 'Sunucu bağlantı hatası.' });
        } finally {
            setSaving(false);
        }
    };

    const handleDelete = async (id) => {
        if (!confirm('Bu soruyu silmek istediğinizden emin misiniz?')) return;

        try {
            const response = await fetch(`${API_URL}/api/sinav-sorulari/${id}`, {
                method: 'DELETE'
            });
            if (response.ok) {
                fetchSorular();
                setMessage({ type: 'success', text: 'Soru silindi.' });
            }
        } catch (error) {
            setMessage({ type: 'error', text: 'Silme işlemi başarısız.' });
        }
    };

    return (
        <div className="bg-white rounded-2xl shadow-xl border border-slate-100 p-8">
            <div className="flex items-center justify-between mb-6">
                <h2 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
                    <BookOpen className="w-6 h-6 text-indigo-600" />
                    Hoca Paneli - Sınav Soruları
                </h2>
                {onClose && (
                    <button onClick={onClose} className="text-slate-400 hover:text-slate-600">
                        ✕
                    </button>
                )}
            </div>

            {/* Message Alert */}
            {message && (
                <div className={`mb-4 p-4 rounded-lg flex items-center gap-3 ${message.type === 'success' ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'
                    }`}>
                    {message.type === 'success' ? <CheckCircle className="w-5 h-5" /> : <AlertCircle className="w-5 h-5" />}
                    {message.text}
                </div>
            )}

            {/* Add Question Form */}
            <form onSubmit={handleSubmit} className="space-y-4 mb-8">
                <div className="grid grid-cols-2 gap-4">
                    <div>
                        <label className="block text-sm font-medium text-slate-700 mb-1">
                            Sınav ID <span className="text-red-500">*</span>
                        </label>
                        <input
                            type="text"
                            value={form.sinav_id}
                            onChange={(e) => setForm({ ...form, sinav_id: e.target.value })}
                            placeholder="örn: VIZE2024"
                            className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-slate-700 mb-1">
                            Soru No <span className="text-red-500">*</span>
                        </label>
                        <input
                            type="number"
                            min="1"
                            value={form.soru_no}
                            onChange={(e) => setForm({ ...form, soru_no: parseInt(e.target.value) || 1 })}
                            className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                        />
                    </div>
                </div>

                <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1 flex items-center gap-1">
                        <FileText className="w-4 h-4" /> Soru Metni <span className="text-red-500">*</span>
                    </label>
                    <textarea
                        value={form.soru_metni}
                        onChange={(e) => setForm({ ...form, soru_metni: e.target.value })}
                        rows={3}
                        placeholder="Sınav sorusunu buraya yazın..."
                        className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    />
                </div>

                <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1 flex items-center gap-1">
                        <CheckCircle className="w-4 h-4 text-green-600" /> İdeal Cevap <span className="text-red-500">*</span>
                    </label>
                    <textarea
                        value={form.ideal_cevap}
                        onChange={(e) => setForm({ ...form, ideal_cevap: e.target.value })}
                        rows={4}
                        placeholder="Bu sorunun ideal/beklenen cevabını yazın..."
                        className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    />
                </div>

                <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1 flex items-center gap-1">
                        <Key className="w-4 h-4 text-amber-600" /> Anahtar Kelimeler (opsiyonel)
                    </label>
                    <input
                        type="text"
                        value={form.anahtar_kelimeler}
                        onChange={(e) => setForm({ ...form, anahtar_kelimeler: e.target.value })}
                        placeholder="virgülle ayırarak yazın: termodinamik, enerji, entropi"
                        className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    />
                </div>

                <button
                    type="submit"
                    disabled={saving}
                    className="w-full flex items-center justify-center gap-2 px-6 py-3 bg-indigo-600 text-white font-semibold rounded-lg hover:bg-indigo-700 transition-colors disabled:bg-slate-400"
                >
                    {saving ? (
                        <>
                            <Loader2 className="w-5 h-5 animate-spin" />
                            Kaydediliyor...
                        </>
                    ) : (
                        <>
                            <Plus className="w-5 h-5" />
                            Soru Ekle
                        </>
                    )}
                </button>
            </form>

            {/* Question List */}
            <div>
                <h3 className="text-lg font-semibold text-slate-800 mb-4">
                    Kayıtlı Sorular ({sorular.length})
                </h3>

                {loading ? (
                    <div className="text-center py-8 text-slate-500">
                        <Loader2 className="w-8 h-8 animate-spin mx-auto mb-2" />
                        Yükleniyor...
                    </div>
                ) : sorular.length === 0 ? (
                    <div className="text-center py-8 text-slate-400 bg-slate-50 rounded-lg">
                        Henüz soru eklenmemiş.
                    </div>
                ) : (
                    <div className="space-y-3 max-h-96 overflow-y-auto">
                        {sorular.map((soru) => (
                            <div key={soru.id} className="bg-slate-50 p-4 rounded-lg border border-slate-200">
                                <div className="flex justify-between items-start">
                                    <div className="flex-1">
                                        <div className="flex items-center gap-2 mb-2">
                                            <span className="bg-indigo-100 text-indigo-700 text-xs font-medium px-2 py-1 rounded">
                                                {soru.sinav_id}
                                            </span>
                                            <span className="bg-slate-200 text-slate-600 text-xs font-medium px-2 py-1 rounded">
                                                Soru {soru.soru_no}
                                            </span>
                                        </div>
                                        <p className="text-slate-700 text-sm mb-1">
                                            <strong>Soru:</strong> {soru.soru_metni.substring(0, 100)}...
                                        </p>
                                        <p className="text-slate-500 text-xs">
                                            <strong>İdeal:</strong> {soru.ideal_cevap.substring(0, 80)}...
                                        </p>
                                    </div>
                                    <button
                                        onClick={() => handleDelete(soru.id)}
                                        className="text-red-400 hover:text-red-600 p-1"
                                    >
                                        <Trash2 className="w-4 h-4" />
                                    </button>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}

export default TeacherPanel;
