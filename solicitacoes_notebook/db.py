"""
db.py — Conexão centralizada com o banco de dados.
Usado por todas as páginas do app Streamlit.

- Com DATABASE_URL nos Streamlit Secrets → PostgreSQL (produção)
- Sem DATABASE_URL                       → SQLite local (desenvolvimento)
"""

import sqlite3
from pathlib import Path

import streamlit as st

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "solicitacoes.db"


def get_connection():
    """Retorna (conn, modo) onde modo é 'postgres' ou 'sqlite'."""
    try:
        db_url = st.secrets["DATABASE_URL"]
        import psycopg2
        return psycopg2.connect(db_url), "postgres"
    except (KeyError, Exception):
        return sqlite3.connect(DB_PATH), "sqlite"


def placeholder(modo: str) -> str:
    """Retorna o placeholder de parâmetro correto para cada banco."""
    return "%s" if modo == "postgres" else "?"
