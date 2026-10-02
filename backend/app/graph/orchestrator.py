import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import asyncio
import time
import json
import re
from datetime import datetime, timezone
from sqlmodel import Session, select
from app.database import engine
from app.models.entities import Course, Module, Lesson, GenerationJob
from app.agents.pipeline import CuratorAgent, WriterAgent, QuizMasterAgent, SummarizerAgent, ResearcherAgent
from app.services.domain_classifier import DomainClassifier

LEVEL_SPECS = {
    "Teste": {"modules": 1, "lessons_per_module": 2, "words": 400},
    "Básico": {"modules": 4, "lessons_per_module": 3, "words": 650},
    "Intermediário": {"modules": 8, "lessons_per_module": 4, "words": 850},
    "Avançado": {"modules": 12, "lessons_per_module": 5, "words": 1100},
}

class CourseOrchestrator:
    job_timings = {}

    @staticmethod
    async def _bg_generate_course_cover(c_id: int, subject: str, visual_archetype: str):
        """
        Gera a imagem de capa exclusiva do curso em background e vincula ao Course.cover_image_url.
        """
        try:
            from app.services.stipple_image_service import StippleImageService
            cover_url = await StippleImageService.generate_course_cover_image(subject, visual_archetype, course_id=c_id)
            if cover_url:
                with Session(engine) as session:
                    c = session.get(Course, c_id)
                    if c:
                        c.cover_image_url = cover_url
                        session.add(c)
                        session.commit()
                print(f"[Orchestrator] Capa exclusiva do curso {c_id} salva com sucesso: {cover_url}")
        except Exception as e:
            print(f"[Orchestrator] Aviso na geração da capa do curso {c_id}: {e}")

    @staticmethod
    async def _bg_enrich_lesson_images(l_id: int, content_md: str, quiz_obj, l_title: str):
        """
        Gera ilustrações em segundo plano sem bloquear a esteira principal de geração de conteúdo pedagógico.
        Atualiza atomicamente a Lesson assim que as imagens estiverem salvas em disco.
        """
        try:
            from app.services.stipple_image_service import StippleImageService
            enriched_md = await StippleImageService.enrich_lesson_with_stipple(content_md, lesson_id=l_id)
            
            if quiz_obj and quiz_obj.socratic_duel and quiz_obj.socratic_duel.question:
                case_prompt_text = f"{l_title} - {quiz_obj.socratic_duel.dilemma_title or ''}: {quiz_obj.socratic_duel.question[:120]}"
                case_img_url = await StippleImageService.generate_case_study_image(case_prompt_text, lesson_id=l_id)
                if case_img_url:
                    quiz_obj.socratic_duel.image_url = case_img_url
                    quiz_obj.socratic_duel.image_caption = f"Artefato conceitual representativo do desafio prático: {l_title}"

            with Session(engine) as session:
                lesson_obj = session.get(Lesson, l_id)
                if lesson_obj:
                    if enriched_md:
                        lesson_obj.content_markdown = enriched_md
                    if quiz_obj:
                        lesson_obj.quiz_json = json.dumps(quiz_obj.model_dump(), ensure_ascii=False)
                    session.add(lesson_obj)
                    session.commit()
        except Exception as e:
            print(f"[Orchestrator] Aviso na geração de imagens em background da aula {l_id}: {e}")

    @staticmethod
    async def run_pipeline(
        job_id: str, 
        subject: str, 
        level: str, 
        language: str = "pt-BR",
        source_type: str = "web",
        book_filename: str = None,
        book_pages: int = None,
        chapter_chunks: list = None
    ):
        specs = LEVEL_SPECS.get(level, LEVEL_SPECS["Básico"])
        num_modules = specs["modules"]
        lessons_per_module = specs["lessons_per_module"]
        target_words = specs["words"]
        total_lessons = num_modules * lessons_per_module
        CourseOrchestrator.job_timings[job_id] = {"t_start": time.time(), "t_post_research": None, "t_finish": None, "post_research_seconds": 0.0}

        def update_job(pct: int, step: str, status: str = "processing", error: str = None, course_id: int = None):
            with Session(engine) as session:
                job = session.get(GenerationJob, job_id)
                if job:
                    job.progress_pct = pct
                    job.current_step = step
                    job.status = status
                    job.updated_at = datetime.now(timezone.utc)
                    if error:
                        job.error_message = error
                    if course_id:
                        job.course_id = course_id
                    session.add(job)
                    session.commit()

        try:
            update_job(2, f"Classificando a natureza epistemológica de '{subject}'...")
            domain_profile = await DomainClassifier.classify(subject, level)
            print(f"[Orchestrator] Domínio: {domain_profile.get('dynamic_domain_name')} | Persona: {domain_profile.get('persona_title')}")

            evidence_ledger = {}
            if source_type == "document" and chapter_chunks:
                update_job(4, f"Consolidando dossiê literário a partir de 100% dos capítulos do livro...")
                # Constrói dossiê literário a partir dos capítulos reais
                dossier_lines = [f"LIVRO-FONTE: {book_filename or subject} ({book_pages or len(chapter_chunks)*10} páginas)"]
                sources_metadata = [{
                    "title": book_filename or subject,
                    "author": domain_profile.get("persona_title", "Autor da Obra"),
                    "domain": "Arquivo Local (PDF/EPUB)",
                    "url": "",
                    "description": f"Obra original com {len(chapter_chunks)} capítulos/seções indexados integralmente."
                }]
                for ch in chapter_chunks:
                    dossier_lines.append(f"\n### [Capítulo {ch.get('chapter_index', 1)}: {ch.get('title', '')}]")
                    # Inclui as primeiras 300 palavras de cada capítulo no dossiê macro
                    words = ch.get('text_content', '').split()[:250]
                    dossier_lines.append(" ".join(words))
                course_dossier = "\n".join(dossier_lines)
            else:
                update_job(4, f"Minerando livros no Internet Archive e checando fatos na web...")
                research_result = await ResearcherAgent.build_research_dossier(subject, domain_profile=domain_profile, language=language)
                if len(research_result) == 3:
                    course_dossier, sources_metadata, evidence_ledger = research_result
                else:
                    course_dossier, sources_metadata = research_result[0], research_result[1]
                    evidence_ledger = {}

            t_post_research = time.time()
            CourseOrchestrator.job_timings[job_id]["t_post_research"] = t_post_research
            print(f"[Orchestrator] Pesquisa concluída em {datetime.now(timezone.utc).isoformat()}. Iniciando cronômetro estrito de geração (SLA: <= 6 min)...", flush=True)

            update_job(8, f"Construindo a Matriz Curricular ({num_modules} módulos)...")
            try:
                curriculum = await CuratorAgent.plan_curriculum(
                    subject, level, num_modules, lessons_per_module,
                    fact_dossier=course_dossier,
                    domain_profile=domain_profile,
                    language=language
                )
            except Exception as cur_err:
                err_str = str(cur_err).lower()
                if "free-models-per-day" in err_str or "free_tier_daily" in err_str or "high-balance" in err_str:
                    quota_msg = "Cota diária de modelos gratuitos atingida no OpenRouter (1.000 requisições/dia). O limite é renovado às 00:00 UTC."
                    print(f"[Orchestrator] {quota_msg}")
                    update_job(0, "Cota diária atingida", status="failed", error=quota_msg)
                    raise RuntimeError(quota_msg)
                raise cur_err

            # Persiste esqueleto inicial no banco incluindo dossiê e fontes verificadas
            with Session(engine) as session:
                course = Course(
                    subject=subject,
                    level=level,
                    language=language,
                    research_dossier=course_dossier,
                    sources_json=json.dumps(sources_metadata, ensure_ascii=False) if sources_metadata else None,
                    source_type=source_type,
                    source_book_filename=book_filename,
                    source_book_pages=book_pages
                )
                session.add(course)
                session.commit()
                session.refresh(course)
                course_id = course.id

                created_modules = []
                for mod_data in curriculum.modules:
                    mod = Module(
                        course_id=course_id,
                        module_number=mod_data.module_number,
                        title=mod_data.title,
                        is_unlocked=(mod_data.module_number == 1)
                    )
                    session.add(mod)
                    session.commit()
                    session.refresh(mod)

                    for l_idx, l_data in enumerate(mod_data.lessons, start=1):
                        lesson = Lesson(
                            module_id=mod.id,
                            lesson_number=l_idx,
                            title=l_data.title,
                            core_concept=l_data.core_concept,
                            status="in_progress" if (mod.module_number == 1 and l_idx == 1) else "locked"
                        )
                        session.add(lesson)
                    session.commit()
            
            # Dispara geração da capa única do curso em background (não bloqueia a esteira de aulas)
            visual_arch = domain_profile.get("visual_archetype", "editorial technical engraving")
            asyncio.create_task(CourseOrchestrator._bg_generate_course_cover(course_id, subject, visual_arch))

            update_job(15, "Matriz gerada. Iniciando esteira de producao de aulas...", course_id=course_id)

            lesson_summaries = []
            used_case_studies = []
            accumulated_questions = []
            completed_count = 0

            # Carrega IDs de modulos e aulas sem travar transacao aberta
            with Session(engine) as session:
                modules = session.exec(select(Module).where(Module.course_id == course_id).order_by(Module.module_number)).all()
                module_items = []
                for mod in modules:
                    lessons = session.exec(select(Lesson).where(Lesson.module_id == mod.id).order_by(Lesson.lesson_number)).all()
                    for l in lessons:
                        module_items.append((mod.module_number, mod.title, l.id, l.lesson_number, l.title, l.core_concept))

            all_lesson_items = module_items

            # Semáforo de controle de taxa/concorrência adaptativa (VRAM Shield para modelos locais vs Nuvem)
            from app.services.settings_service import SettingsService
            active_provider = SettingsService.get_settings().get("llm_provider", "openrouter").lower()
            max_concurrent_lessons = 1 if active_provider in ["local", "ollama"] else 2
            sem = asyncio.Semaphore(max_concurrent_lessons)
            progress_lock = asyncio.Lock()

            # Coleta de tarefas de imagens para sincronização
            enrich_tasks = []

            async def generate_single_lesson(item):
                nonlocal completed_count
                mod_num, mod_title, l_id, l_num, l_title, l_concept = item
                async with sem:
                    # Se for curso de documento/livro, injeta a seção e texto autêntico do capítulo correspondente
                    lesson_specific_dossier = course_dossier
                    if source_type == "document" and chapter_chunks:
                        lesson_global_idx = (mod_num - 1) * lessons_per_module + (l_num - 1)
                        total_target_lessons = max(1, total_lessons)
                        ch_idx = min(int(lesson_global_idx * len(chapter_chunks) / total_target_lessons), len(chapter_chunks) - 1)
                        target_ch = chapter_chunks[ch_idx]
                        ch_text = target_ch.get("text_content", "")[:12000]
                        lesson_specific_dossier = (
                            f"LIVRO-FONTE: {book_filename or subject}\n"
                            f"CAPÍTULO / SEÇÃO DO LIVRO: {target_ch.get('title', f'Capítulo {ch_idx+1}')}\n"
                            f"PÁGINAS ESTIMADAS: {target_ch.get('page_start', 1)} a {target_ch.get('page_end', target_ch.get('page_start', 1))}\n\n"
                            f"--- CONTEÚDO INTEGRAL DESTE CAPÍTULO (FONTE PRIMÁRIA) ---\n"
                            f"{ch_text}\n\n"
                            f"--- DIRETRIZES DE FIDELIDADE AO LIVRO ---\n"
                            f"1. Você DEVE obrigatoriamente explorar os termos exatos, metáforas originais, estudos de caso e conceitos formulados pelo autor neste capítulo.\n"
                            f"2. Capture as entrelinhas e as advertências do autor sobre equívocos comuns.\n"
                        )

                    # 1. Redação Integral da Apostila com Retry Fail-Safe e Scorecard de Qualidade
                    content_md = None
                    min_words = 400 if level in ["Teste", "Básico"] else (650 if level == "Intermediário" else 900)

                    for attempt in range(3):
                        try:
                            content_md = await WriterAgent.write_lesson(
                                subject=subject,
                                level=level,
                                module_num=mod_num,
                                module_title=mod_title,
                                lesson_num=l_num,
                                lesson_title=l_title,
                                core_concept=l_concept,
                                target_words=target_words,
                                previous_summaries=list(lesson_summaries),
                                fact_dossier=lesson_specific_dossier,
                                used_case_studies=list(used_case_studies),
                                domain_profile=domain_profile,
                                evidence_ledger=evidence_ledger,
                                sources_metadata=sources_metadata,
                                language=language
                            )
                        except Exception as write_err:
                            err_str = str(write_err).lower()
                            if "free-models-per-day" in err_str or "free_tier_daily" in err_str or "high-balance" in err_str:
                                quota_msg = "Cota diária de modelos gratuitos atingida no OpenRouter (1.000 requisições/dia). O limite é renovado às 00:00 UTC."
                                print(f"[Orchestrator] {quota_msg}")
                                update_job(0, "Cota diária atingida", status="failed", error=quota_msg)
                                raise RuntimeError(quota_msg)
                            if attempt == 2:
                                error_msg = f"Falha na redação da aula '{l_title}' via IA: {write_err}. Verifique seus modelos no menu de Configurações."
                                print(f"[Orchestrator] {error_msg}")
                                raise RuntimeError(error_msg)
                            await asyncio.sleep(2)
                            continue

                        # Scorecard de Qualidade e Autovalidação
                        if content_md:
                            words_count = len(content_md.split())
                            # Validação de comprimento
                            if words_count < min_words:
                                print(f"[Orchestrator] Aula '{l_title}' veio curta ({words_count} palavras < {min_words}). Refazendo tentativa {attempt+1}/3...")
                                await asyncio.sleep(2)
                                continue

                            # Validação e autocura de KaTeX desbalanceado
                            clean_math = content_md.replace(r"\$", "")
                            single_dollars = len(re.findall(r"(?<!\$)\$(?!\$)", clean_math))
                            if single_dollars % 2 != 0:
                                # Autocura: fecha delimitador solto no final de linha de fórmula
                                content_md = re.sub(r'(\$[^\$\n]+)$', r'\1$', content_md, flags=re.MULTILINE)

                            break
                        else:
                            await asyncio.sleep(2)

                    if not content_md or len(content_md.strip()) < 800:
                        raise RuntimeError(f"A IA retornou conteúdo insuficiente ou truncado ({len(content_md.strip()) if content_md else 0} caracteres) para a aula '{l_title}' após 3 tentativas.")

                    # PERSISTÊNCIA IMEDIATA DO TEXTO DA AULA NO BANCO DE DADOS (Fail-Safe Absoluto)
                    with Session(engine) as session:
                        lesson_obj = session.get(Lesson, l_id)
                        if lesson_obj:
                            lesson_obj.content_markdown = content_md
                            session.add(lesson_obj)
                            session.commit()

                    # 2. Execução Paralela: Quiz Master + Summarizer (Concorrência Intra-Aula)
                    async def fetch_quiz():
                        try:
                            return await QuizMasterAgent.generate_quiz(
                                lesson_title=l_title,
                                lesson_content=content_md,
                                level=level,
                                previous_questions=list(accumulated_questions),
                                core_concept=l_concept,
                                domain_profile=domain_profile,
                                language=language
                            )
                        except Exception as quiz_err:
                            print(f"[Orchestrator] Aviso no quiz da aula {l_id}: {quiz_err}. Acionando construtor resiliente.")
                            return None

                    async def fetch_summary():
                        try:
                            return await SummarizerAgent.summarize_lesson(l_title, content_md, language=language)
                        except Exception as sum_err:
                            words = [w for w in content_md.split() if not w.startswith("#")]
                            return " ".join(words[:40]) + "..."

                    quiz, summary = await asyncio.gather(fetch_quiz(), fetch_summary())

                    if not quiz:
                        try:
                            quiz = QuizMasterAgent.build_fallback_quiz(l_title, l_concept, content_md, language=language)
                        except Exception as fb_err:
                            print(f"[Orchestrator] Falha no construtor de fallback do quiz: {fb_err}")
                            from app.schemas.quiz import QuizSchema
                            quiz = QuizSchema()

                    # Persistência atômica da aula finalizada (conteúdo textual, quiz e resumo)
                    with Session(engine) as session:
                        lesson_obj = session.get(Lesson, l_id)
                        if lesson_obj:
                            lesson_obj.content_markdown = content_md
                            if quiz:
                                lesson_obj.quiz_json = json.dumps(quiz.model_dump(), ensure_ascii=False)
                            lesson_obj.summary_50_words = summary
                            session.add(lesson_obj)
                            session.commit()

                    # Agenda enriquecimento de ilustrações das aulas
                    img_task = asyncio.create_task(CourseOrchestrator._bg_enrich_lesson_images(l_id, content_md, quiz, l_title))
                    enrich_tasks.append(img_task)

                    async with progress_lock:
                        completed_count += 1
                        lesson_summaries.append(f"{l_title}: {summary}")
                        used_case_studies.append(f"Módulo {mod_num} - Aula {l_num}: '{l_title}' ({l_concept})")
                        if quiz and quiz.mcq:
                            for q in quiz.mcq:
                                if q.question:
                                    accumulated_questions.append(q.question)
                        if quiz and quiz.socratic_duel and quiz.socratic_duel.question:
                            accumulated_questions.append(quiz.socratic_duel.question)

                        pct = 15 + int((completed_count / total_lessons) * 80)
                        update_job(pct, f"Progresso: {completed_count}/{total_lessons} aulas concluídas (Módulo {mod_num} - '{l_title}')...")

            tasks = [generate_single_lesson(item) for item in all_lesson_items]
            await asyncio.gather(*tasks)

            # Aguarda a finalização e gravação de todas as ilustrações das aulas
            if enrich_tasks:
                update_job(96, "Finalizando renderização de gravuras e ilustrações didáticas...")
                await asyncio.gather(*enrich_tasks, return_exceptions=True)

            # Finalizacao
            with Session(engine) as session:
                c = session.get(Course, course_id)
                if c:
                    c.is_completed = True
                    session.add(c)
                    session.commit()

            update_job(100, "Curso 100% produzido e liberado!", status="completed", course_id=course_id)
            t_post_research_elapsed = time.time() - t_post_research
            CourseOrchestrator.job_timings[job_id]["t_finish"] = time.time()
            CourseOrchestrator.job_timings[job_id]["post_research_seconds"] = t_post_research_elapsed
            print(f"[Orchestrator] Job {job_id} concluído com sucesso! Tempo pós-pesquisa: {t_post_research_elapsed:.2f}s ({t_post_research_elapsed/60:.2f} min)!", flush=True)

        except Exception as e:
            print(f"[Orchestrator] Erro no pipeline do Job {job_id}: {e}")
            update_job(0, f"Falha na esteira: {str(e)}", status="failed", error=str(e))

