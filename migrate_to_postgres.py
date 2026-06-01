"""
migrate_to_postgres.py
Migra dados do SQLite local para um banco PostgreSQL (Supabase, Railway, etc.).

Uso:
    poetry run python solicitacoes_notebook/migrate_to_postgres.py

Variável de ambiente necessária (ou defina DATABASE_URL abaixo):
    export DATABASE_URL="postgresql://usuario:senha@host:5432/banco"
"""

import os
import sqlite3
from pathlib import Path

try:
    import psycopg2
    from psycopg2.extras import execute_values
except ImportError:
    raise SystemExit("psycopg2 não encontrado. Rode: pip install psycopg2-binary")

BASE_DIR = Path(__file__).resolve().parent.parent
SQLITE_PATH = BASE_DIR / "solicitacoes.db"

DATABASE_URL = os.environ.get("DATABASE_URL") or input("Cole a DATABASE_URL do PostgreSQL: ").strip()

DDL = """
CREATE TABLE IF NOT EXISTS setores (
    id   SERIAL PRIMARY KEY,
    nome TEXT NOT NULL UNIQUE
);
CREATE TABLE IF NOT EXISTS pessoas (
    id   SERIAL PRIMARY KEY,
    nome TEXT NOT NULL UNIQUE
);
CREATE TABLE IF NOT EXISTS motivos (
    id        SERIAL PRIMARY KEY,
    descricao TEXT NOT NULL UNIQUE
);
CREATE TABLE IF NOT EXISTS fornecedores (
    id   SERIAL PRIMARY KEY,
    nome TEXT NOT NULL UNIQUE
);
CREATE TABLE IF NOT EXISTS status (
    id        SERIAL PRIMARY KEY,
    descricao TEXT NOT NULL UNIQUE
);
CREATE TABLE IF NOT EXISTS solicitacoes (
    id                SERIAL PRIMARY KEY,
    ticket            TEXT NOT NULL,
    data_solicitacao  DATE NOT NULL DEFAULT CURRENT_DATE,
    equipamento       TEXT NOT NULL DEFAULT 'NOTEBOOK',
    valor             NUMERIC NOT NULL,
    numero_nf         TEXT,
    setor_id          INTEGER REFERENCES setores(id),
    solicitante_id    INTEGER REFERENCES pessoas(id),
    motivo_id         INTEGER REFERENCES motivos(id),
    colaborador_id    INTEGER REFERENCES pessoas(id),
    autorizado_por_id INTEGER REFERENCES pessoas(id),
    status_id         INTEGER REFERENCES status(id),
    fornecedor_id     INTEGER REFERENCES fornecedores(id)
);
"""

TABELAS_SIMPLES = [
    ("setores",     "nome"),
    ("pessoas",     "nome"),
    ("motivos",     "descricao"),
    ("fornecedores","nome"),
    ("status",      "descricao"),
]

def migrar():
    print(f"Lendo SQLite em: {SQLITE_PATH}")
    sqlite = sqlite3.connect(SQLITE_PATH)
    sqlite.row_factory = sqlite3.Row
    sc = sqlite.cursor()

    print("Conectando ao PostgreSQL...")
    pg = psycopg2.connect(DATABASE_URL)
    pc = pg.cursor()

    print("Criando tabelas no PostgreSQL...")
    pc.execute(DDL)
    pg.commit()

    # Tabelas de lookup
    for tabela, coluna in TABELAS_SIMPLES:
        sc.execute(f"SELECT id, {coluna} FROM {tabela}")
        rows = sc.fetchall()
        if rows:
            execute_values(
                pc,
                f"INSERT INTO {tabela} (id, {coluna}) VALUES %s ON CONFLICT DO NOTHING",
                [(r["id"], r[coluna]) for r in rows],
            )
            print(f"  {tabela}: {len(rows)} registros")

    # Solicitações
    sc.execute("SELECT * FROM solicitacoes")
    rows = sc.fetchall()
    if rows:
        cols = rows[0].keys()
        execute_values(
            pc,
            f"INSERT INTO solicitacoes ({', '.join(cols)}) VALUES %s ON CONFLICT DO NOTHING",
            [tuple(r) for r in rows],
        )
        print(f"  solicitacoes: {len(rows)} registros")

    # Atualiza sequences do PostgreSQL
    for tabela in ["setores", "pessoas", "motivos", "fornecedores", "status", "solicitacoes"]:
        pc.execute(f"SELECT setval(pg_get_serial_sequence('{tabela}', 'id'), COALESCE(MAX(id), 1)) FROM {tabela}")

    pg.commit()
    pg.close()
    sqlite.close()
    print("\nMigração concluída com sucesso! ✅")


if __name__ == "__main__":
    migrar()
