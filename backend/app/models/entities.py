from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime
import json

class Course(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    subject: str = Field(index=True)
    level: str = Field(index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_completed: bool = Field(default=False)
    language: str = Field(default="pt-BR", index=True)
    access_mode: str = Field(default="open") # "open" ou "guided"
    research_dossier: Optional[str] = Field(default=None)
    sources_json: Optional[str] = Field(default=None)
    cover_image_url: Optional[str] = Field(default=None)
    source_type: str = Field(default="web", index=True) # "web" | "document"
    source_book_filename: Optional[str] = Field(default=None)
    source_book_pages: Optional[int] = Field(default=None)

    modules: List['Module'] = Relationship(back_populates='course')

class Module(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    course_id: int = Field(foreign_key='course.id')
    module_number: int
    title: str
    is_unlocked: bool = Field(default=False)
    is_completed: bool = Field(default=False)

    course: Optional[Course] = Relationship(back_populates='modules')
    lessons: List['Lesson'] = Relationship(back_populates='module')

class Lesson(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    module_id: int = Field(foreign_key='module.id')
    lesson_number: int
    title: str
    core_concept: str
    content_markdown: Optional[str] = Field(default=None)
    summary_50_words: Optional[str] = Field(default=None)
    
    # Quiz estruturado em JSON
    quiz_json: Optional[str] = Field(default=None)
    
    # Status e Mastery Learning
    status: str = Field(default='locked') # locked, in_progress, completed
    mcq_score: int = Field(default=0)
    blanks_score: int = Field(default=0)
    discursive_passed: bool = Field(default=False)
    discursive_feedback: Optional[str] = Field(default=None)
    
    # Mini-Simulador Sandbox & Duelo Socrático
    simulation_passed: bool = Field(default=False)
    socratic_passed: bool = Field(default=False)
    socratic_state_json: Optional[str] = Field(default=None)
    
    module: Optional[Module] = Relationship(back_populates='lessons')
    chat_messages: List['LessonChatMessage'] = Relationship(back_populates='lesson')

class LessonChatMessage(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    lesson_id: int = Field(foreign_key='lesson.id', index=True)
    role: str = Field(index=True) # "user" | "assistant"
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

    lesson: Optional[Lesson] = Relationship(back_populates='chat_messages')

class GenerationJob(SQLModel, table=True):
    id: str = Field(primary_key=True)
    course_id: Optional[int] = Field(default=None)
    status: str = Field(default='processing') # processing, completed, failed
    progress_pct: int = Field(default=0)
    current_step: str = Field(default='Iniciando...')
    error_message: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
