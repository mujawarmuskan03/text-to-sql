"""
Simple Streamlit UI for the Text-to-SQL Agent.
Great for a live project demo/viva instead of a terminal.

Run with:
    streamlit run app/streamlit_app.py
"""

import streamlit as st
from agent import ask, get_db_schema

st.set_page_config(page_title="Text-to-SQL Agent", page_icon="🗄️")

st.title("🗄️ Text-to-SQL Agent")
st.caption("Built with LangGraph — ask questions about the company database in plain English.")

with st.expander("📋 View database schema"):
    st.code(get_db_schema())

st.markdown("**Example questions:**")
st.markdown(
    "- Who are the top 3 highest paid employees?\n"
    "- What is the total sales revenue by product?\n"
    "- Which department has the most employees?\n"
    "- List all employees hired after 2022."
)

question = st.text_input("Ask a question about the data:")

if st.button("Run") and question:
    with st.spinner("Thinking..."):
        result = ask(question)

    st.subheader("Generated SQL")
    st.code(result["sql_query"], language="sql")

    st.subheader("Raw Result")
    st.text(result["query_result"])

    st.subheader("Answer")
    st.success(result["final_answer"])

    if result.get("retries", 0) > 0:
        st.info(f"Agent self-corrected {result['retries']} time(s) before succeeding.")
