"""
Command-line interface for the Text-to-SQL Agent.

Usage:
    python app/main.py
Then type natural-language questions about the company database.
Type 'exit' to quit.
"""

from agent import ask


def main():
    print("=" * 60)
    print(" Text-to-SQL Agent (LangGraph)")
    print(" Ask questions about the company database in plain English.")
    print(" Type 'exit' to quit.")
    print("=" * 60)

    while True:
        question = input("\nYour question: ").strip()
        if question.lower() in ("exit", "quit"):
            print("Goodbye!")
            break
        if not question:
            continue

        result = ask(question)

        print(f"\nGenerated SQL:\n  {result['sql_query']}")
        print(f"\nAnswer:\n  {result['final_answer']}")


if __name__ == "__main__":
    main()
