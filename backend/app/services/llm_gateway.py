import os
import re
import json
import time
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
    "HTTP-Referer": "https://github.com/cline/cline",
    "X-Title": "Cline",
    "User-Agent": "Cline/3.0.0"
}

class LLMGateway:
    _rr_counter = 0
    # Circuit Breaker & Health Tracking
    # Formato: {model_name: {"status": "healthy"|"quarantined"|"half_open", "quarantine_until": float, "failures": int, "total_timeouts": int, "successes": int, "last_error": str}}
    _circuit_state = {}

    @classmethod
    def record_success(cls, model: str):
        state = cls._circuit_state.setdefault(model, {
            "status": "healthy",
            "quarantine_until": 0.0,
            "failures": 0,
            "total_timeouts": 0,
            "successes": 0,
            "last_error": ""
        })
        now = time.time()
        # Se estiver em quarentena ativa, requisições concorrentes anteriores NÃO quebram a quarentena
        if state["status"] == "quarantined":
            if now < state["quarantine_until"]:
                return
            state["status"] = "half_open"

        if state["status"] == "half_open":
            print(f"[CircuitBreaker] [RECUPERADO] Modelo {model} respondeu com sucesso em prova! Circuito FECHADO (Healthy).")
            state["status"] = "healthy"
            state["failures"] = 0
            state["quarantine_until"] = 0.0
        elif state["status"] == "healthy":
            state["failures"] = 0

        state["successes"] += 1

    @classmethod
    def record_failure(cls, model: str, error: Exception):
        now = time.time()
        state = cls._circuit_state.setdefault(model, {
            "status": "healthy",
            "quarantine_until": 0.0,
            "failures": 0,
            "total_timeouts": 0,
            "successes": 0,
            "last_error": ""
        })
        state["failures"] += 1
        state["last_error"] = str(error)

        err_str = str(error).lower()
        is_timeout = isinstance(error, (asyncio.TimeoutError, TimeoutError)) or "timeout" in err_str or "timed out" in err_str
        is_rate_limit = "429" in err_str or "rate limit" in err_str or "free-models-per-min" in err_str

        if is_timeout:
            state["total_timeouts"] += 1
            state["status"] = "quarantined"
            state["quarantine_until"] = now + 180.0  # 3 minutos de quarentena
            print(f"[CircuitBreaker] [QUARENTENA] Modelo {model} entrou em QUARENTENA por 180s apos TimeoutError. Sera ignorado nas proximas requisicoes primarias.")
        elif is_rate_limit:
            state["status"] = "quarantined"
            state["quarantine_until"] = now + 90.0  # 90s de quarentena
            print(f"[CircuitBreaker] [QUARENTENA] Modelo {model} entrou em QUARENTENA por 90s apos Rate Limit (429).")
        elif state["failures"] >= 2:
            state["status"] = "quarantined"
            state["quarantine_until"] = now + 120.0  # 2 minutos
            print(f"[CircuitBreaker] [QUARENTENA] Modelo {model} entrou em QUARENTENA por 120s apos {state['failures']} falhas consecutivas.")

    @classmethod
    def get_circuit_state(cls, model: str) -> dict:
        now = time.time()
        state = cls._circuit_state.setdefault(model, {
            "status": "healthy",
            "quarantine_until": 0.0,
            "failures": 0,
            "total_timeouts": 0,
            "successes": 0,
            "last_error": ""
        })
        if state["status"] == "quarantined" and now >= state["quarantine_until"]:
            state["status"] = "half_open"
        return state

    @classmethod
    def get_rotated_models(cls, preferred_model: str = None) -> list:
        all_models = cls.get_models()
        if not all_models:
            return []

        healthy_models = []
        half_open_models = []
        quarantined_models = []

        for m in all_models:
            st = cls.get_circuit_state(m)
            if st["status"] == "healthy":
                healthy_models.append(m)
            elif st["status"] == "half_open":
                half_open_models.append(m)
            else:
                quarantined_models.append(m)

        # Prioriza modelos saudáveis e em prova (half_open)
        available_pool = healthy_models + half_open_models
        if not available_pool:
            # Fallback de sobrevivência: se todos estiverem em quarentena, usa o mais próximo de expirar
            available_pool = sorted(quarantined_models, key=lambda m: cls._circuit_state.get(m, {}).get("quarantine_until", 0))
            quarantined_models = []

        if preferred_model:
            pref = f"openrouter/{preferred_model}" if not preferred_model.startswith("openrouter/") else preferred_model
            if pref in available_pool:
                ordered_avail = [pref] + [m for m in available_pool if m != pref]
            else:
                ordered_avail = available_pool
        else:
            cls._rr_counter = (cls._rr_counter + 1) % len(available_pool)
            idx = cls._rr_counter
            ordered_avail = available_pool[idx:] + available_pool[:idx]

        # Modelos em quarentena ativa vão estritamente para o fim absoluto da fila de contingência
        return ordered_avail + quarantined_models

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

            effective_timeout = max(timeout, 120) if provider == "local" else max(timeout, 30)

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

                LLMGateway.record_success(model)
                return schema_class(**parsed_json)
            except Exception as e:
                LLMGateway.record_failure(model, e)
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

            effective_timeout = max(timeout, 180) if provider == "local" else max(timeout, 40 if max_tokens >= 1500 else 35)

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

                LLMGateway.record_success(model)
                return cleaned_text or text
            except Exception as e:
                LLMGateway.record_failure(model, e)
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
        Executa auditoria fail-fast de padrão industrial em 4 camadas para os modelos gratuitos do OpenRouter:
        Camada 0: Pré-Filtragem em Memória (contexto >= 8k, elimina modelos de código puro, segurança e embeddings)
        Camada 1: Burst Stress Ping Concorrente (disparo simultâneo duplo para eliminar 429 sob concorrência e 404/403)
        Camada 2: Provas Operacionais E2E (Curator JSON Schema estrito + Redação Pedagógica Densa com Throughput TPS)
        Camada 3: Motor Avaliador Semântico & Ranqueamento (Score 0-100, corte >= 75, TPS >= 25.0 tokens/s, sem viés)
        Camada 4: Auto-Save no settings.json por ordem estrita de excelência e throughput
        """
        import urllib.request
        import time
        from app.services.settings_service import SettingsService

        t_start = time.time()
        api_key = SettingsService.get_settings().get("openrouter_api_key") or os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise RuntimeError("Chave de API do OpenRouter não configurada. Insira sua chave antes de executar o teste.")

        try:
            req = urllib.request.Request(
                "https://openrouter.ai/api/v1/models",
                headers={"User-Agent": "Trivium/1.0"}
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))["data"]
        except Exception as err:
            raise RuntimeError(f"Falha ao consultar catálogo de modelos do OpenRouter: {err}")

        # --- CAMADA 0: Pré-Filtragem Técnica em Memória (Sem viés de nomes) ---
        free_raw = [m for m in data if ":free" in m.get("id", "")]
        total_scanned = len(free_raw)

        pruned_layer0 = []
        candidates_layer0 = []

        for m in free_raw:
            m_id = m.get("id", "").lower()
            ctx = m.get("context_length", 0) or 0
            if any(k in m_id for k in ["code", "coder", "-mini-code"]):
                pruned_layer0.append({"model": m["id"], "success": False, "error": "Descartado: Modelo especializado em código", "latency": 0.0, "score": 0})
            elif any(k in m_id for k in ["safety", "guard", "moderation"]):
                pruned_layer0.append({"model": m["id"], "success": False, "error": "Descartado: Filtro de segurança/moderação", "latency": 0.0, "score": 0})
            elif "embed" in m_id:
                pruned_layer0.append({"model": m["id"], "success": False, "error": "Descartado: Modelo de embeddings", "latency": 0.0, "score": 0})
            elif ctx and ctx < 8192:
                pruned_layer0.append({"model": m["id"], "success": False, "error": f"Descartado: Janela de contexto insuficiente ({ctx} tokens)", "latency": 0.0, "score": 0})
            else:
                candidates_layer0.append(m["id"])

        # --- CAMADA 1: Burst Stress Test (< 5s) - Disparo Concorrente Duplo ---
        smoke_sem = asyncio.Semaphore(8)

        async def _burst_ping(model_id: str):
            async with smoke_sem:
                t0 = time.time()
                async def _single_ping():
                    return await asyncio.wait_for(
                        litellm.acompletion(
                            model=f"openrouter/{model_id}",
                            api_key=api_key,
                            messages=[{"role": "user", "content": "1"}],
                            max_tokens=5,
                            extra_headers=AGENTIC_HEADERS,
                            extra_body={"reasoning": {"max_tokens": 10}}
                        ),
                        timeout=4.5
                    )

                try:
                    # Dispara 2 requisições no mesmo milissegundo: se bater 429 ou estourar upstream, elimina imediatamente
                    await asyncio.gather(_single_ping(), _single_ping())
                    elapsed = round(time.time() - t0, 2)
                    return model_id, True, elapsed, "OK"
                except Exception as ex:
                    elapsed = round(time.time() - t0, 2)
                    err_msg = str(ex).lower()
                    if "429" in err_msg or "rate limit" in err_msg or "rate-limited" in err_msg:
                        clean_err = "Rate limit 429 sob concorrência"
                    elif "404" in err_msg:
                        clean_err = "Modelo indisponível (404)"
                    elif "403" in err_msg:
                        clean_err = "Acesso negado (403)"
                    elif "timeout" in err_msg or elapsed >= 4.4:
                        clean_err = "Timeout no Burst Ping (> 4.5s)"
                    else:
                        clean_err = str(ex).split("\n")[0][:60] or "Falha upstream"
                    return model_id, False, elapsed, clean_err

        smoke_results = await asyncio.gather(*[_burst_ping(m) for m in candidates_layer0])

        candidates_layer1 = []
        pruned_layer1 = []

        for m_id, ok, elapsed, reason in smoke_results:
            if ok:
                candidates_layer1.append(m_id)
            else:
                pruned_layer1.append({
                    "model": m_id,
                    "success": False,
                    "error": f"Camada 1: {reason}",
                    "latency": elapsed,
                    "score": 0
                })

        # --- CAMADA 2 & 3: Provas Operacionais E2E & Motor de Throughput (TPS) ---
        op_sem = asyncio.Semaphore(6)

        json_prompt = (
            "Retorne EXCLUSIVAMENTE um objeto JSON válido seguindo esta estrutura exata:\n"
            "{\n"
            '  "subject": "Astronomia Prática",\n'
            '  "modules": [\n'
            "    {\n"
            '      "module_number": 1,\n'
            '      "title": "O Céu Noturno",\n'
            '      "lessons": [\n'
            "        {\n"
            '          "title": "O Farol Invisível",\n'
            '          "core_concept": "Como telescópios capturam fótons ancestrais sob baixa luminosidade."\n'
            "        }\n"
            "      ]\n"
            "    }\n"
            "  ]\n"
            "}\n"
            "PROIBIDO usar as palavras 'string', 'placeholder', 'aula', ou deixar campos vazios."
        )

        writer_system = (
            "Você é um professor catedrático da Trivium Academy. "
            "Escreva uma mini-aula didática de introdução sobre 'A Inércia e o Movimento' para nível Iniciante.\n"
            "REGRAS ESTRITAS DE COMPLIANCE:\n"
            "1. PROIBIDO usar primeira pessoa do singular ('eu', 'percebi', 'acho')!\n"
            "2. PROIBIDO usar o símbolo travessão ('—' ou '–')!\n"
            "3. Desenvolva no mínimo 120 palavras explicando o princípio com um exemplo cotidiano.\n"
            "4. Inclua um bloco '> Regra de Ouro: [princípio em 1 frase]'.\n"
            "5. Responda em Markdown limpo."
        )

        async def _probe_operational(model_id: str):
            async with op_sem:
                # 1. Prova de JSON
                t_j0 = time.time()
                try:
                    res_j = await asyncio.wait_for(
                        litellm.acompletion(
                            model=f"openrouter/{model_id}",
                            api_key=api_key,
                            messages=[{"role": "user", "content": json_prompt}],
                            max_tokens=400,
                            extra_headers=AGENTIC_HEADERS,
                            extra_body={"reasoning": {"max_tokens": 80}}
                        ),
                        timeout=14.0
                    )
                    json_time = round(time.time() - t_j0, 2)
                    choice_j = res_j.choices[0]
                    content_j = getattr(choice_j.message, "content", None) or getattr(choice_j.message, "reasoning_content", None) or ""
                    if not str(content_j).strip() and hasattr(choice_j, "provider_specific_fields") and isinstance(choice_j.provider_specific_fields, dict):
                        content_j = choice_j.provider_specific_fields.get("reasoning", "")

                    raw_j = str(content_j).strip()
                    raw_j = re.sub(r'<think>.*?</think>', '', raw_j, flags=re.DOTALL).strip()
                    if raw_j.startswith("```"):
                        raw_j = re.sub(r'^```(?:json)?\s*', '', raw_j, flags=re.IGNORECASE)
                        raw_j = re.sub(r'\s*```$', '', raw_j).strip()
                    s_idx = raw_j.find("{")
                    e_idx = raw_j.rfind("}")
                    if s_idx != -1 and e_idx != -1 and e_idx > s_idx:
                        raw_j = raw_j[s_idx:e_idx+1]

                    try:
                        parsed = json.loads(raw_j)
                    except Exception:
                        rep = repair_json(raw_j)
                        parsed = json.loads(rep) if isinstance(rep, str) else rep

                    json_ok = False
                    json_err = ""
                    if isinstance(parsed, dict) and "modules" in parsed:
                        mods = parsed.get("modules", [])
                        if mods and len(mods) > 0 and isinstance(mods[0], dict):
                            lessons = mods[0].get("lessons", [])
                            if lessons and len(lessons) > 0 and isinstance(lessons[0], dict):
                                l_title = str(lessons[0].get("title", "")).strip().lower()
                                l_concept = str(lessons[0].get("core_concept", "")).strip().lower()
                                if any(ph in l_title for ph in ["string", "placeholder", "aula"]) or not l_title:
                                    json_err = f"Placeholder no título: '{l_title}'"
                                elif any(ph in l_concept for ph in ["string", "placeholder"]) or not l_concept:
                                    json_err = "Placeholder no core_concept"
                                else:
                                    json_ok = True
                            else:
                                json_err = "Lessons vazio ou malformado"
                        else:
                            json_err = "Modules vazio ou malformado"
                    else:
                        json_err = "JSON ausente ou sem chave 'modules'"
                except Exception as ex_j:
                    json_ok = False
                    json_err = str(ex_j).split("\n")[0][:50]
                    json_time = round(time.time() - t_j0, 2)

                # 2. Prova de Redação & Medição de Throughput Real (TPS)
                t_w0 = time.time()
                try:
                    res_w = await asyncio.wait_for(
                        litellm.acompletion(
                            model=f"openrouter/{model_id}",
                            api_key=api_key,
                            messages=[
                                {"role": "system", "content": writer_system},
                                {"role": "user", "content": "Redija a mini-aula agora cumprindo rigorosamente as 4 regras."}
                            ],
                            max_tokens=500,
                            extra_headers=AGENTIC_HEADERS,
                            extra_body={"reasoning": {"max_tokens": 80}}
                        ),
                        timeout=18.0
                    )
                    writer_time = max(0.1, round(time.time() - t_w0, 2))
                    choice_w = res_w.choices[0]
                    content_w = getattr(choice_w.message, "content", None) or getattr(choice_w.message, "reasoning_content", None) or ""
                    if not str(content_w).strip() and hasattr(choice_w, "provider_specific_fields") and isinstance(choice_w.provider_specific_fields, dict):
                        content_w = choice_w.provider_specific_fields.get("reasoning", "")

                    text_w = str(content_w).strip()
                    text_w = re.sub(r'<think>.*?</think>', '', text_w, flags=re.DOTALL).strip()
                    words = len(re.findall(r'\b\w+\b', text_w))

                    # Throughput real em tokens por segundo
                    usage = getattr(res_w, "usage", None)
                    comp_tokens = getattr(usage, "completion_tokens", None) or int(words * 1.35)
                    tps = round(comp_tokens / writer_time, 1)

                    has_first_person = bool(re.search(r'\b(eu|percebi|acho|minha opini[aã]o|acredito)\b', text_w, flags=re.IGNORECASE))
                    has_em_dash = bool(re.search(r'[—–]', text_w))
                    has_golden_rule = bool(re.search(r'Regra de Ouro', text_w, flags=re.IGNORECASE))
                    sample_text = text_w[:90].replace("\n", " ") + "..."

                    # Compliance estrita da redação
                    writer_ok = (words >= 100 and not has_first_person and not has_em_dash and tps >= 25.0)
                    reasons = []
                    if words < 100: reasons.append(f"Apenas {words} palavras")
                    if has_first_person: reasons.append("Usou 1ª pessoa")
                    if has_em_dash: reasons.append("Usou travessão")
                    if tps < 25.0: reasons.append(f"TPS lento: {tps} t/s (< 25)")
                    writer_err = ", ".join(reasons)
                except Exception as ex_w:
                    writer_time = round(time.time() - t_w0, 2)
                    words = 0
                    tps = 0.0
                    writer_ok = False
                    sample_text = ""
                    has_first_person, has_em_dash, has_golden_rule = False, False, False
                    writer_err = str(ex_w).split("\n")[0][:50]

                # --- Motor Avaliador Semântico Composto Trivium (0 a 100) ---
                score = 0
                if json_ok:
                    score += 35
                if words >= 120:
                    score += 25
                elif words >= 90:
                    score += 15
                elif words >= 40:
                    score += 8

                if not has_first_person:
                    score += 10
                if not has_em_dash:
                    score += 10
                if has_golden_rule:
                    score += 10

                # Bônus de Throughput / Rapidez
                if tps >= 45.0:
                    score += 10
                elif tps >= 25.0:
                    score += 5

                avg_latency = round((json_time + writer_time) / 2, 2)

                compliance_notes = []
                if json_ok:
                    compliance_notes.append("JSON ✓")
                else:
                    compliance_notes.append("JSON Falhou")

                if writer_ok:
                    compliance_notes.append(f"Redação ✓ ({tps} t/s)")
                elif words >= 90:
                    compliance_notes.append(f"Denso ({tps} t/s)")
                else:
                    compliance_notes.append(f"Curto ({tps} t/s)")

                if has_first_person: compliance_notes.append("1ª Pessoa")
                if has_em_dash: compliance_notes.append("Travessão")

                # REQUISITO DE HOMOLOGAÇÃO ESTREITO PARA O FRAMEWORK:
                # 1. Score Composto >= 75
                # 2. JSON Schema 100% válido
                # 3. Redação 100% compliant
                # 4. Throughput mínimo >= 25 tokens/s (elimina modelos lerdos que estouram timeouts)
                is_success = (score >= 75 and json_ok and writer_ok and tps >= 25.0)
                error_msg = ""
                if not is_success:
                    if not json_ok:
                        error_msg = f"Falha no JSON: {json_err}"
                    else:
                        error_msg = f"Redação/Throughput insuficiente: {writer_err or 'Score < 75'}"

                return {
                    "model": model_id,
                    "success": is_success,
                    "score": score,
                    "words": words,
                    "tps": tps,
                    "json_ready": json_ok,
                    "latency": avg_latency,
                    "has_first_person": has_first_person,
                    "has_em_dash": has_em_dash,
                    "compliance": " | ".join(compliance_notes),
                    "sample": sample_text,
                    "error": error_msg
                }

        op_results = await asyncio.gather(*[_probe_operational(m) for m in candidates_layer1])

        approved = [r for r in op_results if r["success"]]
        rejected_op = [r for r in op_results if not r["success"]]

        # Ranquear aprovados: Maior Score primeiro, desempatando por maior Throughput (TPS)
        approved.sort(key=lambda x: (-x["score"], -x["tps"]))

        # Todos os rejeitados consolidados com diagnóstico transparente
        all_rejected = pruned_layer0 + pruned_layer1 + rejected_op

        total_time = round(time.time() - t_start, 2)
        recommended_csv = ", ".join([a["model"] for a in approved])

        # Auto-save imediato no settings.json se houver modelos aprovados
        if approved:
            try:
                SettingsService.update_settings({"openrouter_models": recommended_csv})
                print(f"[LLMGateway] Modelos homologados atualizados com sucesso ({len(approved)} aprovados): {recommended_csv}")
            except Exception as save_err:
                print(f"[LLMGateway] Aviso ao persistir modelos homologados: {save_err}")

        return {
            "total_scanned": total_scanned,
            "approved_count": len(approved),
            "rejected_count": len(all_rejected),
            "benchmark_duration_seconds": total_time,
            "recommended_csv": recommended_csv,
            "approved_models": approved,
            "rejected_models": all_rejected
        }

