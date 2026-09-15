from pydantic import BaseModel, Field, model_validator
from typing import List, Optional, Any, Union

class MultipleChoiceOption(BaseModel):
    label: str = Field(default="A", description="A, B ou C")
    text: str = Field(default="", description="Texto da alternativa")
    is_correct: bool = Field(default=False, description="True se correta")

    @model_validator(mode="before")
    @classmethod
    def parse_option(cls, data: Any) -> Any:
        if isinstance(data, str):
            return {"label": "A", "text": data, "is_correct": False}
        if isinstance(data, dict):
            lbl = data.get("label") or data.get("letter") or data.get("id") or "A"
            txt = data.get("text") or data.get("opcao") or data.get("texto") or ""
            corr = bool(data.get("is_correct") or data.get("correct") or data.get("correta") or False)
            return {"label": str(lbl)[:1].upper(), "text": str(txt), "is_correct": corr}
        return data

class MultipleChoiceQuestion(BaseModel):
    question: str = Field(default="Pergunta", description="Enunciado")
    options: List[MultipleChoiceOption] = Field(default_factory=list, description="Opcoes")
    explanation: str = Field(default="", description="Explicacao")

    @model_validator(mode="before")
    @classmethod
    def parse_mcq(cls, data: Any) -> Any:
        if isinstance(data, dict):
            q = data.get("question") or data.get("pergunta") or data.get("enunciado") or "Pergunta"
            expl = data.get("explanation") or data.get("explicacao") or data.get("justificativa") or ""
            raw_opts = data.get("options") or data.get("alternativas") or data.get("choices") or []
            
            # Se vier lista de strings ["A: texto", "B: texto"] ou dict {"A": "texto", "B": "texto"}
            parsed_opts = []
            labels = ["A", "B", "C", "D", "E"]
            if isinstance(raw_opts, dict):
                corr_key = str(data.get("correct") or data.get("answer") or data.get("correct_answer") or "A").strip()[:1].upper()
                for k, v in raw_opts.items():
                    lbl = str(k)[:1].upper()
                    parsed_opts.append({"label": lbl, "text": str(v), "is_correct": (lbl == corr_key)})
            elif isinstance(raw_opts, list):
                for idx, item in enumerate(raw_opts):
                    if isinstance(item, str):
                        parsed_opts.append({"label": labels[idx % len(labels)], "text": item, "is_correct": (idx == 0)})
                    elif isinstance(item, dict):
                        lbl = item.get("label") or labels[idx % len(labels)]
                        txt = item.get("text") or item.get("opcao") or ""
                        corr = bool(item.get("is_correct") or item.get("correct") or False)
                        parsed_opts.append({"label": str(lbl), "text": str(txt), "is_correct": corr})
            
            # Garante que pelo menos 1 opção seja marcada como correta se nenhuma estiver
            if parsed_opts and not any(o["is_correct"] for o in parsed_opts):
                parsed_opts[0]["is_correct"] = True

            return {"question": str(q), "options": parsed_opts, "explanation": str(expl)}
        return data

class FillInBlankQuestion(BaseModel):
    sentence_with_blank: str = Field(default="", description="Frase com [LACUNA]")
    correct_word: str = Field(default="", description="Palavra correta")
    hint: str = Field(default="", description="Dica")

    @model_validator(mode="before")
    @classmethod
    def parse_blank(cls, data: Any) -> Any:
        if isinstance(data, dict):
            s = data.get("sentence_with_blank") or data.get("sentence") or data.get("frase") or data.get("texto") or ""
            w = data.get("correct_word") or data.get("word") or data.get("resposta") or data.get("lacuna") or ""
            h = data.get("hint") or data.get("dica") or ""
            if "[LACUNA]" not in s and "___" in s:
                s = s.replace("___", "[LACUNA]")
            return {"sentence_with_blank": str(s), "correct_word": str(w), "hint": str(h)}
        return data

