import streamlit as st

st.set_page_config(
    page_title="Gestão de Notebooks",
    page_icon="💻",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("💻 Sistema de Gestão de Notebooks")
st.markdown(
    """
    Bem-vindo! Use o menu lateral para navegar entre as seções:

    - **📋 Cadastro** — registre novas solicitações de equipamentos
    - **📊 Dashboard** — analise custos, volumes e tendências
    """
)
