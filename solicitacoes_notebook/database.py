"""
database.py
Cria as tabelas e insere dados iniciais.

- Com DATABASE_URL no ambiente: usa PostgreSQL (produção/Supabase)
- Sem DATABASE_URL: usa SQLite local (desenvolvimento)

Uso local:
    poetry run python solicitacoes_notebook/database.py

Uso produção (Supabase):
    DATABASE_URL="postgresql://..." poetry run python solicitacoes_notebook/database.py
"""

import os
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "solicitacoes.db"

DATABASE_URL = os.environ.get("DATABASE_URL")


def get_connection():
    if DATABASE_URL:
        import psycopg2
        print("Conectando ao PostgreSQL...")
        return psycopg2.connect(DATABASE_URL), "postgres"
    else:
        print(f"Usando SQLite local em: {DB_PATH}")
        return sqlite3.connect(DB_PATH), "sqlite"


def criar_banco():
    conn, modo = get_connection()
    cursor = conn.cursor()

    if modo == "sqlite":
        cursor.execute("PRAGMA foreign_keys = ON;")

    # ─── Tipo serial/autoincrement dependendo do banco ────────────────────────
    pk = "SERIAL PRIMARY KEY" if modo == "postgres" else "INTEGER PRIMARY KEY AUTOINCREMENT"
    ignore = "ON CONFLICT DO NOTHING" if modo == "postgres" else "OR IGNORE"

    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS setores (
            id   {pk},
            nome TEXT NOT NULL UNIQUE
        )
    """)

    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS pessoas (
            id   {pk},
            nome TEXT NOT NULL UNIQUE
        )
    """)

    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS motivos (
            id        {pk},
            descricao TEXT NOT NULL UNIQUE
        )
    """)

    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS fornecedores (
            id   {pk},
            nome TEXT NOT NULL UNIQUE
        )
    """)

    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS status (
            id        {pk},
            descricao TEXT NOT NULL UNIQUE
        )
    """)

    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS solicitacoes (
            id                {pk},
            ticket            TEXT NOT NULL,
            data_solicitacao  DATE NOT NULL DEFAULT {'CURRENT_DATE' if modo == 'postgres' else "(date('now'))"},
            equipamento       TEXT NOT NULL DEFAULT 'NOTEBOOK',
            valor             {'NUMERIC' if modo == 'postgres' else 'REAL'} NOT NULL,
            numero_nf         TEXT,

            setor_id          INTEGER {'REFERENCES setores(id)' if modo == 'postgres' else ''},
            solicitante_id    INTEGER {'REFERENCES pessoas(id)' if modo == 'postgres' else ''},
            motivo_id         INTEGER {'REFERENCES motivos(id)' if modo == 'postgres' else ''},
            colaborador_id    INTEGER {'REFERENCES pessoas(id)' if modo == 'postgres' else ''},
            autorizado_por_id INTEGER {'REFERENCES pessoas(id)' if modo == 'postgres' else ''},
            status_id         INTEGER {'REFERENCES status(id)' if modo == 'postgres' else ''},
            fornecedor_id     INTEGER {'REFERENCES fornecedores(id)' if modo == 'postgres' else ''}
            {'' if modo == 'postgres' else ''',
            FOREIGN KEY (setor_id)          REFERENCES setores(id),
            FOREIGN KEY (solicitante_id)    REFERENCES pessoas(id),
            FOREIGN KEY (motivo_id)         REFERENCES motivos(id),
            FOREIGN KEY (colaborador_id)    REFERENCES pessoas(id),
            FOREIGN KEY (autorizado_por_id) REFERENCES pessoas(id),
            FOREIGN KEY (status_id)         REFERENCES status(id),
            FOREIGN KEY (fornecedor_id)     REFERENCES fornecedores(id)'''}
        )
    """)

    # ─── Dados iniciais ───────────────────────────────────────────────────────
    status_iniciais = [
        ("ENTREGUE",),
        ("PENDENTE ENTREGA",),
        ("NÃO FOI NECESSÁRIO",),
    ]
    motivos_iniciais = [
        ("UPGRADE SETOR",),
        ("UTILIZA NOTEBOOK PESSOAL",),
        ("MUDANÇA DE FUNÇÃO",),
        ("EQUIPAMENTO OBSOLETO",),
        ("NOVO COLABORADOR",),
        ("SUBSTITUIÇÃO",),
        ("EQUIPAMENTO DANIFICADO",),
    ]

    for descricao, in status_iniciais:
        cursor.execute(f"INSERT INTO status (descricao) VALUES (%s) {ignore}" if modo == "postgres"
                       else f"INSERT {ignore} INTO status (descricao) VALUES (?)", (descricao,))

    for descricao, in motivos_iniciais:
        cursor.execute(f"INSERT INTO motivos (descricao) VALUES (%s) {ignore}" if modo == "postgres"
                       else f"INSERT {ignore} INTO motivos (descricao) VALUES (?)", (descricao,))

    conn.commit()
    conn.close()
    print("Banco de dados criado/atualizado com sucesso! ✅")


if __name__ == "__main__":
    criar_banco()