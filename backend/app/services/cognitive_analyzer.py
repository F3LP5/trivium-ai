"""
Serviço de Diagnóstico Cognitivo Pré-Geração do Livro.
Realiza uma análise rápida (sumário, introdução e primeiros capítulos) para:
1. Higienizar o título do livro pela IA (removendo números, pontos, ISBNs e ruídos de arquivo).
2. Classificar o nível de complexidade real do texto-fonte (Básico, Intermediário, Avançado).
3. Detectar os pressupostos que o autor assume do leitor.
4. Gerar o feedback de transparência para o usuário.
"""
from typing import List, Optional
from pydantic import BaseModel, Field
from app.services.llm_gateway import LLMGateway
from app.services.document_extractor import ChapterChunk, clean_book_title_from_filename

class CognitiveAnalysisSchema(BaseModel):
    clean_title: str = Field(description="Título editorial limpo e canônico do livro, sem nomes de arquivos, hashes, ISBNs ou pontos.")
    author: Optional[str] = Field(default=None, description="Nome do autor ou autores do livro.")
    inferred_level: str = Field(description="Classificação estrita do nível da obra: 'Básico', 'Intermediário' ou 'Avançado'.")
    complexity_reason: str = Field(description="Frase curta estilo Netflix e transparente explicando o porquê desse nível.")
    reader_prerequisites: List[str] = Field(default_factory=list, description="Lista de 1 a 3 pressupostos que o autor já assume que o leitor domina.")

async def analyze_document_cognition(
    filename: str,
    format_type: str,
    total_pages: int,
    chapters: List[ChapterChunk],
    metadata_title: Optional[str] = None,
    metadata_author: Optional[str] = None,
    language: str = "pt-BR"
) -> CognitiveAnalysisSchema:
    """
    Executa a leitura diagnóstica prévia de baixo consumo de tokens (~3.000 tokens)
    utilizando a estrutura inicial do livro.
    """
    fallback_title = metadata_title or clean_book_title_from_filename(filename)
    
    # Prepara amostra estruturada dos primeiros 3 a 5 capítulos
    sample_outline = []
    sample_text_blocks = []
    
    for ch in chapters[:8]:
        sample_outline.append(f"- Capítulo/Seção {ch.chapter_index}: {ch.title} ({ch.word_count} palavras)")
        # Pega amostra de até 400 palavras por capítulo para avaliar vocabulário e densidade
        words = ch.text_content.split()[:350]
        if words:
            sample_text_blocks.append(f"--- [Trecho do Capítulo: {ch.title}] ---\n" + " ".join(words))

    outline_str = "\n".join(sample_outline)
    text_sample_str = "\n\n".join(sample_text_blocks[:4]) # Amostra focada

    system_prompt = (
        "Você é um Auditor Cognitivo e Editor Sênior de livros acadêmicos e técnicos do Trivium Academy. "
        "Sua missão é realizar uma análise diagnóstica rápida, imparcial e precisa do material fornecido para calibrar o nível do curso.\n\n"
        "DIRETRIZES DE NÍVEL:\n"
        "- 'Básico': Livros introdutórios, didáticos, de divulgação geral ou autoaprendizagem básica (ex: introduções, guias para leigos).\n"
        "- 'Intermediário': Livros que exigem raciocínio metodológico, estudos de caso práticos, terminologia de mercado ou fundamentos consolidados.\n"
        "- 'Avançado': Livros teóricos densos, tratados acadêmicos, epistemologia, formalismos matemáticos/computacionais avançados ou análises críticas complexas.\n\n"
        "HIGIENIZAÇÃO DO TÍTULO:\n"
        "- Nunca retorne nomes de arquivos com códigos, ISBNs, datas ou sublinhados.\n"
        "- Retorne o título canônico da obra (ex: 'Aprendendo a Aprender: Como Ter Sucesso em Matemática e Ciências').\n"
        "Responda estritamente no schema JSON solicitado."
    )

    user_prompt = f"""
Analise os seguintes dados do livro carregado:
- Nome original do arquivo: {filename}
- Formato: {format_type.upper()}
- Total de páginas estimadas: {total_pages}
- Metadados detectados: Título="{metadata_title or 'N/A'}", Autor="{metadata_author or 'N/A'}"
- Idioma do curso: {language}

ESTRUTURA INICIAL DE CAPÍTULOS:
{outline_str}

AMOSTRA INICIAL DO TEXTO DO LIVRO:
{text_sample_str}

Retorne:
1. clean_title: Título editorial limpo e canônico.
2. author: Autor detectado.
3. inferred_level: 'Básico', 'Intermediário' ou 'Avançado'.
4. complexity_reason: Frase curta, elegante e estilo Netflix explicando a profundidade do texto.
5. reader_prerequisites: 1 a 3 pressupostos que o autor assume do leitor.
"""

    try:
        result = await LLMGateway.generate_structured(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            schema_class=CognitiveAnalysisSchema,
            max_tokens=1200,
            timeout=35
        )
        return result
    except Exception as e:
        print(f"[DocumentCognitiveAnalyzer] Fallback após erro na análise: {e}")
        # Fallback gracioso com heurística
        return CognitiveAnalysisSchema(
            clean_title=fallback_title,
            author=metadata_author or "Autor não especificado",
            inferred_level="Intermediário",
            complexity_reason="A obra apresenta fundamentos sólidos e metodologia prática estruturada.",
            reader_prerequisites=["Compreensão leitora e interesse pelos conceitos do livro."]
        )
