import os
import re
import json
import asyncio
import litellm
from json_repair import repair_json
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_random_exponential, retry_if_exception_type

# Carrega chaves de .env
load_dotenv(dotenv_path='../.env')
load_dotenv()

OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
MODELS_RAW = os.getenv('OPENROUTER_MODELS', 'minimax/minimax-m3:free,nvidia/nemotron-3-ultra-550b-a55b:free')
MODELS = [f'openrouter/{m.strip()}' for m in MODELS_RAW.split(',') if m.strip()]

AGENTIC_HEADERS = {
    "User-Agent": "OpenCode/1.0",
    "HTTP-Referer": "https://opencode.ai",
    "X-Title": "OpenCode"
}

class LLMGateway:
    _rr_counter = 0

    @classmethod
    def get_rotated_models(cls, preferred_model: str = None) -> list:
        all_models = cls.get_models()
        if not all_models:
            return []
        if preferred_model:
            pref = f"openrouter/{preferred_model}" if not preferred_model.startswith("openrouter/") else preferred_model
            return [pref] + [m for m in all_models if m != pref]
        cls._rr_counter = (cls._rr_counter + 1) % len(all_models)
        idx = cls._rr_counter
        return all_models[idx:] + all_models[:idx]

    @staticmethod
    def get_models():
        try:
            from app.services.settings_service import SettingsService
            models_raw = SettingsService.get_settings().get("openrouter_models", "")
        except Exception:
            models_raw = ""
        if not models_raw:
            models_raw = os.getenv("OPENROUTER_MODELS", "meta-llama/llama-3.3-70b-instruct, qwen/qwen-2.5-72b-instruct, meta-llama/llama-3.1-8b-instruct")
        return [f"openrouter/{m.strip()}" if not m.strip().startswith("openrouter/") else m.strip() for m in models_raw.split(",") if m.strip()]

    @classmethod
    def get_execution_plan(cls, preferred_model: str = None, max_tokens: int = 2000) -> list:
        """
        Retorna a lista ordenada de planos de execução para litellm com base na preferência
        ativa do usuário (Local/Ollama, OpenRouter, OpenAI ou Anthropic Claude), com fallbacks de segurança.
        """
        try:
            from app.services.settings_service import SettingsService
            settings = SettingsService.get_settings()
        except Exception:
            settings = {}

        provider = settings.get("llm_provider", "openrouter").lower()
        plan = []

        reasoning_budget = min(350, max(80, max_tokens // 4))

        if provider in ["local", "ollama"]:
            local_base = settings.get("local_base_url") or os.getenv("LOCAL_BASE_URL") or "http://localhost:11434/v1"
            clean_base = local_base.strip().rstrip("/")
            if not clean_base.endswith("/v1"):
                clean_base = f"{clean_base}/v1"

            local_key = settings.get("local_api_key") or os.getenv("LOCAL_API_KEY") or "ollama"
            raw_models = settings.get("local_models") or os.getenv("LOCAL_MODELS") or "llama3.1:latest, qwen2.5:14b, deepseek-r1:8b, mistral:latest"
            parsed_models = [m.strip() for m in raw_models.split(",") if m.strip()]
            if preferred_model and preferred_model not in parsed_models:
                parsed_models.insert(0, preferred_model)

            for m in parsed_models:
                clean_m = m
                if clean_m.startswith("ollama/"):
                    clean_m = clean_m[len("ollama/"):]
                litellm_model = clean_m if clean_m.startswith("openai/") else f"openai/{clean_m}"
                plan.append({
                    "model": litellm_model,
                    "raw_model": clean_m,
                    "api_key": local_key,
                    "api_base": clean_base,
                    "provider": "local",
                    "extra_headers": {},
                    "extra_body": {
                        "options": {
                            "num_ctx": 8192,
                            "temperature": 0.3
                        }
                    }
                })

        elif provider == "openai":
            openai_key = settings.get("openai_api_key") or os.getenv("OPENAI_API_KEY")
            raw_models = settings.get("openai_models") or settings.get("openai_model") or "gpt-4o-mini, gpt-4o, o3-mini"
            parsed_models = [m.strip() for m in raw_models.split(",") if m.strip()]
            if preferred_model and preferred_model not in parsed_models:
                parsed_models.insert(0, preferred_model)
            if openai_key:
                for m in parsed_models:
                    plan.append({
                        "model": m if "/" in m else f"openai/{m}",
                        "raw_model": m,
                        "api_key": openai_key,
                        "provider": "openai",
                        "extra_headers": {},
                        "extra_body": {}
                    })

        elif provider == "anthropic":
            claude_key = settings.get("anthropic_api_key") or os.getenv("ANTHROPIC_API_KEY")
            raw_models = settings.get("anthropic_models") or settings.get("anthropic_model") or "claude-3-5-sonnet-20241022, claude-3-5-haiku-20241022, claude-3-7-sonnet-20250219"
            parsed_models = [m.strip() for m in raw_models.split(",") if m.strip()]
            if preferred_model and preferred_model not in parsed_models:
                parsed_models.insert(0, preferred_model)
            if claude_key:
                for m in parsed_models:
                    plan.append({
                        "model": m if "/" in m else f"anthropic/{m}",
                        "raw_model": m,
                        "api_key": claude_key,
                        "provider": "anthropic",
                        "extra_headers": {},
                        "extra_body": {}
                    })

        # Modelos OpenRouter (sempre disponíveis como opção principal ou fallback final)
        openrouter_key = settings.get("openrouter_api_key") or os.getenv("OPENROUTER_API_KEY")
        if openrouter_key:
            or_models = cls.get_rotated_models(preferred_model if provider == "openrouter" else None)
            for m in or_models:
                plan.append({
                    "model": m,
                    "raw_model": m,
                    "api_key": openrouter_key,
                    "provider": "openrouter",
                    "extra_headers": AGENTIC_HEADERS,
                    "extra_body": {"reasoning": {"max_tokens": reasoning_budget}}
                })

        return plan

    @staticmethod
    async def generate_structured(
        system_prompt: str,
        user_prompt: str,
        schema_class,
        preferred_model: str = None,
        max_tokens: int = 2000,
        timeout: int = 35
    ):
        execution_plan = LLMGateway.get_execution_plan(preferred_model, max_tokens)
        if not execution_plan:
            raise RuntimeError("Nenhum provedor de LLM configurado com chave de API válida (OpenRouter, OpenAI, Claude ou Local/Ollama).")

        last_error = None

        for item in execution_plan:
            model = item["model"]
            api_key = item["api_key"]
            api_base = item.get("api_base")
            provider = item.get("provider", "")
            extra_headers = item.get("extra_headers") or {}
            extra_body = item.get("extra_body") or {}

            effective_timeout = max(timeout, 120) if provider == "local" else timeout

            try:
                await asyncio.sleep(0.2)
                call_kwargs = {
                    "model": model,
                    "api_key": api_key,
                    "messages": [
                        {'role': 'system', 'content': f'{system_prompt}\n\nIMPORTANTE: Voce DEVE responder exclusivamente com um objeto JSON valido.'},
                        {'role': 'user', 'content': user_prompt}
                    ],
                    "max_tokens": max_tokens
                }
                if api_base:
                    call_kwargs["api_base"] = api_base
                if provider == "local":
                    call_kwargs["response_format"] = {"type": "json_object"}
                if extra_headers:
                    call_kwargs["extra_headers"] = extra_headers
                if extra_body:
                    call_kwargs["extra_body"] = extra_body

                response = await asyncio.wait_for(
                    litellm.acompletion(**call_kwargs),
                    timeout=effective_timeout
                )
                if not response or not getattr(response, "choices", None) or not response.choices:
                    raise ValueError(f"Resposta vazia ou sem escolhas da API no modelo {model}")

                first_choice = response.choices[0]
                if not first_choice:
                    raise ValueError(f"Primeira escolha nula retornada pelo modelo {model}")

                msg = getattr(first_choice, "message", None)
                content = getattr(msg, "content", None) or getattr(msg, "reasoning_content", None) or ""
                if not str(content).strip() and hasattr(first_choice, "provider_specific_fields") and isinstance(first_choice.provider_specific_fields, dict):
                    content = first_choice.provider_specific_fields.get("reasoning", "")

                raw_content = str(content).strip()
                if not raw_content:
                    raise ValueError(f"Conteúdo textual nulo retornado pelo modelo {model}")
                
                # 1. Higieniza tags <think>...</think> antes de qualquer recorte de chaves JSON
                raw_content = re.sub(r'<think>.*?</think>', '', raw_content, flags=re.DOTALL).strip()

                # 2. Remove blocos de markdown ```json ... ``` se o modelo tiver envelopado
                if raw_content.startswith("```"):
                    raw_content = re.sub(r'^```(?:json)?\s*', '', raw_content, flags=re.IGNORECASE)
                    raw_content = re.sub(r'\s*```$', '', raw_content).strip()

                # 3. Extracao robusta do objeto JSON
                start = raw_content.find("{")
                end = raw_content.rfind("}")
                if start != -1 and end != -1 and end > start:
                    raw_content = raw_content[start:end+1]
                
                try:
                    parsed_json = json.loads(raw_content)
                except Exception:
                    repaired = repair_json(raw_content)
                    parsed_json = json.loads(repaired) if isinstance(repaired, str) else repaired

                if isinstance(parsed_json, list):
                    parsed_json = {"mcq": parsed_json}
                elif not isinstance(parsed_json, dict):
                    parsed_json = {}

                return schema_class(**parsed_json)
            except Exception as e:
                last_error = e
                err_str = str(e).lower()
                err_desc = f"{type(e).__name__}: {str(e)}" if str(e) else f"{type(e).__name__} (Tempo limite esgotado)"
                if "connection refused" in err_str or "connecterror" in err_str:
                    err_desc = f"Servidor local inacessível ({api_base or model}). Certifique-se de que o Ollama/LM Studio está em execução ('ollama serve')."
                elif "not found" in err_str and "model" in err_str:
                    raw_name = item.get("raw_model", model)
                    err_desc = f"Modelo local '{raw_name}' não encontrado no servidor. Execute 'ollama run {raw_name}' para baixá-lo."
                elif "in_flight_budget" in err_str or "retry-after" in err_str:
                    print(f'[LLMGateway] Limite de concorrência atingido ({model}). Aguardando 5s para liberação...')
                    await asyncio.sleep(5)
                print(f'[LLMGateway] Falha estruturada com modelo {model} ({provider}): {err_desc}. Tentando próximo modelo do plano...')
                continue
        
        raise RuntimeError(f'Todos os modelos do gateway falharam. Último erro: {last_error}')

    @staticmethod
    async def generate_text(
        system_prompt: str,
        user_prompt: str,
        preferred_model: str = None,
        max_tokens: int = 2000,
        timeout: int = 35
    ) -> str:
        execution_plan = LLMGateway.get_execution_plan(preferred_model, max_tokens)
        if not execution_plan:
            raise RuntimeError("Nenhum provedor de LLM configurado com chave de API válida (OpenRouter, OpenAI, Claude ou Local/Ollama).")

        last_error = None

        for item in execution_plan:
            model = item["model"]
            api_key = item["api_key"]
            api_base = item.get("api_base")
            provider = item.get("provider", "")
            extra_headers = item.get("extra_headers") or {}
            extra_body = item.get("extra_body") or {}

            effective_timeout = max(timeout, 180) if provider == "local" else timeout

            try:
                await asyncio.sleep(0.2)
                call_kwargs = {
                    "model": model,
                    "api_key": api_key,
                    "messages": [
                        {'role': 'system', 'content': system_prompt},
                        {'role': 'user', 'content': user_prompt}
                    ],
                    "max_tokens": max_tokens
                }
                if api_base:
                    call_kwargs["api_base"] = api_base
                if extra_headers:
                    call_kwargs["extra_headers"] = extra_headers
                if extra_body:
                    call_kwargs["extra_body"] = extra_body

                response = await asyncio.wait_for(
                    litellm.acompletion(**call_kwargs),
                    timeout=effective_timeout
                )
                if not response or not getattr(response, "choices", None) or not response.choices:
                    raise ValueError(f"Resposta vazia ou sem escolhas da API no modelo {model}")

                first_choice = response.choices[0]
                if not first_choice:
                    raise ValueError(f"Primeira escolha nula retornada pelo modelo {model}")

                msg = getattr(first_choice, "message", None)
                content = getattr(msg, "content", None) or getattr(msg, "reasoning_content", None) or getattr(msg, "reasoning", None) or ""
                if not str(content).strip() and hasattr(first_choice, "provider_specific_fields") and isinstance(first_choice.provider_specific_fields, dict):
                    content = first_choice.provider_specific_fields.get("reasoning", "")
                text = str(content).strip()
                if not text:
                    raise ValueError(f"Conteúdo textual nulo retornado pelo modelo {model}")

                # Limpa tags <think>...</think> se existirem
                cleaned_text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()

                # Se o texto começar com preâmbulo/anotação de raciocínio antes do título da aula ('## ' ou '# '), localiza e corta
                first_header_match = re.search(r'^(#{1,3}\s+[^\n]+)', cleaned_text, flags=re.MULTILINE)
                if first_header_match and first_header_match.start() > 0:
                    prefix = cleaned_text[:first_header_match.start()].strip()
                    cot_keywords = ["user wants", "we need", "i need", "let's", "need", "hook paragraph", "potential text", "case study", "guidelines", "title", "start with"]
                    if any(kw in prefix.lower() for kw in cot_keywords) or (len(prefix.split()) > 5 and not prefix.startswith(">")):
                        cleaned_text = cleaned_text[first_header_match.start():].strip()

                return cleaned_text or text
            except Exception as e:
                last_error = e
                err_str = str(e).lower()
                err_desc = f"{type(e).__name__}: {str(e)}" if str(e) else f"{type(e).__name__} (Tempo limite esgotado)"
                if "connection refused" in err_str or "connecterror" in err_str:
                    err_desc = f"Servidor local inacessível ({api_base or model}). Certifique-se de que o Ollama/LM Studio está em execução ('ollama serve')."
                elif "not found" in err_str and "model" in err_str:
                    raw_name = item.get("raw_model", model)
                    err_desc = f"Modelo local '{raw_name}' não encontrado no servidor. Execute 'ollama run {raw_name}' para baixá-lo."
                elif "in_flight_budget" in err_str or "retry-after" in err_str or "free-models-per-min" in err_str or "429" in err_str:
                    print(f'[LLMGateway] Limite de concorrência ou taxa atingido ({model}). Aguardando 4s para estabilização...')
                    await asyncio.sleep(4)
                print(f'[LLMGateway] Falha de texto com {model} ({provider}): {err_desc}. Tentando próximo modelo do plano...')
                continue
        raise RuntimeError(f'Falha ao gerar texto com os modelos. Último erro: {last_error}')

    @staticmethod
    async def benchmark_free_models() -> dict:
        """
        Executa uma auditoria concorrente fail-fast (< 2 minutos) em todos os modelos gratuitos do OpenRouter.
        Avalia aderência real ao framework Trivium:
        1. Conformidade com regras de redação (sem primeira pessoa 'eu', sem travessão '—')
        2. Capacidade de densidade textual (contagem de palavras e desenvolvimento)
        3. Suporte a JSON e estrutura analítica
        4. Latência e estabilidade da API
        Ranqueia com score composto (0-100) priorizando os melhores para a esteira Trivium.
        """
        import urllib.request
        import time
        from app.services.settings_service import SettingsService

        t_start = time.time()
        api_key = SettingsService.get_settings().get("openrouter_api_key") or os.getenv("OPENROUTER_API_KEY")

        try:
            req = urllib.request.Request(
                "https://openrouter.ai/api/v1/models",
                headers={"User-Agent": "Trivium/1.0"}
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))["data"]
                free_models = [m["id"] for m in data if ":free" in m.get("id", "")]
        except Exception as err:
            raise RuntimeError(f"Falha ao consultar catálogo de modelos do OpenRouter: {err}")

        # Filtra modelos de nicho estrito irrelevantes para geração de texto (ex: safety filters)
        ignored_models = {"nvidia/nemotron-3.5-content-safety:free"}
        target_models = [m for m in free_models if m not in ignored_models]

        # Limite concorrente para evitar 429 mas terminar em menos de 2 minutos
        sem = asyncio.Semaphore(5)

        # Probe realista do framework Trivium: micro-aula com regras estritas
        test_system = (
            "Você é um professor catedrático da Trivium Academy. "
            "Escreva uma mini-aula didática de introdução sobre 'Como a Internet Funciona' para nível Iniciante.\n"
            "REGRAS ESTRITAS DE COMPLIANCE:\n"
            "1. PROIBIDO usar primeira pessoa do singular ('eu', 'percebi', 'acho')!\n"
            "2. PROIBIDO usar o símbolo travessão ('—' ou '–')!\n"
            "3. Desenvolva no mínimo 150 palavras explicando a diferença entre roteador e internet com uma analogia simples.\n"
            "4. Inclua um bloco '> Regra de Ouro: [princípio em 1 frase]'.\n"
            "5. Responda em Markdown limpo."
        )
        test_user = "Redija a mini-aula agora cumprindo rigorosamente as 4 regras sem desculpas nem metadiscurso."

        async def _probe_single(model_id: str):
            async with sem:
                t0 = time.time()
                try:
                    res = await asyncio.wait_for(
                        litellm.acompletion(
                            model=f"openrouter/{model_id}",
                            api_key=api_key,
                            messages=[
                                {"role": "system", "content": test_system},
                                {"role": "user", "content": test_user}
                            ],
                            max_tokens=650,
                            extra_headers=AGENTIC_HEADERS,
                            extra_body={"reasoning": {"max_tokens": 120}}
                        ),
                        timeout=30.0
                    )
                    elapsed = round(time.time() - t0, 2)
                    if not res or not getattr(res, "choices", None) or not res.choices:
                        return {"model": model_id, "success": False, "error": "Resposta vazia da API", "latency": elapsed, "score": 0}

                    msg = res.choices[0].message
                    content = getattr(msg, "content", None) or getattr(msg, "reasoning_content", None) or ""
                    if not str(content).strip() and hasattr(res.choices[0], "provider_specific_fields") and isinstance(res.choices[0].provider_specific_fields, dict):
                        content = res.choices[0].provider_specific_fields.get("reasoning", "")
                    
                    text = str(content).strip()
                    if not text:
                        return {"model": model_id, "success": False, "error": "Conteúdo nulo ou consumido só em reasoning", "latency": elapsed, "score": 0}

                    # Avaliação analítica de aderência ao Framework Trivium (Score 0-100)
                    words = len(re.findall(r'\b\w+\b', text))
                    
                    # 1. Checagem de Proibições Trivium
                    has_first_person = bool(re.search(r'\b(eu|percebi|acho|minha opini[aã]o|acredito)\b', text, flags=re.IGNORECASE))
                    has_em_dash = bool(re.search(r'[—–]', text))
                    has_golden_rule = bool(re.search(r'Regra de Ouro', text, flags=re.IGNORECASE))

                    # 2. Cálculo do Score de Conformidade
                    # Base por resposta válida: 30 pontos
                    score = 30
                    
                    # Volume textual (até 35 pontos) - penaliza modelos telegráficos/curtos
                    if words >= 140:
                        score += 35
                    elif words >= 90:
                        score += 20
                    else:
                        score += 8
                    
                    # Cumprimento de regras editoriais (até 25 pontos)
                    if not has_first_person:
                        score += 10
                    if not has_em_dash:
                        score += 10
                    if has_golden_rule:
                        score += 5

                    # Bônus de Latência (até 10 pontos)
                    if elapsed < 8.0:
                        score += 10
                    elif elapsed < 16.0:
                        score += 5

                    # Flags de conformidade
                    compliance_notes = []
                    if words >= 140:
                        compliance_notes.append("Denso")
                    else:
                        compliance_notes.append("Curto")
                    if not has_first_person and not has_em_dash:
                        compliance_notes.append("Regras OK")
                    else:
                        if has_first_person: compliance_notes.append("Usou 1ª Pessoa")
                        if has_em_dash: compliance_notes.append("Usou Travessão")

                    return {
                        "model": model_id,
                        "success": True,
                        "score": score,
                        "words": words,
                        "latency": elapsed,
                        "has_first_person": has_first_person,
                        "has_em_dash": has_em_dash,
                        "compliance": " | ".join(compliance_notes),
                        "sample": text[:90].replace("\n", " ") + "..."
                    }
                except asyncio.TimeoutError:
                    return {"model": model_id, "success": False, "error": "Timeout (> 30s)", "latency": 30.0, "score": 0}
                except Exception as ex:
                    err_msg = str(ex).split("\n")[0][:80]
                    if "429" in err_msg or "rate limit" in err_msg.lower():
                        err_msg = "Rate Limit (429)"
                    return {"model": model_id, "success": False, "error": err_msg, "latency": round(time.time() - t0, 2), "score": 0}

        tasks = [_probe_single(m) for m in target_models]
        results = await asyncio.gather(*tasks)

        approved = [r for r in results if r["success"] and r.get("score", 0) >= 40]
        rejected = [r for r in results if not r["success"] or r.get("score", 0) < 40]

        # Ranquear: Score mais alto primeiro, desempatando por latência mais rápida
        approved.sort(key=lambda x: (-x["score"], x["latency"]))

        total_time = round(time.time() - t_start, 2)
        # Monta a lista CSV dos melhores modelos para geração de cursos
        recommended_csv = ", ".join([a["model"] for a in approved])

        return {
            "total_scanned": len(free_models),
            "approved_count": len(approved),
            "rejected_count": len(rejected),
            "benchmark_duration_seconds": total_time,
            "recommended_csv": recommended_csv,
            "approved_models": approved,
            "rejected_models": rejected
        }
