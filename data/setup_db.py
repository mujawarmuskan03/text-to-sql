"""
Sets up a sample SQLite database for the Text-to-SQL Agent to query.
Creates a small "company" database with employees, departments, and sales
tables so the agent has something realistic to demo against.

Run this once before using the agent:
    python data/setup_db.py
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "company.db")


def create_database():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.executescript(
        """
        CREATE TABLE departments (
            department_id INTEGER PRIMARY KEY,
            department_name TEXT NOT NULL,
            location TEXT NOT NULL
        );

        CREATE TABLE employees (
            employee_id INTEGER PRIMARY KEY,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            department_id INTEGER,
            role TEXT NOT NULL,
            salary REAL NOT NULL,
            hire_date TEXT NOT NULL,
            FOREIGN KEY (department_id) REFERENCES departments(department_id)
        );

        CREATE TABLE sales (
            sale_id INTEGER PRIMARY KEY,
            employee_id INTEGER,
            product_name TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            unit_price REAL NOT NULL,
            sale_date TEXT NOT NULL,
            FOREIGN KEY (employee_id) REFERENCES employees(employee_id)
        );
        """
    )

    departments = [
        (1, "Engineering", "Bangalore"),
        (2, "Sales", "Mumbai"),
        (3, "Marketing", "Delhi"),
        (4, "Human Resources", "Pune"),
        (5, "Finance", "Bangalore"),
    ]
    cur.executemany(
        "INSERT INTO departments VALUES (?, ?, ?)", departments
    )

    employees = [
        (1, "Aarav", "Sharma", 1, "Software Engineer", 850000, "2022-03-14"),
        (2, "Priya", "Verma", 1, "Senior Software Engineer", 1350000, "2020-06-01"),
        (3, "Rohan", "Mehta", 2, "Sales Executive", 620000, "2021-11-23"),
        (4, "Ishita", "Kapoor", 2, "Sales Manager", 1100000, "2019-02-17"),
        (5, "Kabir", "Singh", 3, "Marketing Analyst", 700000, "2023-01-09"),
        (6, "Ananya", "Iyer", 3, "Marketing Manager", 1050000, "2020-09-30"),
        (7, "Vikram", "Nair", 4, "HR Executive", 550000, "2022-07-19"),
        (8, "Sanya", "Chopra", 5, "Financial Analyst", 780000, "2021-04-05"),
        (9, "Arjun", "Reddy", 1, "Data Engineer", 950000, "2023-05-22"),
        (10, "Meera", "Pillai", 5, "Finance Manager", 1400000, "2018-12-11"),
    ]
    cur.executemany(
        "INSERT INTO employees VALUES (?, ?, ?, ?, ?, ?, ?)", employees
    )

    sales = [
        (1, 3, "CRM License", 5, 25000, "2026-01-15"),
        (2, 3, "Analytics Suite", 2, 60000, "2026-02-10"),
        (3, 4, "CRM License", 10, 25000, "2026-02-20"),
        (4, 4, "Enterprise Bundle", 1, 500000, "2026-03-05"),
        (5, 3, "Support Plan", 8, 12000, "2026-03-18"),
        (6, 4, "Analytics Suite", 4, 60000, "2026-04-02"),
        (7, 3, "CRM License", 3, 25000, "2026-04-28"),
        (8, 4, "Support Plan", 15, 12000, "2026-05-11"),
    ]
    cur.executemany(
        "INSERT INTO sales VALUES (?, ?, ?, ?, ?, ?)", sales
    )

    conn.commit()
    conn.close()
    print(f"Database created at: {DB_PATH}")


if __name__ == "__main__":
    create_database()
