import streamlit as st

st.set_page_config(page_title="Login", page_icon="🔐")

st.title("🔐 Área Restrita")

usuario = st.text_input("Usuário")
senha = st.text_input("Senha", type="password")

if st.button("Entrar"):

    user_ok = usuario == st.secrets["ADMIN_USER"]
    pass_ok = senha == st.secrets["ADMIN_PASSWORD"]

    if user_ok and pass_ok:
        st.session_state["logado"] = True
        st.success("Login realizado com sucesso!")
        st.switch_page("pages/2_📋_Cadastro.py")

    else:
        st.error("Usuário ou senha inválidos")