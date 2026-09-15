export type SupportedLanguage = "pt-BR" | "en-US";

export const translations = {
  "pt-BR": {
    app_name: "Trivium",
    tagline: "rigor, lógica e maestria",
    version_tag: "V1 Open Source (MIT)",
    settings: "Configurações",
    hero_badge: "Mastery-Based Deep Learning Platform",
    hero_title_1: "O que você quer",
    hero_title_2: "aprender hoje?",
    example_label: "Exemplo:",
    input_placeholder: "Digite qualquer campo do conhecimento (ex: Engenharia Civil)...",
    btn_continue: "Continuar",
    
    // Diferenciais
    diff1_title: "Do Zero ao Avançado",
    diff1_desc: "Comece sem saber nada: defina o nível e veja cada peça se encaixar como uma boa história.",
    diff2_title: "Bastidores e Fatos Reais",
    diff2_desc: "Acesso direto às obras originais e pesquisas reais que deram vida a todo o conteúdo.",
    diff3_title: "Tutor 24/7",
    diff3_desc: "Travou em algum conceito? Converse na hora e destrinche qualquer ideia com exemplos reais.",
    
    // Biblioteca
    library_badge: "Biblioteca Local",
    library_title: "Seus Cursos Criados",
    btn_refresh: "Atualizar",
    track_single: "trilha",
    tracks_plural: "trilhas",
    loading_courses: "Carregando seus cursos salvos...",
    no_courses_title: "Nenhum curso carregado no momento.",
    btn_reload_library: "Recarregar Biblioteca",
    access_course: "Acessar Curso",
    modules_lessons_label: "módulos • {lessons} aulas estruturadas",
    
    // Modal de Configurar Curso
    modal_badge: "Configurar Curso",
    level_modal_title: "Escolha seu nível de profundidade",
    topic_label: "Tema:",
    language_label: "Idioma do Curso",
    level_basic_name: "Básico (Fundamentos)",
    level_basic_meta: "4 Módulos • 12 Aulas",
    level_basic_desc: "~800 palavras por aula. Conceitos centrais, analogias e vocabulário chave.",
    level_inter_name: "Intermediário",
    level_inter_meta: "8 Módulos • 32 Aulas",
    level_inter_desc: "~1.200 palavras por aula. Metodologia prática, cálculos e fluxos de trabalho.",
    level_adv_name: "Avançado (Maestria)",
    level_adv_meta: "12 Módulos • 60 Aulas",
    level_adv_desc: "~2.000 palavras por aula. Casos complexos, normas técnicas e diagnóstico crítico.",

    // Modos de Criação e Upload de Arquivo
    mode_web_search: "Pesquisa web",
    mode_from_document: "Do seu arquivo",
    mode_info_title: "Informações sobre o modo de curso",
    mode_info_tooltip_web: "Crie um curso sob medida sobre qualquer assunto, com fatos e referências reais pesquisados na hora.",
    mode_info_tooltip_doc: "Suba seu livro em PDF ou EPUB e transforme a leitura em uma experiência prática e interativa.",
    doc_upload_reading: "Lendo páginas e analisando complexidade com IA...",
    doc_upload_sanitizing: "Catalogando capítulos e organizando estrutura pedagógica",
    doc_drag_here: "Arraste seu livro aqui ou",
    doc_click_browse: "clique para navegar no computador",
    doc_supported_formats: "Formatos suportados: PDF ou EPUB (leitura integral de 100% dos capítulos)",
    doc_inferred_level: "NÍVEL INFERIDO:",
    doc_pages: "páginas",
    doc_chapters_indexed: "capítulos indexados",
    doc_author: "Autor(a):",
    doc_editorial_title: "Título editorial identificado na obra:",
    doc_change_file: "Trocar arquivo",
    doc_field_course_title: "Título Sugerido para o Curso:",
    doc_course_journey_label: "O curso será construído como uma jornada",
    doc_modules_lessons_pattern: "{modules} Módulos, {lessons} Lições",
    doc_course_journey_suffix: "mantendo esse nível de profundidade e a riqueza conceitual da obra.",
    doc_author_assumptions: "Pressupostos do autor detectados:",
    doc_btn_generate: "Gerar Curso a Partir do Livro",

    // Tela de Loading da Esteira
    pipeline_badge: "Esteira Editorial Trivium",
    pipeline_title: "Organizando seu Curso Completo",
    pipeline_desc: "Compilando pesquisas, apostilas e desafios práticos...",
    pipeline_progress: "Progresso",
    pipeline_step_label: "Etapa Atual",
    pipeline_initial_step: "Iniciando a esteira editorial...",
    pipeline_completed: "Curso pronto! Redirecionando para a sua sala de estudos...",
    pipeline_failed: "Falha na esteira de geração",
    pipeline_close: "Fechar",
    
    // Página de Matriz Curricular (Course Page)
    course_back_search: "Voltar à Busca",
    course_matrix_badge: "TRILHA DE APRENDIZAGEM • TRIVIUM",
    course_matrix_desc: "Aulas organizadas em encadeamento lógico sequencial. Cada módulo só é liberado mediante aprovação no teste da aula anterior.",
    course_progress_label: "Seu Domínio do Conteúdo",
    course_progress_completed: "{completed} de {total} Aulas Concluídas ({percent}%)",
    course_sources_badge: "Lista de Fontes",
    course_sources_verified: "{count} fontes verificadas",
    course_sources_desc: "Conteúdo estruturado com checagem cruzada multi-domínio e referências documentadas.",
    course_sources_title: "Bibliografia e Fontes Primárias",
    course_matrix_extracted: "SÍNTESE DE REFERÊNCIAS",
    course_module_prefix: "Módulo",
    course_episode_prefix: "Episódio",
    course_status_locked: "Bloqueado",
    course_status_completed: "Concluído",
    course_status_in_progress: "Em Progresso",
    course_btn_start_lesson: "Iniciar Aula",
    course_btn_review_lesson: "Rever Aula",
    course_mode_open: "Modo Livre",
    course_mode_guided: "Modo Guiado",
    course_mode_open_tooltip: "Todas as aulas disponíveis livremente com progresso salvo",
    course_mode_guided_tooltip: "Trilha sequencial recomendada com bloqueio de aulas",
    guided_modal_title: "Ativar Modo de Aprendizagem Guiada?",
    guided_modal_desc: "Ao selecionar esta opção, as aulas serão bloqueadas sequencialmente. Este é o modo ideal para aprender de forma mais organizada e consolidar o aprendizado, exigindo a conclusão dos desafios de cada etapa para liberar a próxima.",
    guided_modal_confirm: "Confirmar e Bloquear",
    guided_modal_cancel: "Cancelar",
    course_delete_btn: "Excluir Curso",
    course_delete_confirm_title: "Excluir Curso Definitivamente?",
    course_delete_confirm_desc: "Esta ação é irreversível e removerá todo o histórico.",
    course_delete_cancel: "Cancelar",
    course_delete_proceed: "Sim, Excluir Definitivamente",

    // Página de Aula (Lesson Page)
    lesson_back_course: "Voltar ao Curso",
    lesson_tab_booklet: "Apostila",
    lesson_tab_quiz: "Fazer Questões",
    lesson_btn_download_pdf: "Baixar PDF",
    lesson_btn_tutor: "Tutor IA",
    lesson_reading_time: "min de leitura",
    lesson_words: "palavras",
    lesson_passed_badge: "Aula Concluída",
    lesson_next_btn: "Próxima Aula",
    lesson_mcq_title: "Verificação de Domínio (MCQ)",
    lesson_sim_title: "Simulador de Decisão em 2 Turnos",
    lesson_socratic_title: "Duelo Socrático",
    lesson_submit_btn: "Confirmar Respostas",
    lesson_submitting: "Avaliando...",
    
    // Alertas e Mensagens
    alert_pipeline_trigger_error: "Erro ao disparar esteira. Certifique-se de que o backend está online.",
    alert_file_format_error: "Por favor, selecione um arquivo no formato .pdf ou .epub",
    alert_file_process_error: "Falha ao processar e analisar o arquivo.",
    alert_doc_generate_error: "Erro ao iniciar geração do curso.",
    course_loading_matrix: "Carregando matriz curricular...",
    course_not_found: "Curso não encontrado",
    course_back_home: "Voltar para a Home",
    course_home_tooltip: "Página Inicial (Trivium)",
    course_settings_tooltip: "Configurações",
    course_delete_tooltip: "Excluir este curso permanentemente",

    // Sugestões
    suggestions: [
      "Como Rimar Bem",
      "Engenharia Civil",
      "Python & Sistemas Distribuídos",
      "Design Editorial & Tipografia",
      "Biologia Molecular",
      "Matemática Financeira & Risco",
      "Arquitetura de Agentes de IA",
      "Neurociência & Aprendizagem"
    ]
  },
  "en-US": {
    app_name: "Trivium",
    tagline: "rigor, logic and mastery",
    version_tag: "V1 Open Source (MIT)",
    settings: "Settings",
    hero_badge: "Mastery-Based Deep Learning Platform",
    hero_title_1: "What do you want",
    hero_title_2: "to master today?",
    example_label: "Example:",
    input_placeholder: "Type any field of knowledge (e.g., Civil Engineering)...",
    btn_continue: "Continue",
    
    // Diferenciais
    diff1_title: "From Scratch to Mastery",
    diff1_desc: "Start with zero background: choose depth and watch every piece connect like an irresistible story.",
    diff2_title: "Primary Sources & Reality",
    diff2_desc: "Direct access to original works and authentic research papers that breathe life into the subject.",
    diff3_title: "24/7 AI Mentor",
    diff3_desc: "Stuck on a nuance? Chat in real time and break down any knot with vivid practical analogies.",
    
    // Biblioteca
    library_badge: "Local Library",
    library_title: "Your Generated Courses",
    btn_refresh: "Refresh",
    track_single: "track",
    tracks_plural: "tracks",
    loading_courses: "Loading your saved courses...",
    no_courses_title: "No courses found in local storage.",
    btn_reload_library: "Reload Library",
    access_course: "Open Course",
    modules_lessons_label: "modules • {lessons} structured lessons",
    
    // Modal de Configurar Curso
    modal_badge: "Configure Course",
    level_modal_title: "Choose your epistemic depth",
    topic_label: "Topic:",
    language_label: "Course Language",
    level_basic_name: "Foundational (Basics)",
    level_basic_meta: "4 Modules • 12 Lessons",
    level_basic_desc: "~800 words per lesson. Core mental models, physical analogies, and essential vocabulary.",
    level_inter_name: "Intermediate",
    level_inter_meta: "8 Modules • 32 Lessons",
    level_inter_desc: "~1,200 words per lesson. Applied methodology, formulas, and real-world execution trade-offs.",
    level_adv_name: "Advanced (Mastery)",
    level_adv_meta: "12 Modules • 60 Lessons",
    level_adv_desc: "~2,000 words per lesson. Edge cases, academic debates, and stress-tested diagnostics.",

    // Modos de Criação e Upload de Arquivo
    mode_web_search: "Web search",
    mode_from_document: "From your file",
    mode_info_title: "Information about course creation modes",
    mode_info_tooltip_web: "Create a tailored course on any topic, with real facts and citations researched in real time.",
    mode_info_tooltip_doc: "Upload your PDF or EPUB book and turn reading into a practical, interactive experience.",
    doc_upload_reading: "Reading pages and analyzing complexity with AI...",
    doc_upload_sanitizing: "Cataloging chapters and structuring pedagogical framework",
    doc_drag_here: "Drag your book here or",
    doc_click_browse: "click to browse your computer",
    doc_supported_formats: "Supported formats: PDF or EPUB (full parsing of 100% of chapters)",
    doc_inferred_level: "INFERRED LEVEL:",
    doc_pages: "pages",
    doc_chapters_indexed: "indexed chapters",
    doc_author: "Author:",
    doc_editorial_title: "Editorial title identified in work:",
    doc_change_file: "Change file",
    doc_field_course_title: "Suggested Course Title:",
    doc_course_journey_label: "The course will be designed as an",
    doc_modules_lessons_pattern: "{modules} Modules, {lessons} Lessons",
    doc_course_journey_suffix: "journey, preserving this depth and conceptual richness of the work.",
    doc_author_assumptions: "Author prerequisites detected:",
    doc_btn_generate: "Generate Course from Book",

    // Tela de Loading da Esteira
    pipeline_badge: "Trivium Editorial Pipeline",
    pipeline_title: "Structuring Your Complete Course",
    pipeline_desc: "Compiling research, textbooks, and interactive challenges...",
    pipeline_progress: "Progress",
    pipeline_step_label: "Current Step",
    pipeline_initial_step: "Initializing the editorial pipeline...",
    pipeline_completed: "Course ready! Teleporting to your study room...",
    pipeline_failed: "Pipeline generation failure",
    pipeline_close: "Close",

    // Página de Matriz Curricular (Course Page)
    course_back_search: "Back to Search",
    course_matrix_badge: "LEARNING TRACK • TRIVIUM",
    course_matrix_desc: "Lessons structured in a sequential, logical chain. Each module unlocks strictly upon passing the preceding lesson.",
    course_progress_label: "Your Subject Mastery",
    course_progress_completed: "{completed} of {total} Lessons Completed ({percent}%)",
    course_sources_badge: "Verified Sources",
    course_sources_verified: "{count} verified sources",
    course_sources_desc: "Content structured with multi-domain cross-examination and primary citations.",
    course_sources_title: "Bibliography & Canonical Sources",
    course_matrix_extracted: "REFERENCE SYNTHESIS",
    course_module_prefix: "Module",
    course_episode_prefix: "Episode",
    course_status_locked: "Locked",
    course_status_completed: "Completed",
    course_status_in_progress: "In Progress",
    course_btn_start_lesson: "Start Lesson",
    course_btn_review_lesson: "Review Lesson",
    course_mode_open: "Open Mode",
    course_mode_guided: "Guided Mode",
    course_mode_open_tooltip: "All lessons freely accessible with saved progress",
    course_mode_guided_tooltip: "Sequential track recommended with locked progression",
    guided_modal_title: "Activate Guided Learning Track?",
    guided_modal_desc: "By selecting this option, uncompleted lessons will be locked sequentially. This is the ideal mode to learn in a structured and organized manner, requiring completing each lesson's challenges to unlock the next.",
    guided_modal_confirm: "Confirm and Lock",
    guided_modal_cancel: "Cancel",
    course_delete_btn: "Delete Course",
    course_delete_confirm_title: "Permanently Delete Course?",
    course_delete_confirm_desc: "This action is irreversible and will permanently purge all progress.",
    course_delete_cancel: "Cancel",
    course_delete_proceed: "Yes, Delete Permanently",

    // Página de Aula (Lesson Page)
    lesson_back_course: "Back to Course",
    lesson_tab_booklet: "Textbook",
    lesson_tab_quiz: "Take Quiz",
    lesson_btn_download_pdf: "Download PDF",
    lesson_btn_tutor: "AI Tutor",
    lesson_reading_time: "min read",
    lesson_words: "words",
    lesson_passed_badge: "Lesson Mastered",
    lesson_next_btn: "Next Lesson",
    lesson_mcq_title: "Mastery Verification (MCQ)",
    lesson_sim_title: "Two-Turn Decision Simulator",
    lesson_socratic_title: "Socratic Duel",
    lesson_submit_btn: "Submit Answers",
    lesson_submitting: "Evaluating...",

    // Alertas e Mensagens
    alert_pipeline_trigger_error: "Failed to start pipeline. Please ensure the backend is running.",
    alert_file_format_error: "Please select a file in .pdf or .epub format",
    alert_file_process_error: "Failed to process and analyze the file.",
    alert_doc_generate_error: "Failed to initiate course generation.",
    course_loading_matrix: "Loading curriculum matrix...",
    course_not_found: "Course not found",
    course_back_home: "Back to Home",
    course_home_tooltip: "Home (Trivium)",
    course_settings_tooltip: "Settings",
    course_delete_tooltip: "Delete this course permanently",
    
    // Sugestões
    suggestions: [
      "How to Freestyle Rap & Rhyme",
      "Structural Civil Engineering",
      "Python & Distributed Systems",
      "Editorial Design & Typography",
      "Molecular Biology & Genetics",
      "Financial Mathematics & Risk",
      "Autonomous AI Agent Architecture",
      "Cognitive Neuroscience & Learning"
    ]
  }
};

/**
 * Traduz e formata o nível do curso de acordo com o idioma da interface.
 * Ex: "Básico" -> "Foundational" (em en-US) ou "Básico" (em pt-BR)
 */
export function formatCourseLevel(level: string | undefined | null, lang: SupportedLanguage): string {
  if (!level) return "";
  const l = level.trim().toLowerCase();
  if (lang === "en-US") {
    if (l.includes("básic") || l.includes("basic") || l.includes("fundament") || l.includes("iniciante")) return "Foundational";
    if (l.includes("interm")) return "Intermediate";
    if (l.includes("avan") || l.includes("advan") || l.includes("maestr")) return "Advanced";
    if (l.includes("test")) return "Test";
    return level;
  } else {
    if (l.includes("basic") || l.includes("fundament") || l.includes("iniciante")) return "Básico";
    if (l.includes("interm")) return "Intermediário";
    if (l.includes("advan") || l.includes("maestr")) return "Avançado";
    if (l.includes("test")) return "Teste";
    return level;
  }
}

