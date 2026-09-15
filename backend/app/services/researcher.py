import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import re
import urllib.parse
import logging
import asyncio
import json
from typing import List, Dict, Optional, Tuple, Any
from curl_cffi import requests
from bs4 import BeautifulSoup
import trafilatura

logger = logging.getLogger(__name__)

class TriviumResearchEngine:
    """
    Motor Avançado de Pesquisa Reflexiva e Checagem Factual (Padrão STORM / Deep Research):
    - Decomposição Semântica de Queries: Divide o tema em 3-4 eixos de busca especializados.
    - Desambiguação Canônica na Wikipédia: Consulta termos-chave para extrair fatos enciclopédicos.
    - Busca Multi-Fonte no DuckDuckGo com evasão TLS (Chrome 124) e desduplicação por domínio.
    - Extração limpa e higienizada via Trafilatura (sem scripts, banners ou anúncios).
    - Auditoria Reflexiva (Research Critic): Identifica lacunas e sintetiza uma FactMatrix estruturada com 8-15 entidades reais.
    """

    def __init__(self):
        self.session = requests.Session(impersonate="chrome124")
        self.session.headers.update({
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Sec-Ch-Ua": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Upgrade-Insecure-Requests": "1"
        })
        self._cache: Dict[str, Tuple[str, List[Dict[str, Any]]]] = {}

    def search_duckduckgo(self, query: str, max_results: int = 8) -> List[Dict[str, str]]:
        """Busca no DuckDuckGo HTML com Chrome 124 TLS."""
        try:
            encoded_query = urllib.parse.quote_plus(query)
            url = f"https://html.duckduckgo.com/html/?q={encoded_query}"
            resp = self.session.get(url, timeout=8)
            
            if resp.status_code != 200:
                logger.warning(f"DuckDuckGo retornou status {resp.status_code} para query: {query}")
                return []

            soup = BeautifulSoup(resp.text, "html.parser")
            results = []

            for res in soup.select(".result"):
                title_el = res.select_one(".result__title a")
                snippet_el = res.select_one(".result__snippet")
                if not title_el:
                    continue

                title = title_el.get_text(strip=True)
                raw_href = title_el.get("href", "")

                actual_url = raw_href
                if "uddg=" in raw_href:
                    qs = urllib.parse.parse_qs(urllib.parse.urlparse(raw_href).query)
                    actual_url = qs.get("uddg", [raw_href])[0]

                snippet = snippet_el.get_text(strip=True) if snippet_el else ""

                # Filtra redes sociais e domínios não textuais
                if not any(blocked in actual_url.lower() for blocked in [
                    "youtube.com", "facebook.com", "instagram.com", "tiktok.com", "twitter.com", "x.com", "pinterest.com"
                ]):
                    results.append({
                        "title": title,
                        "url": actual_url,
                        "snippet": snippet
                    })

                if len(results) >= max_results:
                    break

            return results
        except Exception as e:
            logger.error(f"Erro na busca DuckDuckGo ('{query}'): {e}")
            return []

    def fetch_clean_page(self, url: str, timeout: int = 7) -> Optional[str]:
        """Acessa a URL e extrai texto limpo com Trafilatura."""
        try:
            resp = self.session.get(url, timeout=timeout)
            if resp.status_code == 200:
                clean_text = trafilatura.extract(
                    resp.text,
                    include_links=False,
                    include_images=False,
                    no_fallback=False
                )
                if clean_text and len(clean_text.strip()) > 180:
                    # Até 3.500 caracteres de texto limpo integral
                    return clean_text.strip()[:3500]
            return None
        except Exception as e:
            logger.debug(f"Falha ao extrair página ({url}): {e}")
            return None

    def query_wikipedia(self, entity: str, preferred_lang: str = "en") -> Optional[Dict[str, str]]:
        """Consulta à Wikipédia (en e pt) para obter marcos canônicos de uma entidade."""
        langs = ["en", "pt"] if preferred_lang.startswith("en") else ["pt", "en"]
        for lang in langs:
            try:
                search_url = f"https://{lang}.wikipedia.org/w/api.php?action=opensearch&search={urllib.parse.quote(entity)}&limit=1&format=json"
                resp = self.session.get(search_url, timeout=5)
                if resp.status_code == 200:
                    data = resp.json()
                    if len(data) > 1 and data[1]:
                        page_title = data[1][0]
                        summary_url = f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(page_title)}"
                        sum_resp = self.session.get(summary_url, timeout=5)
                        if sum_resp.status_code == 200:
                            sum_data = sum_resp.json()
                            extract = sum_data.get("extract", "")
                            if extract and len(extract) > 100:
                                return {
                                    "title": f"Wikipédia ({lang.upper()}): {page_title}",
                                    "url": f"https://{lang}.wikipedia.org/wiki/{urllib.parse.quote(page_title)}",
                                    "extract": extract,
                                    "domain": "wikipedia.org"
                                }
            except Exception:
                pass
        return None

    def search_archive_org(self, query: str, max_results: int = 6) -> List[Dict[str, Any]]:
        """Busca livros e textos digitalizados na API do Internet Archive."""
        try:
            # Higieniza a query: remove filtros de web como site:archive.org e normaliza aspas para o Lucene
            clean_q = re.sub(r'site:archive\.org', '', query, flags=re.IGNORECASE).strip()
            clean_q = clean_q.replace("'", '"')
            params = {
                "q": f"({clean_q}) AND mediatype:texts",
                "fl[]": ["identifier", "title", "creator", "year", "description", "downloads"],
                "sort[]": "downloads desc",
                "rows": str(max_results),
                "output": "json"
            }
            url = f"https://archive.org/advancedsearch.php?{urllib.parse.urlencode(params, doseq=True)}"
            resp = self.session.get(url, timeout=8)
            if resp.status_code == 200:
                data = resp.json()
                docs = data.get("response", {}).get("docs", [])
                results = []
                for doc in docs:
                    ident = doc.get("identifier")
                    if ident:
                        results.append({
                            "identifier": ident,
                            "title": doc.get("title") or ident,
                            "creator": doc.get("creator") or "Autor Desconhecido",
                            "year": doc.get("year") or "",
                            "url": f"https://archive.org/details/{ident}"
                        })
                return results
        except Exception as e:
            logger.warning(f"Erro ao buscar no Internet Archive ('{query}'): {e}")
        return []

    def fetch_and_index_archive_book(self, identifier: str, topic_keywords: List[str], min_bytes: int = 100000) -> Optional[Dict[str, Any]]:
        """
        Consulta os metadados do Internet Archive para descobrir o arquivo de texto OCR integral
        (_djvu.txt ou .txt), valida o tamanho mínimo (> 100 KB / ~20.000 palavras para garantir obra autêntica
        e descartar folhetos ou panfletos), baixa o conteúdo aberto e extrai passagens de ouro em memória.
        """
        try:
            # 1. Descobre os arquivos do item na API de metadados
            meta_url = f"https://archive.org/metadata/{identifier}/files"
            meta_resp = self.session.get(meta_url, timeout=8)
            if meta_resp.status_code != 200:
                return None

            files_data = meta_resp.json().get("result", [])
            # Identifica arquivos de texto integral candidatos
            candidate_files = []
            for f in files_data:
                fname = f.get("name", "")
                fsize = int(f.get("size", 0) or 0)
                # Aceita _djvu.txt ou .txt, descartando metadados e arquivos compactados
                if (fname.endswith("_djvu.txt") or fname.endswith(".txt")) and not fname.endswith("_meta.txt") and not fname.endswith(".txt.gz"):
                    if fsize >= min_bytes:
                        candidate_files.append((fsize, fname))

            if not candidate_files:
                return None

            # Ordena pelo maior arquivo de texto para pegar a edição mais completa
            candidate_files.sort(key=lambda x: x[0], reverse=True)

            full_text = None
            for fsize, chosen_fname in candidate_files:
                dl_url = f"https://archive.org/download/{identifier}/{urllib.parse.quote(chosen_fname)}"
                resp = self.session.get(dl_url, timeout=15)
                if resp.status_code == 200 and len(resp.text) >= min_bytes and "<html" not in resp.text[:300].lower():
                    full_text = resp.text
                    break

            if not full_text:
                return None

            raw_paras = re.split(r'\n\s*\n|\r\n\s*\r\n', full_text)
            clean_paras = []
            for p in raw_paras:
                p_clean = " ".join(p.split())
                # Filtra parágrafos substanciais (evita cabeçalhos de página e rodapés)
                if 180 <= len(p_clean) <= 1400:
                    clean_paras.append(p_clean)

            if not clean_paras:
                return None

            # Pontua parágrafos por densidade de palavras-chave relevantes
            scored_paras = []
            keywords_lower = [k.lower() for k in topic_keywords if len(k) > 2]
            for idx, p in enumerate(clean_paras):
                p_lower = p.lower()
                score = sum(p_lower.count(k) for k in keywords_lower)
                if score > 0:
                    scored_paras.append((score, idx, p))

            scored_paras.sort(key=lambda x: x[0], reverse=True)
            # Seleciona até 3 passagens distribuídas ao longo do livro
            selected_passages = []
            chosen_indices = set()
            for score, p_idx, text in scored_paras:
                if any(abs(p_idx - c_idx) < 10 for c_idx in chosen_indices):
                    continue
                selected_passages.append(text)
                chosen_indices.add(p_idx)
                if len(selected_passages) >= 3:
                    break

            if not selected_passages and clean_paras:
                # Fallback: pega 2 parágrafos centrais do livro
                mid = len(clean_paras) // 2
                selected_passages = clean_paras[mid:mid+2]

            return {
                "identifier": identifier,
                "golden_passages": selected_passages,
                "total_paragraphs_indexed": len(clean_paras),
                "file_size": len(full_text)
            }
        except Exception as e:
            logger.debug(f"Falha na indexação do livro {identifier}: {e}")
            return None

    async def generate_subqueries(
        self,
        topic: str,
        domain_profile: Optional[Dict[str, Any]] = None,
        language: str = "pt-BR"
    ) -> Dict[str, Any]:
        """
        Decompõe o tema em sub-queries semânticas multi-ângulo usando o perfil epistemológico universal,
        gerando buscas globais em inglês para literatura mundial e na língua alvo para termos contextuais.
        """
        domain_info = ""
        if domain_profile:
            domain_info = (
                f"\nContexto Epistemológico do Domínio:\n"
                f"- Domínio Dinâmico: {domain_profile.get('dynamic_domain_name', 'Geral')}\n"
                f"- Persona Acadêmica: {domain_profile.get('persona_title', 'Especialista')}\n"
                f"- Tom de Voz: {domain_profile.get('tone_of_voice', 'Rigoroso')}\n"
            )

        is_en = language.lower().startswith("en")
        target_name = "Inglês (English)" if is_en else "Português (Brasil)"

        prompt = (
            f"Você é o Arquiteto de Pesquisa Investigativa da Trivium (Padrão NotebookLM / Perplexity Deep Research).\n"
            f"O usuário quer um curso magistral e aprofundado sobre: '{topic}'.{domain_info}\n"
            f"Idioma de entrega final do curso: {target_name}.\n\n"
            f"DIRETRIZ DE PESQUISA GLOBAL UNIVERSAL (MANDATÓRIO):\n"
            f"A maior parte da literatura científica, técnica, primária e documental do mundo está em inglês. "
            f"Portanto, formule sub-queries conceituais de alto nível tanto em INGLÊS (para minerar a literatura mundial aberta) "
            f"quanto na língua alvo (para termos contextuais).\n\n"
            f"Gere exatamente:\n"
            f"1. Três (3) sub-queries de busca na web (DuckDuckGo) altamente específicas e ESTRITAMENTE FOCADAS NO TEMA '{topic}':\n"
            f"   - Query 1 (EM INGLÊS): Fundamentos essenciais, anatomia conceitual, arquitetura ou história seminal (ex: 'Jeff Bezos Amazon founding architecture flywheel principles' ou 'internal combustion engine operating principles mechanical cycle').\n"
            f"   - Query 2 (EM INGLÊS): Dados técnicos, medições, estudos de caso primários ou artigos analíticos aprofundados.\n"
            f"   - Query 3 ({'EM INGLÊS' if is_en else 'EM PORTUGUÊS'}): Casos práticos, diagnóstico ou termos contemporâneos da disciplina.\n"
            f"2. Uma (1) sub-query especializada para o catálogo do Internet Archive (acervo de livros em inglês):\n"
            f"   - O acervo do Internet Archive é 95%+ em inglês. Formule termos canônicos em inglês combinados com subject ou palavras-chave estritas.\n"
            f"   - NUNCA inclua operadores como 'site:archive.org' nem termos genéricos como 'livro' ou 'pdf'.\n"
            f"3. Três (3) entidades canônicas DIRETAS para consulta na Wikipédia (inclua termos canônicos em inglês e português para cobrir as enciclopédias globais).\n\n"
            f"Responda EXCLUSIVAMENTE em JSON válido neste formato exato:\n"
            f"{{\n"
            f'  "queries": ["query web 1 em inglês", "query web 2 em inglês", "query web 3"],\n'
            f'  "archive_query": "termo chave livro archive",\n'
            f'  "wiki_entities": ["entidade 1", "entidade 2", "entidade 3"]\n'
            f"}}"
        )
        try:
            from app.services.llm_gateway import LLMGateway
            from json_repair import repair_json
            raw_json = await LLMGateway.generate_text(
                "Você é um arquiteto de pesquisa investigativa que responde estritamente em JSON válido.",
                prompt,
                max_tokens=600,
                timeout=30
            )
            raw_clean = raw_json.strip()
            start = raw_clean.find("{")
            end = raw_clean.rfind("}")
            if start != -1 and end != -1 and end > start:
                raw_clean = raw_clean[start:end+1]

            data = json.loads(repair_json(raw_clean))
            if data.get("queries") and isinstance(data["queries"], list):
                aq = data.get("archive_query") or topic
                aq = re.sub(r'site:archive\.org', '', aq, flags=re.IGNORECASE).strip()
                # Se a LLM repetiu a frase com "baseado em/no/na [Obra]", extrai a obra canônica para o Archive.org
                if "baseado" in aq.lower():
                    parts = re.split(r'basead[oa]\s+(?:em|no|na|nos|nas)?\s*', aq, flags=re.IGNORECASE)
                    if len(parts) > 1 and len(parts[1].strip()) > 2:
                        ref = parts[1].strip(" .,-")
                        first = ref.split(",")[0].strip()
                        aq = f'"{ref}" OR title:("{first}")'
                data["archive_query"] = aq
                return data
        except Exception as e:
            logger.warning(f"Fallback heurístico na geração de subqueries para '{topic}': {e}")

        # Fallback heurístico de alta precisão
        ref_work = None
        topic_lower = topic.lower()
        if "baseado" in topic_lower:
            parts = re.split(r'basead[oa]\s+(?:em|no|na|nos|nas)?\s*', topic, flags=re.IGNORECASE)
            if len(parts) > 1 and len(parts[1].strip()) > 3:
                ref_work = parts[1].strip()

        words = topic.split()
        core_topic = " ".join(words[:5])

        if ref_work:
            clean_ref = ref_work.strip(" .,-")
            first_term = clean_ref.split(",")[0].strip()
            archive_q = f'"{clean_ref}" OR title:("{first_term}")'
        else:
            archive_q = f'"{core_topic}"'

        return {
            "queries": [
                f"{core_topic} fundamentos historia caracteristicas",
                f"{core_topic} dados metricas casos reais analise",
                f"{core_topic} legislacao metodos praticos desafios"
            ],
            "archive_query": archive_q,
            "wiki_entities": [ref_work or core_topic]
        }

    async def is_book_relevant(self, topic: str, book_title: str, creator: str, year: str) -> bool:
        """
        Auditoria Bibliográfica Reflexiva (Padrão NotebookLM / Perplexity Deep Research):
        Valida criticamente se a obra encontrada no Archive.org é verdadeiramente uma fonte técnica,
        histórica ou canônica pertinente ao tema, descartando obras acidentais, biografias pop,
        músicas, partituras ou ensaios desconexos que apenas mencionam termos de passagem.
        """
        try:
            from app.services.llm_gateway import LLMGateway
            eval_prompt = (
                f"Você é um bibliotecário e curador acadêmico rigoroso de padrão Perplexity Pro/NotebookLM.\n"
                f"Tema do curso: '{topic}'\n"
                f"Candidato a livro no Internet Archive: '{book_title}' por {creator} ({year})\n\n"
                f"Avalie criticamente: Esta obra é diretamente relevante para o estudo, prática, história, botânica ou técnica de '{topic}'?\n"
                f"(Descarte imediatamente obras que sejam biografias pop/bandas, músicas/partituras, ficção contemporânea ou tratados de outras disciplinas que apenas mencionam o termo de passagem).\n\n"
                f"Responda exclusivamente no formato:\n"
                f"RELEVANTE: [SIM ou NAO]\n"
                f"MOTIVO: [1 frase explicativa]"
            )
            resp = await LLMGateway.generate_text(
                "Você avalia rigorosamente a relevância bibliográfica de fontes.",
                eval_prompt,
                max_tokens=80,
                timeout=12
            )
            resp_lower = resp.lower()
            # Procura indicação explícita de relevância positiva
            for line in resp_lower.splitlines():
                if "relevante:" in line:
                    return "sim" in line
            return "relevante: sim" in resp_lower or "sim" in resp_lower.split()[:25]
        except Exception as e:
            logger.debug(f"Falha na validação de relevância do livro '{book_title}': {e}")
            title_lower = book_title.lower()
            return any(w.lower() in title_lower for w in topic.split() if len(w) > 3)

    async def build_dossier_async(
        self,
        topic: str,
        focus_keywords: Optional[List[str]] = None,
        domain_profile: Optional[Dict[str, Any]] = None,
        language: str = "pt-BR"
    ) -> Tuple[str, List[Dict[str, Any]], Dict[str, Any]]:
        """
        Executa o pipeline completo de pesquisa reflexiva com indexação de livros do Internet Archive
        e síntese do Evidence Ledger estruturado:
        1. Decomposição semântica universal bilíngue (Web Global + Livros Archive.org + Wikipédia)
        2. Coleta enciclopédica na Wikipédia
        3. Busca multi-domínio no DuckDuckGo com extração Trafilatura integral (sem snippets)
        4. Mineração de livros no Internet Archive com chunking em memória (0 tokens LLM)
        5. Síntese do Evidence Ledger JSON e FactMatrix com fontes auditadas
        """
        cache_key = f"{topic.lower().strip()}_{language.lower().strip()}_{'-'.join(focus_keywords or [])}"
        if cache_key in self._cache:
            logger.info(f"Dossiê recuperado do cache para: {topic} ({language})")
            cached = self._cache[cache_key]
            if len(cached) == 3:
                return cached
            return (cached[0], cached[1], {})

        print(f"[Pesquisador] Decompondo '{topic}' ({language}) em eixos investigativos globais...")
        subquery_data = await self.generate_subqueries(topic, domain_profile, language=language)
        queries = subquery_data.get("queries", [topic])
        archive_query = subquery_data.get("archive_query", topic)
        wiki_entities = subquery_data.get("wiki_entities", [])

        collected_sources: List[Dict[str, Any]] = []
        domain_counts: Dict[str, int] = {}

        # 1. Coleta na Wikipédia (consultando ambas as enciclopédias conforme entidades)
        for entity in wiki_entities[:4]:
            wiki_res = self.query_wikipedia(entity, preferred_lang=language)
            if wiki_res and wiki_res["extract"]:
                collected_sources.append({
                    "title": wiki_res["title"],
                    "url": wiki_res["url"],
                    "domain": "wikipedia.org",
                    "text": wiki_res["extract"],
                    "type": "wiki"
                })

        # 2. Mineração de Livros no Internet Archive (mediatype:texts) - Obras Canônicas Fundamentais
        print(f"[Pesquisador] Minerando acervo de livros do Internet Archive para '{archive_query}'...")
        archive_books = self.search_archive_org(archive_query, max_results=6)
        if len(archive_books) < 3:
            direct_q = f"({re.sub(r'subject:\([^)]+\)', '', archive_query).strip() or topic}) AND (manual OR engineering OR mechanics OR principles OR history OR science)"
            direct_q = direct_q.replace("()", "").strip()
            extra_books = self.search_archive_org(direct_q, max_results=6)
            for eb in extra_books:
                if not any(b["identifier"] == eb["identifier"] for b in archive_books):
                    archive_books.append(eb)

        topic_words = topic.split() + queries[0].split()
        books_indexed_count = 0

        for b in archive_books:
            ident = b["identifier"]
            clean_title = b.get("title", ident)
            if len(clean_title) < 10 or clean_title.lower() in ["finance", "livro", "untitled", "document", "ebook"]:
                clean_title = ident.replace('-', ' ').replace('_', ' ').title()

            is_rel = await self.is_book_relevant(topic, clean_title, b.get('creator', 'Autor'), b.get('year', ''))
            if not is_rel:
                print(f"[Pesquisador] Descartando obra irrelevante do Archive: '{clean_title}'")
                continue

            book_index = self.fetch_and_index_archive_book(ident, topic_words, min_bytes=100000)
            if book_index and book_index.get("golden_passages"):
                passages_text = "\n\n".join([f"> \"{p}\"" for p in book_index["golden_passages"]])

                collected_sources.append({
                    "title": f"Livro: {clean_title} ({b.get('creator') or 'Autor Clássico'}, {b.get('year') or ''})",
                    "url": b["url"],
                    "domain": "archive.org",
                    "text": f"Trechos Canônicos Extraídos do Livro Integral ({book_index['total_paragraphs_indexed']} parágrafos indexados, {book_index.get('file_size', 0)} bytes):\n{passages_text}",
                    "type": "book"
                })
                books_indexed_count += 1
                if books_indexed_count >= 2:
                    break

        # 3. Coleta no DuckDuckGo com desduplicação e extração integral real (sem snippets)
        target_web_count = 6
        for q in queries:
            ddg_items = self.search_duckduckgo(q, max_results=8)
            for item in ddg_items:
                url = item["url"]
                domain = urllib.parse.urlparse(url).netloc.lower().replace("www.", "")
                if domain_counts.get(domain, 0) >= 2:
                    continue

                page_text = self.fetch_clean_page(url, timeout=7)
                # EXIGÊNCIA ESTRITA: apenas aceita se houver texto limpo e substantivo (> 180 caracteres)
                # Sem snippets de busca! Se falhar, avança organicamente para a próxima URL
                if page_text and len(page_text.strip()) > 180:
                    domain_counts[domain] = domain_counts.get(domain, 0) + 1
                    collected_sources.append({
                        "title": item["title"],
                        "url": url,
                        "domain": domain,
                        "text": page_text.strip(),
                        "type": "web"
                    })

                if len([s for s in collected_sources if s.get("type") == "web"]) >= target_web_count:
                    break
            if len([s for s in collected_sources if s.get("type") == "web"]) >= target_web_count:
                break

        print(f"[Pesquisador] Coletadas {len(collected_sources)} fontes integrais ({books_indexed_count} livros do Archive.org e {len(domain_counts)} domínios web).")

        # 4. Compilação de Materiais Brutos com janela ampla (até 14.000 chars)
        raw_materials = ""
        sources_metadata = []
        for idx, s in enumerate(collected_sources, 1):
            s_type_tag = "[LIVRO/OBRA CANÔNICA]" if s.get("type") == "book" else "[ARTIGO WEB/ENCICLOPÉDIA]"
            raw_materials += f"\n\n--- FONTE #{idx}: {s_type_tag} {s['title']} ({s['domain']}) ---\nURL: {s['url']}\n{s['text'][:2400]}"
            sources_metadata.append({
                "title": s["title"],
                "url": s["url"],
                "domain": s["domain"],
                "type": s.get("type", "web")
            })

        # 5. Auditoria Reflexiva & Síntese do DOSSIÊ DE BASTIDORES E CAUSOS REAIS
        synthesis_prompt = (
            f"Você é o Curador de Pesquisa e Histórias Reais da Trivium (Padrão Masterclass / Documentários Investigativos).\n"
            f"Tema do Curso: '{topic}'.\n\n"
            f"Abaixo está o acervo de livros canônicos do Internet Archive e artigos especializados coletados na web:\n"
            f"{raw_materials[:14000]}\n\n"
            f"Sua missão é extrair e sintetizar um DOSSIÊ DE BASTIDORES em formato JSON.\n"
            f"DIRETRIZES FUNDAMENTAIS:\n"
            f"1. HISTÓRIAS, CONFLITOS E BASTIDORES REAIS:\n"
            f"   - Extraia causos verídicos, impasses vividos por pioneiros, momentos de crise, anedotas de bastidores ou erros clássicos documentados.\n"
            f"   - O material deve alimentar uma narrativa cativante e humana, onde cada conceito resolve um problema da vida real.\n"
            f"2. PURIFICAÇÃO E ADERÊNCIA TEMÁTICA TOTAL:\n"
            f"   - Cada conceito, métrica e entidade DEVE pertencer 100% ao domínio de '{topic}'.\n"
            f"   - DESCARTE fragmentos de software ou bibliotecas desconexas que tenham aparecido por acidente nas buscas.\n"
            f"3. CONCRETUDE E DETALHES TÁTEIS:\n"
            f"   - Extraia detalhes sensoriais e provas empíricas (nomes de lugares, datas cruciais, temperaturas, tensões, números reais ou ferramentas do ofício).\n"
            f"   - Evite listas de dados secos: formate os casos com contexto de drama ou desafio prático.\n"
            f"4. CATÁLOGO DE CASOS E ARMADILHAS PRÁTICAS:\n"
            f"   - Forneça de 6 a 10 estudos de caso e armadilhas reais onde pessoas inteligentes falharam ou onde um método salvou o dia.\n\n"
            f"Responda OBRIGATORIAMENTE em JSON válido com esta estrutura exata:\n"
            f"{{\n"
            f'  "evidence_ledger": {{\n'
            f'    "canonical_concepts": ["Conceito central 1 e por que ele importa", "Conceito 2..."],\n'
            f'    "hard_metrics_and_data": ["Dado/métrica concreta 1 com contexto dramático", "Métrica 2..."],\n'
            f'    "named_entities": ["Personagem/Local/Entidade real 1", "Entidade 2..."],\n'
            f'    "case_study_material": ["História/Causo Real 1 com o dilema e o desfecho", "Caso 2..."]\n'
            f'  }},\n'
            f'  "fact_matrix_markdown": "# DOSSIÊ DE BASTIDORES E EVIDÊNCIAS PRÁTICAS\\n\\n[Síntese em Markdown com crônicas reais, dados e catálogo de armadilhas da prática]"\n'
            f"}}"
        )

        evidence_ledger: Dict[str, Any] = {}
        fact_matrix = ""
        try:
            from app.services.llm_gateway import LLMGateway
            from json_repair import repair_json
            synth_resp = await LLMGateway.generate_text(
                "Você é um pesquisador e roteirista investigativo que responde estritamente em JSON.",
                synthesis_prompt,
                max_tokens=2600,
                timeout=75
            )
            synth_data = json.loads(repair_json(synth_resp.strip()))
            evidence_ledger = synth_data.get("evidence_ledger", {})
            fact_matrix = synth_data.get("fact_matrix_markdown", "")
        except Exception as e:
            logger.warning(f"Fallback para síntese direta de fontes e ledger: {e}")
            fact_matrix = "\n".join([f"### {s['title']}\nURL: {s['url']}\n{s['text'][:1000]}" for s in collected_sources])
            evidence_ledger = {
                "canonical_concepts": [topic],
                "hard_metrics_and_data": [],
                "named_entities": [topic],
                "case_study_material": []
            }

        # Formata o Dossiê de Bastidores no topo para os redatores
        ledger_text = json.dumps(evidence_ledger, ensure_ascii=False, indent=2)
        final_dossier = (
            f"# DOSSIÊ DE BASTIDORES E EVIDÊNCIAS REAIS: '{topic.upper()}'\n"
            f"> **DIRETRIZ NARRATIVA:** Utilize estes causos, personagens e detalhes concretos como combustível vivo da história. "
            f"Nunca liste dados secos; transforme cada fato em parte da trama explicativa.\n\n"
            f"```json\n{ledger_text}\n```\n\n"
            f"{fact_matrix}\n\n"
            f"## Bibliografia e Fontes Auditadas\n"
            + "\n".join([
                f"- **[{s['title']}]({s['url']})** ({s['domain']}) {'[Livro Archive.org]' if s.get('type') == 'book' else '[Web]'}"
                for s in collected_sources
            ])
        )

        result_payload = (final_dossier, sources_metadata, evidence_ledger)
        self._cache[cache_key] = result_payload
        return result_payload


    def build_dossier(self, topic: str, focus_keywords: Optional[List[str]] = None) -> str:
        """Método síncrono legado para compatibilidade retroativa."""
        cache_key = f"{topic.lower().strip()}_{'-'.join(focus_keywords or [])}"
        if cache_key in self._cache:
            return self._cache[cache_key][0]
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Se já estiver em loop assíncrono, executa com fallback direto
                pass
        except Exception:
            pass
        dossier, _ = asyncio.run(self.build_dossier_async(topic, focus_keywords))
        return dossier

# Instância singleton
research_engine = TriviumResearchEngine()
