"""
Streamlit frontend for the Multi-Agent Research Assistant.
Talks to the FastAPI backend over HTTP.
"""
import uuid
import streamlit as st
import requests

BACKEND_URL = st.secrets.get("BACKEND_URL", "http://localhost:8000") if hasattr(st, "secrets") else "http://localhost:8000"
try:
    import os
    BACKEND_URL = os.environ.get("BACKEND_URL", BACKEND_URL)
except Exception:
    pass

st.set_page_config(page_title="Multi-Agent Research Assistant", page_icon="🧠", layout="wide")

if "session_id" not in st.session_state:
    st.session_state.session_id = uuid.uuid4().hex[:12]
if "chat_log" not in st.session_state:
    st.session_state.chat_log = []
if "docs" not in st.session_state:
    st.session_state.docs = []

st.title("🧠 Multi-Agent Research Assistant")
st.caption("Upload papers, ask questions, and let Research / Summarization / Citation / Quiz agents do the work.")

# ---------------------------------------------------------------------------
# Sidebar: document upload & management
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("📄 Documents")
    uploaded = st.file_uploader("Upload a PDF", type=["pdf"])
    if uploaded and st.button("Ingest PDF", use_container_width=True):
        with st.spinner("Extracting text, chunking, and embedding..."):
            files = {"file": (uploaded.name, uploaded.getvalue(), "application/pdf")}
            r = requests.post(f"{BACKEND_URL}/upload", files=files, timeout=300)
        if r.status_code == 200:
            data = r.json()
            st.success(f"Ingested '{data['filename']}' - {data['num_pages']} pages, {data['num_chunks']} chunks.")
        else:
            st.error(f"Upload failed: {r.text}")

    st.divider()
    try:
        docs_resp = requests.get(f"{BACKEND_URL}/documents", timeout=30)
        docs = docs_resp.json() if docs_resp.status_code == 200 else []
    except requests.exceptions.ConnectionError:
        docs = []
        st.warning("Backend not reachable. Start it with `uvicorn backend.main:app --reload`.")

    st.session_state.docs = docs
    if docs:
        st.write(f"**{len(docs)} document(s) uploaded:**")
        for d in docs:
            col1, col2 = st.columns([4, 1])
            col1.write(f"📘 {d['filename']} ({d['num_pages']}p)")
            if col2.button("🗑️", key=f"del_{d['doc_id']}"):
                requests.delete(f"{BACKEND_URL}/documents/{d['doc_id']}")
                st.rerun()
    else:
        st.info("No documents uploaded yet.")

    st.divider()
    restrict = st.checkbox("Restrict Q&A to selected docs only", value=False)
    selected_doc_ids = None
    if restrict and docs:
        chosen = st.multiselect("Select documents", options=[d["filename"] for d in docs])
        selected_doc_ids = [d["doc_id"] for d in docs if d["filename"] in chosen] or None

# ---------------------------------------------------------------------------
# Main tabs
# ---------------------------------------------------------------------------
tab_chat, tab_flash, tab_quiz, tab_roadmap, tab_voice = st.tabs(
    ["💬 Chat", "🗂️ Flashcards", "📝 Quiz", "🗺️ Study Roadmap", "🎙️ Voice"]
)

# ---------------- Chat tab ----------------
with tab_chat:
    for turn in st.session_state.chat_log:
        with st.chat_message(turn["role"]):
            st.markdown(turn["content"])
            if turn.get("citations"):
                with st.expander("📌 Sources & page citations"):
                    for c in turn["citations"]:
                        st.markdown(f"- **{c['filename']}**, page {c['page']}: _{c['snippet']}_")
            if turn.get("agent_trace"):
                st.caption("Agents used: " + " → ".join(turn["agent_trace"]))

    question = st.chat_input("Ask a question about your documents...")
    if question:
        st.session_state.chat_log.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)
        with st.chat_message("assistant"):
            with st.spinner("Research → Summarization → Citation agents working..."):
                payload = {"session_id": st.session_state.session_id, "question": question, "doc_ids": selected_doc_ids}
                r = requests.post(f"{BACKEND_URL}/chat", json=payload, timeout=180)
            if r.status_code == 200:
                data = r.json()
                st.markdown(data["summary"])
                if data["citations"]:
                    with st.expander("📌 Sources & page citations"):
                        for c in data["citations"]:
                            st.markdown(f"- **{c['filename']}**, page {c['page']}: _{c['snippet']}_")
                st.caption("Agents used: " + " → ".join(data["agent_trace"]))
                st.session_state.chat_log.append(
                    {"role": "assistant", "content": data["summary"], "citations": data["citations"], "agent_trace": data["agent_trace"]}
                )
            else:
                st.error(f"Error: {r.text}")

