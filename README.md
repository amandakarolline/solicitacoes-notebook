# 💻 Solicitações de Notebooks

Sistema de gestão e análise de solicitações de equipamentos (notebooks), composto por:

- **`app_flet.py`** — formulário desktop para cadastro de solicitações
- **`app_dash.py`** — dashboard analítico com Streamlit (roda local e na nuvem)
- **`database.py`** — criação e inicialização do banco de dados

---

## 📁 Estrutura do Projeto

```
solicitacoes-notebook/
├── solicitacoes.db              ← banco SQLite (gerado pelo database.py)
├── requirements.txt             ← dependências para Streamlit Cloud
├── pyproject.toml               ← dependências para Poetry (local)
├── .streamlit/
│   └── secrets.toml             ← credenciais (NÃO comitar no Git!)
└── solicitacoes_notebook/
    ├── __init__.py
    ├── database.py
    ├── app_flet.py
    └── app_dash.py
```

---

## 🚀 Rodando Localmente

### 1. Instalar dependências

```bash
poetry install
```

### 2. Criar o banco de dados

```bash
poetry run python solicitacoes_notebook/database.py
```

### 3. Cadastrar solicitações (app Flet)

```bash
poetry run python solicitacoes_notebook/app_flet.py
```

### 4. Visualizar o dashboard (Streamlit)

```bash
poetry run streamlit run solicitacoes_notebook/app_dash.py
```

---

## ☁️ Deploy no Streamlit Cloud

### Pré-requisitos

1. Repositório no GitHub (público ou privado)
2. Conta no [Streamlit Cloud](https://streamlit.io/cloud) (gratuita)
3. Banco PostgreSQL — recomendamos **[Supabase](https://supabase.com)** (plano gratuito)

### Passo a passo

#### 1. Criar banco PostgreSQL no Supabase

1. Crie uma conta em [supabase.com](https://supabase.com)
2. Crie um novo projeto
3. Vá em **Settings → Database → Connection string → URI**
4. Copie a `DATABASE_URL`

#### 2. Configurar secrets no Streamlit Cloud

No painel do Streamlit Cloud: **App → Settings → Secrets** e cole:

```toml
DATABASE_URL = "postgresql://usuario:senha@host:5432/banco"
```

#### 3. Fazer o deploy

1. Push para o GitHub
2. No Streamlit Cloud: **New app → selecione o repositório**
3. **Main file path:** `solicitacoes_notebook/app_dash.py`
4. Clique em **Deploy**

---

## 🔒 Segurança

Adicione ao `.gitignore`:

```
.streamlit/secrets.toml
solicitacoes.db
```

---

## 📊 Funcionalidades do Dashboard

- Filtros por período, status, motivo, setor e fornecedor
- KPIs: investimento total, total de solicitações, ticket médio, maior solicitação
- Evolução mensal de gastos (barras + linha de volume)
- Análise por motivo (barras + pizza)
- Análise por setor e fornecedor
- Distribuição por status com tabela de resumo
- Tabela detalhada completa (setor, fornecedor, colaborador, etc.)
- Exportação para CSV