class DiscursiveQuestion(BaseModel):
    question: str = Field(default="", description="Pergunta discursiva")
    evaluation_rubric: List[str] = Field(default_factory=list, description="Topicos da rubrica")

    @model_validator(mode="before")
    @classmethod
    def parse_disc(cls, data: Any) -> Any:
        if isinstance(data, dict):
            q = data.get("question") or data.get("pergunta") or data.get("enunciado") or ""
            rubric = data.get("evaluation_rubric") or data.get("rubric") or data.get("rubrica") or data.get("criterios") or []
            if isinstance(rubric, str):
                rubric = [rubric]
            return {"question": str(q), "evaluation_rubric": [str(r) for r in rubric]}
        if hasattr(data, "question"):
            return {
                "question": str(getattr(data, "question", "")),
                "evaluation_rubric": [str(r) for r in getattr(data, "evaluation_rubric", [])]
            }
        return data

# =========================================================================
# MINI-SIMULADOR DE IMPACTO EM 2 TURNOS (SANDBOX DE CENÁRIO VIVO)
# =========================================================================

class IndicatorState(BaseModel):
    name: str = Field(default="Indicador", description="Nome do indicador")
    value_type: str = Field(default="percentage", description="'percentage' ou 'label'")
    value: Union[int, str] = Field(default=50, description="Ex: 85 (int se percentage) ou 'Crítico' (str se label)")
    color_hint: Optional[str] = Field(default="yellow", description="'green', 'yellow', 'red'")

    @model_validator(mode="before")
    @classmethod
    def parse_indicator(cls, data: Any) -> Any:
        if isinstance(data, dict):
            n = data.get("name") or data.get("nome") or "Indicador"
            vt = data.get("value_type") or data.get("tipo") or ("label" if isinstance(data.get("value"), str) and not str(data.get("value", "")).isdigit() else "percentage")
            val = data.get("value") or data.get("valor") or (50 if vt == "percentage" else "Moderado")
            col = data.get("color_hint") or data.get("cor") or "yellow"
            return {"name": str(n), "value_type": str(vt), "value": val, "color_hint": str(col)}
        return data

class SimulationTurn2Option(BaseModel):
    id: str = Field(default="A", description="A, B ou C")
    text: str = Field(default="", description="Ação de mitigação/ajuste fino")
    outcome_story: str = Field(default="", description="Desfecho detalhado do desdobramento")
    final_indicators: List[IndicatorState] = Field(default_factory=list)
    verdict_summary: str = Field(default="", description="Veredito e análise dos trade-offs")
    is_success: bool = Field(default=True, description="True se a operação foi sustentável")

    @model_validator(mode="before")
    @classmethod
    def parse_opt2(cls, data: Any) -> Any:
        if isinstance(data, dict):
            i = str(data.get("id") or data.get("letra") or "A")[:1].upper()
            t = data.get("text") or data.get("texto") or data.get("opcao") or ""
            story = data.get("outcome_story") or data.get("desfecho") or data.get("resultado") or ""
            inds = data.get("final_indicators") or data.get("indicadores_finais") or []
            verd = data.get("verdict_summary") or data.get("veredito") or data.get("resumo") or ""
            succ = bool(data.get("is_success") if "is_success" in data else True)
            return {
                "id": i,
                "text": str(t),
                "outcome_story": str(story),
                "final_indicators": inds,
                "verdict_summary": str(verd),
                "is_success": succ
            }
        return data

