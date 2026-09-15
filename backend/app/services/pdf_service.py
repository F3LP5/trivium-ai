import os
import re
import json
import markdown
from playwright.async_api import async_playwright

CSS_STYLE = """
@page {
    size: 600px 848px;
    margin: 0;
}
* { box-sizing: border-box; }
body {
    margin: 0;
    font-family: 'Helvetica Neue', Arial, -apple-system, BlinkMacSystemFont, sans-serif;
    background: #000000;
    color: #ffffff;
}
.page {
    width: 600px;
    height: 848px;
    position: relative;
    padding: 40px 48px 36px 48px;
    page-break-after: always;
}
.page:last-child { page-break-after: auto; }

.brand { 
    font-size: 11px; 
    letter-spacing: 0.5px; 
    color: #ffffff; 
    text-transform: lowercase;
    font-weight: 500;
}

.logo {
    position: absolute;
    top: 34px;
    right: 44px;
    width: 36px;
    height: 36px;
}
.logo svg { width: 100%; height: 100%; }

.side-label {
    position: absolute;
    top: 90px;
    right: 26px;
    writing-mode: vertical-rl;
    font-size: 9px;
    letter-spacing: 1.2px;
    color: #ffffff;
    opacity: 0.85;
    text-transform: lowercase;
}

.title-block {
    margin-top: 240px;
    margin-bottom: 24px;
}
.kicker {
    font-size: 26px;
    color: #ffffff;
    font-weight: 400;
    display: inline;
    margin-right: 6px;
}
.title {
    font-size: 25px;
    font-weight: 800;
    line-height: 1.25;
    display: inline;
    color: #ffffff;
    letter-spacing: -0.3px;
}
.title b { font-weight: 800; color: #ffffff; }

.columns {
    display: flex;
    gap: 28px;
    margin-top: 18px;
}
.col {
    flex: 1;
    font-size: 11.5px;
    line-height: 1.6;
    color: #f2f2f2;
    text-align: justify;
}
.col b, .col strong { font-weight: 700; color: #ffffff; }

.highlight {
    position: absolute;
    left: 48px;
    right: 48px;
    bottom: 64px;
    background: #f5ea0e;
    color: #000000;
    font-weight: 700;
    font-size: 14px;
    line-height: 1.35;
    padding: 16px 20px;
}
.highlight.small {
    font-size: 12px;
    padding: 14px 18px;
}
.highlight b, .highlight strong {
    font-weight: 800;
    color: #000000;
}

.page-number {
    position: absolute;
    bottom: 20px;
    right: 44px;
    font-size: 10px;
    color: #ffffff;
    font-weight: 500;
}

.attribution {
    font-size: 12px;
    line-height: 1.55;
    color: #f2f2f2;
    margin-bottom: 8px;
    margin-top: 60px;
    max-width: 440px;
}
.attribution b, .attribution strong { color: #ffffff; font-weight: 700; }
.quote-block { margin-top: 32px; }
.quote-text {
    font-size: 21px;
    line-height: 1.3;
    font-weight: 400;
    color: #ffffff;
    margin-top: 14px;
}
"""

CONTENT_TEMPLATE = """
<div class="page">
    <div class="brand">{brand}</div>
    <div class="logo">{logo_svg}</div>
    <div class="side-label">{footer_label}</div>

    <div class="title-block"><span class="kicker">{kicker}</span><span class="title">{title_html}</span></div>

    <div class="columns">
        <div class="col">{col1}</div>
        <div class="col">{col2}</div>
    </div>

    <div class="highlight small">{highlight}</div>
    <div class="page-number">{page_number}</div>
</div>
"""

QUOTE_TEMPLATE = """
<div class="page">
    <div class="brand">{brand}</div>
    <div class="logo">{logo_svg}</div>
    <div class="side-label">{footer_label}</div>

    <div class="attribution">{attribution_html}</div>
    <div class="quote-block">
        <div class="quote-text">{quote_text}</div>
    </div>

    <div class="columns" style="margin-top:36px;">
        <div class="col">{col1}</div>
        <div class="col">{col2}</div>
    </div>

    <div class="highlight small">{highlight}</div>
    <div class="page-number">{page_number}</div>
</div>
"""

LOGO_SVG = """<svg viewBox="0 0 40 40" xmlns="http://www.w3.org/2000/svg">
<polygon points="20,2 37,14 30,36 10,36 3,14" fill="none" stroke="#ffffff" stroke-width="1.3"/>
<polygon points="20,2 3,14 20,20" fill="none" stroke="#ffffff" stroke-width="0.9"/>
<polygon points="20,2 37,14 20,20" fill="none" stroke="#ffffff" stroke-width="0.9"/>
<polygon points="3,14 10,36 20,20" fill="none" stroke="#ffffff" stroke-width="0.9"/>
<polygon points="37,14 30,36 20,20" fill="none" stroke="#ffffff" stroke-width="0.9"/>
</svg>"""

