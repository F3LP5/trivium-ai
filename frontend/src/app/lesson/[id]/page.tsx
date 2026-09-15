"use client";

import React, { useEffect, useState, useMemo } from "react";
import { useParams, useRouter } from "next/navigation";
import { 
  getLesson, 
  submitQuiz, 
  submitSimulation, 
  submitSocraticDuel, 
  getLessonPdfUrl, 
  LessonFullDetail,
  IndicatorState,
  SimulationTurn1Option,
  SimulationTurn2Option
} from "@/lib/api";
import { 
  ArrowLeft, 
  ArrowRight, 
  Download, 
  Send, 
  BookOpen, 
  ShieldCheck, 
  CheckCircle2, 
  Target,
  RotateCcw,
  CheckCircle,
  ZoomIn,
  ZoomOut,
  Flame,
  Settings,
  ChevronLeft,
  Bookmark,
  ExternalLink,
  Copy,
  Check
} from "lucide-react";
import Link from "next/link";
import confetti from "canvas-confetti";
import ReactMarkdown from "react-markdown";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { vscDarkPlus } from "react-syntax-highlighter/dist/esm/styles/prism";
import { useZoom } from "@/context/ZoomContext";
import SettingsModal from "@/components/SettingsModal";
import LessonTutorChat from "@/components/LessonTutorChat";
import { translations, SupportedLanguage } from "@/lib/i18n";

// Componente de Bloco de Código com Prism Syntax Highlighting e Botão de Copiar
function CodeBlock({ language, code, isEn }: { language: string; code: string; isEn?: boolean }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="relative my-6 rounded-2xl overflow-hidden border border-[#27272a] bg-[#121214] group shadow-xl not-prose">
      <div className="flex items-center justify-between px-4 py-2 bg-[#18181b] border-b border-[#27272a] text-xs text-neutral-400">
        <span className="font-mono font-bold uppercase text-[11px] text-[#ffe500] tracking-wider">
          {language || (isEn ? "code" : "código")}
        </span>
        <button
          onClick={handleCopy}
          className="flex items-center space-x-1.5 hover:text-white transition-colors bg-[#27272a] hover:bg-[#333338] px-2.5 py-1 rounded-lg text-[11px] cursor-pointer"
          title={isEn ? "Copy code" : "Copiar código"}
        >
          {copied ? (
            <>
              <Check className="w-3 h-3 text-green-400" />
              <span className="text-green-400 font-semibold">{isEn ? "Copied!" : "Copiado!"}</span>
            </>
          ) : (
            <>
              <Copy className="w-3 h-3 text-neutral-400" />
              <span>{isEn ? "Copy" : "Copiar"}</span>
            </>
          )}
        </button>
      </div>
      <div className="p-4 overflow-x-auto text-sm font-mono leading-relaxed">
        <SyntaxHighlighter
          language={language || "text"}
          style={vscDarkPlus}
          customStyle={{
            margin: 0,
            padding: 0,
            background: "transparent",
            fontSize: "14px",
          }}
          wrapLongLines={true}
        >
          {code.trim()}
        </SyntaxHighlighter>
      </div>
    </div>
  );
}

// Níveis de Performance da Régua de 5 Blocos
type PerformanceLevel = "pessimo" | "ruim" | "neutro" | "bom" | "excelente";

// Função para converter indicadores da IA em nível da régua (Péssimo / Ruim / Neutro / Bom / Excelente)
function getPerformanceFromIndicators(indicators?: IndicatorState[] | null, isSuccess?: boolean): PerformanceLevel {
  if (!indicators || indicators.length === 0) {
    if (isSuccess === true) return "excelente";
    if (isSuccess === false) return "ruim";
    return "neutro";
  }

  // Verifica se há dicas explícitas de cor ou labels
  const colors = indicators.map((ind) => ind.color_hint?.toLowerCase());
  const statuses = indicators.map((ind) => String(ind.status_level || ind.value || "").toLowerCase());
  
  if (statuses.some((s) => s.includes("excelente") || s.includes("mestre") || s.includes("ótimo"))) {
    return "excelente";
  }
  if (statuses.some((s) => s.includes("crítico") || s.includes("grave") || s.includes("falha") || s.includes("péssimo"))) {
    return "pessimo";
  }
  if (statuses.some((s) => s.includes("alerta") || s.includes("ruim") || s.includes("instável"))) {
    return "ruim";
  }

  // Se for numérico, calcula a média ponderada
  const numericValues: number[] = [];
  for (const ind of indicators) {
    const rawVal = ind.value_numeric ?? (typeof ind.value === "number" ? ind.value : Number(ind.value));
    if (!isNaN(rawVal) && rawVal !== null && rawVal !== undefined) {
      // Se o indicador for de custo/risco, inverte para medir performance positiva
      const isCostOrRisk = ind.name.toLowerCase().includes("custo") || ind.name.toLowerCase().includes("risco") || ind.name.toLowerCase().includes("risk");
      numericValues.push(isCostOrRisk ? 100 - rawVal : rawVal);
    }
  }

  if (numericValues.length > 0) {
    const avg = numericValues.reduce((a, b) => a + b, 0) / numericValues.length;
    if (avg >= 85) return "excelente";
    if (avg >= 65) return "bom";
    if (avg >= 45) return "neutro";
    if (avg >= 30) return "ruim";
    return "pessimo";
  }

  if (colors.includes("red")) return "ruim";
  if (colors.includes("green")) return isSuccess ? "excelente" : "bom";
  return "neutro";
}

// Renderizador visual da Régua de 5 Blocos (PERFORMANCE)
function renderPerformanceBar(currentLevel: PerformanceLevel, isInitialStep: boolean, lang: string) {
  const levelLabels: Record<PerformanceLevel, string> = {
    pessimo: lang === "en-US" ? "Terrible" : "Péssimo",
    ruim: lang === "en-US" ? "Poor" : "Ruim",
    neutro: lang === "en-US" ? "Neutral" : "Neutro",
    bom: lang === "en-US" ? "Good" : "Bom",
    excelente: lang === "en-US" ? "Excellent" : "Excelente"
  };

  const labelColorClasses: Record<PerformanceLevel, string> = {
    pessimo: "text-rose-500",
    ruim: "text-amber-400",
    neutro: "text-neutral-300",
    bom: "text-green-400",
    excelente: "text-[#00f59b] drop-shadow-[0_0_10px_rgba(0,245,155,0.5)]"
  };

  return (
    <div className="space-y-2.5 pt-1">
      <div className="flex items-center justify-between">
        <span className="text-xs text-neutral-400 font-medium tracking-wider uppercase font-mono">
          {lang === "en-US" ? "PERFORMANCE" : "PERFORMANCE"}
        </span>
        <span className={`text-xs font-black uppercase tracking-wider font-mono transition-colors ${labelColorClasses[currentLevel]}`}>
          {levelLabels[currentLevel]}
        </span>
      </div>

      {/* Régua de 5 Blocos */}
      <div className="grid grid-cols-5 gap-2 w-full">
        {/* Bloco 1: Péssimo */}
        <div 
          className={`h-2 rounded-md transition-all duration-300 ${
            currentLevel === "pessimo" 
              ? "bg-rose-600 shadow-[0_0_12px_rgba(225,29,72,0.6)]" 
              : "bg-[#27272a]"
          }`} 
          title="Péssimo" 
        />
        {/* Bloco 2: Ruim */}
        <div 
          className={`h-2 rounded-md transition-all duration-300 ${
            currentLevel === "ruim" 
              ? "bg-amber-500 shadow-[0_0_10px_rgba(245,158,11,0.5)]" 
              : "bg-[#27272a]"
          }`} 
          title="Ruim" 
        />
        {/* Bloco 3: Neutro */}
        <div 
          className={`h-2 rounded-md transition-all duration-300 ${
            currentLevel === "neutro" 
              ? "bg-neutral-400 shadow-[0_0_8px_rgba(255,255,255,0.3)]" 
              : "bg-[#27272a]"
          }`} 
          title="Neutro" 
        />
        {/* Bloco 4: Bom */}
        <div 
          className={`h-2 rounded-md transition-all duration-300 ${
            currentLevel === "bom" 
              ? "bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.4)]" 
              : "bg-[#27272a]"
          }`} 
          title="Bom" 
        />
        {/* Bloco 5: Excelente */}
        <div 
          className={`h-2 rounded-md transition-all duration-300 ${
            currentLevel === "excelente" 
              ? "bg-[#00f59b] shadow-[0_0_18px_rgba(0,245,155,0.9)]" 
              : "bg-[#27272a]"
          }`} 
          title="Excelente" 
        />
      </div>

      {/* Legenda visual nos extremos (Apenas visível no Cenário Inicial) */}
      {isInitialStep && (
        <div className="flex justify-between text-[10px] text-neutral-600 font-mono transition-opacity duration-200">
          <span>{lang === "en-US" ? "Terrible" : "Péssimo"}</span>
          <span className="text-neutral-500">{lang === "en-US" ? "Neutral" : "Neutro"}</span>
          <span>{lang === "en-US" ? "Excellent" : "Excelente"}</span>
        </div>
      )}
    </div>
  );
}

// Limpa repetições de [LACUNA] e substitui por "..." elegante e padronizado
function renderFormattedBlankSentence(raw: string) {
  if (!raw) return null;
  // Substitui qualquer repetição de [LACUNA], [lacuna], ___, etc. por marcador único
  const normalized = raw
    .replace(/(\s*\[LACUNA\]\s*)+/gi, " __BLANK__ ")
    .replace(/_{2,}/g, " __BLANK__ ")
    .replace(/(\s*\.\.\.\s*)+/g, " __BLANK__ ");

  const parts = normalized.split("__BLANK__");
  if (parts.length === 1) {
    return <span>{raw}</span>;
  }

  return (
    <span>
      {parts.map((part, idx) => (
        <React.Fragment key={idx}>
          {part}
          {idx < parts.length - 1 && (
            <span className="inline-flex items-center justify-center px-2 py-0.5 mx-1 font-mono font-black text-xs text-[#ffe500] bg-[#222226] border border-[#3f3f46] rounded-md tracking-wider shadow-inner select-none">
              ...
            </span>
          )}
        </React.Fragment>
      ))}
    </span>
  );
}

