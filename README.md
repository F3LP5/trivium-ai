<p align="center">
  <a href="https://github.com/F3LP5/trivium-ai">
    <img src="./assets/trivium-logo.png" alt="Trivium AI Logo" width="130" height="130" style="background-color: #000000; border-radius: 24px; padding: 12px; border: 1px solid rgba(255, 229, 0, 0.25);" />
  </a>
</p>

<h1 align="center">Trivium AI</h1>

<p align="center">
  <strong>Build interactive, high-retention courses on any topic—or straight from your books (PDF & EPUB).</strong><br />
  <em>Free, open-source, and powered by local models or free cloud endpoints.</em>
</p>

<p align="center">
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge" alt="License: MIT" /></a>
  <a href="https://nextjs.org/"><img src="https://img.shields.io/badge/Next.js%2014-App%20Router-black?style=for-the-badge&logo=next.js" alt="Next.js 14" /></a>
  <a href="https://fastapi.tiangolo.com/"><img src="https://img.shields.io/badge/FastAPI-0.110+-009688?style=for-the-badge&logo=fastapi" alt="FastAPI" /></a>
  <a href="https://ollama.com/"><img src="https://img.shields.io/badge/Local%20AI-Ollama%20%7C%20LM%20Studio-orange?style=for-the-badge&logo=ollama" alt="Local AI" /></a>
  <a href="https://openrouter.ai/"><img src="https://img.shields.io/badge/OpenRouter-Free%20Tier-blueviolet?style=for-the-badge" alt="OpenRouter Free Tier" /></a>
  <a href="https://playwright.dev/"><img src="https://img.shields.io/badge/PDF%20Export-Playwright%20A4-2EAD33?style=for-the-badge" alt="Playwright" /></a>
  <img src="https://img.shields.io/badge/Languages-EN--US%20%7C%20PT--BR-10B981?style=for-the-badge" alt="Bilingual" />
</p>

<p align="center">
  <a href="https://github.com/F3LP5/trivium-ai/archive/refs/heads/main.zip">
    <img src="https://img.shields.io/badge/⚡_Download_Trivium_(ZIP)-Windows_Launcher-FFE500?style=for-the-badge&logo=windows&logoColor=FFE500&labelColor=0A0A0C" alt="Download ZIP" height="38" />
  </a>
  <a href="https://github.com/F3LP5/trivium-ai/releases/latest">
    <img src="https://img.shields.io/badge/🏷️_Release-v1.0.0-10B981?style=for-the-badge&labelColor=0A0A0C" alt="Latest Release" height="38" />
  </a>
</p>

<p align="center">
  <a href="#-overview">Overview</a> •
  <a href="#-key-features">Key Features</a> •
  <a href="#-how-you-learn">How You Learn</a> •
  <a href="#-course-levels-basic-intermediate--advanced">Course Levels</a> •
  <a href="#-turn-your-books-into-courses">Books to Courses</a> •
  <a href="#-architecture">Architecture</a> •
  <a href="#-quick-start">Quick Start</a> •
  <a href="#-running-for-free--local-ai">Free & Local AI</a>
</p>

---

## ⚡ Overview

Most AI learning tools just give you quick summaries or generic multiple-choice quizzes that you forget ten minutes later.

**Trivium AI** builds structured, step-by-step courses designed to help you actually retain what you learn—whether you want to explore a new field from scratch or turn an entire book in **PDF or EPUB** into an interactive curriculum.

Every lesson is grounded in real sources, optionally enriched with clean gold-stipple diagrams, and backed by active learning checks: practical quizzes, scenario simulations, and conversational challenges.

> 💡 **Learn by doing, not skimming.** Lessons unlock as you demonstrate understanding, keeping you focused and moving forward.

---

## ✨ Key Features

- 🎯 **Learn Any Topic or Niche:** Generate structured courses on whatever you want to learn—from system architecture and finance to philosophy, biology, or niche skills.
- 📚 **Turn Books into Courses (PDF & EPUB):** Drop in a textbook, technical manual, or ebook. Trivium parses the chapters and builds a full course around the author's material, with clear page citations.
- 🔬 **Real Sources, Less Hallucination:** Uses a research engine that references Wikipedia and trusted web sources, keeping lesson content factually accurate.
- 🎮 **Hands-On Decision Scenarios:** Face realistic scenarios with live metrics, choose your action, and see the second-order consequences.
- ⚔️ **Socratic Challenges:** Explain concepts in your own words. The AI tests your understanding against practical edge cases before you advance.
- 💬 **In-Lesson AI Tutor:** A split-screen helper focused strictly on the current lesson, ready to explain tricky ideas without pulling you off-topic.
- 🎨 **Visual Concept Art (Optional):** Clean black-and-gold stipple illustrations designed for conceptual clarity without visual clutter.
- 🖨️ **Printable PDF Booklets:** Export complete course books to cleanly formatted A4 PDFs with Playwright.
- 🌐 **Native English & Portuguese:** Full bilingual support for both the user interface and course generation.
- 💸 **100% Free & Local-Friendly:** Run zero-cost cloud models on OpenRouter, or run completely offline with Ollama or LM Studio.

