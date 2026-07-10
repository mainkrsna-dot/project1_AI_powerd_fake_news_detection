import React, { useState, useEffect, useCallback } from "react";
import { motion } from "framer-motion";
import { useNavigate } from "react-router-dom";
import {
  Shield,
  Clock,
  FileText,
  Image as ImageIcon,
  Video,
  Newspaper,
  CheckCircle,
  XCircle,
  AlertCircle,
  Trash2,
  ArrowLeft,
  Filter,
  Loader2,
  Sun,
  Moon,
} from "lucide-react";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const HistoryPage = () => {
  const navigate = useNavigate();
  const [history, setHistory] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [filterType, setFilterType] = useState(null);
  const [offset, setOffset] = useState(0);
  const limit = 20;
  const [darkMode, setDarkMode] = useState(() => {
    const saved = localStorage.getItem("truthlens-dark-mode");
    return saved === "true";
  });

  useEffect(() => {
    document.documentElement.classList.toggle("dark", darkMode);
    localStorage.setItem("truthlens-dark-mode", darkMode);
  }, [darkMode]);

  const fetchHistory = useCallback(async () => {
    setLoading(true);
    try {
      const params = { limit, offset };
      if (filterType) params.type = filterType;
      const response = await axios.get(`${API}/history`, { params });
      setHistory(response.data.items);
      setTotal(response.data.total);
    } catch (error) {
      toast.error("Failed to load history");
    } finally {
      setLoading(false);
    }
  }, [filterType, offset]);

  useEffect(() => { fetchHistory(); }, [fetchHistory]);

  const handleClearHistory = async () => {
    if (!window.confirm("Are you sure you want to clear all history?")) return;
    try {
      await axios.delete(`${API}/history`);
      setHistory([]);
      setTotal(0);
      toast.success("History cleared");
    } catch (error) {
      toast.error("Failed to clear history");
    }
  };

  const bg = darkMode ? "bg-[#0c0f1a]" : "bg-[#FAFBFD]";
  const cardBg = darkMode ? "bg-[#151929]/90 border-[#232940]" : "bg-white border-slate-200/80";
  const textPrimary = darkMode ? "text-white" : "text-slate-900";
  const textSecondary = darkMode ? "text-slate-400" : "text-slate-500";
  const textMuted = darkMode ? "text-slate-500" : "text-slate-400";
  const headerBg = darkMode ? "bg-[#0c0f1a]/90 border-[#1e2436]" : "bg-white/90 border-slate-100";

  const getTypeIcon = (type) => {
    switch (type) {
      case "text": return <FileText className="w-5 h-5 text-blue-500" />;
      case "image": return <ImageIcon className="w-5 h-5 text-purple-500" />;
      case "video": return <Video className="w-5 h-5 text-pink-500" />;
      case "verification": return <Newspaper className="w-5 h-5 text-green-500" />;
      default: return <FileText className="w-5 h-5 text-slate-500" />;
    }
  };

  const getStatusBadge = (status) => {
    if (status === "REAL") return <span className="inline-flex items-center gap-1 bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 px-2.5 py-1 rounded-full text-xs font-semibold"><CheckCircle className="w-3 h-3" /> REAL</span>;
    if (status === "FAKE") return <span className="inline-flex items-center gap-1 bg-red-500/10 text-red-400 border border-red-500/20 px-2.5 py-1 rounded-full text-xs font-semibold"><XCircle className="w-3 h-3" /> FAKE</span>;
    return <span className="inline-flex items-center gap-1 bg-amber-500/10 text-amber-400 border border-amber-500/20 px-2.5 py-1 rounded-full text-xs font-semibold"><AlertCircle className="w-3 h-3" /> UNCERTAIN</span>;
  };

  const filterOptions = [
    { label: "All", value: null },
    { label: "Text", value: "text" },
    { label: "Image", value: "image" },
    { label: "Video", value: "video" },
    { label: "Verification", value: "verification" },
  ];

  return (
    <div className={`min-h-screen ${bg} transition-colors duration-300`}>
      <header className={`sticky top-0 z-50 ${headerBg} backdrop-blur-2xl border-b shadow-sm transition-colors`} data-testid="history-header">
        <div className="max-w-7xl mx-auto px-6 sm:px-8 lg:px-12 py-3.5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-blue-500/20">
                <Shield className="w-5 h-5 text-white" />
              </div>
              <h1 className={`text-xl font-serif font-bold ${textPrimary}`}>TruthLens AI</h1>
            </div>
            <div className="flex items-center gap-3">
              <button onClick={() => setDarkMode(!darkMode)} className={`w-9 h-9 rounded-full flex items-center justify-center transition-all ${darkMode ? "bg-slate-800 text-yellow-400 hover:bg-slate-700" : "bg-slate-100 text-slate-600 hover:bg-slate-200"}`} data-testid="dark-mode-toggle">
                {darkMode ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
              </button>
              <Button onClick={() => navigate("/")} variant="outline" className={`rounded-xl ${darkMode ? "border-slate-700 text-slate-300 hover:bg-slate-800" : ""}`} data-testid="back-to-home">
                <ArrowLeft className="w-4 h-4 mr-2" /> Back
              </Button>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 sm:px-8 lg:px-12 py-12">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h2 className={`text-3xl sm:text-4xl font-serif ${textPrimary} flex items-center gap-3 transition-colors`} data-testid="history-title">
              <Clock className="w-8 h-8 text-blue-500" /> Analysis History
            </h2>
            <p className={`${textSecondary} mt-2 transition-colors`}>{total} total analyses</p>
          </div>
          {history.length > 0 && (
            <Button onClick={handleClearHistory} variant="outline" className="text-red-400 border-red-500/30 hover:bg-red-500/10" data-testid="clear-history-button">
              <Trash2 className="w-4 h-4 mr-2" /> Clear All
            </Button>
          )}
        </div>

        <div className="flex flex-wrap gap-2 mb-8" data-testid="history-filters">
          <Filter className={`w-5 h-5 ${textMuted} self-center mr-2`} />
          {filterOptions.map((opt) => (
            <Button
              key={opt.label}
              onClick={() => { setFilterType(opt.value); setOffset(0); }}
              variant={filterType === opt.value ? "default" : "outline"}
              size="sm"
              className={`rounded-full ${filterType === opt.value ? "bg-blue-600 text-white" : darkMode ? "bg-transparent border-slate-700 text-slate-400 hover:bg-slate-800" : "bg-white/70 text-slate-600 hover:bg-white"}`}
              data-testid={`filter-${opt.label.toLowerCase()}`}
            >
              {opt.label}
            </Button>
          ))}
        </div>

        {loading && (
          <div className="flex items-center justify-center py-20" data-testid="history-loading">
            <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
            <span className={`ml-3 ${textSecondary}`}>Loading history...</span>
          </div>
        )}

        {!loading && history.length === 0 && (
          <div className="text-center py-20" data-testid="history-empty">
            <Clock className={`w-16 h-16 ${textMuted} mx-auto mb-4`} />
            <h3 className={`text-xl font-serif ${textPrimary} mb-2`}>No analyses yet</h3>
            <p className={`${textSecondary} mb-6`}>Your analysis history will appear here</p>
            <Button onClick={() => navigate("/")} className="bg-blue-600 hover:bg-blue-700 text-white rounded-full">Start Analyzing</Button>
          </div>
        )}

        {!loading && history.length > 0 && (
          <div className="space-y-3" data-testid="history-list">
            {history.map((item, index) => (
              <motion.div
                key={item.id || index}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.04 }}
                className={`${cardBg} border rounded-2xl p-5 hover:shadow-md transition-all`}
                data-testid={`history-item-${index}`}
              >
                <div className="flex items-start gap-4">
                  <div className="flex-shrink-0 mt-0.5">{getTypeIcon(item.type)}</div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-3 mb-2">
                      <span className={`text-xs font-semibold uppercase tracking-wider ${textMuted} ${darkMode ? "bg-slate-800" : "bg-slate-100"} px-2 py-0.5 rounded`}>{item.type}</span>
                      {getStatusBadge(item.status)}
                      <span className="text-sm font-bold text-blue-500">{Math.round(item.confidence)}%</span>
                    </div>
                    <p className={`${darkMode ? "text-slate-300" : "text-slate-800"} text-sm line-clamp-2 mb-2`}>{item.content_preview}</p>
                    <p className={`text-xs ${textMuted}`}>{new Date(item.timestamp).toLocaleString()}</p>
                  </div>
                </div>
                {item.explanation && (
                  <div className={`mt-3 border-l-3 ${darkMode ? "border-blue-500/30" : "border-blue-400"} pl-4 ml-9`}>
                    <p className={`text-sm ${textSecondary} line-clamp-2`}>{item.explanation}</p>
                  </div>
                )}
              </motion.div>
            ))}
          </div>
        )}

        {!loading && total > limit && (
          <div className="flex items-center justify-center gap-4 mt-8" data-testid="history-pagination">
            <Button onClick={() => setOffset(Math.max(0, offset - limit))} disabled={offset === 0} variant="outline" className={`rounded-xl ${darkMode ? "border-slate-700 text-slate-400" : ""}`} data-testid="pagination-prev">Previous</Button>
            <span className={`text-sm ${textSecondary}`}>Showing {offset + 1}-{Math.min(offset + limit, total)} of {total}</span>
            <Button onClick={() => setOffset(offset + limit)} disabled={offset + limit >= total} variant="outline" className={`rounded-xl ${darkMode ? "border-slate-700 text-slate-400" : ""}`} data-testid="pagination-next">Next</Button>
          </div>
        )}
      </main>
    </div>
  );
};

export default HistoryPage;
