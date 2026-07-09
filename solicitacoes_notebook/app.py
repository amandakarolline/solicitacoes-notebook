import streamlit as st

st.set_page_config(page_title="Gestão de Notebooks", page_icon="💻", layout="wide")


# ─── Login ────────────────────────────────────────────────────────────────────

def tela_login():
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.title("🔐 Área Restrita")
        st.caption("Informe suas credenciais para continuar.")

        usuario = st.text_input("Usuário", placeholder="seu usuário")
        senha   = st.text_input("Senha", type="password", placeholder="sua senha")

        if st.button("Entrar", use_container_width=True, type="primary"):
            user_ok = usuario == st.secrets.get("ADMIN_USER", "")
            pass_ok = senha   == st.secrets.get("ADMIN_PASSWORD", "")

            if user_ok and pass_ok:
                st.session_state["logado"] = True
                st.rerun()
            else:
                st.error("Usuário ou senha inválidos.")


# ─── Roteamento ───────────────────────────────────────────────────────────────

if not st.session_state.get("logado", False):
    tela_login()
    st.stop()

# ─── Menu (só aparece após login) ─────────────────────────────────────────────

if st.sidebar.button("Sair"):
    st.session_state["logado"] = False
    st.rerun()

st.title("💻 Sistema de Gestão de Notebooks")
st.markdown("""
    Bem-vindo! Use o menu lateral para navegar:

    - **📊 Dashboard** — analise custos, volumes e tendências
    - **📋 Cadastro** — registre novas solicitações
    - **✏️ Gerenciar** — edite ou exclua registros existentes
""")