class SimulationTurn1Option(BaseModel):
    id: str = Field(default="A", description="A, B ou C")
    text: str = Field(default="", description="Descrição da ação primária")
    reaction_story: str = Field(default="", description="Desdobramento imediato e disparo do efeito colateral imprevisto")
    updated_indicators: List[IndicatorState] = Field(default_factory=list)
    turn2_prompt: str = Field(default="Como você deseja conter este efeito colateral ou otimizar o ganho final?", description="Pergunta do turno 2")
    turn2_options: List[SimulationTurn2Option] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def parse_opt1(cls, data: Any) -> Any:
        if isinstance(data, dict):
            i = str(data.get("id") or data.get("letra") or "A")[:1].upper()
            t = data.get("text") or data.get("texto") or data.get("opcao") or ""
            react = data.get("reaction_story") or data.get("reacao") or data.get("efeito_colateral") or ""
            inds = data.get("updated_indicators") or data.get("indicadores_atualizados") or []
            p2 = data.get("turn2_prompt") or data.get("pergunta_turno2") or "Como você deseja conter este efeito colateral?"
            opts2 = list(data.get("turn2_options") or data.get("opcoes_turno2") or data.get("turn2") or data.get("options") or [])
            if not opts2 and isinstance(data.get("turn2"), dict):
                t2 = data.get("turn2")
                p2 = t2.get("prompt") or p2
                opts2 = list(t2.get("options") or [])

            # GARANTIA ESTRUTURAL: Turno 2 DEVE conter rigorosamente 3 alternativas (A, B e C)
            target_ids = ["A", "B", "C"]
            # Sanitiza IDs existentes
            for idx, op in enumerate(opts2):
                if isinstance(op, dict) and idx < len(target_ids):
                    op["id"] = target_ids[idx]

            default_opt2_templates = [
                {
                    "id": "A",
                    "text": "Implementar contenção técnica estruturada e calibrar checkpoints essenciais",
                    "outcome_story": "A contenção técnica equilibrou a operação com previsibilidade e segurança de ponta a ponta.",
                    "final_indicators": [
                        {"name": "Estabilidade", "value_type": "percentage", "value": 90, "color_hint": "green"},
                        {"name": "Eficiência Operacional", "value_type": "percentage", "value": 85, "color_hint": "green"},
                        {"name": "Margem de Risco", "value_type": "percentage", "value": 15, "color_hint": "green"}
                    ],
                    "verdict_summary": "Operação equilibrada com maturidade e eficácia.",
                    "is_success": True
                },
                {
                    "id": "B",
                    "text": "Acelerar sem novas checagens priorizando velocidade imediata",
                    "outcome_story": "A sobrecarga sem checagens acumulou dívida técnica e instabilidade no fluxo.",
                    "final_indicators": [
                        {"name": "Estabilidade", "value_type": "percentage", "value": 55, "color_hint": "yellow"},
                        {"name": "Eficiência Operacional", "value_type": "percentage", "value": 75, "color_hint": "yellow"},
                        {"name": "Margem de Risco", "value_type": "percentage", "value": 60, "color_hint": "yellow"}
                    ],
                    "verdict_summary": "Ganhos imediatos ao custo de maior volatilidade operacional.",
                    "is_success": False
                },
                {
                    "id": "C",
                    "text": "Adotar monitoramento contínuo por telemetria e ajustes incrementais orientados por métricas",
                    "outcome_story": "O acompanhamento em tempo real ofereceu visibilidade holística e reação preventiva rápida.",
                    "final_indicators": [
                        {"name": "Estabilidade", "value_type": "percentage", "value": 88, "color_hint": "green"},
                        {"name": "Eficiência Operacional", "value_type": "percentage", "value": 88, "color_hint": "green"},
                        {"name": "Margem de Risco", "value_type": "percentage", "value": 14, "color_hint": "green"}
                    ],
                    "verdict_summary": "Abordagem orientada por dados com sustentabilidade comprovada.",
                    "is_success": True
                }
            ]

            while len(opts2) < 3:
                next_idx = len(opts2)
                opts2.append(default_opt2_templates[next_idx])

            return {
                "id": i,
                "text": str(t),
                "reaction_story": str(react),
                "updated_indicators": inds,
                "turn2_prompt": str(p2),
                "turn2_options": opts2[:3]
            }
        return data

