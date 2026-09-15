from typing import Optional
import json
import re
from app.services.llm_gateway import LLMGateway
from app.schemas.curriculum import CurriculumSchema, ModulePlan, LessonPlan
from app.schemas.quiz import (
    QuizSchema, GraderEvaluation, SocraticRound1Evaluation, SocraticRound2Evaluation,
    MultipleChoiceQuestion, MultipleChoiceOption, SocraticDuelQuestion,
    SimulationSandbox, IndicatorState, SimulationTurn1Option, SimulationTurn2Option
)

def normalize_level(level: Optional[str], language: str = "pt-BR") -> str:
    """
    Normalizes level string across English and Portuguese variants.
    e.g. 'Foundational' / 'Basic' -> 'Foundational' (en) or 'Básico' (pt)
    """
    if not level:
        return "Foundational" if language.lower().startswith("en") else "Básico"
    norm = str(level).strip().lower()
    is_en = language.lower().startswith("en")
    if any(k in norm for k in ["bás", "bas", "found", "fund", "inici"]):
        return "Foundational" if is_en else "Básico"
    elif any(k in norm for k in ["interm", "méd", "med"]):
        return "Intermediate" if is_en else "Intermediário"
    elif any(k in norm for k in ["avan", "adv", "expert", "mast"]):
        return "Advanced" if is_en else "Avançado"
    elif "test" in norm:
        return "Test" if is_en else "Teste"
    return level

class ResearcherAgent:
    @staticmethod
    async def build_research_dossier(subject: str, focus_keywords: list[str] = None, domain_profile: dict = None, language: str = "pt-BR"):
        """
        Agente Autônomo de Pesquisa e Checagem Factual (Padrão NotebookLM / Perplexity Deep Research):
        Decompõe queries em sub-vertentes universais, minera livros no Archive.org, consulta Wikipédia canônica, busca em múltiplos domínios web e sintetiza o Evidence Ledger.
        """
        from app.services.researcher import research_engine
        return await research_engine.build_dossier_async(subject, focus_keywords, domain_profile=domain_profile, language=language)

class CuratorAgent:
    @staticmethod
    async def plan_curriculum(
        subject: str,
        level: str,
        num_modules: int,
        lessons_per_module: int,
        fact_dossier: str = "",
        domain_profile: dict = None,
        language: str = "pt-BR"
    ) -> CurriculumSchema:
        is_en = language.lower().startswith("en")
        norm_level = str(level).strip().lower()
        is_basic = any(k in norm_level for k in ["bás", "bas", "found", "fund", "inici"])
        is_inter = any(k in norm_level for k in ["interm", "méd", "med"])
        canonical_level = normalize_level(level, language)
        
        if is_en:
            schema_example = '{"subject": "' + subject + '", "level": "' + canonical_level + '", "modules": [{"module_number": 1, "title": "Foundations and the Spark", "lessons": [{"title": "The Hidden Pulse", "core_concept": "The high stakes of rhythm and mechanical balance."}]}]}'
        else:
            schema_example = '{"subject": "' + subject + '", "level": "' + canonical_level + '", "modules": [{"module_number": 1, "title": "Fundamentos da Rima", "lessons": [{"title": "O que e Rima", "core_concept": "Sons e metricas"}]}]}'

        dossier_block = f"\n\nMATRIZ FACTUAL E CATÁLOGO DE ENTIDADES VERIFICADAS:\n{fact_dossier[:3000]}" if fact_dossier else ""
        
        domain_context = ""
        if domain_profile:
            domain_name = domain_profile.get("dynamic_domain_name", "General")
            persona = domain_profile.get("persona_title", "Masterful Professor and Essayist")
            domain_context = f"PERFIL DO DOMÍNIO: Área '{domain_name}' | Persona Curatorial: '{persona}'"

        if is_en:
            if is_basic:
                arc_guideline = (
                    f"CURRICULAR ARC FOR BASIC LEVEL ({num_modules} Modules):\n"
                    f"- Module 1: The Spark and the Hidden Paradox (the visible mystery, the question unasked, shattering beginner intuition).\n"
                    f"- Module 2: The Machine Behind the Curtain (unseen gears, how parts interlock to create real movement).\n"
                    f"- Module 3: The Master's Touch (fine-tuning, subtle nuances separating the amateur from beautiful execution).\n"
                    f"- Module 4: The Real World and Personal Application (the legacy, how the reader sees and applies this from now on).\n"
                )
            elif is_inter:
                arc_guideline = (
                    f"CURRICULAR ARC FOR INTERMEDIATE LEVEL ({num_modules} Modules of Applied Competence):\n"
                    f"- Modules 1-2: Intuitive Foundation and First Principles (from scratch, setting fundamental laws).\n"
                    f"- Modules 3-4: Anatomy of Components and Operational Tension.\n"
                    f"- Modules 5-6: Practical Friction, Classic Failures, and Diagnostics.\n"
                    f"- Modules 7-8: Consolidated Methodologies and Professional Standards.\n"
                )
            else:
                arc_guideline = (
                    f"CURRICULAR ARC FOR ADVANCED LEVEL ({num_modules} Modules of Systemic Mastery):\n"
                    f"- Modules 1-3: Genesis and Modern First Principles.\n"
                    f"- Modules 4-6: Systemic Operation under Real Stress.\n"
                    f"- Modules 7-9: Hidden Pathologies, Extreme Crises, and Documented Cases.\n"
                    f"- Modules 10-12: Frontiers of Technique, Brutal Trade-offs, and Innovation.\n"
                )

            system_prompt = (
                f"You are the Creative Director and Curricular Showrunner of Trivium (Specialist in Addictive Narratives, Masterclasses, and Netflix-style Documentaries).\n"
                f"Your goal is to build the definitive curriculum matrix for a course on '{subject}' at '{canonical_level}' level.\n"
                f"{domain_context}\n"
                f"{dossier_block}\n\n"
                f"NETFLIX-SERIES CURRICULAR DIRECTIVES:\n"
                f"1. MAGNETIC AND ENIGMATIC LESSON TITLES (EPISODE STYLE):\n"
                f"   - Short, gripping titles focused on a paradox, conflict, or behind-the-scenes scene.\n"
                f"   - NO bureaucratic or academic titles like 'Introduction to X', 'Overview of Y'.\n"
                f"   - NO numeric prefixes inside title strings (like 'Lesson 1:').\n"
                f"2. LESSON SYNOPSES AS DRAMATIC HOOKS:\n"
                f"   - 'core_concept' MUST be a gripping episode synopsis (1-2 sentences, 15-30 words): [Conflict/high stakes/tension] + [Counter-intuitive truth or practical revelation].\n"
                f"3. DIRECT THEMATIC MODULE TITLES:\n"
                f"   - Module titles must be direct thematic names without the word 'Act' or 'Module'.\n"
                f"4. CONTINUOUS PROGRESSION BY LEVEL:\n"
                f"{arc_guideline}\n"
                f"5. EXACT QUANTITATIVE REQUIREMENTS:\n"
                f"   - Exactly {num_modules} modules, each with exactly {lessons_per_module} lessons.\n"
                f"Respond EXCLUSIVELY with a valid JSON object matching this schema:\n"
                f"{schema_example}\n"
            )
            user_prompt = f"Create the complete curriculum matrix in English for '{subject}' at '{canonical_level}' level with {num_modules} modules and {lessons_per_module} lessons per module, applying magnetic Netflix-episode titles and gripping synopses, and direct thematic titles for modules (without the word Act or Module)."
        else:
            # Diretrizes do Arco Narrativo por Nível de Dificuldade (Escada Contínua em PT)
            if is_basic:
                arc_guideline = (
                    f"ARCO CURRICULAR DO NÍVEL BÁSICO ({num_modules} Módulos em 4 Atos Fundamentais):\n"
                    f"- Módulo 1: A Faísca e o Paradoxo Oculto (o mistério visível, a pergunta que ninguém fez, desfazendo a intuição falsa do leigo).\n"
                    f"- Módulo 2: A Máquina nos Bastidores (as engrenagens invisíveis, como as partes dialogam e criam o movimento/efeito real).\n"
                    f"- Módulo 3: O Toque do Mestre (os ajustes finos, as sutilezas que separam o amador da beleza da execução).\n"
                    f"- Módulo 4: O Mundo Real e a Aplicação Pessoal (o legado, como o leitor usa e enxerga isso solto na rua a partir de hoje).\n"
                )
            elif is_inter:
                arc_guideline = (
                    f"ARCO CURRICULAR DO NÍVEL INTERMEDIÁRIO ({num_modules} Módulos de Competência Aplicada):\n"
                    f"- Módulos 1-2: A Base Intuitiva e os Primeiros Princípios (do zero absoluto, estabelecendo as leis fundamentais).\n"
                    f"- Módulos 3-4: Anatomia dos Componentes e Fluxo Real (as peças reais sob tensão operacional).\n"
                    f"- Módulos 5-6: O Atrito Prático, Falhas Clássicas e Diagnóstico (onde os novatos quebram a cara e como identificar patologias).\n"
                    f"- Módulos 7-8: Metodologias Consolidadas e Padrões Profissionais (a transição para a execução de alto nível).\n"
                )
            else: # Avançado
                arc_guideline = (
                    f"ARCO CURRICULAR DO NÍVEL AVANÇADO ({num_modules} Módulos de Maestria Sistêmica):\n"
                    f"- Módulos 1-3: A Gênese e os Primeiros Princípios Modernos (do zero absoluto com clareza cristalina, sem anacronismos na largada).\n"
                    f"- Módulos 4-6: Operação Sistêmica sob Condições Reais (acoplamento de forças, variáveis dinâmicas e atrito).\n"
                    f"- Módulos 7-9: Patologias Ocultas, Crises Extremas e Casos Documentados (dissecção de falhas raras, crises históricas e diagnósticos finos).\n"
                    f"- Módulos 10-12: Fronteiras da Técnica, Trade-offs Brutais e Inovação (dilemas estratégicos sem resposta fácil, legado e visão holística).\n"
                )

            system_prompt = (
                f"Você é o Diretor Criativo e Showrunner Curricular da Trivium (Especialista em Narrativas Viciantes, Masterclasses e Roteiros Padrão Netflix Séries/Documentários).\n"
                f"Seu objetivo é criar a matriz curricular definitiva para um curso de '{subject}' no nível '{canonical_level}'.\n"
                f"{domain_context}\n"
                f"{dossier_block}\n\n"
                f"DIRETRIZES DA LÓGICA 'SÉRIE NETFLIX' PARA O CURRÍCULO:\n"
                f"1. TÍTULOS DE AULA MAGNÉTICOS E ENIGMÁTICOS (ESTILO EPISÓDIO DE SÉRIE):\n"
                f"   - Cada aula é um episódio imperdível. O título deve ser curto, instigante, focado em um paradoxo, conflito ou cena de bastidores.\n"
                f"   - PROIBIDO títulos burocráticos, acadêmicos ou frios como 'Introdução à X', 'Conceitos Fundamentais de Y', 'Panorama Geral', 'Mecanismos de Z'.\n"
                f"   - NUNCA inclua prefixos numéricos dentro da string do título (como 'Aula 1:' ou 'Episódio 1:'). O número já é gerado pela interface.\n"
                f"   - Exemplos de excelência: 'A Navalha Invisível', 'O Blefe Perfeito', 'Onde o Gigante Dobra', 'A Semente da Mentira', 'A Faísca no Escuro', 'O Sangue Frio', 'O Primeiro Erro Fatal'.\n\n"
                f"2. DESCRIÇÕES DE AULA QUE SÃO SINOPSES COM GANCHO (HOOK DRAMÁTICO):\n"
                f"   - O campo 'core_concept' NUNCA deve ser uma ementa fria (ex: 'Estudo das variáveis de...').\n"
                f"   - Deve funcionar como a sinopse de um episódio na Netflix (1 a 2 frases curtas, entre 15 e 30 palavras), estruturada com: [O conflito/aposta alta/mistério sob tensão] + [A verdade contraintuitiva ou revelação prática que o aluno descobre].\n\n"
                f"3. NOMES DE MÓDULOS TEMÁTICOS E DIRETOS:\n"
                f"   - O título do módulo deve ser o nome direto do grande tema abordado, sem a palavra 'Ato' e sem a palavra 'Módulo' na string (o badge 'Módulo X' já é gerado pela interface).\n\n"
                f"4. UNIVERSALIDADE E ZERO JARGÃO NA LARGADA:\n"
                f"   - Seja sobre cinema, mecânica, hip hop, finanças, física quântica ou gastronomia, o curso acolhe qualquer pessoa sem conhecimento prévio no Módulo 1 e escala a maestria com ritmo envolvente.\n\n"
                f"5. A REGRA DO 'CONCEITO REI ÚNICO POR AULA' (ZERO AMONTOAMENTO):\n"
                f"   - Cada aula foca em APENAS UMA engrenagem dramática ou prática crucial.\n\n"
                f"6. PROGRESSÃO EM ESCADA CONTÍNUA CONFORME O NÍVEL:\n"
                f"{arc_guideline}\n"
                f"7. REQUISITOS QUANTITATIVOS ESTRITOS:\n"
                f"   - O curso DEVE conter exatamente {num_modules} módulos.\n"
                f"   - Cada módulo DEVE conter exatamente {lessons_per_module} aulas detalhadas.\n"
                f"Responda exclusivamente com um objeto JSON válido seguindo rigorosamente esta estrutura:\n"
                f"{schema_example}\n"
            )
            user_prompt = f"Crie a matriz curricular completa em português para '{subject}' no nível '{level}' com {num_modules} módulos e {lessons_per_module} aulas por módulo, aplicando títulos magnéticos de episódios e sinopses instigantes, e títulos temáticos diretos para os módulos (sem a palavra Ato)."

        try:
            curriculum = await LLMGateway.generate_structured(system_prompt, user_prompt, CurriculumSchema, max_tokens=3500, timeout=85)
        except Exception as err:
            err_str = str(err).lower()
            if "free-models-per-day" in err_str or "free_tier_daily" in err_str or "high-balance" in err_str:
                raise RuntimeError(f"Cota diária de requisições gratuitas atingida no OpenRouter (1.000 requisições/dia). Renovação diária às 00:00 UTC. Detalhes: {err}")
            print(f"[CuratorAgent] Aviso: IA não estruturou a matriz ({err}). Ativando síntese curricular de alta fidelidade...")
            curriculum = CuratorAgent.build_fallback_curriculum(subject, level, num_modules, lessons_per_module, language)

        if not curriculum or not curriculum.modules:
            print(f"[CuratorAgent] Matriz sem módulos válidos. Ativando síntese curricular de alta fidelidade...")
            curriculum = CuratorAgent.build_fallback_curriculum(subject, level, num_modules, lessons_per_module, language)

        return CuratorAgent.ensure_curriculum_completeness(curriculum, subject, level, num_modules, lessons_per_module, language)

    @staticmethod
    def build_fallback_curriculum(subject: str, level: str, num_modules: int, lessons_per_module: int, language: str = "pt-BR") -> CurriculumSchema:
        is_en = language.lower().startswith("en")
        if is_en:
            module_themes = [
                f"The Foundation and Paradox of {subject}",
                f"The Machinery Behind {subject}",
                f"Real Operational Stress in {subject}",
                f"Anatomy of Fatal Errors in {subject}",
                f"Fine Tuning and Trade-offs in {subject}",
                f"The Master's Touch in {subject}",
                f"Unconventional Moves in {subject}",
                f"Breaking the Limits of {subject}",
                f"The Methodical Turning Point in {subject}",
                f"Collapse and Reconstruction in {subject}",
                f"Frontiers and Modern Innovations in {subject}",
                f"The Lasting Legacy of {subject}"
            ]
            lesson_themes = [
                ("The First Fracture", f"The overlooked detail that shatters beginner intuition and exposes the core challenge in {subject}."),
                ("The Unseen Engine", f"Behind the scenes, a silent force governs outcomes that amateurs completely ignore in {subject}."),
                ("Under Real Pressure", f"The critical test where textbook formulas fail and practical insight takes over in {subject}."),
                ("The Critical Crossroads", f"A high-stakes trade-off with no easy answer, where every choice carries consequence in {subject}."),
                ("The False Shortcut", f"A classic pitfall that appears to save time but leads to systemic breakdown in {subject}."),
                ("The Master's Precision", f"The subtle refinement that separates adequate execution from timeless mastery in {subject}.")
            ]
        else:
            module_themes = [
                f"O Ponto de Partida e o Paradoxo de {subject}",
                f"A Máquina nos Bastidores de {subject}",
                f"O Teste Sob Tensão Real em {subject}",
                f"Anatomia dos Erros Fatais em {subject}",
                f"O Ajuste Fino e os Segredos de {subject}",
                f"O Confronto com o Inevitável em {subject}",
                f"Estratégias Não Convencionais em {subject}",
                f"O Limite da Resistência em {subject}",
                f"A Virada Metódica em {subject}",
                f"O Colapso e a Reconstrução em {subject}",
                f"As Fronteiras e Inovações em {subject}",
                f"O Legado Duradouro de {subject}"
            ]
            lesson_themes = [
                ("A Primeira Fissura", f"O detalhe negligenciado que desmonta a certeza intuitiva e expõe o verdadeiro desafio em {subject}."),
                ("A Engrenagem Oculta", f"Nos bastidores do sistema, uma força silenciosa governa o resultado sem que os amadores percebam em {subject}."),
                ("Quando a Pressão Sobe", f"O teste real onde as fórmulas teóricas falham e apenas o discernimento prático sobrevive em {subject}."),
                ("O Dilema do Meio-Dia", f"Uma encruzilhada de decisões sem saída óbvia, onde cada escolha cobra um preço alto em {subject}."),
                ("O Falso Atalho", f"A armadilha clássica que parece economizar tempo, mas condena o projeto ao retrabalho em {subject}."),
                ("O Toque do Mestre", f"O gesto milimétrico que separa uma execução mediana de uma obra inesquecível em {subject}.")
            ]

        modules = []
        for m_idx in range(1, num_modules + 1):
            lessons = []
            theme_idx = (m_idx - 1) % len(module_themes)
            mod_title = module_themes[theme_idx]
            for l_idx in range(1, lessons_per_module + 1):
                l_theme_idx = (l_idx - 1) % len(lesson_themes)
                l_title_base, l_concept_base = lesson_themes[l_theme_idx]
                lessons.append(LessonPlan(
                    title=l_title_base,
                    core_concept=l_concept_base
                ))
            modules.append(ModulePlan(
                module_number=m_idx,
                title=mod_title,
                lessons=lessons
            ))
        return CurriculumSchema(subject=subject, level=level, modules=modules)

    @staticmethod
    def ensure_curriculum_completeness(curriculum: CurriculumSchema, subject: str, level: str, num_modules: int, lessons_per_module: int, language: str = "pt-BR") -> CurriculumSchema:
        if not curriculum or not curriculum.modules:
            curriculum = CuratorAgent.build_fallback_curriculum(subject, level, num_modules, lessons_per_module, language)
        
        is_en = language.lower().startswith("en")
        while len(curriculum.modules) < num_modules:
            next_mod_idx = len(curriculum.modules) + 1
            mod_title = f"Operational Dynamics of {subject}" if is_en else f"A Tensão Invisível em {subject}"
            curriculum.modules.append(ModulePlan(
                module_number=next_mod_idx,
                title=mod_title,
                lessons=[]
            ))
        
        for m_idx, mod in enumerate(curriculum.modules[:num_modules], start=1):
            mod.module_number = m_idx
            # Limpa prefixos redundantes de 'Módulo X:' ou 'Ato X:' se a IA colocou
            mod.title = re.sub(r'^(?:(?:M[oó]dulo|Ato)\s*\d+\s*[:\-–—]\s*)+', '', mod.title, flags=re.IGNORECASE).strip()
            while len(mod.lessons) < lessons_per_module:
                next_l_idx = len(mod.lessons) + 1
                l_title = f"The Hidden Mechanism {next_l_idx}" if is_en else f"O Segredo Oculto {next_l_idx}"
                l_concept = f"The operational friction and decisive insight in {subject}." if is_en else f"O dilema prático e o atrito real que revelam o funcionamento de {subject}."
                mod.lessons.append(LessonPlan(
                    title=l_title,
                    core_concept=l_concept
                ))
            # Higieniza cada aula: remove prefixos "Aula X:" ou "Episódio X:" colocados por engano
            for l_idx, l in enumerate(mod.lessons[:lessons_per_module], start=1):
                clean_title = re.sub(r'^(?:Aula|Epis[oó]dio|Li[çc][aã]o|Lesson|Episode)\s*\d+\s*[:\-–—]\s*', '', l.title, flags=re.IGNORECASE).strip()
                l.title = clean_title or (f"Episode {l_idx}" if is_en else f"Episódio {l_idx}")
            mod.lessons = mod.lessons[:lessons_per_module]
            
        curriculum.modules = curriculum.modules[:num_modules]
        return curriculum

