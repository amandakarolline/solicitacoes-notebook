import streamlit as st
import pandas as pd
from datetime import date

from db import get_connection, placeholder
from components.footer import footer

# ─── Autenticação ─────────────────────────────────────────────────────────────

if not st.session_state.get("logado", False):
    st.warning("🔒 Você precisa estar logado.")
    st.page_link("app.py", label="Ir para o Login", icon="🔐")
    st.stop()

if st.sidebar.button("Sair"):
    st.session_state["logado"] = False
    st.switch_page("app.py")

st.set_page_config(page_title="Gerenciar", page_icon="✏️", layout="wide")

st.title("✏️ Gerenciar Solicitações")
st.caption("Busque, edite ou exclua solicitações registradas.")
st.divider()


# ─── Funções auxiliares ───────────────────────────────────────────────────────

@st.cache_data(ttl=60)
def carregar_lookup():
    conn, _ = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, descricao FROM motivos ORDER BY descricao")
    motivos = cur.fetchall()
    cur.execute("SELECT id, descricao FROM status ORDER BY descricao")
    status = cur.fetchall()
    conn.close()
    return motivos, status


@st.cache_data(ttl=30)
def carregar_todas():
    conn, _ = get_connection()
    query = """
        SELECT
            s.id,
            s.ticket,
            s.data_solicitacao,
            s.valor,
            COALESCE(m.descricao,  '')  AS motivo,
            COALESCE(st.descricao, '')  AS status,
            COALESCE(se.nome,      '')  AS setor,
            COALESCE(f.nome,       '')  AS fornecedor,
            COALESCE(sol.nome,     '')  AS solicitante,
            COALESCE(col.nome,     '')  AS colaborador,
            COALESCE(aut.nome,     '')  AS autorizado_por,
            s.motivo_id,
            s.status_id
        FROM solicitacoes s
        LEFT JOIN motivos      m   ON s.motivo_id         = m.id
        LEFT JOIN status       st  ON s.status_id         = st.id
        LEFT JOIN setores      se  ON s.setor_id          = se.id
        LEFT JOIN fornecedores f   ON s.fornecedor_id     = f.id
        LEFT JOIN pessoas      sol ON s.solicitante_id    = sol.id
        LEFT JOIN pessoas      col ON s.colaborador_id    = col.id
        LEFT JOIN pessoas      aut ON s.autorizado_por_id = aut.id
        ORDER BY s.data_solicitacao DESC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    df["data_solicitacao"] = pd.to_datetime(df["data_solicitacao"])
    return df


def get_or_create(cur, modo, tabela, coluna, valor):
    if not valor or not valor.strip():
        return None
    valor = valor.strip().upper()
    p = placeholder(modo)
    cur.execute(f"SELECT id FROM {tabela} WHERE {coluna} = {p}", (valor,))
    row = cur.fetchone()
    if row:
        return row[0]
    cur.execute(f"INSERT INTO {tabela} ({coluna}) VALUES ({p})", (valor,))
    if modo == "postgres":
        cur.execute("SELECT lastval()")
        return cur.fetchone()[0]
    return cur.lastrowid


def fmt_brl(v):
    try:
        return f"R$ {float(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return v


# ─── Carrega dados ────────────────────────────────────────────────────────────

motivos_db, status_db = carregar_lookup()
motivos_map = {desc: id_ for id_, desc in motivos_db}
status_map  = {desc: id_ for id_, desc in status_db}
motivos_inv = {id_: desc for id_, desc in motivos_db}
status_inv  = {id_: desc for id_, desc in status_db}

df = carregar_todas()

# ─── Busca ────────────────────────────────────────────────────────────────────

st.markdown("### 🔎 Buscar registro")
col_busca1, col_busca2 = st.columns([1, 2])

with col_busca1:
    ticket_busca = st.text_input("Buscar por Ticket", placeholder="ex: 24500")

with col_busca2:
    df_exibir = df.copy()
    if ticket_busca.strip():
        df_exibir = df_exibir[df_exibir["ticket"].str.contains(ticket_busca.strip(), case=False, na=False)]

# Tabela de seleção
df_tabela = df_exibir[["id","ticket","data_solicitacao","setor","motivo","status","valor"]].copy()
df_tabela["data_solicitacao"] = df_tabela["data_solicitacao"].dt.strftime("%d/%m/%Y")
df_tabela["valor"] = df_tabela["valor"].apply(fmt_brl)
df_tabela.columns = ["ID","Ticket","Data","Setor","Motivo","Status","Valor"]

if df_tabela.empty:
    st.info("Nenhum registro encontrado.")
    st.stop()

evento = st.dataframe(
    df_tabela,
    use_container_width=True,
    hide_index=True,
    on_select="rerun",
    selection_mode="single-row",
)

st.divider()

# ─── Edição / Exclusão ────────────────────────────────────────────────────────

linhas_sel = evento.selection.get("rows", [])

if not linhas_sel:
    st.info("👆 Selecione uma linha na tabela acima para editar ou excluir.")
    footer()
    st.stop()

idx = linhas_sel[0]
reg = df_exibir.iloc[idx]
reg_id = int(reg["id"])

st.markdown(f"### ✏️ Editando Ticket **{reg['ticket']}**")

with st.form("form_edicao"):

    col1, col2 = st.columns(2)
    with col1:
        ticket = st.text_input("Número do Ticket *", value=reg["ticket"])
    with col2:
        valor_str = st.text_input(
            "Valor Total (R$) *",
            value=f"{reg['valor']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        )

    col3, col4 = st.columns(2)
    with col3:
        setor = st.text_input("Setor", value=reg["setor"])
    with col4:
        fornecedor = st.text_input("Fornecedor", value=reg["fornecedor"])

    col5, col6, col7 = st.columns(3)
    with col5:
        solicitante = st.text_input("Solicitante", value=reg["solicitante"])
    with col6:
        colaborador = st.text_input("Colaborador (Destino)", value=reg["colaborador"])
    with col7:
        autorizado = st.text_input("Autorizado por", value=reg["autorizado_por"])

    col8, col9, col10 = st.columns(3)

    lista_motivos = [""] + list(motivos_map.keys())
    motivo_atual  = motivos_inv.get(reg["motivo_id"]) if reg["motivo_id"] else ""
    idx_motivo    = lista_motivos.index(motivo_atual) if motivo_atual in lista_motivos else 0

    lista_status  = [""] + list(status_map.keys())
    status_atual  = status_inv.get(reg["status_id"]) if reg["status_id"] else ""
    idx_status    = lista_status.index(status_atual) if status_atual in lista_status else 0

    with col8:
        motivo_sel = st.selectbox("Motivo", lista_motivos, index=idx_motivo)
    with col9:
        status_sel = st.selectbox("Status", lista_status, index=idx_status)
    with col10:
        data_sol = st.date_input(
            "Data da Solicitação",
            value=reg["data_solicitacao"].date() if pd.notna(reg["data_solicitacao"]) else date.today()
        )

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        salvar = st.form_submit_button("💾 Salvar Alterações", use_container_width=True, type="primary")
    with col_btn2:
        excluir = st.form_submit_button("🗑️ Excluir Registro", use_container_width=True)


# ─── Salvar ───────────────────────────────────────────────────────────────────

if salvar:
    if not ticket.strip() or not valor_str.strip():
        st.error("Os campos **Ticket** e **Valor** são obrigatórios.")
    else:
        try:
            valor = float(valor_str.replace("R$", "").replace(".", "").replace(",", ".").strip())
            conn, modo = get_connection()
            cur = conn.cursor()
            p = placeholder(modo)

            setor_id       = get_or_create(cur, modo, "setores",      "nome", setor)
            fornecedor_id  = get_or_create(cur, modo, "fornecedores", "nome", fornecedor)
            solicitante_id = get_or_create(cur, modo, "pessoas",      "nome", solicitante)
            colaborador_id = get_or_create(cur, modo, "pessoas",      "nome", colaborador)
            autorizado_id  = get_or_create(cur, modo, "pessoas",      "nome", autorizado)
            motivo_id      = motivos_map.get(motivo_sel) if motivo_sel else None
            status_id      = status_map.get(status_sel)  if status_sel  else None

            cur.execute(f"""
                UPDATE solicitacoes SET
                    ticket            = {p},
                    data_solicitacao  = {p},
                    valor             = {p},
                    motivo_id         = {p},
                    status_id         = {p},
                    setor_id          = {p},
                    fornecedor_id     = {p},
                    solicitante_id    = {p},
                    colaborador_id    = {p},
                    autorizado_por_id = {p}
                WHERE id = {p}
            """, (
                ticket.strip(), data_sol.isoformat(), valor,
                motivo_id, status_id,
                setor_id, fornecedor_id, solicitante_id, colaborador_id, autorizado_id,
                reg_id,
            ))

            conn.commit()
            conn.close()
            st.cache_data.clear()
            st.success(f"✅ Ticket **{ticket.strip()}** atualizado com sucesso!")
            st.rerun()

        except ValueError:
            st.error("Valor inválido. Use o formato: **4.500,00**")
        except Exception as e:
            st.error(f"Erro ao salvar: {e}")


# ─── Excluir ──────────────────────────────────────────────────────────────────

if excluir:
    st.session_state["confirmar_exclusao"] = reg_id

if st.session_state.get("confirmar_exclusao") == reg_id:
    st.warning(f"⚠️ Tem certeza que deseja excluir o Ticket **{reg['ticket']}**? Esta ação não pode ser desfeita.")
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        if st.button("✅ Sim, excluir", type="primary", use_container_width=True):
            try:
                conn, modo = get_connection()
                cur = conn.cursor()
                p = placeholder(modo)
                cur.execute(f"DELETE FROM solicitacoes WHERE id = {p}", (reg_id,))
                conn.commit()
                conn.close()
                st.cache_data.clear()
                st.session_state.pop("confirmar_exclusao", None)
                st.success("🗑️ Registro excluído com sucesso!")
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao excluir: {e}")
    with col_c2:
        if st.button("❌ Cancelar", use_container_width=True):
            st.session_state.pop("confirmar_exclusao", None)
            st.rerun()

footer()
