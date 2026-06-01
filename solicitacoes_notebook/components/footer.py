import streamlit as st


def footer():
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: gray; font-size: 14px;'>
            Desenvolvido por <b>Amanda Karolline</b> 💙
        </div>
        """,
        unsafe_allow_html=True
    )