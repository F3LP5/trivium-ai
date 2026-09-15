import os
import json
from pathlib import Path
from typing import Dict, Any
from dotenv import dotenv_values

SETTINGS_FILE = Path(__file__).resolve().parent.parent.parent / "storage" / "settings.json"
SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)

ROOT_ENV = Path(__file__).resolve().parent.parent.parent.parent / ".env"
BACKEND_ENV = Path(__file__).resolve().parent.parent.parent / ".env"

DEFAULT_SETTINGS = {
    "image_provider": "openai",      # "openai", "fal", "google", "huggingface", "disabled"
    "image_aspect_ratio": "1:1",     # "1:1", "16:9", "4:3"
    "image_quality": "standard",     # "standard", "hd"
    "image_model": "dall-e-3",
    "fal_api_key": "",
    "hf_token": "",
    "gemini_api_key": "",
    "openai_api_key": "",
    "openrouter_api_key": "",
    "anthropic_api_key": "",
    "llm_provider": "openrouter",    # "openrouter", "openai", "anthropic", "local", "ollama"
    "openai_models": "gpt-4o-mini, gpt-4o, o3-mini",
    "anthropic_models": "claude-3-5-sonnet-20241022, claude-3-5-haiku-20241022, claude-3-7-sonnet-20250219",
    "openrouter_models": "nvidia/nemotron-3-super-120b-a12b:free, nex-agi/nex-n2.5-pro:free, thinkingmachines/inkling:free, nex-agi/nex-n2.5-mini:free, liquid/lfm-2.5-2.6b:free",
    "local_base_url": "http://localhost:11434/v1",
    "local_models": "llama3.1:latest, qwen2.5:14b, deepseek-r1:8b, mistral:latest",
    "local_api_key": ""
}

