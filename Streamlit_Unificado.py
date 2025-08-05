import streamlit as st
import Streamlit_Libra
import Streamlit_Posicao
import Streamlit_PDD


st.set_page_config(page_title="Dashboard LIBRA", layout="wide")


st.markdown("""
    <style>
    [data-testid="stSidebar"] {
        background-color: #FFF4E3 !important;
        border-right: 2px solid #e5a12522 !important;
    }

    [data-testid="stSidebar"] * {
        color: #C66300 !important;
    }

    /* Corrige cor dos ícones, labels e opções de rádio */
    [data-testid="stSidebar"] label, 
    [data-testid="stSidebar"] .css-16idsys, 
    [data-testid="stSidebar"] .css-10trblm, 
    [data-testid="stSidebar"] .css-1v3fvcr {
        color: #C66300 !important;
    }

    /* Corrige radio button ativo */
    [data-testid="stSidebar"] .st-ef {
        color: #C66300 !important;
    }

    /* Corrige marcador ativo */
    [data-testid="stSidebar"] .st-em {
        background-color: #C6630033 !important;  /* leve destaque para opção ativa */
    }
    </style>
""", unsafe_allow_html=True)

#a

# ======= SISTEMA DE LOGIN UNIFICADO =======
usuarios = {
    "Joao": "LibraJP",
    "Estevan": "LibraDRE2025",
    "Breno": "LibraDRE2025",
    "Juan": "LibraJM",
    "Nelson": "LibraDRE2025"
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
menu = st.sidebar.radio("Selecione o painel:", ["📊 DRE dos Fundos", "📈 Posição Diária", "📉 Análise de PDD"]) 

# ======= ROTEADOR =======
if menu == "📊 DRE dos Fundos":
    Streamlit_Libra.run()
elif menu == "📈 Posição Diária":
    Streamlit_Posicao.run()
elif menu == "📉 Análise de PDD":
    Streamlit_PDD.run()
