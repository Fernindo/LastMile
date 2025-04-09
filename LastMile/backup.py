import os

def clean_sql_file():
    input_path = r"C:\Users\slaso\Desktop\LastMile\backup_inserts.sql"
    output_path = r"C:\Users\slaso\Desktop\LastMile\backup_tables_only.sql"

    skip_keywords = [
        "DROP DATABASE", "CREATE DATABASE", "\\connect",
        "SET statement_timeout", "SET lock_timeout", "SET idle_in_transaction_session_timeout",
        "SET transaction_timeout", "SET client_encoding", "SET standard_conforming_strings",
        "SELECT pg_catalog.set_config", "SET check_function_bodies", "SET xmloption",
        "SET client_min_messages", "SET row_security"
    ]

    with open(input_path, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()

    cleaned_lines = [line for line in lines if not any(keyword in line for keyword in skip_keywords)]

    with open(output_path, "w", encoding="utf-8") as f:
        f.writelines(cleaned_lines)

    print(f"✅ Cleaned file saved to:\n{output_path}")

if __name__ == "__main__":
    clean_sql_file()