---

## 🎯 How You Learn

Each lesson is designed around three practical steps to make sure ideas stick:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      1. READ THE LESSON (500 - 2,000 words)             │
│            Clear, focused prose (with optional concept illustrations)   │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  STEP 1: Quick Concept Checks (MCQs)                                    │
│  • 3 to 5 straightforward questions anchored in the text                │
│  • Immediate feedback to make sure you got the basics                   │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  STEP 2: Interactive Decision Scenario                                  │
│  • A practical situation with 3 live indicators (e.g. Risk, Quality)    │
│  • Make a decision, see the fallout, and handle the consequences        │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  STEP 3: Socratic Discussion                                            │
│  • Defend your reasoning in plain English                               │
│  • The AI pushes back with a realistic edge case to test your logic     │
│  • Pass the review to unlock your next lesson                           │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 📊 Course Levels: Basic, Intermediate & Advanced

Trivium adapts the depth, pacing, and curriculum based on the level you pick:

| Level | What You'll Learn | Structure | Lesson Length | Who It's For |
| :--- | :--- | :---: | :---: | :--- |
| **Basic**<br>*(Foundational)* | Core concepts, practical mental models, and clear real-world examples. Starts from zero with straightforward explanations. | **4 Modules**<br>(12 Lessons) | ~500–900 words | Beginners who want a clear, solid start in a new subject. |
| **Intermediate** | Practical workflows, real-world trade-offs, common pitfalls, and hands-on problem solving. | **8 Modules**<br>(32 Lessons) | ~800–1,200 words | People who know the basics and want working knowledge they can use. |
| **Advanced** | System-level thinking, tricky edge cases, hard design decisions, and deep nuances. | **12 Modules**<br>(60 Lessons) | ~1,200–2,000 words | Experienced learners and builders looking for a comprehensive deep dive. |

---

## 📖 Turn Your Books into Courses

Got a book you've been meaning to read, or a dense PDF manual for work?

```
             ┌─────────────────────────────────────────────────┐
             │       Upload Book / Document (.pdf, .epub)      │
             └────────────────────────┬────────────────────────┘
                                      │
                                      ▼
             ┌─────────────────────────────────────────────────┐
             │            Clean Text Extraction                │
             │   Strips page numbers, headers, and noise       │
             └────────────────────────┬────────────────────────┘
                                      │
                                      ▼
             ┌─────────────────────────────────────────────────┐
             │             Quick Content Preview               │
             │   • Detects book title & central topic          │
             │   • Rebuilds chapter outline                    │
             │   • Suggests matching difficulty level          │
             └────────────────────────┬────────────────────────┘
                                      │
                                      ▼
             ┌─────────────────────────────────────────────────┐
             │       Step-by-Step Course Generated!            │
             │   Includes quizzes, scenarios, and source notes │
             └─────────────────────────────────────────────────┘
```

1. Click **"From Local Document"** on the home screen.
2. Drag and drop any `.pdf` or `.epub` file.
3. Check the instant title preview and suggested level.
4. Click generate to turn the book into an interactive course.

---

## 🏛️ Architecture

Trivium uses an automated multi-agent pipeline to research, write, and verify each course:

```mermaid
flowchart TD
    User([User Prompt / Book Upload]):-- Topic, Level, Language --> Gateway[FastAPI Gateway]
    Gateway -- Job Ticket --> Orch[CourseOrchestrator]
    
    subgraph Research & Extraction
        Orch --> SubQ[Sub-query Search]
        SubQ --> DDG[DuckDuckGo]
        SubQ --> Wiki[Wikipedia API]
        DDG & Wiki --> Traf[Trafilatura Text Extractor]
        Traf --> Dossier[Factual Research Dossier]
        DocExtract[PDF / EPUB Extractor] --> CogAn[Document Analyzer] --> Dossier
    end

    subgraph Course Generation
        Dossier --> Curator[Curator Agent: Course Outline & Syllabus]
        Curator --> Loop[Lesson Generation Loop]
        Loop --> Writer[Writer Agent: Lesson Drafts]
        Writer --> Stipple[Stipple Service: Optional Concept Illustrations]
        Stipple --> Quiz[QuizMaster Agent: MCQs + Scenario + Socratic Prompts]
        Quiz --> Sum[Summarizer Agent: Key Takeaways]
        Sum --> DB[(SQLite Database)]
    end

    subgraph Student Interface
        DB --> ReadUI[Course Reader]
        ReadUI --> Tutor[In-Lesson Sidebar AI Tutor]
        ReadUI --> SandboxUI[Interactive Decision Sandbox]
        ReadUI --> Grader[Grader Agent: Evaluates Socratic Answers]
        Grader -- Pass --> Unlock[Unlock Next Lesson]
        ReadUI --> PDFEngine[Playwright: Export A4 PDF Booklet]
    end
```