class SettingsService:
    @classmethod
    def get_settings(cls) -> Dict[str, Any]:
        env_data = {}
        for p in [ROOT_ENV, BACKEND_ENV]:
            if p.exists():
                try:
                    env_data.update(dotenv_values(p))
                except Exception:
                    pass

        settings = dict(DEFAULT_SETTINGS)

        if env_data.get("HF_TOKEN"):
            settings["hf_token"] = env_data.get("HF_TOKEN")
        if env_data.get("GEMINI_API_KEY"):
            settings["gemini_api_key"] = env_data.get("GEMINI_API_KEY")
        if env_data.get("OPENAI_API_KEY"):
            settings["openai_api_key"] = env_data.get("OPENAI_API_KEY")
        if env_data.get("OPENROUTER_API_KEY"):
            settings["openrouter_api_key"] = env_data.get("OPENROUTER_API_KEY")
        if env_data.get("ANTHROPIC_API_KEY"):
            settings["anthropic_api_key"] = env_data.get("ANTHROPIC_API_KEY")
        if env_data.get("LLM_PROVIDER"):
            settings["llm_provider"] = env_data.get("LLM_PROVIDER")
        if env_data.get("OPENAI_MODELS"):
            settings["openai_models"] = env_data.get("OPENAI_MODELS")
        elif env_data.get("OPENAI_MODEL"):
            settings["openai_models"] = env_data.get("OPENAI_MODEL")
        if env_data.get("ANTHROPIC_MODELS"):
            settings["anthropic_models"] = env_data.get("ANTHROPIC_MODELS")
        elif env_data.get("ANTHROPIC_MODEL"):
            settings["anthropic_models"] = env_data.get("ANTHROPIC_MODEL")
        if env_data.get("OPENROUTER_MODELS"):
            settings["openrouter_models"] = env_data.get("OPENROUTER_MODELS")
        if env_data.get("LOCAL_BASE_URL"):
            settings["local_base_url"] = env_data.get("LOCAL_BASE_URL")
        if env_data.get("LOCAL_MODELS"):
            settings["local_models"] = env_data.get("LOCAL_MODELS")
        if env_data.get("LOCAL_API_KEY"):
            settings["local_api_key"] = env_data.get("LOCAL_API_KEY")
        if env_data.get("IMAGE_PROVIDER"):
            settings["image_provider"] = env_data.get("IMAGE_PROVIDER")
        if env_data.get("IMAGE_ASPECT_RATIO"):
            settings["image_aspect_ratio"] = env_data.get("IMAGE_ASPECT_RATIO")
        if env_data.get("IMAGE_QUALITY"):
            settings["image_quality"] = env_data.get("IMAGE_QUALITY")

        if env_data.get("FAL_KEY"):
            settings["fal_api_key"] = env_data.get("FAL_KEY")
        elif env_data.get("FAL_API_KEY"):
            settings["fal_api_key"] = env_data.get("FAL_API_KEY")
        if env_data.get("IMAGE_MODEL"):
            settings["image_model"] = env_data.get("IMAGE_MODEL")

        if SETTINGS_FILE.exists():
            try:
                saved = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
                for k, v in saved.items():
                    if v is not None and v != "":
                        settings[k] = v
                    elif k in ["image_provider", "image_model", "llm_provider", "openai_models", "anthropic_models", "image_aspect_ratio", "image_quality", "local_base_url", "local_models", "local_api_key"]:
                        settings[k] = v
                # Compatibilidade legada
                if "openai_model" in saved and "openai_models" not in saved:
                    settings["openai_models"] = saved["openai_model"]
                if "anthropic_model" in saved and "anthropic_models" not in saved:
                    settings["anthropic_models"] = saved["anthropic_model"]
            except Exception:
                pass

        return settings

    @classmethod
    def get_public_settings(cls) -> Dict[str, Any]:
        raw = cls.get_settings()
        
        def mask(val: str) -> str:
            if not val or len(val) < 8:
                return "••••••••" if val else ""
            return f"{val[:4]}••••••••{val[-4:]}"

        return {
            "image_provider": raw.get("image_provider", "openai"),
            "image_aspect_ratio": raw.get("image_aspect_ratio", "1:1"),
            "image_quality": raw.get("image_quality", "standard"),
            "image_model": raw.get("image_model", DEFAULT_SETTINGS["image_model"]),
            "has_fal_api_key": bool(raw.get("fal_api_key")),
            "fal_api_key_preview": mask(raw.get("fal_api_key", "")),
            "has_hf_token": bool(raw.get("hf_token")),
            "hf_token_preview": mask(raw.get("hf_token", "")),
            "has_gemini_api_key": bool(raw.get("gemini_api_key")),
            "gemini_api_key_preview": mask(raw.get("gemini_api_key", "")),
            "has_openai_api_key": bool(raw.get("openai_api_key")),
            "openai_api_key_preview": mask(raw.get("openai_api_key", "")),
            "has_openrouter_api_key": bool(raw.get("openrouter_api_key")),
            "openrouter_api_key_preview": mask(raw.get("openrouter_api_key", "")),
            "has_anthropic_api_key": bool(raw.get("anthropic_api_key")),
            "anthropic_api_key_preview": mask(raw.get("anthropic_api_key", "")),
            "llm_provider": raw.get("llm_provider", "openrouter"),
            "openai_models": raw.get("openai_models", DEFAULT_SETTINGS["openai_models"]),
            "anthropic_models": raw.get("anthropic_models", DEFAULT_SETTINGS["anthropic_models"]),
            "openrouter_models": raw.get("openrouter_models", DEFAULT_SETTINGS["openrouter_models"]),
            "local_base_url": raw.get("local_base_url", DEFAULT_SETTINGS["local_base_url"]),
            "local_models": raw.get("local_models", DEFAULT_SETTINGS["local_models"]),
            "has_local_api_key": bool(raw.get("local_api_key")),
            "local_api_key_preview": mask(raw.get("local_api_key", ""))
        }

    @classmethod
    def update_settings(cls, updates: Dict[str, Any]) -> Dict[str, Any]:
        current = cls.get_settings()
        for k, v in updates.items():
            if k in current and v is not None:
                current[k] = v

        SETTINGS_FILE.write_text(json.dumps(current, indent=2, ensure_ascii=False), encoding="utf-8")

        if current.get("fal_api_key"):
            os.environ["FAL_KEY"] = current["fal_api_key"]
        if current.get("hf_token"):
            os.environ["HF_TOKEN"] = current["hf_token"]
        if current.get("gemini_api_key"):
            os.environ["GEMINI_API_KEY"] = current["gemini_api_key"]
        if current.get("openai_api_key"):
            os.environ["OPENAI_API_KEY"] = current["openai_api_key"]
        if current.get("openrouter_api_key"):
            os.environ["OPENROUTER_API_KEY"] = current["openrouter_api_key"]
        if current.get("anthropic_api_key"):
            os.environ["ANTHROPIC_API_KEY"] = current["anthropic_api_key"]
        if current.get("llm_provider"):
            os.environ["LLM_PROVIDER"] = current["llm_provider"]
        if current.get("openai_model"):
            os.environ["OPENAI_MODEL"] = current["openai_model"]
        if current.get("anthropic_model"):
            os.environ["ANTHROPIC_MODEL"] = current["anthropic_model"]
        if current.get("openrouter_models"):
            os.environ["OPENROUTER_MODELS"] = current["openrouter_models"]
        if current.get("local_base_url"):
            os.environ["LOCAL_BASE_URL"] = current["local_base_url"]
        if current.get("local_models"):
            os.environ["LOCAL_MODELS"] = current["local_models"]
        if current.get("local_api_key") is not None:
            os.environ["LOCAL_API_KEY"] = current["local_api_key"]
        if current.get("image_provider"):
            os.environ["IMAGE_PROVIDER"] = current["image_provider"]
        if current.get("image_model"):
            os.environ["IMAGE_MODEL"] = current["image_model"]
        if current.get("image_aspect_ratio"):
            os.environ["IMAGE_ASPECT_RATIO"] = current["image_aspect_ratio"]
        if current.get("image_quality"):
            os.environ["IMAGE_QUALITY"] = current["image_quality"]

        return cls.get_public_settings()
