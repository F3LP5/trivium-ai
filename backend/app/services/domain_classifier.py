import json
import logging
import re
from typing import Dict, Any
from app.services.llm_gateway import LLMGateway
from json_repair import repair_json

logger = logging.getLogger(__name__)

class DomainClassifier:
    """
    Classificador Universal de Domínios e Orquestrador Epistemológico (Padrão NotebookLM / Perplexity):
    Infere a natureza ontológica e pedagógica de qualquer assunto humano a partir de primeiros princípios,
    gerando o contrato de persona, tom de voz, métricas de evidência e arquétipos visuais.
    """

    DEFAULT_PROFILE: Dict[str, Any] = {
        "dynamic_domain_name": "Conhecimento Prático e Fundamentos Aplicados",
        "persona_title": "Mentor Especialista e Comunicador Apaixonado",
        "tone_of_voice": "Tom conversacional, cativante, empático e cristalino. Fala diretamente com o aluno ('você'), usa metáforas visuais do dia a dia, zero burocracia acadêmica e explica a intuição física como um mentor amigo apaixonado pela matéria.",
        "evaluation_rubric_core": "Avalie a compreensão intuitiva dos mecanismos fundamentais e a capacidade de raciocínio prático diante de situações reais.",
        "visual_archetype": "Diagramas esquemáticos clássicos, instrumentos de precisão, mapas conceituais e ferramentas emblemáticas da disciplina",
        "case_study_format": "História real ou dilema prático que ilustra de forma fascinante o conceito em ação no cotidiano."
    }

    @classmethod
    async def classify(cls, topic: str, level: str = "Básico") -> Dict[str, Any]:
        system_prompt = (
            "Você é o Orquestrador Epistemológico e Pedagógico da Trivium.\n"
            "Sua missão é desenhar a alma pedagógica de um curso envolvente, fascinante e memorável (Padrão Masterclass / Coursera / Hitch).\n"
            "O objetivo central de QUALQUER curso na Trivium é ser GOSTOSO DE LER, CATIVANTE E FÁCIL DE ENTENDER DO ZERO ABSOLUTO, mesmo em temas técnicos densos.\n\n"
            "Diretrizes obrigatórias para o perfil:\n"
            "1. Persona: Um mentor carismático, apaixonado e acessível, que domina o assunto profundamente mas fala de forma simples e envolvente.\n"
            "2. Tom de Voz: OBRIGATORIAMENTE conversacional, fluido, convidativo e visual. Proibido tom de relatório burocrático ou enciclopédia fria.\n\n"
            "Retorne ESTRITAMENTE um objeto JSON válido (sem markdown extra) com a seguinte estrutura:\n"
            "{\n"
            '  "dynamic_domain_name": "Nome descritivo e instigante do campo",\n'
            '  "persona_title": "O mentor ideal (ex: \'Engenheiro Apaixonado e Mentor Prático\')",\n'
            '  "tone_of_voice": "Instrução enfática de escrita: conversa direta com o leitor, metáforas vívidas, ritmo agradável e clareza absoluta.",\n'
            '  "visual_archetype": "Descreva em inglês de 1 a 3 objetos físicos tangíveis da disciplina no estilo gravura editorial clássica (máximo 4 elementos visuais). Sem pessoas nem rostos.",\n'
            '  "case_study_format": "Uma história ou cenário prático real e intrigante que demonstre o conceito em ação."\n'
            "}"
        )
        user_prompt = f"Tema solicitado: '{topic}'\nNível de profundidade: '{level}'"

        try:
            raw_response = await LLMGateway.generate_text(
                system_prompt,
                user_prompt,
                max_tokens=500,
                timeout=25
            )
            raw_clean = raw_response.strip()
            # Localiza JSON
            start = raw_clean.find("{")
            end = raw_clean.rfind("}")
            if start != -1 and end != -1 and end > start:
                raw_clean = raw_clean[start:end+1]

            data = json.loads(repair_json(raw_clean))
            profile = {
                "dynamic_domain_name": str(data.get("dynamic_domain_name") or cls.DEFAULT_PROFILE["dynamic_domain_name"]).strip(),
                "persona_title": str(data.get("persona_title") or cls.DEFAULT_PROFILE["persona_title"]).strip(),
                "tone_of_voice": str(data.get("tone_of_voice") or cls.DEFAULT_PROFILE["tone_of_voice"]).strip(),
                "evaluation_rubric_core": str(data.get("evaluation_rubric_core") or cls.DEFAULT_PROFILE["evaluation_rubric_core"]).strip(),
                "visual_archetype": str(data.get("visual_archetype") or cls.DEFAULT_PROFILE["visual_archetype"]).strip(),
                "case_study_format": str(data.get("case_study_format") or cls.DEFAULT_PROFILE["case_study_format"]).strip(),
            }
            logger.info(f"[DomainClassifier] Perfil gerado para '{topic}': {profile['dynamic_domain_name']} ({profile['persona_title']})")
            return profile
        except Exception as e:
            logger.warning(f"[DomainClassifier] Fallback heurístico ativado para '{topic}': {e}")
            fallback = dict(cls.DEFAULT_PROFILE)
            fallback["dynamic_domain_name"] = f"Estudos Especializados em {topic}"
            fallback["persona_title"] = f"Especialista e Pesquisador em {topic}"
            return fallback
