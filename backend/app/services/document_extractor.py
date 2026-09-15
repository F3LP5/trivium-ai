"""
Serviço profissional de extração e indexação de documentos (PDF e EPUB) para o Trivium Academy.
Implementa leitura 100% integral, detecção de scans sem OCR, extração de sumários,
limpeza de títulos e fatiamento semântico por capítulos (Hierarchical Chunking).
"""
import os
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from pypdf import PdfReader
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup

class ChapterChunk(BaseModel):
    chapter_index: int
    title: str
    page_start: Optional[int] = None
    page_end: Optional[int] = None
    text_content: str
    word_count: int

class DocumentAnalysisResult(BaseModel):
    clean_title: str
    raw_filename: str
    author: Optional[str] = None
    format: str # "pdf" | "epub"
    total_pages: int
    total_chapters: int
    total_word_count: int
    inferred_level: str # "Básico" | "Intermediário" | "Avançado"
    complexity_reason: str
    reader_prerequisites: List[str]
    chapters: List[ChapterChunk]
    is_scanned_pdf: bool = False

def sanitize_extracted_text(text: str) -> str:
    """Limpa quebras de linhas desnecessárias, múltiplos espaços e cabeçalhos residuais."""
    if not text:
        return ""
    # Remove múltiplos espaços e quebras excessivas
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

def clean_book_title_from_filename(filename: str) -> str:
    """Higieniza nomes de arquivos sujos com datas, hashes, ISBNs e traços."""
    base = Path(filename).stem
    # Remove partes após separadores de metadados como '--', 'isbn', 'Anna', etc.
    base = re.split(r'--|\b(isbn|annas?|archive|z-lib|10\.\d{4})\b', base, flags=re.IGNORECASE)[0]
    # Remove caracteres especiais desnecessários
    base = re.sub(r'[_\.]+', ' ', base)
    base = re.sub(r'\s+', ' ', base).strip()
    return base or "Livro Selecionado"

def extract_from_pdf(pdf_path: Path) -> Dict[str, Any]:
    """
    Realiza a leitura integral de 100% das páginas de um arquivo PDF.
    Extrai sumário / marcadores estruturados e detecta se é um PDF escaneado (sem texto).
    """
    reader = PdfReader(str(pdf_path))
    total_pages = len(reader.pages)
    
    # 1. Checagem de segurança contra PDFs escaneados (sem texto)
    sample_text = ""
    check_limit = min(10, total_pages)
    for i in range(check_limit):
        try:
            page_t = reader.pages[i].extract_text() or ""
            sample_text += page_t
        except Exception:
            pass
            
    if len(sample_text.strip()) < 30:
        return {
            "is_scanned_pdf": True,
            "total_pages": total_pages,
            "pages_text": [],
            "outlines": [],
            "metadata_title": None,
            "metadata_author": None
        }

    # 2. Extração integral página por página
    pages_text: List[str] = []
    for idx, page in enumerate(reader.pages):
        try:
            txt = page.extract_text() or ""
            pages_text.append(sanitize_extracted_text(txt))
        except Exception:
            pages_text.append("")

    # 3. Metadados do documento
    metadata_title = None
    metadata_author = None
    try:
        meta = reader.metadata
        if meta:
            if meta.title and len(meta.title.strip()) > 3:
                metadata_title = meta.title.strip()
            if meta.author and len(meta.author.strip()) > 2:
                metadata_author = meta.author.strip()
    except Exception:
        pass

    # 4. Sumário / Marcadores
    outlines = []
    try:
        def parse_outlines(outline_list):
            items = []
            for item in outline_list:
                if isinstance(item, list):
                    items.extend(parse_outlines(item))
                elif hasattr(item, 'title'):
                    title = getattr(item, 'title', '')
                    page_dest = getattr(item, 'page', None)
                    page_num = 1
                    if page_dest:
                        try:
                            page_num = reader.get_destination_page_number(item) + 1
                        except Exception:
                            pass
                    if title:
                        items.append({"title": title.strip(), "page": page_num})
            return items
        if reader.outline:
            outlines = parse_outlines(reader.outline)
    except Exception:
        pass

    return {
        "is_scanned_pdf": False,
        "total_pages": total_pages,
        "pages_text": pages_text,
        "outlines": outlines,
        "metadata_title": metadata_title,
        "metadata_author": metadata_author
    }

