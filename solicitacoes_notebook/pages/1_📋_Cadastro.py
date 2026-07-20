import streamlit as st
from datetime import date
from components.footer import footer
from db import get_connection, placeholder

if not st.session_state.get("logado", False):
    st.warning("🔒 Você precisa estar logado para acessar esta página.")
    st.page_link("app.py", label="Ir para o Login", icon="🔐")
    st.stop()

st.set_page_config(page_title="Cadastro", page_icon="📋", layout="centered")

st.title("📋 Cadastro")
st.caption("Registre novas solicitações de equipamentos ou despesas e serviços.")
st.divider()


# ─── Lookup ───────────────────────────────────────────────────────────────────

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


# ─── Abas ─────────────────────────────────────────────────────────────────────

aba_equip, aba_desp = st.tabs(["🖥️ Equipamentos", "💰 Despesas e Serviços"])


# ══════════════════════════════════════════════════════════════════════════════
# ABA 1 — EQUIPAMENTOS
# ══════════════════════════════════════════════════════════════════════════════

with aba_equip:
    st.markdown("##### Nova Solicitação de Equipamento")

    with st.form("form_equipamento", clear_on_submit=True):

        col1, col2, col3 = st.columns(3)
        with col1:
            ticket = st.text_input("Número do Ticket *", placeholder="ex: 24500")
        with col2:
            equipamento = st.text_input("Equipamento *", placeholder="ex: Notebook, Monitor")
        with col3:
            valor_str = st.text_input("Valor Total (R$) *", placeholder="ex: 4.500,00")

        col4, col5, col6 = st.columns(3)
        with col4:
            setor = st.text_input("Setor", placeholder="ex: Tesouraria")
        with col5:
            fornecedor = st.text_input("Fornecedor", placeholder="ex: IBYTE")
        with col6:
            numero_nf = st.text_input("Número da NF", placeholder="ex: 123456")

        col7, col8, col9 = st.columns(3)
        with col7:
            solicitante = st.text_input("Solicitante", placeholder="Nome")
        with col8:
            colaborador = st.text_input("Colaborador (Destino)", placeholder="Nome")
        with col9:
            autorizado = st.text_input("Autorizado por", placeholder="Nome")

        col10, col11, col12 = st.columns(3)
        with col10:
            motivo_sel = st.selectbox("Motivo da Solicitação", [""] + list(motivos_map.keys()))
        with col11:
            status_sel = st.selectbox("Status Atual", [""] + list(status_map.keys()))
        with col12:
            data_sol = st.date_input("Data da Solicitação", value=date.today())

        submitted_equip = st.form_submit_button("💾 Salvar Equipamento", use_container_width=True, type="primary")

    if submitted_equip:
        if not ticket.strip() or not valor_str.strip() or not equipamento.strip():
            st.error("Os campos **Ticket**, **Equipamento** e **Valor** são obrigatórios.")
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
                    INSERT INTO solicitacoes
                        (ticket, equipamento, data_solicitacao, valor, numero_nf,
                         motivo_id, status_id, setor_id, fornecedor_id,
                         solicitante_id, colaborador_id, autorizado_por_id)
                    VALUES ({p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p})
                """, (
                    ticket.strip(), equipamento.strip().upper(), data_sol.isoformat(),
                    valor, numero_nf.strip() or None,
                    motivo_id, status_id,
                    setor_id, fornecedor_id, solicitante_id, colaborador_id, autorizado_id,
                ))

                conn.commit()
                conn.close()
                st.cache_data.clear()
                st.success(f"✅ Equipamento **{ticket.strip()}** salvo com sucesso!")

            except ValueError:
                st.error("Valor inválido. Use o formato: **4.500,00**")
            except Exception as e:
                st.error(f"Erro ao salvar: {e}")


# ══════════════════════════════════════════════════════════════════════════════
# ABA 2 — DESPESAS E SERVIÇOS
# ══════════════════════════════════════════════════════════════════════════════

with aba_desp:
    st.markdown("##### Nova Despesa ou Serviço")

    with st.form("form_despesa", clear_on_submit=True):

        col1, col2, col3 = st.columns(3)
        with col1:
            ticket_d = st.text_input("Número do Ticket", placeholder="ex: 24500", key="ticket_desp")
        with col2:
            descricao = st.text_input("Descrição *", placeholder="ex: Manutenção de impressora")
        with col3:
            valor_str_d = st.text_input("Valor (R$) *", placeholder="ex: 350,00")

        col4, col5, col6 = st.columns(3)
        with col4:
            fornecedor_d = st.text_input("Fornecedor", placeholder="ex: TechService")
        with col5:
            setor_d = st.text_input("Setor", placeholder="ex: TI")
        with col6:
            numero_nf_d = st.text_input("Número da NF", placeholder="ex: 789012")

        col7, col8, col9 = st.columns(3)
        with col7:
            autorizado_d = st.text_input("Autorizado por", placeholder="Nome")
        with col8:
            status_sel_d = st.selectbox("Status", [""] + list(status_map.keys()), key="status_desp")
        with col9:
            data_desp = st.date_input("Data", value=date.today(), key="data_desp")

        submitted_desp = st.form_submit_button("💾 Salvar Despesa", use_container_width=True, type="primary")

    if submitted_desp:
        if not descricao.strip() or not valor_str_d.strip():
            st.error("Os campos **Descrição** e **Valor** são obrigatórios.")
        else:
            try:
                valor_d = float(valor_str_d.replace("R$", "").replace(".", "").replace(",", ".").strip())
                conn, modo = get_connection()
                cur = conn.cursor()
                p = placeholder(modo)

                setor_id_d      = get_or_create(cur, modo, "setores",      "nome", setor_d)
                fornecedor_id_d = get_or_create(cur, modo, "fornecedores", "nome", fornecedor_d)
                autorizado_id_d = get_or_create(cur, modo, "pessoas",      "nome", autorizado_d)
                status_id_d     = status_map.get(status_sel_d) if status_sel_d else None

                cur.execute(f"""
                    INSERT INTO despesas
                        (ticket, descricao, data_despesa, valor, numero_nf,
                         setor_id, fornecedor_id, autorizado_por_id, status_id)
                    VALUES ({p},{p},{p},{p},{p},{p},{p},{p},{p})
                """, (
                    ticket_d.strip() or None, descricao.strip(), data_desp.isoformat(), valor_d,
                    numero_nf_d.strip() or None,
                    setor_id_d, fornecedor_id_d, autorizado_id_d, status_id_d,
                ))

                conn.commit()
                conn.close()
                st.cache_data.clear()
                st.success(f"✅ Despesa **{descricao.strip()}** salva com sucesso!")

            except ValueError:
                st.error("Valor inválido. Use o formato: **350,00**")
            except Exception as e:
                st.error(f"Erro ao salvar: {e}")

footer()