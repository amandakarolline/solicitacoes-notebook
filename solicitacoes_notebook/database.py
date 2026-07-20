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

    pk     = "SERIAL PRIMARY KEY" if modo == "postgres" else "INTEGER PRIMARY KEY AUTOINCREMENT"
    ignore = "ON CONFLICT DO NOTHING" if modo == "postgres" else "OR IGNORE"
    num    = "NUMERIC" if modo == "postgres" else "REAL"
    today  = "CURRENT_DATE" if modo == "postgres" else "(date('now'))"

    # ─── Tabelas de lookup ────────────────────────────────────────────────────

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

    # ─── Solicitações de equipamentos ─────────────────────────────────────────

    if modo == "postgres":
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS solicitacoes (
                id                {pk},
                ticket            TEXT NOT NULL,
                data_solicitacao  DATE NOT NULL DEFAULT {today},
                equipamento       TEXT NOT NULL DEFAULT 'NOTEBOOK',
                valor             {num} NOT NULL,
                numero_nf         TEXT,
                setor_id          INTEGER REFERENCES setores(id),
                solicitante_id    INTEGER REFERENCES pessoas(id),
                motivo_id         INTEGER REFERENCES motivos(id),
                colaborador_id    INTEGER REFERENCES pessoas(id),
                autorizado_por_id INTEGER REFERENCES pessoas(id),
                status_id         INTEGER REFERENCES status(id),
                fornecedor_id     INTEGER REFERENCES fornecedores(id)
            )
        """)
    else:
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS solicitacoes (
                id                {pk},
                ticket            TEXT NOT NULL,
                data_solicitacao  DATE NOT NULL DEFAULT {today},
                equipamento       TEXT NOT NULL DEFAULT 'NOTEBOOK',
                valor             {num} NOT NULL,
                numero_nf         TEXT,
                setor_id          INTEGER,
                solicitante_id    INTEGER,
                motivo_id         INTEGER,
                colaborador_id    INTEGER,
                autorizado_por_id INTEGER,
                status_id         INTEGER,
                fornecedor_id     INTEGER,
                FOREIGN KEY (setor_id)          REFERENCES setores(id),
                FOREIGN KEY (solicitante_id)    REFERENCES pessoas(id),
                FOREIGN KEY (motivo_id)         REFERENCES motivos(id),
                FOREIGN KEY (colaborador_id)    REFERENCES pessoas(id),
                FOREIGN KEY (autorizado_por_id) REFERENCES pessoas(id),
                FOREIGN KEY (status_id)         REFERENCES status(id),
                FOREIGN KEY (fornecedor_id)     REFERENCES fornecedores(id)
            )
        """)

    # ─── Despesas e Serviços ──────────────────────────────────────────────────

    if modo == "postgres":
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS despesas (
                id                {pk},
                ticket            TEXT,
                descricao         TEXT NOT NULL,
                data_despesa      DATE NOT NULL DEFAULT {today},
                valor             {num} NOT NULL,
                numero_nf         TEXT,
                setor_id          INTEGER REFERENCES setores(id),
                fornecedor_id     INTEGER REFERENCES fornecedores(id),
                autorizado_por_id INTEGER REFERENCES pessoas(id),
                status_id         INTEGER REFERENCES status(id)
            )
        """)
    else:
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS despesas (
                id                {pk},
                ticket            TEXT,
                descricao         TEXT NOT NULL,
                data_despesa      DATE NOT NULL DEFAULT {today},
                valor             {num} NOT NULL,
                numero_nf         TEXT,
                setor_id          INTEGER,
                fornecedor_id     INTEGER,
                autorizado_por_id INTEGER,
                status_id         INTEGER,
                FOREIGN KEY (setor_id)          REFERENCES setores(id),
                FOREIGN KEY (fornecedor_id)     REFERENCES fornecedores(id),
                FOREIGN KEY (autorizado_por_id) REFERENCES pessoas(id),
                FOREIGN KEY (status_id)         REFERENCES status(id)
            )
        """)

    # ─── Dados iniciais ───────────────────────────────────────────────────────

    status_iniciais = [
        ("ENTREGUE",),
        ("PENDENTE ENTREGA",),
        ("NÃO FOI NECESSÁRIO",),
        ("PAGO",),
        ("PENDENTE PAGAMENTO",),
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
        if modo == "postgres":
            cursor.execute(f"INSERT INTO status (descricao) VALUES (%s) {ignore}", (descricao,))
        else:
            cursor.execute(f"INSERT {ignore} INTO status (descricao) VALUES (?)", (descricao,))

    for descricao, in motivos_iniciais:
        if modo == "postgres":
            cursor.execute(f"INSERT INTO motivos (descricao) VALUES (%s) {ignore}", (descricao,))
        else:
            cursor.execute(f"INSERT {ignore} INTO motivos (descricao) VALUES (?)", (descricao,))

    conn.commit()
    conn.close()
    print("Banco de dados criado/atualizado com sucesso! ✅")


if __name__ == "__main__":
    criar_banco()