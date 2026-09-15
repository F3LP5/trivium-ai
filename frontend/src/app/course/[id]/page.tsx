"use client";

import React, { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { getCourse, deleteCourse, updateCourseAccessMode, CourseSummary } from "@/lib/api";
import { ArrowLeft, Lock, Unlock, Play, CheckCircle2, Compass, Trash2, AlertTriangle, X, Settings, ExternalLink, ShieldCheck, ChevronDown, ChevronUp } from "lucide-react";
import Link from "next/link";
import SettingsModal from "@/components/SettingsModal";
import { translations, SupportedLanguage, formatCourseLevel } from "@/lib/i18n";

export default function CoursePage() {
  const params = useParams();
  const router = useRouter();
  const courseId = Number(params?.id);

  const [course, setCourse] = useState<CourseSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [showSettingsModal, setShowSettingsModal] = useState(false);
  const [showSourcesDossier, setShowSourcesDossier] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  // Modo de acesso: "open" (desbloqueado padrão) ou "guided" (trilha sequencial com bloqueio)
  const [accessMode, setAccessMode] = useState<"open" | "guided">("open");
  const [showGuidedWarningModal, setShowGuidedWarningModal] = useState(false);

  const handleDeleteCourse = async () => {
    if (!courseId) return;
    setIsDeleting(true);
    setDeleteError(null);
    try {
      await deleteCourse(courseId);
      router.push("/");
    } catch (err: unknown) {
      console.error(err);
      const msg = err instanceof Error ? err.message : "Erro ao excluir o curso";
      setDeleteError(msg);
      setIsDeleting(false);
    }
  };

  const handleSwitchToOpen = async () => {
    if (accessMode === "open") return;
    setAccessMode("open");
    try {
      await updateCourseAccessMode(courseId, "open");
    } catch (err) {
      console.error("Erro ao salvar modo livre:", err);
    }
  };

  const handleSelectGuided = () => {
    if (accessMode === "guided") return;
    // O aviso em pop-up só deve aparecer no máximo 1 vez por curso gerado
    const storageKey = `trivium_guided_warning_shown_${courseId}`;
    const alreadyShown = typeof window !== "undefined" && localStorage.getItem(storageKey) === "true";

    if (!alreadyShown) {
      setShowGuidedWarningModal(true);
    } else {
      confirmSwitchToGuided();
    }
  };

  const confirmSwitchToGuided = async () => {
    setShowGuidedWarningModal(false);
    if (typeof window !== "undefined") {
      localStorage.setItem(`trivium_guided_warning_shown_${courseId}`, "true");
    }
    setAccessMode("guided");
    try {
      await updateCourseAccessMode(courseId, "guided");
    } catch (err) {
      console.error("Erro ao salvar modo guiado:", err);
    }
  };

  const cancelSwitchToGuided = () => {
    setShowGuidedWarningModal(false);
  };

  useEffect(() => {
    if (!courseId) return;
    getCourse(courseId)
      .then((data) => {
        setCourse(data);
        setAccessMode((data.access_mode as "open" | "guided") || "open");
        setLoading(false);
      })
      .catch((err) => {
        console.error(err);
        setLoading(false);
      });
  }, [courseId]);

  const fallbackLang: SupportedLanguage = typeof window !== "undefined" && localStorage.getItem("trivium_ui_lang") === "en-US" ? "en-US" : "pt-BR";
  const lang: SupportedLanguage = course?.language === "en-US" ? "en-US" : fallbackLang;
  const t = translations[lang];

  if (loading) {
    return (
      <div className="min-h-screen bg-[#0b0b0b] text-white flex items-center justify-center">
        <div className="flex items-center space-x-3 text-[#ffe500] font-bold">
          <div className="w-5 h-5 border-2 border-[#ffe500] border-t-transparent rounded-full animate-spin" />
          <span>{t.course_loading_matrix}</span>
        </div>
      </div>
    );
  }

  if (!course) {
    return (
      <div className="min-h-screen bg-[#0b0b0b] text-white flex flex-col items-center justify-center p-6">
        <h2 className="text-2xl font-black mb-4">{t.course_not_found}</h2>
        <Link href="/" className="text-[#ffe500] font-bold flex items-center space-x-2">
          <ArrowLeft className="w-4 h-4" />
          <span>{t.course_back_home}</span>
        </Link>
      </div>
    );
  }

  // Ordenação sequencial estrita dos módulos e aulas para controle de acesso
  const sortedModules = [...course.modules].sort((a, b) => a.module_number - b.module_number);
  const orderedLessons = sortedModules.flatMap((m) =>
    [...m.lessons].sort((a, b) => a.lesson_number - b.lesson_number)
  );
  const allLessons = orderedLessons;
  const completedLessons = allLessons.filter((l) => l.status === "completed").length;
  const progressPercent = Math.round((completedLessons / (allLessons.length || 1)) * 100);
  const firstUncompletedIndex = orderedLessons.findIndex((l) => l.status !== "completed");

  return (
    <main className="min-h-screen bg-[#0b0b0b] text-[#f4f4f5] pb-20">
      {/* Header */}
      <header className="border-b border-[#1f1f23] px-8 py-5 flex justify-between items-center bg-[#0e0e10]/80 backdrop-blur-md sticky top-0 z-40">
        <div className="flex items-center space-x-4">
          <Link href="/" className="flex items-center space-x-2.5 group" title={t.course_home_tooltip}>
            <div className="w-8 h-8 rounded-xl bg-[#141416] border border-[#ffe500]/40 flex items-center justify-center group-hover:border-[#ffe500] transition-all overflow-hidden p-1 shadow-sm">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img 
                src="/trivium-logo.png" 
                alt="Trivium Logo" 
                className="w-full h-full object-contain"
              />
            </div>
            <span className="text-xs font-extrabold text-[#ffe500] uppercase tracking-widest group-hover:opacity-90">TRIVIUM</span>
          </Link>
          <span className="text-neutral-700 hidden sm:inline">|</span>
          <Link href="/" className="flex items-center space-x-1.5 text-xs font-bold text-neutral-400 hover:text-white transition-all">
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>{t.course_back_search}</span>
          </Link>
        </div>
        <div className="flex items-center space-x-3">
          <span className="text-xs bg-[#ffe500]/10 text-[#ffe500] border border-[#ffe500]/30 font-black px-2.5 py-0.5 rounded-full">
            {formatCourseLevel(course.level, lang)}
          </span>
          <button
            onClick={() => setShowSettingsModal(true)}
            className="flex items-center space-x-1.5 text-xs font-semibold text-neutral-300 hover:text-white bg-[#18181b] hover:bg-[#27272a] border border-[#27272a] hover:border-[#ffe500]/40 px-3 py-1 rounded-lg transition-all ml-1"
            title={t.course_settings_tooltip}
          >
            <Settings className="w-3.5 h-3.5 text-[#ffe500]" />
            <span className="hidden sm:inline">{t.settings}</span>
          </button>
          <button
            onClick={() => {
              setDeleteError(null);
              setShowDeleteModal(true);
            }}
            className="flex items-center space-x-1.5 text-xs font-semibold text-red-400 hover:text-red-300 bg-red-950/20 hover:bg-red-950/40 border border-red-900/30 hover:border-red-700/50 px-3 py-1 rounded-lg transition-all ml-1"
            title={t.course_delete_tooltip}
          >
            <Trash2 className="w-3.5 h-3.5" />
            <span>{t.course_delete_btn}</span>
          </button>
        </div>
      </header>

      {/* Hero do Curso */}
      <div className="max-w-4xl mx-auto px-6 pt-8 pb-8">
        {course.cover_image_url && (
          <div className="w-full h-56 sm:h-72 rounded-3xl overflow-hidden mb-8 border border-[#27272a] shadow-2xl relative bg-black/50">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={course.cover_image_url.startsWith("http") ? course.cover_image_url : course.cover_image_url}
              alt={`Capa de ${course.subject}`}
              className="w-full h-full object-cover object-center"
              onError={(e) => {
                (e.target as HTMLElement).parentElement?.classList.add("hidden");
              }}
            />
            <div className="absolute inset-0 bg-gradient-to-t from-[#0b0b0b] via-transparent to-transparent opacity-90" />
          </div>
        )}

        <div className="space-y-3">
          <div className="inline-flex items-center space-x-2 text-xs font-bold uppercase tracking-wider text-[#ffe500]">
            <Compass className="w-4 h-4" />
            <span>{t.course_matrix_badge}</span>
          </div>
          <h1 className="text-3xl sm:text-5xl font-black text-white tracking-tight">
            {course.subject}
          </h1>
          <p className="text-sm text-neutral-400">
            {t.course_matrix_desc}
          </p>
        </div>

        {/* Card de Progresso */}
        <div className="mt-8 bg-[#141416] border border-[#27272a] rounded-2xl p-6 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <div>
            <span className="text-xs font-bold text-neutral-400 uppercase tracking-wider">{t.course_progress_label}</span>
            <div className="text-2xl font-black text-white mt-1">
              {t.course_progress_completed
                .replace("{completed}", String(completedLessons))
                .replace("{total}", String(allLessons.length))
                .replace("{percent}", String(progressPercent))}
            </div>
          </div>
          <div className="w-full sm:w-64">
            <div className="w-full bg-[#27272a] h-3 rounded-full overflow-hidden">
              <div
                className="bg-[#ffe500] h-full rounded-full transition-all duration-500"
                style={{ width: `${progressPercent}%` }}
              />
            </div>
          </div>
        </div>

        {/* Auditoria de Fontes e Pesquisa Factual */}
        {course.sources && course.sources.length > 0 && (
          <div className="mt-6 bg-[#141416] border border-[#27272a] rounded-2xl p-5">
            <button
              onClick={() => setShowSourcesDossier(!showSourcesDossier)}
              className="w-full flex items-center justify-between text-left group"
            >
              <div className="flex items-center space-x-3">
                <div className="w-8 h-8 rounded-xl bg-[#ffe500]/10 border border-[#ffe500]/30 flex items-center justify-center text-[#ffe500]">
                  <ShieldCheck className="w-4 h-4" />
                </div>
                <div>
                  <div className="flex items-center space-x-2">
                    <span className="text-xs font-black uppercase tracking-wider text-[#ffe500]">{t.course_sources_badge}</span>
                    <span className="text-[10px] bg-neutral-800 text-neutral-300 px-2 py-0.5 rounded-full font-mono">
                      {t.course_sources_verified.replace("{count}", String(course.sources.length))}
                    </span>
                  </div>
                  <p className="text-xs text-neutral-400 mt-0.5">
                    {t.course_sources_desc}
                  </p>
                </div>
              </div>
              <div className="text-neutral-400 group-hover:text-white transition-colors p-1">
                {showSourcesDossier ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
              </div>
            </button>

            {showSourcesDossier && (
              <div className="mt-4 pt-4 border-t border-[#27272a] space-y-4">
                <div>
                  <h4 className="text-xs font-bold text-neutral-300 uppercase tracking-wider mb-2">{t.course_sources_title}</h4>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                    {course.sources.map((src, idx) => (
                      <a
                        key={idx}
                        href={src.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center justify-between p-3 rounded-xl bg-[#1a1a1e] hover:bg-[#222228] border border-[#27272a] transition-all group"
                      >
                        <div className="truncate pr-2">
                          <span className="text-xs font-bold text-white group-hover:text-[#ffe500] truncate block">
                            {src.title}
                          </span>
                          <span className="text-[10px] text-neutral-500 font-mono">
                            {src.domain}
                          </span>
                        </div>
                        <ExternalLink className="w-3.5 h-3.5 text-neutral-500 group-hover:text-[#ffe500] flex-shrink-0" />
                      </a>
                    ))}
                  </div>
                </div>

                {course.research_dossier && (
                  <div>
                    <h4 className="text-xs font-bold text-neutral-300 uppercase tracking-wider mb-1.5">{t.course_matrix_extracted}</h4>
                    <div className="bg-[#0e0e10] p-4 rounded-xl border border-[#1f1f23] max-h-60 overflow-y-auto font-mono text-[11px] text-neutral-300 whitespace-pre-wrap leading-relaxed">
                      {course.research_dossier}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* Controle de Modo de Acesso (Cadeado Desbloqueado e Cadeado Bloqueado) */}
        <div className="mt-8 mb-4 flex justify-end items-center">
          <div className="inline-flex items-center p-1 rounded-2xl bg-[#141416] border border-[#27272a] shadow-lg">
            {/* Botão Cadeado Desbloqueado (Modo Livre) */}
            <button
              type="button"
              onClick={handleSwitchToOpen}
              className={`flex items-center space-x-2 px-3.5 py-2 rounded-xl text-xs font-black transition-all cursor-pointer ${
                accessMode === "open"
                  ? "bg-[#ffe500] text-black shadow-md shadow-[#ffe500]/15"
                  : "text-neutral-400 hover:text-white hover:bg-[#1f1f23]"
              }`}
              title={t.course_mode_open_tooltip}
            >
              <Unlock className="w-4 h-4" />
              <span>{t.course_mode_open}</span>
            </button>

            {/* Botão Cadeado Bloqueado Fechado (Modo Guiado) */}
            <button
              type="button"
              onClick={handleSelectGuided}
              className={`flex items-center space-x-2 px-3.5 py-2 rounded-xl text-xs font-black transition-all cursor-pointer ${
                accessMode === "guided"
                  ? "bg-[#ffe500] text-black shadow-md shadow-[#ffe500]/15"
                  : "text-neutral-400 hover:text-white hover:bg-[#1f1f23]"
              }`}
              title={t.course_mode_guided_tooltip}
            >
              <Lock className="w-4 h-4" />
              <span>{t.course_mode_guided}</span>
            </button>
          </div>
        </div>

        {/* Lista de Módulos */}
        <div className="space-y-8">
          {sortedModules.map((module) => {
            const moduleLessons = [...module.lessons].sort((a, b) => a.lesson_number - b.lesson_number);
            const isModuleCompleted = moduleLessons.length > 0 && moduleLessons.every((l) => l.status === "completed");
            const isModuleAccessible = accessMode === "open" || moduleLessons.some((l) => {
              const idx = orderedLessons.findIndex((ol) => ol.id === l.id);
              return l.status === "completed" || idx === firstUncompletedIndex;
            });

            return (
              <div
                key={module.id}
                className={`rounded-3xl border-2 transition-all overflow-hidden ${
                  isModuleAccessible
                    ? "border-[#27272a] bg-[#121214]"
                    : "border-[#1c1c1f] bg-[#0e0e10]/60 opacity-60"
                }`}
              >
                {/* Header do Módulo */}
                <div className="px-6 py-5 border-b border-[#1f1f23] flex justify-between items-center bg-[#151518]">
                  <div className="flex items-center space-x-3">
                    <span className="w-7 h-7 rounded-lg bg-[#ffe500] text-black font-black flex items-center justify-center text-xs">
                      {module.module_number}
                    </span>
                    <div>
                      <span className="text-[10px] font-extrabold uppercase tracking-widest text-[#ffe500] block">
                        {t.course_module_prefix} {module.module_number}
                      </span>
                      <h3 className="text-lg font-black text-white">{module.title}</h3>
                    </div>
                  </div>
                  <div>
                    {!isModuleAccessible ? (
                      <span className="inline-flex items-center space-x-1 text-xs font-bold text-neutral-500 bg-[#1c1c1f] px-3 py-1 rounded-full">
                        <Lock className="w-3.5 h-3.5" />
                        <span>{t.course_status_locked}</span>
                      </span>
                    ) : isModuleCompleted ? (
                      <span className="inline-flex items-center space-x-1 text-xs font-bold text-green-400 bg-green-950/40 border border-green-800/40 px-3 py-1 rounded-full">
                        <CheckCircle2 className="w-3.5 h-3.5" />
                        <span>{t.course_status_completed}</span>
                      </span>
                    ) : (
                      <span className="inline-flex items-center space-x-1 text-xs font-bold text-[#ffe500] bg-[#ffe500]/10 border border-[#ffe500]/30 px-3 py-1 rounded-full">
                        <span>{t.course_status_in_progress}</span>
                      </span>
                    )}
                  </div>
                </div>

                {/* Lista de Aulas do Módulo */}
                <div className="divide-y divide-[#1c1c20]">
                  {moduleLessons.map((lesson) => {
                    const isCompleted = lesson.status === "completed";
                    const lessonGlobalIdx = orderedLessons.findIndex((ol) => ol.id === lesson.id);
                    const isLocked = accessMode === "guided" && !isCompleted && lessonGlobalIdx > firstUncompletedIndex;

                    return (
                      <div
                        key={lesson.id}
                        className="p-5 sm:px-6 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 hover:bg-[#18181c] transition-all"
                      >
                        <div className="flex items-start space-x-4">
                          <div
                            className={`w-9 h-9 rounded-xl flex items-center justify-center shrink-0 mt-0.5 font-black text-sm ${
                              isCompleted
                                ? "bg-green-500/20 text-green-400 border border-green-500/40"
                                : !isLocked
                                ? "bg-[#ffe500]/20 text-[#ffe500] border border-[#ffe500]/40"
                                : "bg-[#1f1f23] text-neutral-600 border border-neutral-800"
                            }`}
                          >
                            {isCompleted ? <CheckCircle2 className="w-5 h-5" /> : lesson.lesson_number}
                          </div>
                          <div className="space-y-1">
                            <div className="flex items-center space-x-2">
                              <span className="text-[10px] font-black uppercase tracking-wider text-[#ffe500]/80">
                                {t.course_episode_prefix} {lesson.lesson_number}
                              </span>
                            </div>
                            <h4 className="font-black text-base sm:text-lg text-white group-hover:text-[#ffe500] transition-colors leading-snug">
                              {lesson.title}
                            </h4>
                            <p className="text-xs sm:text-[13px] text-neutral-300 leading-relaxed font-normal max-w-2xl pt-0.5">
                              {lesson.core_concept}
                            </p>
                          </div>
                        </div>

                        <div>
                          {isLocked ? (
                            <div className="flex items-center space-x-1.5 text-xs text-neutral-600 font-bold px-4 py-2 rounded-xl bg-[#141416] border border-neutral-800/80 cursor-not-allowed">
                              <Lock className="w-4 h-4" />
                              <span>{t.course_status_locked}</span>
                            </div>
                          ) : (
                            <button
                              onClick={() => router.push(`/lesson/${lesson.id}`)}
                              className={`px-5 py-2.5 rounded-xl font-extrabold text-xs flex items-center space-x-2 transition-all cursor-pointer ${
                                isCompleted
                                  ? "bg-[#27272a] hover:bg-[#3f3f46] text-white"
                                  : "bg-[#ffe500] hover:bg-[#fff000] text-black shadow-lg shadow-[#ffe500]/10"
                              }`}
                            >
                              <Play className="w-3.5 h-3.5 fill-current" />
                              <span>{isCompleted ? t.course_btn_review_lesson : t.course_btn_start_lesson}</span>
                            </button>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Modal de Confirmação de Exclusão Definitiva */}
      {showDeleteModal && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-[#141416] border border-[#27272a] rounded-3xl max-w-lg w-full p-6 sm:p-8 shadow-2xl relative animate-in fade-in zoom-in duration-150">
            {/* Botão Fechar no canto superior */}
            <button
              onClick={() => !isDeleting && setShowDeleteModal(false)}
              disabled={isDeleting}
              className="absolute top-5 right-5 text-neutral-400 hover:text-white transition-colors p-1 rounded-lg hover:bg-neutral-800/50"
            >
              <X className="w-5 h-5" />
            </button>

            {/* Cabeçalho do Alerta */}
            <div className="flex items-start space-x-4">
              <div className="w-12 h-12 rounded-2xl bg-red-500/10 border border-red-500/20 flex items-center justify-center flex-shrink-0 text-red-400">
                <AlertTriangle className="w-6 h-6" />
              </div>
              <div>
                <h3 className="text-lg sm:text-xl font-black text-white">
                  {t.course_delete_confirm_title}
                </h3>
                <p className="text-xs text-red-400/90 font-medium mt-0.5">
                  {t.course_delete_confirm_desc}
                </p>
              </div>
            </div>

            {/* Conteúdo Explicativo */}
            <div className="mt-5 space-y-3 text-sm text-neutral-300 bg-[#0d0d0f] border border-[#202024] p-4 rounded-2xl">
              <p>
                <strong className="text-white">&ldquo;{course.subject}&rdquo;</strong>
              </p>
              <ul className="text-xs text-neutral-400 space-y-1.5 list-disc list-inside">
                <li><strong className="text-neutral-300">{course.modules.length} {lang === "en-US" ? "modules" : "módulos"}</strong> &bull; <strong className="text-neutral-300">{allLessons.length} {lang === "en-US" ? "lessons" : "aulas"}</strong></li>
              </ul>
            </div>

            {deleteError && (
              <div className="mt-4 p-3 rounded-xl bg-red-950/30 border border-red-800/40 text-red-400 text-xs font-semibold">
                {deleteError}
              </div>
            )}

            {/* Botões de Ação */}
            <div className="mt-6 flex flex-col-reverse sm:flex-row items-center justify-end gap-3">
              <button
                type="button"
                onClick={() => setShowDeleteModal(false)}
                disabled={isDeleting}
                className="w-full sm:w-auto px-4 py-2.5 rounded-xl border border-[#27272a] hover:bg-[#1f1f23] text-neutral-300 font-bold text-xs transition-colors"
              >
                {t.course_delete_cancel}
              </button>
              <button
                type="button"
                onClick={handleDeleteCourse}
                disabled={isDeleting}
                className="w-full sm:w-auto px-5 py-2.5 rounded-xl bg-red-600 hover:bg-red-700 active:bg-red-800 text-white font-bold text-xs transition-colors flex items-center justify-center space-x-2 shadow-lg shadow-red-950/50 disabled:opacity-50"
              >
                {isDeleting ? (
                  <>
                    <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    <span>{lang === "en-US" ? "Deleting..." : "Excluindo..."}</span>
                  </>
                ) : (
                  <span>{t.course_delete_proceed}</span>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal de Confirmação do Modo Bloqueado / Guiado com Fundo Blur */}
      {showGuidedWarningModal && (
        <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-md flex items-center justify-center p-4 animate-in fade-in duration-200">
          <div className="bg-[#141416] border border-[#2e2e33] rounded-3xl max-w-md w-full p-6 sm:p-7 shadow-2xl relative animate-in fade-in zoom-in-95 duration-150">
            {/* Fechar no canto superior */}
            <button
              onClick={cancelSwitchToGuided}
              className="absolute top-5 right-5 text-neutral-400 hover:text-white transition-colors p-1.5 rounded-lg hover:bg-neutral-800/50 cursor-pointer"
            >
              <X className="w-5 h-5" />
            </button>

            {/* Cabeçalho com Ícone de Cadeado */}
            <div className="flex items-start space-x-3.5">
              <div className="w-11 h-11 rounded-2xl bg-[#ffe500]/10 border border-[#ffe500]/30 flex items-center justify-center flex-shrink-0 text-[#ffe500]">
                <Lock className="w-5 h-5" />
              </div>
              <div className="pr-6">
                <h3 className="text-base sm:text-lg font-black text-white leading-snug">
                  {t.guided_modal_title}
                </h3>
                <span className="text-[11px] font-bold text-[#ffe500] uppercase tracking-wider block mt-0.5">
                  Mastery Learning &bull; {lang === "en-US" ? "Sequential Track" : "Trilha Sequencial"}
                </span>
              </div>
            </div>

            {/* Mensagem Explicativa */}
            <div className="mt-4 p-4 rounded-2xl bg-[#0d0d0f] border border-[#202024] space-y-2.5">
              <p className="text-xs sm:text-[13px] text-neutral-200 leading-relaxed font-normal">
                {t.guided_modal_desc}
              </p>
              <div className="flex items-center space-x-2 text-[11px] text-neutral-400 pt-1">
                <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                <span>{lang === "en-US" ? "Your previously completed lessons will remain saved." : "O progresso de aulas já concluídas continuará salvo."}</span>
              </div>
            </div>

            {/* Botões de Ação: Confirmar em Verde, Cancelar em Vermelho */}
            <div className="mt-6 flex flex-col sm:flex-row items-center justify-end gap-2.5">
              <button
                type="button"
                onClick={cancelSwitchToGuided}
                className="w-full sm:w-auto px-5 py-2.5 rounded-xl bg-red-600/20 hover:bg-red-600/30 text-red-400 hover:text-red-300 border border-red-500/30 font-bold text-xs transition-all cursor-pointer"
              >
                {t.guided_modal_cancel}
              </button>
              <button
                type="button"
                onClick={confirmSwitchToGuided}
                className="w-full sm:w-auto px-6 py-2.5 rounded-xl bg-emerald-500 hover:bg-emerald-400 active:bg-emerald-600 text-black font-black text-xs transition-all flex items-center justify-center space-x-1.5 shadow-lg shadow-emerald-500/20 cursor-pointer"
              >
                <Lock className="w-3.5 h-3.5" />
                <span>{t.guided_modal_confirm}</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal de Configurações */}
      <SettingsModal
        isOpen={showSettingsModal}
        onClose={() => setShowSettingsModal(false)}
        lang={lang}
      />
    </main>
  );
}