// Formata o dilema do Estudo de Caso em cards elegantes e limpos
function renderStructuredDilemma(rawText: string, imageUrl?: string, imageCaption?: string, isEn?: boolean) {
  if (!rawText) return null;

  // Detecta se há opções na pergunta, como "Rota A:", "Opção A:", "Option A:", "Route A:", "1)", "A)" etc.
  const regexA = /(?:(?:Rota|Opção|Option|Route)\s*A[:.\x2d]|(?:\(|\[)?(?:Opção|Option)?\s*(?:1|A)[:.)\]\x2d])\s*([\s\S]*?)(?=(?:(?:Rota|Opção|Option|Route)\s*B[:.\x2d]|(?:\(|\[)?(?:Opção|Option)?\s*(?:2|B)[:.)\]\x2d])|$)/i;
  const matchA = rawText.match(regexA);

  let contentNode = null;

  if (matchA && (rawText.search(/(?:(?:Rota|Opção|Option|Route)\s*B[:.\x2d]|(?:\(|\[)?(?:Opção|Option)?\s*(?:2|B)[:.)\]\x2d])/i) !== -1)) {
    const splitIndex = rawText.search(/(?:(?:Rota|Opção|Option|Route)\s*A[:.\x2d]|(?:\(|\[)?(?:Opção|Option)?\s*(?:1|A)[:.)\]\x2d])/i);
    let introText = splitIndex > 0 ? rawText.substring(0, splitIndex).trim() : "";
    introText = introText.replace(/(?:,\s*|\s+)(?:você\s+tem\s+(?:duas\s+opções|dois\s+caminhos)|you\s+have\s+(?:two\s+options|two\s+paths))[:.]?$/i, ".").trim();

    const optionsPart = rawText.substring(splitIndex);
    const splitB = optionsPart.split(/(?:(?:Rota|Opção|Option|Route)\s*B[:.\x2d]|(?:\(|\[)?(?:Opção|Option)?\s*(?:2|B)[:.)\]\x2d])/i);
    
    const opt1Raw = splitB[0] ? splitB[0].replace(/^(?:(?:Rota|Opção|Option|Route)\s*A[:.\x2d]|(?:\(|\[)?(?:Opção|Option)?\s*(?:1|A)[:.)\]\x2d])\s*/i, "").trim() : "";
    let opt2Raw = splitB[1] || "";

    // Separar a pergunta final (ex: "Qual caminho você recomendaria...") da Opção B
    let outroText = "";
    const questionMatch = opt2Raw.match(/((?:Qual|O que|Como|Which|What|How)[\s\S]*\?)$/i);
    if (questionMatch && questionMatch.index !== undefined) {
      outroText = questionMatch[0].trim();
      opt2Raw = opt2Raw.substring(0, questionMatch.index).trim();
    }

    // Limpa pontuações residuais
    const cleanOption = (txt: string) => {
      let clean = txt.trim().replace(/(?:,\s*(?:ou|e|or|and)|\s+(?:ou|e|or|and)|[,;:.!\x2d])+$/i, "").trim();
      if (clean && !clean.endsWith(".")) clean += ".";
      return clean;
    };

    const opt1 = cleanOption(opt1Raw);
    const opt2 = cleanOption(opt2Raw);

    if (opt1 && opt2) {
      contentNode = (
        <div className="text-sm md:text-base text-neutral-100 font-normal space-y-4 leading-loose">
          {introText && (
            <p className="text-neutral-100">
              {introText}
            </p>
          )}

          <div className="space-y-3 pl-3 border-l-2 border-[#ffe500]/40 py-1.5 my-2">
            <p className="text-neutral-200">
              &bull; <strong className="text-white font-bold">{isEn ? "Option A:" : "Opção A:"}</strong> {opt1}
            </p>
            <p className="text-neutral-200">
              &bull; <strong className="text-white font-bold">{isEn ? "Option B:" : "Opção B:"}</strong> {opt2}
            </p>
          </div>

          {outroText && (
            <p className="pt-1 text-neutral-200">
              {outroText}
            </p>
          )}
        </div>
      );
    }
  }

  if (!contentNode) {
    const paragraphs = rawText.split("\n\n").filter(Boolean);
    contentNode = (
      <div className="text-sm md:text-base text-neutral-100 font-normal space-y-3 leading-loose">
        {paragraphs.map((p, i) => (
          <p key={i}>
            {p}
          </p>
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {imageUrl && (
        <div className="w-full rounded-2xl overflow-hidden border border-[#27272a] bg-[#141416]">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={imageUrl}
            alt={imageCaption || (isEn ? "Case study illustration" : "Ilustração do caso de estudo")}
            className="w-full max-h-56 object-cover object-center filter grayscale contrast-125"
            onError={(e) => {
              // Degradação silenciosa se o arquivo não existir localmente
              (e.currentTarget.parentElement as HTMLElement)?.style.setProperty("display", "none");
            }}
          />
          {imageCaption && (
            <div className="px-4 py-2 text-[11px] text-neutral-400 bg-[#121214] border-t border-[#222226] italic">
              {imageCaption}
            </div>
          )}
        </div>
      )}
      {contentNode}
    </div>
  );
}

// Componente para exibir termos do Glossário com tooltip interativo inline (Desktop hover / Mobile tap)
function GlossaryTerm({ term, definition, isEn }: { term: string; definition: string; isEn?: boolean }) {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <span 
      className="relative inline-block cursor-help group select-none"
      onClick={(e) => {
        e.stopPropagation();
        setIsOpen((prev) => !prev);
      }}
      onMouseEnter={() => setIsOpen(true)}
      onMouseLeave={() => setIsOpen(false)}
    >
      <span className="border-b-2 border-dotted border-[#ffe500]/80 text-[#f4f4f5] font-semibold group-hover:text-[#ffe500] transition-colors underline-offset-4">
        {term}
      </span>
      {isOpen && (
        <span 
          className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2.5 w-72 sm:w-80 p-3.5 bg-[#18181b] border-2 border-[#ffe500] rounded-2xl text-xs text-[#f4f4f5] shadow-2xl z-50 text-left font-normal normal-case leading-relaxed animate-in fade-in zoom-in-95 duration-150 pointer-events-auto"
          onClick={(e) => e.stopPropagation()}
        >
          <span className="flex items-center justify-between font-black text-[#ffe500] mb-1.5 pb-1 border-b border-[#27272a] text-sm">
            <span className="capitalize">💡 {term}</span>
            <span className="text-[10px] text-neutral-400 font-mono tracking-wider uppercase">
              {isEn ? "Glossary" : "Glossário"}
            </span>
          </span>
          <span className="text-[#d4d4d8] leading-relaxed text-[13px] block">
            {definition}
          </span>
          <span className="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-[#ffe500]" />
        </span>
      )}
    </span>
  );
}

function renderTextWithGlossary(text: string, glossary: Map<string, string>, isEn?: boolean): React.ReactNode {
  if (!text || glossary.size === 0) return text;

  // Ordena termos por tamanho decrescente para priorizar termos compostos (ex: "hexâmetro dactílico" antes de "hexâmetro")
  const sortedTerms = Array.from(glossary.keys()).sort((a, b) => b.length - a.length);
  const escapedTerms = sortedTerms.map((t) => t.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"));
  // Usa lookaround compatível com acentos em português (\p{L}\p{N})
  const pattern = new RegExp(`(?<=^|[^\\p{L}\\p{N}])(${escapedTerms.join("|")})(?=[^\\p{L}\\p{N}]|$)`, "gui");

  const parts: React.ReactNode[] = [];
  let lastIndex = 0;
  let match: RegExpExecArray | null;

  while ((match = pattern.exec(text)) !== null) {
    const matchIndex = match.index;
    const matchedWord = match[1] || match[0];
    const definition = glossary.get(matchedWord.toLowerCase());

    if (matchIndex > lastIndex) {
      parts.push(text.slice(lastIndex, matchIndex));
    }

    if (definition) {
      parts.push(
        <GlossaryTerm 
          key={`${matchIndex}-${matchedWord}`} 
          term={matchedWord} 
          definition={definition} 
          isEn={isEn}
        />
      );
    } else {
      parts.push(matchedWord);
    }

    lastIndex = matchIndex + matchedWord.length;
    pattern.lastIndex = lastIndex;
  }

  if (lastIndex < text.length) {
    parts.push(text.slice(lastIndex));
  }

  return parts.length > 0 ? parts : text;
}

function enrichWithGlossary(children: React.ReactNode, glossary: Map<string, string>, isEn?: boolean): React.ReactNode {
  if (!children || glossary.size === 0) return children;
  if (typeof children === "string") {
    return renderTextWithGlossary(children, glossary, isEn);
  }
  if (Array.isArray(children)) {
    return children.map((child, idx) => {
      if (typeof child === "string") {
        return <React.Fragment key={idx}>{renderTextWithGlossary(child, glossary, isEn)}</React.Fragment>;
      }
      return child;
    });
  }
  return children;
}

export default function LessonPage() {
  const params = useParams();
  const router = useRouter();
  const lessonId = Number(params?.id);

  const [lesson, setLesson] = useState<LessonFullDetail | null>(null);
  const [loading, setLoading] = useState(true);

  // Modo de exibição: "reader" (somente leitura) ou "quiz" (somente questões)
  const [activeTab, setActiveTab] = useState<"reader" | "quiz">("reader");
  const [showSettingsModal, setShowSettingsModal] = useState(false);

  // Estado da Gaveta / Split View do Tutor de IA da Aula
  const [isTutorChatOpen, setIsTutorChatOpen] = useState(false);

  const { zoomLevel, zoomIn, zoomOut, resetZoom, canZoomIn, canZoomOut } = useZoom();

  // Estados do Quiz
  const [mcqAnswers, setMcqAnswers] = useState<Record<string, string>>({});
  const [blankAnswers, setBlankAnswers] = useState<Record<string, string>>({});
  const [mcqResult, setMcqResult] = useState<{ mcq_score: number; mcq_passed: boolean; message: string } | null>(null);
  const [discursiveResult, setDiscursiveResult] = useState<{ passed: boolean; score: number; feedback: string } | null>(null);
  const [isSubmittingMcq, setIsSubmittingMcq] = useState(false);

  // Estados do Mini-Simulador de Impacto (Slides Gamificados Horizontais)
  const [simSlide, setSimSlide] = useState<number>(0); // 0: Contexto, 1: Turno 1, 2: Reação/Turno 2, 3: Desfecho Final
  const [simTurn1, setSimTurn1] = useState<SimulationTurn1Option | null>(null);
  const [simTurn2, setSimTurn2] = useState<SimulationTurn2Option | null>(null);
  const [isSubmittingSim, setIsSubmittingSim] = useState(false);
  const [simPassed, setSimPassed] = useState(false);

  // Estados do Duelo Socrático (2 Rounds)
  const [socraticRound1Answer, setSocraticRound1Answer] = useState("");
  const [socraticRound2Answer, setSocraticRound2Answer] = useState("");
  const [socraticFeedback1, setSocraticFeedback1] = useState<string | null>(null);
  const [cognitiveKnot, setCognitiveKnot] = useState<string | null>(null);
  const [socraticResult, setSocraticResult] = useState<{ passed: boolean; score: number; feedback: string } | null>(null);
  const [isSubmittingSocratic, setIsSubmittingSocratic] = useState(false);
  const [socraticPassed, setSocraticPassed] = useState(false);

  useEffect(() => {
    if (!lessonId) return;
    getLesson(lessonId)
      .then((data) => {
        setLesson(data);
        setLoading(false);
        if (data.simulation_passed) {
          setSimPassed(true);
        }
        if (data.socratic_passed) {
          setSocraticPassed(true);
        }
        if (data.socratic_state) {
          if (data.socratic_state.round1_answer) setSocraticRound1Answer(data.socratic_state.round1_answer);
          if (data.socratic_state.round1_feedback) setSocraticFeedback1(data.socratic_state.round1_feedback);
          if (data.socratic_state.cognitive_knot) setCognitiveKnot(data.socratic_state.cognitive_knot);
          if (data.socratic_state.round2_answer) setSocraticRound2Answer(data.socratic_state.round2_answer);
          if (data.socratic_state.passed) {
            const isSavedEn = data.language?.startsWith("en");
            setSocraticPassed(true);
            setSocraticResult({
              passed: true,
              score: data.socratic_state.score ?? 10,
              feedback: data.socratic_state.final_feedback || (isSavedEn ? "Passed the Socratic Duel!" : "Aprovado no Duelo Socrático!"),
            });
          }
        }
        if (data.discursive_passed) {
          const isSavedEn = data.language?.startsWith("en");
          setDiscursiveResult({
            passed: true,
            score: 10,
            feedback: data.discursive_feedback || (isSavedEn ? "Passed the discursive assessment." : "Aprovado na avaliação discursiva."),
          });
        }
      })
      .catch((err) => {
        console.error(err);
        setLoading(false);
      });
  }, [lessonId]);

  // Sanitização de Markdown (evita vazamento de hashtags como '### ###' ou '### ##' e repara URLs corrompidas)
  const sanitizedMarkdown = useMemo(() => {
    if (!lesson?.content_markdown) return "";
    return lesson.content_markdown
      .replace(/^[ \t]*(#{1,6})(?:\s*#+)+\s*/gm, "$1 ")
      .replace(/^([ \t]*>[ \t]*)(#{1,6})(?:\s*#+)+\s*/gm, "$1$2 ")
      .replace(/https?\s*\/\//g, "https://")
      .replace(/https?\*\*:\s*\/\//g, "https://")
      .replace(/https?:\s*\/\//g, "https://");
  }, [lesson?.content_markdown]);

  // Separação entre corpo principal, Glossário e Fontes Recomendadas da Aula
  const { mainMarkdown, glossaryMarkdown, sourcesMarkdown, glossaryMap, parsedSources } = useMemo(() => {
    if (!sanitizedMarkdown) {
      return { 
        mainMarkdown: "", 
        glossaryMarkdown: "", 
        sourcesMarkdown: "", 
        glossaryMap: new Map<string, string>(),
        parsedSources: [] as Array<{ title: string; url: string; tag?: string; description: string; isBook?: boolean }>
      };
    }

    const glossaryIndex = sanitizedMarkdown.search(/#{1,3}\s*(?:📖\s*)?(?:Gloss[aá]rio|Lesson\s+Glossary|Glossary)/i);
    const sourcesIndex = sanitizedMarkdown.search(/#{1,3}\s*(?:📚\s*)?(?:Fontes(?:\s*e\s*Leituras)?|Lesson\s+Sources(?:\s*and\s*Recommended\s*Readings)?|Sources(?:\s*and\s*Readings)?)/i);

    let main = sanitizedMarkdown;
    let glossary = "";
    let sources = "";

    if (glossaryIndex !== -1 && sourcesIndex !== -1) {
      if (glossaryIndex < sourcesIndex) {
        main = sanitizedMarkdown.slice(0, glossaryIndex);
        glossary = sanitizedMarkdown.slice(glossaryIndex, sourcesIndex);
        sources = sanitizedMarkdown.slice(sourcesIndex);
      } else {
        main = sanitizedMarkdown.slice(0, sourcesIndex);
        sources = sanitizedMarkdown.slice(sourcesIndex, glossaryIndex);
        glossary = sanitizedMarkdown.slice(glossaryIndex);
      }
    } else if (glossaryIndex !== -1) {
      main = sanitizedMarkdown.slice(0, glossaryIndex);
      glossary = sanitizedMarkdown.slice(glossaryIndex);
    } else if (sourcesIndex !== -1) {
      main = sanitizedMarkdown.slice(0, sourcesIndex);
      sources = sanitizedMarkdown.slice(sourcesIndex);
    }

    const map = new Map<string, string>();
    if (glossary) {
      const lines = glossary.split("\n");
      for (const line of lines) {
        const match = line.match(/^[-*]\s+\*\*\[?([^\]*:]+)\]?\*\*:\s*(.+)$/);
        if (match) {
          const rawTerm = match[1].trim();
          const definition = match[2].trim();
          if (rawTerm.toLowerCase().startsWith("case study")) continue;

          if (rawTerm.includes("/")) {
            for (const sub of rawTerm.split("/")) {
              const cleanSub = sub.trim();
              if (cleanSub.length >= 3 && cleanSub.length <= 40) {
                map.set(cleanSub.toLowerCase(), definition);
              }
            }
          } else if (rawTerm.length >= 3 && rawTerm.length <= 40) {
            map.set(rawTerm.toLowerCase(), definition);
          }
        }
      }
    }

    const parsedSourcesList: Array<{ title: string; url: string; tag?: string; description: string; isBook?: boolean }> = [];
    if (sources) {
      const lines = sources.split("\n");
      for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed.startsWith("-") && !trimmed.startsWith("*")) continue;

        let cleaned = trimmed.replace(/^[-*]\s*/, "");
        cleaned = cleaned
          .replace(/https?\s*\/\//g, "https://")
          .replace(/https?\*\*:\s*\/\//g, "https://")
          .replace(/https?:\s*\/\//g, "https://");

        let title = "";
        let url = "";
        let tag = "";
        let description = "";
        let isBook = false;

        const linkMatch = cleaned.match(/\[([^\]]+)\]\(([^()]*(?:\([^()]*\))*[^()]*)\)/);
        if (linkMatch) {
          const rawTitle = linkMatch[1].trim();
          const rawTarget = linkMatch[2].trim();
          title = rawTitle.replace(/^\*+|\*+$/g, "").trim();

          if (/^https?:\/\/[^\s]+$/i.test(rawTarget)) {
            url = rawTarget;
          } else if (/arquivo\s+local|pdf|epub|livro/i.test(rawTarget)) {
            tag = rawTarget;
            isBook = true;
          }

          let afterLink = cleaned.slice(linkMatch.index! + linkMatch[0].length).trim();
          afterLink = afterLink.replace(/^\*+/, "").replace(/\(dom[ií]nio\)/gi, "").trim();

          const parenMatch = afterLink.match(/^\(([^()]*(?:\([^()]*\))*[^()]*)\)\s*:?\s*(.*)$/);
          if (parenMatch) {
            const capturedTag = parenMatch[1].trim();
            if (!/^(?:dom[ií]nio|dominio)$/i.test(capturedTag)) {
              tag = capturedTag;
            }
            afterLink = parenMatch[2].trim();
          }

          afterLink = afterLink.replace(/^[:\s\*]+/, "").replace(/^\(dom[ií]nio\)\s*:?\s*/gi, "").trim();
          description = afterLink;
        } else {
          const colonIdx = cleaned.indexOf(":");
          if (colonIdx !== -1) {
            const left = cleaned.slice(0, colonIdx).trim().replace(/^\*+|\*+$/g, "");
            const right = cleaned.slice(colonIdx + 1).trim();

            const pMatch = left.match(/^(.*?)\s*\(([^()]*(?:\([^()]*\))*[^()]*)\)$/);
            if (pMatch) {
              title = pMatch[1].trim().replace(/^\*+|\*+$/g, "");
              tag = pMatch[2].trim();
            } else {
              title = left;
            }
            description = right;
          } else {
            title = cleaned.replace(/^\*+|\*+$/g, "");
          }
        }

        description = description.replace(/^\*+|\*+$/g, "").replace(/^[:\s\-–]+/, "").trim();

        if (
          /arquivo\s+local|livro\s+base|pdf|epub|documento/i.test(tag || "") ||
          /arquivo\s+local|livro\s+base/i.test(title || "")
        ) {
          isBook = true;
        }

        if (title) {
          parsedSourcesList.push({
            title,
            url,
            tag: tag || undefined,
            description,
            isBook
          });
        }
      }
    }

    return { 
      mainMarkdown: main, 
      glossaryMarkdown: glossary, 
      sourcesMarkdown: sources, 
      glossaryMap: map, 
      parsedSources: parsedSourcesList 
    };
  }, [sanitizedMarkdown]);

  const cleanHeadingChildren = (children: React.ReactNode): React.ReactNode => {
    if (typeof children === "string") {
      return children.replace(/^[#\s]+/, "");
    }
    if (Array.isArray(children)) {
      return children.map((c, idx) => {
        if (idx === 0 && typeof c === "string") {
          return c.replace(/^[#\s]+/, "");
        }
        return c;
      });
    }
    return children;
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#0b0b0b] text-white flex items-center justify-center">
        <div className="flex items-center space-x-3 text-[#ffe500] font-bold">
          <div className="w-5 h-5 border-2 border-[#ffe500] border-t-transparent rounded-full animate-spin" />
          <span>Carregando apostila... / Loading lesson...</span>
        </div>
      </div>
    );
  }

  if (!lesson) {
    return (
      <div className="min-h-screen bg-[#0b0b0b] text-white flex flex-col items-center justify-center p-6">
        <h2 className="text-2xl font-black mb-4">Aula não encontrada / Lesson not found</h2>
        <Link href="/" className="text-[#ffe500] font-bold">Voltar ao Início / Back to Home</Link>
      </div>
    );
  }

  const lang: SupportedLanguage = lesson.language?.startsWith("en") ? "en-US" : "pt-BR";
  const t = translations[lang];

  const handleMcqSubmit = async () => {
    setIsSubmittingMcq(true);
    try {
      const res = await submitQuiz(lesson.id, mcqAnswers, blankAnswers);
      setMcqResult(res);
      if (res.lesson_completed) {
        setLesson((prev) => (prev ? { ...prev, status: "completed" } : null));
      }
      if (res.mcq_passed) {
        confetti({ particleCount: 50, spread: 60, origin: { y: 0.8 } });
      }
    } catch {
      alert(lang === "en-US" ? "Failed to submit objective answers." : "Erro ao enviar respostas objetivas.");
    } finally {
      setIsSubmittingMcq(false);
    }
  };

  const handleSelectSimTurn1 = (opt: SimulationTurn1Option) => {
    setSimTurn1(opt);
    setSimTurn2(null);
    setSimSlide(2); // Avança automaticamente para o Slide 2 (Reação e Turno 2)
  };

  const handleSelectSimTurn2 = async (opt2: SimulationTurn2Option) => {
    if (!simTurn1) return;
    setSimTurn2(opt2);
    setSimSlide(3); // Avança imediatamente para o Slide 3 (Desfecho Final)

    // Submissão e validação 100% automática sem necessidade de botão manual
    setIsSubmittingSim(true);
    try {
      const res = await submitSimulation(lesson.id, simTurn1.id, opt2.id, opt2.is_success);
      setSimPassed(true);
      if (res.lesson_completed) {
        setLesson((prev) => (prev ? { ...prev, status: "completed" } : null));
      }
      confetti({ particleCount: 60, spread: 65, origin: { y: 0.7 } });
    } catch {
      // Fallback gracioso caso dê erro de rede
      setSimPassed(true);
    } finally {
      setIsSubmittingSim(false);
    }
  };

  const handleResetSimulation = () => {
    setSimTurn1(null);
    setSimTurn2(null);
    setSimSlide(0);
  };

  const handleSocraticRound1Submit = async () => {
    if (!socraticRound1Answer.trim()) return;
    setIsSubmittingSocratic(true);
    try {
      const res = await submitSocraticDuel(lesson.id, 1, socraticRound1Answer.trim());
      if (res.passed_round1) {
        setCognitiveKnot(res.cognitive_knot);
        setSocraticFeedback1(res.feedback);
        confetti({ particleCount: 40, spread: 60, origin: { y: 0.8 } });
      } else {
        setSocraticFeedback1(res.feedback);
      }
    } catch {
      alert(lang === "en-US" ? "Failed to submit thesis to Socratic Debater." : "Erro ao submeter tese para o Debatedor Socrático.");
    } finally {
      setIsSubmittingSocratic(false);
    }
  };

  const handleSocraticRound2Submit = async () => {
    if (!socraticRound2Answer.trim()) return;
    setIsSubmittingSocratic(true);
    try {
      const res = await submitSocraticDuel(lesson.id, 2, socraticRound2Answer.trim());
      setSocraticResult(res);
      if (res.passed) {
        setSocraticPassed(true);
        confetti({ particleCount: 100, spread: 90, origin: { y: 0.6 } });
      }
      if (res.lesson_completed) {
        setLesson((prev) => (prev ? { ...prev, status: "completed" } : null));
      }
    } catch {
      alert(lang === "en-US" ? "Failed to submit rebuttal to Socratic Debater." : "Erro ao submeter réplica do Duelo Socrático.");
    } finally {
      setIsSubmittingSocratic(false);
    }
  };

  const quiz = lesson.quiz;
  const hasSim = Boolean(quiz?.simulation);
  const hasSoc = Boolean(quiz?.socratic_duel);

  const totalMcqsCount = quiz?.mcq?.length || 0;
  const minMcqRequired = totalMcqsCount <= 3 ? 2 : 3;
  const mcqOk = mcqResult ? mcqResult.mcq_passed : ((lesson.mcq_score ?? 0) >= minMcqRequired);
  const simOk = hasSim ? (simPassed || Boolean(lesson.simulation_passed)) : true;
  const socOk = hasSoc 
    ? (socraticPassed || Boolean(lesson.socratic_passed)) 
    : (discursiveResult ? discursiveResult.passed : Boolean(lesson.discursive_passed));

  const isLessonCompleted = lesson.status === "completed" || (mcqOk && simOk && socOk);

  // Estimativa de tempo de leitura
  const wordCount = lesson.content_markdown ? lesson.content_markdown.split(/\s+/).filter(Boolean).length : 0;
  const readingTimeMin = Math.max(1, Math.ceil(wordCount / 180));

  const switchToQuiz = () => {
    setActiveTab("quiz");
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const switchToReader = () => {
    setActiveTab("reader");
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  return (
    <main className={`min-h-screen bg-[#09090b] text-[#f4f4f5] pb-28 transition-[padding,margin] duration-300 ${
      isTutorChatOpen ? "sm:pr-[420px] md:pr-[460px] lg:pr-[480px]" : ""
    }`}>
      {/* Header Fixo de Navegação */}
      <header className="h-14 border-b border-[#1f1f23] px-4 sm:px-8 flex justify-between items-center bg-[#09090b]/95 backdrop-blur-md sticky top-0 z-40">
        {/* Lado Esquerdo: Logo Home + Botão Voltar */}
        <div className="flex items-center space-x-3">
          <Link href="/" className="flex items-center space-x-2 group" title={lang === "en-US" ? "Home (Trivium)" : "Página Inicial (Trivium)"}>
            <div className="w-7 h-7 rounded-lg bg-[#141416] border border-[#ffe500]/40 flex items-center justify-center group-hover:border-[#ffe500] transition-all overflow-hidden p-0.5 shadow-sm">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img 
                src="/trivium-logo.png" 
                alt="Trivium Logo" 
                className="w-full h-full object-contain"
              />
            </div>
            <span className="text-[11px] font-extrabold text-[#ffe500] uppercase tracking-widest group-hover:opacity-90 hidden sm:inline">TRIVIUM</span>
          </Link>
          <span className="text-neutral-700 hidden sm:inline">|</span>
          <button
            onClick={() => router.back()}
            className="flex items-center space-x-1.5 text-xs font-bold text-neutral-400 hover:text-white transition-colors group cursor-pointer"
          >
            <ArrowLeft className="w-3.5 h-3.5 group-hover:-translate-x-0.5 transition-transform" />
            <span>{t.lesson_back_course}</span>
          </button>
        </div>

        {/* Seletor de Modo (Leitor vs Questões) */}
        <div className="flex items-center bg-[#141416] p-1 rounded-xl border border-[#27272a]">
          <button
            id="tab-reader-btn"
            onClick={switchToReader}
            className={`flex items-center space-x-2 px-3 sm:px-4 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer ${
              activeTab === "reader"
                ? "bg-[#222226] text-white shadow-sm"
                : "text-neutral-400 hover:text-white"
            }`}
          >
            <BookOpen className="w-3.5 h-3.5 text-[#ffe500]" />
            <span>{t.lesson_tab_booklet}</span>
          </button>

          <button
            id="tab-quiz-btn"
            onClick={switchToQuiz}
            className={`flex items-center space-x-2 px-3 sm:px-4 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer ${
              activeTab === "quiz"
                ? "bg-[#ffe500] text-black shadow-sm font-extrabold"
                : "text-neutral-400 hover:text-white"
            }`}
          >
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>{t.lesson_tab_quiz}</span>
            {isLessonCompleted && (
              <CheckCircle2 className="w-3.5 h-3.5 text-green-500 ml-1" />
            )}
          </button>
        </div>

        {/* Lado Direito: Controles de Zoom + Botão de Download PDF */}
        <div className="flex items-center space-x-2 sm:space-x-3">
          {/* Controles de Zoom (100% a 200%) */}
          <div 
            className="flex items-center bg-[#141416] p-1 rounded-xl border border-[#27272a] space-x-1"
            title={lang === "en-US" ? "Global Zoom: 80% to 150% (Ctrl + Mouse Wheel or Ctrl +/-)" : "Zoom global: 80% a 150% (Ctrl + Roda do Mouse ou Ctrl +/-)"}
          >
            <button
              id="zoom-out-btn"
              onClick={zoomOut}
              disabled={!canZoomOut}
              className="p-1.5 rounded-lg text-neutral-400 hover:text-white disabled:opacity-25 disabled:cursor-not-allowed transition-colors cursor-pointer"
              title={lang === "en-US" ? "Zoom Out (Ctrl -)" : "Diminuir zoom (Ctrl - ou Roda para baixo)"}
              aria-label="Zoom Out"
            >
              <ZoomOut className="w-3.5 h-3.5" />
            </button>

            <button
              id="zoom-reset-btn"
              onClick={resetZoom}
              className="text-[11px] font-mono font-black px-1.5 py-0.5 rounded text-neutral-300 hover:text-[#ffe500] transition-colors cursor-pointer"
              title={lang === "en-US" ? "Reset Zoom to 100% (Ctrl 0)" : "Redefinir zoom para 100% (Ctrl 0)"}
            >
              {zoomLevel}%
            </button>

            <button
              id="zoom-in-btn"
              onClick={zoomIn}
              disabled={!canZoomIn}
              className="p-1.5 rounded-lg text-neutral-400 hover:text-white disabled:opacity-25 disabled:cursor-not-allowed transition-colors cursor-pointer"
              title={lang === "en-US" ? "Zoom In (Ctrl +)" : "Aumentar zoom (Ctrl + ou Roda para cima)"}
              aria-label="Zoom In"
            >
              <ZoomIn className="w-3.5 h-3.5" />
            </button>
          </div>

          <a
            href={getLessonPdfUrl(lesson.id)}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center space-x-2 bg-[#18181b] hover:bg-[#222226] border border-[#2e2e33] text-white px-3.5 py-1.5 rounded-xl text-xs font-bold transition-all shadow-sm"
            title="PDF"
          >
            <Download className="w-3.5 h-3.5 text-[#ffe500]" />
            <span className="hidden sm:inline">{t.lesson_btn_download_pdf}</span>
          </a>

          <button
            onClick={() => setShowSettingsModal(true)}
            className="flex items-center space-x-1.5 text-xs font-semibold text-neutral-300 hover:text-white bg-[#18181b] hover:bg-[#222226] border border-[#2e2e33] hover:border-[#ffe500]/40 px-3 py-1.5 rounded-xl transition-all"
            title={t.settings}
          >
            <Settings className="w-3.5 h-3.5 text-[#ffe500]" />
            <span className="hidden md:inline">{t.settings}</span>
          </button>
        </div>
      </header>

      {/* Wrapper do Conteúdo com Zoom Aplicado */}
      <div 
        id="lesson-zoom-container"
        
        className="transition-[zoom] duration-150 origin-top"
      >
      {/* ========================================================================= */}
      {/* 1. MODO LEITOR DE AULA (Imersivo, Legível, Tipografia Editorial de Livro) */}
      {/* ========================================================================= */}
      {activeTab === "reader" && (
        <div className="max-w-3xl mx-auto px-6 pt-10 sm:pt-14 space-y-10 animate-in fade-in duration-200">
          {/* Cabeçalho da Aula */}
          <div className="space-y-4 border-b border-[#222226] pb-8">
            <div className="flex items-center justify-between">
              <span className="text-xs font-black uppercase tracking-widest text-[#ffe500]">
                {lesson.module_title} • {lang === "en-US" ? "Lesson" : "Aula"} {lesson.lesson_number}
              </span>
              <span className="text-[11px] font-semibold text-neutral-400 bg-[#141416] border border-[#27272a] px-2.5 py-1 rounded-full">
                ~{readingTimeMin} {t.lesson_reading_time} • {wordCount} {t.lesson_words}
              </span>
            </div>

            <h1 className="text-3xl sm:text-4xl md:text-5xl font-black text-white leading-tight tracking-tight">
              {lesson.title}
            </h1>

            {/* Banner de Destaque da Sinopse / Tensão Dramática do Episódio */}
            <div className="bg-[#141416] border-l-4 border-[#ffe500] border-y border-r border-[#27272a] rounded-r-2xl p-4 sm:p-5">
              <span className="text-[11px] font-extrabold uppercase tracking-wider text-[#ffe500] block mb-1">
                {lang === "en-US" ? "Episode Synopsis" : "Sinopse do Episódio"}
              </span>
              <p className="text-sm sm:text-base font-semibold text-neutral-200 leading-relaxed">
                {lesson.core_concept}
              </p>
            </div>
          </div>

          {/* Corpo do Artigo / Apostila */}
          <article className="prose prose-invert max-w-none space-y-6">
            {lesson.content_markdown ? (
              <>
                <ReactMarkdown
                  remarkPlugins={[remarkMath]}
                  rehypePlugins={[rehypeKatex]}
                  components={{
                    code: ({ className, children, ...props }: React.ComponentPropsWithoutRef<"code">) => {
                      const match = /language-(\w+)/.exec(className || "");
                      const codeStr = String(children).replace(/\n$/, "");
                      const isBlock = Boolean(match) || codeStr.includes("\n");
                      if (isBlock) {
                        return <CodeBlock language={match ? match[1] : ""} code={codeStr} isEn={lang === "en-US"} />;
                      }
                      return (
                        <code className="bg-[#18181b] text-[#ffe500] border border-[#27272a] px-1.5 py-0.5 rounded text-sm font-mono" {...props}>
                          {children}
                        </code>
                      );
                    },
                    h1: ({ children }) => (
                      <h2 className="text-2xl sm:text-3xl font-black text-white mt-10 mb-4 pb-2 border-b border-[#222226] tracking-tight">
                        {cleanHeadingChildren(children)}
                      </h2>
                    ),
                    h2: ({ children }) => (
                      <h3 className="text-xl sm:text-2xl font-extrabold mt-10 mb-4 pb-2 border-b tracking-tight flex items-center space-x-2 text-white border-[#222226]">
                        <span>{cleanHeadingChildren(children)}</span>
                      </h3>
                    ),
                    h3: ({ children }) => (
                      <h4 className="text-lg font-bold text-[#ffe500] mt-6 mb-2">
                        {cleanHeadingChildren(children)}
                      </h4>
                    ),
                    p: ({ children }) => (
                      <p className="text-[17px] sm:text-[18px] text-[#d4d4d8] leading-[1.85] font-normal my-5 text-justify sm:text-left">
                        {enrichWithGlossary(children, glossaryMap, lang === "en-US")}
                      </p>
                    ),
                    strong: ({ children }) => (
                      <strong className="text-[#ffe500] font-black">
                        {enrichWithGlossary(children, glossaryMap, lang === "en-US")}
                      </strong>
                    ),
                    blockquote: ({ children }) => (
                      <blockquote className="border-l-4 border-[#ffe500] bg-[#141416] px-5 py-4 my-6 rounded-r-2xl text-neutral-200 text-base sm:text-lg italic leading-relaxed shadow-sm">
                        {enrichWithGlossary(children, glossaryMap, lang === "en-US")}
                      </blockquote>
                    ),
                    ul: ({ children }) => (
                      <ul className="my-5 pl-6 space-y-3 text-[17px] text-[#d4d4d8] list-disc marker:text-[#ffe500]">
                        {children}
                      </ul>
                    ),
                    ol: ({ children }) => (
                      <ol className="my-5 pl-6 space-y-2.5 text-[17px] text-[#d4d4d8] list-decimal">
                        {children}
                      </ol>
                    ),
                    li: ({ children }) => (
                      <li className="leading-relaxed">
                        {enrichWithGlossary(children, glossaryMap, lang === "en-US")}
                      </li>
                    ),
                    img: ({ src, alt }) => {
                      const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
                      const resolvedSrc = src?.startsWith("http")
                        ? src
                        : `${apiBase}${src?.startsWith("/") ? "" : "/"}${src || ""}`;

                      return (
                        <figure className="my-8 flex flex-col items-center">
                          <div className="w-full max-h-[460px] bg-[#0c0c0e] rounded-2xl border border-[#27272a] shadow-2xl overflow-hidden flex items-center justify-center p-2">
                            {/* eslint-disable-next-line @next/next/no-img-element */}
                            <img
                              src={resolvedSrc}
                              alt={alt || (lang === "en-US" ? "Technical stippling engraving" : "Gravura técnica em pontilhismo")}
                              className="max-h-[440px] w-full object-contain rounded-xl"
                              loading="lazy"
                              onError={(e) => {
                                const figure = e.currentTarget.closest("figure");
                                if (figure) figure.style.display = "none";
                              }}
                            />
                          </div>
                          {alt && (
                            <figcaption className="mt-3 text-center text-xs sm:text-sm text-neutral-400 italic max-w-xl">
                              {alt}
                            </figcaption>
                          )}
                        </figure>
                      );
                    },
                  }}
                >
                  {mainMarkdown}
                </ReactMarkdown>

                {/* Seção Estruturada e Elegante do Glossário da Aula */}
                {glossaryMarkdown && (
                  <div className="mt-14 pt-10 border-t border-[#222226]">
                    <div className="bg-[#121214] border border-[#27272a] rounded-3xl p-6 sm:p-8 shadow-xl space-y-6">
                      <div className="flex items-center space-x-3 pb-4 border-b border-[#222226]">
                        <div className="w-10 h-10 rounded-xl bg-[#ffe500]/10 border border-[#ffe500]/30 flex items-center justify-center">
                          <BookOpen className="w-5 h-5 text-[#ffe500]" />
                        </div>
                        <div>
                          <h3 className="text-xl sm:text-2xl font-black text-white">
                            {lang === "en-US" ? "Lesson Glossary" : "Glossário da Aula"}
                          </h3>
                          <p className="text-xs text-neutral-400">
                            {lang === "en-US" 
                              ? "Hover or tap on dotted terms in the text above to view inline explanations." 
                              : "Passe o mouse ou toque nos termos pontilhados no texto acima para ver estas explicações diretamente inline."}
                          </p>
                        </div>
                      </div>

                      <div className="space-y-3">
                        <ReactMarkdown
                          components={{
                            ul: ({ children }) => (
                              <ul className="space-y-3 pl-0 list-none my-0">
                                {children}
                              </ul>
                            ),
                            li: ({ children }) => {
                              let cleanedChildren = children;
                              if (Array.isArray(children)) {
                                cleanedChildren = children.map((c, idx) => {
                                  if (idx > 0 && typeof c === "string") {
                                    return c.replace(/^:\s*/, "");
                                  }
                                  return c;
                                });
                              }
                              return (
                                <li className="bg-[#18181b] border border-[#27272a] p-4 rounded-2xl text-[15px] sm:text-[16px] text-neutral-300 leading-relaxed">
                                  {cleanedChildren}
                                </li>
                              );
                            },
                            strong: ({ children }) => (
                              <strong className="text-[#ffe500] font-black mr-2 inline-block">
                                {children}:
                              </strong>
                            ),
                          }}
                        >
                          {glossaryMarkdown.replace(/^#{1,3}\s*(?:📖\s*)?Gloss[aá]rio[^\n]*\n+/i, "").replace(/^#{1,3}\s*Lesson\s+Glossary[^\n]*\n+/i, "")}
                        </ReactMarkdown>
                      </div>
                    </div>
                  </div>
                )}

                {/* Seção Separada com Mesmo Visual para Fontes e Leituras Recomendadas */}
                {sourcesMarkdown && (
                  <div className="mt-8">
                    <div className="bg-[#121214] border border-[#27272a] rounded-3xl p-6 sm:p-8 shadow-xl space-y-6">
                      <div className="flex items-center space-x-3 pb-4 border-b border-[#222226]">
                        <div className="w-10 h-10 rounded-xl bg-[#ffe500]/10 border border-[#ffe500]/30 flex items-center justify-center">
                          <Bookmark className="w-5 h-5 text-[#ffe500]" />
                        </div>
                        <div>
                          <h3 className="text-xl sm:text-2xl font-black text-white">
                            {lang === "en-US" ? "Lesson References & Readings" : "Referências e Leituras da Aula"}
                          </h3>
                          <p className="text-xs sm:text-sm text-neutral-400">
                            {lang === "en-US" 
                              ? "Core book, recommended readings, and sources supporting this lesson." 
                              : "Livro base e fontes de pesquisa que fundamentam os conceitos desta aula."}
                          </p>
                        </div>
                      </div>

                      <div className="space-y-3.5">
                        {parsedSources.length > 0 ? (
                          parsedSources.map((source, idx) => (
                            <div 
                              key={idx} 
                              className="bg-[#18181b] border border-[#27272a] p-4 sm:p-5 rounded-2xl space-y-2.5 transition-colors hover:border-[#3f3f46]"
                            >
                              <div className="flex flex-wrap items-center justify-between gap-2">
                                <h4 className="text-base sm:text-lg font-bold text-white leading-snug">
                                  {source.title}
                                </h4>
                                <div className="flex items-center gap-1.5 flex-wrap">
                                  {source.isBook && (
                                    <span className="text-[11px] font-semibold text-[#ffe500] bg-[#ffe500]/10 border border-[#ffe500]/25 px-2.5 py-0.5 rounded-full">
                                      {lang === "en-US" ? "Core Reference" : "Livro Base"}
                                    </span>
                                  )}
                                  {source.tag && !source.tag.toLowerCase().includes("arquivo local") && (
                                    <span className="text-[11px] font-semibold text-neutral-300 bg-[#222226] border border-[#2e2e33] px-2.5 py-0.5 rounded-full">
                                      {source.tag}
                                    </span>
                                  )}
                                </div>
                              </div>

                              {source.description && (
                                <p className="text-[14px] sm:text-[15px] text-neutral-300 leading-relaxed">
                                  {source.description}
                                </p>
                              )}

                              {source.url && (
                                <div className="pt-1">
                                  <a 
                                    href={source.url} 
                                    target="_blank" 
                                    rel="noopener noreferrer" 
                                    className="inline-flex items-center gap-1.5 text-xs sm:text-sm font-semibold text-[#ffe500] hover:text-[#fff066] hover:underline"
                                  >
                                    <span>{lang === "en-US" ? "Access source" : "Acessar fonte"}</span>
                                    <ExternalLink className="w-3.5 h-3.5 flex-shrink-0" />
                                  </a>
                                </div>
                              )}
                            </div>
                          ))
                        ) : (
                          <ReactMarkdown
                            components={{
                              ul: ({ children }) => (
                                <ul className="space-y-3 pl-0 list-none my-0">
                                  {children}
                                </ul>
                              ),
                              li: ({ children }) => (
                                <li className="bg-[#18181b] border border-[#27272a] p-4 sm:p-5 rounded-2xl text-[15px] sm:text-[16px] text-neutral-300 leading-relaxed space-y-1.5">
                                  {children}
                                </li>
                              ),
                              a: ({ href, children }) => (
                                <div className="space-y-1">
                                  <span className="font-bold text-white text-base sm:text-lg block leading-snug">
                                    {children}
                                  </span>
                                  {href && (
                                    <a 
                                      href={href} 
                                      target="_blank" 
                                      rel="noopener noreferrer" 
                                      className="inline-flex items-center gap-1.5 text-xs sm:text-sm font-semibold text-[#ffe500] hover:underline"
                                    >
                                      <span>{lang === "en-US" ? "Access source" : "Acessar fonte"}</span>
                                      <ExternalLink className="w-3.5 h-3.5 flex-shrink-0 ml-1" />
                                    </a>
                                  )}
                                </div>
                              ),
                            }}
                          >
                            {sourcesMarkdown.replace(/^#{1,3}\s*(?:📚\s*)?Fontes[^\n]*\n+/i, "").replace(/^#{1,3}\s*(?:Lesson\s+)?Sources[^\n]*\n+/i, "")}
                          </ReactMarkdown>
                        )}
                      </div>
                    </div>
                  </div>
                )}
              </>
            ) : (
              <div className="text-center py-16 text-neutral-500">
                <BookOpen className="w-10 h-10 mx-auto mb-3 text-neutral-600 animate-pulse" />
                <p className="text-sm font-medium">
                  {lang === "en-US" 
                    ? "Textbook is being prepared by the writer agent..." 
                    : "Apostila em processamento pelo agente redator..."}
                </p>
              </div>
            )}
          </article>

          {/* Cartão de Transição para os Desafios Práticos (Fim da Aula) */}
          <div className="mt-14 pt-8 border-t border-[#222226]">
            <div className="bg-gradient-to-b from-[#141416] to-[#121214] border-2 border-[#27272a] rounded-3xl p-6 sm:p-10 text-center space-y-6 shadow-xl">
              <div className="w-14 h-14 rounded-2xl bg-[#ffe500]/10 border border-[#ffe500]/30 mx-auto flex items-center justify-center">
                <Target className="w-7 h-7 text-[#ffe500]" />
              </div>

              <div className="max-w-md mx-auto space-y-2">
                <h3 className="text-2xl font-black text-white">
                  {lang === "en-US" ? "Time to test your knowledge" : "Hora de testar seu conhecimento"}
                </h3>
                <p className="text-sm sm:text-base text-neutral-200 font-medium leading-relaxed">
                  {lang === "en-US" 
                    ? "You've seen the theory. Now solve the problems and see how you perform in practice." 
                    : "A teoria você já viu. Agora resolva os problemas e veja como você se sai na prática."}
                </p>
              </div>

              <div className="flex flex-wrap items-center justify-center gap-4 text-xs font-semibold text-neutral-300">
                <span className="flex items-center space-x-1.5 bg-[#1a1a1e] px-3 py-1.5 rounded-lg border border-[#27272a]">
                  <span className="w-2 h-2 rounded-full bg-[#ffe500]" />
                  <span>{lang === "en-US" ? "3 Questions" : "3 Questões"}</span>
                </span>
                <span className="flex items-center space-x-1.5 bg-[#1a1a1e] px-3 py-1.5 rounded-lg border border-[#27272a]">
                  <span className="w-2 h-2 rounded-full bg-[#ffe500]" />
                  <span>{lang === "en-US" ? "Scenario Simulation" : "Simulação de Cenários"}</span>
                </span>
                <span className="flex items-center space-x-1.5 bg-[#1a1a1e] px-3 py-1.5 rounded-lg border border-[#27272a]">
                  <span className="w-2 h-2 rounded-full bg-[#ffe500]" />
                  <span>Mini Case</span>
                </span>
              </div>

              <div>
                <button
                  onClick={switchToQuiz}
                  className="bg-[#ffe500] hover:bg-[#fff000] text-black font-black px-8 py-4 rounded-2xl text-sm sm:text-base flex items-center justify-center space-x-3 mx-auto shadow-lg shadow-[#ffe500]/10 hover:shadow-[#ffe500]/25 transition-all transform hover:-translate-y-0.5 cursor-pointer"
                >
                  <span>{lang === "en-US" ? "Apply Knowledge" : "Aplicar conhecimentos"}</span>
                  <ArrowRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* 2. MODO QUESTIONÁRIO / VERIFICAÇÃO SOCRÁTICA (Foco Total nas Questões)     */}
      {/* ========================================================================= */}
      {activeTab === "quiz" && (
        <div className="max-w-3xl mx-auto px-6 pt-8 sm:pt-12 space-y-8 animate-in fade-in duration-200">
          {/* Barra Superior de Retorno à Leitura */}
          <div className="bg-[#141416] border border-[#27272a] rounded-2xl p-4 sm:p-5 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 rounded-xl bg-[#ffe500]/10 border border-[#ffe500]/20 flex items-center justify-center shrink-0">
                <ShieldCheck className="w-5 h-5 text-[#ffe500]" />
              </div>
              <div>
                <h2 className="text-base font-extrabold text-white">
                  {lang === "en-US" ? "Mastery Assessment" : "Verificação de Aprendizado"}
                </h2>
                <p className="text-xs text-neutral-400">
                  {lesson.module_title} • {lang === "en-US" ? "Lesson" : "Aula"} {lesson.lesson_number}
                </p>
              </div>
            </div>

            {/* Botão de Retorno à Apostila para consulta */}
            <button
              onClick={switchToReader}
              className="flex items-center space-x-2 bg-[#1f1f23] hover:bg-[#28282e] border border-[#333338] text-white px-4 py-2 rounded-xl text-xs font-bold transition-all self-stretch sm:self-auto justify-center cursor-pointer"
            >
              <RotateCcw className="w-3.5 h-3.5 text-[#ffe500]" />
              <span>{lang === "en-US" ? "Back to Textbook" : "Voltar para Ler a Aula"}</span>
            </button>
          </div>

          {quiz ? (
            <div className="space-y-8">
              {/* PARTE 1: MÚLTIPLA ESCOLHA (MCQs) */}
              <section className="bg-[#121214] border border-[#27272a] rounded-3xl p-6 sm:p-8 space-y-6 shadow-xl">
                <div className="border-b border-[#222226] pb-4">
                  <span className="text-xs font-bold uppercase tracking-wider text-[#ffe500] block">
                    {lang === "en-US" ? "Part 1 of 3" : "Parte 1 de 3"}
                  </span>
                  <h3 className="text-xl font-black text-white mt-1">
                    {lang === "en-US" ? `Multiple Choice Questions (${quiz.mcq.length} Questions)` : `Questões de Múltipla Escolha (${quiz.mcq.length} Questões)`}
                  </h3>
                  <p className="text-xs text-neutral-400 mt-1">
                    {lang === "en-US" 
                      ? `Select the single correct option based strictly on the lesson text. (Minimum: ${minMcqRequired} correct)` 
                      : `Selecione a única alternativa correta baseando-se estritamente no texto da aula. (Mínimo: ${minMcqRequired} acertos)`}
                  </p>
                </div>

                <div className="space-y-6">
                  {quiz.mcq.map((q, qIdx) => (
                    <div key={qIdx} className="bg-[#18181b] p-5 rounded-2xl border border-[#27272a] space-y-3">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-extrabold text-[#ffe500]">
                          {lang === "en-US" ? `Question ${qIdx + 1} of ${quiz.mcq.length}` : `Questão ${qIdx + 1} de ${quiz.mcq.length}`}
                        </span>
                        {mcqAnswers[String(qIdx)] && (
                          <span className="text-[10px] uppercase font-bold text-neutral-400 bg-[#222226] px-2 py-0.5 rounded">
                            {lang === "en-US" ? "Answered" : "Respondida"}
                          </span>
                        )}
                      </div>

                      <p className="text-sm font-semibold text-white leading-relaxed">
                        {q.question}
                      </p>

                      <div className="space-y-2 pt-2">
                        {q.options.map((opt) => {
                          const isSelected = mcqAnswers[String(qIdx)] === opt.label;
                          const optionDisplay = opt.text && opt.text !== opt.label ? opt.text : (lang === "en-US" ? `Option ${opt.label}` : `Alternativa ${opt.label}`);
                          
                          // Estilização após submissão do gabarito:
                          // Se foi avaliado e o usuário passou, destaca a correta em verde
                          let optionClasses = "bg-[#1f1f23] text-neutral-300 border-[#2b2b30] hover:border-neutral-500 hover:bg-[#25252a]";
                          let badgeClasses = "bg-[#27272a] text-neutral-300";

                          if (mcqResult) {
                            if (opt.is_correct) {
                              optionClasses = "bg-green-950/40 text-green-200 border-green-600/60 font-semibold shadow-sm";
                              badgeClasses = "bg-green-600 text-black font-black";
                            } else if (isSelected && !opt.is_correct) {
                              optionClasses = "bg-red-950/30 text-red-300 border-red-800/60 font-medium";
                              badgeClasses = "bg-red-900 text-white font-bold";
                            }
                          } else if (isSelected) {
                            optionClasses = "bg-[#ffe500] text-black border-[#ffe500] font-bold shadow-md";
                            badgeClasses = "bg-black text-[#ffe500]";
                          }

                          return (
                            <button
                              key={opt.label}
                              disabled={Boolean(mcqResult && mcqResult.mcq_passed)}
                              onClick={() => setMcqAnswers({ ...mcqAnswers, [String(qIdx)]: opt.label })}
                              className={`w-full text-left px-4 py-3 rounded-xl border text-xs sm:text-sm flex items-start space-x-3 transition-all cursor-pointer ${optionClasses}`}
                            >
                              <span className={`w-6 h-6 rounded-lg flex items-center justify-center font-extrabold shrink-0 uppercase text-xs ${badgeClasses}`}>
                                {opt.label}
                              </span>
                              <span className="pt-0.5 leading-relaxed">{optionDisplay}</span>
                            </button>
                          );
                        })}
                      </div>

                      {/* Explicação Didática após verificação */}
                      {mcqResult && q.explanation && (
                        <div className="mt-3 p-3.5 rounded-xl bg-[#141416] border border-[#2e2e33] text-xs text-neutral-300 space-y-1 animate-in fade-in duration-150">
                          <span className="text-[10px] font-bold text-[#ffe500] uppercase tracking-wider block">
                            {lang === "en-US" ? "Explanation:" : "Gabarito Comentado:"}
                          </span>
                          <p className="leading-relaxed font-normal text-neutral-300">{q.explanation}</p>
                        </div>
                      )}
                    </div>
                  ))}
                </div>

                {/* Se a aula for antiga e ainda tiver fill_in_the_blanks e não tiver simulation */}
                {!quiz.simulation && quiz.fill_in_the_blanks && quiz.fill_in_the_blanks.length > 0 && (
                  <div className="pt-4 border-t border-[#222226] space-y-4">
                    <span className="text-xs font-bold text-[#ffe500] uppercase tracking-wider block">
                      {lang === "en-US" ? "Fill in the Blanks (Legacy)" : "Preenchimento de Lacunas (Legado)"}
                    </span>
                    {quiz.fill_in_the_blanks.map((b, bIdx) => (
                      <div key={bIdx} className="bg-[#18181b] p-5 rounded-2xl border border-[#27272a] space-y-3">
                        <p className="text-sm text-neutral-200 font-medium leading-relaxed">
                          {renderFormattedBlankSentence(b.sentence_with_blank)}
                        </p>
                        <input
                          type="text"
                          placeholder={lang === "en-US" ? "Type exact term..." : "Digite o termo exato..."}
                          value={blankAnswers[String(bIdx)] || ""}
                          onChange={(e) => setBlankAnswers({ ...blankAnswers, [String(bIdx)]: e.target.value })}
                          className="w-full bg-[#141416] border border-[#27272a] focus:border-[#ffe500] rounded-xl px-4 py-3 text-sm text-white outline-none font-semibold transition-colors"
                        />
                      </div>
                    ))}
                  </div>
                )}

                {/* Botão de Envio das Questões Objetivas */}
                <div className="pt-2">
                  <button
                    onClick={handleMcqSubmit}
                    disabled={isSubmittingMcq}
                    className="w-full bg-[#ffe500] hover:bg-[#fff000] text-black font-black py-3.5 rounded-xl text-sm transition-all disabled:opacity-40 shadow-lg shadow-[#ffe500]/10 hover:shadow-[#ffe500]/20 cursor-pointer"
                  >
                    {isSubmittingMcq 
                      ? (lang === "en-US" ? "Checking Answers..." : "Verificando Gabarito...") 
                      : (lang === "en-US" ? "Check Multiple Choice Answers" : "Verificar Gabarito das Questões Objetivas")}
                  </button>

                  {mcqResult && (
                    <div className={`mt-4 p-4 rounded-xl text-xs sm:text-sm font-bold flex items-center space-x-3 border ${
                      mcqResult.mcq_passed 
                        ? "bg-green-950/60 text-green-300 border-green-800/60" 
                        : "bg-red-950/60 text-red-300 border-red-800/60"
                    }`}>
                      {mcqResult.mcq_passed ? (
                        <CheckCircle className="w-5 h-5 text-green-400 shrink-0" />
                      ) : (
                        <RotateCcw className="w-5 h-5 text-red-400 shrink-0" />
                      )}
                      <div>
                        <p>{mcqResult.message}</p>
                        {!mcqResult.mcq_passed && (
                          <p className="text-[11px] text-neutral-400 font-normal mt-0.5">
                            {lang === "en-US"
                              ? `You need at least ${minMcqRequired} correct answers to complete this stage. You may review the textbook and try again.`
                              : `Você precisa de pelo menos ${minMcqRequired} acertos para concluir esta etapa. Você pode voltar à apostila e tentar novamente.`}
                          </p>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              </section>

              {/* PARTE 2: SIMULAÇÃO - ESTRUTURA MINIMALISTA GAMIFICADA */}
              {quiz.simulation && (() => {
                const currentLevel: PerformanceLevel = simTurn2
                  ? getPerformanceFromIndicators(simTurn2.final_indicators || simTurn2.updated_indicators, simTurn2.is_success)
                  : simTurn1
                  ? getPerformanceFromIndicators(simTurn1.updated_indicators)
                  : "neutro";

                const isFailure = currentLevel === "pessimo" || currentLevel === "ruim";

                return (
                  <section className="bg-[#121214] border border-[#27272a] rounded-3xl p-6 sm:p-7 space-y-6 shadow-2xl relative overflow-hidden">
                    {/* 1. Linha Superior: Título à esquerda + Traços sutis de etapa à direita */}
                    <div className="flex items-center justify-between gap-4">
                      <div>
                        <span className="text-xs font-black uppercase tracking-wider text-[#ffe500] block">
                          {lang === "en-US" ? "PART 2 OF 3" : "PARTE 2 DE 3"}
                        </span>
                        <h3 className="text-xl md:text-2xl font-black text-white mt-1 tracking-tight">
                          {lang === "en-US" ? "Simulation" : "Simulação"}
                        </h3>
                      </div>

                      {/* Traços sutis de progresso das 4 etapas (0: Cenário, 1: Turno 1, 2: Turno 2, 3: Desfecho) */}
                      <div className="flex items-center space-x-1.5 shrink-0" title={lang === "en-US" ? `Step ${simSlide + 1} of 4` : `Etapa ${simSlide + 1} de 4`}>
                        {[0, 1, 2, 3].map((step) => {
                          const isCurrent = simSlide === step;
                          const isPast = simSlide > step;
                          return (
                            <button
                              key={step}
                              disabled={step > (simTurn2 ? 3 : simTurn1 ? 2 : 1)}
                              onClick={() => setSimSlide(step)}
                              className={`h-[2.5px] rounded-full transition-all cursor-pointer ${
                                isCurrent
                                  ? "w-6 bg-[#ffe500] shadow-[0_0_8px_rgba(255,229,0,0.4)]"
                                  : isPast
                                  ? "w-6 bg-neutral-600 hover:bg-neutral-400"
                                  : "w-6 bg-[#27272a] opacity-40 cursor-not-allowed"
                              }`}
                            />
                          );
                        })}
                      </div>
                    </div>

                    {/* 2. Régua de Performance em 5 Blocos (Sempre Visível) */}
                    {renderPerformanceBar(currentLevel, simSlide === 0, lang)}

                    {/* 3. Container de Slides com Altura Controlada */}
                    <div className="relative min-h-[220px] flex flex-col justify-center">
                      {/* SLIDE 0: Cenário Inicial */}
                      {simSlide === 0 && (
                        <div className="space-y-5 animate-in fade-in duration-200">
                          <div className="space-y-2.5">
                            <span className="text-xs font-mono text-[#ffe500] uppercase tracking-wider block font-bold">
                              {lang === "en-US" ? "SCENARIO" : "CENÁRIO"}
                            </span>
                            <p className="text-sm sm:text-base text-neutral-100 leading-relaxed font-normal">
                              {quiz.simulation.context_description || quiz.simulation.context}
                            </p>
                          </div>

                          <div className="flex justify-end pt-2">
                            <button
                              onClick={() => setSimSlide(1)}
                              className="bg-[#ffe500] hover:bg-[#fff000] text-black font-extrabold px-4 py-2 rounded-xl text-xs transition-all shadow-md cursor-pointer flex items-center space-x-1.5"
                            >
                              <span>{lang === "en-US" ? "Start Simulation" : "Iniciar Simulação"}</span>
                              <span className="text-sm font-bold">&rarr;</span>
                            </button>
                          </div>
                        </div>
                      )}

                      {/* SLIDE 1: Turno 1 (Primeira Decisão) */}
                      {simSlide === 1 && (
                        <div className="space-y-4 animate-in fade-in slide-in-from-right-4 duration-200">
                          <p className="text-sm sm:text-base text-neutral-100 font-normal leading-relaxed">
                            {quiz.simulation.turn1_prompt}
                          </p>

                          <div className="space-y-3">
                            {quiz.simulation.turn1_options.map((opt) => (
                              <button
                                key={opt.id}
                                onClick={() => handleSelectSimTurn1(opt)}
                                className="w-full text-left p-4 rounded-2xl bg-[#18181b] hover:bg-[#202025] border border-[#27272a] hover:border-[#ffe500]/60 transition-all duration-150 cursor-pointer flex items-start space-x-3.5 group"
                              >
                                <span className="text-xs font-mono text-neutral-400 group-hover:text-[#ffe500] transition-colors pt-0.5 shrink-0 font-bold">
                                  {opt.id}
                                </span>
                                <span className="text-xs sm:text-sm text-neutral-200 group-hover:text-white transition-colors leading-relaxed font-normal">
                                  {opt.text || opt.action_label}
                                </span>
                              </button>
                            ))}
                          </div>

                          <div className="pt-2 flex justify-start">
                            <button
                              onClick={() => setSimSlide(0)}
                              className="text-xs text-neutral-500 hover:text-neutral-300 transition-colors cursor-pointer flex items-center space-x-1"
                            >
                              <ChevronLeft className="w-4 h-4" />
                              <span>{lang === "en-US" ? "View Scenario" : "Ver Cenário"}</span>
                            </button>
                          </div>
                        </div>
                      )}

                      {/* SLIDE 2: Turno 2 (Desdobramento da Primeira Decisão + Segunda Pergunta) */}
                      {simSlide === 2 && simTurn1 && (
                        <div className="space-y-4 animate-in fade-in slide-in-from-right-4 duration-200">
                          <div className="p-4 rounded-2xl bg-[#18181b] border border-[#27272a] space-y-1.5">
                            <span className="text-xs font-mono text-neutral-400 uppercase tracking-wider block font-semibold">
                              {lang === "en-US" ? "Outcome of the First Decision" : "Desdobramento da Primeira Decisão"}
                            </span>
                            <p className="text-xs sm:text-sm text-neutral-200 leading-relaxed font-normal">
                              {simTurn1.reaction_story}
                              {simTurn1.collateral_effect ? ` ${simTurn1.collateral_effect}` : ""}
                            </p>
                          </div>

                          <p className="text-sm sm:text-base text-neutral-100 font-normal leading-relaxed pt-1">
                            {simTurn1.turn2_prompt}
                          </p>

                          <div className="space-y-3">
                            {simTurn1.turn2_options.map((opt2) => (
                              <button
                                key={opt2.id}
                                disabled={isSubmittingSim}
                                onClick={() => handleSelectSimTurn2(opt2)}
                                className="w-full text-left p-4 rounded-2xl bg-[#18181b] hover:bg-[#202025] border border-[#27272a] hover:border-[#ffe500]/60 transition-all duration-150 cursor-pointer flex items-start space-x-3.5 group disabled:opacity-50"
                              >
                                <span className="text-xs font-mono text-neutral-400 group-hover:text-[#ffe500] transition-colors pt-0.5 shrink-0 font-bold">
                                  {opt2.id}
                                </span>
                                <span className="text-xs sm:text-sm text-neutral-200 group-hover:text-white transition-colors leading-relaxed font-normal">
                                  {opt2.text || opt2.action_label}
                                </span>
                              </button>
                            ))}
                          </div>

                          <div className="pt-2 flex justify-start">
                            <button
                              onClick={() => setSimSlide(1)}
                              className="text-xs text-neutral-500 hover:text-neutral-300 transition-colors cursor-pointer flex items-center space-x-1"
                            >
                              <ChevronLeft className="w-4 h-4" />
                              <span>{lang === "en-US" ? "Back to Turn 1" : "Voltar ao Turno 1"}</span>
                            </button>
                          </div>
                        </div>
                      )}

                      {/* SLIDE 3: Desfecho Final (FEEDBACK Unificado sem Selos Prolixos) */}
                      {simSlide === 3 && simTurn2 && (
                        <div className="space-y-5 animate-in fade-in duration-200">
                          <div className="space-y-2.5">
                            <span className="text-xs font-black uppercase tracking-wider text-neutral-400 font-mono block">
                              FEEDBACK
                            </span>
                            <p className="text-sm sm:text-base text-neutral-100 leading-relaxed font-normal">
                              {simTurn2.verdict_summary || simTurn2.operation_scorecard || simTurn2.outcome_story}
                              {simTurn2.trade_off_analysis ? ` ${simTurn2.trade_off_analysis}` : ""}
                            </p>
                          </div>

                          <div className="pt-4 border-t border-[#222226] flex items-center justify-between">
                            <span className="text-xs text-neutral-500">
                              {isFailure
                                ? (lang === "en-US" ? "Simulation ended with warnings" : "Simulação encerrada com ressalvas")
                                : (lang === "en-US" ? "Simulation successfully completed" : "Simulação concluída com sucesso")}
                            </span>
                            <button
                              onClick={handleResetSimulation}
                              className="text-xs text-neutral-400 hover:text-[#ffe500] bg-[#18181b] border border-[#27272a] px-3.5 py-2 rounded-xl transition-colors cursor-pointer font-bold"
                            >
                              {isFailure
                                ? (lang === "en-US" ? "Try Again" : "Tentar Novamente")
                                : (lang === "en-US" ? "Test Another Path" : "Testar Outro Caminho")}
                            </button>
                          </div>
                        </div>
                      )}
                    </div>
                  </section>
                );
              })()}

              {/* PARTE 3: ESTUDO DE CASO INTERATIVO (ANÁLISE E RESOLUÇÃO COM A IA) */}
              {(quiz.socratic_duel || quiz.discursive) && (
                <section className="glass-panel rounded-3xl p-6 sm:p-8 space-y-6 shadow-2xl relative overflow-hidden">
                  <div className="border-b border-[#222226] pb-4">
                    <div className="text-xs font-black uppercase tracking-wider text-[#ffe500]">
                      <span>{lang === "en-US" ? "PART 3 OF 3" : "PARTE 3 DE 3"}</span>
                    </div>
                    <h3 className="text-xl md:text-2xl font-black text-white mt-1 tracking-tight">
                      {quiz.socratic_duel?.dilemma_title || (lang === "en-US" ? "Interactive Case Study" : "Estudo de Caso Prático")}
                    </h3>
                    <p className="text-xs text-neutral-400 mt-1 font-normal leading-relaxed">
                      {lang === "en-US"
                        ? "Analyze the practical situation, present your solution, and receive immediate AI tutor feedback with trade-off analysis."
                        : "Analise a situação prática, apresente sua solução e receba feedback imediato do tutor com análise de trade-offs."}
                    </p>
                  </div>

                  {/* Dilema Formatado em Cartões e Parágrafos Arejados em Vidro */}
                  <div className="glass-panel-scenario p-6 rounded-2xl space-y-3">
                    <span className="text-xs font-mono font-bold uppercase text-[#ffe500] tracking-wider block">
                      {lang === "en-US" ? "SCENARIO" : "CENÁRIO"}
                    </span>
                    {renderStructuredDilemma(
                      quiz.socratic_duel?.question || quiz.discursive?.question || "",
                      quiz.socratic_duel?.image_url,
                      quiz.socratic_duel?.image_caption,
                      lang === "en-US"
                    )}
                  </div>

                  {/* Formulário de Resposta Limpo e Descomplicado */}
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <span className="w-5 h-5 rounded-full bg-[#1e1e26] border border-neutral-700 text-[#ffe500] text-xs font-black flex items-center justify-center">
                          1
                        </span>
                        <span className="text-xs font-bold text-neutral-200">
                          {lang === "en-US" ? "How would you solve this?" : "Como você resolveria?"}
                        </span>
                      </div>
                      {cognitiveKnot && (
                        <span className="text-[10px] font-bold text-emerald-400 bg-emerald-950/40 px-2.5 py-0.5 rounded border border-emerald-800/40">
                          {lang === "en-US" ? "Answer Evaluated" : "Resposta Avaliada"}
                        </span>
                      )}
                    </div>

                    <textarea
                      rows={4}
                      disabled={Boolean(cognitiveKnot) || socraticPassed}
                      placeholder={lang === "en-US" ? "Explain which approach you would adopt and why..." : "Explique qual abordagem você adotaria e o porquê..."}
                      value={socraticRound1Answer}
                      onChange={(e) => setSocraticRound1Answer(e.target.value)}
                      className="glass-panel-input w-full rounded-2xl p-4 text-sm text-white outline-none font-normal leading-relaxed placeholder:text-neutral-500 transition-colors"
                    />

                    {!cognitiveKnot && !socraticPassed && (
                      <button
                        onClick={handleSocraticRound1Submit}
                        disabled={isSubmittingSocratic || !socraticRound1Answer.trim()}
                        className="w-full bg-[#ffe500] hover:bg-[#fff000] text-black font-extrabold py-3.5 rounded-2xl text-xs sm:text-sm flex items-center justify-center space-x-2 transition-all disabled:opacity-40 shadow-lg shadow-[#ffe500]/10 hover:shadow-[#ffe500]/20 cursor-pointer"
                      >
                        <Send className="w-4 h-4" />
                        <span>
                          {isSubmittingSocratic
                            ? (lang === "en-US" ? "Evaluating response..." : "Avaliando resposta...")
                            : (lang === "en-US" ? "Submit Response" : "Enviar Resposta")}
                        </span>
                      </button>
                    )}

                    {socraticFeedback1 && (
                      <div className="p-4 rounded-xl bg-[#161622]/80 border border-white/[0.08] text-xs text-neutral-300 space-y-1 backdrop-blur-md">
                        <span className="text-[11px] font-bold text-[#ffe500] uppercase block">
                          {lang === "en-US" ? "Tutor Feedback:" : "Feedback do Tutor:"}
                        </span>
                        <p className="leading-relaxed font-normal">{socraticFeedback1}</p>
                      </div>
                    )}
                  </div>

                  {/* DESAFIO DE CENÁRIO (O Contra-argumento do Tutor) */}
                  {cognitiveKnot && (
                    <div className="space-y-4 pt-2 animate-in fade-in slide-in-from-top-3 duration-200">
                      <div className="bg-amber-950/20 border border-amber-500/30 p-5 rounded-2xl space-y-2 backdrop-blur-md shadow-lg">
                        <div className="flex items-center space-x-2 text-amber-300 font-black text-xs uppercase tracking-wider">
                          <Flame className="w-4 h-4 text-amber-400" />
                          <span>{lang === "en-US" ? "Scenario Challenge (Adverse Condition)" : "Desafio de Cenário (Situação Adversa)"}</span>
                        </div>
                        <p className="text-sm font-normal text-neutral-100 leading-relaxed">
                          {cognitiveKnot}
                        </p>
                      </div>

                      {/* PASSO 2: Adaptação Estratégica */}
                      <div className="space-y-3 pt-2">
                        <div className="flex items-center space-x-2">
                          <span className="w-5 h-5 rounded-full bg-[#1e1e26] border border-neutral-700 text-[#ffe500] text-xs font-black flex items-center justify-center">
                            2
                          </span>
                          <span className="text-xs font-bold text-neutral-200">
                            {lang === "en-US" ? "How do you adjust the plan now?" : "Como você ajusta o plano agora?"}
                          </span>
                        </div>

                        <textarea
                          rows={3}
                          disabled={socraticPassed}
                          placeholder={lang === "en-US" ? "Explain how you would handle this change..." : "Explique como você lidaria com essa mudança..."}
                          value={socraticRound2Answer}
                          onChange={(e) => setSocraticRound2Answer(e.target.value)}
                          className="glass-panel-input w-full rounded-2xl p-4 text-sm text-white outline-none font-normal leading-relaxed placeholder:text-neutral-500 transition-colors"
                        />

                        {!socraticPassed && (
                          <button
                            onClick={handleSocraticRound2Submit}
                            disabled={isSubmittingSocratic || !socraticRound2Answer.trim()}
                            className="w-full bg-[#ffe500] hover:bg-[#fff000] text-black font-extrabold py-3.5 rounded-2xl text-xs sm:text-sm flex items-center justify-center space-x-2 transition-all disabled:opacity-40 shadow-lg shadow-[#ffe500]/10 hover:shadow-[#ffe500]/20 cursor-pointer"
                          >
                            <CheckCircle2 className="w-4 h-4" />
                            <span>
                              {isSubmittingSocratic
                                ? (lang === "en-US" ? "Concluding evaluation..." : "Concluindo avaliação...")
                                : (lang === "en-US" ? "Submit Reply & Conclude Case" : "Enviar Resposta e Concluir Caso")}
                            </span>
                          </button>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Veredito Final do Duelo Socrático em Vidro */}
                  {socraticResult && (
                    <div className={`p-5 rounded-2xl text-xs sm:text-sm space-y-3 border backdrop-blur-md ${
                      socraticResult.passed
                        ? "bg-emerald-950/20 text-emerald-300 border-emerald-500/30"
                        : "bg-rose-950/20 text-rose-300 border-rose-500/30"
                    }`}>
                      <div className="flex justify-between items-center font-black text-sm">
                        <span className="flex items-center space-x-2">
                          <CheckCircle2 className="w-4 h-4" />
                          <span>
                            {socraticResult.passed
                              ? (lang === "en-US" ? "SOCRATIC DUEL MASTERED WITH HONORS!" : "ESTUDO DE CASO CONCLUÍDO COM SUCESSO!")
                              : (lang === "en-US" ? "INCOMPLETE REPLY" : "RESPOSTA INCOMPLETA")}
                          </span>
                        </span>
                        <span className="bg-black/40 px-3 py-1 rounded-lg font-mono">
                          {lang === "en-US" ? "Score:" : "Nota:"} {socraticResult.score}/10
                        </span>
                      </div>
                      <p className="text-neutral-200 leading-relaxed font-normal whitespace-pre-line">
                        {socraticResult.feedback}
                      </p>
                    </div>
                  )}
                </section>
              )}

              {/* CARD FINAL DE STATUS DA AULA */}
              {isLessonCompleted && (
                <div className="bg-green-950/40 border-2 border-green-700/60 rounded-3xl p-6 sm:p-8 text-center space-y-4 animate-in fade-in zoom-in-95 duration-200">
                  <CheckCircle className="w-12 h-12 text-green-400 mx-auto" />
                  <h3 className="text-2xl font-black text-white">
                    {lang === "en-US" ? "Congratulations! Lesson Mastered with Excellence!" : "Parabéns! Aula Concluída com Maestria!"}
                  </h3>
                  <p className="text-xs sm:text-sm text-neutral-300 max-w-md mx-auto">
                    {lang === "en-US"
                      ? "You mastered the objective questions, tested operational trade-offs in the Simulator, and overcame the Socratic Duel. The next step is unlocked!"
                      : "Você dominou as questões objetivas, testou as consequências operacionais no Mini-Simulador e superou o Duelo Socrático. A próxima etapa está desbloqueada!"}
                  </p>
                  <button
                    onClick={() => router.back()}
                    className="bg-green-500 hover:bg-green-400 text-black font-black px-6 py-3 rounded-xl text-sm transition-all cursor-pointer"
                  >
                    {lang === "en-US" ? "Return to Course Track" : "Voltar à Trilha do Curso"}
                  </button>
                </div>
              )}
            </div>
          ) : (
            <div className="text-center py-16 text-neutral-500">
              <ShieldCheck className="w-10 h-10 mx-auto mb-3 text-neutral-600 animate-pulse" />
              <p className="text-sm font-medium">
                {lang === "en-US" ? "Assessments being prepared by AI..." : "Testes em elaboração pela IA..."}
              </p>
            </div>
          )}
        </div>
      )}
      </div>

      {/* Tutor de IA Flutuante e Persistente da Aula (Split Screen) */}
      {lesson && (
        <LessonTutorChat 
          lesson={lesson} 
          isOpen={isTutorChatOpen}
          onOpen={() => setIsTutorChatOpen(true)}
          onClose={() => setIsTutorChatOpen(false)}
        />
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
