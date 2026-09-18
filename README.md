# ResearchMind AI 🧠🔬

**ResearchMind AI** is an autonomous, multi-modal AI agent built for comprehensive academic and scientific paper analysis, critical peer review, grounded Q&A, and comparative cross-paper synthesis.

Powered by Google Gemini (`gemini-3.5-flash` and `gemini-2.5-pro` via the official `google-genai` SDK), it provides deep academic rigor with exact page citations and LaTeX formula rendering.

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https%3A%2F%2Fgithub.com%2Fdarursrikar-sketch%2Fresearchmind-ai&env=GEMINI_API_KEY,GEMINI_MODEL,FLASK_SECRET_KEY&project-name=researchmind-ai)

---

## Key Features

1. **Multi-Source Paper Ingestion**:
   - **arXiv One-Click Fetch**: Ingest any paper by arXiv ID (e.g., `1706.03762`) or URL. Automatically retrieves metadata and downloads the full PDF.
   - **Local PDF Upload**: Drag-and-drop or path-based ingestion of local papers.
   - **Page-Aware Extraction**: Parses text page-by-page to enable page-grounded citations (`[Page 4]`).

2. **Autonomous Agent Analysis Pipeline**:
   - **Executive Summary & TL;DR**: Problem statement, core innovation, and headline metrics.
   - **Methodology & Architecture**: Algorithmic pipelines, LaTeX equations ($...$ and $$...$$), loss functions, and theoretical bounds.
   - **Critical Peer Review**: Senior reviewer simulation (NeurIPS / ICML / Nature style) with 1–10 score, acceptance recommendation, missing baselines, and author rebuttal questions.
   - **Findings & Benchmarks**: Datasets evaluated, comparative tables against prior art, and ablation takeaways.
   - **Limitations & Future Work**: Fundamental failure modes, scaling bottlenecks, and high-impact follow-ups.
   - **Implementation & Replication**: Pseudocode, hyperparameter tables, compute requirements, and subtle engineering pitfalls.

3. **Grounded Interactive Paper Chat**:
   - Multi-turn conversational dialogue strictly grounded in the paper.
   - Every claim is cited with page numbers to eliminate hallucinations.
   - Automated generation of paper-specific research inquiries.

4. **Multi-Paper Comparative Synthesis**:
   - Select 2+ papers from your local workspace.
   - Synthesizes side-by-side comparison tables, architectural trade-offs, and practical deployment recommendations.

5. **Dual Interface**:
   - **Interactive Web Dashboard**: Reactive SPA with Tailwind CSS, Lucide icons, KaTeX math rendering, dark mode, and real-time streaming.
   - **Terminal CLI**: Full command-line tool with batch analysis, REPL chat, and export capabilities.

6. **Exporting & Local Storage**:
   - One-click export to Markdown (`.md`), standalone printable HTML (`.html`), or structured JSON (`.json`).
   - SQLite-backed local workspace library.

---

## Quick Start

### 1. Configure Gemini API Key
Obtain an API key from [Google AI Studio](https://aistudio.google.com/).

Set it in `.env`:
```env
GEMINI_API_KEY=AIzaSy...
GEMINI_MODEL=gemini-3.7-flash
```
*(You can also set or change the API key anytime directly inside the Web UI or via the CLI!)*

### 2. Launch Web Dashboard
```bash
python run_web.py
```
Then open your browser at **`http://localhost:5000`**.

---

## Command Line Interface (CLI)

ResearchMind comes with a rich CLI for automated scripts or terminal workflows:

### Analyze a Paper (arXiv or Local PDF)
```bash
# Analyze arXiv paper
python run_cli.py analyze 1706.03762

# Analyze local PDF and export to Markdown
python run_cli.py analyze ./path/to/paper.pdf --export md --out report.md

# Use Gemini 2.5 Pro for exhaustive peer review
python run_cli.py analyze 2106.09685 --model gemini-2.5-pro --export html
```

### Interactive Grounded Chat in Terminal
```bash
python run_cli.py chat 1706.03762
```

### Compare Multiple Papers
```bash
python run_cli.py compare 1706.03762 2106.09685
```

### List Saved Papers in Local Library
```bash
python run_cli.py list
```

### Manage API Configuration
```bash
python run_cli.py config --set-key YOUR_API_KEY
python run_cli.py config --set-model gemini-3.7-flash
```

---

## Project Structure

```
research mind project/
├── .env                             # Local API key & config
├── .env.example                     # Environment template
├── requirements.txt                 # Dependencies
├── run_web.py                       # Web server launcher
├── run_cli.py                       # CLI launcher
├── researchmind/
│   ├── config.py                    # Settings & Gemini Client factory
│   ├── paper_loader.py              # PDF extraction & arXiv API fetcher
│   ├── storage.py                   # SQLite persistence for papers and analyses
│   ├── exporter.py                  # Markdown, HTML, JSON exporters
│   ├── cli.py                       # CLI commands & REPL
│   ├── core/
│   │   ├── prompts.py               # Domain-specific prompts for academic analysis
│   │   ├── agent.py                 # Multi-module PaperAnalysisAgent
│   │   ├── chat_engine.py           # Grounded Q&A engine with citations
│   │   └── comparative.py           # Multi-paper synthesis agent
│   └── web/
│       ├── app.py                   # Flask REST API & streaming routes
│       ├── templates/
│       │   └── index.html           # Modern dashboard UI
│       └── static/
│           ├── css/custom.css       # Typography & layout styling
│           └── js/app.js            # Client-side reactivity & SSE streaming
└── data/                            # Local database and uploaded papers
```