class SimulationSandbox(BaseModel):
    context: str = Field(default="", description="Situação prática resumida (2 a 3 frases) contextualizada na matéria da aula")
    initial_indicators: List[IndicatorState] = Field(default_factory=list, description="3 indicadores iniciais")
    turn1_prompt: str = Field(default="Qual é a sua ação estratégica primária?", description="Pergunta do turno 1")
    turn1_options: List[SimulationTurn1Option] = Field(default_factory=list, description="3 caminhos de ação")

    @model_validator(mode="before")
    @classmethod
    def parse_sim(cls, data: Any) -> Any:
        if isinstance(data, dict):
            ctx = data.get("context") or data.get("contexto") or data.get("cenario") or data.get("context_description") or data.get("description") or "Cenário de tomada de decisão prática aplicando os conceitos essenciais da aula."
            init_inds = data.get("initial_indicators") or data.get("indicadores_iniciais") or data.get("indicators") or data.get("indicadores") or []
            p1 = data.get("turn1_prompt") or data.get("pergunta_turno1") or data.get("prompt_turno1") or "Qual é a sua ação estratégica primária?"
            opts1 = list(data.get("turn1_options") or data.get("opcoes_turno1") or data.get("options") or data.get("turn1") or data.get("acoes") or [])

            if not opts1 and isinstance(data.get("turn1"), dict):
                t1 = data.get("turn1")
                p1 = t1.get("prompt") or p1
                opts1 = list(t1.get("options") or t1.get("turn1_options") or [])

            if not init_inds:
                init_inds = [
                    {"name": "Estabilidade", "value_type": "percentage", "value": 75, "color_hint": "green"},
                    {"name": "Eficiência Operacional", "value_type": "percentage", "value": 60, "color_hint": "yellow"},
                    {"name": "Margem de Risco", "value_type": "percentage", "value": 30, "color_hint": "green"}
                ]

            default_opt1_templates = [
                {
                    "id": "A",
                    "text": "Adotar protocolo conservador e estruturar validações controladas",
                    "reaction_story": "A abordagem reduziu a volatilidade operacional, mas gerou fila de processamento e lentidão percebida.",
                    "updated_indicators": [
                        {"name": "Estabilidade", "value_type": "percentage", "value": 90, "color_hint": "green"},
                        {"name": "Eficiência Operacional", "value_type": "percentage", "value": 50, "color_hint": "yellow"},
                        {"name": "Margem de Risco", "value_type": "percentage", "value": 15, "color_hint": "green"}
                    ],
                    "turn2_prompt": "Com a demanda crescendo, qual ajuste você faz para recuperar o ritmo sem perder controle?",
                    "turn2_options": [
                        {
                            "id": "A",
                            "text": "Automatizar pipelines de conferência e manter os checkpoints essenciais",
                            "outcome_story": "O fluxo foi otimizado com segurança, restabelecendo o ritmo e preservando a integridade.",
                            "final_indicators": [
                                {"name": "Estabilidade", "value_type": "percentage", "value": 92, "color_hint": "green"},
                                {"name": "Eficiência Operacional", "value_type": "percentage", "value": 85, "color_hint": "green"},
                                {"name": "Margem de Risco", "value_type": "percentage", "value": 10, "color_hint": "green"}
                            ],
                            "verdict_summary": "Operação equilibrada com maturidade e eficácia.",
                            "is_success": True
                        },
                        {
                            "id": "B",
                            "text": "Flexibilizar as validações para acelerar entregas",
                            "outcome_story": "A flexibilização gerou vazamento de inconsistências, elevando a dívida técnica.",
                            "final_indicators": [
                                {"name": "Estabilidade", "value_type": "percentage", "value": 55, "color_hint": "yellow"},
                                {"name": "Eficiência Operacional", "value_type": "percentage", "value": 85, "color_hint": "green"},
                                {"name": "Margem de Risco", "value_type": "percentage", "value": 50, "color_hint": "yellow"}
                            ],
                            "verdict_summary": "Ganhos pontuais de velocidade ao custo da estabilidade.",
                            "is_success": False
                        },
                        {
                            "id": "C",
                            "text": "Implantar conferência assistida por regras heurísticas e amostragem ágil",
                            "outcome_story": "A amostragem garantiu fluidez com taxa de erro residual mínima.",
                            "final_indicators": [
                                {"name": "Estabilidade", "value_type": "percentage", "value": 89, "color_hint": "green"},
                                {"name": "Eficiência Operacional", "value_type": "percentage", "value": 84, "color_hint": "green"},
                                {"name": "Margem de Risco", "value_type": "percentage", "value": 14, "color_hint": "green"}
                            ],
                            "verdict_summary": "Equilíbrio pragmático entre rigor de validação e velocidade.",
                            "is_success": True
                        }
                    ]
                },
                {
                    "id": "B",
                    "text": "Executar intervenção rápida e direta focada em rendimento imediato",
                    "reaction_story": "O rendimento disparou, mas surgiram alertas de inconsistência nos canais de monitoramento.",
                    "updated_indicators": [
                        {"name": "Estabilidade", "value_type": "percentage", "value": 50, "color_hint": "yellow"},
                        {"name": "Eficiência Operacional", "value_type": "percentage", "value": 90, "color_hint": "green"},
                        {"name": "Margem de Risco", "value_type": "percentage", "value": 45, "color_hint": "yellow"}
                    ],
                    "turn2_prompt": "Os alertas continuam crescendo. Qual ação você toma para conter o efeito colateral?",
                    "turn2_options": [
                        {
                            "id": "A",
                            "text": "Isolar componentes afetados e aplicar contenção modular",
                            "outcome_story": "A contenção conteve os erros e estabilizou o fluxo sem paralisar o sistema.",
                            "final_indicators": [
                                {"name": "Estabilidade", "value_type": "percentage", "value": 82, "color_hint": "green"},
                                {"name": "Eficiência Operacional", "value_type": "percentage", "value": 85, "color_hint": "green"},
                                {"name": "Margem de Risco", "value_type": "percentage", "value": 20, "color_hint": "green"}
                            ],
                            "verdict_summary": "Resposta rápida e eficiente mitigou o risco.",
                            "is_success": True
                        },
                        {
                            "id": "B",
                            "text": "Ignorar temporariamente os alertas e manter o throughput",
                            "outcome_story": "O acúmulo de inconsistências causou interrupção parcial do serviço.",
                            "final_indicators": [
                                {"name": "Estabilidade", "value_type": "percentage", "value": 25, "color_hint": "red"},
                                {"name": "Eficiência Operacional", "value_type": "percentage", "value": 35, "color_hint": "red"},
                                {"name": "Margem de Risco", "value_type": "percentage", "value": 85, "color_hint": "red"}
                            ],
                            "verdict_summary": "Degradação crítica decorrente da falta de contenção.",
                            "is_success": False
                        },
                        {
                            "id": "C",
                            "text": "Ativar mitigação automatizada com telemetria em tempo real",
                            "outcome_story": "A telemetria estabilizou os nós críticos sem comprometer as entregas.",
                            "final_indicators": [
                                {"name": "Estabilidade", "value_type": "percentage", "value": 86, "color_hint": "green"},
                                {"name": "Eficiência Operacional", "value_type": "percentage", "value": 88, "color_hint": "green"},
                                {"name": "Margem de Risco", "value_type": "percentage", "value": 16, "color_hint": "green"}
                            ],
                            "verdict_summary": "Mitigação ágil assistida por dados preservou a integridade.",
                            "is_success": True
                        }
                    ]
                },
                {
                    "id": "C",
                    "text": "Executar transição híbrida com rollouts canários e observabilidade contínua",
                    "reaction_story": "A transição gradual manteve os serviços estáveis e permitiu detectar anomalias antes que atingissem a produção geral.",
                    "updated_indicators": [
                        {"name": "Estabilidade", "value_type": "percentage", "value": 85, "color_hint": "green"},
                        {"name": "Eficiência Operacional", "value_type": "percentage", "value": 75, "color_hint": "green"},
                        {"name": "Margem de Risco", "value_type": "percentage", "value": 20, "color_hint": "green"}
                    ],
                    "turn2_prompt": "Com os primeiros 20% migrados com sucesso, qual o próximo passo de consolidação?",
                    "turn2_options": [
                        {
                            "id": "A",
                            "text": "Expandir o rollout progressivamente com testes de carga automatizados",
                            "outcome_story": "A migração concluiu com 100% de integridade e alta confiabilidade operacional.",
                            "final_indicators": [
                                {"name": "Estabilidade", "value_type": "percentage", "value": 95, "color_hint": "green"},
                                {"name": "Eficiência Operacional", "value_type": "percentage", "value": 90, "color_hint": "green"},
                                {"name": "Margem de Risco", "value_type": "percentage", "value": 8, "color_hint": "green"}
                            ],
                            "verdict_summary": "Arquitetura resiliente e execução impecável.",
                            "is_success": True
                        },
                        {
                            "id": "B",
                            "text": "Acelerar a virada para 100% de uma só vez para poupar tempo",
                            "outcome_story": "O salto repentino sobrecarregou a infraestrutura auxiliar não testada.",
                            "final_indicators": [
                                {"name": "Estabilidade", "value_type": "percentage", "value": 45, "color_hint": "yellow"},
                                {"name": "Eficiência Operacional", "value_type": "percentage", "value": 60, "color_hint": "yellow"},
                                {"name": "Margem de Risco", "value_type": "percentage", "value": 65, "color_hint": "yellow"}
                            ],
                            "verdict_summary": "A pressa na fase final comprometeu os ganhos da abordagem híbrida.",
                            "is_success": False
                        },
                        {
                            "id": "C",
                            "text": "Capacitar times operacionais e consolidar documentação viva antes da ativação final",
                            "outcome_story": "O alinhamento transversal assegurou transição transparente e perene.",
                            "final_indicators": [
                                {"name": "Estabilidade", "value_type": "percentage", "value": 92, "color_hint": "green"},
                                {"name": "Eficiência Operacional", "value_type": "percentage", "value": 88, "color_hint": "green"},
                                {"name": "Margem de Risco", "value_type": "percentage", "value": 11, "color_hint": "green"}
                            ],
                            "verdict_summary": "Transição de alto nível com engajamento e sustentabilidade operacional.",
                            "is_success": True
                        }
                    ]
                }
            ]

            target_turn1_ids = ["A", "B", "C"]
            for idx, op in enumerate(opts1):
                if isinstance(op, dict) and idx < len(target_turn1_ids):
                    op["id"] = target_turn1_ids[idx]

            while len(opts1) < 3:
                next_idx = len(opts1)
                opts1.append(default_opt1_templates[next_idx])

            return {
                "context": str(ctx),
                "initial_indicators": init_inds,
                "turn1_prompt": str(p1),
                "turn1_options": opts1[:3]
            }
        return data

