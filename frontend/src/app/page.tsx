"use client";

import React, { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { 
  ArrowRight, BookOpen, Compass, ShieldCheck, MessageSquare, CheckCircle, 
  RotateCw, Settings, AlertCircle, Brain, Globe, FileText, ChevronDown, 
  UploadCloud, Info, X 
} from "lucide-react";
import { 
  createCourse, getJobStatus, getCourses, JobStatusResponse, CourseListItem,
  uploadDocument, generateCourseFromDocument, DocumentUploadResponse
} from "@/lib/api";
import { useRouter } from "next/navigation";
import SettingsModal from "@/components/SettingsModal";
import { translations, SupportedLanguage, formatCourseLevel } from "@/lib/i18n";

const SUGGESTIONS = [
  "Como Rimar Bem",
  "Engenharia Civil",
  "Python & Sistemas Distribuídos",
  "Design Editorial & Tipografia",
  "Biologia Molecular",
  "Matemática Financeira & Risco",
  "Arquitetura de Agentes de IA",
  "Neurociência & Aprendizagem"
];

export default function HomePage() {
  const router = useRouter();
  const [suggestionIdx, setSuggestionIdx] = useState(0);
  const [subject, setSubject] = useState("");
  const [showLevelModal, setShowLevelModal] = useState(false);
  const [showSettingsModal, setShowSettingsModal] = useState(false);
  const [uiLang, setUiLang] = useState<SupportedLanguage>("pt-BR");
  const [courseLang, setCourseLang] = useState<SupportedLanguage>("pt-BR");

  // Carrega idioma salvo no localStorage
  useEffect(() => {
    if (typeof window !== "undefined") {
      const savedLang = localStorage.getItem("trivium_ui_lang") as SupportedLanguage | null;
      if (savedLang === "pt-BR" || savedLang === "en-US") {
        setUiLang(savedLang);
        setCourseLang(savedLang);
      }
    }
  }, []);

  const handleSetLanguage = (lang: SupportedLanguage) => {
    setUiLang(lang);
    setCourseLang(lang);
    if (typeof window !== "undefined") {
      localStorage.setItem("trivium_ui_lang", lang);
    }
  };

  const t = translations[uiLang];

  // Modo de Criação: "web" (Pesquisa Web) ou "document" (Do seu arquivo)
  const [creationMode, setCreationMode] = useState<"web" | "document">("web");
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [modeTooltipOpen, setModeTooltipOpen] = useState(false);

  // Estados do Modo Arquivo Local
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isAnalyzingDoc, setIsAnalyzingDoc] = useState(false);
  const [analyzedDoc, setAnalyzedDoc] = useState<DocumentUploadResponse | null>(null);
  const [docSubject, setDocSubject] = useState("");
  const [uploadError, setUploadError] = useState<string | null>(null);

  // Lista de Cursos Existentes
  const [existingCourses, setExistingCourses] = useState<CourseListItem[]>([]);
  const [loadingCourses, setLoadingCourses] = useState<boolean>(true);

  // Job de Esteira
  const [jobId, setJobId] = useState<string | null>(null);
  const [jobStatus, setJobStatus] = useState<JobStatusResponse | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Carrega cursos salvos no banco de dados com auto-retry resiliente
  const fetchCourses = () => {
    setLoadingCourses(true);
    getCourses()
      .then((data) => {
        setExistingCourses(data.filter((c) => c.total_lessons > 0));
        setLoadingCourses(false);
      })
      .catch((err) => {
        console.error("Erro ao carregar cursos existentes:", err);
        setLoadingCourses(false);
      });
  };

  useEffect(() => {
    fetchCourses();
    const timer1 = setTimeout(fetchCourses, 1500);
    const timer2 = setTimeout(fetchCourses, 3500);
    return () => {
      clearTimeout(timer1);
      clearTimeout(timer2);
    };
  }, []);

  // Carrossel de texto dinâmico animado
  useEffect(() => {
    const timer = setInterval(() => {
      setSuggestionIdx((prev) => (prev + 1) % SUGGESTIONS.length);
    }, 2800);
    return () => clearInterval(timer);
  }, []);

  // Polling da esteira assíncrona
  useEffect(() => {
    if (!jobId) return;

    const interval = setInterval(async () => {
      try {
        const data = await getJobStatus(jobId);
        setJobStatus(data);
        if (data.status === "completed" && data.course_id) {
          clearInterval(interval);
          setTimeout(() => {
            router.push(`/course/${data.course_id}`);
          }, 1200);
        } else if (data.status === "failed") {
          clearInterval(interval);
        }
      } catch (err) {
        console.error("Erro no polling:", err);
      }
    }, 2500);

    return () => clearInterval(interval);
  }, [jobId, router]);

  const handleStartCourse = async (level: string) => {
    if (!subject.trim()) return;
    setShowLevelModal(false);
    setIsSubmitting(true);

    try {
      const res = await createCourse(subject.trim(), level, courseLang);
      setJobId(res.job_id);
    } catch {
      alert(t.alert_pipeline_trigger_error);
      setIsSubmitting(false);
    }
  };

  const handleFileSelect = async (file: File) => {
    const ext = file.name.split(".").pop()?.toLowerCase();
    if (ext !== "pdf" && ext !== "epub") {
      setUploadError(t.alert_file_format_error);
      return;
    }

    setUploadError(null);
    setIsAnalyzingDoc(true);
    setAnalyzedDoc(null);

    try {
      const result = await uploadDocument(file);
      setAnalyzedDoc(result);
      setDocSubject(result.clean_title);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : t.alert_file_process_error;
      setUploadError(msg);
    } finally {
      setIsAnalyzingDoc(false);
    }
  };

  const handleStartDocumentCourse = async () => {
    if (!analyzedDoc || !docSubject.trim()) return;
    setIsSubmitting(true);

    try {
      const res = await generateCourseFromDocument(
        analyzedDoc.doc_id,
        docSubject.trim(),
        analyzedDoc.inferred_level,
        courseLang
      );
      setJobId(res.job_id);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : t.alert_doc_generate_error;
      alert(msg);
      setIsSubmitting(false);
    }
  };

  return (
    <main className="min-h-screen flex flex-col bg-[#0b0b0b] text-[#f4f4f5] selection:bg-[#ffe500] selection:text-black">
      {/* Header Minimalista */}
      <header className="border-b border-[#1f1f23] px-8 py-5 flex justify-between items-center">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 rounded-xl bg-[#141416] border border-[#ffe500]/40 flex items-center justify-center shadow-lg shadow-[#ffe500]/5 group hover:border-[#ffe500] transition-all overflow-hidden p-1">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src="/trivium-logo.png" alt="Trivium" width={32} height={32} style={{ maxWidth: 32, maxHeight: 32 }} className="w-full h-full object-contain" />
          </div>
          <div>
            <h2 className="text-sm font-black tracking-wider text-white">TRIVIUM</h2>
            <p className="text-[10px] text-neutral-500 font-medium">Autonomous Learning System</p>
          </div>
        </div>
        <div className="flex items-center space-x-3 text-xs font-semibold tracking-wider text-neutral-400">
          {/* Seletor de Idioma da Interface com Bandeiras 2D */}
          <div className="flex items-center bg-[#18181b] border border-[#27272a] rounded-xl p-1 space-x-1">
            <button
              type="button"
              onClick={() => handleSetLanguage("pt-BR")}
              className={`flex items-center justify-center p-1.5 rounded-lg transition-all ${
                uiLang === "pt-BR"
                  ? "bg-[#27272a] ring-1 ring-[#ffe500] shadow-sm"
                  : "opacity-40 hover:opacity-100 hover:bg-[#27272a]/50"
              }`}
              title="Português (Brasil)"
              aria-label="Português (Brasil)"
            >
              <svg className="w-5 h-3.5 rounded-sm shadow-sm" viewBox="0 0 720 504">
                <rect width="720" height="504" fill="#009b3a" />
                <polygon points="360,42 678,252 360,462 42,252" fill="#fedf00" />
                <circle cx="360" cy="252" r="126" fill="#002776" />
                <path d="M 234 252 A 126 126 0 0 0 486 252 A 126 110 0 0 1 234 252 Z" fill="#ffffff" />
              </svg>
            </button>
            <button
              type="button"
              onClick={() => handleSetLanguage("en-US")}
              className={`flex items-center justify-center p-1.5 rounded-lg transition-all ${
                uiLang === "en-US"
                  ? "bg-[#27272a] ring-1 ring-[#ffe500] shadow-sm"
                  : "opacity-40 hover:opacity-100 hover:bg-[#27272a]/50"
              }`}
              title="English (United States)"
              aria-label="English (United States)"
            >
              <svg className="w-5 h-3.5 rounded-sm shadow-sm" viewBox="0 0 1900 1000">
                <rect width="1900" height="1000" fill="#b22234" />
                <path d="M0,76.92h1900M0,230.77h1900M0,384.62h1900M0,538.46h1900M0,692.31h1900M0,846.15h1900" stroke="#ffffff" strokeWidth="76.92" />
                <rect width="760" height="538.46" fill="#3c3b6e" />
                <g fill="#ffffff">
                  <g id="us-star">
                    <polygon points="0,-18 5.56,-5.56 18,-5.56 8.35,3.44 11.12,16.5 0,8.8 -11.12,16.5 -8.35,3.44 -18,-5.56 -5.56,-5.56" />
                  </g>
                  {[
                    [63.3, 44.8], [189.9, 44.8], [316.5, 44.8], [443.1, 44.8], [569.7, 44.8], [696.3, 44.8],
                    [63.3, 152.5], [189.9, 152.5], [316.5, 152.5], [443.1, 152.5], [569.7, 152.5], [696.3, 152.5],
                    [63.3, 260.2], [189.9, 260.2], [316.5, 260.2], [443.1, 260.2], [569.7, 260.2], [696.3, 260.2],
                    [63.3, 367.9], [189.9, 367.9], [316.5, 367.9], [443.1, 367.9], [569.7, 367.9], [696.3, 367.9],
                    [63.3, 475.6], [189.9, 475.6], [316.5, 475.6], [443.1, 475.6], [569.7, 475.6], [696.3, 475.6],
                  ].map(([cx, cy], i) => (
                    <use key={`s6-${i}`} href="#us-star" x={cx} y={cy} />
                  ))}
                  {[
                    [126.6, 98.6], [253.2, 98.6], [379.8, 98.6], [506.4, 98.6], [633.0, 98.6],
                    [126.6, 206.3], [253.2, 206.3], [379.8, 206.3], [506.4, 206.3], [633.0, 206.3],
                    [126.6, 314.0], [253.2, 314.0], [379.8, 314.0], [506.4, 314.0], [633.0, 314.0],
                    [126.6, 421.7], [253.2, 421.7], [379.8, 421.7], [506.4, 421.7], [633.0, 421.7],
                  ].map(([cx, cy], i) => (
                    <use key={`s5-${i}`} href="#us-star" x={cx} y={cy} />
                  ))}
                </g>
              </svg>
            </button>
          </div>

          <button
            onClick={() => setShowSettingsModal(true)}
            className="flex items-center space-x-2 bg-[#18181b] hover:bg-[#27272a] border border-[#27272a] hover:border-[#ffe500]/50 text-neutral-300 hover:text-white px-3 py-1.5 rounded-xl transition-all cursor-pointer"
            title={t.settings}
          >
            <Settings className="w-3.5 h-3.5 text-[#ffe500]" />
            <span>{t.settings}</span>
          </button>
        </div>
      </header>

      {/* Conteúdo Principal */}
      <div className="flex-1 max-w-5xl mx-auto w-full px-6 flex flex-col justify-center py-14">
        {/* Título & Pergunta com Animação */}
        <div className="space-y-3 text-center sm:text-left mb-8">
          <h1 className="text-4xl sm:text-6xl font-black tracking-tight text-white leading-tight">
            {t.hero_title_1} <br className="hidden sm:block" />
            {t.hero_title_2}
          </h1>

          {/* Linha animada com matérias rodando */}
          <div className="h-10 flex items-center justify-center sm:justify-start overflow-hidden">
            <span className="text-neutral-500 font-medium text-lg mr-2">{t.example_label}</span>
            <AnimatePresence mode="wait">
              <motion.span
                key={t.suggestions[suggestionIdx % t.suggestions.length]}
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -15 }}
                transition={{ duration: 0.35, ease: "easeOut" }}
                className="text-lg sm:text-xl font-bold text-[#ffe500] hover:text-[#ffd000] cursor-pointer transition-colors"
                onClick={() => setSubject(t.suggestions[suggestionIdx % t.suggestions.length])}
              >
                {t.suggestions[suggestionIdx % t.suggestions.length]}
              </motion.span>
            </AnimatePresence>
          </div>
        </div>

        {/* ========================================================================= */}
        {/* SELETOR DROPDOWN DE MODO: PESQUISA WEB VS DO SEU ARQUIVO */}
        {/* ========================================================================= */}
        <div className="flex items-center justify-between mb-3 relative z-30">
          <div className="relative">
            <div className="flex items-center space-x-2">
              <button
                type="button"
                onClick={() => setDropdownOpen((prev) => !prev)}
                className="flex items-center space-x-2.5 bg-[#18181b] hover:bg-[#222226] border border-[#2e2e33] hover:border-[#ffe500]/60 text-white px-3.5 py-2 rounded-xl text-xs font-bold transition-all shadow-md cursor-pointer"
              >
                {creationMode === "web" ? (
                  <Globe className="w-4 h-4 text-neutral-300" />
                ) : (
                  <FileText className="w-4 h-4 text-neutral-300" />
                )}
                <span>{creationMode === "web" ? t.mode_web_search : t.mode_from_document}</span>
                <ChevronDown className={`w-3.5 h-3.5 text-neutral-400 transition-transform ${dropdownOpen ? "rotate-180" : ""}`} />
              </button>

              {/* Botão de Info com Tooltip estilo Netflix */}
              <div className="relative">
                <button
                  type="button"
                  onMouseEnter={() => setModeTooltipOpen(true)}
                  onMouseLeave={() => setModeTooltipOpen(false)}
                  onClick={() => setModeTooltipOpen((prev) => !prev)}
                  className="w-6 h-6 rounded-full bg-[#18181b] border border-[#27272a] hover:border-[#ffe500]/60 flex items-center justify-center text-neutral-400 hover:text-white text-xs transition-all cursor-pointer"
                  title={t.mode_info_title}
                >
                  <Info className="w-3.5 h-3.5" />
                </button>

                <AnimatePresence>
                  {modeTooltipOpen && (
                    <motion.div
                      initial={{ opacity: 0, y: 5 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: 5 }}
                      className="absolute left-0 top-full mt-2 w-72 p-3 bg-[#18181b] border border-[#333338] rounded-xl text-xs text-neutral-200 shadow-2xl z-50 leading-relaxed font-normal pointer-events-none"
                    >
                      {creationMode === "web"
                        ? t.mode_info_tooltip_web
                        : t.mode_info_tooltip_doc}
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            </div>

            {/* Menu Popover do Dropdown */}
            <AnimatePresence>
              {dropdownOpen && (
                <motion.div
                  initial={{ opacity: 0, y: -5, scale: 0.98 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  exit={{ opacity: 0, y: -5, scale: 0.98 }}
                  transition={{ duration: 0.15 }}
                  className="absolute left-0 top-full mt-2 w-52 bg-[#141416] border border-[#27272a] rounded-xl shadow-2xl z-50 p-1.5 space-y-1"
                >
                  <button
                    type="button"
                    onClick={() => {
                      setCreationMode("web");
                      setDropdownOpen(false);
                    }}
                    className={`w-full flex items-center space-x-2.5 px-3 py-2 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                      creationMode === "web"
                        ? "bg-[#27272a] text-[#ffe500]"
                        : "text-neutral-300 hover:bg-[#1c1c20] hover:text-white"
                    }`}
                  >
                    <Globe className="w-4 h-4 text-neutral-300" />
                    <span>{t.mode_web_search}</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => {
                      setCreationMode("document");
                      setDropdownOpen(false);
                    }}
                    className={`w-full flex items-center space-x-2.5 px-3 py-2 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                      creationMode === "document"
                        ? "bg-[#27272a] text-[#ffe500]"
                        : "text-neutral-300 hover:bg-[#1c1c20] hover:text-white"
                    }`}
                  >
                    <FileText className="w-4 h-4 text-neutral-300" />
                    <span>{t.mode_from_document}</span>
                  </button>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>

        {/* ========================================================================= */}
        {/* ÁREA DINÂMICA DE ENTRADA (MODO WEB OU MODO ARQUIVO) */}
        {/* ========================================================================= */}
        <div className="relative mb-12">
          {creationMode === "web" ? (
            <div className="relative flex flex-col sm:flex-row items-stretch sm:items-center bg-[#141416] border-2 border-[#27272a] focus-within:border-[#ffe500] rounded-2xl p-2 transition-all shadow-2xl">
              <input
                type="text"
                value={subject}
                onChange={(e) => setSubject(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && subject.trim()) setShowLevelModal(true);
                }}
                placeholder={t.input_placeholder}
                className="flex-1 bg-transparent px-5 py-4 text-lg text-white placeholder:text-neutral-500 outline-none font-medium"
              />
              <button
                onClick={() => {
                  if (subject.trim()) setShowLevelModal(true);
                }}
                disabled={!subject.trim() || isSubmitting}
                className="mt-2 sm:mt-0 bg-[#ffe500] hover:bg-[#fff000] text-black font-extrabold px-8 py-4 rounded-xl flex items-center justify-center space-x-2 transition-all disabled:opacity-40 disabled:cursor-not-allowed shadow-lg shadow-[#ffe500]/10 cursor-pointer"
              >
                <span>{t.btn_continue}</span>
                <ArrowRight className="w-5 h-5" />
              </button>
            </div>
          ) : (
            <div className="space-y-4">
              <input
                type="file"
                ref={fileInputRef}
                className="hidden"
                accept=".pdf,.epub"
                onChange={(e) => {
                  if (e.target.files?.[0]) handleFileSelect(e.target.files[0]);
                }}
              />

              {!analyzedDoc ? (
                <div
                  onClick={() => !isAnalyzingDoc && fileInputRef.current?.click()}
                  onDragOver={(e) => {
                    e.preventDefault();
                    if (!isAnalyzingDoc) setIsDragging(true);
                  }}
                  onDragLeave={() => setIsDragging(false)}
                  onDrop={(e) => {
                    e.preventDefault();
                    setIsDragging(false);
                    if (!isAnalyzingDoc && e.dataTransfer.files?.[0]) {
                      handleFileSelect(e.dataTransfer.files[0]);
                    }
                  }}
                  className={`rounded-2xl border-2 border-dashed p-8 sm:p-10 text-center transition-all bg-[#141416] cursor-pointer ${
                    isDragging
                      ? "border-[#ffe500] bg-[#1a1a1e]"
                      : "border-[#27272a] hover:border-[#ffe500]/70 hover:bg-[#18181c]"
                  }`}
                >
                  {isAnalyzingDoc ? (
                    <div className="flex flex-col items-center space-y-3 py-4">
                      <div className="w-8 h-8 border-2 border-[#ffe500] border-t-transparent rounded-full animate-spin" />
                      <p className="text-base font-bold text-white">{t.doc_upload_reading}</p>
                      <p className="text-xs text-neutral-400">{t.doc_upload_sanitizing}</p>
                    </div>
                  ) : (
                    <div className="flex flex-col items-center space-y-3 py-2">
                      <div className="w-12 h-12 rounded-2xl bg-[#1c1c20] border border-[#2e2e33] flex items-center justify-center text-neutral-300">
                        <UploadCloud className="w-6 h-6 text-[#ffe500]" />
                      </div>
                      <div>
                        <p className="text-base font-bold text-white">
                          {t.doc_drag_here} <span className="text-[#ffe500] underline">{t.doc_click_browse}</span>
                        </p>
                        <p className="text-xs text-neutral-500 mt-1.5">
                          {t.doc_supported_formats}
                        </p>
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                /* Card de Diagnóstico Cognitivo Pré-Geração */
                <div className="bg-[#141416] border-2 border-[#ffe500]/50 rounded-2xl p-6 sm:p-8 shadow-2xl space-y-5">
                  <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3">
                    <div className="space-y-1.5">
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="text-[10px] font-black uppercase tracking-wider px-2.5 py-1 rounded bg-[#ffe500] text-black">
                          {t.doc_inferred_level} {formatCourseLevel(analyzedDoc.inferred_level, uiLang).toUpperCase()}
                        </span>
                        <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-[#27272a] text-neutral-300 uppercase">
                          {analyzedDoc.format}
                        </span>
                        <span className="text-xs text-neutral-400">
                          {analyzedDoc.total_pages} {t.doc_pages} • {analyzedDoc.total_chapters} {t.doc_chapters_indexed}
                        </span>
                      </div>
                      <p className="text-xs text-neutral-400">
                        {analyzedDoc.author ? `${t.doc_author} ${analyzedDoc.author}` : t.doc_editorial_title}
                      </p>
                    </div>
                    <button
                      type="button"
                      onClick={() => {
                        setAnalyzedDoc(null);
                        fileInputRef.current?.click();
                      }}
                      className="self-start text-xs text-neutral-400 hover:text-white bg-[#1e1e24] hover:bg-[#27272a] px-3 py-1.5 rounded-xl border border-[#333338] transition-all cursor-pointer"
                    >
                      {t.doc_change_file}
                    </button>
                  </div>

                  {/* Campo de Título Higienizado (Editável pelo Usuário) */}
                  <div className="space-y-1.5">
                    <label className="text-xs font-bold text-neutral-400 block">
                      {t.doc_field_course_title}
                    </label>
                    <input
                      type="text"
                      value={docSubject}
                      onChange={(e) => setDocSubject(e.target.value)}
                      className="w-full bg-[#18181b] border border-[#27272a] focus:border-[#ffe500] rounded-xl px-4 py-3 text-base font-bold text-white outline-none"
                    />
                  </div>

                  {/* Frase Transparente de Diagnóstico Cognitivo Estilo Netflix */}
                  <div className="p-4 bg-[#18181b] border border-[#27272a] rounded-xl space-y-2.5">
                    <p className="text-xs sm:text-sm text-neutral-200 leading-relaxed font-medium">
                      💡 {analyzedDoc.complexity_reason}
                    </p>
                    <p className="text-xs text-neutral-400">
                      {t.doc_course_journey_label} <strong>{formatCourseLevel(analyzedDoc.inferred_level, uiLang)}</strong> (
                      {analyzedDoc.inferred_level === "Avançado" || analyzedDoc.inferred_level === "Advanced"
                        ? t.doc_modules_lessons_pattern.replace("{modules}", "12").replace("{lessons}", "60")
                        : analyzedDoc.inferred_level === "Intermediário" || analyzedDoc.inferred_level === "Intermediate"
                        ? t.doc_modules_lessons_pattern.replace("{modules}", "8").replace("{lessons}", "32")
                        : t.doc_modules_lessons_pattern.replace("{modules}", "4").replace("{lessons}", "12")}
                      ) {t.doc_course_journey_suffix}
                    </p>
                    {analyzedDoc.reader_prerequisites && analyzedDoc.reader_prerequisites.length > 0 && (
                      <div className="pt-2 border-t border-[#27272a]">
                        <span className="text-[11px] font-bold text-neutral-400 block mb-1">
                          {t.doc_author_assumptions}
                        </span>
                        <ul className="text-xs text-neutral-300 space-y-1 list-disc list-inside">
                          {analyzedDoc.reader_prerequisites.map((req, i) => (
                            <li key={i}>{req}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>

                  <div className="flex justify-end pt-2">
                    <button
                      type="button"
                      onClick={handleStartDocumentCourse}
                      disabled={isSubmitting || !docSubject.trim()}
                      className="bg-[#ffe500] hover:bg-[#fff000] text-black font-black px-8 py-4 rounded-xl flex items-center space-x-2 transition-all shadow-lg shadow-[#ffe500]/10 disabled:opacity-50 cursor-pointer"
                    >
                      <span>{t.doc_btn_generate}</span>
                      <ArrowRight className="w-5 h-5" />
                    </button>
                  </div>
                </div>
              )}

              {uploadError && (
                <div className="p-4 bg-red-950/40 border border-red-800/60 rounded-xl text-xs text-red-300 flex items-center justify-between">
                  <span>{uploadError}</span>
                  <button onClick={() => setUploadError(null)} className="text-red-400 hover:text-white ml-3">
                    <X className="w-4 h-4" />
                  </button>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Badges de Diferenciais do Trivium */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-6 border-t border-[#1f1f23]">
          <div className="bg-[#141416]/60 border border-[#27272a] p-4 rounded-xl flex items-start space-x-3">
            <Compass className="w-5 h-5 text-[#ffe500] shrink-0 mt-0.5" />
            <div>
              <h4 className="text-sm font-bold text-white">{t.diff1_title}</h4>
              <p className="text-xs text-neutral-400 mt-1 leading-relaxed">
                {t.diff1_desc}
              </p>
            </div>
          </div>
          <div className="bg-[#141416]/60 border border-[#27272a] p-4 rounded-xl flex items-start space-x-3">
            <ShieldCheck className="w-5 h-5 text-[#ffe500] shrink-0 mt-0.5" />
            <div>
              <h4 className="text-sm font-bold text-white">{t.diff2_title}</h4>
              <p className="text-xs text-neutral-400 mt-1 leading-relaxed">
                {t.diff2_desc}
              </p>
            </div>
          </div>
          <div className="bg-[#141416]/60 border border-[#27272a] p-4 rounded-xl flex items-start space-x-3">
            <MessageSquare className="w-5 h-5 text-[#ffe500] shrink-0 mt-0.5" />
            <div>
              <h4 className="text-sm font-bold text-white">{t.diff3_title}</h4>
              <p className="text-xs text-neutral-400 mt-1 leading-relaxed">
                {t.diff3_desc}
              </p>
            </div>
          </div>
        </div>

        {/* Seção da Biblioteca de Cursos Salvos */}
        <div className="mt-14 pt-10 border-t border-[#1f1f23]">
          <div className="flex items-center justify-between mb-6">
            <div>
              <span className="text-xs font-bold uppercase tracking-widest text-[#ffe500]">{t.library_badge}</span>
              <h3 className="text-2xl font-black text-white mt-0.5">{t.library_title}</h3>
            </div>
            <div className="flex items-center space-x-3">
              <button
                id="refresh-courses-btn"
                onClick={fetchCourses}
                className="flex items-center space-x-1.5 text-xs font-semibold text-neutral-400 hover:text-white bg-[#141416] hover:bg-[#1f1f23] border border-[#27272a] px-3 py-1.5 rounded-xl transition-all cursor-pointer"
                title="Refresh library"
              >
                <RotateCw className={`w-3 h-3 text-[#ffe500] ${loadingCourses ? "animate-spin" : ""}`} />
                <span>{t.btn_refresh}</span>
              </button>
              <span className="text-xs font-semibold text-neutral-500">
                {existingCourses.length} {existingCourses.length === 1 ? t.track_single : t.tracks_plural}
              </span>
            </div>
          </div>

          {loadingCourses && existingCourses.length === 0 ? (
            <div className="flex items-center space-x-3 text-neutral-400 text-sm py-8">
              <div className="w-4 h-4 border-2 border-[#ffe500] border-t-transparent rounded-full animate-spin" />
              <span>{t.loading_courses}</span>
            </div>
          ) : existingCourses.length === 0 ? (
            <div className="bg-[#141416]/40 border border-[#27272a] rounded-2xl p-8 text-center text-neutral-400 space-y-3">
              <BookOpen className="w-8 h-8 text-neutral-600 mx-auto" />
              <p className="text-sm font-medium">{t.no_courses_title}</p>
              <button
                onClick={fetchCourses}
                className="inline-flex items-center space-x-2 text-xs font-bold text-[#ffe500] hover:underline cursor-pointer bg-[#1e1e24] px-4 py-2 rounded-xl border border-[#333338]"
              >
                <RotateCw className="w-3.5 h-3.5" />
                <span>{t.btn_reload_library}</span>
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
              {existingCourses.map((c) => (
                <div
                  key={c.id}
                  onClick={() => router.push(`/course/${c.id}`)}
                  className="group bg-[#141416] hover:bg-[#19191d] border border-[#27272a] hover:border-[#ffe500] rounded-2xl overflow-hidden cursor-pointer transition-all duration-200 flex flex-col justify-between shadow-lg hover:shadow-[#ffe500]/5"
                >
                  {c.cover_image_url && (
                    <div className="w-full h-32 overflow-hidden bg-black/60 relative border-b border-[#222226]">
                      {/* eslint-disable-next-line @next/next/no-img-element */}
                      <img
                        src={c.cover_image_url}
                        alt={c.subject}
                        className="w-full h-full object-cover object-center group-hover:scale-105 transition-transform duration-300 opacity-90 group-hover:opacity-100"
                        onError={(e) => {
                          (e.target as HTMLElement).parentElement?.classList.add("hidden");
                        }}
                      />
                      <div className="absolute inset-0 bg-gradient-to-t from-[#141416] via-transparent to-transparent opacity-80" />
                    </div>
                  )}

                  <div className="p-5 flex-1 flex flex-col justify-between">
                    <div>
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center space-x-1.5">
                          {/* A badge de nível traduzida dinamicamente conforme o idioma da UI */}
                          <span className="text-[10px] uppercase tracking-wider font-extrabold px-2.5 py-1 rounded-md bg-[#222226] text-neutral-300 group-hover:bg-[#ffe500] group-hover:text-black transition-colors">
                            {formatCourseLevel(c.level, uiLang)}
                          </span>
                          <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-[#18181b] text-neutral-400 border border-[#27272a]">
                            {c.language === "en-US" ? "EN - US" : "PT - BR"}
                          </span>
                        </div>
                        <span className="text-xs font-bold text-[#ffe500]">
                          {c.progress_percent}%
                        </span>
                      </div>

                      <h4 className="text-base font-extrabold text-white group-hover:text-[#ffe500] transition-colors line-clamp-2">
                        {c.subject}
                      </h4>

                      {/* Mini SVG discreto da fonte (Livro ou Web) antes do ponto e módulos */}
                      <div className="flex items-center text-xs text-neutral-400 mt-2.5 space-x-1.5">
                        {c.source_type === "document" ? (
                          <span title="Fonte: Arquivo Local" className="flex items-center">
                            <BookOpen className="w-3.5 h-3.5 text-neutral-400 shrink-0" />
                          </span>
                        ) : (
                          <span title="Fonte: Pesquisa Web" className="flex items-center">
                            <Globe className="w-3.5 h-3.5 text-neutral-400 shrink-0" />
                          </span>
                        )}
                        <span>•</span>
                        <span>
                          {c.total_modules} {t.modules_lessons_label.replace("{lessons}", String(c.total_lessons))}
                        </span>
                      </div>
                    </div>

                    <div className="mt-5 pt-3 border-t border-[#222226] flex items-center justify-between text-xs font-bold text-neutral-400 group-hover:text-white transition-colors">
                      <span>{t.access_course}</span>
                      <ArrowRight className="w-4 h-4 text-[#ffe500] transform group-hover:translate-x-1 transition-transform" />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Modal de Seleção de Nível (Modo Web) */}
      <AnimatePresence>
        {showLevelModal && (
          <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="bg-[#141416] border border-[#27272a] rounded-3xl max-w-lg w-full p-6 sm:p-8 shadow-2xl relative space-y-6"
            >
              <div className="space-y-1">
                <span className="text-xs font-bold uppercase tracking-widest text-[#ffe500]">{t.modal_badge}</span>
                <h3 className="text-2xl font-black text-white">{t.level_modal_title}</h3>
                <p className="text-xs text-neutral-400">
                  {t.topic_label} <strong className="text-white">&apos;{subject}&apos;</strong>
                </p>
              </div>

              {/* Seletor do Idioma do Curso */}
              <div className="p-3 bg-[#18181b] rounded-2xl border border-[#27272a] flex items-center justify-between">
                <span className="text-xs font-bold text-neutral-300 flex items-center space-x-1.5">
                  <Globe className="w-3.5 h-3.5 text-[#ffe500]" />
                  <span>{t.language_label}:</span>
                </span>
                <div className="flex items-center space-x-2">
                  <button
                    type="button"
                    onClick={() => setCourseLang("pt-BR")}
                    className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-xl text-xs font-extrabold transition-all cursor-pointer ${
                      courseLang === "pt-BR"
                        ? "bg-[#ffe500] text-black shadow-md shadow-[#ffe500]/20"
                        : "bg-[#27272a] text-neutral-400 hover:text-white"
                    }`}
                  >
                    <svg viewBox="0 0 20 14" className="w-4 h-3 rounded-[2px] shrink-0" aria-hidden="true">
                      <rect width="20" height="14" fill="#009c3b" />
                      <polygon points="10,1.5 18.5,7 10,12.5 1.5,7" fill="#ffdf00" />
                      <circle cx="10" cy="7" r="3.2" fill="#002776" />
                      <path d="M 7.3,6.8 Q 10,5.8 12.7,7.6" fill="none" stroke="#ffffff" strokeWidth="0.6" strokeLinecap="round" />
                    </svg>
                    <span>PT - BR</span>
                  </button>
                  <button
                    type="button"
                    onClick={() => setCourseLang("en-US")}
                    className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-xl text-xs font-extrabold transition-all cursor-pointer ${
                      courseLang === "en-US"
                        ? "bg-[#ffe500] text-black shadow-md shadow-[#ffe500]/20"
                        : "bg-[#27272a] text-neutral-400 hover:text-white"
                    }`}
                  >
                    <svg viewBox="0 0 1900 1000" className="w-4 h-3 rounded-[2px] shrink-0 shadow-sm" aria-hidden="true">
                      <rect width="1900" height="1000" fill="#b22234" />
                      <path d="M0,76.92h1900M0,230.77h1900M0,384.62h1900M0,538.46h1900M0,692.31h1900M0,846.15h1900" stroke="#ffffff" strokeWidth="76.92" />
                      <rect width="760" height="538.46" fill="#3c3b6e" />
                      <g fill="#ffffff">
                        {[
                          [80, 55], [230, 55], [380, 55], [530, 55], [680, 55],
                          [155, 120], [305, 120], [455, 120], [605, 120],
                          [80, 185], [230, 185], [380, 185], [530, 185], [680, 185],
                          [155, 250], [305, 250], [455, 250], [605, 250],
                          [80, 315], [230, 315], [380, 315], [530, 315], [680, 315],
                          [155, 380], [305, 380], [455, 380], [605, 380],
                          [80, 445], [230, 445], [380, 445], [530, 445], [680, 445],
                        ].map(([cx, cy], i) => (
                          <polygon
                            key={`modal-us-star-${i}`}
                            points={`${cx},${cy - 20} ${cx + 6},${cy - 6} ${cx + 20},${cy - 6} ${cx + 9},${cy + 4} ${cx + 12},${cy + 18} ${cx},${cy + 10} ${cx - 12},${cy + 18} ${cx - 9},${cy + 4} ${cx - 20},${cy - 6} ${cx - 6},${cy - 6}`}
                          />
                        ))}
                      </g>
                    </svg>
                    <span>EN - US</span>
                  </button>
                </div>
              </div>

              <div className="grid grid-cols-1 gap-3">
                {/* Básico */}
                <button
                  onClick={() => handleStartCourse("Básico")}
                  className="group text-left p-5 rounded-2xl border-2 border-[#27272a] hover:border-[#ffe500] bg-[#18181b] hover:bg-[#1f1f23] transition-all flex justify-between items-center cursor-pointer"
                >
                  <div>
                    <div className="flex items-center space-x-2">
                      <span className="font-black text-white group-hover:text-[#ffe500] text-base">{t.level_basic_name}</span>
                      <span className="bg-[#27272a] text-[10px] font-bold px-2 py-0.5 rounded text-neutral-300">{t.level_basic_meta}</span>
                    </div>
                    <p className="text-xs text-neutral-400 mt-1">{t.level_basic_desc}</p>
                  </div>
                  <ArrowRight className="w-5 h-5 text-neutral-500 group-hover:text-[#ffe500] group-hover:translate-x-1 transition-all" />
                </button>

                {/* Intermediário */}
                <button
                  onClick={() => handleStartCourse("Intermediário")}
                  className="group text-left p-5 rounded-2xl border-2 border-[#27272a] hover:border-[#ffe500] bg-[#18181b] hover:bg-[#1f1f23] transition-all flex justify-between items-center cursor-pointer"
                >
                  <div>
                    <div className="flex items-center space-x-2">
                      <span className="font-black text-white group-hover:text-[#ffe500] text-base">{t.level_inter_name}</span>
                      <span className="bg-[#27272a] text-[10px] font-bold px-2 py-0.5 rounded text-neutral-300">{t.level_inter_meta}</span>
                    </div>
                    <p className="text-xs text-neutral-400 mt-1">{t.level_inter_desc}</p>
                  </div>
                  <ArrowRight className="w-5 h-5 text-neutral-500 group-hover:text-[#ffe500] group-hover:translate-x-1 transition-all" />
                </button>

                {/* Avançado */}
                <button
                  onClick={() => handleStartCourse("Avançado")}
                  className="group text-left p-5 rounded-2xl border-2 border-[#27272a] hover:border-[#ffe500] bg-[#18181b] hover:bg-[#1f1f23] transition-all flex justify-between items-center cursor-pointer"
                >
                  <div>
                    <div className="flex items-center space-x-2">
                      <span className="font-black text-white group-hover:text-[#ffe500] text-base">{t.level_adv_name}</span>
                      <span className="bg-[#27272a] text-[10px] font-bold px-2 py-0.5 rounded text-neutral-300">{t.level_adv_meta}</span>
                    </div>
                    <p className="text-xs text-neutral-400 mt-1">{t.level_adv_desc}</p>
                  </div>
                  <ArrowRight className="w-5 h-5 text-neutral-500 group-hover:text-[#ffe500] group-hover:translate-x-1 transition-all" />
                </button>
              </div>

              <div className="flex justify-end">
                <button
                  onClick={() => setShowLevelModal(false)}
                  className="text-xs text-neutral-400 hover:text-white px-4 py-2 cursor-pointer"
                >
                  {uiLang === "en-US" ? "Cancel" : "Cancelar"}
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* Modal de Progresso da Esteira Assíncrona */}
      <AnimatePresence>
        {isSubmitting && (
          <div className="fixed inset-0 bg-black/90 backdrop-blur-md z-50 flex items-center justify-center p-4">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="bg-[#141416] border border-[#27272a] rounded-3xl max-w-md w-full p-8 shadow-2xl text-center space-y-6 relative"
            >
              <div className="w-16 h-16 rounded-2xl bg-[#ffe500]/10 border border-[#ffe500]/30 flex items-center justify-center mx-auto text-[#ffe500]">
                <Brain className="w-8 h-8 animate-pulse" />
              </div>

              <div className="space-y-1">
                <span className="text-xs font-bold uppercase tracking-widest text-[#ffe500]">{t.pipeline_badge}</span>
                <h3 className="text-2xl font-black text-white mt-1">{t.pipeline_title}</h3>
                <p className="text-xs text-neutral-400 mt-1">
                  {t.pipeline_desc}
                </p>
              </div>

              {/* Barra de Progresso */}
              <div className="space-y-2">
                <div className="flex justify-between text-xs font-bold">
                  <span className="text-neutral-400">{t.pipeline_progress}</span>
                  <span className="text-[#ffe500]">{jobStatus?.progress_pct || 5}%</span>
                </div>
                <div className="w-full bg-[#27272a] h-3 rounded-full overflow-hidden">
                  <motion.div
                    className="bg-[#ffe500] h-full rounded-full"
                    initial={{ width: "5%" }}
                    animate={{ width: `${jobStatus?.progress_pct || 5}%` }}
                    transition={{ duration: 0.5 }}
                  />
                </div>
              </div>

              {/* Status Atual do Grafo */}
              <div className="p-4 rounded-xl bg-[#18181b] border border-[#27272a] text-left">
                <span className="text-[10px] font-bold text-neutral-500 uppercase tracking-wider block">{t.pipeline_step_label}</span>
                <p className="text-xs font-semibold text-white mt-1">
                  {jobStatus?.current_step || t.pipeline_initial_step}
                </p>
              </div>

              {jobStatus?.status === "completed" && (
                <div className="flex items-center justify-center space-x-2 text-sm font-bold text-green-400">
                  <CheckCircle className="w-5 h-5" />
                  <span>{t.pipeline_completed}</span>
                </div>
              )}

              {jobStatus?.status === "failed" && (
                <div className="space-y-4 pt-2">
                  <div className="p-4 rounded-xl bg-red-950/40 border border-red-800/60 text-left space-y-2">
                    <div className="flex items-center space-x-2 text-red-400 font-bold text-xs">
                      <AlertCircle className="w-4 h-4 shrink-0" />
                      <span>{t.pipeline_failed}</span>
                    </div>
                    <p className="text-xs text-red-200/90 leading-relaxed break-words font-mono">
                      {jobStatus.error_message || jobStatus.current_step || "Pipeline failure"}
                    </p>
                  </div>
                  <div className="flex items-center justify-end space-x-2">
                    <button
                      type="button"
                      onClick={() => {
                        setIsSubmitting(false);
                        setJobId(null);
                        setJobStatus(null);
                        setShowSettingsModal(true);
                      }}
                      className="bg-[#ffe500] hover:bg-[#fff000] text-black font-extrabold text-xs px-4 py-2.5 rounded-xl transition-all cursor-pointer"
                    >
                      {t.settings}
                    </button>
                    <button
                      type="button"
                      onClick={() => {
                        setIsSubmitting(false);
                        setJobId(null);
                        setJobStatus(null);
                      }}
                      className="bg-[#27272a] hover:bg-[#3f3f46] text-neutral-300 font-semibold text-xs px-4 py-2.5 rounded-xl transition-all cursor-pointer"
                    >
                      {t.pipeline_close}
                    </button>
                  </div>
                </div>
              )}
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* Modal de Configurações */}
      <SettingsModal
        isOpen={showSettingsModal}
        onClose={() => setShowSettingsModal(false)}
        lang={uiLang}
      />
    </main>
  );
}