import streamlit as st
import Streamlit_Libra
import Streamlit_Posicao

st.set_page_config(page_title="Dashboard LIBRA", layout="wide")


st.markdown("""
    <style>
    [data-testid="stSidebar"] {
        background-color: #DCDCDC !important;
        border-right: 2px solid #e5a12522 !important;
        color: #e5a125 !important;
    }
    [data-testid="stSidebar"] * {
        color: #e5a125 !important;
    }
    </style>
""", unsafe_allow_html=True)



# ======= SISTEMA DE LOGIN UNIFICADO =======
usuarios = {
    "Joao": "LibraJP",
    "Estevan": "LibraDRE2025",
    "Breno": "LibraDRE2025",
    "Juan": "LibraJM"
}

if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    with st.form("login_form"):
        st.subheader("🔐 Área Restrita")
        usuario = st.text_input("Usuário:")
        senha = st.text_input("Senha:", type="password")
        submit = st.form_submit_button("Entrar")

        if submit:
            if usuario in usuarios and usuarios[usuario] == senha:
                st.session_state.autenticado = True
                st.success("Login realizado com sucesso!")
                st.rerun()
            else:
                st.error("Usuário ou senha inválidos.")
    st.stop()

# ======= MENU LATERAL =======
menu = st.sidebar.radio("Selecione o painel:", ["📊 DRE dos Fundos", "📈 Posição Diária"])

# ======= ROTEADOR =======
if menu == "📊 DRE dos Fundos":
    Streamlit_Libra.run()
elif menu == "📈 Posição Diária":
    Streamlit_Posicao.run()