class WriterAgent:
    @staticmethod
    async def write_lesson(
        subject: str,
        level: str,
        module_num: int,
        module_title: str,
        lesson_num: int,
        lesson_title: str,
        core_concept: str,
        target_words: int,
        previous_summaries: list[str],
        fact_dossier: str = "",
        used_case_studies: list[str] = None,
        domain_profile: dict = None,
        evidence_ledger: dict = None,
        sources_metadata: list = None,
        language: str = "pt-BR"
    ) -> str:
        is_en = language.lower().startswith("en")
        is_first_lesson = (module_num == 1 and lesson_num == 1)

        if is_en:
            if is_first_lesson:
                context_block = "The student is learning this topic from absolute ZERO. Do not use metadiscourse or say 'in this first lesson'. Dive directly into the subject with a gripping hook."
            else:
                if previous_summaries:
                    prev_text = "\n- ".join(previous_summaries[-5:])
                    context_block = f"What the student already explored in previous lessons (use for organic scaffolding without repeating concepts):\n- {prev_text}"
                else:
                    context_block = f"The student already grasped the big picture and now advances in practical and conceptual mastery of: {core_concept}."

            used_cases_str = ", ".join(used_case_studies) if used_case_studies else "None yet (inaugural lesson)"
            cases_constraint = (
                f"\n\n10. CASE ROTATION AND EXCLUSIVITY:\n"
                f"Previous lessons have covered: [{used_cases_str}]. Do NOT repeat these as the main case study for this lesson.\n"
                f"Select and dissect a fresh, concrete real-world case study or historical/scientific project.\n"
            )
        else:
            if is_first_lesson:
                context_block = "O aluno está aprendendo este assunto do absoluto ZERO. Não utilize metadiscurso nem diga 'nesta primeira aula' ou 'no módulo inaugural'. Mergulhe diretamente na matéria com um gancho instigante e envolvente."
            else:
                if previous_summaries:
                    prev_text = "\n- ".join(previous_summaries[-5:])
                    context_block = f"O que o aluno já explorou nas aulas anteriores (use para scaffolding orgânico sem repetir conceitos):\n- {prev_text}"
                else:
                    context_block = f"O aluno já compreendeu a imagem geral e agora avança no domínio prático e conceitual de: {core_concept}."

            used_cases_str = ", ".join(used_case_studies) if used_case_studies else "Nenhum ainda (aula inaugural)"
            cases_constraint = (
                f"\n\n10. ROTATIVIDADE E EXCLUSIVIDADE DE ESTUDOS DE CASO (LEI DO CASE ÚNICO - RIGOR COURSERA):\n"
                f"Nas aulas anteriores deste curso, já foram explorados os seguintes estudos de caso/exemplos: [{used_cases_str}].\n"
                f"É EXPRESSAMENTE PROIBIDO utilizar qualquer um desses elementos como o estudo de caso ou exemplo principal desta aula!\n"
                f"Você DEVE selecionar e dissecar em profundidade um estudo de caso concreto e exclusivo, adequado à matéria da aula (podendo ser uma localidade, praia, ecossistema, obra, técnica, fenômeno histórico/científico, projeto prático ou personalidade relevante).\n"
            )

        # Injeção de Persona Dinâmica e Tom de Voz Epistemológico
        persona_title = "professor e ensaísta magistral da Trivium Academy" if not is_en else "master professor and essayist of Trivium Academy"
        tone_of_voice = "magistral, cativante e límpido" if not is_en else "masterful, gripping, and crystal clear"
        case_study_format = "Estudos de caso reais e empíricos" if not is_en else "Real and empirical case studies"
        if domain_profile:
            persona_title = domain_profile.get("persona_title") or persona_title
            tone_of_voice = domain_profile.get("tone_of_voice") or tone_of_voice
            case_study_format = domain_profile.get("case_study_format") or case_study_format

        # Injeção do Evidence Ledger e Lei da Concretude Factual
        ledger_block = ""
        if evidence_ledger and any(evidence_ledger.values()):
            ledger_block = (
                f"\n\n11. REPOSITÓRIO DE EVIDÊNCIAS E CASOS (EVIDENCE LEDGER):\n"
                f"- Conceitos Canônicos & Teoria: {evidence_ledger.get('canonical_concepts', [])}\n"
                f"- Métricas & Dados Numéricos: {evidence_ledger.get('hard_metrics_and_data', [])}\n"
                f"- Entidades e Referências: {evidence_ledger.get('named_entities', [])}\n"
                f"- Material para Casos Documentados: {evidence_ledger.get('case_study_material', [])}\n"
            )
        elif fact_dossier:
            ledger_block = (
                f"\n\n11. RIGOR FACTUAL E FONTES VERIFICADAS:\n"
                f"{fact_dossier[:3000]}\n"
            )

        # Regra de Bibliografia por Aula: prioriza livros canônicos do Archive.org e artigos auditados
        book_sources = [s for s in (sources_metadata or []) if s.get('type') == 'book' or 'archive.org' in s.get('url', '')]
        other_sources = [s for s in (sources_metadata or []) if s not in book_sources]
        sources_sample = (book_sources + other_sources)[:6]

        sources_list_prompt = ""
        if sources_sample:
            sources_list_prompt = "\n".join([f"  * [{s.get('title')}]({s.get('url')}) ({s.get('domain')})" for s in sources_sample])
        else:
            sources_list_prompt = "  * Fontes auditadas presentes no acervo de pesquisa do curso." if not is_en else "  * Audited sources from the course research dossier."

        if is_en:
            system_prompt = (
                f"You are {persona_title}.\n"
                f"Your mandatory tone of voice is: {tone_of_voice}.\n"
                f"You are an analytical, clear, and deeply didactic essayist (Richard Feynman, Yuval Harari, and Coursera Masterclass tier).\n"
                f"You are drafting the canonical textbook lesson on '{subject}' at '{level}' level.\n"
                f"Current Lesson: Module {module_num} ({module_title}), Lesson {lesson_num} - '{lesson_title}'.\n"
                f"Core Concept to master: {core_concept}.\n\n"

                f"EDITORIAL AND ANALYTICAL DISCIPLINE (STRICT CUTS TO RHETORICAL NOISE):\n"
                f"Write with analytical clarity, firm pacing, and factual density. The student demands substance and real reasoning, not empty poetry.\n"
                f"1. CONTROL METAPHORS (FORBIDDEN METAPHOR PILING): Choose AT MOST ONE guiding analogy for the lesson (e.g. seed/forest, engine/combustion, map/territory) and use it strictly in the opening hook and closing takeaway. It is strictly forbidden to pile up different metaphors in the middle of the text or repeat them in every paragraph.\n"
                f"2. ZERO EMPTY INTENSIFIERS AND CHEAP MELODRAMA: Cut intensifiers without informative load such as 'almost pitiful', 'invisible to hurried eyes', 'in the blink of an eye', or 'wild obsession'. Prefer data, mechanisms, documented facts, operational dilemmas, and concrete metrics.\n"
                f"3. ADVANCE THE ARGUMENT WITHOUT REPEATING THE THESIS: Do not rephrase the same thesis ('start small to scale later', etc.) multiple times across sections using different words. Express the thesis with maximum punch in the Golden Rule, and use the preceding paragraphs to unpack mechanics, trade-offs, and authentic backstage operations.\n"
                f"4. SOBER DIDACTIC PRECISION (ZERO SELF-HELP TONE): Avoid generic clichés like 'the master transforms the world through a single action'. Create '## ' section titles that are specific to the lesson's subject, without repeating generic literary clichés like 'The Machinery in Motion' or 'The Starting Point' as universal headings.\n"
                f"5. MANDATORY CALIBRATION BY LEVEL: The level of this lesson is '{level}'. If beginner (or equivalent), every acronym, technical unit, mechanism, or specialized term must be defined in plain language upon its first appearance before being used freely; do not presume any knowledge beyond what has already been taught in earlier modules of this course. If intermediate or advanced, technical jargon may be used with fewer definition pauses, but always clearly. Never write a lesson technically too dense for the declared level.\n"
                f"6. LEXICAL PRECISION ABOVE ALL: Never sacrifice vocabulary precision for dramatic effect or to sound more literary. If there is any doubt about the exact meaning of a word, replace it with a simpler and accurate alternative. A vocabulary error is the worst possible defect in this text, worse than a slightly less poetic sentence.\n"
                f"7. ONE MENTION, ONE FUNCTION (STRUCTURAL ANTI-REPETITION): The central paradox of the lesson may be cited at most 2 times across the entire text (in the opening hook and in the Golden Rule). The other required sections (Common Trap, Final Takeaway) MUST bring NEW angles and additional information about the topic, never restating the same paradox or thesis in other words.\n\n"

                f"NARRATIVE ARCHITECTURE IN 6 ORGANIC MOMENTS:\n"
                f"1. THE HOOK AND INITIAL PARADOX:\n"
                f"   - Start IMMEDIATELY with the lesson title at level 1: '# {lesson_title}'.\n"
                f"   - Right beneath, open directly into a vivid, intimate, and human scene or a striking everyday analogy of the topic, developed in 2 immersive paragraphs.\n"
                f"   - FORBIDDEN artificial AI formulas like 'Have you ever noticed...' or 'Intuition often deceives us...'. Step straight into the story and show the paradox in action.\n\n"

                f"2. DISSECTING INTUITION (ANALYTICAL AND UNHURRIED EXPLANATION):\n"
                f"   - Develop 2 to 3 robust narrative sections using level 2 subtitles '## ' (NEVER use '# ' for internal sections).\n"
                f"   - The '## ' titles must be thematic and descriptive of this specific lesson's concept, NOT generic literary phrases reusable in any subject.\n"
                f"   - Each section MUST contain at least 2 to 3 well-developed, engaging paragraphs, ALWAYS grounded in facts, mechanisms, or verifiable data, never merely in poetic impressions.\n"
                f"   - In one of the main sections, dismantle the mechanism step-by-step in a detailed numbered format. Step labels MUST be created specifically for the vocabulary of this subject (it is forbidden to literally reuse the generic labels 'the initial baseline', 'the core trade-off', and 'the systemic outcome' as fixed text; they serve solely as a functional guide for each step, not text to copy):\n"
                f"     1. **[Subject-specific label for the initial archetype/element]:** [Rich dissection of the initial element]\n"
                f"     2. **[Subject-specific label for the logic inversion]:** [How the mechanism turns common sense upside down]\n"
                f"     3. **[Subject-specific label for the result in action]:** [How this shift takes shape and delivers practical real-world results]\n"
                f"   - Use **bold** strategically on keywords and anchor concepts to create luminous focal points across reading.\n\n"

                f"3. PRACTICAL EVERYDAY EXAMPLE:\n"
                f"   - Insert a callout block in this exact format (no emojis in header):\n"
                f"   > Practical Everyday Example: [A vivid, visual, and engaging everyday vignette in 2 to 3 sentences where this concept operates in silence]\n\n"

                f"4. SECTION 'BETWEEN RIGHT AND TRAP' (NARRATIVE BLOCK FORMAT):\n"
                f"   - Create the section with the exact title: '## Between Right and Trap'.\n"
                f"   - Develop the contrast in clear, analytical blocks (clean markdown, NEVER leave loose or unclosed asterisks):\n"
                f"     **The failing path:** [The novice illusion or common mistake and the technical/psychological reason it fails]\n"
                f"     **The working path:** [The sharp, elegant, and effective specialist move that solves the deadlock]\n"
                f"     > The Common Trap: [A practical, in-depth warning about the pitfall where most people stumble, bringing a NEW angle, without repeating the opening paradox]\n\n"

                f"5. THE GOLDEN RULE:\n"
                f"   - Present the definitive insight of the lesson in a callout:\n"
                f"   > 🟡 Golden Rule: [The definitive, memorable 1-2 sentence principle summarizing the essence of the lesson]\n"
                f"   - Right beneath the Golden Rule, write 1 reflective paragraph contextualizing its real-world execution.\n\n"

                f"6. FINAL PROVOCATION:\n"
                f"   - Close the narrative with a provocative 1-paragraph personal reflection inviting the student to view themselves or reality differently before moving to the next lesson, bringing an additional angle instead of repeating the Golden Rule.\n\n"

                f"VISUAL AND PUNCTUATION LAWS (STRICT RIGOR):\n"
                f"- STRICTLY FORBIDDEN to use first-person singular ('I', 'I noticed', 'I thought', 'in my opinion')! Converse directly with the student ('you') or narrate the facts and subject matter in engaging third person.\n"
                f"- STRICTLY FORBIDDEN to use the em-dash or en-dash ('—' or '–') anywhere in the text! Use commas, parentheses, or periods to pace sentences naturally.\n"
                f"- STRICTLY FORBIDDEN to put emojis in section headers (no 📖, 📚, 💡, 🎯, etc. in '## ' titles).\n"
                f"- PROIBIDO to create Markdown tables or telegraphic summaries in the middle of the lesson.\n\n"

                f"TECHNICAL GUIDELINES FOR MATH AND CODE (IF APPLICABLE):\n"
                f"- If the topic involves mathematics, physics, quantitative economics, or statistics, use rigorous KaTeX notation: `$expression$` for inline formulas and `$$equation$$` for display blocks. Ensure delimiters are always closed.\n"
                f"- If the topic involves programming or computer science, use markdown code blocks with explicit language tags (e.g. ```python, ```javascript, ```sql) with clean, educational examples.\n\n"
                f"MANDATORY CLOSING SECTIONS:\n"
                f"## Lesson Glossary\n"
                f"- **Term 1**: Crisp, clear, and didactic definition in 1 simple sentence.\n"
                f"- **Term 2**: Exact and accessible definition...\n"
                f"## Lesson Sources and Recommended Readings\n"
                f"- **[Source or Book Title](URL)** (domain): Brief 1-sentence synthesis demonstrating how this research or book grounded this lesson's analysis.\n"
                f"{sources_list_prompt}\n"
                f"{cases_constraint}"
                f"{ledger_block}\n"
            )
            user_prompt = (
                f"Write the complete lesson textbook for Lesson {lesson_num}: '{lesson_title}' ({core_concept}) with an analytical, fluid, human voice without rhetorical filler.\n\n"

                f"STUDENT JOURNEY CONTEXT:\n{context_block}\n\n"

                f"LENGTH AND RICHNESS OF DETAIL: Write a complete, deeply educational text with a MINIMUM of {target_words} words (never less than 600 words).\n\n"

                f"LEVEL CALIBRATION: This lesson is at level '{level}'. If beginner, define every technical term, acronym, or mechanism upon first appearance in simple language, without presuming prior knowledge beyond what was taught before this module. If intermediate or advanced, jargon may be used with fewer pauses, but always with clarity.\n\n"

                f"STRUCTURE & EDITORIAL RULES:\n"
                f"- Start with '# {lesson_title}'.\n"
                f"- Open with a vivid scene or striking analogy in 2 paragraphs about '{lesson_title}', revealing the concept's paradox without AI clichés and NEVER in first-person ('I'). Keep at MOST ONE analogy (opening/close), zero metaphor piling, and cite the central paradox at MOST 2 times across the lesson (opening and Golden Rule).\n"
                f"- Develop '{core_concept}' with composure under thematic '## ' subtitles specific to this subject (never generic reusable titles like 'The Machinery in Motion' or 'The Starting Point'), each with 2 to 3 paragraphs grounded in verifiable facts, mechanisms, or data. In one of the sections, include the step-by-step numbered breakdown, creating subject-specific labels for each step (it is forbidden to use the labels 'the initial baseline', 'the core trade-off', or 'the systemic outcome' as literal text; they are internal functional guides only), highlighting key concepts in **bold**.\n"
                f"- Insert the callout '> Practical Everyday Example:' (a vivid and witty everyday vignette in 2 to 3 sentences).\n"
                f"- Develop '## Between Right and Trap' in clean analytical blocks (**The failing path:** [text] / **The working path:** [text] / > The Common Trap: [bringing a NEW angle, without repeating the opening paradox]). Clean formatting with zero loose asterisks.\n"
                f"- Insert callout '> 🟡 Golden Rule:' with the 1-2 sentence core rule followed by 1 reflective paragraph.\n"
                f"- Close with a provocative personal takeaway inviting reflection before advancing, bringing an additional angle rather than repeating the Golden Rule.\n"
                f"- End with '## Lesson Glossary' and '## Lesson Sources and Recommended Readings'.\n\n"

                f"REMEMBER: ABSOLUTE PROHIBITION of first-person ('I', 'my'), em-dash ('—'), header emojis, and empty adjectival melodrama. LEXICAL PRECISION ABOVE POETIC EFFECT: NEVER USE A WORD WHOSE EXACT MEANING IS NOT CERTAIN; ALWAYS PREFER THE SIMPLER, ACCURATE ALTERNATIVE."
            )
        else:
            system_prompt = (
                f"Você é {persona_title}.\n"
                f"Seu tom de voz obrigatório nesta matéria é: {tone_of_voice}.\n"
                f"Você é um ensaísta analítico, lúcido e profundamente didático (nível Richard Feynman, Yuval Harari e Coursera Masterclass).\n"
                f"Você está redigindo o texto canônico da apostila sobre '{subject}' no nível '{level}'.\n"
                f"Aula atual: Módulo {module_num} ({module_title}), Aula {lesson_num} - '{lesson_title}'.\n"
                f"Conceito Central que o aluno precisa dominar: {core_concept}.\n\n"

                f"DISCIPLINA EDITORIAL E ANALÍTICA (CORTES DE RUÍDO RETÓRICO):\n"
                f"Escreva com clareza analítica, ritmo firme e densidade factual. O aluno quer substância e raciocínio real, não poesia vazia.\n"
                f"1. CONTROLE DE METÁFORAS (PROIBIDO EMPILHAMENTO): Escolha NO MÁXIMO UMA analogia condutora para a aula (ex: semente/floresta, motor/combustão, mapa/terreno) e use-a estritamente na abertura e no fechamento. É terminantemente proibido amontoar metáforas diferentes no meio do texto ou repeti-las a cada parágrafo.\n"
                f"2. ZERO ADJETIVAÇÃO VAZIA E DRAMA BARATO: Corte intensificadores sem carga informativa como 'quase pobre, quase ridículo', 'invisível para os olhos apressados', 'num estalar de dedos' ou 'obsessão selvagem'. Prefira dados, mecanismos, fatos documentados, dilemas operacionais e métricas concretas.\n"
                f"3. AVANCE O ARGUMENTO SEM REPETIR A TESE: Não reformule a mesma tese ('comece pequeno para escalar depois', etc.) múltiplas vezes ao longo do texto com palavras diferentes. Expresse a tese com força máxima na Regra de Ouro, e use os parágrafos anteriores para desdobrar a mecânica, os trade-offs e os bastidores reais.\n"
                f"4. SOBRIEDADE DIDÁTICA (ZERO TOM DE AUTOAJUDA): Evite frases genéricas como 'o mestre muda o mundo a partir de uma única ação'. Crie títulos de '## ' específicos para o assunto da aula, sem repetir clichês literários como 'A Engrenagem em Ação' ou 'O Ponto de Partida' como cabeçalhos genéricos.\n"
                f"5. CALIBRAGEM OBRIGATÓRIA POR NÍVEL: O nível desta aula é '{level}'. Se for iniciante (ou equivalente), toda sigla, unidade técnica, mecanismo ou termo especializado deve ser definido em linguagem simples na primeira aparição, antes de ser usado livremente; não presuma nenhum conhecimento além do que já foi ensinado em módulos anteriores deste curso. Se for intermediário ou avançado, jargão técnico pode ser usado com menos pausas de definição, mas ainda assim de forma clara. Nunca escreva uma aula tecnicamente densa demais para o nível declarado.\n"
                f"6. PRECISÃO LEXICAL ACIMA DE TUDO: Nunca sacrifique a precisão do vocabulário por efeito dramático ou por soar mais literário. Se houver qualquer dúvida sobre o significado exato de uma palavra em português, substitua-a por uma alternativa mais simples e correta. Um erro de vocabulário é o pior defeito possível neste texto, pior do que uma frase levemente menos poética.\n"
                f"7. UMA MENÇÃO, UMA FUNÇÃO (ANTI-REPETIÇÃO ESTRUTURAL): O paradoxo central da aula pode ser citado no máximo 2 vezes em todo o texto (na abertura e na Regra de Ouro). As demais seções obrigatórias (Armadilha Comum, Provocação Final) devem trazer ângulos NOVOS e informações adicionais sobre o tema, nunca reafirmar o mesmo paradoxo ou a mesma tese com outras palavras.\n\n"

                f"ARQUITETURA NARRATIVA DA AULA EM 6 MOMENTOS ORGÂNICOS:\n"
                f"1. O GANCHO E O PARADOXO INICIAL:\n"
                f"   - Comece IMEDIATAMENTE com o título da aula em nível 1: '# {lesson_title}'.\n"
                f"   - Logo abaixo, abra direto numa cena viva, íntima e humana ou numa analogia cotidiana marcante do tema, desenvolvida em 2 parágrafos imersivos.\n"
                f"   - PROIBIDO fórmulas artificiais de IA como 'Você já percebeu como...' ou 'A intuição costuma nos enganar...'. Entre direto na história e mostre o paradoxo em ação.\n\n"

                f"2. A DESCONSTRUÇÃO DA INTUIÇÃO (A EXPLICAÇÃO ANALÍTICA E SEM PRESSA):\n"
                f"   - Desenvolva de 2 a 3 seções narrativas robustas usando subtítulos de nível 2 '## ' (NUNCA use '# ' para seções internas).\n"
                f"   - Os títulos '## ' devem ser temáticos e descritivos do conceito específico desta aula, e NÃO frases literárias genéricas reutilizáveis em qualquer assunto.\n"
                f"   - Cada seção DEVE conter no mínimo 2 a 3 parágrafos bem desenvolvidos e prazerosos de ler, mas SEMPRE ancorados em fatos, mecanismos ou dados verificáveis, nunca apenas em impressão poética.\n"
                f"   - Em uma das seções principais, desmonte a engrenagem passo a passo em formato numerado detalhado. Os rótulos de cada passo DEVEM ser criados especificamente para o vocabulário deste assunto (é proibido reutilizar literalmente os rótulos genéricos 'ponto de partida', 'inversão da lógica' e 'engrenagem em ação' como texto fixo; eles servem apenas como guia de FUNÇÃO de cada passo, não como texto a copiar):\n"
                f"     1. **[Rótulo específico do tema para o elemento ou arquétipo inicial]:** [Dissecção rica do elemento inicial]\n"
                f"     2. **[Rótulo específico do tema para a virada de lógica]:** [Como o mecanismo vira o senso comum de cabeça para baixo]\n"
                f"     3. **[Rótulo específico do tema para o resultado em ação]:** [Como essa virada ganha forma e produz o resultado prático no mundo real]\n"
                f"   - Use **negrito** estrategicamente nas palavras-chave e conceitos âncora para criar pontos focais luminosos na leitura.\n\n"

                f"3. EXEMPLO PRÁTICO NO COTIDIANO:\n"
                f"   - Insira um bloco de destaque no seguinte formato (sem emojis no título):\n"
                f"   > Exemplo Prático no Cotidiano: [Uma vinheta viva, visual e bem-humorada da rotina em 2 a 3 frases onde esse conceito atua em silêncio]\n\n"

                f"4. SEÇÃO 'ENTRE O ACERTO E A ARMADILHA' (FORMATO NARRATIVO EM BLOCOS):\n"
                f"   - Crie a seção com o título exato: '## Entre o Acerto e a Armadilha'.\n"
                f"   - Desenvolva o contraste em blocos claros e analíticos (markdown limpo, NUNCA deixe asteriscos soltos ou mal fechados):\n"
                f"     **O caminho que falha:** [A ilusão ou o erro comum do leigo/amador e a explicação técnica/psicológica de por que quebra o resultado]\n"
                f"     **O caminho que funciona:** [A atitude sagaz, elegante e eficaz do mestre/especialista que resolve o impasse]\n"
                f"     > A Armadilha Comum: [Um aviso prático e aprofundado sobre a casca de banana onde a maioria tropeça, trazendo um ângulo NOVO, não repetindo o paradoxo da abertura]\n\n"

                f"5. A REGRA DE OURO:\n"
                f"   - Apresente a sacada definitiva da aula em destaque:\n"
                f"   > 🟡 Regra de Ouro: [O princípio definitivo e memorável que resume a essência da aula em 1 a 2 frases de impacto]\n"
                f"   - Logo abaixo da Regra de Ouro, escreva 1 parágrafo reflexivo contextualizando a aplicação desse princípio na prática.\n\n"

                f"6. PROVOCAÇÃO FINAL:\n"
                f"   - Feche a narrativa com uma reflexão pessoal provocativa em 1 parágrafo que convide o aluno a olhar para si mesmo ou para a realidade ao seu redor de um jeito novo antes da próxima aula, trazendo um ângulo adicional, não uma repetição da Regra de Ouro.\n\n"

                f"LEIS VISUAIS E DE PONTUAÇÃO (RIGOR ABSOLUTO):\n"
                f"- É TERMINANTEMENTE PROIBIDO usar primeira pessoa do singular ('eu', 'eu percebi', 'eu voltei', 'minha viagem mental', 'eu acho')! Converse diretamente com o aluno ('você') ou narre os fatos e a matéria em terceira pessoa envolvente.\n"
                f"- É TERMINANTEMENTE PROIBIDO usar o caractere travessão ('—' ou '–') em qualquer parte do texto! Use vírgulas, parênteses ou ponto final para estruturar as frases com ritmo natural.\n"
                f"- É TERMINANTEMENTE PROIBIDO colocar emojis nos títulos das seções (proibido 📖, 📚, 💡, 🎯, etc. nos títulos '## ').\n"
                f"- PROIBIDO criar tabelas Markdown ou resumos telegráficos frios no meio da aula.\n\n"
                f"DIRETRIZES TÉCNICAS DE FÓRMULAS E CÓDIGO (SE APLICÁVEL):\n"
                f"- Se a aula tratar de matemática, física, economia quantitativa ou estatística, use notação KaTeX rigorosa: `$expressão$` para fórmulas inline e `$$equação$$` para equações em bloco. Certifique-se de que os delimitadores estejam sempre fechados.\n"
                f"- Se a aula tratar de programação ou computação, utilize blocos de código markdown com a linguagem explícita (ex: ```python, ```javascript, ```sql) com exemplos limpos, elegantes e funcionais.\n\n"
                f"SEÇÕES OBRIGATÓRIAS AO FINAL:\n"
                f"## Glossário da Aula\n"
                f"- **Termo 1**: Definição límpida, precisa e didática em 1 frase simples.\n"
                f"- **Termo 2**: Definição exata e acessível...\n"
                f"## Fontes e Leituras Recomendadas da Aula\n"
                f"- **[Título da Fonte ou Livro](URL)** (domínio): Breve síntese de 1 frase demonstrando como este estudo ou obra fundamentou a análise desta aula.\n"
                f"{sources_list_prompt}\n"
                f"{cases_constraint}"
                f"{ledger_block}\n"
            )
            user_prompt = (
                f"Escreva a apostila completa da Aula {lesson_num}: '{lesson_title}' ({core_concept}) com voz analítica, fluida, humana e sem gordura retórica.\n\n"

                f"CONTEXTO DO ALUNO NA JORNADA:\n{context_block}\n\n"

                f"EXTENSÃO E RIQUEZA DE DETALHES: Escreva um texto completo e substantivo, com no MÍNIMO {target_words} palavras (aproximadamente 4.000 a 4.800 caracteres no total; nunca faça resumos curtos abaixo de 600 palavras).\n\n"

                f"CALIBRAGEM DE NÍVEL: Esta aula é de nível '{level}'. Se for iniciante, defina cada termo técnico, sigla ou mecanismo na primeira aparição, em linguagem simples, sem presumir conhecimento prévio além do que já foi ensinado antes deste módulo. Se for intermediário ou avançado, pode usar jargão com menos pausas, mas sempre com clareza.\n\n"

                f"ESTRUTURA E REGRAS EDITORIAIS:\n"
                f"- Inicie com '# {lesson_title}'.\n"
                f"- Abra com uma cena viva ou analogia marcante em 2 parágrafos sobre '{lesson_title}', revelando o paradoxo do conceito sem clichês de IA e NUNCA em primeira pessoa ('eu'). Mantenha no MÁXIMO UMA analogia (abertura/fecho), sem empilhamento metafórico, e cite o paradoxo central no MÁXIMO 2 vezes em toda a aula (abertura e Regra de Ouro).\n"
                f"- Desenvolva o conceito '{core_concept}' com calma sob subtítulos narrativos '## ' temáticos e específicos deste assunto (nunca títulos genéricos reutilizáveis, como 'A Engrenagem em Ação' ou 'O Ponto de Partida'), cada um com 2 a 3 parágrafos ancorados em fatos, mecanismos ou dados verificáveis. Em uma das seções, inclua a dissecção numerada passo a passo, mas crie rótulos próprios do vocabulário deste tema para cada passo (é proibido usar literalmente os rótulos 'ponto de partida', 'inversão da lógica' e 'engrenagem em ação' como texto; eles são só um guia de função interno), destacando conceitos-chave em **negrito**.\n"
                f"- Insira o callout '> Exemplo Prático no Cotidiano:' (vinheta vívida e bem-humorada em 2 a 3 frases).\n"
                f"- Desenvolva a seção '## Entre o Acerto e a Armadilha' em blocos analíticos limpos (**O caminho que falha:** [texto] / **O caminho que funciona:** [texto] / > A Armadilha Comum: [trazendo um ângulo NOVO, sem repetir o paradoxo da abertura]). Formatação perfeita sem asteriscos soltos ou mal fechados.\n"
                f"- Insira o callout '> 🟡 Regra de Ouro:' com a sacada definitiva em 1 a 2 frases, acompanhado de 1 parágrafo reflexivo.\n"
                f"- Feche com uma provocação pessoal instigante para o aluno refletir antes de avançar, trazendo um ângulo adicional em vez de repetir a Regra de Ouro.\n"
                f"- Finalize com '## Glossário da Aula' e '## Fontes e Leituras Recomendadas da Aula'.\n\n"

                f"LEMBRE-SE: PROIBIÇÃO ABSOLUTA DA PRIMEIRA PESSOA ('EU', 'PERCEBI', ETC.), DO SÍMBOLO '—' (travessão), DE EMOJIS NOS TÍTULOS E DE ADJETIVAÇÃO VAZIA SEM DADOS. PRECISÃO LEXICAL ACIMA DE EFEITO POÉTICO: NUNCA USE UMA PALAVRA CUJO SIGNIFICADO EXATO NÃO SEJA CERTO; PREFIRA SEMPRE A ALTERNATIVA MAIS SIMPLES E CORRETA."
            )

        raw_text = await LLMGateway.generate_text(system_prompt, user_prompt, max_tokens=3800, timeout=60)
        # Sanitização e normalização de cabeçalhos markdown
        cleaned_text = re.sub(r'^[ \t]*(#{1,6})(?:\s*#+)+\s*', r'\1 ', raw_text, flags=re.MULTILINE)
        cleaned_text = re.sub(r'^\s*\[(?:Hook|Note|Intuition|Case)[^\]]*\]\s*\n+', '', cleaned_text, flags=re.IGNORECASE | re.MULTILINE)
        cleaned_text = re.sub(r'^\s*(?:Hook paragraph|Hook vivid|Then intuitive explanation|Include case study|Add STIPPLE_IMAGE)[^\n]*\n+', '', cleaned_text, flags=re.IGNORECASE | re.MULTILINE)
        cleaned_text = re.sub(r'\b[êe]mbolo\b', 'pistão', cleaned_text, flags=re.IGNORECASE)
        # Banimento e substituição limpa de travessões (em-dash e en-dash)
        cleaned_text = re.sub(r'\s*[—–]\s*', ', ', cleaned_text)
        # Banimento de primeira pessoa do singular
        cleaned_text = re.sub(r'\b[Ee]u voltei dessa viagem mental e percebi:\s*', 'Ao olhar com atenção para essa engrenagem, percebe-se algo fundamental: ', cleaned_text)
        cleaned_text = re.sub(r'\b[Ee]u percebi\b', 'percebe-se', cleaned_text)
        cleaned_text = re.sub(r'\b[Ee]u voltei\b', 'voltando', cleaned_text)
        cleaned_text = re.sub(r'\b[Ee]u acho\b', 'nota-se', cleaned_text)
        cleaned_text = re.sub(r'\b[Nn]a minha opinião\b', 'na prática', cleaned_text)
        cleaned_text = re.sub(r'\bI noticed\b', 'one notices', cleaned_text, flags=re.IGNORECASE)
        cleaned_text = re.sub(r'\bIn my opinion\b', 'in practice', cleaned_text, flags=re.IGNORECASE)
        cleaned_text = re.sub(r'\bI believe\b', 'it is clear that', cleaned_text, flags=re.IGNORECASE)

        # HIGIENIZAÇÃO DETERMINÍSTICA DE PONTUAÇÃO E FORMATAÇÃO MARKDOWN
        # Garante remoção física de travessões
        cleaned_text = re.sub(r'\s*[—–]\s*', ', ', cleaned_text)
        # Limpeza de asteriscos soltos nos blocos de contraste
        cleaned_text = re.sub(r'\*\*\s*:\s*', ': ', cleaned_text)
        cleaned_text = re.sub(r':\s*\*\*\s*', ': ', cleaned_text)
        cleaned_text = re.sub(r'(^|\n)(\s*(?:\d+\.|\-)\s*\*\*([^\n:\*\(\]]+)):(?!\/)', r'\1\2**: ', cleaned_text)

        # Converte títulos secundários de nível 1 (# ) em nível 2 (## )
        first_h1_found = False
        def normalize_h1(match):
            nonlocal first_h1_found
            header_text = match.group(1).strip()
            if not first_h1_found:
                first_h1_found = True
                return f"# {header_text}"
            return f"## {header_text}"
        cleaned_text = re.sub(r'^#\s+([^#\n].*)$', normalize_h1, cleaned_text, flags=re.MULTILINE)

        # Separa a seção de Glossário caso a IA tenha colado junto à última linha
        cleaned_text = re.sub(r'([^\n])\s*(##\s*(?:Gloss[aá]rio|Glossary))', r'\1\n\n\2', cleaned_text)

        # Normalização dos títulos de seções estruturais
        cleaned_text = re.sub(r'^(?:#{1,3})\s*(?:📊\s*)?(?:Resumo Visual|Visual Summary)[^\n]*\n+[\s\S]*?(?=(?:#{1,3})\s*(?:📖\s*)?(?:Gloss[aá]rio|Glossary)|$)', '', cleaned_text, flags=re.MULTILINE)
        if is_en:
            cleaned_text = re.sub(r'^(?:#{1,3})\s*(?:📖\s*)?(?:Gloss[aá]rio|Glossary)\s*(?:of\s*the\s*Lesson)?', r'## Lesson Glossary', cleaned_text, flags=re.MULTILINE)
            cleaned_text = re.sub(r'^(?:#{1,3})\s*(?:📚\s*)?(?:Fontes|Sources)(?:\s*(?:e|and)\s*(?:Leituras|Readings))?\s*(?:Recomendadas|Recommended)?(?:\s*(?:da|of\s*the)\s*(?:Aula|Lesson))?', r'## Lesson Sources and Recommended Readings', cleaned_text, flags=re.MULTILINE)
            cleaned_text = re.sub(r'^(?:#{1,3})\s*(?:⚖️\s*)?(?:Entre\s*o\s*Acerto\s*e\s*a\s*Armadilha|Between\s*Right\s*and\s*Trap)', r'## Between Right and Trap', cleaned_text, flags=re.MULTILINE)
            cleaned_text = re.sub(r'^(?:[-*]\s*)?(?:\*\*)?(?:The failing path|O caminho que falha)(?:\*\*)?[:\s]*(?:\*\*)?\s*(.*)$', r'**The failing path:** \1', cleaned_text, flags=re.MULTILINE | re.IGNORECASE)
            cleaned_text = re.sub(r'^(?:[-*]\s*)?(?:\*\*)?(?:The working path|O caminho que funciona)(?:\*\*)?[:\s]*(?:\*\*)?\s*(.*)$', r'**The working path:** \1', cleaned_text, flags=re.MULTILINE | re.IGNORECASE)
        else:
            cleaned_text = re.sub(r'^(?:#{1,3})\s*(?:📖\s*)?Gloss[aá]rio\s*(?:da\s*Aula)?', r'## Glossário da Aula', cleaned_text, flags=re.MULTILINE)
            cleaned_text = re.sub(r'^(?:#{1,3})\s*(?:📚\s*)?Fontes(?:\s*e\s*Leituras)?\s*(?:Recomendadas)?(?:\s*da\s*Aula)?', r'## Fontes e Leituras Recomendadas da Aula', cleaned_text, flags=re.MULTILINE)
            cleaned_text = re.sub(r'^(?:#{1,3})\s*(?:⚖️\s*)?Entre\s*o\s*Acerto\s*e\s*a\s*Armadilha', r'## Entre o Acerto e a Armadilha', cleaned_text, flags=re.MULTILINE)
            cleaned_text = re.sub(r'^(?:[-*]\s*)?(?:\*\*)?O caminho que falha(?:\*\*)?[:\s]*(?:\*\*)?\s*(.*)$', r'**O caminho que falha:** \1', cleaned_text, flags=re.MULTILINE | re.IGNORECASE)
            cleaned_text = re.sub(r'^(?:[-*]\s*)?(?:\*\*)?O caminho que funciona(?:\*\*)?[:\s]*(?:\*\*)?\s*(.*)$', r'**O caminho que funciona:** \1', cleaned_text, flags=re.MULTILINE | re.IGNORECASE)

        cleaned_text = re.sub(r'(\*\*(?:O caminho que falha|O caminho que funciona|The failing path|The working path):\*\*)\s*\*\*\s*', r'\1 ', cleaned_text)

        # =========================================================================
        # CAMADA DETERMINÍSTICA DE REVISÃO EDITORIAL E EXPANSÃO (CRITIC PASS)
        # =========================================================================
        word_count = len(re.findall(r'\b\w+\b', cleaned_text))
        
        # Detecta necessidade de polimento: texto curto (< 550 palavras) ou falhas de gramática/tradução
        if word_count < 550:
            if is_en:
                revisor_system = (
                    "You are the Chief Senior Editor of Trivium Academy. "
                    "Your mission is to polish and naturally expand this lesson draft to meet our masterclass standard.\n"
                    "EDITORIAL RULES:\n"
                    "1. EXPAND depth and pedagogical richness across all narrative sections so the total length reaches 700-800 words.\n"
                    "2. FIX all grammatical flaws, awkward phrasing, word choices, or unnatural syntax.\n"
                    "3. KEEP all structural Markdown elements intact (# Title, ## Subtitles, > Practical Everyday Example, ## Between Right and Trap, > 🟡 Golden Rule, ## Lesson Glossary, ## Lesson Sources and Recommended Readings).\n"
                    "4. STRICTLY FORBIDDEN: first-person ('I'), em-dash ('—'), or empty melodrama.\n"
                    "Return ONLY the complete, corrected and enriched Markdown text."
                )
                revisor_user = (
                    f"The current draft on '{lesson_title}' ({core_concept}) has only {word_count} words and needs editorial expansion and lexical correction.\n"
                    f"Here is the draft:\n\n{cleaned_text}\n\n"
                    f"Return the complete, expanded and polished lesson now."
                )
            else:
                revisor_system = (
                    "Você é o Editor-Chefe Sênior da Trivium Academy. "
                    "Sua missão é revisar, corrigir qualquer vício de linguagem, erro gramatical ou tradução mecânica (como falsos cognatos, concordâncias truncadas ou palavras sem sentido), e expandir o conteúdo com profundidade pedagógica para o padrão Masterclass.\n"
                    "DIRETRIZES DA REVISÃO:\n"
                    "1. CORREÇÃO GRAMATICAL E LEXICAL PURA: Corrija imediatamente qualquer erro de ortografia, pontuação, concordância ou palavras traduzidas incorretamente do inglês (por exemplo, construções como 'quando a vez checa' devem ser corrigidas para o português natural e preciso: 'quando a sua vez chega').\n"
                    "2. EXPANSÃO DE PROFUNDIDADE: O rascunho atual ficou curto. Desenvolva as seções narrativas adicionando contexto operacional e explicando os detalhes físicos/práticos com clareza, atingindo entre 700 e 800 palavras sem enrolação.\n"
                    "3. PRESERVE A ESTRUTURA EXATA: Mantenha o título '# ', subtítulos '## ', callouts '> Exemplo Prático no Cotidiano:', '## Entre o Acerto e a Armadilha', '> 🟡 Regra de Ouro:', '## Glossário da Aula' e '## Fontes e Leituras Recomendadas da Aula'.\n"
                    "4. RIGOR: Proibido primeira pessoa ('eu') e proibido travessão ('—').\n"
                    "Responda exclusivamente com o texto completo da apostila revisada em Markdown limpo."
                )
                revisor_user = (
                    f"O rascunho da aula '{lesson_title}' ({core_concept}) possui apenas {word_count} palavras e contém imperfeições de vocabulário que precisam de lapidação editorial.\n"
                    f"Rascunho atual:\n\n{cleaned_text}\n\n"
                    f"Entregue agora o texto completo, corrigido e expandido com maestria."
                )

            try:
                expanded_text = await LLMGateway.generate_text(revisor_system, revisor_user, max_tokens=3800, timeout=60)
                if expanded_text and len(re.findall(r'\b\w+\b', expanded_text)) > word_count:
                    # Aplica a mesma sanitização determinística no texto expandido
                    cleaned_text = re.sub(r'^[ \t]*(#{1,6})(?:\s*#+)+\s*', r'\1 ', expanded_text, flags=re.MULTILINE)
                    cleaned_text = re.sub(r'\s*[—–]\s*', ', ', cleaned_text)
                    cleaned_text = re.sub(r'\*\*\s*:\s*', ': ', cleaned_text)
                    cleaned_text = re.sub(r':\s*\*\*\s*', ': ', cleaned_text)
                    cleaned_text = re.sub(r'(^|\n)(\s*(?:\d+\.|\-)\s*\*\*([^\n:\*]+)):', r'\1\2**: ', cleaned_text)
            except Exception as e:
                print(f"[WriterAgent] Loop de expansão editorial ignorado por timeout/erro: {e}")

        # Higienização cirúrgica de links markdown (corrige casos de [Texto](https**: //url)** gerados por modelos)
        cleaned_text = re.sub(r'\[([^\]]+)\]\((https?):\s*\/\/\s*([^\)]+)\)', r'[\1](\2://\3)', cleaned_text)
        cleaned_text = re.sub(r'-\s*\*\*\[([^\]]+)\]\((https?[^\)]+)\)\*\*', r'- [\1](\2)', cleaned_text)
        cleaned_text = re.sub(r'-\s*\[([^\]]+)\]\((https?[^\)]+)\)\s*\*\*', r'- [\1](\2)', cleaned_text)

        return cleaned_text