# ---------------- Flashcards tab ----------------
with tab_flash:
    st.subheader("Generate flashcards from your documents")
    topic = st.text_input("Topic (optional - leave blank for general coverage)", key="fc_topic")
    num_cards = st.slider("Number of flashcards", 5, 30, 10)
    if st.button("Generate Flashcards"):
        with st.spinner("Quiz/Flashcard agent generating cards..."):
            payload = {"session_id": st.session_state.session_id, "topic": topic, "num_cards": num_cards, "doc_ids": selected_doc_ids}
            r = requests.post(f"{BACKEND_URL}/flashcards", json=payload, timeout=180)
        if r.status_code == 200:
            cards = r.json()["flashcards"]
            if not cards:
                st.warning("No flashcards could be generated - try uploading documents first.")
            for i, c in enumerate(cards):
                with st.expander(f"Card {i+1}: {c['question']}"):
                    st.write(c["answer"])
                    if c.get("source_page"):
                        st.caption(f"Source: {c['source_page']}")
        else:
            st.error(f"Error: {r.text}")

# ---------------- Quiz tab ----------------
with tab_quiz:
    st.subheader("Generate a quiz to test yourself")
    q_topic = st.text_input("Topic (optional)", key="quiz_topic")
    num_q = st.slider("Number of questions", 3, 15, 5)
    difficulty = st.select_slider("Difficulty", options=["easy", "medium", "hard"], value="medium")
    if st.button("Generate Quiz"):
        with st.spinner("Quiz Generator Agent working..."):
            payload = {
                "session_id": st.session_state.session_id, "topic": q_topic,
                "num_questions": num_q, "difficulty": difficulty, "doc_ids": selected_doc_ids,
            }
            r = requests.post(f"{BACKEND_URL}/quiz", json=payload, timeout=180)
        if r.status_code == 200:
            questions = r.json()["questions"]
            if not questions:
                st.warning("No quiz could be generated - try uploading documents first.")
            for i, q in enumerate(questions):
                st.markdown(f"**Q{i+1}. {q['question']}**")
                choice = st.radio("Options", q["options"], key=f"quiz_{i}", label_visibility="collapsed")
                if st.button("Check answer", key=f"check_{i}"):
                    if choice == q["correct_answer"]:
                        st.success(f"Correct! {q['explanation']}")
                    else:
                        st.error(f"Incorrect. Correct answer: {q['correct_answer']}\n\n{q['explanation']}")
                if q.get("source_page"):
                    st.caption(f"Source: {q['source_page']}")
                st.divider()
        else:
            st.error(f"Error: {r.text}")

# ---------------- Roadmap tab ----------------
with tab_roadmap:
    st.subheader("Generate a personalized study roadmap")
    goal = st.text_area("What's your study goal?", placeholder="e.g. Master transformer architectures for my thesis in 4 weeks")
    weeks = st.slider("Number of weeks", 1, 12, 4)
    if st.button("Generate Roadmap"):
        with st.spinner("Roadmap agent planning your study path..."):
            payload = {"session_id": st.session_state.session_id, "goal": goal, "weeks": weeks, "doc_ids": selected_doc_ids}
            r = requests.post(f"{BACKEND_URL}/roadmap", json=payload, timeout=180)
        if r.status_code == 200:
            plan = r.json()["weeks"]
            for w in plan:
                st.markdown(f"### Week {w['week']}: {w['title']}")
                st.markdown("**Topics:** " + ", ".join(w["topics"]))
                st.markdown("**Tasks:**")
                for t in w["tasks"]:
                    st.markdown(f"- {t}")
                st.markdown("**Resources:**")
                for res in w["resources"]:
                    st.markdown(f"- {res}")
                st.divider()
        else:
            st.error(f"Error: {r.text}")

# ---------------- Voice tab ----------------
with tab_voice:
    st.subheader("🎙️ Voice input/output (optional)")
    st.caption("Record or upload a short WAV clip to transcribe it into a question, or generate speech from text.")

    audio_file = st.file_uploader("Upload a WAV audio clip", type=["wav"], key="voice_upload")
    if audio_file and st.button("Transcribe"):
        with st.spinner("Transcribing..."):
            files = {"file": (audio_file.name, audio_file.getvalue(), "audio/wav")}
            r = requests.post(f"{BACKEND_URL}/voice/transcribe", files=files, timeout=60)
        if r.status_code == 200:
            st.session_state["voice_text"] = r.json()["text"]
            st.success(f"Transcribed: {st.session_state['voice_text']}")
        else:
            st.error(f"Error: {r.text}")

    tts_text = st.text_area("Text to speak", value=st.session_state.get("voice_text", ""))
    if st.button("Generate Speech") and tts_text.strip():
        with st.spinner("Synthesizing speech..."):
            r = requests.post(f"{BACKEND_URL}/voice/speak", params={"text": tts_text}, timeout=60)
        if r.status_code == 200:
            st.audio(r.content, format="audio/mpeg")
        else:
            st.error(f"Error: {r.text}")
