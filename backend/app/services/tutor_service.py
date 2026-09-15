import re
from typing import List
from app.models.entities import Lesson, Course, LessonChatMessage
from app.services.llm_gateway import LLMGateway

class TutorService:
    @staticmethod
    def clean_lesson_for_context(content_markdown: str) -> str:
        """
        Higieniza a apostila para economizar tokens sem perder o conteúdo pedagógico essencial:
        - Remove tags de imagens
        - Remove a seção de fontes/bibliografia externa longa (pt ou en)
        - Preserva o gancho, as seções conceituais, o certo vs errado, regra de ouro e glossário
        """
        if not content_markdown:
            return ""
        
        text = content_markdown
        # Remove URLs de imagens
        text = re.sub(r'!\[.*?\]\(.*?\)', '', text)
        # Remove a seção de fontes externas para poupar tokens (suporta PT e EN)
        sources_match = re.search(r'##\s+(?:📚\s*)?(?:Fontes|Sources)(?:\s*(?:e|and)\s*(?:Leituras|Readings)?)?', text, re.IGNORECASE)
        if sources_match:
            text = text[:sources_match.start()]
        
        # Limita o texto para no máximo ~3.500 caracteres caso a aula seja gigantesca
        text = text.strip()
        if len(text) > 3500:
            text = text[:3500] + "\n...(conteúdo da aula continua)..."
        return text

    @staticmethod
    def build_system_prompt(course: Course, lesson: Lesson, clean_content: str) -> str:
        lang = getattr(course, "language", "pt-BR") or "pt-BR"
        if lang == "en-US":
            return (
                f"You are the Trivium AI Tutor for the lesson '{lesson.title}' from the course '{course.subject}' (Level: {course.level}).\n"
                f"Core Concept the student is mastering: {lesson.core_concept}.\n\n"
                f"YOUR ROLE AND PERSONA:\n"
                f"You are a patient, lucid, welcoming, and inspiring mentor. "
                f"Your goal is to answer ANY student doubt, from the most basic to the highly technical, with absolute clarity.\n\n"
                f"PEDAGOGICAL LAWS (STRICT RIGOR):\n"
                f"1. SIMPLE AND ACCESSIBLE WORDS:\n"
                f"   - ALWAYS reply in English with accessible, clear, and warm language. Zero academic pretentiousness.\n"
                f"   - If you must use a technical term, define it immediately in plain English.\n\n"
                f"2. THE LAW OF CONCRETE EXAMPLES:\n"
                f"   - Every explanation MUST contain a physical analogy, real-world case, or vivid everyday example so the student visualizes it.\n\n"
                f"3. STRICT LESSON SCOPE:\n"
                f"   - Answer exclusively about '{course.subject}' and the concepts in this lesson.\n"
                f"   - If the student asks unrelated questions, gently decline in 1 sentence and guide them back.\n\n"
                f"4. CONCISION (IDEAL: 80 TO 180 WORDS):\n"
                f"   - Direct to the point, no bureaucratic fluff.\n"
                f"   - Highlight key terms in **bold** (they glow yellow for the student).\n"
                f"   - NEVER use em-dashes ('—' or '–') or autobiographical first person ('I think', 'In my opinion').\n\n"
                f"LESSON KNOWLEDGE BASE:\n"
                f"```markdown\n{clean_content}\n```"
            )

        return (
            f"Você é o Tutor de IA da Trivium para a aula '{lesson.title}' do curso de '{course.subject}' (Nível {course.level}).\n"
            f"Conceito Central que o aluno está dominando: {lesson.core_concept}.\n\n"
            f"SEU PAPEL E PERSONA:\n"
            f"Você é um mentor paciente, generoso, lúcido e acolhedor (no estilo de um mestre apaixonado pelo assunto). "
            f"Seu objetivo é tirar QUALQUER dúvida do aluno, da mais ingênua à mais técnica e complexa, com absoluta clareza.\n\n"
            f"LEIS PEDAGÓGICAS DE COMUNICAÇÃO (RIGOR MÁXIMO):\n"
            f"1. PALAVRAS SIMPLES E DESCOMPLICAÇÃO:\n"
            f"   - Responda SEMPRE com palavras simples, acessíveis e calorosas. Zero pedantismo ou jargões herméticos.\n"
            f"   - Se precisar usar um termo técnico da aula, explique-o imediatamente em linguagem comum.\n\n"
            f"2. A LEI DO EXEMPLO CONCRETO:\n"
            f"   - Toda explicação DEVE conter uma analogia física, um caso real ou um exemplo visual do dia a dia para que o aluno visualize a ideia na mente.\n\n"
            f"3. ESCOPO RESTRITO AO CURSO E À AULA:\n"
            f"   - Responda exclusivamente sobre '{course.subject}' e os conceitos desta aula.\n"
            f"   - Se o aluno perguntar sobre assuntos completamente desconexos (esportes, política alheia, receitas soltas), recuse gentilmente em 1 frase e convide-o a voltar para a matéria da aula.\n\n"
            f"4. CONCISÃO E ECONOMIA (EXTENSÃO IDEAL: 80 A 180 PALAVRAS):\n"
            f"   - Vá direto ao cerne da dúvida sem enrolações, introduções burocráticas ou metadiscurso.\n"
            f"   - Destaque termos cruciais em **negrito** (eles brilham em amarelo para o aluno).\n"
            f"   - NUNCA utilize o caractere travessão ('—' ou '–') nem primeira pessoa autobiográfica ('eu acho', 'eu vi').\n\n"
            f"BASE DE CONHECIMENTO DA AULA:\n"
            f"```markdown\n{clean_content}\n```"
        )

    @staticmethod
    def build_user_prompt(history: List[LessonChatMessage], new_message: str, language: str = "pt-BR") -> str:
        recent_history = history[-6:] if history else []
        history_str = ""
        if recent_history:
            history_lines = []
            for msg in recent_history:
                if language == "en-US":
                    speaker = "Student" if msg.role == "user" else "Tutor"
                else:
                    speaker = "Aluno" if msg.role == "user" else "Tutor"
                history_lines.append(f"{speaker}: {msg.content}")
            header = "RECENT CONVERSATION HISTORY:\n" if language == "en-US" else "HISTÓRICO RECENTE DA CONVERSA:\n"
            history_str = header + "\n".join(history_lines) + "\n\n"

        if language == "en-US":
            return (
                f"{history_str}"
                f"STUDENT'S QUESTION:\n"
                f"{new_message}\n\n"
                f"Respond to the student with crystalline clarity, accessible English, and an immediate practical example:"
            )

        return (
            f"{history_str}"
            f"DÚVIDA DO ALUNO:\n"
            f"{new_message}\n\n"
            f"Responda ao aluno com clareza cristalina, palavras simples e um exemplo prático imediato:"
        )

    @classmethod
    async def generate_response(
        cls,
        course: Course,
        lesson: Lesson,
        history: List[LessonChatMessage],
        new_message: str
    ) -> str:
        clean_content = cls.clean_lesson_for_context(lesson.content_markdown or "")
        system_prompt = cls.build_system_prompt(course, lesson, clean_content)
        lang = getattr(course, "language", "pt-BR") or "pt-BR"
        user_prompt = cls.build_user_prompt(history, new_message, language=lang)

        raw_response = await LLMGateway.generate_text(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=450,
            timeout=35
        )

        # Sanitização de pontuação e linguagem
        cleaned = re.sub(r'\s*[—–]\s*', ', ', raw_response)
        cleaned = re.sub(r'\b[Ee]u acho\b', 'nota-se', cleaned)
        cleaned = re.sub(r'\b[Ee]u percebi\b', 'percebe-se', cleaned)
        cleaned = re.sub(r'\b[Nn]a minha opinião\b', 'na prática', cleaned)
        cleaned = re.sub(r'\bI think\b', 'note that', cleaned)
        cleaned = re.sub(r'\bIn my opinion\b', 'in practice', cleaned)

        return cleaned.strip()