---

## 🚀 Quick Start

### Option A: Windows 1-Click Launcher (Easiest)

1. **[Click here to Download Trivium (ZIP)](https://github.com/F3LP5/trivium-ai/archive/refs/heads/main.zip)** and extract the archive to your computer.
2. Inside the extracted folder, double-click:
```powershell
.\Trivium-Launcher.bat
```

> **What it does on first launch:**
> 1. Adds a desktop shortcut with the official Trivium icon.
> 2. Sets up Python and Node.js automatically if missing.
> 3. Starts both the backend and frontend cleanly in the background.

---

### Option B: Manual Setup (Developers)

#### Prerequisites
- **Python 3.12+** (or `uv`)
- **Node.js 18+** and `npm`
- An API key (OpenRouter, OpenAI, Anthropic) or a local Ollama instance

#### 1. Backend Setup
```bash
cd backend

# Create virtual environment
uv venv
# On Windows: .venv\Scripts\activate
# On Linux/macOS: source .venv/bin/activate

# Install dependencies & Playwright browser
uv pip install -r requirements.txt
playwright install chromium

# Start the FastAPI server
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
*API docs available at `http://127.0.0.1:8000/docs`.*

#### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
*Web app available at `http://localhost:3000`.*

---

## 🦙 Running for Free & Local AI

You don't need expensive API subscriptions to use Trivium:

### 1. Free Cloud Models (OpenRouter)
- Use the built-in **Benchmark Tool** in Settings to test all active free models on OpenRouter (`:free`) for speed and reliability in real-time.
- One click sets up your preferred free models with automatic fallback.

### 2. 100% Offline with Local Models (Ollama / LM Studio)
- **Zero Cost, Zero Data Sharing:** Everything stays on your machine.
- **Pre-Configured for Local GPUs:**
  - Auto-allocates an 8,192-token context window (`num_ctx = 8192`).
  - Enforces valid JSON structure so models don't ramble.
  - Automatically cleans up DeepSeek reasoning tags (`<think>...</think>`).
  - VRAM concurrency guards prevent GPU out-of-memory errors.
  - Click **"Test Connection"** in Settings to check latency and auto-detect your installed models.

```bash
# Example: Install Ollama and download a model
ollama run llama3.1

# Then open Trivium Settings, select "Local / Ollama", and test your connection!
```

---

## 📂 Project Structure

```text
trivium-ai/
├── README.md                      # Documentation
├── assets/                        # Logos and visual assets
│   └── trivium-logo.png
├── backend/                       # FastAPI Server, Agents & Database
│   ├── app/
│   │   ├── main.py                # REST API & background task runner
│   │   ├── database.py            # SQLite setup & schema migrations
│   │   ├── models/entities.py     # SQLModel database tables
│   │   ├── agents/pipeline.py     # AI Agents (Curator, Writer, QuizMaster, Grader)
│   │   ├── graph/orchestrator.py  # Course production coordinator
│   │   └── services/
│   │       ├── llm_gateway.py     # LLM Gateway & free models benchmark
│   │       ├── local_ai_wrapper.py# Ollama & LM Studio wrapper
│   │       ├── document_extractor.py # PDF & EPUB segmenter
│   │       ├── cognitive_analyzer.py # Book analyzer
│   │       ├── researcher.py      # Web & Wikipedia research engine
│   │       ├── tutor_service.py   # In-lesson AI tutor
│   │       ├── stipple_image_service.py # Optional stipple illustration generator
│   │       └── pdf_service.py     # Playwright PDF compiler
│   └── storage/                   # Databases, images, and upload caches
└── frontend/                      # Next.js 14 Web Interface
    └── src/
        ├── app/
        │   ├── page.tsx           # Home: Course creator, book upload, library
        │   ├── course/[id]/       # Syllabus, research sources, progress tracker
        │   └── lesson/[id]/       # Lesson reader, quiz, scenario, Socratic chat
        ├── components/
        │   ├── SettingsModal.tsx  # Settings (Providers, keys, benchmark)
        │   └── LessonTutorChat.tsx# Lesson-specific AI tutor
        └── lib/
            ├── api.ts             # API client
            └── i18n.ts            # English & Portuguese localization
```

---

## 🌟 The Vision

> Learn anything at your own pace—from **Basic** foundations to **Intermediate** practice and **Advanced** deep dives.  
> Get structured courses grounded in real sources—100% free using local models or the free models available on OpenRouter.  
> Turn any book on your shelf into an interactive, step-by-step course.  
>  
> **The only limit to your learning is you!**

---

<p align="center">
  Distributed under the <strong>MIT License</strong>. Built for curious minds, autodidacts, and developers everywhere.
</p>