class QuizMasterAgent:
    @staticmethod
    async def generate_quiz(
        lesson_title: str,
        lesson_content: str,
        level: str = "Básico",
        previous_questions: list[str] = None,
        core_concept: str = "",
        domain_profile: dict = None,
        language: str = "pt-BR"
    ) -> QuizSchema:
        is_en = language.lower().startswith("en")
        rubric_hint = ""
        domain_rubric_core = "Rigor conceitual, coerência argumentativa e aplicabilidade prática" if not is_en else "Conceptual rigor, argumentative coherence, and practical applicability"
        if domain_profile:
            domain_rubric_core = domain_profile.get("evaluation_rubric_core") or domain_rubric_core
            rubric_hint = f"\nDIRETRIZ DA RUBRICA DO DOMÍNIO ({domain_profile.get('dynamic_domain_name', 'Geral')}): {domain_rubric_core}\n"

        if is_en:
            schema_example = json.dumps({
                "lesson_title": lesson_title,
                "core_concept": core_concept,
                "socratic_duel": {
                    "question": "Engaging, open-ended practical dilemma demanding direct application of the lesson's core concept.",
                    "evaluation_rubric": [
                        f"Criterion 1: Student demonstrates intuitive understanding and adherence to the core principle: {domain_rubric_core}.",
                        "Criterion 2: The argument presented has coherent ground to be challenged by the Cognitive Knot."
                    ]
                },
                "mcq": [
                    {
                        "question": "Objective question statement in natural English",
                        "options": [
                            {"label": "A", "text": "Alternative A", "is_correct": True},
                            {"label": "B", "text": "Alternative B", "is_correct": False},
                            {"label": "C", "text": "Alternative C", "is_correct": False}
                        ],
                        "explanation": "Clear explanation of the correct answer based on the lesson text"
                    }
                ],
                "simulation": {
                    "context": "Concise practical scenario (2 to 3 sentences) contextualized in the lesson topic.",
                    "initial_indicators": [
                        {"name": "Quality & Efficiency", "value_type": "percentage", "value": 75, "color_hint": "green"},
                        {"name": "Cost & Risk", "value_type": "percentage", "value": 80, "color_hint": "red"},
                        {"name": "Team Morale & Stability", "value_type": "label", "value": "Moderate", "color_hint": "yellow"}
                    ],
                    "turn1_prompt": "Faced with this scenario, what is your primary strategic intervention?",
                    "turn1_options": [
                        {
                            "id": "A",
                            "text": "Primary strategic action A",
                            "reaction_story": "Your decision stabilized X, but triggered an unforeseen side effect Y.",
                            "updated_indicators": [
                                {"name": "Quality & Efficiency", "value_type": "percentage", "value": 85, "color_hint": "green"},
                                {"name": "Cost & Risk", "value_type": "percentage", "value": 65, "color_hint": "yellow"},
                                {"name": "Team Morale & Stability", "value_type": "label", "value": "Critical", "color_hint": "red"}
                            ],
                            "turn2_prompt": "How will you contain this unexpected side effect?",
                            "turn2_options": [
                                {
                                    "id": "A",
                                    "text": "Immediate targeted mitigation",
                                    "outcome_story": "Containment was swift and rebalanced operations sustainably.",
                                    "final_indicators": [
                                        {"name": "Quality & Efficiency", "value_type": "percentage", "value": 90, "color_hint": "green"},
                                        {"name": "Cost & Risk", "value_type": "percentage", "value": 60, "color_hint": "green"},
                                        {"name": "Team Morale & Stability", "value_type": "label", "value": "Healthy", "color_hint": "green"}
                                    ],
                                    "verdict_summary": "Simulation Successfully Mastered. Excellent balance between gain and risk mitigation.",
                                    "is_success": True
                                },
                                {
                                    "id": "B",
                                    "text": "Long-term structural mitigation",
                                    "outcome_story": "Processes were redesigned with continuous stability.",
                                    "final_indicators": [
                                        {"name": "Quality & Efficiency", "value_type": "percentage", "value": 85, "color_hint": "green"},
                                        {"name": "Cost & Risk", "value_type": "percentage", "value": 55, "color_hint": "green"},
                                        {"name": "Team Morale & Stability", "value_type": "label", "value": "Excellent", "color_hint": "green"}
                                    ],
                                    "verdict_summary": "Simulation Completed with Honors. Consistent, lasting strategic choice.",
                                    "is_success": True
                                },
                                {
                                    "id": "C",
                                    "text": "Minimal reactive fix",
                                    "outcome_story": "Containment was only partial and stability remained fragile.",
                                    "final_indicators": [
                                        {"name": "Quality & Efficiency", "value_type": "percentage", "value": 70, "color_hint": "yellow"},
                                        {"name": "Cost & Risk", "value_type": "percentage", "value": 75, "color_hint": "yellow"},
                                        {"name": "Team Morale & Stability", "value_type": "label", "value": "Alert", "color_hint": "yellow"}
                                    ],
                                    "verdict_summary": "Operation Completed with Trade-offs. Survives but requires ongoing care.",
                                    "is_success": True
                                }
                            ]
                        }
                    ]
                }
            }, ensure_ascii=False)
        else:
            schema_example = json.dumps({
                "lesson_title": lesson_title,
                "core_concept": core_concept,
                "socratic_duel": {
                    "question": "Dilema prático aberto instigante que exige aplicação da ideia central da aula.",
                    "evaluation_rubric": [
                        f"Critério 1: O aluno demonstra compreensão intuitiva e aderência ao princípio: {domain_rubric_core}.",
                        "Critério 2: A tese apresentada possui fundamentação coerente para ser desafiada pelo Nó Cognitivo."
                    ]
                },
                "mcq": [
                    {
                        "question": "Enunciado da questão objetiva",
                        "options": [
                            {"label": "A", "text": "Alternativa A", "is_correct": True},
                            {"label": "B", "text": "Alternativa B", "is_correct": False},
                            {"label": "C", "text": "Alternativa C", "is_correct": False}
                        ],
                        "explanation": "Justificativa da resposta correta"
                    }
                ],
                "simulation": {
                    "context": "Situação prática resumida (2 a 3 frases) contextualizada no assunto da aula.",
                    "initial_indicators": [
                        {"name": "Eficiência / Qualidade", "value_type": "percentage", "value": 75, "color_hint": "green"},
                        {"name": "Custo / Risco", "value_type": "percentage", "value": 80, "color_hint": "red"},
                        {"name": "Moral / Estabilidade", "value_type": "label", "value": "Moderado", "color_hint": "yellow"}
                    ],
                    "turn1_prompt": "Diante deste cenário, qual é a sua intervenção inicial prioritária?",
                    "turn1_options": [
                        {
                            "id": "A",
                            "text": "Ação estratégica primária A",
                            "reaction_story": "A sua decisão estabilizou X, mas gerou um efeito colateral imprevisto Y.",
                            "updated_indicators": [
                                {"name": "Eficiência / Qualidade", "value_type": "percentage", "value": 85, "color_hint": "green"},
                                {"name": "Custo / Risco", "value_type": "percentage", "value": 65, "color_hint": "yellow"},
                                {"name": "Moral / Estabilidade", "value_type": "label", "value": "Crítico", "color_hint": "red"}
                            ],
                            "turn2_prompt": "Como você conterá este efeito colateral imprevisto?",
                            "turn2_options": [
                                {
                                    "id": "A",
                                    "text": "Mitigação pontual imediata",
                                    "outcome_story": "A contenção foi rápida e equilibrou a operação de forma sustentável.",
                                    "final_indicators": [
                                        {"name": "Eficiência / Qualidade", "value_type": "percentage", "value": 90, "color_hint": "green"},
                                        {"name": "Custo / Risco", "value_type": "percentage", "value": 60, "color_hint": "green"},
                                        {"name": "Moral / Estabilidade", "value_type": "label", "value": "Saudável", "color_hint": "green"}
                                    ],
                                    "verdict_summary": "Simulação Concluída com Sucesso. Excelente balanço entre ganho e mitigação de risco.",
                                    "is_success": True
                                },
                                {
                                    "id": "B",
                                    "text": "Mitigação estrutural de longo prazo",
                                    "outcome_story": "Os processos foram reestruturados com estabilidade contínua.",
                                    "final_indicators": [
                                        {"name": "Eficiência / Qualidade", "value_type": "percentage", "value": 85, "color_hint": "green"},
                                        {"name": "Custo / Risco", "value_type": "percentage", "value": 55, "color_hint": "green"},
                                        {"name": "Moral / Estabilidade", "value_type": "label", "value": "Excelente", "color_hint": "green"}
                                    ],
                                    "verdict_summary": "Simulação Concluída com Louvor. Decisão consistente e duradoura.",
                                    "is_success": True
                                },
                                {
                                    "id": "C",
                                    "text": "Ação paliativa mínima",
                                    "outcome_story": "A contenção foi parcial e o indicador de estabilidade permaneceu vulnerável.",
                                    "final_indicators": [
                                        {"name": "Eficiência / Qualidade", "value_type": "percentage", "value": 70, "color_hint": "yellow"},
                                        {"name": "Custo / Risco", "value_type": "percentage", "value": 75, "color_hint": "yellow"},
                                        {"name": "Moral / Estabilidade", "value_type": "label", "value": "Alerta", "color_hint": "yellow"}
                                    ],
                                    "verdict_summary": "Operação Concluída com Trade-offs. Operação sobreviveu mas exige atenção.",
                                    "is_success": True
                                }
                            ]
                        },
                        {
                            "id": "B",
                            "text": "Ação estratégica primária B",
                            "reaction_story": "Desdobramento da opção B com efeito colateral em outro indicador.",
                            "updated_indicators": [
                                {"name": "Eficiência / Qualidade", "value_type": "percentage", "value": 60, "color_hint": "yellow"},
                                {"name": "Custo / Risco", "value_type": "percentage", "value": 90, "color_hint": "red"},
                                {"name": "Moral / Estabilidade", "value_type": "label", "value": "Saudável", "color_hint": "green"}
                            ],
                            "turn2_prompt": "Como você reverterá essa pressão de custo/risco?",
                            "turn2_options": [
                                {
                                    "id": "A",
                                    "text": "Ajuste orçamentário rígido",
                                    "outcome_story": "Equilíbrio financeiro restabelecido.",
                                    "final_indicators": [
                                        {"name": "Eficiência / Qualidade", "value_type": "percentage", "value": 80, "color_hint": "green"},
                                        {"name": "Custo / Risco", "value_type": "percentage", "value": 60, "color_hint": "green"},
                                        {"name": "Moral / Estabilidade", "value_type": "label", "value": "Saudável", "color_hint": "green"}
                                    ],
                                    "verdict_summary": "Simulação Concluída com Sucesso.",
                                    "is_success": True
                                },
                                {
                                    "id": "B",
                                    "text": "Redução do escopo da entrega",
                                    "outcome_story": "Alívio imediato mas entrega limitada.",
                                    "final_indicators": [
                                        {"name": "Eficiência / Qualidade", "value_type": "percentage", "value": 75, "color_hint": "yellow"},
                                        {"name": "Custo / Risco", "value_type": "percentage", "value": 50, "color_hint": "green"},
                                        {"name": "Moral / Estabilidade", "value_type": "label", "value": "Estável", "color_hint": "green"}
                                    ],
                                    "verdict_summary": "Simulação Concluída. Trade-off consciente de escopo.",
                                    "is_success": True
                                },
                                {
                                    "id": "C",
                                    "text": "Manter como está e focar em prazos",
                                    "outcome_story": "Pressão continuou elevada.",
                                    "final_indicators": [
                                        {"name": "Eficiência / Qualidade", "value_type": "percentage", "value": 70, "color_hint": "yellow"},
                                        {"name": "Custo / Risco", "value_type": "percentage", "value": 85, "color_hint": "red"},
                                        {"name": "Moral / Estabilidade", "value_type": "label", "value": "Moderado", "color_hint": "yellow"}
                                    ],
                                    "verdict_summary": "Operação de Alto Risco. Margens operacionais no limite.",
                                    "is_success": True
                                }
                            ]
                        },
                        {
                            "id": "C",
                            "text": "Ação estratégica primária C",
                            "reaction_story": "Desdobramento da opção C com impacto em tempo e recursos.",
                            "updated_indicators": [
                                {"name": "Eficiência / Qualidade", "value_type": "percentage", "value": 80, "color_hint": "green"},
                                {"name": "Custo / Risco", "value_type": "percentage", "value": 70, "color_hint": "yellow"},
                                {"name": "Moral / Estabilidade", "value_type": "label", "value": "Alerta", "color_hint": "yellow"}
                            ],
                            "turn2_prompt": "Qual é a sua decisão de fechamento para consolidar os ganhos?",
                            "turn2_options": [
                                {
                                    "id": "A",
                                    "text": "Alinhamento com as partes envolvidas",
                                    "outcome_story": "Consenso obtido e operação estabilizada.",
                                    "final_indicators": [
                                        {"name": "Eficiência / Qualidade", "value_type": "percentage", "value": 85, "color_hint": "green"},
                                        {"name": "Custo / Risco", "value_type": "percentage", "value": 65, "color_hint": "green"},
                                        {"name": "Moral / Estabilidade", "value_type": "label", "value": "Saudável", "color_hint": "green"}
                                    ],
                                    "verdict_summary": "Simulação Concluída com Sucesso.",
                                    "is_success": True
                                },
                                {
                                    "id": "B",
                                    "text": "Treinamento intensivo da equipe",
                                    "outcome_story": "Capacitação rápida garantiu suporte sólido.",
                                    "final_indicators": [
                                        {"name": "Eficiência / Qualidade", "value_type": "percentage", "value": 90, "color_hint": "green"},
                                        {"name": "Custo / Risco", "value_type": "percentage", "value": 60, "color_hint": "green"},
                                        {"name": "Moral / Estabilidade", "value_type": "label", "value": "Excelente", "color_hint": "green"}
                                    ],
                                    "verdict_summary": "Simulação Concluída com Excelência.",
                                    "is_success": True
                                },
                                {
                                    "id": "C",
                                    "text": "Desacelerar o ritmo para absorção gradual",
                                    "outcome_story": "Ritmo menor garantiu previsibilidade.",
                                    "final_indicators": [
                                        {"name": "Eficiência / Qualidade", "value_type": "percentage", "value": 75, "color_hint": "yellow"},
                                        {"name": "Custo / Risco", "value_type": "percentage", "value": 55, "color_hint": "green"},
                                        {"name": "Moral / Estabilidade", "value_type": "label", "value": "Tranquilo", "color_hint": "green"}
                                    ],
                                    "verdict_summary": "Simulação Concluída com Estabilidade.",
                                    "is_success": True
                                }
                            ]
                        }
                    ]
                }
            }, ensure_ascii=False)

        questions_memory = ""
        if previous_questions:
            recent_questions = previous_questions[-20:]
            questions_list = "\n".join(f"- {q}" for q in recent_questions)
            if is_en:
                questions_memory = (
                    f"\nPREVIOUS QUESTIONS MEMORY (STRICTLY FORBIDDEN TO REPEAT IDENTICAL PROMPTS):\n"
                    f"The following questions were already asked in previous lessons. Your 3 new questions and Socratic Duel MUST be 100% original:\n"
                    f"{questions_list}\n"
                )
            else:
                questions_memory = (
                    f"\nMEMÓRIA DE QUESTÕES ANTERIORES DO CURSO (PROIBIDO REPETIR ENUNCIADOS OU TEMÁTICAS IDÊNTICAS):\n"
                    f"As seguintes perguntas já foram feitas em aulas anteriores. Suas 3 novas questões e o Duelo Socrático DEVEM ser 100% inéditos, abordando novos ângulos e conceitos específicos desta aula:\n"
                    f"{questions_list}\n"
                )

        if is_en:
            system_prompt = (
                f"You are the Assessment and Cognitive Challenge Architect of Trivium for courses at the '{level}' level.\n"
                f"Your mission is to transform lesson verification into a high-impact practical and reflective ecosystem in NATURAL ENGLISH.\n"
                f"{rubric_hint}\n"
                f"ABSOLUTE PEDAGOGICAL LAWS (STRICT RIGOR):\n"
                f"A. 100% GROUNDED IN LESSON CONTENT:\n"
                f"   - Every question, alternative, and consequence MUST be formulated EXCLUSIVELY from what was taught and explained in the provided lesson text.\n"
                f"   - NEVER assume advanced external knowledge or unintroduced jargon.\n"
                f"   - Mini-Simulation choices (Turn 1 & 2) MUST be strategic decisions in natural, intuitive language accessible to the '{level}' level.\n"
                f"B. REALISTIC AND CONTEMPORARY PRACTICAL CASE STUDY:\n"
                f"   - Formulate a plausible real-world situation applying the core concept '{core_concept}'.\n"
                f"   - ZERO infantile fairy tales or archaic fables. Create real market, engineering, design, editorial, or scientific scenarios.\n"
                f"   - Structure: Brief context (2 lines) -> Two contrasting routes (Route A vs Route B) -> Direct prompt: 'Which path would you recommend to solve the challenge and what is your strategic rationale based on the lesson?'\n"
                f"{questions_memory}\n"
                f"STRUCTURE GUIDELINES:\n"
                f"1. INTERACTIVE CASE STUDY (socratic_duel) [FIRST IN JSON]: Open practical dilemma with 2 decision paths and 2 clear rubric criteria.\n"
                f"2. OBJECTIVE QUESTIONS (mcq): Exactly 3 multiple-choice questions with 3 options (A, B, C), only one correct (is_correct=True), with concise didactic explanation.\n"
                f"3. 2-TURN IMPACT MINI-SIMULATOR (simulation):\n"
                f"   - Practical simulation with 3 tangible indicators, full causal tree:\n"
                f"   - Turn 1: RIGIDLY EXACTLY 3 options (id: 'A', 'B', 'C').\n"
                f"   - Turn 2: RIGIDLY EXACTLY 3 options (id: 'A', 'B', 'C') for EACH Turn 1 option (mitigation/strategic follow-up).\n"
                f"   - Outcome: Final indicators, trade-off verdict, and is_success=True.\n\n"
                f"CRITICAL: ALL content must be written in NATURAL ENGLISH.\n"
                f"Respond exclusively with a valid JSON object matching this schema:\n"
                f"{schema_example}"
            )
            concept_hint = f" (Core concept: {core_concept})" if core_concept else ""
            safe_content = (lesson_content or "").strip()
            user_prompt = f"Generate the complete Quiz (1 priority Socratic Duel, 3 original MCQs, and 1 pre-generated 2-Turn Impact Mini-Simulation with exactly 3 options in both Turn 1 and Turn 2) in English for lesson '{lesson_title}'{concept_hint} based on this text:\n\n{safe_content[:1800]}"
        else:
            system_prompt = (
                f"Você é o Arquiteto de Avaliação e Desafios Cognitivos da Trivium para cursos no nível '{level}'.\n"
                f"Sua missão é transformar a verificação da aula em um ecossistema de alto impacto prático e reflexivo.\n"
                f"{rubric_hint}\n"
                f"LEIS PEDAGÓGICAS ABSOLUTAS DO QUIZ (RIGOR CONTRA JARGÕES DESCONEXOS E CONTRA DUPLICIDADES):\n"
                f"A. 100% BASEADO NO CONTEÚDO DA AULA (ZERO PRESSUPOSTO DE CONHECIMENTO PRÉVIO):\n"
                f"   - Toda pergunta, alternativa e desdobramento DEVE ser formulado EXCLUSIVAMENTE a partir do que foi ensinado e explicado no texto da aula fornecido.\n"
                f"   - É TERMINANTEMENTE PROIBIDO exigir conhecimento de arquiteturas avançadas, engenharia de software ou jargões em inglês que não tenham sido explicitamente explicados e detalhados no texto da aula.\n"
                f"   - As opções de ação do Mini-Simulador (Turno 1 e Turno 2) DEVEM ser decisões estratégicas em linguagem natural, intuitiva e acessível ao nível '{level}'.\n"
                f"B. ESTUDO DE CASO PRÁTICO E REALISTA (PRIORIDADE MÁXIMA):\n"
                f"   - Formule uma situação prática contemporânea e plausível aplicando o conceito central '{core_concept}'.\n"
                f"   - ZERO contos de fadas infantis ou fábulas arcaicas. Crie cenários reais de mercado, engenharia, design, redação ou ciência.\n"
                f"   - Estrutura: Contexto breve (2 linhas) -> Duas rotas contrastantes (Rota A vs Rota B) -> Pergunta direta: 'Qual caminho você recomendaria para solucionar o desafio e qual justificativa estratégica você defenderia?'\n"
                f"     * Pergunta de fechamento direta: 'Qual caminho você recomendaria para resolver o desafio e qual é a sua justificativa estratégica baseada na aula?'\n"
                f"{questions_memory}\n"
                f"DIRETRIZES DA ESTRUTURA DO QUIZ:\n"
                f"1. ESTUDO DE CASO INTERATIVO (socratic_duel) [GERADO PRIMEIRO NO JSON]:\n"
                f"   - Formule o caso prático aberto instigante e acessível com 2 caminhos de decisão (Rota 1 vs Rota 2).\n"
                f"   - Defina 2 critérios claros na rubrica para orientar o posterior Desafio de Cenário com trade-offs.\n\n"
                f"2. QUESTÕES OBJETIVAS (mcq):\n"
                f"   - Exatamente 3 questões de múltipla escolha com 3 alternativas (A, B e C), sendo apenas uma correta (is_correct=True).\n"
                f"   - Cada questão DEVE ter uma explicação concisa e didática justificando o gabarito com base no texto.\n"
                f"   - É PROIBIDO repetir enunciados ou temas das aulas anteriores.\n\n"
                f"3. MINI-SIMULADOR DE IMPACTO EM 2 TURNOS (simulation - Interactive Sandbox):\n"
                f"   - Crie uma simulação prática viva baseada no tema exato da aula.\n"
                f"   - Defina 3 indicadores tangíveis contextualizados (0-100% ou rótulos qualitativos como Crítico, Baixo, Moderado, Alto, Saudável, Excelente).\n"
                f"   - Crie a árvore de causalidade completa:\n"
                f"     * Turno 1: RIGOROSAMENTE 3 opções de ação (id: 'A', 'B', 'C').\n"
                f"     * Cada opção do Turno 1 DEVE conter reação de desdobramento + efeito colateral + atualização dos indicadores.\n"
                f"     * Turno 2: RIGOROSAMENTE 3 opções de mitigação/continuidade (id: 'A', 'B', 'C') para CADA uma das 3 opções do turno 1 (totalizando 3 desfechos por ramo).\n"
                f"     * Desfecho com indicadores finais, veredito de trade-offs e is_success=True.\n\n"
                f"IMPORTANTE: Você DEVE responder exclusivamente com um objeto JSON válido seguindo rigorosamente esta estrutura (note que socratic_duel vem PRIMEIRO):\n"
                f"{schema_example}"
            )
            concept_hint = f" (Conceito central: {core_concept})" if core_concept else ""
            safe_content = (lesson_content or "").strip()
            user_prompt = f"Gere o Quiz completo (1 Duelo Socrático prioritário, 3 MCQ inéditas e 1 Mini-Simulador de Impacto em 2 Turnos pré-gerado com exatamente 3 opções no Turno 1 e 3 opções no Turno 2) para a aula '{lesson_title}'{concept_hint} com base neste texto:\n\n{safe_content[:1800]}"
        
        try:
            quiz = await LLMGateway.generate_structured(system_prompt, user_prompt, QuizSchema, max_tokens=1800, timeout=35)
            if not quiz or not getattr(quiz, "mcq", None) or len(quiz.mcq) < 2:
                fallback = QuizMasterAgent.build_fallback_quiz(lesson_title, core_concept, safe_content, language=language)
                if quiz:
                    if not getattr(quiz, "mcq", None):
                        quiz.mcq = fallback.mcq
                    if not getattr(quiz, "socratic_duel", None):
                        quiz.socratic_duel = fallback.socratic_duel
                    if not getattr(quiz, "simulation", None):
                        quiz.simulation = fallback.simulation
                else:
                    quiz = fallback
            return quiz
        except Exception as e:
            print(f"[QuizMasterAgent] Aviso: Gerador contextual ativado para a aula '{lesson_title}' devido a: {e}")
            return QuizMasterAgent.build_fallback_quiz(lesson_title, core_concept, safe_content, language=language)

    @staticmethod
    def build_fallback_quiz(lesson_title: str, core_concept: str = "", lesson_content: str = "", language: str = "pt-BR") -> QuizSchema:
        """Gera um quiz 100% estruturado, contextualizado e válido quando o modelo remoto não puder produzir o JSON integral."""
        is_en = language.lower().startswith("en")
        concept = (core_concept or lesson_title).strip()

        if is_en:
            socratic = SocraticDuelQuestion(
                dilemma_title=f"Practical Dilemma: {lesson_title}",
                question=(
                    f"When applying the foundational principles of '{lesson_title}' ({concept}), you encounter an operational trade-off between deployment velocity and sustainable delivery. "
                    f"Route A: Maintain a conservative and rigorous stance, ensuring maximum precision at the expense of short-term pace. "
                    f"Route B: Adopt flexible guidelines and dynamic adaptations to accelerate immediate results. "
                    f"Which path would you recommend to solve the challenge, and what strategic rationale would you defend based on the lesson?"
                ),
                evaluation_rubric=[
                    f"Demonstration of practical understanding and alignment with the core principle: {concept}",
                    "Lucid justification of operational trade-offs when facing the Cognitive Knot"
                ]
            )

            mcqs = [
                MultipleChoiceQuestion(
                    question=f"What is the primary objective explored in the study of '{lesson_title}'?",
                    options=[
                        MultipleChoiceOption(label="A", text=f"Understand the core mechanisms and practical applicability of {concept}.", is_correct=True),
                        MultipleChoiceOption(label="B", text="Replace established workflows without conducting any impact assessment.", is_correct=False),
                        MultipleChoiceOption(label="C", text="Confine learning to abstract definitions detached from real-world operations.", is_correct=False),
                    ],
                    explanation=f"The central purpose is to empower mastery and intuitive application of {concept}."
                ),
                MultipleChoiceQuestion(
                    question=f"When evaluating the outcomes of {concept}, which criterion ensures consistency across results?",
                    options=[
                        MultipleChoiceOption(label="A", text="Ignore contextual variables and apply one-size-fits-all generic formulas.", is_correct=False),
                        MultipleChoiceOption(label="B", text="A reasoned balance between conceptual rigor, risk mitigation, and practical efficacy.", is_correct=True),
                        MultipleChoiceOption(label="C", text="Postpone strategic decisions indefinitely due to risk aversion.", is_correct=False),
                    ],
                    explanation="Execution excellence relies on balancing technical rigor with sustainable delivery capacity."
                ),
                MultipleChoiceQuestion(
                    question=f"Which methodological mindset prevents common conceptual traps when handling {concept}?",
                    options=[
                        MultipleChoiceOption(label="A", text="Structured hypothesis validation and continuous system observability.", is_correct=True),
                        MultipleChoiceOption(label="B", text="Eliminating testing phases to prioritize raw delivery speed.", is_correct=False),
                        MultipleChoiceOption(label="C", text="Relying exclusively on unverified intuition without empirical backing.", is_correct=False),
                    ],
                    explanation="Resilient processes require progressive validation and empirical tracking of evidence."
                )
            ]

            simulation = SimulationSandbox(
                context=f"You are coordinating the operational implementation of '{lesson_title}'. Your team must balance execution quality, delivery pace, and operational stability.",
                initial_indicators=[
                    IndicatorState(name="Quality & Precision", value_type="percentage", value=75, color_hint="green"),
                    IndicatorState(name="Operational Efficiency", value_type="percentage", value=60, color_hint="yellow"),
                    IndicatorState(name="Risk Margin", value_type="percentage", value=35, color_hint="green")
                ],
                turn1_prompt=f"What is your priority strategic action to structure {concept}?",
                turn1_options=[
                    SimulationTurn1Option(
                        id="A",
                        text="Establish controlled validation protocols before expanding operational scope",
                        reaction_story="Systemic stability increased significantly, although initial velocity required adjustments.",
                        updated_indicators=[
                            IndicatorState(name="Quality & Precision", value_type="percentage", value=90, color_hint="green"),
                            IndicatorState(name="Operational Efficiency", value_type="percentage", value=55, color_hint="yellow"),
                            IndicatorState(name="Risk Margin", value_type="percentage", value=20, color_hint="green")
                        ],
                        turn2_prompt="How will you recover operational speed without compromising achieved standards?",
                        turn2_options=[
                            SimulationTurn2Option(
                                id="A",
                                text="Automate audit pipelines while preserving critical review checkpoints",
                                outcome_story="Throughput regained momentum with end-to-end traceability and operational safety.",
                                final_indicators=[
                                    IndicatorState(name="Quality & Precision", value_type="percentage", value=92, color_hint="green"),
                                    IndicatorState(name="Operational Efficiency", value_type="percentage", value=85, color_hint="green"),
                                    IndicatorState(name="Risk Margin", value_type="percentage", value=15, color_hint="green")
                                ],
                                verdict_summary="Simulation succeeded. Balanced operations with high maturity.",
                                is_success=True
                            ),
                            SimulationTurn2Option(
                                id="B",
                                text="Slash validation steps to accelerate delivery at all costs",
                                outcome_story="Unforeseen defects surfaced in the final stage, triggering costly rework.",
                                final_indicators=[
                                    IndicatorState(name="Quality & Precision", value_type="percentage", value=60, color_hint="yellow"),
                                    IndicatorState(name="Operational Efficiency", value_type="percentage", value=75, color_hint="yellow"),
                                    IndicatorState(name="Risk Margin", value_type="percentage", value=60, color_hint="yellow")
                                ],
                                verdict_summary="High-risk trade-off. Rushed shortcuts compromised process stability.",
                                is_success=False
                            ),
                            SimulationTurn2Option(
                                id="C",
                                text="Establish peer checkpoints with asynchronous review queues",
                                outcome_story="Steady pace achieved with collective validation and minimal bottlenecks.",
                                final_indicators=[
                                    IndicatorState(name="Quality & Precision", value_type="percentage", value=88, color_hint="green"),
                                    IndicatorState(name="Operational Efficiency", value_type="percentage", value=80, color_hint="green"),
                                    IndicatorState(name="Risk Margin", value_type="percentage", value=18, color_hint="green")
                                ],
                                verdict_summary="Pragmatic middle path. Sustainable velocity maintained.",
                                is_success=True
                            )
                        ]
                    ),
                    SimulationTurn1Option(
                        id="B",
                        text="Adopt an agile short-cycle strategy with continuous field validation",
                        reaction_story="Deliverables moved with agility, allowing swift adjustments based on real demand.",
                        updated_indicators=[
                            IndicatorState(name="Quality & Precision", value_type="percentage", value=80, color_hint="green"),
                            IndicatorState(name="Operational Efficiency", value_type="percentage", value=85, color_hint="green"),
                            IndicatorState(name="Risk Margin", value_type="percentage", value=25, color_hint="green")
                        ],
                        turn2_prompt="With initial traction established, which final adjustment secures sustainability?",
                        turn2_options=[
                            SimulationTurn2Option(
                                id="A",
                                text="Institute living documentation and progressive standardization of lessons learned",
                                outcome_story="Knowledge retention strengthened the entire ecosystem with durable outcomes.",
                                final_indicators=[
                                    IndicatorState(name="Quality & Precision", value_type="percentage", value=90, color_hint="green"),
                                    IndicatorState(name="Operational Efficiency", value_type="percentage", value=88, color_hint="green"),
                                    IndicatorState(name="Risk Margin", value_type="percentage", value=12, color_hint="green")
                                ],
                                verdict_summary="Exemplary execution. Virtuous cycle of learning and efficiency.",
                                is_success=True
                            ),
                            SimulationTurn2Option(
                                id="B",
                                text="Suspend formalization to maintain rapid unstructured momentum",
                                outcome_story="Knowledge became fragmented, increasing reliance on manual fire-fighting.",
                                final_indicators=[
                                    IndicatorState(name="Quality & Precision", value_type="percentage", value=70, color_hint="yellow"),
                                    IndicatorState(name="Operational Efficiency", value_type="percentage", value=80, color_hint="green"),
                                    IndicatorState(name="Risk Margin", value_type="percentage", value=45, color_hint="yellow")
                                ],
                                verdict_summary="Fragile growth due to lack of operational standardization.",
                                is_success=False
                            ),
                            SimulationTurn2Option(
                                id="C",
                                text="Automate telemetry dashboards to flag bottlenecks before they scale",
                                outcome_story="Telemetry gave total operational clarity, empowering teams to act early.",
                                final_indicators=[
                                    IndicatorState(name="Quality & Precision", value_type="percentage", value=86, color_hint="green"),
                                    IndicatorState(name="Operational Efficiency", value_type="percentage", value=90, color_hint="green"),
                                    IndicatorState(name="Risk Margin", value_type="percentage", value=16, color_hint="green")
                                ],
                                verdict_summary="Data-driven agility. Fast feedback loops ensured high reliability.",
                                is_success=True
                            )
                        ]
                    ),
                    SimulationTurn1Option(
                        id="C",
                        text="Execute progressive rollout with canary stages and real-time observability",
                        reaction_story="Controlled deployment prevented global incidents and identified performance variations early.",
                        updated_indicators=[
                            IndicatorState(name="Quality & Precision", value_type="percentage", value=85, color_hint="green"),
                            IndicatorState(name="Operational Efficiency", value_type="percentage", value=75, color_hint="green"),
                            IndicatorState(name="Risk Margin", value_type="percentage", value=20, color_hint="green")
                        ],
                        turn2_prompt="With the baseline verified, what is your next consolidation step?",
                        turn2_options=[
                            SimulationTurn2Option(
                                id="A",
                                text="Scale adoption gradually with automated regression guardrails",
                                outcome_story="Seamless scaling achieved with zero downtime and verified stability.",
                                final_indicators=[
                                    IndicatorState(name="Quality & Precision", value_type="percentage", value=94, color_hint="green"),
                                    IndicatorState(name="Operational Efficiency", value_type="percentage", value=92, color_hint="green"),
                                    IndicatorState(name="Risk Margin", value_type="percentage", value=10, color_hint="green")
                                ],
                                verdict_summary="Optimal execution. Resilient scaling model established.",
                                is_success=True
                            ),
                            SimulationTurn2Option(
                                id="B",
                                text="Force immediate 100% switch to bypass staged rollout overhead",
                                outcome_story="Sudden peak exposed uncalibrated secondary dependencies.",
                                final_indicators=[
                                    IndicatorState(name="Quality & Precision", value_type="percentage", value=65, color_hint="yellow"),
                                    IndicatorState(name="Operational Efficiency", value_type="percentage", value=70, color_hint="yellow"),
                                    IndicatorState(name="Risk Margin", value_type="percentage", value=55, color_hint="yellow")
                                ],
                                verdict_summary="Premature optimization compromised initial safety gains.",
                                is_success=False
                            ),
                            SimulationTurn2Option(
                                id="C",
                                text="Consolidate telemetry baselines and train key stakeholders before full rollout",
                                outcome_story="Broad organizational readiness ensured smooth, frictionless adoption.",
                                final_indicators=[
                                    IndicatorState(name="Quality & Precision", value_type="percentage", value=90, color_hint="green"),
                                    IndicatorState(name="Operational Efficiency", value_type="percentage", value=85, color_hint="green"),
                                    IndicatorState(name="Risk Margin", value_type="percentage", value=14, color_hint="green")
                                ],
                                verdict_summary="Sustainable scaling with high organizational buy-in.",
                                is_success=True
                            )
                        ]
                    )
                ]
            )
        else:
            # Socratic Duel
            socratic = SocraticDuelQuestion(
                dilemma_title=f"Dilema Prático: {lesson_title}",
                question=(
                    f"Ao aplicar os conceitos essenciais de '{lesson_title}' ({concept}), você se depara com um conflito operacional entre velocidade de implementação e sustentabilidade da entrega. "
                    f"Rota A: Manter uma postura rigorosa e conservadora, garantindo precisão em detrimento do ritmo imediato. "
                    f"Rota B: Flexibilizar as diretrizes e adotar soluções dinâmicas de curto prazo para acelerar os resultados. "
                    f"Qual caminho você recomendaria para solucionar o desafio e qual justificativa estratégica você defenderia?"
                ),
                evaluation_rubric=[
                    f"Demonstração de compreensão prática e alinhamento com a ideia central: {concept}",
                    "Fundamentação lúcida de trade-offs operacionais frente ao Nó Cognitivo"
                ]
            )

            # 3 Questões de Múltipla Escolha (MCQ)
            mcqs = [
                MultipleChoiceQuestion(
                    question=f"Qual é a finalidade primordial discutida no estudo de '{lesson_title}'?",
                    options=[
                        MultipleChoiceOption(label="A", text=f"Compreender os mecanismos de funcionamento e a aplicabilidade de {concept}.", is_correct=True),
                        MultipleChoiceOption(label="B", text="Substituir integralmente processos consolidados sem qualquer análise de impacto.", is_correct=False),
                        MultipleChoiceOption(label="C", text="Limitar o aprendizado a definições abstratas sem conexão com a realidade operacional.", is_correct=False),
                    ],
                    explanation=f"O propósito central da aula é capacitar o aluno no domínio prático e intuitivo de {concept}."
                ),
                MultipleChoiceQuestion(
                    question=f"Ao avaliar os desdobramentos de {concept}, qual critério assegura a consistência dos resultados?",
                    options=[
                        MultipleChoiceOption(label="A", text="Desconsiderar variáveis de contexto e aplicar fórmulas genéricas.", is_correct=False),
                        MultipleChoiceOption(label="B", text="Equilíbrio fundamentado entre rigor conceitual, mitigação de riscos e eficácia prática.", is_correct=True),
                        MultipleChoiceOption(label="C", text="Adiar decisões estratégicas indefinidamente por aversão à incerteza.", is_correct=False),
                    ],
                    explanation="A excelência na execução depende de equilibrar rigor técnico com capacidade de entrega sustentável."
                ),
                MultipleChoiceQuestion(
                    question=f"Qual postura metodológica previne armadilhas conceituais ao lidar com {concept}?",
                    options=[
                        MultipleChoiceOption(label="A", text="Validação estruturada de hipóteses e observabilidade contínua dos processos.", is_correct=True),
                        MultipleChoiceOption(label="B", text="Supressão de testes para priorizar velocidade de entrega.", is_correct=False),
                        MultipleChoiceOption(label="C", text="Dependência exclusiva de intuição sem sustentação em evidências tangíveis.", is_correct=False),
                    ],
                    explanation="Processos resilientes exigem validações progressivas e acompanhamento empírico de dados."
                )
            ]

            # Mini-Simulador de Impacto em 2 Turnos
            simulation = SimulationSandbox(
                context=f"Você está coordenando a operacionalização de '{lesson_title}'. A equipe precisa equilibrar qualidade da execução, ritmo de entrega e estabilidade operacional.",
                initial_indicators=[
                    IndicatorState(name="Qualidade & Precisão", value_type="percentage", value=75, color_hint="green"),
                    IndicatorState(name="Eficiência Operacional", value_type="percentage", value=60, color_hint="yellow"),
                    IndicatorState(name="Margem de Risco", value_type="percentage", value=35, color_hint="green")
                ],
                turn1_prompt=f"Qual é a sua ação estratégica prioritária para estruturar {concept}?",
                turn1_options=[
                    SimulationTurn1Option(
                        id="A",
                        text="Estabelecer protocolos controlados de validação antes de expandir o escopo",
                        reaction_story="A estabilidade da operação elevou-se expressivamente, embora a velocidade inicial tenha exigido ajustes.",
                        updated_indicators=[
                            IndicatorState(name="Qualidade & Precisão", value_type="percentage", value=90, color_hint="green"),
                            IndicatorState(name="Eficiência Operacional", value_type="percentage", value=55, color_hint="yellow"),
                            IndicatorState(name="Margem de Risco", value_type="percentage", value=20, color_hint="green")
                        ],
                        turn2_prompt="Como você recuperará o ritmo operacional sem comprometer o padrão de qualidade alcançado?",
                        turn2_options=[
                            SimulationTurn2Option(
                                id="A",
                                text="Automatizar fluxos de conferência e manter os checkpoints essenciais",
                                outcome_story="O fluxo readquiriu ritmo acelerado com total rastreabilidade e segurança operacional.",
                                final_indicators=[
                                    IndicatorState(name="Qualidade & Precisão", value_type="percentage", value=92, color_hint="green"),
                                    IndicatorState(name="Eficiência Operacional", value_type="percentage", value=85, color_hint="green"),
                                    IndicatorState(name="Margem de Risco", value_type="percentage", value=15, color_hint="green")
                                ],
                                verdict_summary="Simulação bem-sucedida. Operação balanceada com alta maturidade.",
                                is_success=True
                            ),
                            SimulationTurn2Option(
                                id="B",
                                text="Reduzir as validações para acelerar a qualquer custo",
                                outcome_story="Erros imprevistos surgiram na etapa final, gerando retrabalho expressivo.",
                                final_indicators=[
                                    IndicatorState(name="Qualidade & Precisão", value_type="percentage", value=60, color_hint="yellow"),
                                    IndicatorState(name="Eficiência Operacional", value_type="percentage", value=75, color_hint="yellow"),
                                    IndicatorState(name="Margem de Risco", value_type="percentage", value=60, color_hint="yellow")
                                ],
                                verdict_summary="Trade-off arriscado. A pressa comprometeu a estabilidade do processo.",
                                is_success=False
                            ),
                            SimulationTurn2Option(
                                id="C",
                                text="Implementar checkpoints por amostragem inteligente orientada a risco",
                                outcome_story="A amostragem manteve alta confiabilidade com ganho de velocidade perceptível.",
                                final_indicators=[
                                    IndicatorState(name="Qualidade & Precisão", value_type="percentage", value=88, color_hint="green"),
                                    IndicatorState(name="Eficiência Operacional", value_type="percentage", value=82, color_hint="green"),
                                    IndicatorState(name="Margem de Risco", value_type="percentage", value=18, color_hint="green")
                                ],
                                verdict_summary="Equilíbrio pragmático entre rigor de validação e velocidade de entrega.",
                                is_success=True
                            )
                        ]
                    ),
                    SimulationTurn1Option(
                        id="B",
                        text="Adotar estratégia ágil de ciclos curtos com validação contínua em campo",
                        reaction_story="As entregas fluíram com agilidade, permitindo adaptações rápidas conforme as demandas reais.",
                        updated_indicators=[
                            IndicatorState(name="Qualidade & Precisão", value_type="percentage", value=80, color_hint="green"),
                            IndicatorState(name="Eficiência Operacional", value_type="percentage", value=85, color_hint="green"),
                            IndicatorState(name="Margem de Risco", value_type="percentage", value=25, color_hint="green")
                        ],
                        turn2_prompt="Com a tração estabelecida, qual ajuste final consolida a sustentabilidade do modelo?",
                        turn2_options=[
                            SimulationTurn2Option(
                                id="A",
                                text="Instituir documentação viva e padronização progressiva das lições aprendidas",
                                outcome_story="A retenção do conhecimento fortaleceu todo o ecossistema com resultados perenes.",
                                final_indicators=[
                                    IndicatorState(name="Qualidade & Precisão", value_type="percentage", value=90, color_hint="green"),
                                    IndicatorState(name="Eficiência Operacional", value_type="percentage", value=88, color_hint="green"),
                                    IndicatorState(name="Margem de Risco", value_type="percentage", value=12, color_hint="green")
                                ],
                                verdict_summary="Execução exemplar. Ciclo virtuoso de aprendizado e eficiência.",
                                is_success=True
                            ),
                            SimulationTurn2Option(
                                id="B",
                                text="Suspender a formalização para manter ritmo acelerado sem processos",
                                outcome_story="O conhecimento ficou fragmentado e a dependência de intervenções manuais aumentou.",
                                final_indicators=[
                                    IndicatorState(name="Qualidade & Precisão", value_type="percentage", value=70, color_hint="yellow"),
                                    IndicatorState(name="Eficiência Operacional", value_type="percentage", value=80, color_hint="green"),
                                    IndicatorState(name="Margem de Risco", value_type="percentage", value=45, color_hint="yellow")
                                ],
                                verdict_summary="Crescimento com fragilidade estrutural pela falta de padronização.",
                                is_success=False
                            ),
                            SimulationTurn2Option(
                                id="C",
                                text="Desenvolver dashboards de observabilidade e métricas de desempenho em tempo real",
                                outcome_story="A visibilidade imediata permitiu prever gargalos e manter o ritmo com total controle.",
                                final_indicators=[
                                    IndicatorState(name="Qualidade & Precisão", value_type="percentage", value=86, color_hint="green"),
                                    IndicatorState(name="Eficiência Operacional", value_type="percentage", value=90, color_hint="green"),
                                    IndicatorState(name="Margem de Risco", value_type="percentage", value=16, color_hint="green")
                                ],
                                verdict_summary="Agilidade orientada por dados com alta previsibilidade operacional.",
                                is_success=True
                            )
                        ]
                    ),
                    SimulationTurn1Option(
                        id="C",
                        text="Executar rollout progressivo com fases canário e observabilidade contínua",
                        reaction_story="A distribuição por fases manteve os sistemas estáveis e mitigou imprevistos antes do impacto geral.",
                        updated_indicators=[
                            IndicatorState(name="Qualidade & Precisão", value_type="percentage", value=85, color_hint="green"),
                            IndicatorState(name="Eficiência Operacional", value_type="percentage", value=75, color_hint="green"),
                            IndicatorState(name="Margem de Risco", value_type="percentage", value=20, color_hint="green")
                        ],
                        turn2_prompt="Com a linha de base validada, qual é o próximo passo de consolidação?",
                        turn2_options=[
                            SimulationTurn2Option(
                                id="A",
                                text="Expandir a implantação progressivamente com testes automatizados de regressão",
                                outcome_story="A expansão foi concluída com alta integridade e estabilidade operacional comprovada.",
                                final_indicators=[
                                    IndicatorState(name="Qualidade & Precisão", value_type="percentage", value=95, color_hint="green"),
                                    IndicatorState(name="Eficiência Operacional", value_type="percentage", value=90, color_hint="green"),
                                    IndicatorState(name="Margem de Risco", value_type="percentage", value=10, color_hint="green")
                                ],
                                verdict_summary="Execução excelente. Arquitetura resiliente e escalabilidade segura.",
                                is_success=True
                            ),
                            SimulationTurn2Option(
                                id="B",
                                text="Acelerar a transição completa de uma vez só sem novas verificações",
                                outcome_story="A transição abrupta gerou sobrecarga nas estruturas secundárias não homologadas.",
                                final_indicators=[
                                    IndicatorState(name="Qualidade & Precisão", value_type="percentage", value=62, color_hint="yellow"),
                                    IndicatorState(name="Eficiência Operacional", value_type="percentage", value=68, color_hint="yellow"),
                                    IndicatorState(name="Margem de Risco", value_type="percentage", value=58, color_hint="yellow")
                                ],
                                verdict_summary="A pressa na reta final anulou os benefícios da implantação progressiva.",
                                is_success=False
                            ),
                            SimulationTurn2Option(
                                id="C",
                                text="Treinar equipes de ponta e disponibilizar canais de suporte antes da ativação plena",
                                outcome_story="O alinhamento dos operadores garantiu transição suave e rápida curva de adesão.",
                                final_indicators=[
                                    IndicatorState(name="Qualidade & Precisão", value_type="percentage", value=91, color_hint="green"),
                                    IndicatorState(name="Eficiência Operacional", value_type="percentage", value=86, color_hint="green"),
                                    IndicatorState(name="Margem de Risco", value_type="percentage", value=14, color_hint="green")
                                ],
                                verdict_summary="Prontidão operacional e cultural que garantiu sucesso sustentável.",
                                is_success=True
                            )
                        ]
                    )
                ]
            )

        return QuizSchema(
            mcq=mcqs,
            simulation=simulation,
            socratic_duel=socratic,
            discursive={"question": socratic.question, "evaluation_rubric": socratic.evaluation_rubric}
        )

