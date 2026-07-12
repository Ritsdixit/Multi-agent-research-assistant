# 🧠 Multi-Agent Research Assistant (RAG + AI Agents)

An end-to-end research assistant that lets you upload PDFs (papers, notes, textbooks),
ask natural-language questions, and get answers grounded in your documents with
**exact page-level citations** — powered by a multi-agent workflow built on **LangGraph**.

## ✨ Features

- 📄 **Upload PDFs** — research papers, notes, textbooks (drag & drop in the UI)
- 💬 **Ask questions in natural language** — grounded RAG over your own documents
- 🤖 **Multi-agent workflow** (LangGraph):
  - **Research Agent** — retrieves relevant chunks and synthesizes findings
  - **Summarization Agent** — turns findings into a concise, clear answer
  - **Citation Agent** — maps every claim to exact source + page number
  - **Quiz Generator Agent** — builds MCQ quizzes grounded in your material
- 🧵 **Memory** — conversation history persisted per session (SQLite)
- 🗂️ **Flashcard generation** — auto-generated Q&A flashcards with source pages
- 🗺️ **Study roadmap generator** — personalized week-by-week study plan
- 📌 **Exact page citations** — every answer traces back to `filename, page X`
- 🎙️ **Voice input/output** (optional) — speech-to-text and text-to-speech

## 🏗️ Architecture

```
                    ┌─────────────────────┐
                    │   Streamlit UI       │
                    │ (chat / flashcards / │
                    │  quiz / roadmap)      │
                    └──────────┬───────────┘
                               │ HTTP
                    ┌──────────▼───────────┐
                    │   FastAPI backend      │
                    └──────────┬───────────┘
                               │
        ┌──────────────────────┼───────────────────────┐
        │                      │                        │
┌───────▼────────┐   ┌─────────▼─────────┐   ┌──────────▼─────────┐
│  PDF Ingestion   │   │   LangGraph        │   │  SQLite            │
│  (PyMuPDF +      │   │   Agent Pipeline    │   │  (memory, docs,    │
│  page-aware       │  │  Research →         │   │  flashcards,        │
│  chunking)         │ │  Summarize → Cite   │   │  roadmaps)           │
└───────┬────────┘   └─────────┬─────────┘   └─────────────────────┘
        │                      │
┌───────▼──────────────────────▼─────────┐
│         ChromaDB (vector store)          │
│   chunks tagged with doc_id + page #     │
└───────────────────────────────────────────┘
```

**Tech stack:** Python · FastAPI · Streamlit · LangChain · LangGraph · ChromaDB ·
HuggingFace / OpenAI embeddings · OpenAI or Gemini LLMs · SQLite · PyMuPDF

## 📂 Project Structure

```
multi-agent-research-assistant/
├── backend/
│   ├── main.py                     # FastAPI app & all endpoints
│   ├── config.py                   # settings, LLM/embeddings provider switch
│   ├── database.py                 # SQLAlchemy models (SQLite)
│   ├── models.py                   # Pydantic request/response schemas
│   ├── ingestion/
│   │   └── pdf_processor.py        # PDF -> page-aware chunks
│   ├── vectorstore/
│   │   └── store.py                # ChromaDB wrapper
│   ├── agents/
│   │   ├── graph.py                # LangGraph orchestration
│   │   ├── research_agent.py
│   │   ├── summarization_agent.py
│   │   ├── citation_agent.py
│   │   ├── quiz_agent.py
│   │   └── json_utils.py
│   ├── memory/
│   │   └── conversation_memory.py  # SQLite-backed chat memory
│   ├── features/
│   │   ├── flashcards.py
│   │   └── roadmap.py
│   └── voice/
│       └── voice_io.py             # optional STT/TTS
├── frontend/
│   └── app.py                      # Streamlit UI
├── tests/
│   └── test_basic.py
├── scripts/
│   └── run.sh                      # start backend + frontend together
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env.example
└── README.md
```

## 🚀 Quickstart

### 1. Clone & set up environment

```bash
git clone https://github.com/<your-username>/multi-agent-research-assistant.git
cd multi-agent-research-assistant

python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

### 2. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env`:
- Set `LLM_PROVIDER=openai` and `OPENAI_API_KEY=...` (or `LLM_PROVIDER=gemini` with `GOOGLE_API_KEY=...`)
- `EMBEDDING_PROVIDER=huggingface` works **out of the box with no API key** (runs locally).
  Set it to `openai` if you'd rather use OpenAI embeddings.

### 3. Run the app

**Option A — one command (Linux/Mac):**
```bash
bash scripts/run.sh
```

**Option B — run manually in two terminals:**
```bash
# Terminal 1
uvicorn backend.main:app --reload --port 8000

# Terminal 2
streamlit run frontend/app.py
```

Then open **http://localhost:8501** in your browser. The API docs are at
**http://localhost:8000/docs** (FastAPI Swagger UI).

### 4. Run with Docker

```bash
docker-compose up --build
```

## 🧪 Running tests

```bash
pytest tests/ -v
```

## 🔍 How the multi-agent pipeline works

1. **Ingestion**: PDF is parsed page-by-page (PyMuPDF), then chunked with overlap
   while preserving exact page metadata; chunks are embedded and stored in ChromaDB.
2. **Research Agent**: retrieves the top-k relevant chunks for a question and
   drafts findings *strictly grounded* in retrieved text.
3. **Summarization Agent**: condenses those findings into a clear, readable answer.
4. **Citation Agent**: deduplicates and formats the exact `filename + page number`
   for every retrieved chunk that contributed to the answer — no hallucinated citations,
   since page numbers come straight from ingestion metadata, not the LLM.
5. **Quiz Generator Agent** / **Flashcard feature**: same retrieval-grounded approach,
   producing structured JSON (MCQs / flashcards) validated against the source content.

All of this is orchestrated as a **LangGraph `StateGraph`** (`backend/agents/graph.py`),
so it's easy to extend — e.g. add a routing/supervisor node, parallel branches, or
new agents (translation, plagiarism-check, etc.) without rewriting the pipeline.

## 🛠️ Extending the project

- **Swap LLM providers**: change `LLM_PROVIDER` in `.env` — code already supports OpenAI & Gemini via `backend/config.py::get_llm()`.
- **Swap vector DB**: `backend/vectorstore/store.py` is a thin wrapper — swap ChromaDB for FAISS/Pinecone/Weaviate by changing this file only.
- **Add a new agent**: write a function in `backend/agents/`, add a node + edge in `backend/agents/graph.py`.
- **Switch frontend to React**: the FastAPI backend is fully decoupled — any frontend can call its REST endpoints (`/chat`, `/flashcards`, `/quiz`, `/roadmap`, `/upload`).

## ⚠️ Notes & limitations

- Scanned/image-only PDFs won't extract text (no OCR included by default) — add `pytesseract` if needed.
- The free `EMBEDDING_PROVIDER=huggingface` runs a local sentence-transformers model on CPU; the first run downloads the model (~90MB).
- Voice transcription uses the free Google Web Speech API via `SpeechRecognition`, which requires an internet connection and has rate limits; for production, swap in Whisper API.

## 📄 License

MIT — free to use, modify, and build on for personal or academic projects.