def extract_from_epub(epub_path: Path) -> Dict[str, Any]:
    """
    Realiza a leitura integral de 100% dos capítulos e itens da espinha dorsal (Spine) de um EPUB.
    """
    book = epub.read_epub(str(epub_path))
    
    metadata_title = None
    metadata_author = None
    try:
        t = book.get_metadata('DC', 'title')
        if t:
            metadata_title = t[0][0]
        a = book.get_metadata('DC', 'creator')
        if a:
            metadata_author = a[0][0]
    except Exception:
        pass

    chapters_raw = []
    for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
        try:
            content = item.get_content()
            soup = BeautifulSoup(content, 'html.parser')
            # Extrai título do capítulo se houver tag h1/h2/title
            h_tag = soup.find(['h1', 'h2', 'h3', 'title'])
            chapter_title = h_tag.get_text().strip() if h_tag else item.get_name()
            # Remove scripts, estilos e extrai texto limpo
            for s in soup(['script', 'style']):
                s.decompose()
            text = sanitize_extracted_text(soup.get_text())
            if len(text) > 80: # descarta páginas vazias/de capa pura
                chapters_raw.append({
                    "title": chapter_title,
                    "text": text
                })
        except Exception:
            continue

    return {
        "metadata_title": metadata_title,
        "metadata_author": metadata_author,
        "chapters_raw": chapters_raw,
        "total_pages": max(1, len(chapters_raw) * 12) # estimativa de páginas
    }

def build_chapter_chunks(extracted_data: Dict[str, Any], file_format: str) -> List[ChapterChunk]:
    """
    Agrupa o conteúdo textual em blocos de capítulos consistentes para os agentes.
    Se houver sumário, usa as demarcações. Caso contrário, divide em fatias semânticas sequenciais.
    """
    chunks: List[ChapterChunk] = []
    
    if file_format == "epub":
        for idx, ch in enumerate(extracted_data.get("chapters_raw", []), 1):
            txt = ch["text"]
            chunks.append(ChapterChunk(
                chapter_index=idx,
                title=ch["title"][:120],
                text_content=txt,
                word_count=len(txt.split())
            ))
    else:
        # Modo PDF
        pages_text = extracted_data.get("pages_text", [])
        total_pages = len(pages_text)
        outlines = extracted_data.get("outlines", [])

        if outlines and len(outlines) >= 3:
            # Organiza por marcadores do sumário
            for i, out in enumerate(outlines):
                start_p = max(1, out["page"])
                end_p = total_pages
                if i + 1 < len(outlines):
                    end_p = max(start_p, outlines[i+1]["page"] - 1)
                
                ch_text = "\n\n".join(pages_text[start_p-1 : end_p])
                if len(ch_text.strip()) > 100:
                    chunks.append(ChapterChunk(
                        chapter_index=len(chunks) + 1,
                        title=out["title"][:120],
                        page_start=start_p,
                        page_end=end_p,
                        text_content=ch_text,
                        word_count=len(ch_text.split())
                    ))
        
        # Se não tiver sumário ou tiver poucos marcadores, particiona em blocos de ~15 a 20 páginas
        if not chunks:
            pages_per_chunk = max(8, min(25, total_pages // 8 or 15))
            current_start = 1
            idx = 1
            while current_start <= total_pages:
                current_end = min(total_pages, current_start + pages_per_chunk - 1)
                slice_text = "\n\n".join(pages_text[current_start-1 : current_end])
                if slice_text.strip():
                    chunks.append(ChapterChunk(
                        chapter_index=idx,
                        title=f"Parte {idx}: Páginas {current_start} a {current_end}",
                        page_start=current_start,
                        page_end=current_end,
                        text_content=slice_text,
                        word_count=len(slice_text.split())
                    ))
                    idx += 1
                current_start = current_end + 1

    return chunks
