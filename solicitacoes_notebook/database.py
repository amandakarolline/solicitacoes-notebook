import sqlite3
from pathlib import Path

# ─── Caminho correto: 1 nível acima (raiz do projeto) ─────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "solicitacoes.db"


def criar_banco():
    """Cria todas as tabelas e insere dados iniciais no SQLite local."""
    conexao = sqlite3.connect(DB_PATH)
    cursor = conexao.cursor()

    cursor.execute("PRAGMA foreign_keys = ON;")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS setores (
            id   INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL UNIQUE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pessoas (
            id   INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL UNIQUE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS motivos (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            descricao TEXT NOT NULL UNIQUE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fornecedores (
            id   INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL UNIQUE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS status (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            descricao TEXT NOT NULL UNIQUE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS solicitacoes (
            id                INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket            TEXT NOT NULL,
            data_solicitacao  DATE NOT NULL DEFAULT (date('now')),
            equipamento       TEXT NOT NULL DEFAULT 'NOTEBOOK',
            valor             REAL NOT NULL,
            numero_nf         TEXT,

            setor_id          INTEGER,
            solicitante_id    INTEGER,
            motivo_id         INTEGER,
            colaborador_id    INTEGER,
            autorizado_por_id INTEGER,
            status_id         INTEGER,
            fornecedor_id     INTEGER,

            FOREIGN KEY (setor_id)          REFERENCES setores (id),
            FOREIGN KEY (solicitante_id)    REFERENCES pessoas (id),
            FOREIGN KEY (motivo_id)         REFERENCES motivos (id),
            FOREIGN KEY (colaborador_id)    REFERENCES pessoas (id),
            FOREIGN KEY (autorizado_por_id) REFERENCES pessoas (id),
            FOREIGN KEY (status_id)         REFERENCES status (id),
            FOREIGN KEY (fornecedor_id)     REFERENCES fornecedores (id)
        )
    """)

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

    cursor.executemany("INSERT OR IGNORE INTO status   (descricao) VALUES (?)", status_iniciais)
    cursor.executemany("INSERT OR IGNORE INTO motivos  (descricao) VALUES (?)", motivos_iniciais)

    conexao.commit()
    conexao.close()
    print(f"Banco de dados criado/atualizado em: {DB_PATH}")


if __name__ == "__main__":
    criar_banco()