class PDFService:
    @staticmethod
    def _convert_markdown_to_booklet_dict(title: str, module_title: str, content_markdown: str) -> dict:
        """
        Converte o markdown da aula em páginas perfeitamente estruturadas no padrão Trivium:
        - Página 1 (content): Fundamentação e conceito central
        - Página 2 (quote/aplicação): Prática técnica profunda e provocação socrática
        """
        paragraphs = [p.strip() for p in content_markdown.split("\n\n") if p.strip()]
        
        # Filtra títulos markdown crus e quaisquer hashtags duplicadas
        clean_paras = []
        for p in paragraphs:
            # Remove qualquer marcador de hashtag no início de linhas (ex: '### ###', '### ##', '#')
            cleaned = re.sub(r'^[ \t]*#+\s*', '', p, flags=re.MULTILINE).strip()
            # Remove marcadores de citação no início caso estejam combinados com hashtags
            cleaned = re.sub(r'^[ \t]*>[ \t]*#*\s*', '', cleaned, flags=re.MULTILINE).strip()
            if cleaned:
                clean_paras.append(cleaned)

        p1_col1 = clean_paras[0] if len(clean_paras) > 0 else "Fundamentos da aula."
        p1_col2 = clean_paras[1] if len(clean_paras) > 1 else p1_col1
        p1_highlight = clean_paras[2] if len(clean_paras) > 2 else "O domínio técnico nasce da prática deliberada e do rigor conceitual."
        if len(p1_highlight) > 140:
            p1_highlight = p1_highlight[:137] + "..."

        p2_attribution = f"Aplicação Prática no <b>{module_title}</b>:"
        p2_quote = f"Como dominar {title.lower()} na prática?"
        p2_col1 = clean_paras[3] if len(clean_paras) > 3 else (clean_paras[0] if clean_paras else "")
        p2_col2 = clean_paras[4] if len(clean_paras) > 4 else (clean_paras[1] if len(clean_paras) > 1 else "")
        p2_highlight = clean_paras[5] if len(clean_paras) > 5 else "A excelência não é um ato isolado, mas um hábito de consistência técnica."
        if len(p2_highlight) > 140:
            p2_highlight = p2_highlight[:137] + "..."

        return {
            "brand": "trivium academy",
            "footer_label": "rigor, lógica e maestria",
            "pages": [
                {
                    "type": "content",
                    "kicker": "?",
                    "title_html": f"{title.lower()}",
                    "columns": [p1_col1, p1_col2],
                    "highlight_block": p1_highlight,
                    "page_number": 1
                },
                {
                    "type": "quote",
                    "attribution_html": p2_attribution,
                    "quote_text": p2_quote,
                    "columns": [p2_col1, p2_col2],
                    "highlight_block": p2_highlight,
                    "page_number": 2
                }
            ]
        }

    @staticmethod
    def render_page(page: dict, brand: str, footer_label: str) -> str:
        cols = page.get("columns", ["", ""])
        if page.get("type") == "quote":
            return QUOTE_TEMPLATE.format(
                brand=brand,
                footer_label=footer_label,
                logo_svg=LOGO_SVG,
                attribution_html=page.get("attribution_html", ""),
                quote_text=page.get("quote_text", ""),
                col1=cols[0] if len(cols) > 0 else "",
                col2=cols[1] if len(cols) > 1 else "",
                highlight=page.get("highlight_block", ""),
                page_number=page.get("page_number", ""),
            )
        else:
            return CONTENT_TEMPLATE.format(
                brand=brand,
                footer_label=footer_label,
                logo_svg=LOGO_SVG,
                kicker=page.get("kicker", "?"),
                title_html=page.get("title_html", ""),
                col1=cols[0] if len(cols) > 0 else "",
                col2=cols[1] if len(cols) > 1 else "",
                highlight=page.get("highlight_block", ""),
                page_number=page.get("page_number", ""),
            )

    @staticmethod
    async def render_lesson_pdf(title: str, module_title: str, content_markdown: str, output_path: str):
        # Tenta carregar se o content_markdown já for um JSON de booklet
        booklet_data = None
        if content_markdown.strip().startswith("{") and '"pages"' in content_markdown:
            try:
                booklet_data = json.loads(content_markdown)
            except Exception:
                booklet_data = None
        
        if not booklet_data:
            booklet_data = PDFService._convert_markdown_to_booklet_dict(title, module_title, content_markdown)

        brand = booklet_data.get("brand", "trivium academy")
        footer_label = booklet_data.get("footer_label", "rigor, lógica e maestria")
        pages = booklet_data.get("pages", [])

        pages_html = "\n".join(PDFService.render_page(p, brand, footer_label) for p in pages)
        full_html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
{CSS_STYLE}
</style>
</head>
<body>
{pages_html}
</body>
</html>"""

        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.set_content(full_html, wait_until="networkidle")
            await page.pdf(
                path=output_path,
                width="600px",
                height="848px",
                print_background=True,
                margin={"top": "0px", "right": "0px", "bottom": "0px", "left": "0px"}
            )
            await browser.close()

        return output_path
