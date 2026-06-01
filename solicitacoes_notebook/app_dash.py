import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

st.set_page_config(
    page_title="Dashboard de Equipamentos",
    page_icon="💻",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Conexão: PostgreSQL (nuvem) ou SQLite (local) ────────────────────────────

def get_connection():
    """Retorna uma conexão ativa. Usa PostgreSQL se DATABASE_URL estiver
    configurado nos Streamlit Secrets; caso contrário, usa o SQLite local."""
    try:
        db_url = st.secrets["DATABASE_URL"]
        import psycopg2
        return psycopg2.connect(db_url), "postgres"
    except (KeyError, Exception):
        import sqlite3
        BASE_DIR = Path(__file__).resolve().parent.parent
        db_path = BASE_DIR / "solicitacoes.db"
        return sqlite3.connect(db_path), "sqlite"


@st.cache_data(ttl=60)
def get_data():
    conn, _ = get_connection()
    query = """
        SELECT
            s.id,
            s.ticket,
            s.data_solicitacao,
            s.valor,
            COALESCE(m.descricao,  'Não Informado') AS motivo,
            COALESCE(st.descricao, 'Sem Status')    AS status,
            COALESCE(se.nome,      'Não Informado') AS setor,
            COALESCE(f.nome,       'Não Informado') AS fornecedor,
            COALESCE(sol.nome,     'Não Informado') AS solicitante,
            COALESCE(col.nome,     'Não Informado') AS colaborador,
            COALESCE(aut.nome,     'Não Informado') AS autorizado_por
        FROM solicitacoes s
        LEFT JOIN motivos    m   ON s.motivo_id         = m.id
        LEFT JOIN status     st  ON s.status_id         = st.id
        LEFT JOIN setores    se  ON s.setor_id          = se.id
        LEFT JOIN fornecedores f ON s.fornecedor_id     = f.id
        LEFT JOIN pessoas   sol  ON s.solicitante_id    = sol.id
        LEFT JOIN pessoas   col  ON s.colaborador_id    = col.id
        LEFT JOIN pessoas   aut  ON s.autorizado_por_id = aut.id
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    df["data_solicitacao"] = pd.to_datetime(df["data_solicitacao"])
    return df


def fmt_brl(valor: float) -> str:
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


# ─── Carrega dados ─────────────────────────────────────────────────────────────

try:
    df = get_data()
except Exception as e:
    st.error(f"Erro ao conectar com o banco de dados: {e}")
    st.stop()

if df.empty:
    st.info("Nenhum dado encontrado. Insira solicitações pelo app Flet primeiro.")
    st.stop()

# ─── Sidebar – Filtros ────────────────────────────────────────────────────────

st.sidebar.header("🔍 Filtros")

# Período
data_min = df["data_solicitacao"].min().date()
data_max = df["data_solicitacao"].max().date()
periodo = st.sidebar.date_input(
    "Período:", value=(data_min, data_max), min_value=data_min, max_value=data_max
)
if isinstance(periodo, (list, tuple)) and len(periodo) == 2:
    data_ini, data_fim = periodo
else:
    data_ini, data_fim = data_min, data_max

# Demais filtros
todos = lambda col: df[col].unique().tolist()

status_sel    = st.sidebar.multiselect("Status:",      todos("status"),      default=todos("status"))
motivos_sel   = st.sidebar.multiselect("Motivo:",      todos("motivo"),      default=todos("motivo"))
setores_sel   = st.sidebar.multiselect("Setor:",       todos("setor"),       default=todos("setor"))
fornec_sel    = st.sidebar.multiselect("Fornecedor:",  todos("fornecedor"),  default=todos("fornecedor"))

dff = df[
    (df["data_solicitacao"].dt.date >= data_ini) &
    (df["data_solicitacao"].dt.date <= data_fim) &
    (df["status"].isin(status_sel)) &
    (df["motivo"].isin(motivos_sel)) &
    (df["setor"].isin(setores_sel)) &
    (df["fornecedor"].isin(fornec_sel))
]

if st.sidebar.button("🔄 Atualizar dados"):
    st.cache_data.clear()
    st.rerun()

# ─── Header ───────────────────────────────────────────────────────────────────

st.title("💻 Painel de Solicitações de Notebooks")
st.caption("Acompanhamento de custos e volumetria das solicitações de infraestrutura.")
st.divider()

# ─── KPIs ─────────────────────────────────────────────────────────────────────

valor_total   = dff["valor"].sum()
total_tickets = len(dff)
ticket_medio  = valor_total / total_tickets if total_tickets else 0
valor_max     = dff["valor"].max() if total_tickets else 0

k1, k2, k3, k4 = st.columns(4)
k1.metric("💰 Investimento Total",    fmt_brl(valor_total))
k2.metric("📋 Total de Solicitações", total_tickets)
k3.metric("📊 Ticket Médio",          fmt_brl(ticket_medio))
k4.metric("🔝 Maior Solicitação",     fmt_brl(valor_max))

st.divider()

# ─── Evolução mensal ──────────────────────────────────────────────────────────

st.markdown("### 📈 Evolução Mensal de Gastos")

mensal = (
    dff.assign(mes=dff["data_solicitacao"].dt.to_period("M").astype(str))
    .groupby("mes")
    .agg(valor=("valor", "sum"), qtd=("id", "count"))
    .reset_index()
    .sort_values("mes")
)

if not mensal.empty:
    fig_linha = go.Figure()
    fig_linha.add_trace(go.Bar(
        x=mensal["mes"], y=mensal["valor"],
        name="Valor (R$)", marker_color="#1f77b4", opacity=0.7,
        yaxis="y1"
    ))
    fig_linha.add_trace(go.Scatter(
        x=mensal["mes"], y=mensal["qtd"],
        name="Qtd Solicitações", mode="lines+markers",
        marker=dict(color="#ff7f0e", size=8), line=dict(width=2),
        yaxis="y2"
    ))
    fig_linha.update_layout(
        title="Investimento mensal (barras) e volume (linha)",
        yaxis=dict(title="Valor (R$)"),
        yaxis2=dict(title="Qtd", overlaying="y", side="right"),
        legend=dict(orientation="h", y=1.1),
        hovermode="x unified",
    )
    st.plotly_chart(fig_linha, use_container_width=True)

st.divider()

# ─── Análise de Causas ────────────────────────────────────────────────────────

st.markdown("### 🔍 Análise de Causas")
col1, col2 = st.columns(2)

with col1:
    por_motivo = dff.groupby("motivo")["valor"].sum().reset_index().sort_values("valor")
    fig_bar = px.bar(
        por_motivo, x="valor", y="motivo", orientation="h",
        title="Custo total por Motivo",
        labels={"valor": "Valor Gasto (R$)", "motivo": "Motivo"},
        color="valor", color_continuous_scale="Blues",
        text_auto=".2s",
    )
    fig_bar.update_layout(coloraxis_showscale=False, yaxis_title="")
    st.plotly_chart(fig_bar, use_container_width=True)

with col2:
    vol_motivo = dff["motivo"].value_counts().reset_index()
    vol_motivo.columns = ["motivo", "quantidade"]
    fig_pizza = px.pie(
        vol_motivo, values="quantidade", names="motivo", hole=0.45,
        title="Distribuição por Volume (Qtd por Motivo)",
        color_discrete_sequence=px.colors.qualitative.Set3,
    )
    fig_pizza.update_traces(textinfo="percent+label")
    st.plotly_chart(fig_pizza, use_container_width=True)

st.divider()

# ─── Análise por Setor e Fornecedor ──────────────────────────────────────────

st.markdown("### 🏢 Análise por Setor e Fornecedor")
col3, col4 = st.columns(2)

with col3:
    por_setor = (
        dff.groupby("setor")
        .agg(valor=("valor", "sum"), qtd=("id", "count"))
        .reset_index()
        .sort_values("valor", ascending=False)
    )
    fig_setor = px.bar(
        por_setor, x="setor", y="valor",
        title="Investimento por Setor",
        labels={"valor": "Valor (R$)", "setor": "Setor"},
        color="setor",
        text_auto=".2s",
        color_discrete_sequence=px.colors.qualitative.Pastel,
    )
    fig_setor.update_layout(showlegend=False, xaxis_title="")
    st.plotly_chart(fig_setor, use_container_width=True)

with col4:
    por_fornec = (
        dff.groupby("fornecedor")
        .agg(valor=("valor", "sum"), qtd=("id", "count"))
        .reset_index()
        .sort_values("valor", ascending=False)
    )
    fig_fornec = px.bar(
        por_fornec, x="fornecedor", y="valor",
        title="Investimento por Fornecedor",
        labels={"valor": "Valor (R$)", "fornecedor": "Fornecedor"},
        color="fornecedor",
        text_auto=".2s",
        color_discrete_sequence=px.colors.qualitative.Safe,
    )
    fig_fornec.update_layout(showlegend=False, xaxis_title="")
    st.plotly_chart(fig_fornec, use_container_width=True)

st.divider()

# ─── Status ───────────────────────────────────────────────────────────────────

st.markdown("### 📌 Distribuição por Status")
col5, col6 = st.columns([1, 2])

with col5:
    por_status = dff["status"].value_counts().reset_index()
    por_status.columns = ["status", "qtd"]
    fig_status = px.pie(
        por_status, values="qtd", names="status", hole=0.5,
        color_discrete_sequence=["#2ecc71", "#e74c3c", "#f39c12", "#3498db"],
    )
    fig_status.update_traces(textinfo="value+percent")
    st.plotly_chart(fig_status, use_container_width=True)

with col6:
    status_valor = (
        dff.groupby("status")["valor"]
        .agg(["sum", "mean", "count"])
        .rename(columns={"sum": "Total (R$)", "mean": "Média (R$)", "count": "Qtd"})
        .reset_index()
    )
    status_valor["Total (R$)"] = status_valor["Total (R$)"].apply(fmt_brl)
    status_valor["Média (R$)"] = status_valor["Média (R$)"].apply(fmt_brl)
    st.dataframe(status_valor, use_container_width=True, hide_index=True)

st.divider()

# ─── Tabela detalhada ─────────────────────────────────────────────────────────

st.markdown("### 📄 Detalhamento Completo")

colunas_exibir = ["ticket", "data_solicitacao", "setor", "fornecedor",
                  "solicitante", "colaborador", "motivo", "status", "valor"]

df_exibir = (
    dff[colunas_exibir]
    .sort_values("data_solicitacao", ascending=False)
    .copy()
)
df_exibir["data_solicitacao"] = df_exibir["data_solicitacao"].dt.strftime("%d/%m/%Y")
df_exibir["valor"] = df_exibir["valor"].apply(fmt_brl)
df_exibir.columns = ["Ticket", "Data", "Setor", "Fornecedor",
                     "Solicitante", "Colaborador", "Motivo", "Status", "Valor"]

st.dataframe(df_exibir, use_container_width=True, hide_index=True)

csv = dff[colunas_exibir].to_csv(index=False).encode("utf-8")
st.download_button("⬇️ Exportar CSV", csv, "solicitacoes.csv", "text/csv")
