"use client";

import React, { useState, useEffect } from "react";
import { createPortal } from "react-dom";
import {
  Settings,
  Image as ImageIcon,
  Cpu,
  CheckCircle2,
  AlertCircle,
  Save,
  Sparkles,
  Zap,
  Copy,
  Check,
  Activity,
  ChevronDown,
  ChevronUp,
  ExternalLink,
  ShieldCheck,
  Lock,
  Layers,
  Sliders,
  Server,
  Terminal,
  ArrowLeft
} from "lucide-react";
import { SupportedLanguage } from "@/lib/i18n";
import {
  getSettings,
  updateSettings,
  runFreeModelsBenchmark,
  testLocalConnection,
  SettingsData,
  SettingsUpdateData,
  BenchmarkResult,
  LocalConnectionTestResult
} from "@/lib/api";

// --- LOGOS OFICIAIS VETORIAIS DE ALTA DEFINIÇÃO ---

function OpenRouterLogo({ className = "w-5 h-5" }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
      <path
        d="M16.778 1.844v1.919q-.569-.026-1.138-.032-.708-.008-1.415.037c-1.93.126-4.023.728-6.149 2.237-2.911 2.066-2.731 1.95-4.14 2.75-.396.223-1.342.574-2.185.798-.841.225-1.753.333-1.751.333v4.229s.768.108 1.61.333c.842.224 1.789.575 2.185.799 1.41.798 1.228.683 4.14 2.75 2.126 1.509 4.22 2.11 6.148 2.236.88.058 1.716.041 2.555.005v1.918l7.222-4.168-7.222-4.17v2.176c-.86.038-1.611.065-2.278.021-1.364-.09-2.417-.357-3.979-1.465-2.244-1.593-2.866-2.027-3.68-2.508.889-.518 1.449-.906 3.822-2.59 1.56-1.109 2.614-1.377 3.978-1.466.667-.044 1.418-.017 2.278.02v2.176L24 6.014Z"
        fill="#6366F1"
      />
    </svg>
  );
}

function OpenAILogo({ className = "w-5 h-5" }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
      <path
        d="M22.2819 9.8211a5.9847 5.9847 0 0 0-.5157-4.9108 6.0462 6.0462 0 0 0-6.5098-2.9A6.0651 6.0651 0 0 0 4.9807 4.1818a5.9847 5.9847 0 0 0-3.9977 2.9 6.0462 6.0462 0 0 0 .7427 7.0966 5.98 5.98 0 0 0 .511 4.9107 6.051 6.051 0 0 0 6.5146 2.9001A5.9847 5.9847 0 0 0 13.2599 24a6.0557 6.0557 0 0 0 5.7718-4.2058 5.9894 5.9894 0 0 0 3.9977-2.9001 6.0557 6.0557 0 0 0-.7475-7.0729zm-9.022 12.6081a4.4755 4.4755 0 0 1-2.8764-1.0408l.1419-.0804 4.7783-2.7582a.7948.7948 0 0 0 .3927-.6813v-6.7369l2.02 1.1686a.071.071 0 0 1 .038.052v5.5826a4.504 4.504 0 0 1-4.4945 4.4944zm-9.6607-4.1254a4.4708 4.4708 0 0 1-.5346-3.0137l.142.0852 4.783 2.7582a.7712.7712 0 0 0 .7806 0l5.8428-3.3685v2.3324a.0804.0804 0 0 1-.0332.0615L9.74 19.9502a4.4992 4.4992 0 0 1-6.1408-1.6464zM2.3408 7.8956a4.485 4.485 0 0 1 2.3655-1.9728V11.6a.7664.7664 0 0 0 .3879.6765l5.8144 3.3543-2.0201 1.1685a.0757.0757 0 0 1-.071 0l-4.8303-2.7865A4.504 4.504 0 0 1 2.3408 7.872zm16.5963 3.8558L13.1038 8.364 15.1192 7.2a.0757.0757 0 0 1 .071 0l4.8303 2.7913a4.4944 4.4944 0 0 1-.6765 8.1042v-5.6772a.79.79 0 0 0-.407-.667zm2.0107-3.0231l-.142-.0852-4.7735-2.7818a.7759.7759 0 0 0-.7854 0L9.409 9.2297V6.8974a.0662.0662 0 0 1 .0284-.0615l4.8303-2.7866a4.4992 4.4992 0 0 1 6.6802 4.66zM8.3065 12.863l-2.02-1.1638a.0804.0804 0 0 1-.038-.0567V6.0742a4.4992 4.4992 0 0 1 7.3757-3.4537l-.142.0805L8.704 5.459a.7948.7948 0 0 0-.3927.6813zm1.0976-2.3654l2.602-1.4998 2.6069 1.4998v2.9994l-2.5974 1.4997-2.6067-1.4997Z"
        fill="#10A37F"
      />
    </svg>
  );
}

function ClaudeLogo({ className = "w-5 h-5" }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
      <path
        d="m4.7144 15.9555 4.7174-2.6471.079-.2307-.079-.1275h-.2307l-.7893-.0486-2.6956-.0729-2.3375-.0971-2.2646-.1214-.5707-.1215-.5343-.7042.0546-.3522.4797-.3218.686.0608 1.5179.1032 2.2767.1578 1.6514.0972 2.4468.255h.3886l.0546-.1579-.1336-.0971-.1032-.0972L6.973 9.8356l-2.55-1.6879-1.3356-.9714-.7225-.4918-.3643-.4614-.1578-1.0078.6557-.7225.8803.0607.2246.0607.8925.686 1.9064 1.4754 2.4893 1.8336.3643.3035.1457-.1032.0182-.0728-.164-.2733-1.3539-2.4467-1.445-2.4893-.6435-1.032-.17-.6194c-.0607-.255-.1032-.4674-.1032-.7285L6.287.1335 6.6997 0l.9957.1336.419.3642.6192 1.4147 1.0018 2.2282 1.5543 3.0296.4553.8985.2429.8318.091.255h.1579v-.1457l.1275-1.706.2368-2.0947.2307-2.6957.0789-.7589.3764-.9107.7468-.4918.5828.2793.4797.686-.0668.4433-.2853 1.8517-.5586 2.9021-.3643 1.9429h.2125l.2429-.2429.9835-1.3053 1.6514-2.0643.7286-.8196.85-.9046.5464-.4311h1.0321l.759 1.1293-.34 1.1657-1.0625 1.3478-.8804 1.1414-1.2628 1.7-.7893 1.36.0729.1093.1882-.0183 2.8535-.607 1.5421-.2794 1.8396-.3157.8318.3886.091.3946-.3278.8075-1.967.4857-2.3072.4614-3.4364.8136-.0425.0304.0486.0607 1.5482.1457.6618.0364h1.621l3.0175.2247.7892.522.4736.6376-.079.4857-1.2142.6193-1.6393-.3886-3.825-.9107-1.3113-.3279h-.1822v.1093l1.0929 1.0686 2.0035 1.8092 2.5075 2.3314.1275.5768-.3218.4554-.34-.0486-2.2039-1.6575-.85-.7468-1.9246-1.621h-.1275v.17l.4432.6496 2.3436 3.5214.1214 1.0807-.17.3521-.6071.2125-.6679-.1214-1.3721-1.9246L14.38 17.959l-1.1414-1.9428-.1397.079-.674 7.2552-.3156.3703-.7286.2793-.6071-.4614-.3218-.7468.3218-1.4753.3886-1.9246.3157-1.53.2853-1.9004.17-.6314-.0121-.0425-.1397.0182-1.4328 1.9672-2.1796 2.9446-1.7243 1.8456-.4128.164-.7164-.3704.0667-.6618.4008-.5889 2.386-3.0357 1.4389-1.882.929-1.0868-.0062-.1579h-.0546l-6.3385 4.1164-1.1293.1457-.4857-.4554.0608-.7467.2307-.2429 1.9064-1.3114Z"
        fill="#D97757"
      />
    </svg>
  );
}

function FluxLogo({ className = "w-5 h-5" }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <rect x="3" y="3" width="8" height="8" rx="2" fill="#FFE500" />
      <rect x="13" y="3" width="8" height="8" rx="2" fill="#FFE500" fillOpacity="0.4" />
      <rect x="3" y="13" width="8" height="8" rx="2" fill="#FFE500" fillOpacity="0.4" />
      <rect x="13" y="13" width="8" height="8" rx="2" fill="#FFE500" />
    </svg>
  );
}

function GeminiSparkleLogo({ className = "w-5 h-5" }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path
        d="M12 2C12 7.5 7.5 12 2 12C7.5 12 12 16.5 12 22C12 16.5 16.5 12 22 12C16.5 12 12 7.5 12 2Z"
        fill="url(#gemini_grad)"
      />
      <defs>
        <linearGradient id="gemini_grad" x1="2" y1="2" x2="22" y2="22" gradientUnits="userSpaceOnUse">
          <stop stopColor="#4285F4" />
          <stop offset="0.5" stopColor="#9B72CB" />
          <stop offset="1" stopColor="#D96570" />
        </linearGradient>
      </defs>
    </svg>
  );
}

function FalLogo({ className = "w-5 h-5" }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 512 512" xmlns="http://www.w3.org/2000/svg" fillRule="evenodd" clipRule="evenodd" strokeLinejoin="round" strokeMiterlimit="2">
      <g transform="scale(32)">
        <path d="M10.318 0c.277 0 .5.225.525.501A5.199 5.199 0 0015.5 5.157c.275.027.501.249.501.526v4.634a.542.542 0 01-.501.526 5.199 5.199 0 00-4.657 4.656.542.542 0 01-.525.501H5.683a.542.542 0 01-.526-.501 5.2 5.2 0 00-4.656-4.656.542.542 0 01-.501-.526V5.683c0-.277.225-.499.501-.526A5.2 5.2 0 005.157.501.543.543 0 015.684 0h4.634zM3.213 7.987v.002c0 2.642 2.173 4.816 4.815 4.818 2.642-.002 4.815-2.176 4.815-4.818v-.002a4.817 4.817 0 00-4.815-4.82c-2.643.001-4.817 2.177-4.815 4.82z" fill="#ec0648" />
      </g>
    </svg>
  );
}

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  lang?: SupportedLanguage;
}

