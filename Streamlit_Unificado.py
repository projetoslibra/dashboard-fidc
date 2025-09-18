import streamlit as st
import Streamlit_Libra
import Streamlit_Posicao
import Streamlit_PDD
import Streamlit_Enquadramento


# ==== NOVO: cookies e token ====
import time, json, hmac, hashlib, base64
from streamlit_cookies_manager import EncryptedCookieManager

st.set_page_config(page_title="Dashboard LIBRA", layout="wide")

# ====== CSS (seu código) ======
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

# ======= USUÁRIOS via secrets.toml =======
# Estrutura esperada em .streamlit/secrets.toml:
# [usuarios]
# Joao = "LibraJP"
# Estevan = "14785236"
# ...
usuarios = st.secrets["usuarios"]

# ======= COOKIES CRIPTOGRAFADOS =======
cookies = EncryptedCookieManager(
    prefix="libra_dash",
    password=st.secrets["cookie_password"],  # definido no secrets.toml
)
if not cookies.ready():
    st.stop()

# ======= TOKEN HMAC (não guarda senha no cookie) =======
AUTH_TTL_DAYS = 30  # validade do login lembrado

def _make_token(usuario: str) -> str:
    payload = {"u": usuario, "ts": int(time.time())}
    msg = json.dumps(payload).encode()
    secret = st.secrets["auth_secret"].encode()  # definido no secrets.toml
    sig = hmac.new(secret, msg, hashlib.sha256).hexdigest()
    b64 = base64.urlsafe_b64encode(msg).decode()
    return f"{b64}.{sig}"

def _check_token(token: str):
    try:
        b64, sig = token.split(".")
        msg = base64.urlsafe_b64decode(b64.encode())
        secret = st.secrets["auth_secret"].encode()
        exp_sig = hmac.new(secret, msg, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, exp_sig):
            return None
        data = json.loads(msg.decode())
        # expiração
        if int(time.time()) - data["ts"] > AUTH_TTL_DAYS * 24 * 3600:
            return None
        return data["u"]
    except Exception:
        return None

# ======= ESTADO DE SESSÃO =======
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False
if "usuario" not in st.session_state:
    st.session_state.usuario = None

# ======= AUTO-LOGIN POR COOKIE =======
token_cookie = None
try:
    token_val = cookies.get("auth_token")
    token_cookie = token_val.strip() if token_val else None
except Exception:
    token_cookie = None

if token_cookie and not st.session_state.autenticado:
    user_ok = _check_token(token_cookie)
    if user_ok:
        st.session_state.autenticado = True
        st.session_state.usuario = user_ok

# ======= LOGIN COM "LEMBRAR" =======
if not st.session_state.autenticado:
    with st.form("login_form"):
        st.subheader("🔐 Área Restrita")
        usuario = st.text_input("Usuário:")
        senha = st.text_input("Senha:", type="password")
        lembrar = st.checkbox("Lembrar meu acesso neste dispositivo", value=True)
        submit = st.form_submit_button("Entrar")

        if submit:
            if usuario in usuarios and senha == usuarios[usuario]:
                st.session_state.autenticado = True
                st.session_state.usuario = usuario

                if lembrar:
                    cookies["auth_token"] = _make_token(usuario)
                    cookies.save()  # grava cookie no navegador

                st.success("Login realizado com sucesso!")
                st.rerun()
            else:
                st.error("Usuário ou senha inválidos.")
    st.stop()

# ======= BOTÃO SAIR =======
with st.sidebar:
    user_label = st.session_state.get("usuario") or "—"
    st.caption(f"Conectado como **{user_label}**")

    if st.button("Sair", use_container_width=True):
        # 1) Invalida o cookie (apaga o token do navegador)
        try:
            cookies["auth_token"] = ""   # string vazia
            cookies.save()               # grava remoção
        except Exception:
            pass  # segue sem quebrar, mesmo se cookies não estiver pronto

        # 2) Reseta apenas as chaves que controlam o login
        st.session_state.autenticado = False
        st.session_state.usuario = None

        # 3) Força recarregar a app para exibir a tela de login
        st.rerun()

# ======= MENU LATERAL =======
menu = st.sidebar.radio("Selecione o painel:", ["📊 DRE dos Fundos", "📈 Posição Diária", "📉 Análise de PDD", "📊 Enquadramento"]) 

# ======= ROTEADOR =======
if menu == "📊 DRE dos Fundos":
    Streamlit_Libra.run()
elif menu == "📈 Posição Diária":
    Streamlit_Posicao.run()
elif menu == "📉 Análise de PDD":
    Streamlit_PDD.run()
elif menu == "📊 Enquadramento":
    Streamlit_Enquadramento.run()    
