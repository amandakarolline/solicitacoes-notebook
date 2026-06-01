import flet as ft
import sqlite3
from datetime import datetime
from pathlib import Path

# ─── Caminho correto: 1 nível acima (raiz do projeto) ─────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "solicitacoes.db"


def main(page: ft.Page):
    page.title = "Gestão de Solicitações de Equipamentos"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 30
    page.vertical_alignment = ft.MainAxisAlignment.START
    page.scroll = ft.ScrollMode.AUTO

    def conectar_banco():
        return sqlite3.connect(DB_PATH)

    try:
        conn = conectar_banco()
        cursor = conn.cursor()
        cursor.execute("SELECT id, descricao FROM motivos")
        motivos_db = cursor.fetchall()
        cursor.execute("SELECT id, descricao FROM status")
        status_db = cursor.fetchall()
        conn.close()
    except sqlite3.OperationalError:
        page.add(
            ft.Text(
                "Erro: Banco de dados não encontrado. Rode o database.py primeiro!",
                color=ft.Colors.RED,
            )
        )
        return

    ticket_input     = ft.TextField(label="Número do Ticket",        width=300, prefix_icon="numbers")
    valor_input      = ft.TextField(label="Valor Total (R$)",         width=300, prefix_icon="monetization_on")
    setor_input      = ft.TextField(label="Setor (ex: Tesouraria)",   width=300, prefix_icon="domain")
    fornecedor_input = ft.TextField(label="Fornecedor (ex: IBYTE)",   width=300, prefix_icon="store")
    solicitante_input= ft.TextField(label="Solicitante",              width=300, prefix_icon="person")
    colaborador_input= ft.TextField(label="Colaborador (Destino)",    width=300, prefix_icon="person_outline")
    autorizado_input = ft.TextField(label="Autorizado por",           width=300, prefix_icon="verified_user")

    motivo_dropdown = ft.Dropdown(
        label="Motivo da Solicitação", width=300,
        options=[ft.dropdown.Option(key=str(m[0]), text=m[1]) for m in motivos_db],
    )
    status_dropdown = ft.Dropdown(
        label="Status Atual", width=300,
        options=[ft.dropdown.Option(key=str(s[0]), text=s[1]) for s in status_db],
    )

    def get_or_create(cursor, tabela, coluna, valor):
        if not valor:
            return None
        valor = valor.strip().upper()
        cursor.execute(f"SELECT id FROM {tabela} WHERE {coluna} = ?", (valor,))
        resultado = cursor.fetchone()
        if resultado:
            return resultado[0]
        cursor.execute(f"INSERT INTO {tabela} ({coluna}) VALUES (?)", (valor,))
        return cursor.lastrowid

    def salvar_solicitacao(e):
        if not ticket_input.value or not valor_input.value:
            page.snack_bar = ft.SnackBar(ft.Text("Por favor, preencha o Ticket e o Valor!"))
            page.snack_bar.open = True
            page.update()
            return

        try:
            conn = conectar_banco()
            cursor = conn.cursor()
            data_hoje = datetime.now().strftime("%Y-%m-%d")

            valor_formatado = float(
                valor_input.value.replace("R$", "").replace(".", "").replace(",", ".").strip()
            )

            setor_id      = get_or_create(cursor, "setores",      "nome", setor_input.value)
            fornecedor_id = get_or_create(cursor, "fornecedores",  "nome", fornecedor_input.value)
            solicitante_id= get_or_create(cursor, "pessoas",       "nome", solicitante_input.value)
            colaborador_id= get_or_create(cursor, "pessoas",       "nome", colaborador_input.value)
            autorizado_id = get_or_create(cursor, "pessoas",       "nome", autorizado_input.value)

            cursor.execute(
                """
                INSERT INTO solicitacoes
                    (ticket, data_solicitacao, valor, motivo_id, status_id,
                     setor_id, fornecedor_id, solicitante_id, colaborador_id, autorizado_por_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    ticket_input.value, data_hoje, valor_formatado,
                    int(motivo_dropdown.value) if motivo_dropdown.value else None,
                    int(status_dropdown.value) if status_dropdown.value else None,
                    setor_id, fornecedor_id, solicitante_id, colaborador_id, autorizado_id,
                ),
            )

            conn.commit()
            conn.close()

            page.snack_bar = ft.SnackBar(
                ft.Text("Solicitação salva com sucesso!", color=ft.Colors.GREEN)
            )
            page.snack_bar.open = True

            for campo in [ticket_input, valor_input, setor_input, fornecedor_input,
                          solicitante_input, colaborador_input, autorizado_input]:
                campo.value = ""
            motivo_dropdown.value = None
            status_dropdown.value = None
            page.update()

        except ValueError:
            page.snack_bar = ft.SnackBar(
                ft.Text("Erro: Digite um valor numérico válido.", color=ft.Colors.RED)
            )
            page.snack_bar.open = True
            page.update()
        except Exception as erro:
            page.snack_bar = ft.SnackBar(
                ft.Text(f"Erro ao salvar: {erro}", color=ft.Colors.RED)
            )
            page.snack_bar.open = True
            page.update()

    botao_salvar = ft.Button(
        width=250,
        height=45,
        content=ft.Row(
            [ft.Icon(ft.Icons.SAVE), ft.Text("Salvar Solicitação", weight=ft.FontWeight.BOLD)],
            alignment=ft.MainAxisAlignment.CENTER,
        ),
        on_click=salvar_solicitacao,
        style=ft.ButtonStyle(
            bgcolor=ft.Colors.BLUE_700,
            color=ft.Colors.WHITE,
            shape=ft.RoundedRectangleBorder(radius=8),
        ),
    )

    page.add(
        ft.Text("Nova Solicitação de Notebook", size=28, weight=ft.FontWeight.BOLD),
        ft.Text("Preencha os dados abaixo para registrar uma nova movimentação.", color=ft.Colors.GREY_400),
        ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
        ft.Row([ticket_input, valor_input], spacing=20),
        ft.Row([setor_input, fornecedor_input], spacing=20),
        ft.Row([solicitante_input, colaborador_input, autorizado_input], spacing=20),
        ft.Row([motivo_dropdown, status_dropdown], spacing=20),
        ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
        botao_salvar,
    )


if __name__ == "__main__":
    ft.run(main)
