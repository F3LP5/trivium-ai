from pydantic import BaseModel, Field, model_validator
from typing import List, Optional, Any

class LessonPlan(BaseModel):
    title: str = Field(default="Aula", description="Titulo direto e atrativo da aula")
    core_concept: str = Field(default="", description="O conceito central que sera ensinado")

    @model_validator(mode="before")
    @classmethod
    def parse_lesson(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # Normaliza campos alternativos
            title = data.get("title") or data.get("name") or data.get("topic") or "Aula"
            concept = data.get("core_concept") or data.get("concept") or data.get("description") or data.get("objective") or title
            return {"title": str(title), "core_concept": str(concept)}
        return data

class ModulePlan(BaseModel):
    module_number: int = Field(default=1, description="Numero sequencial do modulo")
    title: str = Field(default="Modulo", description="Titulo do modulo")
    lessons: List[LessonPlan] = Field(default_factory=list, description="Lista de aulas")

    @model_validator(mode="before")
    @classmethod
    def parse_module(cls, data: Any) -> Any:
        if isinstance(data, dict):
            num = data.get("module_number") or data.get("id") or data.get("number") or 1
            title = data.get("title") or data.get("name") or f"Modulo {num}"
            raw_lessons = data.get("lessons") or data.get("topics") or []
            return {"module_number": int(num), "title": str(title), "lessons": raw_lessons}
        return data

class CurriculumSchema(BaseModel):
    subject: str = Field(default="Curso", description="Tema do curso")
    level: str = Field(default="Básico", description="Nivel do curso")
    modules: List[ModulePlan] = Field(default_factory=list, description="Modulos")

    @model_validator(mode="before")
    @classmethod
    def parse_curriculum(cls, data: Any) -> Any:
        if isinstance(data, list):
            # Se a LLM retornar diretamente uma lista de módulos
            return {
                "subject": "Curso",
                "level": "Básico",
                "modules": [
                    {**(m if isinstance(m, dict) else {}), "module_number": idx}
                    for idx, m in enumerate(data, start=1)
                ]
            }
        elif isinstance(data, dict):
            sub = data.get("subject") or data.get("courseName") or data.get("course_title") or data.get("title") or "Curso"
            lvl = data.get("level") or data.get("difficulty") or "Básico"
            raw_mods = data.get("modules") or data.get("curriculum") or []
            if isinstance(raw_mods, list):
                mods = []
                for idx, m in enumerate(raw_mods, start=1):
                    if isinstance(m, dict):
                        m_copy = dict(m)
                        if not m_copy.get("module_number"):
                            m_copy["module_number"] = idx
                        mods.append(m_copy)
                    else:
                        mods.append(m)
            else:
                mods = []
            return {"subject": str(sub), "level": str(lvl), "modules": mods}
        return data
