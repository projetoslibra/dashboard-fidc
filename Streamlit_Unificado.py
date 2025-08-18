import streamlit as st
import Streamlit_Libra
import Streamlit_Posicao
import Streamlit_PDD


st.set_page_config(page_title="Dashboard LIBRA", layout="wide")


st.markdown("""
    <style>
    /* ===== Ajustes de largura e overflow da sidebar ===== */
    [data-testid="stSidebar"] {
        width: 360px !important;          /* ajuste para 330–400 se quiser */
        min-width: 360px !important;
        overflow: visible !important;      /* evita cortar o popover */
    }

    /* Garante que containers internos não cortem o calendário */
    [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
        overflow: visible !important;
    }

    /* Datepicker ocupa toda a largura disponível */
    [data-testid="stSidebar"] .stDateInput div[data-baseweb="datepicker"] {
        width: 100% !important;
    }

    /* (Opcional) dá um respiro ao input do datepicker */
    [data-testid="stSidebar"] .stDateInput > div {
        width: 100% !important;
    }
    </style>
""", unsafe_allow_html=True)

#a

# ======= SISTEMA DE LOGIN UNIFICADO =======
usuarios = {
    "Joao": "LibraJP",
    "Estevan": "14785236",
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
