
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


##  How the multi-agent pipeline works

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