# =========================================================================
# DUELO SOCRÁTICO (2 ROUNDS COM NÓ COGNITIVO)
# =========================================================================

class SocraticDuelQuestion(BaseModel):
    dilemma_title: Optional[str] = Field(default="Estudo de Caso Prático", description="Título do caso")
    question: str = Field(default="", description="Pergunta aberta ou dilema prático inicial")
    evaluation_rubric: List[str] = Field(default_factory=list, description="Critérios de avaliação para orientar o Desafio de Cenário")
    image_url: Optional[str] = Field(default=None, description="URL da gravura contextualizada do caso de estudo")
    image_caption: Optional[str] = Field(default=None, description="Legenda da gravura do caso")

    @model_validator(mode="before")
    @classmethod
    def parse_socratic(cls, data: Any) -> Any:
        if isinstance(data, dict):
            title = data.get("dilemma_title") or data.get("titulo") or "Estudo de Caso Prático"
            q = data.get("question") or data.get("pergunta") or data.get("dilema") or ""
            rubric = data.get("evaluation_rubric") or data.get("rubric") or data.get("rubrica") or []
            img_url = data.get("image_url") or data.get("img") or None
            img_cap = data.get("image_caption") or data.get("legenda") or None
            if isinstance(rubric, str):
                rubric = [rubric]
            return {
                "dilemma_title": str(title),
                "question": str(q),
                "evaluation_rubric": [str(r) for r in rubric],
                "image_url": img_url,
                "image_caption": img_cap
            }
        return data

