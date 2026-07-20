import streamlit as st
import pandas as pd
from datetime import date
from components.footer import footer
from db import get_connection, placeholder

if not st.session_state.get("logado", False):
    st.warning("🔒 Você precisa estar logado para acessar esta página.")
    st.page_link("app.py", label="Ir para o Login", icon="🔐")
    st.stop()

st.set_page_config(page_title="Gerenciar", page_icon="✏️", layout="wide")

st.title("✏️ Gerenciar Registros")
st.caption("Busque, edite ou exclua equipamentos, despesas e serviços.")
st.divider()


# ─── Helpers ──────────────────────────────────────────────────────────────────

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


@st.cache_data(ttl=30)
def carregar_equipamentos():
    conn, _ = get_connection()
    query = """
        SELECT
            s.id, s.ticket, s.equipamento, s.data_solicitacao, s.valor, s.numero_nf,
            COALESCE(m.descricao,  '') AS motivo,
            COALESCE(st.descricao, '') AS status,
            COALESCE(se.nome,      '') AS setor,
            COALESCE(f.nome,       '') AS fornecedor,
            COALESCE(sol.nome,     '') AS solicitante,
            COALESCE(col.nome,     '') AS colaborador,
            COALESCE(aut.nome,     '') AS autorizado_por,
            s.motivo_id, s.status_id
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


@st.cache_data(ttl=30)
def carregar_despesas():
    conn, _ = get_connection()
    query = """
        SELECT
            d.id, d.descricao, d.data_despesa, d.valor, d.numero_nf,
            COALESCE(st.descricao, '') AS status,
            COALESCE(se.nome,      '') AS setor,
            COALESCE(f.nome,       '') AS fornecedor,
            COALESCE(aut.nome,     '') AS autorizado_por,
            d.status_id
        FROM despesas d
        LEFT JOIN status       st  ON d.status_id         = st.id
        LEFT JOIN setores      se  ON d.setor_id          = se.id
        LEFT JOIN fornecedores f   ON d.fornecedor_id     = f.id
        LEFT JOIN pessoas      aut ON d.autorizado_por_id = aut.id
        ORDER BY d.data_despesa DESC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    df["data_despesa"] = pd.to_datetime(df["data_despesa"])
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


motivos_db, status_db = carregar_lookup()
motivos_map = {desc: id_ for id_, desc in motivos_db}
status_map  = {desc: id_ for id_, desc in status_db}
motivos_inv = {id_: desc for id_, desc in motivos_db}
status_inv  = {id_: desc for id_, desc in status_db}

aba_equip, aba_desp = st.tabs(["🖥️ Equipamentos", "💰 Despesas e Serviços"])


# ══════════════════════════════════════════════════════════════════════════════
# ABA 1 — EQUIPAMENTOS
# ══════════════════════════════════════════════════════════════════════════════

