from sqlmodel import SQLModel, create_engine, Session
import os

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "trivium.db"

DATABASE_URL = os.getenv('DATABASE_URL', f'sqlite:///{DB_PATH.as_posix()}')
engine = create_engine(DATABASE_URL, echo=False, connect_args={'check_same_thread': False, 'timeout': 30.0})

def init_db():
    from app.models.entities import Course, Module, Lesson, GenerationJob
    
    with engine.connect() as conn:
        from sqlalchemy import text
        try:
            conn.execute(text("PRAGMA journal_mode=WAL;"))
            conn.execute(text("PRAGMA synchronous=NORMAL;"))
            conn.commit()
        except Exception:
            pass

    SQLModel.metadata.create_all(engine)
    
    # Migração segura para colunas novas em bases SQLite já existentes
    with engine.connect() as conn:
        from sqlalchemy import text
        for col, col_type in [
            ("simulation_passed", "BOOLEAN DEFAULT 0"),
            ("socratic_passed", "BOOLEAN DEFAULT 0"),
            ("socratic_state_json", "TEXT DEFAULT NULL"),
        ]:
            try:
                conn.execute(text(f"ALTER TABLE lesson ADD COLUMN {col} {col_type}"))
                conn.commit()
            except Exception:
                pass

        for col, col_type in [
            ("research_dossier", "TEXT DEFAULT NULL"),
            ("sources_json", "TEXT DEFAULT NULL"),
            ("cover_image_url", "TEXT DEFAULT NULL"),
            ("language", "VARCHAR DEFAULT 'pt-BR'"),
            ("access_mode", "VARCHAR DEFAULT 'open'"),
            ("source_type", "VARCHAR DEFAULT 'web'"),
            ("source_book_filename", "TEXT DEFAULT NULL"),
            ("source_book_pages", "INTEGER DEFAULT NULL"),
        ]:
            try:
                conn.execute(text(f"ALTER TABLE course ADD COLUMN {col} {col_type}"))
                conn.commit()
            except Exception:
                pass

def get_session():
    with Session(engine) as session:
        yield session
