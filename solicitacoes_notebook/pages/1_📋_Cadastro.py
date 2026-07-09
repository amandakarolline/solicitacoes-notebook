import streamlit as st
from datetime import date
from components.footer import footer

from db import get_connection, placeholder

if not st.session_state.get("logado", False):
    st.warning("🔒 Você precisa estar logado.")
    st.page_link("app.py", label="Ir para o Login", icon="🔐")
    st.stop()

if st.sidebar.button("Sair"):
    st.session_state["logado"] = False
    st.switch_page("app.py")

st.set_page_config(page_title="Cadastro", page_icon="📋", layout="centered")

st.title("📋 Nova Solicitação de Notebook")
st.caption("Preencha os dados abaixo para registrar uma nova movimentação.")
st.divider()


# ─── Carrega listas de motivos e status do banco ──────────────────────────────

@st.cache_data(ttl=300)
def carregar_lookup():
    conn, _ = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, descricao FROM motivos ORDER BY descricao")
    motivos = cur.fetchall()
    cur.execute("SELECT id, descricao FROM status ORDER BY descricao")
    status = cur.fetchall()
    conn.close()
    return motivos, status


try:
    motivos_db, status_db = carregar_lookup()
except Exception as e:
    st.error(f"Erro ao conectar com o banco: {e}")
    st.stop()

motivos_map = {desc: id_ for id_, desc in motivos_db}
status_map  = {desc: id_ for id_, desc in status_db}


# ─── Formulário ───────────────────────────────────────────────────────────────

with st.form("form_solicitacao", clear_on_submit=True):

    col1, col2 = st.columns(2)
    with col1:
        ticket = st.text_input("Número do Ticket *", placeholder="ex: 24500")
    with col2:
        valor_str = st.text_input("Valor Total (R$) *", placeholder="ex: 4.500,00")

    col3, col4 = st.columns(2)
    with col3:
        setor = st.text_input("Setor", placeholder="ex: Tesouraria")
    with col4:
        fornecedor = st.text_input("Fornecedor", placeholder="ex: IBYTE")

    col5, col6, col7 = st.columns(3)
    with col5:
        solicitante = st.text_input("Solicitante", placeholder="Nome")
    with col6:
        colaborador = st.text_input("Colaborador (Destino)", placeholder="Nome")
    with col7:
        autorizado = st.text_input("Autorizado por", placeholder="Nome")

    col8, col9, col10 = st.columns(3)
    with col8:
        motivo_sel = st.selectbox("Motivo da Solicitação", [""] + list(motivos_map.keys()))
    with col9:
        status_sel = st.selectbox("Status Atual", [""] + list(status_map.keys()))
    with col10:
        data_sol = st.date_input("Data da Solicitação", value=date.today())

    submitted = st.form_submit_button("💾 Salvar Solicitação", use_container_width=True, type="primary")


# ─── Processamento ────────────────────────────────────────────────────────────

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


if submitted:
    if not ticket.strip() or not valor_str.strip():
        st.error("Os campos **Ticket** e **Valor** são obrigatórios.")
    else:
        try:
            valor = float(
                valor_str.replace("R$", "").replace(".", "").replace(",", ".").strip()
            )

            conn, modo = get_connection()
            cur = conn.cursor()
            p = placeholder(modo)

            setor_id       = get_or_create(cur, modo, "setores",     "nome",      setor)
            fornecedor_id  = get_or_create(cur, modo, "fornecedores","nome",      fornecedor)
            solicitante_id = get_or_create(cur, modo, "pessoas",     "nome",      solicitante)
            colaborador_id = get_or_create(cur, modo, "pessoas",     "nome",      colaborador)
            autorizado_id  = get_or_create(cur, modo, "pessoas",     "nome",      autorizado)
            motivo_id      = motivos_map.get(motivo_sel) if motivo_sel else None
            status_id      = status_map.get(status_sel)  if status_sel  else None

            cur.execute(f"""
                INSERT INTO solicitacoes
                    (ticket, data_solicitacao, valor, motivo_id, status_id,
                     setor_id, fornecedor_id, solicitante_id, colaborador_id, autorizado_por_id)
                VALUES ({p},{p},{p},{p},{p},{p},{p},{p},{p},{p})
            """, (
                ticket.strip(), data_sol.isoformat(), valor,
                motivo_id, status_id,
                setor_id, fornecedor_id, solicitante_id, colaborador_id, autorizado_id,
            ))

            conn.commit()
            conn.close()

            # Limpa cache do dashboard para refletir o novo dado
            st.cache_data.clear()

            st.success(f"✅ Solicitação **{ticket.strip()}** salva com sucesso!")

        except ValueError:
            st.error("Valor inválido. Use o formato: **4.500,00**")
        except Exception as e:
            st.error(f"Erro ao salvar: {e}")

footer()
