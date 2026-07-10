import React, { useState, useRef, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useNavigate } from "react-router-dom";
import {
  FileText,
  Image as ImageIcon,
  Video,
  CheckCircle,
  XCircle,
  AlertCircle,
  Upload,
  Loader2,
  Shield,
  Zap,
  Target,
  Clock,
  Newspaper,
  Files,
  ExternalLink,
  RotateCcw,
  Languages,
  Globe,
  Search,
  Sparkles,
  History,
  ChevronRight,
  Sun,
  Moon,
  Activity,
  Eye,
  Brain,
} from "lucide-react";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { toast } from "sonner";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const LANGUAGE_LABELS = {
  english: "English",
  hindi: "Hindi",
  marathi: "Marathi",
  tamil: "Tamil",
  hinglish: "Hinglish",
};

const HomePage = () => {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState("text");
  const [textInput, setTextInput] = useState("");
  const [imageFile, setImageFile] = useState(null);
  const [videoFile, setVideoFile] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [result, setResult] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);
  const [videoPreview, setVideoPreview] = useState(null);
  const [batchMode, setBatchMode] = useState(false);
  const [batchFiles, setBatchFiles] = useState([]);
  const [batchResults, setBatchResults] = useState(null);
  const [batchProgress, setBatchProgress] = useState("");
  const [verifyMode, setVerifyMode] = useState(false);
  const [recentSearches, setRecentSearches] = useState([]);
  const [showRecent, setShowRecent] = useState(true);
  const [darkMode, setDarkMode] = useState(() => {
    const saved = localStorage.getItem("truthlens-dark-mode");
    return saved === "true";
  });

  const imageInputRef = useRef(null);
  const videoInputRef = useRef(null);
  const batchImageInputRef = useRef(null);
  const batchVideoInputRef = useRef(null);

  useEffect(() => {
    document.documentElement.classList.toggle("dark", darkMode);
    localStorage.setItem("truthlens-dark-mode", darkMode);
  }, [darkMode]);

  const fetchRecentSearches = useCallback(async () => {
    try {
      const response = await axios.get(`${API}/history`, { params: { limit: 5 } });
      setRecentSearches(response.data.items || []);
    } catch (e) { /* non-critical */ }
  }, []);

  useEffect(() => { fetchRecentSearches(); }, [fetchRecentSearches]);

  const handleNewSearch = () => {
    setResult(null);
    setBatchResults(null);
    setTextInput("");
    setImageFile(null);
    setVideoFile(null);
    setImagePreview(null);
    setVideoPreview(null);
    setBatchFiles([]);
    setBatchProgress("");
    fetchRecentSearches();
    document.getElementById("detection-section")?.scrollIntoView({ behavior: "smooth" });
  };

  const handleTextAnalysis = async () => {
    if (!textInput.trim()) { toast.error("Please enter some text to analyze"); return; }
    setIsAnalyzing(true); setResult(null); setBatchResults(null);
    try {
      const endpoint = verifyMode ? `${API}/verify-news` : `${API}/detect-text`;
      const payload = verifyMode ? { claim: textInput } : { text: textInput };
      const response = await axios.post(endpoint, payload);
      setResult(response.data);
      toast.success("Analysis complete!");
      fetchRecentSearches();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Analysis failed. Please try again.");
    } finally { setIsAnalyzing(false); }
  };

  const handleImageUpload = (e) => {
    const file = e.target.files[0];
    if (file) { setImageFile(file); const r = new FileReader(); r.onloadend = () => setImagePreview(r.result); r.readAsDataURL(file); }
  };

  const handleImageAnalysis = async () => {
    if (!imageFile) { toast.error("Please upload an image first"); return; }
    setIsAnalyzing(true); setResult(null); setBatchResults(null);
    try {
      const formData = new FormData(); formData.append("file", imageFile);
      const response = await axios.post(`${API}/detect-image`, formData, { headers: { "Content-Type": "multipart/form-data" } });
      setResult(response.data);
      toast.success("Image analysis complete!");
      fetchRecentSearches();
    } catch (error) { toast.error(error.response?.data?.detail || "Image analysis failed."); }
    finally { setIsAnalyzing(false); }
  };

  const handleVideoUpload = (e) => {
    const file = e.target.files[0];
    if (file) { setVideoFile(file); const r = new FileReader(); r.onloadend = () => setVideoPreview(r.result); r.readAsDataURL(file); }
  };

  const handleVideoAnalysis = async () => {
    if (!videoFile) { toast.error("Please upload a video first"); return; }
    setIsAnalyzing(true); setResult(null); setBatchResults(null);
    try {
      const formData = new FormData(); formData.append("file", videoFile);
      const response = await axios.post(`${API}/detect-video`, formData, { headers: { "Content-Type": "multipart/form-data" } });
      setResult(response.data);
      toast.success("Video analysis complete!");
      fetchRecentSearches();
    } catch (error) { toast.error(error.response?.data?.detail || "Video analysis failed."); }
    finally { setIsAnalyzing(false); }
  };

  const handleBatchFilesSelect = (e) => setBatchFiles(Array.from(e.target.files));

  const handleBatchAnalysis = async () => {
    if (batchFiles.length === 0) { toast.error("Please select files"); return; }
    setIsAnalyzing(true); setResult(null); setBatchResults(null);
    setBatchProgress(`Analyzing ${batchFiles.length} files...`);
    try {
      const formData = new FormData();
      batchFiles.forEach((file) => formData.append("files", file));
      const endpoint = activeTab === "image" ? `${API}/batch-detect-images` : `${API}/batch-detect-videos`;
      const response = await axios.post(endpoint, formData, { headers: { "Content-Type": "multipart/form-data" } });
      setBatchResults(response.data);
      toast.success(`Batch complete! ${response.data.successful}/${response.data.total_files} analyzed.`);
      fetchRecentSearches();
    } catch (error) { toast.error(error.response?.data?.detail || "Batch failed."); }
    finally { setIsAnalyzing(false); setBatchProgress(""); }
  };

  const scrollToDetection = () => document.getElementById("detection-section")?.scrollIntoView({ behavior: "smooth" });

  // Theme classes
  const bg = darkMode ? "bg-[#0c0f1a]" : "bg-[#FAFBFD]";
  const cardBg = darkMode ? "bg-[#151929]/90 border-[#232940]" : "bg-white border-slate-200/80";
  const textPrimary = darkMode ? "text-white" : "text-slate-900";
  const textSecondary = darkMode ? "text-slate-400" : "text-slate-500";
  const textMuted = darkMode ? "text-slate-500" : "text-slate-400";
  const headerBg = darkMode ? "bg-[#0c0f1a]/90 border-[#1e2436]" : "bg-white/90 border-slate-100";
  const inputBg = darkMode ? "bg-[#1a1f33] border-[#2a3150] text-white placeholder:text-slate-600" : "bg-slate-50 border-slate-200 text-slate-900";
  const uploadBg = darkMode ? "border-[#2a3150] bg-[#131726] hover:bg-[#1a1f33] hover:border-blue-500/40" : "border-slate-200 bg-slate-50/50 hover:bg-blue-50/30 hover:border-blue-300";

  const ResultBadge = ({ status }) => {
    if (status === "REAL") return (
      <div className="flex items-center gap-2 bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 px-4 py-2 rounded-full font-semibold text-sm" data-testid="result-badge-real">
        <CheckCircle className="w-4 h-4" /> REAL
      </div>
    );
    if (status === "FAKE") return (
      <div className="flex items-center gap-2 bg-red-500/10 text-red-400 border border-red-500/20 px-4 py-2 rounded-full font-semibold text-sm" data-testid="result-badge-fake">
        <XCircle className="w-4 h-4" /> FAKE
      </div>
    );
    return (
      <div className="flex items-center gap-2 bg-amber-500/10 text-amber-400 border border-amber-500/20 px-4 py-2 rounded-full font-semibold text-sm" data-testid="result-badge-uncertain">
        <AlertCircle className="w-4 h-4" /> UNCERTAIN
      </div>
    );
  };

  const ResultCard = ({ data }) => (
    <motion.div
      initial={{ opacity: 0, y: 20, scale: 0.98 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ type: "spring", stiffness: 200, damping: 20 }}
      className={`${cardBg} backdrop-blur-2xl shadow-2xl rounded-3xl p-8 relative overflow-hidden border`}
      data-testid="result-card"
    >
      <div className={`absolute top-0 left-0 right-0 h-1 ${data.status === "REAL" ? "bg-gradient-to-r from-emerald-400 to-teal-500" : data.status === "FAKE" ? "bg-gradient-to-r from-red-400 to-rose-500" : "bg-gradient-to-r from-amber-400 to-orange-500"}`} />

      <div className="flex items-center justify-between mb-6 mt-2">
        <h3 className={`text-2xl font-serif ${textPrimary}`}>Analysis Result</h3>
        <ResultBadge status={data.status} />
      </div>

      {data.detected_language && data.detected_language !== "english" && (
        <div className={`flex items-center gap-2 mb-5 ${darkMode ? "bg-indigo-500/10 border-indigo-500/20 text-indigo-300" : "bg-indigo-50 border-indigo-100 text-indigo-700"} border px-4 py-2.5 rounded-xl text-sm`} data-testid="language-badge">
          <Languages className="w-4 h-4" />
          <span>Detected: <strong>{LANGUAGE_LABELS[data.detected_language] || data.detected_language}</strong></span>
        </div>
      )}

      {/* Confidence */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-3">
          <span className={`${textSecondary} font-medium text-sm`}>Confidence Score</span>
          <div className="flex items-baseline gap-1">
            <span className="text-4xl font-bold text-blue-500" data-testid="confidence-score">{Math.round(data.confidence)}</span>
            <span className="text-lg text-blue-400/60 font-medium">%</span>
          </div>
        </div>
        <div className={`relative h-2.5 rounded-full ${darkMode ? "bg-slate-800" : "bg-slate-100"} overflow-hidden`}>
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${data.confidence}%` }}
            transition={{ duration: 1.2, ease: "easeOut" }}
            className={`absolute inset-y-0 left-0 rounded-full ${data.status === "REAL" ? "bg-gradient-to-r from-emerald-400 to-teal-500" : data.status === "FAKE" ? "bg-gradient-to-r from-red-400 to-rose-500" : "bg-gradient-to-r from-amber-400 to-orange-500"}`}
          />
        </div>
      </div>

      {/* Explanation */}
      <div className={`border-l-4 border-blue-500 ${darkMode ? "bg-blue-500/5" : "bg-blue-50/80"} p-5 rounded-r-xl mb-5`} data-testid="explanation-box">
        <h4 className={`font-semibold ${textPrimary} mb-2 flex items-center gap-2 text-sm`}>
          {data.detected_language && data.detected_language !== "english" && <Globe className="w-4 h-4 text-blue-500" />}
          Explanation {data.detected_language && data.detected_language !== "english" && `(${LANGUAGE_LABELS[data.detected_language]})`}
        </h4>
        <p className={`${darkMode ? "text-slate-300" : "text-slate-700"} leading-relaxed text-sm`}>{data.explanation}</p>
      </div>

      {data.explanation_english && data.detected_language && data.detected_language !== "english" && (
        <div className={`border-l-4 ${darkMode ? "border-slate-700 bg-slate-800/50" : "border-slate-300 bg-slate-50/80"} p-5 rounded-r-xl mb-5`} data-testid="english-explanation-box">
          <h4 className={`font-semibold ${textSecondary} mb-2 flex items-center gap-2 text-xs uppercase tracking-wider`}>
            <Globe className="w-3.5 h-3.5" /> English Translation
          </h4>
          <p className={`${darkMode ? "text-slate-400" : "text-slate-600"} leading-relaxed text-sm`}>{data.explanation_english}</p>
        </div>
      )}

      {data.suspicious_keywords && data.suspicious_keywords.length > 0 && (
        <div className="mb-5" data-testid="suspicious-keywords">
          <h4 className={`font-semibold ${textPrimary} mb-3 text-sm`}>Key Indicators</h4>
          <div className="flex flex-wrap gap-2">
            {data.suspicious_keywords.map((kw, i) => (
              <span key={i} className={`${darkMode ? "bg-slate-800 text-slate-300 border-slate-700" : "bg-slate-100 text-slate-700 border-slate-200"} border px-3 py-1.5 rounded-lg text-xs`}>{kw}</span>
            ))}
          </div>
        </div>
      )}

      {data.sources && data.sources.length > 0 && data.sources[0] && (
        <div className="mb-5" data-testid="sources-section">
          <h4 className={`font-semibold ${textPrimary} mb-3 text-sm`}>Additional Context</h4>
          <ul className="space-y-1.5">
            {data.sources.map((s, i) => s ? <li key={i} className={`${textSecondary} text-xs pl-3 border-l-2 ${darkMode ? "border-slate-700" : "border-slate-200"}`}>{s}</li> : null)}
          </ul>
        </div>
      )}

      {data.matching_articles && data.matching_articles.length > 0 && (
        <div className={`border-t ${darkMode ? "border-slate-800" : "border-slate-200"} pt-5`} data-testid="news-articles-section">
          <h4 className={`font-semibold ${textPrimary} mb-3 flex items-center gap-2 text-sm`}>
            <Newspaper className="w-4 h-4 text-blue-500" /> Related News
          </h4>
          <div className="space-y-2">
            {data.matching_articles.map((a, i) => (
              <div key={i} className={`${darkMode ? "bg-slate-800/50 border-slate-700" : "bg-white border-slate-200"} border rounded-xl p-3`}>
                <a href={a.url} target="_blank" rel="noopener noreferrer" className="text-blue-500 hover:underline text-sm flex items-center gap-1 font-medium">
                  {a.title} <ExternalLink className="w-3 h-3" />
                </a>
                <p className={`text-xs ${textMuted} mt-0.5`}>{a.source}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className={`mt-8 pt-5 border-t ${darkMode ? "border-slate-800" : "border-slate-200"} flex justify-center`}>
        <Button onClick={handleNewSearch} variant="outline" className={`rounded-full px-8 py-3 gap-2 ${darkMode ? "text-blue-400 border-blue-500/30 hover:bg-blue-500/10" : "text-blue-600 border-blue-200 hover:bg-blue-50"}`} data-testid="new-search-button">
          <RotateCcw className="w-4 h-4" /> New Search
        </Button>
      </div>
    </motion.div>
  );

  return (
    <div className={`min-h-screen ${bg} transition-colors duration-300`}>
      {/* Header */}
      <header className={`sticky top-0 z-50 ${headerBg} backdrop-blur-2xl border-b shadow-sm transition-colors duration-300`} data-testid="header">
        <div className="max-w-7xl mx-auto px-6 sm:px-8 lg:px-12 py-3.5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-blue-500/20">
                <Shield className="w-5 h-5 text-white" />
              </div>
              <h1 className={`text-xl font-serif font-bold ${textPrimary} transition-colors`} data-testid="logo">TruthLens AI</h1>
            </div>
            <nav className="hidden md:flex items-center gap-7">
              <a href="#home" className={`${textSecondary} hover:text-blue-500 font-medium transition-colors text-sm`} data-testid="nav-home">Home</a>
              <a href="#detection-section" className={`${textSecondary} hover:text-blue-500 font-medium transition-colors text-sm`} data-testid="nav-detect">Detect</a>
              <a href="#how-it-works" className={`${textSecondary} hover:text-blue-500 font-medium transition-colors text-sm`} data-testid="nav-how">How It Works</a>
              <button onClick={() => navigate("/history")} className={`${textSecondary} hover:text-blue-500 font-medium transition-colors text-sm flex items-center gap-1`} data-testid="nav-history">
                <Clock className="w-3.5 h-3.5" /> History
              </button>
            </nav>
            <div className="flex items-center gap-3">
              <button
                onClick={() => setDarkMode(!darkMode)}
                className={`w-9 h-9 rounded-full flex items-center justify-center transition-all ${darkMode ? "bg-slate-800 text-yellow-400 hover:bg-slate-700" : "bg-slate-100 text-slate-600 hover:bg-slate-200"}`}
                data-testid="dark-mode-toggle"
              >
                {darkMode ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
              </button>
              <Button onClick={scrollToDetection} className="bg-blue-600 hover:bg-blue-700 text-white rounded-full px-5 py-2 text-sm shadow-md shadow-blue-500/20 hover:shadow-lg transition-all" data-testid="header-cta-button">
                Verify Now
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section id="home" className="relative py-28 sm:py-36 overflow-hidden" data-testid="hero-section">
        {/* Animated background */}
        <div className={`absolute inset-0 ${darkMode ? "bg-[#0c0f1a]" : "bg-gradient-to-br from-blue-50/60 via-white to-indigo-50/40"}`} />
        {darkMode ? (
          <>
            <div className="absolute top-20 left-10 w-80 h-80 bg-blue-600/8 rounded-full blur-3xl" />
            <div className="absolute bottom-20 right-10 w-96 h-96 bg-indigo-600/6 rounded-full blur-3xl" />
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-blue-600/4 rounded-full blur-3xl" />
          </>
        ) : (
          <>
            <div className="absolute top-20 left-10 w-72 h-72 bg-blue-100/50 rounded-full blur-3xl animate-pulse" />
            <div className="absolute bottom-20 right-10 w-96 h-96 bg-indigo-100/40 rounded-full blur-3xl" />
          </>
        )}

        <div className="max-w-7xl mx-auto px-6 sm:px-8 lg:px-12 text-center relative z-10">
          <motion.div initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.7 }}>
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.3 }}
              className={`inline-flex items-center gap-2 ${darkMode ? "bg-blue-500/10 border-blue-500/20 text-blue-300" : "bg-white/80 border-slate-200 text-slate-600"} backdrop-blur-sm border rounded-full px-4 py-2 text-sm mb-8 shadow-sm`}
              data-testid="multilingual-badge"
            >
              <Languages className="w-4 h-4 text-blue-500" />
              Supports English, Hindi, Marathi, Tamil & Hinglish
            </motion.div>

            <h1 className={`text-5xl sm:text-6xl lg:text-7xl tracking-tighter font-serif ${textPrimary} leading-[1.1] mb-6 transition-colors`} data-testid="hero-title">
              AI-Powered{" "}
              <span className="bg-gradient-to-r from-blue-500 to-indigo-500 bg-clip-text text-transparent">
                Fake News
              </span>
              <br />
              <span className={darkMode ? "text-slate-200" : "text-slate-800"}>Detector</span>
            </h1>
            <p className={`text-lg ${textSecondary} max-w-2xl mx-auto mb-10 leading-relaxed transition-colors`} data-testid="hero-subtitle">
              Verify the authenticity of news articles, images, and videos using cutting-edge AI. Get instant results in your preferred language.
            </p>

            {/* Stats row */}
            <div className="flex items-center justify-center gap-8 mb-10">
              {[
                { icon: Brain, label: "GPT-5.2 Powered", value: "AI" },
                { icon: Eye, label: "Vision Analysis", value: "Deep" },
                { icon: Activity, label: "Detection Rate", value: "98%" },
              ].map((stat, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.5 + i * 0.1 }}
                  className={`flex items-center gap-2 ${textMuted} text-sm`}
                >
                  <stat.icon className="w-4 h-4 text-blue-500" />
                  <span className={`font-semibold ${textPrimary}`}>{stat.value}</span>
                  <span>{stat.label}</span>
                </motion.div>
              ))}
            </div>

            <Button onClick={scrollToDetection} size="lg" className="bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white rounded-full px-10 py-6 text-base shadow-xl shadow-blue-500/20 hover:shadow-2xl hover:shadow-blue-500/30 transition-all gap-2" data-testid="hero-cta-button">
              <Search className="w-5 h-5" />
              Start Verification
            </Button>
          </motion.div>
        </div>
      </section>

      {/* Detection Section */}
      <section id="detection-section" className="py-20 relative" data-testid="detection-section">
        <div className="max-w-7xl mx-auto px-6 sm:px-8 lg:px-12">
          <div className="text-center mb-12">
            <h2 className={`text-3xl sm:text-4xl tracking-tight font-serif ${textPrimary} mb-4 transition-colors`} data-testid="detection-title">
              Choose Detection Method
            </h2>
            <p className={`${textSecondary} text-base transition-colors`}>Select the type of content you want to verify</p>
          </div>

          {/* Tab Selection */}
          <div className="flex justify-center mb-10" data-testid="detection-tabs">
            <div className={`inline-flex ${darkMode ? "bg-[#151929]" : "bg-slate-100"} rounded-2xl p-1.5 gap-1 transition-colors`}>
              {["text", "image", "video"].map((tab) => (
                <button
                  key={tab}
                  onClick={() => { setActiveTab(tab); setResult(null); setBatchResults(null); setBatchMode(false); }}
                  className={`flex items-center gap-2 px-6 py-3 rounded-xl text-sm font-medium transition-all ${activeTab === tab ? (darkMode ? "bg-[#1e2436] text-blue-400 shadow-lg shadow-blue-500/5" : "bg-white text-blue-600 shadow-sm") : `${textSecondary} hover:text-blue-500`}`}
                  data-testid={`tab-${tab}`}
                >
                  {tab === "text" && <FileText className="w-4 h-4" />}
                  {tab === "image" && <ImageIcon className="w-4 h-4" />}
                  {tab === "video" && <Video className="w-4 h-4" />}
                  {tab.charAt(0).toUpperCase() + tab.slice(1)}
                </button>
              ))}
            </div>
          </div>

          {/* Detection Cards */}
          <div className="max-w-3xl mx-auto">
            <AnimatePresence mode="wait">
              {activeTab === "text" && (
                <motion.div key="text" initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: 20 }} className={`${cardBg} border shadow-xl rounded-3xl p-8 transition-colors`} data-testid="text-detection-card">
                  <div className="flex items-center justify-between mb-5">
                    <h3 className={`text-lg font-serif ${textPrimary} flex items-center gap-2 transition-colors`}>
                      <Sparkles className="w-5 h-5 text-blue-500" />Text News Detection
                    </h3>
                    <label className={`flex items-center gap-2 cursor-pointer ${darkMode ? "bg-slate-800 border-slate-700" : "bg-slate-50 border-slate-200"} px-3 py-1.5 rounded-lg border`} data-testid="verify-mode-toggle">
                      <input type="checkbox" checked={verifyMode} onChange={(e) => setVerifyMode(e.target.checked)} className="w-3.5 h-3.5 text-blue-600 rounded" />
                      <span className={`text-xs ${textSecondary} flex items-center gap-1 font-medium`}><Newspaper className="w-3.5 h-3.5" /> Verify</span>
                    </label>
                  </div>
                  <p className={`text-xs ${textMuted} mb-3 flex items-center gap-1`}><Languages className="w-3.5 h-3.5" />Supports: English, Hindi, Marathi, Tamil, Hinglish</p>
                  <Textarea
                    value={textInput}
                    onChange={(e) => setTextInput(e.target.value)}
                    placeholder={verifyMode ? "Enter a claim to verify (any language)..." : "Paste news article text here (any language)..."}
                    className={`min-h-[180px] ${inputBg} focus:ring-4 focus:ring-blue-500/10 focus:border-blue-400 rounded-2xl mb-5 text-base resize-none transition-colors`}
                    data-testid="text-input"
                  />
                  <Button onClick={handleTextAnalysis} disabled={isAnalyzing} className="w-full bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white rounded-2xl py-6 text-base font-medium shadow-lg shadow-blue-500/15 hover:shadow-xl transition-all" data-testid="text-analyze-button">
                    {isAnalyzing ? <><Loader2 className="w-5 h-5 mr-2 animate-spin" />Analyzing...</> : verifyMode ? <><Newspaper className="w-5 h-5 mr-2" />Verify Claim</> : <><Search className="w-5 h-5 mr-2" />Analyze Text</>}
                  </Button>
                </motion.div>
              )}

              {activeTab === "image" && (
                <motion.div key="image" initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: 20 }} className={`${cardBg} border shadow-xl rounded-3xl p-8 transition-colors`} data-testid="image-detection-card">
                  <div className="flex items-center justify-between mb-5">
                    <h3 className={`text-lg font-serif ${textPrimary} flex items-center gap-2`}><Sparkles className="w-5 h-5 text-purple-500" />Image Deepfake Detection</h3>
                    <label className={`flex items-center gap-2 cursor-pointer ${darkMode ? "bg-slate-800 border-slate-700" : "bg-slate-50 border-slate-200"} px-3 py-1.5 rounded-lg border`} data-testid="batch-mode-toggle">
                      <input type="checkbox" checked={batchMode} onChange={(e) => { setBatchMode(e.target.checked); setBatchFiles([]); setBatchResults(null); }} className="w-3.5 h-3.5 text-blue-600 rounded" />
                      <span className={`text-xs ${textSecondary} flex items-center gap-1 font-medium`}><Files className="w-3.5 h-3.5" /> Batch</span>
                    </label>
                  </div>
                  {!batchMode ? (
                    <>
                      <div onClick={() => imageInputRef.current?.click()} className={`border-2 border-dashed ${uploadBg} transition-all rounded-2xl p-10 flex flex-col items-center justify-center text-center cursor-pointer mb-5 min-h-[200px] group`} data-testid="image-upload-area">
                        {imagePreview ? <img src={imagePreview} alt="Preview" className="max-h-56 rounded-xl shadow-lg" /> : (
                          <><div className={`w-14 h-14 rounded-2xl ${darkMode ? "bg-blue-500/10" : "bg-blue-50"} flex items-center justify-center mb-4`}><Upload className="w-7 h-7 text-blue-500" /></div><p className={`${textSecondary} font-medium`}>Click to upload or drag and drop</p><p className={`text-sm ${textMuted} mt-1`}>PNG, JPG up to 10MB</p></>
                        )}
                      </div>
                      <input ref={imageInputRef} type="file" accept="image/*" onChange={handleImageUpload} className="hidden" data-testid="image-file-input" />
                      <Button onClick={handleImageAnalysis} disabled={isAnalyzing || !imageFile} className="w-full bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white rounded-2xl py-6 text-base font-medium shadow-lg shadow-blue-500/15 transition-all" data-testid="image-analyze-button">
                        {isAnalyzing ? <><Loader2 className="w-5 h-5 mr-2 animate-spin" />Analyzing...</> : "Analyze Image"}
                      </Button>
                    </>
                  ) : (
                    <>
                      <div onClick={() => batchImageInputRef.current?.click()} className={`border-2 border-dashed ${uploadBg} transition-all rounded-2xl p-10 flex flex-col items-center justify-center text-center cursor-pointer mb-5 min-h-[200px] group`} data-testid="batch-image-upload-area">
                        {batchFiles.length > 0 ? <div className="text-center"><div className={`w-14 h-14 rounded-2xl ${darkMode ? "bg-blue-500/10" : "bg-blue-50"} flex items-center justify-center mb-4 mx-auto`}><Files className="w-7 h-7 text-blue-500" /></div><p className={`${textPrimary} font-medium`}>{batchFiles.length} files selected</p><p className={`text-sm ${textMuted} mt-1 max-w-sm truncate`}>{batchFiles.map(f => f.name).join(", ")}</p></div> : <><div className={`w-14 h-14 rounded-2xl ${darkMode ? "bg-blue-500/10" : "bg-blue-50"} flex items-center justify-center mb-4`}><Files className="w-7 h-7 text-blue-500" /></div><p className={`${textSecondary} font-medium`}>Select multiple images</p><p className={`text-sm ${textMuted} mt-1`}>Max 10 files</p></>}
                      </div>
                      <input ref={batchImageInputRef} type="file" accept="image/*" multiple onChange={handleBatchFilesSelect} className="hidden" data-testid="batch-image-file-input" />
                      <Button onClick={handleBatchAnalysis} disabled={isAnalyzing || batchFiles.length === 0} className="w-full bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white rounded-2xl py-6 text-base font-medium shadow-lg transition-all" data-testid="batch-image-analyze-button">
                        {isAnalyzing ? <><Loader2 className="w-5 h-5 mr-2 animate-spin" />{batchProgress}</> : `Analyze ${batchFiles.length} Images`}
                      </Button>
                    </>
                  )}
                </motion.div>
              )}

              {activeTab === "video" && (
                <motion.div key="video" initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: 20 }} className={`${cardBg} border shadow-xl rounded-3xl p-8 transition-colors`} data-testid="video-detection-card">
                  <div className="flex items-center justify-between mb-5">
                    <h3 className={`text-lg font-serif ${textPrimary} flex items-center gap-2`}><Sparkles className="w-5 h-5 text-pink-500" />Video Deepfake Detection</h3>
                    <label className={`flex items-center gap-2 cursor-pointer ${darkMode ? "bg-slate-800 border-slate-700" : "bg-slate-50 border-slate-200"} px-3 py-1.5 rounded-lg border`} data-testid="batch-video-toggle">
                      <input type="checkbox" checked={batchMode} onChange={(e) => { setBatchMode(e.target.checked); setBatchFiles([]); setBatchResults(null); }} className="w-3.5 h-3.5 text-blue-600 rounded" />
                      <span className={`text-xs ${textSecondary} flex items-center gap-1 font-medium`}><Files className="w-3.5 h-3.5" /> Batch</span>
                    </label>
                  </div>
                  {!batchMode ? (
                    <>
                      <div onClick={() => videoInputRef.current?.click()} className={`border-2 border-dashed ${uploadBg} transition-all rounded-2xl p-10 flex flex-col items-center justify-center text-center cursor-pointer mb-5 min-h-[200px] group`} data-testid="video-upload-area">
                        {videoPreview ? <video src={videoPreview} controls className="max-h-56 rounded-xl shadow-lg" /> : <><div className={`w-14 h-14 rounded-2xl ${darkMode ? "bg-blue-500/10" : "bg-blue-50"} flex items-center justify-center mb-4`}><Video className="w-7 h-7 text-blue-500" /></div><p className={`${textSecondary} font-medium`}>Click to upload or drag and drop</p><p className={`text-sm ${textMuted} mt-1`}>MP4, MOV up to 100MB</p></>}
                      </div>
                      <input ref={videoInputRef} type="file" accept="video/*" onChange={handleVideoUpload} className="hidden" data-testid="video-file-input" />
                      <Button onClick={handleVideoAnalysis} disabled={isAnalyzing || !videoFile} className="w-full bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white rounded-2xl py-6 text-base font-medium shadow-lg transition-all" data-testid="video-analyze-button">
                        {isAnalyzing ? <><Loader2 className="w-5 h-5 mr-2 animate-spin" />Analyzing...</> : "Analyze Video"}
                      </Button>
                    </>
                  ) : (
                    <>
                      <div onClick={() => batchVideoInputRef.current?.click()} className={`border-2 border-dashed ${uploadBg} transition-all rounded-2xl p-10 flex flex-col items-center justify-center text-center cursor-pointer mb-5 min-h-[200px] group`} data-testid="batch-video-upload-area">
                        {batchFiles.length > 0 ? <div className="text-center"><div className={`w-14 h-14 rounded-2xl ${darkMode ? "bg-blue-500/10" : "bg-blue-50"} flex items-center justify-center mb-4 mx-auto`}><Files className="w-7 h-7 text-blue-500" /></div><p className={`${textPrimary} font-medium`}>{batchFiles.length} videos selected</p><p className={`text-sm ${textMuted} mt-1 max-w-sm truncate`}>{batchFiles.map(f => f.name).join(", ")}</p></div> : <><div className={`w-14 h-14 rounded-2xl ${darkMode ? "bg-blue-500/10" : "bg-blue-50"} flex items-center justify-center mb-4`}><Files className="w-7 h-7 text-blue-500" /></div><p className={`${textSecondary} font-medium`}>Select multiple videos</p><p className={`text-sm ${textMuted} mt-1`}>Max 5 files</p></>}
                      </div>
                      <input ref={batchVideoInputRef} type="file" accept="video/*" multiple onChange={handleBatchFilesSelect} className="hidden" data-testid="batch-video-file-input" />
                      <Button onClick={handleBatchAnalysis} disabled={isAnalyzing || batchFiles.length === 0} className="w-full bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white rounded-2xl py-6 text-base font-medium shadow-lg transition-all" data-testid="batch-video-analyze-button">
                        {isAnalyzing ? <><Loader2 className="w-5 h-5 mr-2 animate-spin" />{batchProgress}</> : `Analyze ${batchFiles.length} Videos`}
                      </Button>
                    </>
                  )}
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {/* Result */}
          {result && <div className="max-w-3xl mx-auto mt-10"><ResultCard data={result} /></div>}

          {/* Batch Results */}
          {batchResults && (
            <div className="max-w-3xl mx-auto mt-10" data-testid="batch-results">
              <div className={`${cardBg} border shadow-xl rounded-3xl p-8 mb-4 transition-colors`}>
                <h3 className={`text-2xl font-serif ${textPrimary} mb-4`}>Batch Results</h3>
                <div className="flex items-center gap-8 mb-4">
                  <div className="text-center"><p className="text-3xl font-bold text-blue-500">{batchResults.total_files}</p><p className={`text-xs ${textMuted} uppercase tracking-wider mt-1`}>Total</p></div>
                  <div className="text-center"><p className="text-3xl font-bold text-emerald-500">{batchResults.successful}</p><p className={`text-xs ${textMuted} uppercase tracking-wider mt-1`}>Passed</p></div>
                  {batchResults.failed > 0 && <div className="text-center"><p className="text-3xl font-bold text-red-500">{batchResults.failed}</p><p className={`text-xs ${textMuted} uppercase tracking-wider mt-1`}>Failed</p></div>}
                </div>
              </div>
              <div className="space-y-3">
                {batchResults.results.map((item, index) => (
                  <motion.div key={index} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: index * 0.08 }} className={`${cardBg} border shadow-sm rounded-2xl p-5 transition-colors`} data-testid={`batch-result-${index}`}>
                    <div className="flex items-center justify-between mb-2"><span className={`font-medium ${textPrimary} text-sm`}>{item.filename}</span><ResultBadge status={item.status} /></div>
                    {item.success ? <><div className="flex items-center gap-2 mb-1"><span className={`text-xs ${textMuted}`}>Confidence:</span><span className="font-bold text-blue-500 text-sm">{Math.round(item.confidence)}%</span></div><p className={`text-sm ${textSecondary} line-clamp-2`}>{item.explanation}</p></> : <p className="text-sm text-red-400">{item.explanation}</p>}
                  </motion.div>
                ))}
              </div>
              <div className="mt-8 flex justify-center">
                <Button onClick={handleNewSearch} variant="outline" className={`rounded-full px-8 py-3 gap-2 ${darkMode ? "text-blue-400 border-blue-500/30 hover:bg-blue-500/10" : "text-blue-600 border-blue-200 hover:bg-blue-50"}`} data-testid="batch-new-search-button"><RotateCcw className="w-4 h-4" /> New Search</Button>
              </div>
            </div>
          )}

          {/* Recent Searches Widget */}
          {recentSearches.length > 0 && !result && !batchResults && (
            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }} className="max-w-3xl mx-auto mt-10" data-testid="recent-searches-widget">
              <div className={`${cardBg} border shadow-sm rounded-2xl overflow-hidden transition-colors`}>
                <button onClick={() => setShowRecent(!showRecent)} className={`w-full flex items-center justify-between px-6 py-4 ${darkMode ? "hover:bg-slate-800/50" : "hover:bg-slate-50/50"} transition-colors`} data-testid="recent-searches-toggle">
                  <div className="flex items-center gap-2.5">
                    <History className="w-4 h-4 text-blue-500" />
                    <span className={`text-sm font-semibold ${textPrimary}`}>Recent Searches</span>
                    <span className={`text-xs ${textMuted} ${darkMode ? "bg-slate-800" : "bg-slate-100"} px-2 py-0.5 rounded-full`}>{recentSearches.length}</span>
                  </div>
                  <ChevronRight className={`w-4 h-4 ${textMuted} transition-transform ${showRecent ? "rotate-90" : ""}`} />
                </button>
                <AnimatePresence>
                  {showRecent && (
                    <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: "auto", opacity: 1 }} exit={{ height: 0, opacity: 0 }} transition={{ duration: 0.2 }} className="overflow-hidden">
                      <div className={`border-t ${darkMode ? "border-slate-800 divide-slate-800" : "border-slate-100 divide-slate-100"} divide-y`}>
                        {recentSearches.map((item, index) => (
                          <div key={item.id || index} className={`px-6 py-3.5 flex items-center gap-4 ${darkMode ? "hover:bg-slate-800/30" : "hover:bg-slate-50/50"} transition-colors`} data-testid={`recent-item-${index}`}>
                            <div className="flex-shrink-0">
                              {item.type === "text" && <FileText className="w-4 h-4 text-blue-500" />}
                              {item.type === "image" && <ImageIcon className="w-4 h-4 text-purple-500" />}
                              {item.type === "video" && <Video className="w-4 h-4 text-pink-500" />}
                              {item.type === "verification" && <Newspaper className="w-4 h-4 text-green-500" />}
                            </div>
                            <div className="flex-1 min-w-0">
                              <p className={`text-sm ${darkMode ? "text-slate-300" : "text-slate-700"} truncate`}>{item.content_preview}</p>
                              <p className={`text-xs ${textMuted} mt-0.5`}>{new Date(item.timestamp).toLocaleString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}</p>
                            </div>
                            <div className="flex items-center gap-2 flex-shrink-0">
                              <span className={`text-xs font-bold ${item.status === "REAL" ? "text-emerald-500" : item.status === "FAKE" ? "text-red-500" : "text-amber-500"}`}>{Math.round(item.confidence)}%</span>
                              {item.status === "REAL" && <CheckCircle className="w-3.5 h-3.5 text-emerald-500" />}
                              {item.status === "FAKE" && <XCircle className="w-3.5 h-3.5 text-red-500" />}
                              {item.status === "UNCERTAIN" && <AlertCircle className="w-3.5 h-3.5 text-amber-500" />}
                            </div>
                          </div>
                        ))}
                      </div>
                      <div className={`border-t ${darkMode ? "border-slate-800" : "border-slate-100"} px-6 py-3`}>
                        <button onClick={() => navigate("/history")} className="text-xs text-blue-500 hover:text-blue-400 font-medium flex items-center gap-1 transition-colors" data-testid="view-all-history-link">View all history <ChevronRight className="w-3 h-3" /></button>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            </motion.div>
          )}
        </div>
      </section>

      {/* How It Works */}
      <section id="how-it-works" className={`py-24 ${darkMode ? "bg-[#0e1221] border-[#1e2436]" : "bg-white border-slate-100"} border-t transition-colors`} data-testid="how-it-works-section">
        <div className="max-w-7xl mx-auto px-6 sm:px-8 lg:px-12">
          <div className="text-center mb-16">
            <h2 className={`text-3xl sm:text-4xl tracking-tight font-serif ${textPrimary} mb-4 transition-colors`} data-testid="how-it-works-title">How It Works</h2>
            <p className={`${textSecondary} transition-colors`}>Our AI-powered detection process in three simple steps</p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-12">
            {[
              { icon: Upload, title: "1. Upload Content", desc: "Submit text, images, or videos in any supported language.", color: "text-blue-500", bg: darkMode ? "bg-blue-500/10" : "bg-blue-50" },
              { icon: Zap, title: "2. AI Analysis", desc: "Our GPT-5.2 models analyze for manipulation and inconsistencies.", color: "text-purple-500", bg: darkMode ? "bg-purple-500/10" : "bg-purple-50" },
              { icon: Target, title: "3. Get Results", desc: "Receive multilingual results with confidence scores and explanations.", color: "text-emerald-500", bg: darkMode ? "bg-emerald-500/10" : "bg-emerald-50" },
            ].map((step, i) => (
              <motion.div key={i} initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: i * 0.15 }} className="text-center" data-testid={`how-it-works-step-${i + 1}`}>
                <div className={`inline-flex items-center justify-center w-16 h-16 ${step.bg} ${step.color} rounded-2xl mb-5`}><step.icon className="w-7 h-7" /></div>
                <h3 className={`text-lg font-serif ${textPrimary} mb-2 transition-colors`}>{step.title}</h3>
                <p className={`${textSecondary} text-sm leading-relaxed transition-colors`}>{step.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Why Trust Us */}
      <section className={`py-24 ${darkMode ? "bg-[#0c0f1a] border-[#1e2436]" : "bg-slate-50/50 border-slate-100"} border-t transition-colors`}>
        <div className="max-w-7xl mx-auto px-6 sm:px-8 lg:px-12 text-center">
          <h2 className={`text-3xl sm:text-4xl tracking-tight font-serif ${textPrimary} mb-6 transition-colors`} data-testid="why-trust-title">Why Trust TruthLens AI?</h2>
          <p className={`${textSecondary} max-w-2xl mx-auto mb-14 transition-colors`}>State-of-the-art AI models providing accurate, reliable fake news detection across multiple languages.</p>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {[
              { icon: Shield, title: "Advanced AI Models", desc: "Powered by GPT-5.2 and cutting-edge computer vision technology." },
              { icon: Languages, title: "Multilingual Support", desc: "Analyze content in English, Hindi, Marathi, Tamil, and Hinglish." },
              { icon: Target, title: "Multi-Format Support", desc: "Analyze text, images, and videos with batch processing." },
            ].map((card, i) => (
              <motion.div key={i} initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: i * 0.1 }} className={`${cardBg} border shadow-sm rounded-2xl p-8 hover:shadow-lg transition-all`}>
                <card.icon className="w-10 h-10 text-blue-500 mx-auto mb-4" />
                <h3 className={`text-lg font-serif ${textPrimary} mb-2 transition-colors`}>{card.title}</h3>
                <p className={`${textSecondary} text-sm transition-colors`}>{card.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className={`py-16 ${darkMode ? "bg-[#0a0d17] border-[#1e2436]" : "bg-white border-slate-100"} border-t transition-colors`} data-testid="footer">
        <div className="max-w-7xl mx-auto px-6 sm:px-8 lg:px-12 text-center">
          <div className="flex items-center justify-center gap-3 mb-5">
            <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-blue-500/20">
              <Shield className="w-4 h-4 text-white" />
            </div>
            <h3 className={`text-xl font-serif font-bold ${textPrimary} transition-colors`}>TruthLens AI</h3>
          </div>
          <p className={`${textSecondary} text-sm mb-6 transition-colors`}>Empowering truth in the digital age with AI-powered verification.</p>
          <div className={`flex justify-center gap-8 text-sm ${textSecondary}`}>
            <a href="#" className="hover:text-blue-500 transition-colors">Privacy Policy</a>
            <a href="#" className="hover:text-blue-500 transition-colors">Terms of Service</a>
            <a href="#" className="hover:text-blue-500 transition-colors">Contact</a>
          </div>
          <p className={`${textMuted} text-xs mt-6`}>&copy; 2026 TruthLens AI. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
};

export default HomePage;
