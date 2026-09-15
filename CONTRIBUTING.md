# Guia de Contribuição • Trivium Academy 🏛️

Obrigado pelo interesse em contribuir com o **Trivium**! Este projeto foi desenvolvido com uma arquitetura modular orientada a agentes de IA, princípios pedagógicos de *Mastery Learning* e rigor técnico.

Para manter a estabilidade do projeto e garantir uma convivência saudável e produtiva, pedimos que todos os colaboradores sigam as diretrizes abaixo.

---

## 🛡️ Princípios Fundamentais

1. **A branch `main` é estável**: Nenhum código entra na `main` sem passar por revisão, testes e validação.
2. **Proponha antes de codificar grandes mudanças**: Se você tem uma ideia de nova feature ou grande refatoração de arquitetura, abra primeiro uma **Issue de Discussão (Feature Request)** para alinharmos a proposta antes de gastar tempo desenvolvendo.
3. **Mantenha o minimalismo e a elegância**: O Trivium preza por uma interface limpa, rápida, sem distrações e com foco absoluto no aprendizado profundo.
4. **Sem dados sensíveis**: Jamais inclua chaves de API, segredos ou arquivos `.env` em seus commits ou Pull Requests.

---

## 🛠️ Como Contribuir

### 1. Criando seu Fork
1. Faça um **Fork** do repositório oficial para a sua conta no GitHub.
2. Clone o seu fork localmente:
   ```bash
   git clone https://github.com/SEU_USUARIO/Trivium.git
   cd Trivium
   ```

### 2. Configurando o Ambiente Local

#### Backend (Python 3.10+)
```bash
cd backend
python -m venv .venv
# No Windows:
.venv\Scripts\activate
# No Linux/Mac:
source .venv/bin/activate

pip install -r requirements.txt
```

Copie o `.env.example` para `.env` e adicione suas chaves de API locais para teste:
```bash
cp .env.example .env
```

Inicie o servidor backend:
```bash
uvicorn app.main:app --reload --port 8000
```

#### Frontend (Node.js 18+ / Next.js)
```bash
cd frontend
npm install
npm run dev
```
Acesse `http://localhost:3000`.

---

## 🌿 Padrão de Branches

Crie uma branch descritiva a partir da `main`:
* **Correção de bugs**: `fix/nome-do-bug` (ex: `fix/socratic-duel-evaluation`)
* **Novas funcionalidades**: `feat/nome-da-feature` (ex: `feat/anki-export`)
* **Melhorias de documentação**: `docs/nome-da-melhoria`

```bash
git checkout -b feat/minha-melhoria
```

---

## 🧪 Validação Obrigatória Antes de Abrir PR

Antes de submeter o seu Pull Request, execute localmente as rotinas de verificação:

1. **Frontend (Build & Linting)**:
   ```bash
   cd frontend
   npm run build
   ```
   *O build do Next.js deve passar com 0 erros de TypeScript e 0 warnings impeditivos.*

2. **Backend (Sintaxe e Imports)**:
   ```bash
   cd backend
   python -m py_compile app/main.py app/agents/pipeline.py app/services/tutor_service.py
   ```

---

## 📬 Abrindo um Pull Request (PR)

1. Faça o commit das suas mudanças com mensagens claras no padrão [Conventional Commits](https://www.conventionalcommits.org/):
   ```bash
   git commit -m "fix(simulation): ensure 3 options are always present in turn 2"
   ```
2. Dê push para o seu fork:
   ```bash
   git push origin feat/minha-melhoria
   ```
3. Abra o **Pull Request** no GitHub:
   * Descreva claramente o **problema** que o PR resolve.
   * Explique a **solução adotada**.
   * Anexe prints/vídeos se houver mudanças visuais no frontend.
   * Cite a Issue correspondente (ex: `Closes #12`).

---

## 🔍 Processo de Revisão

* Todos os PRs são revisados pelos mantenedores do projeto.
* Podemos sugerir ajustes ou solicitar testes adicionais antes do merge.
* Seja respeitoso e aberto ao feedback nas discussões dos PRs.

Obrigado por ajudar a tornar o Trivium uma ferramenta cada vez mais poderosa e transformadora! 🚀
