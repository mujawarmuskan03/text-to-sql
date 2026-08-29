"""
Text-to-SQL Agent built with LangGraph.

Pipeline (graph nodes):
    1. get_schema      -> reads the DB schema so the LLM knows the tables/columns
    2. generate_sql     -> LLM converts the natural-language question into SQL
    3. execute_sql       -> runs the SQL against SQLite
    4. fix_sql (loop)    -> if execution fails, feeds the error back to the LLM
                            and asks it to correct the query (max N retries)
    5. generate_answer  -> LLM turns the raw SQL result into a plain-English answer

This self-correction loop is the main "agentic" behavior: the agent doesn't
just generate SQL once and give up, it observes execution errors and retries.
"""

import os
import sqlite3
from typing import TypedDict, Optional

from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage

load_dotenv()  # reads the .env file in the project folder and loads GROQ_API_KEY

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "company.db")
MAX_RETRIES = 3

# On a fresh deployment (e.g. Streamlit Cloud), the .db file won't exist yet
# since it's excluded from git. Build it automatically the first time.
if not os.path.exists(DB_PATH):
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "data"))
    from setup_db import create_database
    create_database()

llm = ChatGroq(
    model=os.environ.get("GROQ_MODEL", "openai/gpt-oss-120b"),
    temperature=0,
)


# ---------------------------------------------------------------------------
# State definition
# ---------------------------------------------------------------------------
class AgentState(TypedDict):
    question: str
    schema: str
    sql_query: str
    query_result: Optional[str]
    error: Optional[str]
    retries: int
    final_answer: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def get_db_schema() -> str:
    """Reads table + column info from SQLite so the LLM knows what it can query."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cur.fetchall()]

    schema_parts = []
    for table in tables:
        cur.execute(f"PRAGMA table_info({table})")
        columns = cur.fetchall()
        col_desc = ", ".join(f"{c[1]} ({c[2]})" for c in columns)
        schema_parts.append(f"Table {table}: {col_desc}")

    conn.close()
    return "\n".join(schema_parts)


def run_sql(query: str):
    """Executes SQL and returns rows, or raises an exception with the DB error."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(query)
    rows = cur.fetchall()
    col_names = [desc[0] for desc in cur.description] if cur.description else []
    conn.close()
    return col_names, rows


# ---------------------------------------------------------------------------
# Graph nodes
# ---------------------------------------------------------------------------
def get_schema_node(state: AgentState) -> AgentState:
    state["schema"] = get_db_schema()
    return state


def generate_sql_node(state: AgentState) -> AgentState:
    system_prompt = f"""You are an expert SQL generator for a SQLite database.

Database schema:
{state['schema']}

Rules:
- Return ONLY the SQL query, no explanation, no markdown fences.
- Use standard SQLite syntax.
- Only generate SELECT queries. Never generate INSERT, UPDATE, DELETE, or DROP.
- If a previous attempt failed, fix it based on the error message provided.
"""

    user_content = f"Question: {state['question']}"
    if state.get("error"):
        user_content += (
            f"\n\nYour previous SQL query was:\n{state['sql_query']}\n"
            f"It failed with this error:\n{state['error']}\n"
            f"Please generate a corrected query."
        )

    response = llm.invoke(
        [SystemMessage(content=system_prompt), HumanMessage(content=user_content)]
    )
    sql = response.content.strip()
    # strip accidental markdown fences if the model adds them
    sql = sql.replace("```sql", "").replace("```", "").strip()

    state["sql_query"] = sql
    state["error"] = None
    return state


def execute_sql_node(state: AgentState) -> AgentState:
    query = state["sql_query"]

    # Basic safety guard: this agent is read-only by design.
    forbidden = ["insert", "update", "delete", "drop", "alter", "truncate"]
    if any(word in query.lower() for word in forbidden):
        state["error"] = "Refused: only SELECT queries are permitted."
        state["query_result"] = None
        return state

    try:
        col_names, rows = run_sql(query)
        if not rows:
            state["query_result"] = "No results found."
        else:
            formatted = [", ".join(col_names)]
            for row in rows[:50]:  # cap rows shown to the LLM
                formatted.append(", ".join(str(v) for v in row))
            state["query_result"] = "\n".join(formatted)
        state["error"] = None
    except Exception as e:
        state["error"] = str(e)
        state["query_result"] = None

    return state


def should_retry(state: AgentState) -> str:
    """Conditional edge: retry generation on error, else move to final answer."""
    if state.get("error") and state["retries"] < MAX_RETRIES:
        state["retries"] += 1
        return "retry"
    if state.get("error") and state["retries"] >= MAX_RETRIES:
        return "give_up"
    return "success"


def generate_answer_node(state: AgentState) -> AgentState:
    system_prompt = (
        "You turn raw SQL query results into a short, clear, plain-English "
        "answer for a non-technical user. Be concise. If relevant, mention "
        "specific numbers from the data."
    )
    user_content = (
        f"Question: {state['question']}\n"
        f"SQL used: {state['sql_query']}\n"
        f"Query result:\n{state['query_result']}\n\n"
        f"Answer the question in plain English."
    )
    response = llm.invoke(
        [SystemMessage(content=system_prompt), HumanMessage(content=user_content)]
    )
    state["final_answer"] = response.content.strip()
    return state


def give_up_node(state: AgentState) -> AgentState:
    state["final_answer"] = (
        f"I couldn't generate a working query after {MAX_RETRIES} attempts. "
        f"Last error: {state.get('error')}"
    )
    return state


# ---------------------------------------------------------------------------
# Build the graph
# ---------------------------------------------------------------------------
def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("get_schema", get_schema_node)
    graph.add_node("generate_sql", generate_sql_node)
    graph.add_node("execute_sql", execute_sql_node)
    graph.add_node("generate_answer", generate_answer_node)
    graph.add_node("give_up", give_up_node)

    graph.set_entry_point("get_schema")
    graph.add_edge("get_schema", "generate_sql")
    graph.add_edge("generate_sql", "execute_sql")

    graph.add_conditional_edges(
        "execute_sql",
        should_retry,
        {
            "retry": "generate_sql",
            "give_up": "give_up",
            "success": "generate_answer",
        },
    )

    graph.add_edge("generate_answer", END)
    graph.add_edge("give_up", END)

    return graph.compile()


def ask(question: str) -> dict:
    """Convenience wrapper: run the full graph for one question."""
    app = build_graph()
    initial_state: AgentState = {
        "question": question,
        "schema": "",
        "sql_query": "",
        "query_result": None,
        "error": None,
        "retries": 0,
        "final_answer": "",
    }
    result = app.invoke(initial_state)
    return result
