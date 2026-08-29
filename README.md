# Text-to-SQL Agent (LangGraph)

A self-correcting AI agent that converts natural-language questions into SQL
queries, executes them against a database, and returns a plain-English
answer. Built with **LangGraph** to demonstrate a real agentic workflow —
not just a single LLM call, but a graph with a retry/self-correction loop.

Live demo:-https://text-to-sql-qfi4xd3wao6msue85nz3qe.streamlit.app/



---

## Why this project

Most "chat with your database" tutorials just do: question → SQL → run it.
This project goes a step further: if the generated SQL fails (bad column
name, syntax error, etc.), the agent **feeds the error back to the LLM** and
asks it to fix the query — up to 3 attempts — before giving up. That
feedback loop is what makes it an *agent* rather than a script, and it's a
strong thing to highlight in your viva.

---

## Architecture

```
        ┌─────────────┐
        │  get_schema │
        └──────┬──────┘
               ▼
       ┌───────────────┐
   ┌──▶│ generate_sql   │
   │   └───────┬───────┘
   │           ▼
   │   ┌───────────────┐
   │   │  execute_sql   │
   │   └───────┬───────┘
   │           ▼
   │     error? ──yes──► retries < 3? ──yes──┘  (loop back)
   │           │                │
   │           no               no (give up)
   │           ▼                ▼
   │  ┌─────────────────┐  ┌──────────┐
   └──│ generate_answer │  │ give_up  │
      └────────┬────────┘  └────┬─────┘
               ▼                ▼
              END               END
```

**Nodes:**
| Node | Purpose |
|---|---|
| `get_schema` | Reads table/column names from SQLite so the LLM knows what it can query |
| `generate_sql` | LLM converts the question (+ any previous error) into SQL |
| `execute_sql` | Runs the SQL; captures success or error |
| `generate_answer` | LLM turns raw rows into a plain-English answer |
| `give_up` | Returns a clear failure message after 3 failed attempts |

**Safety guard:** the agent only allows `SELECT` statements — any generated
query containing `INSERT`/`UPDATE`/`DELETE`/`DROP`/`ALTER` is rejected before
it ever touches the database.

---

## Tech stack

- **LangGraph** — orchestrates the agent as a state graph with a retry loop
- **Llama 3.3 70B (via Groq API, free tier)** — generates SQL and natural-language answers
- **SQLite** — lightweight sample database (no server setup needed)
- **Streamlit** — optional web UI for demos

---

## Setup

1. **Clone / copy this project**, then install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up your API key:**
   ```bash
   cp .env.example .env
   # edit .env and add your GROQ_API_KEY
   ```

3. **Create the sample database:**
   ```bash
   python data/setup_db.py
   ```

4. **Run it — two options:**

   **CLI:**
   ```bash
   cd app
   python main.py
   ```

   **Web UI (recommended for demos):**
   ```bash
   streamlit run app/streamlit_app.py
   ```

---

## Example questions to try

- "Who are the top 3 highest paid employees?"
- "What is the total sales revenue by product?"
- "Which department has the most employees?"
- "List all employees hired after 2022."
- "What is the average salary in the Engineering department?"

---

## Sample database schema

Three tables, pre-populated with sample data:

- **departments** — department_id, department_name, location
- **employees** — employee_id, first_name, last_name, department_id, role, salary, hire_date
- **sales** — sale_id, employee_id, product_name, quantity, unit_price, sale_date

You can swap in your own SQLite database by replacing `data/company.db` and
updating `DB_PATH` in `app/agent.py` — the agent reads the schema
dynamically, so no other code changes are needed.

---

## Possible extensions (good for "future scope" in your report)

- Support PostgreSQL/MySQL instead of SQLite
- Add a chat history so follow-up questions ("now filter by 2026") work
- Add query result visualization (charts) in the Streamlit UI
- Add a confirmation step before running queries on a production database
- Log all generated queries for auditing

---

## Project structure

```
text-to-sql-agent/
├── app/
│   ├── agent.py           # LangGraph agent definition
│   ├── main.py             # CLI interface
│   └── streamlit_app.py    # Web UI
├── data/
│   └── setup_db.py         # Creates the sample SQLite database
├── requirements.txt
├── .env.example
└── README.md
```

---

## License

MIT — free to use and modify for academic or personal projects.