with aba_equip:
    df_eq = carregar_equipamentos()

    st.markdown("### 🔎 Buscar Equipamento")
    ticket_busca = st.text_input("Buscar por Ticket", placeholder="ex: 24500", key="busca_eq")

    df_eq_ex = df_eq.copy()
    if ticket_busca.strip():
        df_eq_ex = df_eq_ex[df_eq_ex["ticket"].str.contains(ticket_busca.strip(), case=False, na=False)]

    df_eq_tab = df_eq_ex[["id","ticket","equipamento","data_solicitacao","setor","motivo","status","valor","numero_nf"]].copy()
    df_eq_tab["data_solicitacao"] = df_eq_tab["data_solicitacao"].dt.strftime("%d/%m/%Y")
    df_eq_tab["valor"] = df_eq_tab["valor"].apply(fmt_brl)
    df_eq_tab.columns = ["ID","Ticket","Equipamento","Data","Setor","Motivo","Status","Valor","NF"]

    if df_eq_tab.empty:
        st.info("Nenhum registro encontrado.")
    else:
        ev_eq = st.dataframe(df_eq_tab, use_container_width=True, hide_index=True,
                             on_select="rerun", selection_mode="single-row", key="sel_eq")
        st.divider()

        linhas_eq = ev_eq.selection.get("rows", [])
        if not linhas_eq:
            st.info("👆 Selecione uma linha para editar ou excluir.")
        else:
            reg = df_eq_ex.iloc[linhas_eq[0]]
            reg_id = int(reg["id"])
            st.markdown(f"### ✏️ Editando Ticket **{reg['ticket']}**")

            with st.form("form_eq_edicao"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    ticket = st.text_input("Número do Ticket *", value=reg["ticket"])
                with col2:
                    equipamento = st.text_input("Equipamento *", value=reg.get("equipamento", ""))
                with col3:
                    valor_str = st.text_input("Valor (R$) *",
                        value=f"{reg['valor']:,.2f}".replace(",","X").replace(".",",").replace("X","."))

                col4, col5, col6 = st.columns(3)
                with col4:
                    setor = st.text_input("Setor", value=reg["setor"])
                with col5:
                    fornecedor = st.text_input("Fornecedor", value=reg["fornecedor"])
                with col6:
                    numero_nf = st.text_input("Número da NF", value=reg.get("numero_nf") or "")

                col7, col8, col9 = st.columns(3)
                with col7:
                    solicitante = st.text_input("Solicitante", value=reg["solicitante"])
                with col8:
                    colaborador = st.text_input("Colaborador (Destino)", value=reg["colaborador"])
                with col9:
                    autorizado = st.text_input("Autorizado por", value=reg["autorizado_por"])

                col10, col11, col12 = st.columns(3)
                lista_motivos = [""] + list(motivos_map.keys())
                motivo_atual  = motivos_inv.get(reg["motivo_id"]) if reg["motivo_id"] else ""
                idx_motivo    = lista_motivos.index(motivo_atual) if motivo_atual in lista_motivos else 0
                lista_status  = [""] + list(status_map.keys())
                status_atual  = status_inv.get(reg["status_id"]) if reg["status_id"] else ""
                idx_status    = lista_status.index(status_atual) if status_atual in lista_status else 0

                with col10:
                    motivo_sel = st.selectbox("Motivo", lista_motivos, index=idx_motivo)
                with col11:
                    status_sel = st.selectbox("Status", lista_status, index=idx_status)
                with col12:
                    data_sol = st.date_input("Data",
                        value=reg["data_solicitacao"].date() if pd.notna(reg["data_solicitacao"]) else date.today())

                c1, c2 = st.columns(2)
                with c1:
                    salvar  = st.form_submit_button("💾 Salvar Alterações", use_container_width=True, type="primary")
                with c2:
                    excluir = st.form_submit_button("🗑️ Excluir Registro",  use_container_width=True)

            if salvar:
                if not ticket.strip() or not valor_str.strip() or not equipamento.strip():
                    st.error("Ticket, Equipamento e Valor são obrigatórios.")
                else:
                    try:
                        valor = float(valor_str.replace("R$","").replace(".","").replace(",",".").strip())
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
                                ticket={p}, equipamento={p}, data_solicitacao={p}, valor={p}, numero_nf={p},
                                motivo_id={p}, status_id={p}, setor_id={p}, fornecedor_id={p},
                                solicitante_id={p}, colaborador_id={p}, autorizado_por_id={p}
                            WHERE id={p}
                        """, (ticket.strip(), equipamento.strip().upper(), data_sol.isoformat(), valor,
                              numero_nf.strip() or None, motivo_id, status_id,
                              setor_id, fornecedor_id, solicitante_id, colaborador_id, autorizado_id, reg_id))
                        conn.commit()
                        conn.close()
                        st.cache_data.clear()
                        st.success(f"✅ Ticket **{ticket.strip()}** atualizado!")
                        st.rerun()
                    except ValueError:
                        st.error("Valor inválido.")
                    except Exception as e:
                        st.error(f"Erro: {e}")

            if excluir:
                st.session_state["confirmar_eq"] = reg_id

            if st.session_state.get("confirmar_eq") == reg_id:
                st.warning(f"⚠️ Excluir o Ticket **{reg['ticket']}**? Esta ação não pode ser desfeita.")
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("✅ Sim, excluir", type="primary", use_container_width=True, key="conf_eq"):
                        try:
                            conn, modo = get_connection()
                            cur = conn.cursor()
                            cur.execute(f"DELETE FROM solicitacoes WHERE id = {placeholder(modo)}", (reg_id,))
                            conn.commit()
                            conn.close()
                            st.cache_data.clear()
                            st.session_state.pop("confirmar_eq", None)
                            st.success("🗑️ Excluído com sucesso!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro: {e}")
                with c2:
                    if st.button("❌ Cancelar", use_container_width=True, key="canc_eq"):
                        st.session_state.pop("confirmar_eq", None)
                        st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# ABA 2 — DESPESAS E SERVIÇOS
# ══════════════════════════════════════════════════════════════════════════════

with aba_desp:
    df_dp = carregar_despesas()

    st.markdown("### 🔎 Buscar Despesa")
    desc_busca = st.text_input("Buscar por Descrição", placeholder="ex: Manutenção", key="busca_dp")

    df_dp_ex = df_dp.copy()
    if desc_busca.strip():
        df_dp_ex = df_dp_ex[df_dp_ex["descricao"].str.contains(desc_busca.strip(), case=False, na=False)]

    df_dp_tab = df_dp_ex[["id","descricao","data_despesa","setor","fornecedor","status","valor","numero_nf"]].copy()
    df_dp_tab["data_despesa"] = df_dp_tab["data_despesa"].dt.strftime("%d/%m/%Y")
    df_dp_tab["valor"] = df_dp_tab["valor"].apply(fmt_brl)
    df_dp_tab.columns = ["ID","Descrição","Data","Setor","Fornecedor","Status","Valor","NF"]

    if df_dp_tab.empty:
        st.info("Nenhuma despesa encontrada.")
    else:
        ev_dp = st.dataframe(df_dp_tab, use_container_width=True, hide_index=True,
                             on_select="rerun", selection_mode="single-row", key="sel_dp")
        st.divider()

        linhas_dp = ev_dp.selection.get("rows", [])
        if not linhas_dp:
            st.info("👆 Selecione uma linha para editar ou excluir.")
        else:
            reg = df_dp_ex.iloc[linhas_dp[0]]
            reg_id = int(reg["id"])
            st.markdown(f"### ✏️ Editando: **{reg['descricao']}**")

            with st.form("form_dp_edicao"):
                col1, col2 = st.columns(2)
                with col1:
                    descricao = st.text_input("Descrição *", value=reg["descricao"])
                with col2:
                    valor_str_d = st.text_input("Valor (R$) *",
                        value=f"{reg['valor']:,.2f}".replace(",","X").replace(".",",").replace("X","."))

                col3, col4, col5 = st.columns(3)
                with col3:
                    fornecedor_d = st.text_input("Fornecedor", value=reg["fornecedor"])
                with col4:
                    setor_d = st.text_input("Setor", value=reg["setor"])
                with col5:
                    numero_nf_d = st.text_input("Número da NF", value=reg.get("numero_nf") or "")

                col6, col7, col8 = st.columns(3)
                lista_status = [""] + list(status_map.keys())
                status_atual = status_inv.get(reg["status_id"]) if reg["status_id"] else ""
                idx_status   = lista_status.index(status_atual) if status_atual in lista_status else 0

                with col6:
                    autorizado_d = st.text_input("Autorizado por", value=reg["autorizado_por"])
                with col7:
                    status_sel_d = st.selectbox("Status", lista_status, index=idx_status, key="status_dp_ed")
                with col8:
                    data_desp = st.date_input("Data",
                        value=reg["data_despesa"].date() if pd.notna(reg["data_despesa"]) else date.today(),
                        key="data_dp_ed")

                c1, c2 = st.columns(2)
                with c1:
                    salvar_d  = st.form_submit_button("💾 Salvar Alterações", use_container_width=True, type="primary")
                with c2:
                    excluir_d = st.form_submit_button("🗑️ Excluir Registro",  use_container_width=True)

            if salvar_d:
                if not descricao.strip() or not valor_str_d.strip():
                    st.error("Descrição e Valor são obrigatórios.")
                else:
                    try:
                        valor_d = float(valor_str_d.replace("R$","").replace(".","").replace(",",".").strip())
                        conn, modo = get_connection()
                        cur = conn.cursor()
                        p = placeholder(modo)
                        setor_id_d      = get_or_create(cur, modo, "setores",      "nome", setor_d)
                        fornecedor_id_d = get_or_create(cur, modo, "fornecedores", "nome", fornecedor_d)
                        autorizado_id_d = get_or_create(cur, modo, "pessoas",      "nome", autorizado_d)
                        status_id_d     = status_map.get(status_sel_d) if status_sel_d else None
                        cur.execute(f"""
                            UPDATE despesas SET
                                descricao={p}, data_despesa={p}, valor={p}, numero_nf={p},
                                setor_id={p}, fornecedor_id={p}, autorizado_por_id={p}, status_id={p}
                            WHERE id={p}
                        """, (descricao.strip(), data_desp.isoformat(), valor_d,
                              numero_nf_d.strip() or None,
                              setor_id_d, fornecedor_id_d, autorizado_id_d, status_id_d, reg_id))
                        conn.commit()
                        conn.close()
                        st.cache_data.clear()
                        st.success(f"✅ **{descricao.strip()}** atualizado!")
                        st.rerun()
                    except ValueError:
                        st.error("Valor inválido.")
                    except Exception as e:
                        st.error(f"Erro: {e}")

            if excluir_d:
                st.session_state["confirmar_dp"] = reg_id

            if st.session_state.get("confirmar_dp") == reg_id:
                st.warning(f"⚠️ Excluir **{reg['descricao']}**? Esta ação não pode ser desfeita.")
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("✅ Sim, excluir", type="primary", use_container_width=True, key="conf_dp"):
                        try:
                            conn, modo = get_connection()
                            cur = conn.cursor()
                            cur.execute(f"DELETE FROM despesas WHERE id = {placeholder(modo)}", (reg_id,))
                            conn.commit()
                            conn.close()
                            st.cache_data.clear()
                            st.session_state.pop("confirmar_dp", None)
                            st.success("🗑️ Excluído com sucesso!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro: {e}")
                with c2:
                    if st.button("❌ Cancelar", use_container_width=True, key="canc_dp"):
                        st.session_state.pop("confirmar_dp", None)
                        st.rerun()

footer()