export default function SettingsModal({ isOpen, onClose, lang }: SettingsModalProps) {
  const isEn = lang === "en-US" || (typeof window !== "undefined" && localStorage.getItem("trivium_ui_lang") === "en-US");
  const [mounted, setMounted] = useState(false);
  const [activeTab, setActiveTab] = useState<"llm" | "images">("llm");
  const [loading, setLoading] = useState<boolean>(true);
  const [saving, setSaving] = useState<boolean>(false);
  const [saveSuccess, setSaveSuccess] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Benchmark state (teste exclusivo Trivium)
  const [benchmarking, setBenchmarking] = useState<boolean>(false);
  const [benchmarkResult, setBenchmarkResult] = useState<BenchmarkResult | null>(null);
  const [benchmarkError, setBenchmarkError] = useState<string | null>(null);
  const [copied, setCopied] = useState<boolean>(false);
  const [showRejected, setShowRejected] = useState<boolean>(false);

  // Settings state
  const [settings, setSettings] = useState<SettingsData | null>(null);

  // LLM states
  const [llmProvider, setLlmProvider] = useState<"openrouter" | "openai" | "anthropic" | "local">("openrouter");
  const [openrouterKey, setOpenrouterKey] = useState<string>("");
  const [openaiKey, setOpenaiKey] = useState<string>("");
  const [anthropicKey, setAnthropicKey] = useState<string>("");
  const [openrouterModels, setOpenrouterModels] = useState<string>("");
  const [openaiModels, setOpenaiModels] = useState<string>("gpt-4o-mini, gpt-4o, o3-mini");
  const [anthropicModels, setAnthropicModels] = useState<string>("claude-3-5-sonnet-20241022, claude-3-5-haiku-20241022, claude-3-7-sonnet-20250219");
  const [localBaseUrl, setLocalBaseUrl] = useState<string>("http://localhost:11434/v1");
  const [localModels, setLocalModels] = useState<string>("llama3.1:latest, qwen2.5:14b, deepseek-r1:8b, mistral:latest");
  const [localApiKey, setLocalApiKey] = useState<string>("");

  // Local Connection Test states
  const [testingConnection, setTestingConnection] = useState<boolean>(false);
  const [connectionTestResult, setConnectionTestResult] = useState<LocalConnectionTestResult | null>(null);

  // Image states
  const [imageProvider, setImageProvider] = useState<string>("openai");
  const [imageAspectRatio, setImageAspectRatio] = useState<"1:1" | "16:9" | "4:3">("1:1");
  const [imageQuality, setImageQuality] = useState<"standard" | "hd">("standard");
  const [imageModel, setImageModel] = useState<string>("dall-e-3");
  const [falKey, setFalKey] = useState<string>("");
  const [hfToken, setHfToken] = useState<string>("");
  const [geminiKey, setGeminiKey] = useState<string>("");

  useEffect(() => {
    setMounted(true);
  }, []);

  const handleSelectImageProvider = async (providerId: string) => {
    setImageProvider(providerId);
    let chosenModel = imageModel;
    if (providerId === "openai" && (!imageModel || imageModel.includes("flux") || imageModel.includes("imagen"))) {
      chosenModel = "dall-e-3";
      setImageModel("dall-e-3");
    } else if (providerId === "fal" && (!imageModel || imageModel.includes("dall-e") || imageModel.includes("imagen"))) {
      chosenModel = "fal-ai/flux/schnell";
      setImageModel("fal-ai/flux/schnell");
    } else if (providerId === "google" && (!imageModel || imageModel.includes("dall-e") || imageModel.includes("flux"))) {
      chosenModel = "imagen-3.0-generate-002";
      setImageModel("imagen-3.0-generate-002");
    } else if (providerId === "huggingface" && (!imageModel || imageModel.includes("dall-e") || imageModel.includes("imagen"))) {
      chosenModel = "black-forest-labs/FLUX.1-schnell";
      setImageModel("black-forest-labs/FLUX.1-schnell");
    }
    try {
      const updated = await updateSettings({ image_provider: providerId, image_model: chosenModel });
      setSettings(updated);
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 2500);
    } catch (err: unknown) {
      console.error("Falha ao salvar provedor de imagem automaticamente:", err);
    }
  };

  const handleSelectLlmProvider = async (provider: "openrouter" | "openai" | "anthropic" | "local") => {
    setLlmProvider(provider);
    setError(null);
    try {
      const updated = await updateSettings({ llm_provider: provider });
      setSettings(updated);
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 2500);
    } catch (err: unknown) {
      console.error("Falha ao salvar provedor de IA automaticamente:", err);
    }
  };

  useEffect(() => {
    if (!isOpen) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onClose();
      }
    };

    const origOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    window.addEventListener("keydown", handleKeyDown);
    return () => {
      window.removeEventListener("keydown", handleKeyDown);
      document.body.style.overflow = origOverflow;
    };
  }, [isOpen, onClose]);

  useEffect(() => {
    if (isOpen) {
      setLoading(true);
      setError(null);
      setSaveSuccess(false);
      getSettings()
        .then((data) => {
          setSettings(data);
          setImageProvider(data.image_provider || "openai");
          setImageAspectRatio((data.image_aspect_ratio as "1:1" | "16:9" | "4:3") || "1:1");
          setImageQuality((data.image_quality as "standard" | "hd") || (data.image_quality === "fast" ? "standard" : "standard"));
          setImageModel(data.image_model || "dall-e-3");
          const prov = (data.llm_provider as string) || "openrouter";
          setLlmProvider(prov === "ollama" ? "local" : (prov as "openrouter" | "openai" | "anthropic" | "local"));
          setOpenaiModels(data.openai_models || (data as unknown as { openai_model?: string }).openai_model || "gpt-4o-mini, gpt-4o, o3-mini");
          setAnthropicModels(data.anthropic_models || (data as unknown as { anthropic_model?: string }).anthropic_model || "claude-3-5-sonnet-20241022, claude-3-5-haiku-20241022, claude-3-7-sonnet-20250219");
          setOpenrouterModels(data.openrouter_models || "");
          setLocalBaseUrl(data.local_base_url || "http://localhost:11434/v1");
          setLocalModels(data.local_models || "llama3.1:latest, qwen2.5:14b, deepseek-r1:8b, mistral:latest");
          setLoading(false);
        })
        .catch((err) => {
          console.error("Erro ao carregar configurações:", err);
          setError("Não foi possível carregar as configurações do servidor.");
          setLoading(false);
        });
    }
  }, [isOpen]);

  const handleSave = async () => {
    setError(null);
    setSaveSuccess(false);

    // REGRA DE VALIDAÇÃO ESTREITA: A chave de API deve ser obrigatória para o provedor em primeiro lugar (preferência)
    if (llmProvider === "openrouter") {
      const hasKey = settings?.has_openrouter_api_key || openrouterKey.trim().length > 0;
      if (!hasKey) {
        setError("A chave da API do OpenRouter (OPENROUTER_API_KEY) é obrigatória quando o OpenRouter está selecionado como preferência principal.");
        setActiveTab("llm");
        return;
      }
    } else if (llmProvider === "openai") {
      const hasKey = settings?.has_openai_api_key || openaiKey.trim().length > 0;
      if (!hasKey) {
        setError("A chave da API da OpenAI (OPENAI_API_KEY) é obrigatória quando a OpenAI (ChatGPT) está selecionada como preferência principal.");
        setActiveTab("llm");
        return;
      }
    } else if (llmProvider === "anthropic") {
      const hasKey = settings?.has_anthropic_api_key || anthropicKey.trim().length > 0;
      if (!hasKey) {
        setError("A chave da API da Anthropic (ANTHROPIC_API_KEY) é obrigatória quando o Claude está selecionado como preferência principal.");
        setActiveTab("llm");
        return;
      }
    }

    setSaving(true);

    const payload: SettingsUpdateData = {
      image_provider: imageProvider,
      image_aspect_ratio: imageAspectRatio,
      image_quality: imageQuality,
      image_model: imageModel.trim(),
      llm_provider: llmProvider,
      openai_models: openaiModels.trim(),
      anthropic_models: anthropicModels.trim(),
      openrouter_models: openrouterModels.trim(),
      local_base_url: localBaseUrl.trim(),
      local_models: localModels.trim(),
    };

    if (falKey.trim()) payload.fal_api_key = falKey.trim();
    if (hfToken.trim()) payload.hf_token = hfToken.trim();
    if (geminiKey.trim()) payload.gemini_api_key = geminiKey.trim();
    if (openaiKey.trim()) payload.openai_api_key = openaiKey.trim();
    if (openrouterKey.trim()) payload.openrouter_api_key = openrouterKey.trim();
    if (anthropicKey.trim()) payload.anthropic_api_key = anthropicKey.trim();
    if (localApiKey.trim()) payload.local_api_key = localApiKey.trim();

    try {
      const updated = await updateSettings(payload);
      setSettings(updated);
      setFalKey("");
      setHfToken("");
      setGeminiKey("");
      setOpenaiKey("");
      setOpenrouterKey("");
      setAnthropicKey("");
      setLocalApiKey("");
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Falha ao salvar configurações";
      setError(msg);
    } finally {
      setSaving(false);
    }
  };

  const handleTestLocalConnection = async () => {
    setTestingConnection(true);
    setConnectionTestResult(null);
    try {
      const res = await testLocalConnection(localBaseUrl.trim(), localApiKey.trim() || undefined);
      setConnectionTestResult(res);
      if (res.online && res.models && res.models.length > 0) {
        const currentList = localModels.split(",").map((s) => s.trim()).filter(Boolean);
        const combined = Array.from(new Set([...res.models, ...currentList])).join(", ");
        setLocalModels(combined);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Falha ao testar conexão com o servidor local";
      setConnectionTestResult({
        online: false,
        provider_detected: "offline",
        base_url: localBaseUrl.trim(),
        models: [],
        latency_ms: 0,
        error: msg,
        message: "Certifique-se de que o Ollama ('ollama serve') ou LM Studio está rodando.",
      });
    } finally {
      setTestingConnection(false);
    }
  };

  const handleRunBenchmark = async () => {
    setBenchmarking(true);
    setBenchmarkError(null);
    try {
      const res = await runFreeModelsBenchmark();
      setBenchmarkResult(res);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Falha ao executar benchmark";
      setBenchmarkError(msg);
    } finally {
      setBenchmarking(false);
    }
  };

  const handleApplyRecommended = () => {
    if (benchmarkResult?.recommended_csv) {
      setOpenrouterModels(benchmarkResult.recommended_csv);
    }
  };

  const handleCopyRecommended = () => {
    if (benchmarkResult?.recommended_csv) {
      navigator.clipboard.writeText(benchmarkResult.recommended_csv);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  if (!isOpen || !mounted) return null;

  return createPortal(
    <div
      data-trivium-modal="true"
      className="fixed inset-0 z-[100] bg-[#09090b] text-white flex flex-col overflow-hidden animate-in fade-in duration-200"
    >
      {/* 1. TOP BAR (HEADER FIXO) */}
      <header className="relative h-16 shrink-0 border-b border-[#222226] bg-[#111114] px-6 sm:px-10 flex items-center justify-between z-10">
        {/* Left: Back button & Title */}
        <div className="flex items-center space-x-4 z-10">
          <button
            onClick={onClose}
            className="h-10 flex items-center space-x-2 text-xs sm:text-sm font-semibold text-neutral-300 hover:text-white bg-[#18181c] hover:bg-[#222228] border border-[#2e2e34] px-3.5 rounded-xl transition-all"
            title={isEn ? "Back / Close (ESC)" : "Voltar / Fechar (ESC)"}
          >
            <ArrowLeft className="w-4 h-4 shrink-0" />
            <span className="hidden sm:inline">{isEn ? "Back" : "Voltar"}</span>
            <kbd className="hidden md:inline-flex items-center justify-center px-1.5 py-0.5 text-[10px] font-mono text-neutral-400 bg-[#121215] border border-[#2e2e34] rounded leading-none">
              ESC
            </kbd>
          </button>

          <div className="h-6 w-px bg-[#27272a] hidden sm:block" />

          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-[#ffe500]/10 border border-[#ffe500]/30 flex items-center justify-center text-[#ffe500] shrink-0">
              <Settings className="w-5 h-5" />
            </div>
            <div className="flex flex-col justify-center">
              <h1 className="text-sm sm:text-base font-bold text-white tracking-wide leading-tight">
                {isEn ? "Trivium Settings" : "Configurações do Trivium"}
              </h1>
              <p className="text-xs text-neutral-400 hidden md:block leading-tight mt-0.5">
                {isEn ? "AI models and image generation providers" : "Provedores de inteligência artificial e geração de imagens"}
              </p>
            </div>
          </div>
        </div>

        {/* Center: Tabs (perfeitamente centralizadas no meio da tela) */}
        <div className="absolute left-1/2 -translate-x-1/2 top-1/2 -translate-y-1/2 hidden md:flex items-center bg-[#18181c] border border-[#27272a] p-1 rounded-xl h-10 gap-1 z-0">
          <button
            type="button"
            onClick={() => setActiveTab("llm")}
            className={`h-8 flex items-center space-x-2 px-4 rounded-lg text-xs sm:text-sm font-bold transition-all ${
              activeTab === "llm"
                ? "bg-[#ffe500] text-black shadow-sm"
                : "text-neutral-400 hover:text-white"
            }`}
          >
            <Cpu className="w-4 h-4 shrink-0" />
            <span>{isEn ? "AI Models" : "Modelos de IA"}</span>
          </button>
          <button
            type="button"
            onClick={() => setActiveTab("images")}
            className={`h-8 flex items-center space-x-2 px-4 rounded-lg text-xs sm:text-sm font-bold transition-all ${
              activeTab === "images"
                ? "bg-[#ffe500] text-black shadow-sm"
                : "text-neutral-400 hover:text-white"
            }`}
          >
            <ImageIcon className="w-4 h-4 shrink-0" />
            <span>{isEn ? "Illustrations & Images" : "Ilustrações & Imagens"}</span>
          </button>
        </div>

        {/* Right: Save Action */}
        <div className="flex items-center space-x-3 z-10">
          <button
            type="button"
            onClick={handleSave}
            disabled={saving || loading}
            className="h-10 flex items-center space-x-2 bg-[#ffe500] hover:bg-[#ffe500]/90 text-black font-bold text-xs sm:text-sm px-5 rounded-xl transition-all disabled:opacity-50 shadow-md shadow-[#ffe500]/10"
          >
            {saving ? (
              <>
                <div className="w-4 h-4 border-2 border-black border-t-transparent rounded-full animate-spin shrink-0" />
                <span>{isEn ? "Saving..." : "Salvando..."}</span>
              </>
            ) : (
              <>
                <Save className="w-4 h-4 shrink-0" />
                <span>{isEn ? "Save Changes" : "Salvar Alterações"}</span>
              </>
            )}
          </button>
        </div>
      </header>

      {/* 2. ÁREA PRINCIPAL FULLSCREEN COM SCROLL SUAVE */}
      <main className="flex-1 overflow-y-auto">
        <div className="max-w-5xl mx-auto px-6 sm:px-10 py-8 sm:py-10 space-y-8">
          {loading ? (
            <div className="py-24 flex flex-col items-center justify-center space-y-3 text-neutral-400">
              <div className="w-8 h-8 border-2 border-[#ffe500] border-t-transparent rounded-full animate-spin" />
              <p className="text-sm font-medium">{isEn ? "Loading system settings..." : "Carregando configurações do sistema..."}</p>
            </div>
          ) : (
            <>
              {error && (
                <div className="p-4 bg-red-950/40 border border-red-800/60 rounded-2xl text-red-200 text-sm flex items-center space-x-3">
                  <AlertCircle className="w-5 h-5 shrink-0 text-red-400" />
                  <span>{error}</span>
                </div>
              )}

              {saveSuccess && (
                <div className="p-4 bg-emerald-950/40 border border-emerald-800/60 rounded-2xl text-emerald-200 text-sm flex items-center space-x-3">
                  <CheckCircle2 className="w-5 h-5 shrink-0 text-emerald-400" />
                  <span className="font-semibold">{isEn ? "Settings saved and applied successfully!" : "Configurações salvas e aplicadas com sucesso!"}</span>
                </div>
              )}

              {/* ========================================================================= */}
              {/* ABA 1: MODELOS DE IA (LLMS) */}
              {/* ========================================================================= */}
              {activeTab === "llm" && (
                <div className="space-y-8">
                  {/* Seletor de Provedor Prioritário */}
                  <div className="space-y-3">
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1">
                      <div>
                        <h2 className="text-sm sm:text-base font-black uppercase tracking-wider text-neutral-200">
                          {isEn ? "Primary AI Provider" : "Provedor de IA Prioritário"}
                        </h2>
                        <p className="text-xs text-neutral-400">
                          {isEn 
                            ? "Select the primary engine responsible for pedagogical synthesis, simulators, and quizzes." 
                            : "Selecione o motor principal responsável pela síntese pedagógica, simuladores e quizzes."}
                        </p>
                      </div>
                      <span className="text-xs text-amber-400/90 flex items-center space-x-1.5 font-medium">
                        <Lock className="w-3.5 h-3.5" />
                        <span>{isEn ? "Key required for selected provider" : "Chave obrigatória para o provedor selecionado"}</span>
                      </span>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                      {/* OpenRouter Card */}
                      <button
                        type="button"
                        onClick={() => handleSelectLlmProvider("openrouter")}
                        className={`p-5 rounded-2xl border text-left transition-all flex flex-col justify-between space-y-4 ${
                          llmProvider === "openrouter"
                            ? "bg-[#6366F1]/10 border-[#818CF8] shadow-lg shadow-[#6366F1]/15 ring-1 ring-[#818CF8]"
                            : "bg-[#141417] border-[#27272a] hover:border-neutral-500"
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <div className="w-9 h-9 rounded-xl bg-[#1e1e26] border border-[#2e2e38] flex items-center justify-center">
                            <OpenRouterLogo className="w-5 h-5" />
                          </div>
                          {llmProvider === "openrouter" && (
                            <span className="text-[10px] px-2 py-0.5 rounded-full bg-[#6366F1] text-white font-bold uppercase tracking-wider">
                              {isEn ? "Primary" : "1º Lugar"}
                            </span>
                          )}
                        </div>
                        <div className="space-y-1">
                          <h3 className="font-bold text-sm sm:text-base text-white">OpenRouter</h3>
                          <p className="text-xs text-neutral-300 leading-relaxed">
                            {isEn
                              ? "Access dozens of free (:free) and premium models with a single unified key."
                              : "Acesso a dezenas de modelos gratuitos (:free) e pagos com chave unificada."}
                          </p>
                        </div>
                        <div className="pt-2 border-t border-[#222228] flex items-center justify-between text-xs">
                          {settings?.has_openrouter_api_key ? (
                            <span className="text-emerald-400 font-medium flex items-center space-x-1.5">
                              <CheckCircle2 className="w-3.5 h-3.5" />
                              <span>{isEn ? "Key active" : "Chave ativa"}</span>
                            </span>
                          ) : (
                            <span className="text-amber-400/90 font-medium flex items-center space-x-1.5">
                              <AlertCircle className="w-3.5 h-3.5" />
                              <span>{isEn ? "Requires key" : "Requer chave"}</span>
                            </span>
                          )}
                          <span className="text-neutral-500 font-mono text-[11px]">:free & pro</span>
                        </div>
                      </button>

                      {/* OpenAI Card */}
                      <button
                        type="button"
                        onClick={() => handleSelectLlmProvider("openai")}
                        className={`p-5 rounded-2xl border text-left transition-all flex flex-col justify-between space-y-4 ${
                          llmProvider === "openai"
                            ? "bg-[#10A37F]/10 border-[#10A37F] shadow-lg shadow-[#10A37F]/15 ring-1 ring-[#10A37F]"
                            : "bg-[#141417] border-[#27272a] hover:border-neutral-500"
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <div className="w-9 h-9 rounded-xl bg-[#1e1e26] border border-[#2e2e38] flex items-center justify-center">
                            <OpenAILogo className="w-5 h-5" />
                          </div>
                          {llmProvider === "openai" && (
                            <span className="text-[10px] px-2 py-0.5 rounded-full bg-[#10A37F] text-white font-bold uppercase tracking-wider">
                              {isEn ? "Primary" : "1º Lugar"}
                            </span>
                          )}
                        </div>
                        <div className="space-y-1">
                          <h3 className="font-bold text-sm sm:text-base text-white">OpenAI (ChatGPT)</h3>
                          <p className="text-xs text-neutral-300 leading-relaxed">
                            {isEn
                              ? "Official GPT-4o and o3-mini models. Maximum speed and structured precision."
                              : "Modelos oficiais GPT-4o e o3-mini. Máxima velocidade e precisão estruturada."}
                          </p>
                        </div>
                        <div className="pt-2 border-t border-[#222228] flex items-center justify-between text-xs">
                          {settings?.has_openai_api_key ? (
                            <span className="text-emerald-400 font-medium flex items-center space-x-1.5">
                              <CheckCircle2 className="w-3.5 h-3.5" />
                              <span>{isEn ? "Key active" : "Chave ativa"}</span>
                            </span>
                          ) : (
                            <span className="text-amber-400/90 font-medium flex items-center space-x-1.5">
                              <AlertCircle className="w-3.5 h-3.5" />
                              <span>{isEn ? "Requires key" : "Requer chave"}</span>
                            </span>
                          )}
                          <span className="text-neutral-500 font-mono text-[11px]">GPT-4o</span>
                        </div>
                      </button>

                      {/* Anthropic Card */}
                      <button
                        type="button"
                        onClick={() => handleSelectLlmProvider("anthropic")}
                        className={`p-5 rounded-2xl border text-left transition-all flex flex-col justify-between space-y-4 ${
                          llmProvider === "anthropic"
                            ? "bg-[#D97757]/10 border-[#D97757] shadow-lg shadow-[#D97757]/15 ring-1 ring-[#D97757]"
                            : "bg-[#141417] border-[#27272a] hover:border-neutral-500"
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <div className="w-9 h-9 rounded-xl bg-[#1e1e26] border border-[#2e2e38] flex items-center justify-center">
                            <ClaudeLogo className="w-5 h-5" />
                          </div>
                          {llmProvider === "anthropic" && (
                            <span className="text-[10px] px-2 py-0.5 rounded-full bg-[#D97757] text-white font-bold uppercase tracking-wider">
                              {isEn ? "Primary" : "1º Lugar"}
                            </span>
                          )}
                        </div>
                        <div className="space-y-1">
                          <h3 className="font-bold text-sm sm:text-base text-white">Anthropic (Claude)</h3>
                          <p className="text-xs text-neutral-300 leading-relaxed">
                            {isEn
                              ? "Claude 3.5 Sonnet and 3.7. Deep reasoning, humanized prose, and editorial nuance."
                              : "Claude 3.5 Sonnet e 3.7. Raciocínio aprofundado e escrita refinada."}
                          </p>
                        </div>
                        <div className="pt-2 border-t border-[#222228] flex items-center justify-between text-xs">
                          {settings?.has_anthropic_api_key ? (
                            <span className="text-emerald-400 font-medium flex items-center space-x-1.5">
                              <CheckCircle2 className="w-3.5 h-3.5" />
                              <span>{isEn ? "Key active" : "Chave ativa"}</span>
                            </span>
                          ) : (
                            <span className="text-amber-400/90 font-medium flex items-center space-x-1.5">
                              <AlertCircle className="w-3.5 h-3.5" />
                              <span>{isEn ? "Requires key" : "Requer chave"}</span>
                            </span>
                          )}
                          <span className="text-neutral-500 font-mono text-[11px]">Sonnet 3.5</span>
                        </div>
                      </button>

                      {/* Local / Ollama Card */}
                      <button
                        type="button"
                        onClick={() => handleSelectLlmProvider("local")}
                        className={`p-5 rounded-2xl border text-left transition-all flex flex-col justify-between space-y-4 ${
                          llmProvider === "local"
                            ? "bg-amber-500/10 border-amber-500 shadow-lg shadow-amber-500/15 ring-1 ring-amber-500"
                            : "bg-[#141417] border-[#27272a] hover:border-neutral-500"
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <div className="w-9 h-9 rounded-xl bg-[#1e1e26] border border-[#2e2e38] flex items-center justify-center">
                            <Server className="w-5 h-5 text-amber-400" />
                          </div>
                          {llmProvider === "local" && (
                            <span className="text-[10px] px-2 py-0.5 rounded-full bg-amber-500 text-black font-bold uppercase tracking-wider">
                              {isEn ? "Primary" : "1º Lugar"}
                            </span>
                          )}
                        </div>
                        <div className="space-y-1">
                          <h3 className="font-bold text-sm sm:text-base text-white">Local / Ollama</h3>
                          <p className="text-xs text-neutral-300 leading-relaxed">
                            {isEn
                              ? "100% offline and private execution via Ollama or LM Studio on your machine."
                              : "Execução 100% offline e privada via Ollama ou LM Studio na máquina."}
                          </p>
                        </div>
                        <div className="pt-2 border-t border-[#222228] flex items-center justify-between text-xs">
                          <span className="text-emerald-400 font-medium flex items-center space-x-1.5">
                            <CheckCircle2 className="w-3.5 h-3.5" />
                            <span>{isEn ? "Zero Cost" : "Zero Custo"}</span>
                          </span>
                          <span className="text-neutral-500 font-mono text-[11px]">localhost</span>
                        </div>
                      </button>
                    </div>
                  </div>

                  {/* Contextual Settings for Selected Provider */}
                  <div className="p-6 sm:p-8 rounded-2xl bg-[#131317] border border-[#27272a] space-y-6">
                    {/* OPENROUTER */}
                    {llmProvider === "openrouter" && (
                      <div className="space-y-6">
                        <div className="space-y-2">
                          <div className="flex items-center justify-between">
                            <label className="text-sm font-bold text-neutral-200 flex items-center space-x-2">
                              <OpenRouterLogo className="w-4 h-4" />
                              <span>{isEn ? "OpenRouter API Key" : "Chave de API do OpenRouter"}</span>
                              <span className="text-red-400">*</span>
                            </label>
                            {settings?.has_openrouter_api_key ? (
                              <span className="text-xs text-emerald-400 font-medium flex items-center space-x-1.5">
                                <CheckCircle2 className="w-3.5 h-3.5" />
                                <span>
                                  {isEn
                                    ? `Connected (${settings.openrouter_api_key_preview})`
                                    : `Conectado (${settings.openrouter_api_key_preview})`}
                                </span>
                              </span>
                            ) : (
                              <span className="text-xs text-amber-400/90 font-medium flex items-center space-x-1.5">
                                <AlertCircle className="w-3.5 h-3.5" />
                                <span>{isEn ? "Required to save" : "Obrigatória para salvar"}</span>
                              </span>
                            )}
                          </div>
                          <input
                            type="password"
                            placeholder={
                              settings?.has_openrouter_api_key
                                ? isEn
                                  ? "Replace existing key (sk-or-v1-...)"
                                  : "Substituir chave existente (sk-or-v1-...)"
                                : isEn
                                ? "Enter your OPENROUTER_API_KEY (sk-or-v1-...)"
                                : "Insira sua OPENROUTER_API_KEY (sk-or-v1-...)"
                            }
                            value={openrouterKey}
                            onChange={(e) => setOpenrouterKey(e.target.value)}
                            className="w-full h-12 bg-[#0c0c0e] border border-[#2c2c34] rounded-xl px-4 text-sm text-white placeholder-neutral-500 focus:outline-none focus:border-[#818CF8]"
                          />
                        </div>

                        <div className="space-y-2">
                          <div className="flex items-center justify-between">
                            <label className="text-sm font-bold text-neutral-200 uppercase tracking-wider">
                              {isEn ? "Model Pool (Fallback Order)" : "Pool de Modelos (Ordem de Fallback)"}
                            </label>
                            <span className="text-xs text-neutral-400">
                              {isEn ? "Comma separated" : "Separados por vírgula"}
                            </span>
                          </div>
                          <textarea
                            rows={3}
                            value={openrouterModels}
                            onChange={(e) => setOpenrouterModels(e.target.value)}
                            placeholder="google/gemini-2.0-flash-exp:free, meta-llama/llama-3.3-70b-instruct:free"
                            className="w-full bg-[#0c0c0e] border border-[#2c2c34] rounded-xl p-4 text-sm font-mono text-neutral-200 placeholder-neutral-500 focus:outline-none focus:border-[#818CF8]"
                          />
                        </div>

                        {/* Benchmark Tool */}
                        <div className="p-5 sm:p-6 rounded-2xl bg-[#0d0d10] border border-[#25252b] space-y-4">
                          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                            <div className="space-y-1">
                              <div className="flex items-center space-x-2 text-sm font-bold text-[#ffe500]">
                                <Zap className="w-4 h-4 text-[#ffe500]" />
                                <span>
                                  {isEn
                                    ? "Free Models Diagnostic & Ranking (:free)"
                                    : "Diagnóstico e Ranking de Modelos Gratuitos (:free)"}
                                </span>
                              </div>
                              <p className="text-xs text-neutral-400 leading-relaxed">
                                {isEn
                                  ? "Concurrent fail-fast scan (latency & JSON validity) in real-time across all active free models."
                                  : "Varredura concorrente fail-fast (latência & JSON) em tempo real em todos os modelos gratuitos ativos."}
                              </p>
                            </div>
                            <button
                              type="button"
                              onClick={handleRunBenchmark}
                              disabled={benchmarking}
                              className="shrink-0 flex items-center space-x-2 bg-[#1f1f24] hover:bg-[#2c2c34] text-[#ffe500] hover:text-white border border-[#ffe500]/30 font-bold text-xs sm:text-sm px-4 py-2.5 rounded-xl transition-all disabled:opacity-50"
                            >
                              {benchmarking ? (
                                <>
                                  <div className="w-4 h-4 border-2 border-[#ffe500] border-t-transparent rounded-full animate-spin" />
                                  <span>{isEn ? "Scanning (10-15s)..." : "Escaneando (10-15s)..."}</span>
                                </>
                              ) : (
                                <>
                                  <Activity className="w-4 h-4" />
                                  <span>{isEn ? "Rank Free Models" : "Ranquear Gratuitos"}</span>
                                </>
                              )}
                            </button>
                          </div>

                          {benchmarkError && (
                            <div className="p-3 bg-red-950/40 border border-red-800/60 rounded-xl text-red-200 text-xs flex items-center space-x-2">
                              <AlertCircle className="w-4 h-4 shrink-0" />
                              <span>{benchmarkError}</span>
                            </div>
                          )}

                          {benchmarkResult && (
                            <div className="space-y-4 pt-3 border-t border-[#222228]">
                              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs sm:text-sm">
                                <span className="text-emerald-400 font-medium flex items-center space-x-2">
                                  <CheckCircle2 className="w-4 h-4" />
                                  <span>
                                    {isEn
                                      ? `${benchmarkResult.approved_count} models approved out of ${benchmarkResult.total_scanned} scanned (${benchmarkResult.benchmark_duration_seconds}s)`
                                      : `${benchmarkResult.approved_count} modelos aprovados de ${benchmarkResult.total_scanned} escaneados (${benchmarkResult.benchmark_duration_seconds}s)`}
                                  </span>
                                </span>
                                <div className="flex items-center space-x-2">
                                  <button
                                    type="button"
                                    onClick={handleCopyRecommended}
                                    className="text-xs flex items-center space-x-1.5 bg-[#1e1e24] hover:bg-[#282830] text-neutral-300 px-3 py-1.5 rounded-lg transition-all"
                                  >
                                    {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                                    <span>
                                      {copied
                                        ? isEn
                                          ? "Copied!"
                                          : "Copiado!"
                                        : isEn
                                        ? "Copy CSV"
                                        : "Copiar CSV"}
                                    </span>
                                  </button>
                                  <button
                                    type="button"
                                    onClick={handleApplyRecommended}
                                    className="text-xs font-bold flex items-center space-x-1.5 bg-[#ffe500] hover:bg-[#ffe500]/90 text-black px-3.5 py-1.5 rounded-lg transition-all shadow-sm"
                                  >
                                    <Check className="w-3.5 h-3.5" />
                                    <span>{isEn ? "Apply to Pool" : "Aplicar ao Pool"}</span>
                                  </button>
                                </div>
                              </div>

                              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                                {benchmarkResult.approved_models.slice(0, 8).map((m, idx) => (
                                  <div
                                    key={m.model}
                                    className="p-3.5 rounded-xl bg-[#141418] border border-[#2a2a30] flex flex-col justify-between space-y-2"
                                  >
                                    <div className="flex items-center justify-between">
                                      <span className="font-mono text-xs text-white truncate max-w-[200px]" title={m.model}>
                                        <strong className="text-[#ffe500] mr-1.5">#{idx + 1}</strong>
                                        {m.model.split("/")[1] || m.model}
                                      </span>
                                      <div className="flex items-center space-x-1.5">
                                        {m.score !== undefined && (
                                          <span className="text-[11px] px-2 py-0.5 rounded bg-[#ffe500]/10 text-[#ffe500] border border-[#ffe500]/30 font-bold font-mono">
                                            ★ {m.score} pts
                                          </span>
                                        )}
                                        <span className="text-[11px] px-2 py-0.5 rounded bg-emerald-950/80 text-emerald-400 border border-emerald-800/40 font-mono">
                                          ⚡ {m.latency}s
                                        </span>
                                      </div>
                                    </div>
                                    <div className="flex items-center justify-between text-xs text-neutral-400">
                                      <span className="text-neutral-300 font-mono">
                                        {m.words
                                          ? isEn
                                            ? `${m.words} words`
                                            : `${m.words} palavras`
                                          : m.json_ready
                                          ? isEn
                                            ? "✓ Valid JSON"
                                            : "✓ JSON Válido"
                                          : isEn
                                          ? "Text"
                                          : "Texto"}
                                      </span>
                                      <span className="text-emerald-400/90 font-medium truncate max-w-[150px]">
                                        {m.compliance || (m.json_ready ? (isEn ? "✓ Approved" : "✓ Aprovado") : "Online")}
                                      </span>
                                    </div>
                                  </div>
                                ))}
                              </div>

                              {benchmarkResult.rejected_count > 0 && (
                                <div className="pt-2">
                                  <button
                                    type="button"
                                    onClick={() => setShowRejected(!showRejected)}
                                    className="text-xs text-neutral-400 hover:text-neutral-200 flex items-center space-x-1.5 transition-all"
                                  >
                                    {showRejected ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                                    <span>
                                      {showRejected ? (isEn ? "Hide" : "Ocultar") : isEn ? "View" : "Ver"}{" "}
                                      {benchmarkResult.rejected_count}{" "}
                                      {isEn ? "unstable or timed out models" : "modelos instáveis ou com timeout"}
                                    </span>
                                  </button>

                                  {showRejected && (
                                    <div className="mt-2.5 p-3 rounded-xl bg-[#09090b] border border-[#222226] space-y-2 max-h-40 overflow-y-auto text-xs">
                                      {benchmarkResult.rejected_models.map((r) => (
                                        <div key={r.model} className="flex items-center justify-between text-neutral-400">
                                          <span className="font-mono text-neutral-300 truncate max-w-[240px]">{r.model}</span>
                                          <span className="text-red-400/90 truncate max-w-[200px]">{r.error || "Timeout"}</span>
                                        </div>
                                      ))}
                                    </div>
                                  )}
                                </div>
                              )}
                            </div>
                          )}
                        </div>
                      </div>
                    )}

                    {/* OPENAI */}
                    {llmProvider === "openai" && (
                      <div className="space-y-6">
                        <div className="space-y-2">
                          <div className="flex items-center justify-between">
                            <label className="text-sm font-bold text-neutral-200 flex items-center space-x-2">
                              <OpenAILogo className="w-4 h-4" />
                              <span>{isEn ? "OpenAI API Key (OPENAI_API_KEY)" : "Chave de API da OpenAI (OPENAI_API_KEY)"}</span>
                              <span className="text-red-400">*</span>
                            </label>
                            {settings?.has_openai_api_key ? (
                              <span className="text-xs text-emerald-400 font-medium flex items-center space-x-1.5">
                                <CheckCircle2 className="w-3.5 h-3.5" />
                                <span>
                                  {isEn
                                    ? `Connected (${settings.openai_api_key_preview})`
                                    : `Conectado (${settings.openai_api_key_preview})`}
                                </span>
                              </span>
                            ) : (
                              <span className="text-xs text-amber-400/90 font-medium flex items-center space-x-1.5">
                                <AlertCircle className="w-3.5 h-3.5" />
                                <span>{isEn ? "Required to save" : "Obrigatória para salvar"}</span>
                              </span>
                            )}
                          </div>
                          <input
                            type="password"
                            placeholder={
                              settings?.has_openai_api_key
                                ? isEn
                                  ? "Replace existing key (sk-...)"
                                  : "Substituir chave existente (sk-...)"
                                : isEn
                                ? "Enter your OPENAI_API_KEY (sk-...)"
                                : "Insira sua OPENAI_API_KEY (sk-...)"
                            }
                            value={openaiKey}
                            onChange={(e) => setOpenaiKey(e.target.value)}
                            className="w-full h-12 bg-[#0c0c0e] border border-[#2c2c34] rounded-xl px-4 text-sm text-white placeholder-neutral-500 focus:outline-none focus:border-[#10A37F]"
                          />
                          <p className="text-xs text-neutral-400 flex items-center justify-between pt-1">
                            <span>
                              {isEn
                                ? "Your key is stored securely and locally."
                                : "Sua chave é armazenada de forma segura e local."}
                            </span>
                            <a
                              href="https://platform.openai.com/api-keys"
                              target="_blank"
                              rel="noreferrer"
                              className="text-[#10A37F] hover:underline flex items-center space-x-1"
                            >
                              <span>{isEn ? "OpenAI Console" : "Console OpenAI"}</span>
                              <ExternalLink className="w-3 h-3" />
                            </a>
                          </p>
                        </div>

                        <div className="space-y-2">
                          <div className="flex items-center justify-between">
                            <label className="text-sm font-bold text-neutral-200 uppercase tracking-wider">
                              {isEn ? "Model Pool (Fallback Order)" : "Pool de Modelos (Ordem de Fallback)"}
                            </label>
                            <span className="text-xs text-neutral-400">
                              {isEn ? "Comma separated" : "Separados por vírgula"}
                            </span>
                          </div>
                          <textarea
                            rows={3}
                            value={openaiModels}
                            onChange={(e) => setOpenaiModels(e.target.value)}
                            placeholder="gpt-4o-mini, gpt-4o, o3-mini"
                            className="w-full bg-[#0c0c0e] border border-[#2c2c34] rounded-xl p-4 text-sm font-mono text-neutral-200 placeholder-neutral-500 focus:outline-none focus:border-[#10A37F]"
                          />
                        </div>
                      </div>
                    )}

                    {/* ANTHROPIC */}
                    {llmProvider === "anthropic" && (
                      <div className="space-y-6">
                        <div className="space-y-2">
                          <div className="flex items-center justify-between">
                            <label className="text-sm font-bold text-neutral-200 flex items-center space-x-2">
                              <ClaudeLogo className="w-4 h-4" />
                              <span>{isEn ? "Anthropic API Key (ANTHROPIC_API_KEY)" : "Chave de API da Anthropic (ANTHROPIC_API_KEY)"}</span>
                              <span className="text-red-400">*</span>
                            </label>
                            {settings?.has_anthropic_api_key ? (
                              <span className="text-xs text-emerald-400 font-medium flex items-center space-x-1.5">
                                <CheckCircle2 className="w-3.5 h-3.5" />
                                <span>
                                  {isEn
                                    ? `Connected (${settings.anthropic_api_key_preview})`
                                    : `Conectado (${settings.anthropic_api_key_preview})`}
                                </span>
                              </span>
                            ) : (
                              <span className="text-xs text-amber-400/90 font-medium flex items-center space-x-1.5">
                                <AlertCircle className="w-3.5 h-3.5" />
                                <span>{isEn ? "Required to save" : "Obrigatória para salvar"}</span>
                              </span>
                            )}
                          </div>
                          <input
                            type="password"
                            placeholder={
                              settings?.has_anthropic_api_key
                                ? isEn
                                  ? "Replace existing key (sk-ant-...)"
                                  : "Substituir chave existente (sk-ant-...)"
                                : isEn
                                ? "Enter your ANTHROPIC_API_KEY (sk-ant-...)"
                                : "Insira sua ANTHROPIC_API_KEY (sk-ant-...)"
                            }
                            value={anthropicKey}
                            onChange={(e) => setAnthropicKey(e.target.value)}
                            className="w-full h-12 bg-[#0c0c0e] border border-[#2c2c34] rounded-xl px-4 text-sm text-white placeholder-neutral-500 focus:outline-none focus:border-[#D97757]"
                          />
                          <p className="text-xs text-neutral-400 flex items-center justify-between pt-1">
                            <span>
                              {isEn
                                ? "Your key is stored securely and locally."
                                : "Sua chave é armazenada de forma segura e local."}
                            </span>
                            <a
                              href="https://console.anthropic.com/settings/keys"
                              target="_blank"
                              rel="noreferrer"
                              className="text-[#D97757] hover:underline flex items-center space-x-1"
                            >
                              <span>{isEn ? "Anthropic Console" : "Console Anthropic"}</span>
                              <ExternalLink className="w-3 h-3" />
                            </a>
                          </p>
                        </div>

                        <div className="space-y-2">
                          <div className="flex items-center justify-between">
                            <label className="text-sm font-bold text-neutral-200 uppercase tracking-wider">
                              {isEn ? "Model Pool (Fallback Order)" : "Pool de Modelos (Ordem de Fallback)"}
                            </label>
                            <span className="text-xs text-neutral-400">
                              {isEn ? "Comma separated" : "Separados por vírgula"}
                            </span>
                          </div>
                          <textarea
                            rows={3}
                            value={anthropicModels}
                            onChange={(e) => setAnthropicModels(e.target.value)}
                            placeholder="claude-3-5-sonnet-20241022, claude-3-5-haiku-20241022, claude-3-7-sonnet-20250219"
                            className="w-full bg-[#0c0c0e] border border-[#2c2c34] rounded-xl p-4 text-sm font-mono text-neutral-200 placeholder-neutral-500 focus:outline-none focus:border-[#D97757]"
                          />
                        </div>
                      </div>
                    )}

                    {/* LOCAL / OLLAMA */}
                    {llmProvider === "local" && (
                      <div className="space-y-6">
                        <div className="space-y-3">
                          <div className="flex items-center justify-between">
                            <label className="text-sm font-bold text-neutral-200 flex items-center space-x-2">
                              <Server className="w-4 h-4 text-amber-400" />
                              <span>
                                {isEn
                                  ? "Local Server Endpoint (OpenAI Compatible)"
                                  : "Endpoint do Servidor Local (Compatível com OpenAI)"}
                              </span>
                            </label>
                            <span className="text-xs text-neutral-400 font-mono">
                              {isEn ? "/v1 auto-normalized" : "/v1 auto-normalizado"}
                            </span>
                          </div>

                          {/* Presets */}
                          <div className="flex flex-wrap items-center gap-2">
                            <span className="text-xs font-bold uppercase tracking-wider text-neutral-400 mr-1">
                              {isEn ? "Presets:" : "Presets:"}
                            </span>
                            {[
                              { label: "Ollama (11434)", url: "http://localhost:11434/v1", key: "11434" },
                              { label: "LM Studio (1234)", url: "http://localhost:1234/v1", key: "1234" },
                              { label: "vLLM (8000)", url: "http://localhost:8000/v1", key: "8000" },
                              { label: "LocalAI (8080)", url: "http://localhost:8080/v1", key: "8080" },
                            ].map((p) => (
                              <button
                                key={p.key}
                                type="button"
                                onClick={() => setLocalBaseUrl(p.url)}
                                className={`text-xs font-mono px-3.5 py-1.5 rounded-xl border transition-all ${
                                  localBaseUrl.includes(p.key)
                                    ? "bg-amber-500/20 border-amber-500 text-amber-300 font-bold shadow-sm"
                                    : "bg-[#141417] border-[#2c2c34] text-neutral-300 hover:text-white hover:border-neutral-500"
                                }`}
                              >
                                {p.label}
                              </button>
                            ))}
                          </div>

                          <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
                            <input
                              type="text"
                              placeholder="http://localhost:11434/v1"
                              value={localBaseUrl}
                              onChange={(e) => setLocalBaseUrl(e.target.value)}
                              className="flex-1 h-12 bg-[#0c0c0e] border border-[#2c2c34] rounded-xl px-4 text-sm font-mono text-white placeholder-neutral-500 focus:outline-none focus:border-amber-500"
                            />
                            <button
                              type="button"
                              onClick={handleTestLocalConnection}
                              disabled={testingConnection}
                              className="shrink-0 h-12 flex items-center justify-center space-x-2 bg-[#1f1f24] hover:bg-[#2c2c34] text-amber-300 hover:text-white border border-amber-500/40 font-bold text-xs sm:text-sm px-5 rounded-xl transition-all disabled:opacity-50"
                            >
                              {testingConnection ? (
                                <>
                                  <div className="w-4 h-4 border-2 border-amber-400 border-t-transparent rounded-full animate-spin" />
                                  <span>{isEn ? "Testing..." : "Testando..."}</span>
                                </>
                              ) : (
                                <>
                                  <Activity className="w-4 h-4" />
                                  <span>{isEn ? "Test Connection" : "Testar Conexão"}</span>
                                </>
                              )}
                            </button>
                          </div>

                          {/* Diagnostic Feedback */}
                          {connectionTestResult && (
                            <div
                              className={`p-4 rounded-xl border text-xs sm:text-sm flex flex-col space-y-2 ${
                                connectionTestResult.online
                                  ? "bg-emerald-950/30 border-emerald-800/60 text-emerald-200"
                                  : "bg-red-950/30 border-red-800/60 text-red-200"
                              }`}
                            >
                              <div className="flex items-center justify-between font-semibold">
                                <span className="flex items-center space-x-2">
                                  {connectionTestResult.online ? (
                                    <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                                  ) : (
                                    <AlertCircle className="w-4 h-4 text-red-400 shrink-0" />
                                  )}
                                  <span>
                                    {connectionTestResult.online
                                      ? isEn
                                        ? `${connectionTestResult.provider_detected.toUpperCase()} Server Online (${connectionTestResult.latency_ms}ms)`
                                        : `Servidor ${connectionTestResult.provider_detected.toUpperCase()} Online (${connectionTestResult.latency_ms}ms)`
                                      : isEn
                                      ? "Server Unreachable"
                                      : "Servidor Inacessível"}
                                  </span>
                                </span>
                                {connectionTestResult.online && connectionTestResult.models && (
                                  <span className="text-xs font-mono text-emerald-400">
                                    {isEn
                                      ? `${connectionTestResult.models.length} models detected`
                                      : `${connectionTestResult.models.length} modelos detectados`}
                                  </span>
                                )}
                              </div>
                              <p className="text-xs leading-relaxed text-neutral-300">
                                {connectionTestResult.online
                                  ? connectionTestResult.models.length > 0
                                    ? isEn
                                      ? `Installed models detected: ${connectionTestResult.models.slice(0, 8).join(", ")}${connectionTestResult.models.length > 8 ? "..." : ""}`
                                      : `Modelos instalados detectados: ${connectionTestResult.models.slice(0, 8).join(", ")}${connectionTestResult.models.length > 8 ? "..." : ""}`
                                    : isEn
                                    ? "Server connected successfully. No models loaded on the machine currently."
                                    : "Servidor conectado com sucesso. Nenhum modelo carregado na máquina no momento."
                                  : connectionTestResult.message || connectionTestResult.error}
                              </p>
                            </div>
                          )}
                        </div>

                        {/* Local Models List */}
                        <div className="space-y-3">
                          <div className="flex items-center justify-between">
                            <label className="text-sm font-bold text-neutral-200 uppercase tracking-wider">
                              {isEn ? "Local Model Pool (Fallback Order)" : "Pool de Modelos Locais (Ordem de Fallback)"}
                            </label>
                            <span className="text-xs text-neutral-400">
                              {isEn ? "Comma separated" : "Separados por vírgula"}
                            </span>
                          </div>

                          <div className="flex flex-wrap items-center gap-2">
                            <span className="text-xs font-bold uppercase tracking-wider text-neutral-400 mr-1">
                              {isEn ? "Recommended:" : "Recomendados:"}
                            </span>
                            {["llama3.1:latest", "qwen2.5:14b", "deepseek-r1:8b", "mistral:latest", "gemma2:9b"].map((rec) => (
                              <button
                                key={rec}
                                type="button"
                                onClick={() => {
                                  const current = localModels.split(",").map((s) => s.trim()).filter(Boolean);
                                  if (!current.includes(rec)) {
                                    setLocalModels(current.length > 0 ? `${rec}, ${current.join(", ")}` : rec);
                                  }
                                }}
                                className="text-xs font-mono px-3 py-1 rounded-lg bg-[#1a1a20] border border-[#2f2f38] text-neutral-200 hover:text-white hover:border-amber-500/60 transition-all"
                              >
                                + {rec}
                              </button>
                            ))}
                          </div>

                          <textarea
                            rows={3}
                            value={localModels}
                            onChange={(e) => setLocalModels(e.target.value)}
                            placeholder="llama3.1:latest, qwen2.5:14b, deepseek-r1:8b"
                            className="w-full bg-[#0c0c0e] border border-[#2c2c34] rounded-xl p-4 text-sm font-mono text-neutral-200 placeholder-neutral-500 focus:outline-none focus:border-amber-500"
                          />
                        </div>

                        {/* Local Auth Key */}
                        <div className="space-y-2 pt-1">
                          <div className="flex items-center justify-between">
                            <label className="text-xs font-semibold text-neutral-400 flex items-center space-x-2">
                              <Lock className="w-3.5 h-3.5 text-neutral-500" />
                              <span>{isEn ? "Local Authentication Key (Optional)" : "Chave de Autenticação Local (Opcional)"}</span>
                            </label>
                            <span className="text-xs text-neutral-500">
                              {isEn ? "Usually empty for Ollama / LM Studio" : "Geralmente vazia para Ollama / LM Studio"}
                            </span>
                          </div>
                          <input
                            type="password"
                            placeholder={
                              settings?.has_local_api_key
                                ? isEn
                                  ? "Replace existing local token"
                                  : "Substituir token local existente"
                                : isEn
                                ? "Leave empty for standard Ollama (or enter Bearer token if configured)"
                                : "Deixe vazio para Ollama padrão (ou insira Bearer token se configurado)"
                            }
                            value={localApiKey}
                            onChange={(e) => setLocalApiKey(e.target.value)}
                            className="w-full h-11 bg-[#0c0c0e] border border-[#2c2c34] rounded-xl px-4 text-xs text-white placeholder-neutral-500 focus:outline-none focus:border-neutral-500"
                          />
                        </div>

                        {/* Terminal Info */}
                        <div className="p-4 bg-[#0a0a0d] border border-[#222226] rounded-xl flex items-center justify-between space-x-3 text-xs font-mono text-neutral-300">
                          <div className="flex items-center space-x-2 truncate">
                            <Terminal className="w-4 h-4 shrink-0 text-amber-400" />
                            <span className="text-neutral-200 truncate">$ ollama run llama3.1</span>
                          </div>
                          <span className="text-xs text-neutral-500 shrink-0 font-sans">
                            {isEn ? "8k context • Native JSON support" : "8k contexto • Suporte nativo a JSON"}
                          </span>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* ========================================================================= */}
              {/* ABA 2: ILUSTRAÇÕES & IMAGENS */}
              {/* ========================================================================= */}
              {activeTab === "images" && (
                <div className="space-y-8">
                  {/* Style Banner */}
                  <div className="p-6 rounded-2xl bg-gradient-to-r from-[#17171c] to-[#111114] border border-[#27272a] space-y-2">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2 text-sm font-bold text-[#ffe500]">
                        <Sparkles className="w-4 h-4 text-[#ffe500]" />
                        <span>
                          {isEn
                            ? "Art Direction: Woodcut & Stippling in Pure Gold"
                            : "Direção de Arte: Talhe-Doce & Pontilhismo em Ouro Puro"}
                        </span>
                      </div>
                      <span className="text-xs px-2.5 py-1 rounded-full bg-[#ffe500]/10 text-[#ffe500] border border-[#ffe500]/30 font-mono">
                        1:1 (1024×1024)
                      </span>
                    </div>
                    <p className="text-xs sm:text-sm text-neutral-300 leading-relaxed">
                      {isEn
                        ? "Conceptual vignettes rendered on pure black background (#000000) with fine gold and white stippling, zero watermarks and guaranteed silent degradation."
                        : "Vinhetas conceituais geradas sobre fundo preto absoluto (#000000) com pontilhismo fino dourado e branco, sem marcas d'água e com degradação silenciosa garantida."}
                    </p>
                    <div className="flex items-center space-x-3 text-xs text-neutral-400 pt-1">
                      <span className="flex items-center space-x-1.5 text-neutral-300">
                        <ShieldCheck className="w-4 h-4 text-emerald-400" />
                        <span>{isEn ? "Zero People/Faces" : "Zero Pessoas/Rostos"}</span>
                      </span>
                      <span>•</span>
                      <span className="flex items-center space-x-1.5 text-neutral-300">
                        <ShieldCheck className="w-4 h-4 text-emerald-400" />
                        <span>{isEn ? "Zero Logos or Text" : "Zero Logos ou Textos"}</span>
                      </span>
                      <span>•</span>
                      <span className="text-neutral-400">
                        {isEn ? "Silent fallback to text" : "Fallback silencioso para texto"}
                      </span>
                    </div>
                  </div>

                  {/* Engine Cards */}
                  <div className="space-y-3">
                    <h2 className="text-sm sm:text-base font-black uppercase tracking-wider text-neutral-200">
                      {isEn ? "Image Generation Engine" : "Engine de Geração de Imagem"}
                    </h2>

                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                      {[
                        {
                          id: "openai",
                          title: "OpenAI DALL-E",
                          providerName: "DALL-E 3 / DALL-E 2",
                          badge: isEn ? "Default" : "Padrão",
                          logo: <OpenAILogo className="w-5 h-5" />,
                          desc: isEn
                            ? "Supreme fidelity for engravings and conceptual metaphors with zero watermarks."
                            : "Suprema fidelidade para gravuras e metáforas conceituais com zero marcas d'água.",
                        },
                        {
                          id: "fal",
                          title: "Fal.ai",
                          providerName: "FLUX.1 (schnell / dev)",
                          badge: isEn ? "Fast (1-2s)" : "Rápido (1-2s)",
                          logo: <FalLogo className="w-5 h-5" />,
                          desc: isEn
                            ? "The fastest and most cost-effective pure FLUX.1 engine with zero logos."
                            : "O motor mais rápido e econômico para FLUX.1 puro sem logos.",
                        },
                        {
                          id: "google",
                          title: "Google Imagen 3",
                          providerName: "Gemini API (DeepMind)",
                          badge: isEn ? "High Fidelity" : "Alta Fidelidade",
                          logo: <GeminiSparkleLogo className="w-5 h-5" />,
                          desc: isEn
                            ? "Geometric precision and technical lighting via Google Generative AI."
                            : "Precisão geométrica e iluminação técnica via Google Generative AI.",
                        },
                        {
                          id: "huggingface",
                          title: "Hugging Face",
                          providerName: "Inference Client",
                          badge: isEn ? "HF Token" : "Token HF",
                          logo: <FluxLogo className="w-5 h-5" />,
                          desc: isEn
                            ? "Direct connection to community endpoints for FLUX.1 or SDXL."
                            : "Conexão direta aos endpoints da comunidade para FLUX.1 ou SDXL.",
                        },
                        {
                          id: "disabled",
                          title: isEn ? "Disabled" : "Desativado",
                          providerName: isEn ? "Pure Text Mode" : "Modo Texto Puro",
                          badge: isEn ? "No Images" : "Sem Imagens",
                          logo: <Layers className="w-5 h-5 text-neutral-400" />,
                          desc: isEn
                            ? "Lessons focused exclusively on structured text, simulators, and quizzes."
                            : "Aulas focadas exclusivamente em texto estruturado, simuladores e quizzes.",
                        },
                      ].map((item) => (
                        <button
                          key={item.id}
                          type="button"
                          onClick={() => handleSelectImageProvider(item.id)}
                          className={`p-5 rounded-2xl border text-left transition-all flex flex-col justify-between space-y-3 ${
                            imageProvider === item.id
                              ? "bg-[#ffe500]/10 border-[#ffe500] shadow-lg shadow-[#ffe500]/10 ring-1 ring-[#ffe500]"
                              : "bg-[#141417] border-[#27272a] hover:border-neutral-500"
                          }`}
                        >
                          <div className="flex items-center justify-between">
                            <div className="flex items-center space-x-2.5">
                              {item.logo}
                              <span className="font-bold text-sm sm:text-base text-white">{item.title}</span>
                            </div>
                            <span
                              className={`text-[10px] px-2 py-0.5 rounded-full font-mono ${
                                imageProvider === item.id
                                  ? "bg-[#ffe500] text-black font-bold"
                                  : "bg-[#27272a] text-neutral-400"
                              }`}
                            >
                              {item.badge}
                            </span>
                          </div>
                          <div className="text-xs text-neutral-400 font-medium">{item.providerName}</div>
                          <p className="text-xs text-neutral-300 leading-relaxed">{item.desc}</p>
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Engine Details */}
                  {imageProvider !== "disabled" && (
                    <div className="p-6 sm:p-8 rounded-2xl bg-[#131317] border border-[#27272a] space-y-6">
                      <div className="space-y-2">
                        <div className="flex items-center justify-between">
                          <label className="text-sm font-bold text-neutral-200 uppercase tracking-wider">
                            {isEn ? "Engine Model (Editable)" : "Modelo da Engine (Editável)"}
                          </label>
                          <span className="text-xs text-neutral-400 font-mono">
                            {imageProvider === "openai" && (isEn ? "e.g. dall-e-3, dall-e-2" : "Ex: dall-e-3, dall-e-2")}
                            {imageProvider === "fal" && (isEn ? "e.g. fal-ai/flux/schnell, fal-ai/flux/dev" : "Ex: fal-ai/flux/schnell, fal-ai/flux/dev")}
                            {imageProvider === "google" && (isEn ? "e.g. imagen-3.0-generate-002" : "Ex: imagen-3.0-generate-002")}
                            {imageProvider === "huggingface" && (isEn ? "e.g. black-forest-labs/FLUX.1-schnell" : "Ex: black-forest-labs/FLUX.1-schnell")}
                          </span>
                        </div>
                        <input
                          type="text"
                          value={imageModel}
                          onChange={(e) => setImageModel(e.target.value)}
                          placeholder={
                            imageProvider === "openai"
                              ? "dall-e-3"
                              : imageProvider === "fal"
                              ? "fal-ai/flux/schnell"
                              : imageProvider === "google"
                              ? "imagen-3.0-generate-002"
                              : "black-forest-labs/FLUX.1-schnell"
                          }
                          className="w-full h-12 bg-[#0c0c0e] border border-[#2c2c34] rounded-xl px-4 text-sm font-mono text-white placeholder-neutral-500 focus:outline-none focus:border-[#ffe500]"
                        />
                      </div>

                      {/* Quality Presets */}
                      <div className="space-y-2">
                        <div className="flex items-center justify-between">
                          <label className="text-sm font-bold text-neutral-200 uppercase tracking-wider flex items-center space-x-2">
                            <Sliders className="w-4 h-4 text-[#ffe500]" />
                            <span>{isEn ? "Quality & Resolution" : "Qualidade & Resolução"}</span>
                          </label>
                          <span className="text-xs text-neutral-400 font-mono">
                            {isEn ? "1:1 Square (1024×1024)" : "1:1 Quadrado (1024×1024)"}
                          </span>
                        </div>
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                          {[
                            {
                              id: "standard",
                              label: isEn ? "Standard / Fast" : "Standard / Rápido",
                              desc: isEn ? "Optimized speed & efficient inference" : "Velocidade otimizada e inferência eficiente",
                            },
                            {
                              id: "hd",
                              label: isEn ? "HD / Fine Detail" : "HD / Detalhe Fino",
                              desc: isEn ? "Maximum stippling contrast & fidelity" : "Máximo contraste pontilhado e fidelidade",
                            },
                          ].map((q) => (
                            <button
                              key={q.id}
                              type="button"
                              onClick={() => setImageQuality(q.id as "standard" | "hd")}
                              className={`p-4 rounded-xl border text-center transition-all flex flex-col items-center justify-center space-y-1 ${
                                imageQuality === q.id
                                  ? "bg-[#ffe500]/15 border-[#ffe500] text-[#ffe500]"
                                  : "bg-[#0c0c0e] border-[#27272a] text-neutral-400 hover:border-neutral-600"
                              }`}
                            >
                              <span className="font-bold text-sm">{q.label}</span>
                              <span className="text-xs text-neutral-400">{q.desc}</span>
                            </button>
                          ))}
                        </div>
                      </div>

                      {/* Contextual API Keys */}
                      <div className="pt-4 border-t border-[#222228] space-y-4">
                        <h3 className="text-sm font-bold uppercase tracking-wider text-neutral-200">
                          {isEn ? "Selected Engine Credential" : "Credencial da Engine Selecionada"}
                        </h3>

                        {imageProvider === "openai" && (
                          <div className="p-4 rounded-xl bg-[#0e0e11] border border-[#27272a] space-y-2">
                            <div className="flex items-center justify-between text-xs sm:text-sm">
                              <span className="text-neutral-200 font-medium flex items-center space-x-2">
                                <OpenAILogo className="w-4 h-4" />
                                <span>{isEn ? "OpenAI Key (OPENAI_API_KEY)" : "Chave da OpenAI (OPENAI_API_KEY)"}</span>
                              </span>
                              {settings?.has_openai_api_key || openaiKey.trim() ? (
                                <span className="text-xs text-emerald-400 flex items-center space-x-1.5 font-medium">
                                  <CheckCircle2 className="w-3.5 h-3.5" />
                                  <span>
                                    {isEn
                                      ? `Inherited from OpenAI (${settings?.openai_api_key_preview || "Configured"})`
                                      : `Herdada da OpenAI (${settings?.openai_api_key_preview || "Configurada"})`}
                                  </span>
                                </span>
                              ) : (
                                <span className="text-xs text-amber-400/90 flex items-center space-x-1.5 font-medium">
                                  <AlertCircle className="w-3.5 h-3.5" />
                                  <span>{isEn ? "Required for DALL-E" : "Necessária para DALL-E"}</span>
                                </span>
                              )}
                            </div>
                            <input
                              type="password"
                              placeholder={
                                settings?.has_openai_api_key
                                  ? isEn
                                    ? "Replace existing key (sk-...)"
                                    : "Substituir chave existente (sk-...)"
                                  : isEn
                                  ? "Enter your OPENAI_API_KEY (sk-...)"
                                  : "Insira sua OPENAI_API_KEY (sk-...)"
                              }
                              value={openaiKey}
                              onChange={(e) => setOpenaiKey(e.target.value)}
                              className="w-full h-11 bg-[#141417] border border-[#27272a] rounded-xl px-4 text-xs text-white placeholder-neutral-500 focus:outline-none focus:border-[#10A37F]"
                            />
                            <p className="text-xs text-neutral-400 pt-1">
                              {isEn
                                ? "The OpenAI key is automatically shared between LLMs and image generation via DALL-E."
                                : "A chave da OpenAI é compartilhada automaticamente entre LLMs e geração de imagens via DALL-E."}
                            </p>
                          </div>
                        )}

                        {imageProvider === "fal" && (
                          <div className="p-4 rounded-xl bg-[#0e0e11] border border-[#27272a] space-y-2">
                            <div className="flex items-center justify-between text-xs sm:text-sm">
                              <span className="text-neutral-200 font-medium flex items-center space-x-2">
                                <FalLogo className="w-4 h-4" />
                                <span>{isEn ? "Fal.ai Key (FAL_KEY)" : "Chave da Fal.ai (FAL_KEY)"}</span>
                              </span>
                              {settings?.has_fal_api_key ? (
                                <span className="text-xs text-emerald-400 flex items-center space-x-1.5 font-medium">
                                  <CheckCircle2 className="w-3.5 h-3.5" />
                                  <span>
                                    {isEn
                                      ? `Configured (${settings.fal_api_key_preview})`
                                      : `Configurado (${settings.fal_api_key_preview})`}
                                  </span>
                                </span>
                              ) : (
                                <span className="text-xs text-amber-400/90 flex items-center space-x-1.5 font-medium">
                                  <AlertCircle className="w-3.5 h-3.5" />
                                  <span>{isEn ? "Required for Fal.ai" : "Necessária para Fal.ai"}</span>
                                </span>
                              )}
                            </div>
                            <input
                              type="password"
                              placeholder={
                                settings?.has_fal_api_key
                                  ? isEn
                                    ? "Replace existing key (fal_...)"
                                    : "Substituir chave existente (fal_...)"
                                  : isEn
                                  ? "Enter your FAL_KEY"
                                  : "Insira sua chave FAL_KEY"
                              }
                              value={falKey}
                              onChange={(e) => setFalKey(e.target.value)}
                              className="w-full h-11 bg-[#141417] border border-[#27272a] rounded-xl px-4 text-xs text-white placeholder-neutral-500 focus:outline-none focus:border-[#ec0648]"
                            />
                            <div className="flex items-center justify-between text-xs text-neutral-400 pt-1">
                              <span>
                                {isEn
                                  ? "Generates images with pure FLUX.1 in 1 to 2 seconds at ultra-low costs."
                                  : "Gera imagens com FLUX.1 puro em 1 a 2 segundos a custos ultra-baixos."}
                              </span>
                              <a
                                href="https://fal.ai/dashboard/keys"
                                target="_blank"
                                rel="noreferrer"
                                className="text-[#ec0648] hover:underline flex items-center space-x-1"
                              >
                                <span>{isEn ? "Fal.ai Dashboard" : "Dashboard Fal.ai"}</span>
                                <ExternalLink className="w-3 h-3" />
                              </a>
                            </div>
                          </div>
                        )}

                        {imageProvider === "google" && (
                          <div className="p-4 rounded-xl bg-[#0e0e11] border border-[#27272a] space-y-2">
                            <div className="flex items-center justify-between text-xs sm:text-sm">
                              <span className="text-neutral-200 font-medium flex items-center space-x-2">
                                <GeminiSparkleLogo className="w-4 h-4" />
                                <span>Google Gemini / Imagen Key (GEMINI_API_KEY)</span>
                              </span>
                              {settings?.has_gemini_api_key || geminiKey.trim() ? (
                                <span className="text-xs text-emerald-400 flex items-center space-x-1.5 font-medium">
                                  <CheckCircle2 className="w-3.5 h-3.5" />
                                  <span>
                                    {isEn
                                      ? `Configured (${settings?.gemini_api_key_preview || "Configured"})`
                                      : `Configurado (${settings?.gemini_api_key_preview || "Configurada"})`}
                                  </span>
                                </span>
                              ) : (
                                <span className="text-xs text-amber-400/90 flex items-center space-x-1.5 font-medium">
                                  <AlertCircle className="w-3.5 h-3.5" />
                                  <span>{isEn ? "Not configured" : "Não configurado"}</span>
                                </span>
                              )}
                            </div>
                            <input
                              type="password"
                              placeholder={
                                settings?.has_gemini_api_key
                                  ? isEn
                                    ? "Replace Google key"
                                    : "Substituir chave do Google"
                                  : isEn
                                  ? "Enter your GEMINI_API_KEY"
                                  : "Insira sua GEMINI_API_KEY"
                              }
                              value={geminiKey}
                              onChange={(e) => setGeminiKey(e.target.value)}
                              className="w-full h-11 bg-[#141417] border border-[#27272a] rounded-xl px-4 text-xs text-white placeholder-neutral-500 focus:outline-none focus:border-[#4285F4]"
                            />
                            <div className="flex items-center justify-between text-xs text-neutral-400 pt-1">
                              <span>
                                {isEn
                                  ? "Used for Google Generative AI Imagen 3 model."
                                  : "Usado para o modelo Imagen 3 do Google Generative AI."}
                              </span>
                              <a
                                href="https://aistudio.google.com/app/apikey"
                                target="_blank"
                                rel="noreferrer"
                                className="text-[#4285F4] hover:underline flex items-center space-x-1"
                              >
                                <span>Google AI Studio</span>
                                <ExternalLink className="w-3 h-3" />
                              </a>
                            </div>
                          </div>
                        )}

                        {imageProvider === "huggingface" && (
                          <div className="p-4 rounded-xl bg-[#0e0e11] border border-[#27272a] space-y-2">
                            <div className="flex items-center justify-between text-xs sm:text-sm">
                              <span className="text-neutral-200 font-medium flex items-center space-x-2">
                                <FluxLogo className="w-4 h-4" />
                                <span>Hugging Face Token (HF_TOKEN)</span>
                              </span>
                              {settings?.has_hf_token ? (
                                <span className="text-xs text-emerald-400 flex items-center space-x-1.5 font-medium">
                                  <CheckCircle2 className="w-3.5 h-3.5" />
                                  <span>
                                    {isEn
                                      ? `Configured (${settings.hf_token_preview})`
                                      : `Configurado (${settings.hf_token_preview})`}
                                  </span>
                                </span>
                              ) : (
                                <span className="text-xs text-amber-400/90 flex items-center space-x-1.5 font-medium">
                                  <AlertCircle className="w-3.5 h-3.5" />
                                  <span>{isEn ? "Recommended Token" : "Token Recomendado"}</span>
                                </span>
                              )}
                            </div>
                            <input
                              type="password"
                              placeholder={
                                settings?.has_hf_token
                                  ? isEn
                                    ? "Replace existing token (hf_...)"
                                    : "Substituir token existente (hf_...)"
                                  : isEn
                                  ? "Enter your Hugging Face token (hf_...)"
                                  : "Insira seu token do Hugging Face (hf_...)"
                              }
                              value={hfToken}
                              onChange={(e) => setHfToken(e.target.value)}
                              className="w-full h-11 bg-[#141417] border border-[#27272a] rounded-xl px-4 text-xs text-white placeholder-neutral-500 focus:outline-none focus:border-[#ffe500]"
                            />
                            <div className="flex items-center justify-between text-xs text-neutral-400 pt-1">
                              <span>
                                {isEn
                                  ? "Required to call FLUX.1 schnell model via Hugging Face API."
                                  : "Necessário para chamar o modelo FLUX.1 schnell via API do Hugging Face."}
                              </span>
                              <a
                                href="https://huggingface.co/settings/tokens"
                                target="_blank"
                                rel="noreferrer"
                                className="text-[#ffe500] hover:underline flex items-center space-x-1"
                              >
                                <span>{isEn ? "Get HF token" : "Obter token no HF"}</span>
                                <ExternalLink className="w-3 h-3" />
                              </a>
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </>
          )}
        </div>
      </main>
    </div>,
    document.body
  );
}
