"""
LangGraph orchestration: wires Research -> Summarization -> Citation agents
into a single stateful workflow. This is the "multi-agent" core of the app.

Flow:
    START -> research_node -> summarization_node -> citation_node -> END

Each node reads/writes to a shared AgentState (a TypedDict), so agents can
build on each other's outputs while keeping clean separation of concerns.
"""
from typing import TypedDict, List, Optional
from langgraph.graph import StateGraph, END

from backend.agents.research_agent import run_research_agent
from backend.agents.summarization_agent import run_summarization_agent
from backend.agents.citation_agent import run_citation_agent


class AgentState(TypedDict, total=False):
    question: str
    history: str
    doc_ids: Optional[List[str]]
    research_output: str
    retrieved_chunks: list
    summary: str
    citations: list
    agent_trace: List[str]


def research_node(state: AgentState) -> AgentState:
    result = run_research_agent(state["question"], state.get("history", ""), state.get("doc_ids"))
    trace = state.get("agent_trace", []) + ["research_agent"]
    return {
        "research_output": result["research_output"],
        "retrieved_chunks": result["retrieved_chunks"],
        "agent_trace": trace,
    }


def summarization_node(state: AgentState) -> AgentState:
    summary = run_summarization_agent(state["question"], state["research_output"])
    trace = state.get("agent_trace", []) + ["summarization_agent"]
    return {"summary": summary, "agent_trace": trace}


def citation_node(state: AgentState) -> AgentState:
    citations = run_citation_agent(state.get("retrieved_chunks", []))
    trace = state.get("agent_trace", []) + ["citation_agent"]
    return {"citations": citations, "agent_trace": trace}


def build_graph():
    graph = StateGraph(AgentState)
    graph.add_node("research", research_node)
    graph.add_node("summarize", summarization_node)
    graph.add_node("cite", citation_node)

    graph.set_entry_point("research")
    graph.add_edge("research", "summarize")
    graph.add_edge("summarize", "cite")
    graph.add_edge("cite", END)

    return graph.compile()


_compiled_graph = None


def get_graph():
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_graph()
    return _compiled_graph


def run_pipeline(question: str, history: str = "", doc_ids: list[str] | None = None) -> AgentState:
    graph = get_graph()
    initial_state: AgentState = {
        "question": question,
        "history": history,
        "doc_ids": doc_ids,
        "agent_trace": [],
    }
    final_state = graph.invoke(initial_state)
    return final_state
