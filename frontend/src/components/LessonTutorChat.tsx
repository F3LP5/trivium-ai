"use client";

import React, { useState, useEffect, useRef } from "react";
import { 
  MessageSquare, 
  X, 
  Send, 
  Sparkles, 
  RotateCcw, 
  Bot, 
  User,
  Loader2,
  HelpCircle
} from "lucide-react";
import ReactMarkdown from "react-markdown";
import { 
  LessonFullDetail, 
  LessonChatMessageItem, 
  getLessonChatHistory, 
  sendLessonChatMessage, 
  clearLessonChatHistory 
} from "@/lib/api";

interface LessonTutorChatProps {
  lesson: LessonFullDetail;
  isOpen?: boolean;
  onOpen?: () => void;
  onClose?: () => void;
}

export default function LessonTutorChat({ 
  lesson, 
  isOpen: externalIsOpen, 
  onOpen: externalOnOpen, 
  onClose: externalOnClose 
}: LessonTutorChatProps) {
  const [internalIsOpen, setInternalIsOpen] = useState(false);
  const isControlled = externalIsOpen !== undefined;
  const isOpen = isControlled ? externalIsOpen : internalIsOpen;

  const handleOpen = () => {
    if (isControlled) {
      externalOnOpen?.();
    } else {
      setInternalIsOpen(true);
    }
  };

  const handleClose = () => {
    if (isControlled) {
      externalOnClose?.();
    } else {
      setInternalIsOpen(false);
    }
  };

  const [messages, setMessages] = useState<LessonChatMessageItem[]>([]);
  const [inputMessage, setInputMessage] = useState("");
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [sending, setSending] = useState(false);
  const [showClearConfirm, setShowClearConfirm] = useState(false);
  const isEn = lesson.language?.startsWith("en");

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // Carrega histórico persistente da aula
  useEffect(() => {
    let isMounted = true;
    const fetchHistory = async () => {
      try {
        setLoadingHistory(true);
        const history = await getLessonChatHistory(lesson.id);
        if (isMounted) {
          setMessages(history);
        }
      } catch (err) {
        console.error("Erro ao carregar histórico do chat:", err);
      } finally {
        if (isMounted) {
          setLoadingHistory(false);
        }
      }
    };

    fetchHistory();
    return () => {
      isMounted = false;
    };
  }, [lesson.id]);

  // Rola suavemente para o final quando novas mensagens chegam
  useEffect(() => {
    if (isOpen) {
      messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, isOpen, sending]);

  // Foco no input ao abrir
  useEffect(() => {
    if (isOpen) {
      setTimeout(() => {
        inputRef.current?.focus();
      }, 150);
    }
  }, [isOpen]);

  const handleSendMessage = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    const text = inputMessage.trim();
    if (!text || sending) return;

    // Adiciona temporariamente a mensagem do usuário na tela
    const tempUserMsg: LessonChatMessageItem = {
      id: Date.now(),
      role: "user",
      content: text,
      created_at: new Date().toISOString()
    };

    setMessages((prev) => [...prev, tempUserMsg]);
    setInputMessage("");
    setSending(true);

    try {
      const responseMsg = await sendLessonChatMessage(lesson.id, text);
      setMessages((prev) => [...prev.filter((m) => m.id !== tempUserMsg.id), tempUserMsg, responseMsg]);
    } catch {
      const errorMsg: LessonChatMessageItem = {
        id: Date.now() + 1,
        role: "assistant",
        content: isEn
          ? "⚠️ Connection issue while answering your question. Please try sending again!"
          : "⚠️ Tive uma breve oscilação de conexão para responder sua dúvida. Por favor, tente enviar novamente!",
        created_at: new Date().toISOString()
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setSending(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleClearChat = async () => {
    try {
      await clearLessonChatHistory(lesson.id);
      setMessages([]);
      setShowClearConfirm(false);
    } catch (err) {
      console.error("Erro ao limpar histórico:", err);
    }
  };

  return (
    <>
      {/* Botão de Ação Flutuante (FAB) Amarelo no Canto Inferior Direito (Apenas visível quando o chat NÃO está aberto) */}
      {!isOpen && (
        <div className="fixed bottom-6 right-6 z-50">
          <button
            onClick={handleOpen}
            aria-label={isEn ? "Ask the AI Tutor" : "Tirar dúvidas com o Tutor da Aula"}
            className="w-12 h-12 bg-[#ffe500] hover:bg-[#ffd000] text-black rounded-full shadow-[0_6px_24px_rgba(0,0,0,0.5)] flex items-center justify-center transition-all duration-200 transform hover:scale-105 active:scale-95 group cursor-pointer"
            title={isEn ? "Ask the AI Tutor" : "Tirar dúvidas com o Tutor da Aula"}
          >
            <MessageSquare className="w-5 h-5 fill-black" />

            {/* Tooltip de chamada visual ao passar o mouse */}
            <span className="absolute right-full mr-3 px-3 py-1.5 bg-[#121214] border border-[#27272a] text-white text-xs font-bold rounded-xl whitespace-nowrap shadow-xl opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none hidden sm:block">
              {isEn ? "Questions? Ask the Tutor" : "Dúvidas da aula? Fale com o Tutor"}
            </span>
          </button>
        </div>
      )}

      {/* Painel Lateral do Chat (Split View à Direita que respeita a barra superior) */}
      {isOpen && (
        <aside 
          id="lesson-tutor-sidebar"
          aria-label={isEn ? "Class Tutor" : "Tutor da Aula"}
          className="fixed top-14 right-0 z-30 h-[calc(100vh-3.5rem)] w-full sm:w-[420px] md:w-[460px] lg:w-[480px] bg-[#0d0d0f] border-l border-t border-[#27272a] shadow-[-12px_0_35px_rgba(0,0,0,0.75)] flex flex-col overflow-hidden animate-in slide-in-from-right duration-200"
        >
          {/* Cabeçalho do Chat */}
          <div className="px-5 py-4 bg-[#121214] border-b border-[#222226] flex items-center justify-between flex-shrink-0">
            <div className="flex items-center space-x-3 min-w-0">
              <div className="w-8 h-8 rounded-xl bg-[#ffe500]/10 border border-[#ffe500]/30 flex items-center justify-center flex-shrink-0">
                <Sparkles className="w-4 h-4 text-[#ffe500]" />
              </div>
              <div className="min-w-0">
                <div className="flex items-center space-x-1.5">
                  <span className="text-sm font-black text-white">{isEn ? "Class AI Tutor" : "Tutor da Aula"}</span>
                  <span className="text-[10px] font-black px-1.5 py-0.2 rounded-full bg-[#ffe500]/20 text-[#ffe500] border border-[#ffe500]/30">
                    {isEn ? "AI" : "IA"}
                  </span>
                </div>
                <p className="text-[11px] text-neutral-400 truncate max-w-[220px]" title={lesson.title}>
                  {lesson.title}
                </p>
              </div>
            </div>

            <div className="flex items-center space-x-1.5 flex-shrink-0">
              {messages.length > 0 && (
                <button
                  onClick={() => setShowClearConfirm(true)}
                  className="p-1.5 text-neutral-400 hover:text-rose-400 hover:bg-[#1f1f23] rounded-lg transition-colors cursor-pointer"
                  title={isEn ? "Clear chat history for this lesson" : "Limpar histórico desta aula"}
                  aria-label={isEn ? "Clear history" : "Limpar histórico"}
                >
                  <RotateCcw className="w-4 h-4" />
                </button>
              )}
              {/* Botão Slim Pequeno de X */}
              <button
                onClick={handleClose}
                className="p-1.5 text-neutral-400 hover:text-white hover:bg-[#222226] rounded-lg transition-colors cursor-pointer"
                title={isEn ? "Close panel and return to full screen" : "Fechar painel e voltar à tela cheia"}
                aria-label={isEn ? "Close tutor panel" : "Fechar painel do tutor"}
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Modal / Alerta de Confirmação de Limpeza */}
          {showClearConfirm && (
            <div className="bg-[#1c1917] border-b border-amber-900/40 p-3 px-4 flex items-center justify-between text-xs text-amber-200">
              <span>{isEn ? "Reset this lesson's conversation?" : "Deseja reiniciar a conversa desta aula?"}</span>
              <div className="flex items-center space-x-2">
                <button
                  onClick={handleClearChat}
                  className="bg-rose-600 hover:bg-rose-500 text-white font-bold px-2.5 py-1 rounded-lg transition-colors"
                >
                  {isEn ? "Yes" : "Sim"}
                </button>
                <button
                  onClick={() => setShowClearConfirm(false)}
                  className="bg-[#2a2a2e] hover:bg-[#38383e] text-neutral-300 font-semibold px-2 py-1 rounded-lg transition-colors"
                >
                  {isEn ? "No" : "Não"}
                </button>
              </div>
            </div>
          )}

          {/* Área de Mensagens (Scrollable) */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4 text-sm scrollbar-thin scrollbar-thumb-[#27272a] scrollbar-track-transparent">
            {loadingHistory ? (
              <div className="flex flex-col items-center justify-center h-full text-neutral-500 space-y-2">
                <Loader2 className="w-6 h-6 animate-spin text-[#ffe500]" />
                <span className="text-xs font-semibold">{isEn ? "Loading history..." : "Carregando histórico..."}</span>
              </div>
            ) : (
              <>
                {/* Mensagem Inicial de Orientação e Apresentação (Regra de Negócio Trivium) */}
                <div className="bg-[#18181b] border border-[#27272a] p-4 rounded-2xl space-y-2.5 shadow-sm">
                  <div className="flex items-center space-x-2 text-[#ffe500]">
                    <Sparkles className="w-4 h-4 flex-shrink-0" />
                    <span className="text-xs font-black uppercase tracking-wider">{isEn ? "How the Tutor works" : "Como funciona o Tutor"}</span>
                  </div>
                  {isEn ? (
                    <>
                      <p className="text-xs sm:text-[13px] text-neutral-300 leading-relaxed">
                        Hello! I am your AI tutor for this lesson on <strong className="text-white font-bold">{lesson.title}</strong>.
                      </p>
                      <p className="text-xs sm:text-[13px] text-neutral-300 leading-relaxed">
                        I am here exclusively to answer your questions with simple, clear language and practical examples about <strong className="text-[#ffe500] font-bold">{lesson.core_concept}</strong>.
                      </p>
                      <div className="bg-[#121214] border border-[#27272a] p-2.5 rounded-xl text-[11px] text-neutral-400 flex items-start space-x-1.5">
                        <HelpCircle className="w-3.5 h-3.5 text-[#ffe500] mt-0.5 flex-shrink-0" />
                        <span>Off-topic questions are avoided to ensure your focus and mastery of the subject.</span>
                      </div>
                    </>
                  ) : (
                    <>
                      <p className="text-xs sm:text-[13px] text-neutral-300 leading-relaxed">
                        Olá! Sou seu tutor inteligente nesta aula de <strong className="text-white font-bold">{lesson.title}</strong>.
                      </p>
                      <p className="text-xs sm:text-[13px] text-neutral-300 leading-relaxed">
                        Estou aqui exclusivamente para tirar suas dúvidas com linguagem simples, clara e exemplos do dia a dia sobre <strong className="text-[#ffe500] font-bold">{lesson.core_concept}</strong>.
                      </p>
                      <div className="bg-[#121214] border border-[#27272a] p-2.5 rounded-xl text-[11px] text-neutral-400 flex items-start space-x-1.5">
                        <HelpCircle className="w-3.5 h-3.5 text-[#ffe500] mt-0.5 flex-shrink-0" />
                        <span>Perguntas fora do assunto desta aula não são abordadas para garantir seu foco e aprendizado.</span>
                      </div>
                    </>
                  )}
                </div>

                {/* Lista de Mensagens Persistidas */}
                {messages.map((msg) => {
                  const isUser = msg.role === "user";
                  return (
                    <div
                      key={msg.id}
                      className={`flex items-start space-x-2.5 ${
                        isUser ? "flex-row-reverse space-x-reverse" : "flex-row"
                      }`}
                    >
                      <div
                        className={`w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0 mt-0.5 ${
                          isUser
                            ? "bg-[#27272a] text-neutral-300"
                            : "bg-[#ffe500]/10 border border-[#ffe500]/30 text-[#ffe500]"
                        }`}
                      >
                        {isUser ? <User className="w-3.5 h-3.5" /> : <Bot className="w-3.5 h-3.5" />}
                      </div>

                      <div
                        className={`max-w-[82%] rounded-2xl p-3.5 text-[13px] sm:text-[14px] leading-relaxed shadow-sm ${
                          isUser
                            ? "bg-[#222226] text-white rounded-tr-sm border border-[#2e2e33]"
                            : "bg-[#18181b] text-neutral-200 rounded-tl-sm border border-[#27272a]"
                        }`}
                      >
                        {isUser ? (
                          <p className="whitespace-pre-wrap">{msg.content}</p>
                        ) : (
                          <div className="prose prose-invert max-w-none text-neutral-200 text-[13px] sm:text-[14px] leading-relaxed">
                            <ReactMarkdown
                              components={{
                                p: ({ children }) => <p className="my-1.5 first:mt-0 last:mb-0">{children}</p>,
                                strong: ({ children }) => (
                                  <strong className="text-[#ffe500] font-black">{children}</strong>
                                ),
                                ul: ({ children }) => <ul className="my-2 pl-4 list-disc space-y-1">{children}</ul>,
                                ol: ({ children }) => <ol className="my-2 pl-4 list-decimal space-y-1">{children}</ol>,
                                li: ({ children }) => <li className="my-0.5">{children}</li>,
                                blockquote: ({ children }) => (
                                  <blockquote className="border-l-2 border-[#ffe500] pl-3 py-1 my-2 bg-[#121214] rounded-r text-neutral-300 italic">
                                    {children}
                                  </blockquote>
                                ),
                              }}
                            >
                              {msg.content}
                            </ReactMarkdown>
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })}

                {/* Indicador de Digitação do Tutor */}
                {sending && (
                  <div className="flex items-start space-x-2.5">
                    <div className="w-7 h-7 rounded-lg bg-[#ffe500]/10 border border-[#ffe500]/30 text-[#ffe500] flex items-center justify-center flex-shrink-0 mt-0.5">
                      <Bot className="w-3.5 h-3.5 animate-pulse" />
                    </div>
                    <div className="bg-[#18181b] border border-[#27272a] rounded-2xl rounded-tl-sm p-3 px-4 flex items-center space-x-2 text-neutral-400 text-xs shadow-sm">
                      <div className="flex space-x-1">
                        <span className="w-1.5 h-1.5 bg-[#ffe500] rounded-full animate-bounce [animation-delay:-0.3s]" />
                        <span className="w-1.5 h-1.5 bg-[#ffe500] rounded-full animate-bounce [animation-delay:-0.15s]" />
                        <span className="w-1.5 h-1.5 bg-[#ffe500] rounded-full animate-bounce" />
                      </div>
                      <span className="text-[11px] font-semibold text-neutral-300">
                        {isEn ? "Tutor is thinking..." : "Tutor pensando..."}
                      </span>
                    </div>
                  </div>
                )}

                <div ref={messagesEndRef} />
              </>
            )}
          </div>

          {/* Campo de Entrada de Mensagem (Footer) */}
          <div className="p-3 bg-[#141416] border-t border-[#222226]">
            <form onSubmit={handleSendMessage} className="relative flex items-end space-x-2">
              <textarea
                ref={inputRef}
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder={isEn ? "Ask a question about this lesson..." : "Tire sua dúvida sobre esta aula..."}
                rows={1}
                disabled={sending}
                className="flex-1 bg-[#18181b] text-white placeholder-neutral-500 text-xs sm:text-sm rounded-xl px-3.5 py-2.5 border border-[#2e2e33] focus:border-[#ffe500]/60 focus:outline-none resize-none min-h-[42px] max-h-[100px] leading-relaxed transition-all"
              />
              <button
                type="submit"
                disabled={!inputMessage.trim() || sending}
                className={`p-2.5 rounded-xl flex items-center justify-center transition-all ${
                  inputMessage.trim() && !sending
                    ? "bg-[#ffe500] hover:bg-[#ffd000] text-black shadow-md cursor-pointer"
                    : "bg-[#222226] text-neutral-500 cursor-not-allowed"
                }`}
                aria-label={isEn ? "Send question" : "Enviar pergunta"}
                title={isEn ? "Send (Enter)" : "Enviar (Enter)"}
              >
                {sending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
              </button>
            </form>
            <div className="flex items-center text-[10px] text-neutral-500 mt-2 px-1">
              <span>
                {isEn ? (
                  <>Press <strong>Enter</strong> to send</>
                ) : (
                  <>Pressione <strong>Enter</strong> para enviar</>
                )}
              </span>
            </div>
          </div>
        </aside>
      )}
    </>
  );
}
