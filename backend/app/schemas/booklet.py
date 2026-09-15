from pydantic import BaseModel, Field, model_validator
from typing import List, Optional, Any

class ReportPage(BaseModel):
    type: str = Field(default="content", description="'content' ou 'quote'")
    kicker: Optional[str] = Field(default="?", description="Símbolo inicial ou kicker (ex: '?', '!', '01')")
    title_html: str = Field(default="título da <b>seção</b>", description="Título em minúsculas com tags <b> para destaques")
    attribution_html: Optional[str] = Field(default=None, description="Apenas para type='quote'. Contexto/autor com <b>")
    quote_text: Optional[str] = Field(default=None, description="Apenas para type='quote'. A grande pergunta ou citação")
    columns: List[str] = Field(default_factory=list, description="Exatamente 2 colunas de texto denso e aprofundado com tags <b>")
    highlight_block: str = Field(default="", description="Frase de impacto da caixa amarela inferior com <b>")
    page_number: int = Field(default=1, description="Número da página")

    @model_validator(mode="before")
    @classmethod
    def parse_page(cls, data: Any) -> Any:
        if isinstance(data, dict):
            t = data.get("type") or "content"
            title = data.get("title_html") or data.get("title") or "título"
            cols = data.get("columns") or []
            if not isinstance(cols, list):
                cols = [str(cols)]
            while len(cols) < 2:
                cols.append("")
            highlight = data.get("highlight_block") or data.get("highlight") or data.get("quote") or ""
            return {
                "type": str(t),
                "kicker": str(data.get("kicker") or "?"),
                "title_html": str(title),
                "attribution_html": data.get("attribution_html"),
                "quote_text": data.get("quote_text"),
                "columns": [str(cols[0]), str(cols[1])],
                "highlight_block": str(highlight),
                "page_number": int(data.get("page_number") or 1)
            }
        return data

class LessonBookletReport(BaseModel):
    brand: str = Field(default="trivium academy", description="Marca no topo")
    footer_label: str = Field(default="rigor, lógica e maestria", description="Slogan vertical lateral")
    pages: List[ReportPage] = Field(default_factory=list, description="Páginas da apostila editorial")
