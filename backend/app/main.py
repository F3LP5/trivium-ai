import os
import uuid
import json
import shutil
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, BackgroundTasks, HTTPException, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlmodel import Session, select, delete
from pydantic import BaseModel

from app.database import init_db, get_session, engine
from app.models.entities import Course, Module, Lesson, GenerationJob, LessonChatMessage
from app.graph.orchestrator import CourseOrchestrator
from app.agents.pipeline import GraderAgent, normalize_level
from app.services.tutor_service import TutorService
from app.services.document_extractor import (
    extract_from_pdf, extract_from_epub, build_chapter_chunks, clean_book_title_from_filename
)
from app.services.cognitive_analyzer import analyze_document_cognition

app = FastAPI(title="Trivium API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.services.settings_service import SettingsService

IMAGES_DIR = Path(__file__).resolve().parent.parent / "storage" / "images"
IMAGES_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/api/images", StaticFiles(directory=str(IMAGES_DIR)), name="images")

DOCS_CACHE_DIR = Path(__file__).resolve().parent.parent / "storage" / "documents"
DOCS_CACHE_DIR.mkdir(parents=True, exist_ok=True)
UPLOADS_DIR = Path(__file__).resolve().parent.parent / "storage" / "uploads"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

@app.on_event("startup")
def on_startup():
    init_db()

class SettingsUpdateRequest(BaseModel):
    image_provider: Optional[str] = None
    image_aspect_ratio: Optional[str] = None
    image_quality: Optional[str] = None
    image_model: Optional[str] = None
    fal_api_key: Optional[str] = None
    hf_token: Optional[str] = None
    gemini_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    openrouter_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    llm_provider: Optional[str] = None
    openai_models: Optional[str] = None
    anthropic_models: Optional[str] = None
    openai_model: Optional[str] = None
    anthropic_model: Optional[str] = None
    openrouter_models: Optional[str] = None
    local_base_url: Optional[str] = None
    local_models: Optional[str] = None
    local_api_key: Optional[str] = None

class LocalConnectionTestRequest(BaseModel):
    base_url: Optional[str] = None
    api_key: Optional[str] = None

@app.get("/api/settings")
def get_settings():
    return SettingsService.get_public_settings()

@app.post("/api/settings")
def update_settings(req: SettingsUpdateRequest):
    updates = req.model_dump(exclude_unset=True)
    allowed_empty_or_preserved = {
        "image_provider", "image_model", "llm_provider", "openai_models", "anthropic_models",
        "openai_model", "anthropic_model", "image_aspect_ratio", "image_quality", "openrouter_models",
        "local_base_url", "local_models", "local_api_key"
    }
    clean_updates = {
        k: v for k, v in updates.items() 
        if v is not None and (v != "" or k in allowed_empty_or_preserved)
    }
    return SettingsService.update_settings(clean_updates)

@app.post("/api/settings/test-local-connection")
async def test_local_connection(req: Optional[LocalConnectionTestRequest] = None):
    import time
    import urllib.request
    from urllib.error import URLError

    current_settings = SettingsService.get_settings()
    base_url = (req.base_url if req and req.base_url else current_settings.get("local_base_url")) or "http://localhost:11434/v1"
    clean_url = base_url.strip().rstrip("/")
    if not clean_url.endswith("/v1"):
        clean_url = f"{clean_url}/v1"

    root_url = clean_url[:-3] if clean_url.endswith("/v1") else clean_url

    headers = {"User-Agent": "Trivium/1.0"}
    api_key = (req.api_key if req and req.api_key else current_settings.get("local_api_key")) or "ollama"
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    t0 = time.time()
    models = []
    provider_detected = "generic"
    if "11434" in clean_url:
        provider_detected = "ollama"
    elif "1234" in clean_url:
        provider_detected = "lm_studio"
    elif "8000" in clean_url:
        provider_detected = "vllm"

    # Tentativa 1: Endpoint padronizado OpenAI /v1/models
    try:
        req_obj = urllib.request.Request(f"{clean_url}/models", headers=headers)
        with urllib.request.urlopen(req_obj, timeout=4.0) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if isinstance(data, dict) and "data" in data and isinstance(data["data"], list):
                models = [m["id"] for m in data["data"] if isinstance(m, dict) and "id" in m]
            elif isinstance(data, list):
                models = [m.get("id") or m.get("name") for m in data if isinstance(m, dict)]
            
            latency_ms = max(1, round((time.time() - t0) * 1000))
            return {
                "online": True,
                "provider_detected": provider_detected,
                "base_url": clean_url,
                "models": models,
                "latency_ms": latency_ms
            }
    except Exception:
        pass

    # Tentativa 2: Endpoint nativo Ollama /api/tags
    try:
        req_tags = urllib.request.Request(f"{root_url}/api/tags", headers={"User-Agent": "Trivium/1.0"})
        with urllib.request.urlopen(req_tags, timeout=4.0) as resp:
            tags_data = json.loads(resp.read().decode("utf-8"))
            if isinstance(tags_data, dict) and "models" in tags_data:
                models = [m["name"] for m in tags_data["models"] if isinstance(m, dict) and "name" in m]
            latency_ms = max(1, round((time.time() - t0) * 1000))
            return {
                "online": True,
                "provider_detected": "ollama",
                "base_url": clean_url,
                "models": models,
                "latency_ms": latency_ms
            }
    except Exception:
        pass

    return {
        "online": False,
        "provider_detected": "offline",
        "base_url": clean_url,
        "models": [],
        "latency_ms": 0,
        "error": "Servidor local inacessível",
        "message": f"Não foi possível conectar ao servidor em {clean_url}. Verifique se o Ollama, LM Studio ou vLLM está em execução ('ollama serve')."
    }

@app.post("/api/settings/benchmark-free-models")
async def benchmark_free_models():
    try:
        from app.services.llm_gateway import LLMGateway
        return await LLMGateway.benchmark_free_models()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class CourseCreateRequest(BaseModel):
    subject: str
    level: str = "Básico" # Básico, Intermediário, Avançado
    language: str = "pt-BR" # pt-BR, en-US

class SimulationSubmitRequest(BaseModel):
    turn1_id: str
    turn2_id: str
    is_success: bool = True

class SocraticSubmitRequest(BaseModel):
    round: int
    answer: str

class DiscursiveSubmitRequest(BaseModel):
    lesson_id: int
    answer: str

class MCQSubmitRequest(BaseModel):
    lesson_id: int
    answers: dict[str, str] # {"0": "A", "1": "C"}
    blanks: dict[str, str] # {"0": "palavra", "1": "termo"}

class DocumentGenerateRequest(BaseModel):
    doc_id: str
    subject: Optional[str] = None
    level: Optional[str] = None
    language: str = "pt-BR"

@app.post("/api/courses/upload-document")
async def upload_document(file: UploadFile = File(...)):
    filename = file.filename or "livro"
    ext = filename.split(".")[-1].lower()
    if ext not in ["pdf", "epub"]:
        raise HTTPException(status_code=400, detail="Formato inválido. Por favor, envie um arquivo .pdf ou .epub.")

    temp_id = uuid.uuid4().hex[:12]
    safe_filename = f"{temp_id}_{Path(filename).name}"
    temp_path = UPLOADS_DIR / safe_filename

    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        if ext == "pdf":
            extracted = extract_from_pdf(temp_path)
            if extracted.get("is_scanned_pdf"):
                raise HTTPException(
                    status_code=400,
                    detail="Este arquivo PDF contém apenas imagens escaneadas sem camada de texto selecionável. Por favor, utilize um PDF com texto digital ou um arquivo EPUB."
                )
        else:
            extracted = extract_from_epub(temp_path)

        chunks = build_chapter_chunks(extracted, ext)
        if not chunks:
            raise HTTPException(
                status_code=400,
                detail="Não foi possível identificar capítulos ou texto legível neste documento."
            )

        total_pages = extracted.get("total_pages", max(1, len(chunks) * 12))
        analysis = await analyze_document_cognition(
            filename=filename,
            format_type=ext,
            total_pages=total_pages,
            chapters=chunks,
            metadata_title=extracted.get("metadata_title"),
            metadata_author=extracted.get("metadata_author")
        )

        doc_id = f"doc_{uuid.uuid4().hex[:12]}"
        doc_record = {
            "doc_id": doc_id,
            "clean_title": analysis.clean_title,
            "author": analysis.author,
            "format": ext,
            "total_pages": total_pages,
            "total_chapters": len(chunks),
            "total_word_count": sum(c.word_count for c in chunks),
            "inferred_level": analysis.inferred_level,
            "complexity_reason": analysis.complexity_reason,
            "reader_prerequisites": analysis.reader_prerequisites,
            "raw_filename": filename,
            "chunks": [c.model_dump() for c in chunks]
        }

        # Salva o índice textual leve no storage
        doc_cache_path = DOCS_CACHE_DIR / f"{doc_id}.json"
        with open(doc_cache_path, "w", encoding="utf-8") as f:
            json.dump(doc_record, f, ensure_ascii=False)

        # Retorna o diagnóstico ao frontend (sem a carga pesada de texto das chunks)
        res_data = dict(doc_record)
        del res_data["chunks"]
        return res_data

    finally:
        # Limpeza e descarte automático do arquivo binário pesado temporário
        if temp_path.exists():
            try:
                temp_path.unlink()
            except Exception:
                pass

@app.post("/api/courses/generate-from-document")
async def generate_course_from_document(
    req: DocumentGenerateRequest,
    bg: BackgroundTasks,
    session: Session = Depends(get_session)
):
    doc_cache_path = DOCS_CACHE_DIR / f"{req.doc_id}.json"
    if not doc_cache_path.exists():
        raise HTTPException(status_code=404, detail="Documento analisado não encontrado ou sessão expirada.")

    with open(doc_cache_path, "r", encoding="utf-8") as f:
        doc_data = json.load(f)

    final_subject = (req.subject or doc_data.get("clean_title") or doc_data.get("raw_filename")).strip()
    raw_level = req.level or doc_data.get("inferred_level") or "Básico"
    final_level = normalize_level(raw_level, req.language)

    job_id = f"job_{uuid.uuid4().hex[:10]}"
    job = GenerationJob(
        id=job_id,
        status="processing",
        progress_pct=2,
        current_step=f"Iniciando esteira do livro '{final_subject}' ({final_level})..."
    )
    session.add(job)
    session.commit()

    # Dispara pipeline em background com source_type="document" e os chunks do livro
    bg.add_task(
        CourseOrchestrator.run_pipeline,
        job_id=job_id,
        subject=final_subject,
        level=final_level,
        language=req.language,
        source_type="document",
        book_filename=doc_data.get("clean_title") or doc_data.get("raw_filename"),
        book_pages=doc_data.get("total_pages"),
        chapter_chunks=doc_data.get("chunks", [])
    )

    return {
        "job_id": job_id,
        "status": "processing",
        "message": f"Esteira do livro '{final_subject}' iniciada com sucesso."
    }

@app.post("/api/courses/generate")
async def generate_course(req: CourseCreateRequest, bg: BackgroundTasks, session: Session = Depends(get_session)):
    req.level = normalize_level(req.level, req.language)
    job_id = f"job_{uuid.uuid4().hex[:10]}"
    job = GenerationJob(
        id=job_id,
        status="processing",
        progress_pct=2,
        current_step=f"Iniciando esteira de producao para '{req.subject}' ({req.level})..."
    )
    session.add(job)
    session.commit()

    # Dispara LangGraph em background
    bg.add_task(CourseOrchestrator.run_pipeline, job_id, req.subject, req.level, req.language)

    return {
        "job_id": job_id,
        "status": "processing",
        "message": "Esteira assincrona iniciada com sucesso."
    }

@app.get("/api/jobs/{job_id}")
def get_job_status(job_id: str, session: Session = Depends(get_session)):
    job = session.get(GenerationJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job nao encontrado")
    return {
        "job_id": job.id,
        "status": job.status,
        "progress_pct": job.progress_pct,
        "current_step": job.current_step,
        "course_id": job.course_id,
        "error_message": job.error_message
    }

@app.get("/api/courses")
def list_courses(session: Session = Depends(get_session)):
    courses = session.exec(select(Course).order_by(Course.id.desc())).all()
    results = []
    for c in courses:
        modules = session.exec(select(Module).where(Module.course_id == c.id)).all()
        lessons = session.exec(select(Lesson).join(Module).where(Module.course_id == c.id)).all()
        completed_lessons = [l for l in lessons if l.status == "completed"]
        results.append({
            "id": c.id,
            "subject": c.subject,
            "level": c.level,
            "language": getattr(c, "language", "pt-BR") or "pt-BR",
            "access_mode": getattr(c, "access_mode", "open") or "open",
            "cover_image_url": c.cover_image_url,
            "is_completed": c.is_completed,
            "created_at": c.created_at.isoformat() if c.created_at else None,
            "source_type": getattr(c, "source_type", "web") or "web",
            "source_book_filename": getattr(c, "source_book_filename", None),
            "source_book_pages": getattr(c, "source_book_pages", None),
            "total_modules": len(modules),
            "total_lessons": len(lessons),
            "completed_lessons": len(completed_lessons),
            "progress_percent": int((len(completed_lessons) / len(lessons) * 100)) if lessons else 0
        })
    return results

@app.get("/api/courses/{course_id}")
def get_course_details(course_id: int, session: Session = Depends(get_session)):
    course = session.get(Course, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Curso nao encontrado")
    
    modules = session.exec(select(Module).where(Module.course_id == course_id).order_by(Module.module_number)).all()
    modules_res = []
    for mod in modules:
        lessons = session.exec(select(Lesson).where(Lesson.module_id == mod.id).order_by(Lesson.lesson_number)).all()
        modules_res.append({
            "id": mod.id,
            "module_number": mod.module_number,
            "title": mod.title,
            "is_unlocked": mod.is_unlocked,
            "is_completed": mod.is_completed,
            "lessons": [
                {
                    "id": l.id,
                    "lesson_number": l.lesson_number,
                    "title": l.title,
                    "core_concept": l.core_concept,
                    "status": l.status,
                    "mcq_score": l.mcq_score,
                    "discursive_passed": l.discursive_passed
                }
                for l in lessons
            ]
        })

    return {
        "id": course.id,
        "subject": course.subject,
        "level": course.level,
        "language": getattr(course, "language", "pt-BR") or "pt-BR",
        "access_mode": getattr(course, "access_mode", "open") or "open",
        "cover_image_url": course.cover_image_url,
        "is_completed": course.is_completed,
        "source_type": getattr(course, "source_type", "web") or "web",
        "source_book_filename": getattr(course, "source_book_filename", None),
        "source_book_pages": getattr(course, "source_book_pages", None),
        "research_dossier": course.research_dossier,
        "sources": json.loads(course.sources_json) if course.sources_json else [],
        "modules": modules_res
    }

class CourseAccessModeRequest(BaseModel):
    access_mode: str # "open" ou "guided"

@app.patch("/api/courses/{course_id}/access-mode")
def update_course_access_mode(course_id: int, req: CourseAccessModeRequest, session: Session = Depends(get_session)):
    course = session.get(Course, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Curso não encontrado")
    if req.access_mode not in ["open", "guided"]:
        raise HTTPException(status_code=400, detail="Modo inválido. Use 'open' ou 'guided'")
    course.access_mode = req.access_mode
    session.add(course)
    session.commit()
    session.refresh(course)
    return {"success": True, "access_mode": course.access_mode}

@app.delete("/api/courses/{course_id}")
def delete_course(course_id: int, session: Session = Depends(get_session)):
    course = session.get(Course, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Curso não encontrado")

    # 1. Encontra todos os módulos e aulas pertencentes ao curso
    modules = session.exec(select(Module).where(Module.course_id == course_id)).all()
    lessons: list[Lesson] = []
    for mod in modules:
        if mod.id is not None:
            mod_lessons = session.exec(select(Lesson).where(Lesson.module_id == mod.id)).all()
            lessons.extend(mod_lessons)

    # 2. Exclui arquivos físicos de mídia e PDFs locais associados às aulas
    storage_dir = Path(__file__).resolve().parent.parent / "storage"
    images_dir = storage_dir / "images"
    pdfs_dir = storage_dir / "pdfs"

    for lesson in lessons:
        if lesson.id is not None:
            # Imagens
            if images_dir.exists():
                for img_file in images_dir.glob(f"lesson_{lesson.id}_*.*"):
                    try:
                        img_file.unlink(missing_ok=True)
                    except Exception:
                        pass
            # PDFs
            if pdfs_dir.exists():
                for pdf_file in pdfs_dir.glob(f"aula_{lesson.id}_*.pdf"):
                    try:
                        pdf_file.unlink(missing_ok=True)
                    except Exception:
                        pass

    # 3. Exclui GenerationJobs vinculados ao curso
    jobs = session.exec(select(GenerationJob).where(GenerationJob.course_id == course_id)).all()
    for job in jobs:
        session.delete(job)

    # 4. Exclui aulas
    for lesson in lessons:
        session.delete(lesson)

    # 5. Exclui módulos
    for mod in modules:
        session.delete(mod)

    # 6. Exclui o curso
    subject_name = course.subject
    session.delete(course)
    session.commit()

    return {
        "success": True,
        "message": f"Curso '{subject_name}' (ID {course_id}) e todos os seus recursos foram excluídos com sucesso."
    }

@app.get("/api/lessons/{lesson_id}")
def get_lesson(lesson_id: int, session: Session = Depends(get_session)):
    lesson = session.get(Lesson, lesson_id)
    if not lesson:
        raise HTTPException(status_code=404, detail="Aula nao encontrada")
    
    mod = session.get(Module, lesson.module_id)
    course = session.get(Course, mod.course_id) if mod else None
    quiz_data = json.loads(lesson.quiz_json) if lesson.quiz_json else None
    
    return {
        "id": lesson.id,
        "course_id": mod.course_id if mod else None,
        "language": getattr(course, "language", "pt-BR") or "pt-BR" if course else "pt-BR",
        "module_id": lesson.module_id,
        "module_title": mod.title if mod else "",
        "lesson_number": lesson.lesson_number,
        "title": lesson.title,
        "core_concept": lesson.core_concept,
        "content_markdown": lesson.content_markdown,
        "quiz": quiz_data,
        "status": lesson.status,
        "mcq_score": lesson.mcq_score,
        "blanks_score": lesson.blanks_score,
        "discursive_passed": lesson.discursive_passed,
        "discursive_feedback": lesson.discursive_feedback,
        "simulation_passed": lesson.simulation_passed,
        "socratic_passed": lesson.socratic_passed,
        "socratic_state": json.loads(lesson.socratic_state_json) if lesson.socratic_state_json else None
    }

def check_and_unlock_lesson(session: Session, lesson: Lesson):
    """
    Verifica se a aula cumpre todos os critérios de conclusão:
    - MCQ >= 3
    - Se a aula possuir Mini-Simulador: simulation_passed == True
    - Se a aula possuir Duelo Socrático: socratic_passed == True (ou discursive_passed para legado)
    Se aprovado, marca a aula como completed e desbloqueia a próxima aula ou o próximo módulo.
    """
    quiz_data = json.loads(lesson.quiz_json) if lesson.quiz_json else {}
    has_sim = bool(quiz_data.get("simulation"))
    has_soc = bool(quiz_data.get("socratic_duel"))
    total_mcqs = len(quiz_data.get("mcq", []))
    min_mcq_required = 2 if total_mcqs <= 3 else 3

    mcq_ok = (lesson.mcq_score is not None and lesson.mcq_score >= min_mcq_required)
    sim_ok = lesson.simulation_passed if has_sim else True
    soc_ok = lesson.socratic_passed if has_soc else (lesson.discursive_passed or False)

    if mcq_ok and sim_ok and soc_ok:
        if lesson.status != "completed":
            lesson.status = "completed"
            session.add(lesson)

            # Desbloqueia proxima aula no mesmo módulo
            next_lesson = session.exec(
                select(Lesson)
                .where(Lesson.module_id == lesson.module_id)
                .where(Lesson.lesson_number == lesson.lesson_number + 1)
            ).first()

            if next_lesson:
                if next_lesson.status == "locked":
                    next_lesson.status = "in_progress"
                session.add(next_lesson)
            else:
                # Concluiu todas as aulas do módulo atual, desbloqueia próximo módulo
                cur_mod = session.get(Module, lesson.module_id)
                if cur_mod:
                    cur_mod.is_completed = True
                    session.add(cur_mod)
                    next_mod = session.exec(
                        select(Module)
                        .where(Module.course_id == cur_mod.course_id)
                        .where(Module.module_number == cur_mod.module_number + 1)
                    ).first()
                    if next_mod:
                        next_mod.is_unlocked = True
                        session.add(next_mod)
                        first_lesson_next = session.exec(
                            select(Lesson)
                            .where(Lesson.module_id == next_mod.id)
                            .where(Lesson.lesson_number == 1)
                        ).first()
                        if first_lesson_next and first_lesson_next.status == "locked":
                            first_lesson_next.status = "in_progress"
                            session.add(first_lesson_next)

@app.post("/api/lessons/{lesson_id}/submit-quiz")
async def submit_quiz(lesson_id: int, req: MCQSubmitRequest, session: Session = Depends(get_session)):
    lesson = session.get(Lesson, lesson_id)
    if not lesson or not lesson.quiz_json:
        raise HTTPException(status_code=404, detail="Aula ou quiz nao encontrado")
    
    quiz = json.loads(lesson.quiz_json)
    
    # 1. Valida MCQ (no mínimo 2 acertos em 3 questões, ou 3 em 5)
    mcq_correct = 0
    mcqs = quiz.get("mcq", [])
    total_mcqs = len(mcqs)
    min_required = 2 if total_mcqs <= 3 else 3

    for idx, q in enumerate(mcqs):
        chosen = req.answers.get(str(idx))
        for opt in q.get("options", []):
            if opt.get("is_correct") and opt.get("label") == chosen:
                mcq_correct += 1
                break

    # 2. Valida Blanks
    blanks_correct = 0
    blanks = quiz.get("fill_in_the_blanks", [])
    for idx, b in enumerate(blanks):
        typed = req.blanks.get(str(idx), "").strip().lower()
        expected = b.get("correct_word", "").strip().lower()
        if typed == expected or (expected in typed and len(typed) >= 3):
            blanks_correct += 1

    lesson.mcq_score = mcq_correct
    lesson.blanks_score = blanks_correct
    check_and_unlock_lesson(session, lesson)
    session.add(lesson)
    session.commit()

    is_passed = mcq_correct >= min_required
    
    mod = session.get(Module, lesson.module_id)
    course = session.get(Course, mod.course_id) if mod else None
    is_en = bool(course and getattr(course, "language", "").startswith("en"))

    if is_en:
        msg = f"You answered {mcq_correct} of {total_mcqs} objective questions correctly." if total_mcqs > 0 else f"You got {blanks_correct} blank answers correct."
    else:
        msg = f"Você acertou {mcq_correct} de {total_mcqs} questões objetivas." if total_mcqs > 0 else f"Você acertou {blanks_correct} nas lacunas."

    return {
        "mcq_score": mcq_correct,
        "mcq_passed": is_passed,
        "blanks_score": blanks_correct,
        "lesson_completed": lesson.status == "completed",
        "message": msg
    }

@app.post("/api/lessons/{lesson_id}/submit-discursive")
async def submit_discursive(lesson_id: int, req: DiscursiveSubmitRequest, session: Session = Depends(get_session)):
    lesson = session.get(Lesson, lesson_id)
    if not lesson or not lesson.quiz_json:
        raise HTTPException(status_code=404, detail="Aula ou quiz nao encontrado")

    quiz = json.loads(lesson.quiz_json)
    disc = quiz.get("discursive", {})
    question = disc.get("question", "")
    rubric = disc.get("evaluation_rubric", [])
    
    mod = session.get(Module, lesson.module_id)
    course = session.get(Course, mod.course_id) if mod else None
    level = course.level if course else "Básico"
    course_language = getattr(course, "language", "pt-BR") or "pt-BR" if course else "pt-BR"

    evaluation = await GraderAgent.evaluate_discursive(
        lesson_title=lesson.title,
        question=question,
        rubric=rubric,
        student_answer=req.answer,
        level=level,
        language=course_language
    )

    lesson.discursive_passed = evaluation.passed
    lesson.discursive_feedback = evaluation.feedback

    check_and_unlock_lesson(session, lesson)
    session.add(lesson)
    session.commit()

    return {
        "passed": evaluation.passed,
        "score": evaluation.score,
        "feedback": evaluation.feedback,
        "lesson_completed": lesson.status == "completed"
    }

@app.post("/api/lessons/{lesson_id}/submit-simulation")
async def submit_simulation(lesson_id: int, req: SimulationSubmitRequest, session: Session = Depends(get_session)):
    lesson = session.get(Lesson, lesson_id)
    if not lesson or not lesson.quiz_json:
        raise HTTPException(status_code=404, detail="Aula ou quiz não encontrado")

    lesson.simulation_passed = True
    check_and_unlock_lesson(session, lesson)
    session.add(lesson)
    session.commit()

    mod = session.get(Module, lesson.module_id)
    course = session.get(Course, mod.course_id) if mod else None
    is_en = bool(course and getattr(course, "language", "").startswith("en"))

    sim_msg = "Simulation completed and impact successfully validated!" if is_en else "Simulação concluída e impacto validado com sucesso!"

    return {
        "success": True,
        "simulation_passed": True,
        "lesson_completed": lesson.status == "completed",
        "message": sim_msg
    }

@app.post("/api/lessons/{lesson_id}/socratic-duel")
async def submit_socratic_duel(lesson_id: int, req: SocraticSubmitRequest, session: Session = Depends(get_session)):
    lesson = session.get(Lesson, lesson_id)
    if not lesson or not lesson.quiz_json:
        raise HTTPException(status_code=404, detail="Aula ou quiz não encontrado")

    quiz = json.loads(lesson.quiz_json)
    soc = quiz.get("socratic_duel") or quiz.get("discursive") or {}
    question = soc.get("question", "")
    rubric = soc.get("evaluation_rubric", [])

    mod = session.get(Module, lesson.module_id)
    course = session.get(Course, mod.course_id) if mod else None
    level = course.level if course else "Básico"
    course_language = getattr(course, "language", "pt-BR") or "pt-BR" if course else "pt-BR"

    state = json.loads(lesson.socratic_state_json) if lesson.socratic_state_json else {}

    if req.round == 1:
        eval1 = await GraderAgent.evaluate_socratic_round1(
            lesson_title=lesson.title,
            question=question,
            rubric=rubric,
            student_answer=req.answer,
            level=level,
            language=course_language
        )

        if eval1.passed_round1:
            state["round1_answer"] = req.answer
            state["cognitive_knot"] = eval1.cognitive_knot
            state["round1_feedback"] = eval1.feedback
            state["current_round"] = 2
            lesson.socratic_state_json = json.dumps(state, ensure_ascii=False)
            session.add(lesson)
            session.commit()

            return {
                "round": 1,
                "passed_round1": True,
                "feedback": eval1.feedback,
                "cognitive_knot": eval1.cognitive_knot,
                "socratic_passed": False,
                "lesson_completed": False
            }
        else:
            return {
                "round": 1,
                "passed_round1": False,
                "feedback": eval1.feedback,
                "cognitive_knot": None,
                "socratic_passed": False,
                "lesson_completed": False
            }

    elif req.round == 2:
        round1_answer = state.get("round1_answer", "")
        cognitive_knot = state.get("cognitive_knot", "")

        eval2 = await GraderAgent.evaluate_socratic_round2(
            lesson_title=lesson.title,
            question=question,
            student_answer_round1=round1_answer,
            cognitive_knot=cognitive_knot,
            student_answer_round2=req.answer,
            level=level,
            language=course_language
        )

        lesson.socratic_passed = eval2.passed
        state["round2_answer"] = req.answer
        state["score"] = eval2.score
        state["final_feedback"] = eval2.feedback
        state["passed"] = eval2.passed
        state["current_round"] = 2 if not eval2.passed else 3
        lesson.socratic_state_json = json.dumps(state, ensure_ascii=False)

        if eval2.passed:
            lesson.discursive_passed = True
            lesson.discursive_feedback = eval2.feedback

        check_and_unlock_lesson(session, lesson)
        session.add(lesson)
        session.commit()

        return {
            "round": 2,
            "passed": eval2.passed,
            "score": eval2.score,
            "feedback": eval2.feedback,
            "socratic_passed": lesson.socratic_passed,
            "lesson_completed": lesson.status == "completed"
        }
    else:
        raise HTTPException(status_code=400, detail="Round inválido. Deve ser 1 ou 2.")


@app.get("/api/lessons/{lesson_id}/download-pdf")
async def download_pdf(lesson_id: int, session: Session = Depends(get_session)):
    from app.services.pdf_service import PDFService
    lesson = session.get(Lesson, lesson_id)
    if not lesson or not lesson.content_markdown:
        raise HTTPException(status_code=404, detail="Conteudo da aula nao encontrado")

    mod = session.get(Module, lesson.module_id)
    mod_title = f"Modulo {mod.module_number}: {mod.title}" if mod else "Apostila de Aula"

    os.makedirs("storage/pdfs", exist_ok=True)
    pdf_filename = f"storage/pdfs/aula_{lesson.id}_{lesson.title.replace(' ', '_')}.pdf"
    
    try:
        await PDFService.render_lesson_pdf(
            title=lesson.title,
            module_title=mod_title,
            content_markdown=lesson.content_markdown,
            output_path=pdf_filename
        )
    except Exception as e:
        print(f"[PDFService] Erro na geração de PDF: {e}")
        raise HTTPException(status_code=500, detail=f"Falha ao gerar PDF da apostila: {str(e)}")

    return FileResponse(
        path=pdf_filename,
        filename=f"{lesson.title}.pdf",
        media_type="application/pdf"
    )

class LessonChatSubmitRequest(BaseModel):
    message: str

@app.get("/api/lessons/{lesson_id}/chat")
def get_lesson_chat_history(lesson_id: int, session: Session = Depends(get_session)):
    lesson = session.get(Lesson, lesson_id)
    if not lesson:
        raise HTTPException(status_code=404, detail="Aula não encontrada")
    
    messages = session.exec(
        select(LessonChatMessage)
        .where(LessonChatMessage.lesson_id == lesson_id)
        .order_by(LessonChatMessage.created_at.asc())
    ).all()

    return [
        {
            "id": msg.id,
            "role": msg.role,
            "content": msg.content,
            "created_at": msg.created_at.isoformat() if msg.created_at else None
        }
        for msg in messages
    ]

@app.post("/api/lessons/{lesson_id}/chat")
async def send_lesson_chat_message(
    lesson_id: int,
    req: LessonChatSubmitRequest,
    session: Session = Depends(get_session)
):
    clean_msg = req.message.strip()
    if not clean_msg:
        raise HTTPException(status_code=400, detail="A mensagem não pode ser vazia")
    if len(clean_msg) > 1200:
        raise HTTPException(status_code=400, detail="A mensagem excede o limite de 1.200 caracteres")

    lesson = session.get(Lesson, lesson_id)
    if not lesson:
        raise HTTPException(status_code=404, detail="Aula não encontrada")

    mod = session.get(Module, lesson.module_id)
    course = session.get(Course, mod.course_id) if mod else None
    if not course:
        raise HTTPException(status_code=404, detail="Curso não encontrado")

    # 1. Salva a mensagem do usuário no histórico
    user_chat = LessonChatMessage(
        lesson_id=lesson_id,
        role="user",
        content=clean_msg
    )
    session.add(user_chat)
    session.commit()
    session.refresh(user_chat)

    # 2. Carrega o histórico recente para a janela deslizante
    history = session.exec(
        select(LessonChatMessage)
        .where(LessonChatMessage.lesson_id == lesson_id)
        .order_by(LessonChatMessage.created_at.asc())
    ).all()

    # 3. Invoca o TutorService (otimizado para tokens, linguagem simples e exemplos práticos)
    try:
        assistant_content = await TutorService.generate_response(
            course=course,
            lesson=lesson,
            history=history,
            new_message=clean_msg
        )
    except Exception as e:
        print(f"[TutorService] Erro na geração de resposta: {e}")
        assistant_content = (
            "Tive um tropeço momentâneo na conexão com a IA para responder sua dúvida. "
            "Poderia tentar enviar novamente em alguns segundos?"
        )

    # 4. Salva a resposta do assistente no banco
    assistant_chat = LessonChatMessage(
        lesson_id=lesson_id,
        role="assistant",
        content=assistant_content
    )
    session.add(assistant_chat)
    session.commit()
    session.refresh(assistant_chat)

    return {
        "id": assistant_chat.id,
        "role": assistant_chat.role,
        "content": assistant_chat.content,
        "created_at": assistant_chat.created_at.isoformat() if assistant_chat.created_at else None
    }

@app.delete("/api/lessons/{lesson_id}/chat")
def clear_lesson_chat_history(lesson_id: int, session: Session = Depends(get_session)):
    lesson = session.get(Lesson, lesson_id)
    if not lesson:
        raise HTTPException(status_code=404, detail="Aula não encontrada")

    session.exec(delete(LessonChatMessage).where(LessonChatMessage.lesson_id == lesson_id))
    session.commit()

    return {"status": "cleared", "lesson_id": lesson_id}