class SummarizerAgent:
    @staticmethod
    async def summarize_lesson(lesson_title: str, lesson_content: str, language: str = "pt-BR") -> str:
        is_en = language.lower().startswith("en")
        safe_content = (lesson_content or "").strip()
        if is_en:
            system_prompt = (
                "You are the Knowledge Condenser of Trivium Academy.\n"
                "Your mission is to read the lesson and generate an ultra-concise summary of approximately 40 to 50 words in natural English, highlighting the fundamental concepts taught.\n"
                "ABSOLUTE RULE: Start DIRECTLY with the summary in English. Any preamble, word count commentary, or thinking aloud is strictly prohibited."
            )
            user_prompt = f"Summarize directly in English (40-50 words) the essential concepts of lesson '{lesson_title}':\n\n{safe_content[:1500]}"
        else:
            system_prompt = (
                "Você é o Condensador de Conhecimento da Trivium.\n"
                "Sua missão é ler a aula e gerar um resumo ultra-enxuto de aproximadamente 40 a 50 palavras em português brasileiro, destacando os conceitos fundamentais ensinados.\n"
                "REGRA ABSOLUTA: Comece DIRETAMENTE com o resumo em português. É TERMINANTEMENTE PROIBIDO qualquer preâmbulo em inglês ('We need...', 'The user wants...', 'Let\'s...'), anotações de contagem de palavras ou pensamento em voz alta."
            )
            user_prompt = f"Resuma diretamente em português (40-50 palavras) os conceitos essenciais da aula '{lesson_title}':\n\n{safe_content[:1500]}"
        try:
            summary = await LLMGateway.generate_text(system_prompt, user_prompt, max_tokens=180, timeout=25)
            # Remove qualquer vazamento de Chain-of-Thought
            if not is_en and re.match(r'^(?:we need|the user|i will|let\'s|here is|sure|need to|this lesson)\b', summary, flags=re.IGNORECASE):
                lines = [l.strip() for l in summary.split('\n') if l.strip()]
                valid_lines = [l for l in lines if not re.match(r'^(?:we need|the user|i will|let\'s|here is|sure|need to)\b', l, flags=re.IGNORECASE)]
                if valid_lines:
                    summary = " ".join(valid_lines)
                else:
                    clean_words = [w for w in safe_content.split() if not w.startswith("#")]
                    summary = " ".join(clean_words[:45]) + "..."
            return summary.strip()
        except Exception as e:
            print(f"[SummarizerAgent] Aviso: Fallback acionado para resumo da aula '{lesson_title}': {e}")
            clean_words = [w for w in safe_content.split() if not w.startswith("#")]
            return " ".join(clean_words[:45]) + "..."

