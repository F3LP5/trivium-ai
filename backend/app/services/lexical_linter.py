import re
import regex
from typing import Dict, List, Optional, Set
from pydantic import BaseModel
from spellchecker import SpellChecker
from app.services.llm_gateway import LLMGateway

class LexicalCorrectionResult(BaseModel):
    corrections: Dict[str, str] = {}

class LexicalLinterService:
    _spell_pt: Optional[SpellChecker] = None
    _spell_en: Optional[SpellChecker] = None

    # Termos técnicos, empresariais e empréstimos comuns de uso universal em aulas
    COMMON_TECH_WORDS: Set[str] = {
        "software", "hardware", "feedback", "machine", "learning", "insight", "insights",
        "trade-off", "tradeoff", "tradeoffs", "mindset", "prompt", "prompts", "online",
        "download", "design", "designer", "designers", "marketing", "performance",
        "workflow", "workflows", "dataset", "datasets", "benchmark", "benchmarks",
        "backend", "frontend", "setup", "status", "debug", "debugging", "dashboard",
        "stakeholder", "stakeholders", "score", "scores", "framework", "frameworks",
        "pipeline", "pipelines", "sprint", "sprints", "pitch", "pitchs", "roadmap",
        "roadmaps", "case", "cases", "input", "inputs", "output", "outputs", "target",
        "targets", "link", "links", "post", "posts", "site", "sites", "web", "layout",
        "briefing", "lead", "leads", "hub", "gap", "gaps", "fit", "burnout", "turnover",
        "brainstorming", "coaching", "compliance", "default", "drive", "drives", "delay",
        "delays", "draft", "drafts", "feed", "feeds", "guideline", "guidelines",
        "highlight", "highlights", "know-how", "networking", "playbook", "pool",
        "release", "releases", "roster", "skill", "skills", "squad", "squads", "startup",
        "startups", "storytelling", "tag", "tags", "timeline", "timelines", "upgrade",
        "upgrades", "workshop", "workshops", "overview", "checklist", "checklists",
        "offline", "token", "tokens", "deep", "reinforcement", "neural", "network",
        "heuristic", "heuristics", "sandbox", "socratic", "mastery", "learning"
    }

    @classmethod
    def get_spellchecker(cls, language: str) -> SpellChecker:
        is_en = language.lower().startswith("en")
        if is_en:
            if cls._spell_en is None:
                cls._spell_en = SpellChecker(language="en")
            return cls._spell_en
        else:
            if cls._spell_pt is None:
                cls._spell_pt = SpellChecker(language="pt")
            return cls._spell_pt

    @classmethod
    def get_en_spellchecker(cls) -> SpellChecker:
        if cls._spell_en is None:
            cls._spell_en = SpellChecker(language="en")
        return cls._spell_en

    @classmethod
    def _extract_clean_text_and_whitelist(
        cls,
        text: str,
        lesson_title: str = "",
        core_concept: str = ""
    ) -> tuple[str, Set[str]]:
        """
        Remove sintaxes markdown (código, fórmulas, URLs) e extrai
        termos legítimos do glossário e títulos para whitelist dinâmica.
        """
        # Extrai termos do glossário da própria aula
        whitelist: Set[str] = set(cls.COMMON_TECH_WORDS)
        glossary_match = re.search(r'##\s*(?:Gloss[aá]rio|Glossary)[\s\S]*', text)
        if glossary_match:
            for gw in re.findall(r'\*\*(.*?)\*\*', glossary_match.group(0)):
                for w in regex.findall(r'\b\p{L}+\b', gw.lower()):
                    whitelist.add(w)

        # Adiciona palavras do título e do conceito-chave
        for w in regex.findall(r'\b\p{L}+\b', f"{lesson_title} {core_concept}".lower()):
            whitelist.add(w)

        # Higieniza markdown para análise léxica
        clean = text
        clean = re.sub(r'```[\s\S]*?```', ' ', clean)
        clean = re.sub(r'`[^`]+`', ' ', clean)
        clean = re.sub(r'\$\$[\s\S]*?\$\$', ' ', clean)
        clean = re.sub(r'\$[^\$]+\$', ' ', clean)
        clean = re.sub(r'!\[.*?\]\(.*?\)', ' ', clean)
        clean = re.sub(r'https?://\S+', ' ', clean)
        clean = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', clean)

        return clean, whitelist

    @classmethod
    async def lint_and_fix(
        cls,
        content_markdown: str,
        language: str = "pt-BR",
        lesson_title: str = "",
        core_concept: str = ""
    ) -> str:
        """
        Linter Léxico Híbrido:
        1. Passagem rápida (< 50ms) via dicionário offline determinístico.
        2. Se houver tokens inexistentes, micro-auditoria contextual via LLM (< 2s).
        3. Aplica correções cirúrgicas preservando formatação e maiúsculas.
        """
        if not content_markdown or len(content_markdown) < 100:
            return content_markdown

        is_en = language.lower().startswith("en")
        sp_main = cls.get_spellchecker(language)
        sp_en = cls.get_en_spellchecker() if not is_en else sp_main

        clean_text, whitelist = cls._extract_clean_text_and_whitelist(
            content_markdown,
            lesson_title=lesson_title,
            core_concept=core_concept
        )

        # Extrai todas as palavras alfabéticas com pelo menos 3 caracteres
        all_words = set(regex.findall(r'\b\p{L}{3,}\b', clean_text))

        suspicious_words: List[str] = []
        for w in all_words:
            # Pula siglas em maiúsculas (ex: CEO, API, SQL, NASA, DNA)
            if w.isupper() and len(w) <= 6:
                continue

            wl = w.lower()
            if wl in whitelist:
                continue

            # Se for texto em PT, aceita se existir no dicionário PT OU no dicionário EN (estrangeirismos comuns)
            if not is_en:
                if wl in sp_main or wl in sp_en:
                    continue
            else:
                if wl in sp_main:
                    continue

            suspicious_words.append(w)

        # Se nenhuma palavra suspeita for detectada (caminho rápido em > 90% das aulas), retorna imediatamente
        if not suspicious_words:
            return content_markdown

        # Limita a até 10 palavras mais relevantes por aula para manter a consulta ultrarrápida
        suspicious_words = suspicious_words[:10]

        # Extrai trecho de contexto (~120 caracteres) para cada palavra suspeita
        words_with_context: List[tuple[str, str]] = []
        for w in suspicious_words:
            match = re.search(r'([^\n.]{0,60}\b' + re.escape(w) + r'\b[^\n.]{0,60})', clean_text)
            snippet = match.group(0).strip() if match else w
            words_with_context.append((w, snippet))

        # Micro-Auditor Semântico via LLM
        if not is_en:
            lines = [f"- Palavra: \"{w}\" | Trecho: \"{ctx}\"" for w, ctx in words_with_context]
            system_prompt = (
                "Você é um Revisor Ortográfico e Léxico Editorial de altíssima precisão da Trivium Academy.\n"
                "Sua missão é inspecionar as palavras abaixo encontradas no rascunho de uma aula.\n"
                "DIRETRIZES ESTRITAS:\n"
                "1. Se a palavra for um ERRO DE DIGITAÇÃO, NEOLOGISMO ACIDENTAL ou FUSÃO FONÉTICA (ex: 'cerpo' no lugar de 'cerne', 'desenvolvel' no lugar de 'desenvolveu'), forneça a palavra correta pretendida pelo autor segundo o contexto.\n"
                "2. Se a palavra for um NOME PRÓPRIO de autor/pessoa/lugar (ex: Kahneman, Dalio, Feynman), TERMO TÉCNICO VÁLIDO da matéria (ex: cingulado, dopaminérgico), ou PALAVRA LEGÍTIMA da língua portuguesa, NÃO CORRIJA (ignore).\n"
                "3. Retorne APENAS um objeto JSON no formato exato:\n"
                "{\"corrections\": {\"palavra_errada\": \"palavra_correta\"}}"
            )
            user_prompt = (
                "Analise as seguintes palavras e seus contextos:\n"
                + "\n".join(lines) +
                "\n\nRetorne exclusivamente o JSON com as correções necessárias (se houver)."
            )
        else:
            lines = [f"- Word: \"{w}\" | Excerpt: \"{ctx}\"" for w, ctx in words_with_context]
            system_prompt = (
                "You are a Precision Editorial and Lexical Proofreader for Trivium Academy.\n"
                "Your mission is to inspect the candidate words below found in a lesson draft.\n"
                "STRICT GUIDELINES:\n"
                "1. If a word is a TYPO, ACCIDENTAL NEOLOGISM, or SPELLING ERROR (e.g., 'algoritm' -> 'algorithm', 'paradocks' -> 'paradox'), provide the intended correct word based on context.\n"
                "2. If a word is a PROPER NOUN (author, person, place), a VALID TECHNICAL TERM (e.g., backpropagation, eigenvector), or a STANDARD WORD, DO NOT CORRECT IT (ignore it).\n"
                "3. Return ONLY a JSON object in the exact format:\n"
                "{\"corrections\": {\"wrong_word\": \"correct_word\"}}"
            )
            user_prompt = (
                "Analyze the following words and their excerpts:\n"
                + "\n".join(lines) +
                "\n\nReturn exclusively the JSON with necessary corrections (if any)."
            )

        try:
            result = await LLMGateway.generate_structured(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                schema_class=LexicalCorrectionResult,
                max_tokens=220,
                timeout=12
            )

            corrections = result.corrections if result and hasattr(result, "corrections") else {}
            if not corrections:
                return content_markdown

            updated_markdown = content_markdown
            applied_count = 0

            for wrong, right in corrections.items():
                if not wrong or not right or wrong.strip().lower() == right.strip().lower():
                    continue

                wrong_clean = wrong.strip()
                right_clean = right.strip()

                # Segurança: não permite substituição por frases longas ou código
                if len(right_clean) > len(wrong_clean) + 12 or "\n" in right_clean:
                    continue

                # Preserva maiúscula inicial se a palavra original estava capitalizada
                def replacer(m):
                    orig = m.group(0)
                    if orig.isupper():
                        return right_clean.upper()
                    elif orig[0].isupper():
                        return right_clean.capitalize()
                    return right_clean.lower()

                pattern = r'\b' + re.escape(wrong_clean) + r'\b'
                new_text, count = re.subn(pattern, replacer, updated_markdown, flags=re.IGNORECASE)
                if count > 0:
                    updated_markdown = new_text
                    applied_count += count
                    print(f"[LexicalLinter] [Fix] Correção editorial aplicada ({count}x): '{wrong_clean}' -> '{right_clean}'")

            if applied_count > 0:
                print(f"[LexicalLinter] Total de {applied_count} correções léxicas aplicadas com sucesso na aula.")

            return updated_markdown

        except Exception as e:
            # Em caso de falha transitória ou timeout do micro-auditor, não interrompe a geração da aula
            print(f"[LexicalLinter] Aviso: Micro-auditoria léxica ignorada por exceção/timeout: {e}")
            return content_markdown