class SocraticRound1Evaluation(BaseModel):
    passed_round1: bool = Field(default=True, description="True se o aluno demonstrou mérito suficiente para avançar ao Nó Cognitivo")
    feedback: str = Field(default="", description="Comentário sobre a tese inicial do aluno")
    cognitive_knot: Optional[str] = Field(default=None, description="O Nó Cognitivo (provocação com caso de borda / edge case)")

class SocraticRound2Evaluation(BaseModel):
    passed: bool = Field(default=True, description="True se o aluno adaptou e defendeu com solidez sua estratégia diante do Nó Cognitivo")
    score: int = Field(default=9, ge=0, le=10, description="Nota de 0 a 10")
    feedback: str = Field(default="", description="Feedback final do debatedor socrático")

# =========================================================================
# SCHEMA UNIFICADO DO QUIZ
# =========================================================================

class QuizSchema(BaseModel):
    mcq: List[MultipleChoiceQuestion] = Field(default_factory=list)
    simulation: Optional[SimulationSandbox] = Field(default=None)
    socratic_duel: Optional[SocraticDuelQuestion] = Field(default=None)
    # Suporte legado para compatibilidade com cursos já gerados no banco
    fill_in_the_blanks: Optional[List[FillInBlankQuestion]] = Field(default_factory=list)
    discursive: Optional[Union[DiscursiveQuestion, SocraticDuelQuestion]] = Field(default_factory=DiscursiveQuestion)

    @model_validator(mode="before")
    @classmethod
    def parse_quiz(cls, data: Any) -> Any:
        if isinstance(data, list):
            data = {"mcq": data}
        if isinstance(data, dict):
            source = data.get("quiz") or data.get("teste") or data
            
            raw_mcq = source.get("mcq") or source.get("multiple_choice") or source.get("multipla_escolha") or []
            if isinstance(raw_mcq, dict):
                raw_mcq = [raw_mcq]
            raw_sim = source.get("simulation") or source.get("simulador") or source.get("mini_simulador") or source.get("sandbox")
            raw_socratic = (
                source.get("socratic_duel") or 
                source.get("socratic") or 
                source.get("duelo_socratico") or 
                source.get("duelo") or 
                source.get("socratic_question") or
                source.get("discursive") or 
                source.get("discursiva")
            )
            
            raw_blanks = source.get("fill_in_the_blanks") or source.get("blanks") or source.get("lacunas") or []
            raw_disc = source.get("discursive") or source.get("discursiva") or source.get("dissertativa")

            if not raw_sim:
                raw_sim = {}

            # Fallback inteligente contextual se socratic_duel não foi gerado ou veio genérico
            is_generic = False
            if isinstance(raw_socratic, dict):
                q_text = raw_socratic.get("question", "")
                if not q_text or "qual decisão estratégica você adotaria em um cenário adverso e por quê" in q_text.lower():
                    is_generic = True
            elif not raw_socratic:
                is_generic = True

            if is_generic:
                if raw_disc and isinstance(raw_disc, dict) and raw_disc.get("question"):
                    raw_socratic = raw_disc
                else:
                    topic_hint = source.get("lesson_title") or source.get("title") or "esta lição"
                    concept_hint = source.get("core_concept") or ""
                    if concept_hint:
                        dilemma_text = f"Imagine que você precisa liderar a aplicação prática dos conceitos de '{topic_hint}' ({concept_hint[:110]}), mas enfrenta um conflito crítico entre velocidade de execução e sustentabilidade do modelo. Qual conduta você priorizaria e qual trade-off consciente aceitaria defender?"
                    else:
                        dilemma_text = f"Em um cenário de incerteza operacional envolvendo '{topic_hint}', você é confrontado com uma escolha irrevogável de alocação de esforço. Como você sustentaria sua decisão estratégica com base no que foi ensinado?"

                    raw_socratic = {
                        "dilemma_title": f"Dilema Prático: {topic_hint}",
                        "question": dilemma_text,
                        "evaluation_rubric": [
                            "Demonstração de raciocínio prático e alinhamento com a ideia central da aula",
                            "Coerência lógica para sustentação da tese frente ao Nó Cognitivo"
                        ]
                    }

            if not raw_disc and raw_socratic:
                if isinstance(raw_socratic, dict):
                    raw_disc = {
                        "question": raw_socratic.get("question", ""),
                        "evaluation_rubric": raw_socratic.get("evaluation_rubric", [])
                    }
                elif hasattr(raw_socratic, "question"):
                    raw_disc = {
                        "question": str(getattr(raw_socratic, "question", "")),
                        "evaluation_rubric": list(getattr(raw_socratic, "evaluation_rubric", []))
                    }
                else:
                    raw_disc = raw_socratic
            
            return {
                "mcq": raw_mcq,
                "simulation": raw_sim,
                "socratic_duel": raw_socratic,
                "fill_in_the_blanks": raw_blanks,
                "discursive": raw_disc
            }
        return data

class GraderEvaluation(BaseModel):
    passed: bool = Field(default=False, description="True se aprovado")
    score: int = Field(default=0, ge=0, le=10, description="Nota de 0 a 10")
    feedback: str = Field(default="", description="Feedback socratico")

    @model_validator(mode="before")
    @classmethod
    def parse_grader(cls, data: Any) -> Any:
        if isinstance(data, dict):
            p = bool(data.get("passed") if "passed" in data else data.get("aprovado", False))
            s = int(data.get("score") or data.get("nota") or (10 if p else 3))
            fb = data.get("feedback") or data.get("comentario") or data.get("justificativa") or ""
            return {"passed": p, "score": s, "feedback": str(fb)}
        return data