class GraderAgent:
    @staticmethod
    async def evaluate_socratic_round1(
        lesson_title: str,
        question: str,
        rubric: list[str],
        student_answer: str,
        level: str = "Básico",
        language: str = "pt-BR"
    ) -> SocraticRound1Evaluation:
        """
        Avalia a tese inicial do aluno (Round 1). Se tiver substância e mérito,
        a IA não dá nota 10 imediatamente: contra-ataca com o 'Nó Cognitivo' (caso de borda extremo).
        """
        is_en = language.lower().startswith("en")
        rubric_str = "\n- ".join(rubric) if rubric else ("General comprehension of core concept" if is_en else "Compreensão geral da ideia central")

        if is_en:
            system_prompt = (
                f"You are a Socratic Master Debater of Trivium, intellectually sharp, empathetic, and welcoming.\n"
                f"You are conversing DIRECTLY with the student regarding lesson '{lesson_title}' (Level: {level}).\n"
                f"Original Dilemma: {question}\n"
                f"Reference Rubric:\n- {rubric_str}\n\n"
                f"DEBATE GUIDELINES (SOCRATIC DUEL - ROUND 1):\n"
                f"1. DIRECT SECOND-PERSON VOICE ('YOU'):\n"
                f"   - Always address the student as 'You' ('You accurately identified...', 'Your argument raises a key point...'). Strictly avoid third-person references ('The student').\n"
                f"2. INITIAL THESIS EVALUATION:\n"
                f"   - If the answer is completely incoherent or empty: set passed_round1=False, cognitive_knot=None and give warm guidance on what to review.\n"
                f"   - If the answer has practical merit (even if concise): set passed_round1=True.\n\n"
                f"3. FORMULATION OF THE 'COGNITIVE KNOT' (EXTREME EDGE CASE):\n"
                f"   - If passed_round1=True, DO NOT award final completion yet!\n"
                f"   - In 'feedback', give a brief, intelligent compliment to their thesis (1 sentence, 'You...').\n"
                f"   - In 'cognitive_knot', craft a realistic, tangible EXTREME EDGE CASE contextualized to their thesis in English:\n"
                f"     Example: 'Solid reasoning. But what if [deadlines are halved / operational constraints double unexpectedly], why would your initial path struggle and how would you adapt?'\n\n"
                f"Respond exclusively with a valid JSON containing: passed_round1 (bool), feedback (str), cognitive_knot (str or null)."
            )
            user_prompt = f"Student's thesis in Round 1:\n\"{student_answer}\""
        else:
            system_prompt = (
                f"Você é um Mestre Debatedor Socrático da Trivium, intelectualmente afiado, empático e acolhedor.\n"
                f"Você está dialogando DIRETAMENTE com o estudante sobre a aula '{lesson_title}' (Nível: {level}).\n"
                f"Dilema Original: {question}\n"
                f"Critérios de Referência:\n- {rubric_str}\n\n"
                f"DIRETRIZES DE ATUAÇÃO (DUELO SOCRÁTICO - ROUND 1):\n"
                f"1. VOZ DIRETA EM SEGUNDA PESSOA ('VOCÊ'):\n"
                f"   - Dirija-se sempre diretamente ao usuário usando 'Você' ('Você captou muito bem...', 'Sua reflexão traz um ponto importante...'). É TERMINANTEMENTE PROIBIDO falar em terceira pessoa ('O aluno').\n"
                f"2. AVALIAÇÃO DA TESE INICIAL:\n"
                f"   - Se a resposta for vazia, desconexa ou sem sentido: defina passed_round1=False, cognitive_knot=None e dê um feedback caloroso orientando o que rever na apostila.\n"
                f"   - Se a resposta tiver mérito prático (mesmo simples ou concisa): defina passed_round1=True.\n\n"
                f"3. FORMULAÇÃO DO 'NÓ COGNITIVO' (O CONTRA-ATAQUE COM CASO DE BORDA):\n"
                f"   - Se passed_round1=True, NÃO conceda aprovação definitiva agora!\n"
                f"   - No campo 'feedback', faça um elogio direto e inteligente à tese dele (1 frase, falando 'Você...').\n"
                f"   - No campo 'cognitive_knot', elabore um CASO DE BORDA EXTREMO (edge case) realista, compreensível e contextualizado à resposta dele:\n"
                f"     Exemplo: 'Boa colocação. Mas e se [o prazo cair pela metade / a complexidade dobrar / surgir uma restrição imprevista], por que essa sua abordagem inicial falharia e como você a adaptaria?'\n\n"
                f"Responda exclusivamente com um JSON contendo: passed_round1 (bool), feedback (str), cognitive_knot (str ou null)."
            )
            user_prompt = f"Tese do aluno no Round 1:\n\"{student_answer}\""
        from app.schemas.quiz import SocraticRound1Evaluation
        return await LLMGateway.generate_structured(system_prompt, user_prompt, SocraticRound1Evaluation, max_tokens=600, timeout=40)

    @staticmethod
    async def evaluate_socratic_round2(
        lesson_title: str,
        question: str,
        student_answer_round1: str,
        cognitive_knot: str,
        student_answer_round2: str,
        level: str = "Básico",
        language: str = "pt-BR"
    ) -> SocraticRound2Evaluation:
        """
        Avalia a réplica do aluno frente ao Nó Cognitivo (Round 2) e concede a aprovação final com a melhor solução pedagógica.
        """
        is_en = language.lower().startswith("en")
        if is_en:
            system_prompt = (
                f"You are the Socratic Master Debater of Trivium evaluating the conclusion of the Socratic Duel with the student.\n"
                f"Lesson: {lesson_title} (Level: {level})\n"
                f"Initial Dilemma: {question}\n"
                f"Student's Thesis (Round 1): \"{student_answer_round1}\"\n"
                f"Cognitive Knot Presented (Round 2): \"{cognitive_knot}\"\n\n"
                f"FINAL JUDGMENT GUIDELINES (ROUND 2):\n"
                f"1. DIRECT SECOND-PERSON VOICE ('YOU'):\n"
                f"   - Speak DIRECTLY to the student ('You demonstrated...', 'Your strategy addressed...'). Strictly forbidden to speak in third person ('The student').\n"
                f"2. MANDATORY 3-PART FEEDBACK STRUCTURE:\n"
                f"   - Part 1 (Empathetic Recognition): Enthusiastically acknowledge the strong point or practical intent of their response.\n"
                f"   - Part 2 (The Recommended Strategy and the Why): CLEARLY state what the best operational strategy would be for that extreme cognitive knot and explain WHY with didactic clarity based on the lesson.\n"
                f"   - Part 3 (Encouraging Conclusion): A closing sentence commending their intellectual maturity.\n"
                f"3. FORMATIVE AND GENEROUS EVALUATION:\n"
                f"   - If the student engaged with intellectual honesty and common sense, APPROVE WITH HONORS (passed=True, score 8 to 10).\n\n"
                f"Respond exclusively with a JSON containing: passed (bool), score (int 0 to 10), feedback (str in English)."
            )
            user_prompt = f"Student's reply to the Cognitive Knot in Round 2:\n\"{student_answer_round2}\""
        else:
            system_prompt = (
                f"Você é o Mestre Debatedor Socrático da Trivium avaliando a conclusão do Duelo Socrático com o estudante.\n"
                f"Aula: {lesson_title} (Nível: {level})\n"
                f"Dilema Inicial: {question}\n"
                f"Tese do Aluno (Round 1): \"{student_answer_round1}\"\n"
                f"Nó Cognitivo Apresentado (Round 2): \"{cognitive_knot}\"\n\n"
                f"DIRETRIZES DE JULGAMENTO FINAL (ROUND 2):\n"
                f"1. VOZ DIRETA EM SEGUNDA PESSOA ('VOCÊ'):\n"
                f"   - Fale DIRETAMENTE com o estudante ('Você demonstrou...', 'Sua estratégia buscou...', 'Você percebeu que...'). É EXPRESSAMENTE PROIBIDO falar na terceira pessoa ('O aluno demonstrou...').\n"
                f"2. ESTRUTURA OBRIGATÓRIA DO FEEDBACK (3 PARTES CLARAS):\n"
                f"   - Parte 1 (Reconhecimento Empático): Reconheça com entusiasmo o ponto forte ou a intenção prática da resposta dele.\n"
                f"   - Parte 2 (A Solução Mais Recomendada e o Porquê): Indique CLARAMENTE qual seria a melhor solução ou conduta estratégica para responder àquele nó cognitivo extremo e explique com clareza o PORQUÊ detalhado dessa abordagem (ex: 'Nesse cenário adverso, a melhor saída estratégica seria [solução], porque [justificativa clara e didática baseada na aula]').\n"
                f"   - Parte 3 (Conclusão Encorajadora): Uma frase de fechamento valorizando a maturidade e o raciocínio dele.\n"
                f"3. AVALIAÇÃO FORMATIVA E GENEROSA:\n"
                f"   - Se o estudante enfrentou o desafio com honestidade intelectual e bom senso, APROVE COM LOUVOR (passed=True, score entre 8 e 10). O objetivo é formar e ensinar a melhor estratégia, nunca punir com tom punitivo.\n\n"
                f"Responda exclusivamente com um JSON contendo: passed (bool), score (int 0 a 10), feedback (str)."
            )
            user_prompt = f"Réplica do aluno ao Nó Cognitivo no Round 2:\n\"{student_answer_round2}\""
        from app.schemas.quiz import SocraticRound2Evaluation
        return await LLMGateway.generate_structured(system_prompt, user_prompt, SocraticRound2Evaluation, max_tokens=600, timeout=40)

    @staticmethod
    async def evaluate_discursive(
        lesson_title: str,
        question: str,
        rubric: list[str],
        student_answer: str,
        level: str = "Básico",
        language: str = "pt-BR"
    ) -> GraderEvaluation:
        """Mantido para compatibilidade retroativa com aulas legadas"""
        is_en = language.lower().startswith("en")
        rubric_str = "\n- ".join(rubric) if rubric else ("General comprehension of core concept" if is_en else "Compreensao geral da ideia central da aula")
        if is_en:
            system_prompt = (
                f"You are an empathetic, encouraging, and intelligent Mentor Professor of Trivium.\n"
                f"Your mission is to evaluate a student's answer at the '{level}' level in English.\n"
                f"Lesson: {lesson_title}\n"
                f"Question: {question}\n"
                f"Reference Criteria (Rubric):\n{rubric_str}\n\n"
                f"EVALUATION GUIDELINES:\n"
                f"1. If the student grasped the intuitive idea, APPROVE (passed=True, score 8 to 10).\n"
                f"2. feedback: 2 to 3 warm sentences in English.\n"
                f"Return exclusively a JSON with: passed (bool), score (int 0 to 10), feedback (str)."
            )
        else:
            system_prompt = (
                f"Você é um Professor Mentor empático, encorajador e inteligente da Trivium.\n"
                f"Sua missão é avaliar a resposta discursiva de um aluno no nível '{level}'.\n"
                f"Aula: {lesson_title}\n"
                f"Pergunta: {question}\n"
                f"Critérios de Referência (Rubrica):\n{rubric_str}\n\n"
                f"DIRETRIZES DE AVALIAÇÃO:\n"
                f"1. Se o aluno captou a ideia intuitiva, APROVE (passed=True, score 8 a 10).\n"
                f"2. feedback: 2 a 3 frases calorosas.\n"
                f"Retorne exclusivamente um JSON com: passed (bool), score (int 0 a 10), feedback (str)."
            )
        user_prompt = f"Student answer:\n\"{student_answer}\"" if is_en else f"Resposta do aluno:\n\"{student_answer}\""
        return await LLMGateway.generate_structured(system_prompt, user_prompt, GraderEvaluation, max_tokens=500, timeout=40)
