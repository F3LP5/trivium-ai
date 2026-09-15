import os
import re
import asyncio
import base64
import json
import urllib.request
from pathlib import Path
from typing import Optional, Tuple
from app.services.settings_service import SettingsService

STORAGE_DIR = Path(__file__).resolve().parent.parent.parent / "storage" / "images"
STORAGE_DIR.mkdir(parents=True, exist_ok=True)

class StippleImageService:
    _image_semaphore = None

    @classmethod
    def get_semaphore(cls):
        if cls._image_semaphore is None:
            cls._image_semaphore = asyncio.Semaphore(1)
        return cls._image_semaphore
    @staticmethod
    def build_stipple_prompt(subject_desc: str) -> str:
        """
        Gera o prompt editorial canônico no estilo Direção de Arte 2 Tradicional (19th-Century Classical Editorial Book Engraver):
        - Regra de no máximo 4 elementos visuais.
        - Fundo 100% preto sólido (#000000).
        - Gravura clássica em talhe-doce com sombreamento metálico e pontilhismo fino dourado e branco.
        - Ausência estrita de 'relógios', 'mostradores', setas flutuantes, textos, rostos/pessoas e molduras.
        """
        clean_desc = subject_desc.strip().strip('"').strip("'")
        return (
            "Art Direction: 19th-Century Classical Editorial Book Engraver. "
            f"Subject: {clean_desc}. "
            "Composition rules: Maximum 4 focal visual elements total, clean geometric harmony, centered on 100% solid pure pitch black background #000000 with wide negative black space. "
            "Rendering: Detailed fine-dot gold and white intaglio stipple engraving, high contrast, classical craftsmanship and organic metallurgical shading. "
            "Negative constraints: Strictly NO dials, NO clocks, NO meters, NO gauges, NO floating arrows, NO charts, NO text, NO labels, NO words, NO letters, NO human figures, NO portraits, NO faces, NO frames, NO borders, NO margins."
        )

    @classmethod
    def _generate_via_openrouter(cls, prompt: str, api_key: str, dest_path: Path) -> bool:
        try:
            req_data = {
                'model': 'google/gemini-2.5-flash-image',
                'messages': [
                    {'role': 'user', 'content': f'Generate an image: {prompt}'}
                ]
            }
            req = urllib.request.Request(
                'https://openrouter.ai/api/v1/chat/completions',
                headers={
                    'Authorization': f'Bearer {api_key}',
                    'Content-Type': 'application/json'
                },
                data=json.dumps(req_data).encode('utf-8')
            )
            with urllib.request.urlopen(req, timeout=40) as resp:
                res = json.loads(resp.read())
                msg = res['choices'][0]['message']
                if 'images' in msg and msg['images']:
                    img_item = msg['images'][0]
                    url = img_item.get('image_url', {}).get('url') if isinstance(img_item, dict) else None
                    if url and url.startswith('data:image'):
                        _, b64data = url.split(',', 1)
                        dest_path.write_bytes(base64.b64decode(b64data))
                        return dest_path.exists() and dest_path.stat().st_size > 1000
        except Exception as e:
            print(f"[StippleImageService] Erro OpenRouter: {e}")
        return False

    @classmethod
    def _generate_via_fal(cls, prompt: str, api_key: str, dest_path: Path, model: str = "fal-ai/flux/schnell", width: int = 1024, height: int = 1024) -> bool:
        try:
            clean_model = model.strip() if model and model.strip() else "fal-ai/flux/schnell"
            url = f"https://fal.run/{clean_model}"
            payload = {
                "prompt": prompt,
                "image_size": {"width": width, "height": height},
                "num_images": 1
            }
            req = urllib.request.Request(
                url,
                headers={
                    "Authorization": f"Key {api_key}",
                    "Content-Type": "application/json"
                },
                data=json.dumps(payload).encode("utf-8")
            )
            with urllib.request.urlopen(req, timeout=35) as resp:
                res = json.loads(resp.read())
                images = res.get("images", [])
                if images and images[0].get("url"):
                    img_url = images[0]["url"]
                    with urllib.request.urlopen(img_url, timeout=25) as r:
                        dest_path.write_bytes(r.read())
                    return dest_path.exists() and dest_path.stat().st_size > 1000
        except Exception as e:
            print(f"[StippleImageService] Erro Fal.ai ({model}): {e}")
        return False

    @classmethod
    def _generate_via_huggingface(cls, prompt: str, token: str, dest_path: Path, model: str = "black-forest-labs/FLUX.1-schnell", width: int = 1024, height: int = 1024) -> bool:
        try:
            from huggingface_hub import InferenceClient
            clean_model = model.strip() if model and model.strip() else "black-forest-labs/FLUX.1-schnell"
            client = InferenceClient(token=token)
            img = client.text_to_image(prompt, model=clean_model)
            img.save(dest_path, "JPEG", quality=92)
            return dest_path.exists() and dest_path.stat().st_size > 1000
        except Exception as e:
            err_str = str(e)
            if "402" in err_str or "depleted your monthly included credits" in err_str.lower():
                print(f"[StippleImageService] HuggingFace Quota Esgotada (402 Payment Required): Seus créditos gratuitos mensais do Hugging Face para o modelo {clean_model} foram esgotados.")
            else:
                print(f"[StippleImageService] Erro na geração HuggingFace ({clean_model}): {e}")
            return False

    @classmethod
    def _generate_via_google_imagen(cls, prompt: str, api_key: str, dest_path: Path, model: str = "imagen-3.0-generate-002") -> bool:
        try:
            from google import genai
            from google.genai import types
            clean_model = model.strip() if model and model.strip() else "imagen-3.0-generate-002"
            client = genai.Client(api_key=api_key)
            resp = client.models.generate_images(
                model=clean_model,
                prompt=prompt,
                config=types.GenerateImagesConfig(
                    number_of_images=1,
                    aspect_ratio="1:1",
                    person_generation="dont_allow"
                )
            )
            if resp.generated_images:
                img_bytes = resp.generated_images[0].image.image_bytes
                dest_path.write_bytes(img_bytes)
                return dest_path.exists() and dest_path.stat().st_size > 1000
        except Exception as e:
            print(f"[StippleImageService] Erro Google Imagen: {e}")
        return False

    @classmethod
    def _generate_via_openai(cls, prompt: str, api_key: str, dest_path: Path, model: str = "dall-e-3", quality: str = "standard") -> bool:
        try:
            import urllib.request
            from openai import OpenAI
            clean_model = model.strip() if model and model.strip() else "dall-e-3"
            clean_quality = "hd" if quality == "hd" else "standard"
            client = OpenAI(api_key=api_key)
            res = client.images.generate(
                model=clean_model,
                prompt=prompt,
                size="1024x1024",
                quality=clean_quality if clean_model == "dall-e-3" else "standard",
                n=1
            )
            if res.data and res.data[0].url:
                img_url = res.data[0].url
                with urllib.request.urlopen(img_url, timeout=20) as r:
                    dest_path.write_bytes(r.read())
                return dest_path.exists() and dest_path.stat().st_size > 1000
        except Exception as e:
            print(f"[StippleImageService] Erro OpenAI DALL-E: {e}")
        return False

    @classmethod
    def _execute_provider_cascade(cls, prompt: str, dest_path: Path, width: int = 1024, height: int = 1024) -> bool:
        """
        Executa tentativa em cascata: Provedor preferencial -> Fal.ai -> OpenAI -> Google Imagen -> HuggingFace -> OpenRouter.
        Se nenhum responder ou tiver crédito, retorna False com degradação silenciosa garantida.
        """
        settings = SettingsService.get_settings()
        preferred = settings.get("image_provider", "openai").lower()
        if preferred == "disabled":
            return False

        user_model = (settings.get("image_model") or "").strip()
        quality = (settings.get("image_quality") or "standard").lower()

        # Lista ordenada de tentativas baseada no provedor preferido
        candidates = [preferred]
        for p in ["openai", "fal", "google", "huggingface", "openrouter"]:
            if p not in candidates:
                candidates.append(p)

        for provider in candidates:
            try:
                if provider == "openai" and settings.get("openai_api_key"):
                    m = user_model if preferred == "openai" and user_model else "dall-e-3"
                    if cls._generate_via_openai(prompt, settings["openai_api_key"], dest_path, model=m, quality=quality):
                        return True
                elif provider == "fal" and settings.get("fal_api_key"):
                    m = user_model if preferred == "fal" and user_model else "fal-ai/flux/schnell"
                    if cls._generate_via_fal(prompt, settings["fal_api_key"], dest_path, model=m, width=width, height=height):
                        return True
                elif provider == "google" and settings.get("gemini_api_key"):
                    m = user_model if preferred == "google" and user_model else "imagen-3.0-generate-002"
                    if cls._generate_via_google_imagen(prompt, settings["gemini_api_key"], dest_path, model=m):
                        return True
                elif provider == "huggingface" and settings.get("hf_token"):
                    m = user_model if preferred == "huggingface" and user_model and "/" in user_model else "black-forest-labs/FLUX.1-schnell"
                    if cls._generate_via_huggingface(prompt, settings["hf_token"], dest_path, model=m, width=width, height=height):
                        return True
                elif provider == "openrouter" and settings.get("openrouter_api_key"):
                    if cls._generate_via_openrouter(prompt, settings["openrouter_api_key"], dest_path):
                        return True
            except Exception:
                continue

        return False

    @classmethod
    async def generate_stipple_image(cls, concept_desc: str, lesson_id: int, idx: int) -> Optional[str]:
        """
        Dispara a geração da ilustração usando cascata de provedores com degradação silenciosa.
        """
        settings = SettingsService.get_settings()
        ratio = settings.get("image_aspect_ratio", "1:1")
        if ratio == "16:9":
            w, h = 1024, 576
        elif ratio == "4:3":
            w, h = 1024, 768
        else:
            w, h = 1024, 1024

        prompt = cls.build_stipple_prompt(concept_desc)
        dest_filename = f"lesson_{lesson_id}_stipple_{idx}.jpg"
        dest_path = STORAGE_DIR / dest_filename

        try:
            sem = cls.get_semaphore()
            async with sem:
                success = await asyncio.wait_for(
                    asyncio.to_thread(cls._execute_provider_cascade, prompt, dest_path, width=w, height=h),
                    timeout=45.0
                )
                if success and dest_path.exists():
                    return f"/api/images/{dest_filename}"
        except Exception:
            pass

        return None

    @classmethod
    async def enrich_lesson_with_stipple(cls, content_markdown: str, lesson_id: int) -> str:
        """
        Substitui marcadores <!-- STIPPLE_IMAGE: "..." | CAPTION: "..." --> por imagens reais locais.
        Em caso de ausência ou falha de provedores, remove o marcador silenciosamente para não poluir o texto.
        """
        pattern = re.compile(r'<!--\s*STIPPLE_IMAGE:\s*"([^"]+)"\s*\|\s*CAPTION:\s*"([^"]+)"\s*-->', re.IGNORECASE)
        matches = list(pattern.finditer(content_markdown))

        if not matches:
            return content_markdown

        enriched_md = content_markdown
        for idx, match in enumerate(matches[:2], start=1):
            full_tag = match.group(0)
            concept_query = match.group(1).strip()
            caption = match.group(2).strip()

            rel_url = await cls.generate_stipple_image(concept_query, lesson_id, idx)
            if rel_url:
                replacement = f"\n\n![{caption}]({rel_url})\n\n"
                enriched_md = enriched_md.replace(full_tag, replacement, 1)
            else:
                # Remoção limpa e silenciosa do marcador quando nenhum provedor gerar imagem
                enriched_md = enriched_md.replace(full_tag, "", 1)

        return enriched_md

    @classmethod
    async def generate_case_study_image(cls, case_title_or_context: str, lesson_id: int) -> Optional[str]:
        """
        Gera uma ilustração em pontilhismo contextualizada para o Estudo de Caso usando cascata de provedores.
        """
        try:
            clean_subject = " ".join(case_title_or_context.split())[:140].strip()
            prompt = cls.build_stipple_prompt(f"conceptual instrument, artifact or symbol for: {clean_subject}")
            dest_filename = f"lesson_{lesson_id}_case_study.jpg"
            dest_path = STORAGE_DIR / dest_filename

            sem = cls.get_semaphore()
            async with sem:
                success = await asyncio.wait_for(
                    asyncio.to_thread(cls._execute_provider_cascade, prompt, dest_path),
                    timeout=45.0
                )
                if success and dest_path.exists():
                    return f"/api/images/{dest_filename}"
        except Exception:
            pass
        return None

    @classmethod
    def build_cover_prompt(cls, subject: str, visual_archetype: str) -> str:
        """
        Gera o prompt da capa do curso mantendo exatamente a MESMA identidade visual das ilustrações das aulas.
        """
        clean_subj = subject.strip().strip('"').strip("'")
        clean_arch = visual_archetype.strip().strip('"').strip("'")
        return cls.build_stipple_prompt(f"{clean_subj}, {clean_arch}")

    @classmethod
    async def generate_course_cover_image(cls, subject: str, visual_archetype: str, course_id: int) -> Optional[str]:
        """
        Gera uma imagem de capa exclusiva para o curso usando a cascata de provedores.
        A capa é salva no diretório de imagens e referenciada no Course.cover_image_url.
        """
        try:
            prompt = cls.build_cover_prompt(subject, visual_archetype)
            dest_filename = f"course_{course_id}_cover.jpg"
            dest_path = STORAGE_DIR / dest_filename

            success = await asyncio.wait_for(
                asyncio.to_thread(cls._execute_provider_cascade, prompt, dest_path, 1024, 1024),
                timeout=45.0
            )
            if success and dest_path.exists():
                return f"/api/images/{dest_filename}"
        except Exception:
            pass
        return None
