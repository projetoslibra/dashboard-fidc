import streamlit as st
import pandas as pd
import requests
from io import StringIO
import os
def run():

    # =================== CORES ===================
    SPACE_CADET = "#042F3C"
    HARVEST_GOLD = "#C66300"
    HONEYDEW = "#FFF4E3"
    SLATE_GRAY = "#717c89"

    # ========== CSS VISUAL ==========
    st.markdown(f"""
    <style>
        html, body, .stApp, .block-container {{
            background-color: {SPACE_CADET} !important;
        }}
        header, .css-18e3th9, .e1fb0mya2 {{
            background: {SPACE_CADET}!important;
            min-height:0px!important;
            border-bottom: none!important;
        }}
        h3 {{
            color: {HARVEST_GOLD}!important;
            font-size: 1.3rem!important;
        }}
        .table-title {{
            color: {HARVEST_GOLD}; font-size:1.2rem; font-weight:700;
        }}
        .stDataFrame thead tr th {{
            background: {HARVEST_GOLD} !important;
            color: {SPACE_CADET} !important;
            font-weight:800 !important;
            font-size:1.1em !important;
        }}
        .stDataFrame tbody tr td {{
            background: {SPACE_CADET} !important;
            color: {HONEYDEW} !important;
            font-size:1em !important;
            border-color: {SLATE_GRAY}30 !important;
        }}
        .stDataFrame {{border:2px solid {SLATE_GRAY}!important; border-radius:10px!important;}}
        .main .block-container {{
            max-width: 100vw!important;
        }}
    </style>
    """, unsafe_allow_html=True)

    # ========== FUNÇÃO PARA CONVERTER VALORES BRASILEIROS ==========
    def converter_valor_br(valor):
        if pd.isna(valor) or valor == "" or valor is None:
            return 0.0
        valor_str = str(valor).replace("R$", "").replace(" ", "").strip()
        if valor_str.count('.') == 1 and valor_str.count(',') == 0:
            try:
                return float(valor_str)
            except:
                return 0.0
        if ',' in valor_str:
            partes = valor_str.split(',')
            parte_inteira = partes[0].replace('.', '')
            parte_decimal = partes[1] if len(partes) > 1 else '00'
            valor_str = f"{parte_inteira}.{parte_decimal}"
        else:
            valor_str = valor_str.replace('.', '')
        try:
            return float(valor_str)
        except:
            return 0.0

    # ========== LIMITES DE ENQUADRAMENTO ==========
    LIMITES = {
        "Apuama": {
            "maior_cedente": 10,
            "top_cedentes": 40,
            "maior_sacado": 10,
            "top_sacados": 35
        },
        "Bristol": {
            "maior_cedente": 7,
            "top_cedentes": 40,
            "maior_sacado": 10,
            "top_sacados": 25
        }
    }

    # Cedentes que devem virar sacados
    CEDENTES_SUBSTITUIR = [
        "UY3 SOCIEDADE DE CREDITO DIRETO S/ A",
        "MONEY PLUS SOCIEDADE DE CREDITO AO MICROEMPREENDED",
        "MONEY PLUS SOCIEDADE DE CREDITO AO MICRO",
        "BMP MONEY PLUS SOCIEDADE DE CRÉDITO DIRETO SA"
    ]

    # ========== APP ENQUADRAMENTO ==========

    # HEADER
    with st.container():
        cols = st.columns([0.095, 0.905])
        with cols[0]:
            st.image("imagens/Capital-branca.png", width=400, output_format="PNG")
        with cols[1]:
            st.markdown(
                f"""
                <span style='
                    color: {HONEYDEW};
                    font-size: 2.4rem;
                    font-weight:900;
                    border-bottom: 2px solid {HARVEST_GOLD}99;
                    padding-bottom: 0.12em;'>
                    LIBRA CAPITAL
                    <span style='font-weight:400;color:{HARVEST_GOLD};'>| Enquadramento</span>
                </span>
                """,
                unsafe_allow_html=True
            )

    st.markdown('<br/>', unsafe_allow_html=True)

    fundo_sel = st.selectbox("Selecione o fundo", ["Apuama", "Bristol"])
    limites = LIMITES[fundo_sel]

    # caminho salvo em /tmp
    tmp_path = f"/tmp/{fundo_sel}.xlsx"

    uploaded_file = st.file_uploader(f"Envie o arquivo de estoque ({fundo_sel})", type=["xlsx"], key=f"upload_{fundo_sel}")
    if uploaded_file is not None:
        # salva o arquivo em /tmp
        with open(tmp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        df_estoque = pd.read_excel(uploaded_file)
    elif os.path.exists(tmp_path):
        df_estoque = pd.read_excel(tmp_path)
        st.info(f"Usando arquivo salvo anteriormente para {fundo_sel}.")
    else:
        st.warning("Nenhum arquivo enviado ainda.")
        df_estoque = None

    if df_estoque is not None:
        df_estoque = df_estoque.rename(columns={
            "NOME_CEDENTE": "Cedente",
            "DOC_CEDENTE": "CNPJ_Cedente",
            "NOME_SACADO": "Sacado",
            "DOC_SACADO": "CNPJ_Sacado",
            "VALOR_NOMINAL": "Valor"
        })

        # substitui cedente -> sacado
        mask = df_estoque["Cedente"].isin(CEDENTES_SUBSTITUIR)
        df_estoque.loc[mask, "Cedente"] = df_estoque.loc[mask, "Sacado"]
        df_estoque.loc[mask, "CNPJ_Cedente"] = df_estoque.loc[mask, "CNPJ_Sacado"]

        # consolida
        df_estoque = df_estoque.groupby(["Cedente", "CNPJ_Cedente", "Sacado", "CNPJ_Sacado"], as_index=False)["Valor"].sum()

        # PL
        GOOGLE_SHEET_ID = "1F4ziJnyxpLr9VuksbSvL21cjmGzoV0mDPSk7XzX72iQ"
        aba_pl = "Dre_Apuama" if fundo_sel == "Apuama" else "Dre_Bristol"
        url_pl = f"https://docs.google.com/spreadsheets/d/{GOOGLE_SHEET_ID}/gviz/tq?tqx=out:csv&sheet={aba_pl}"
        r_pl = requests.get(url_pl)
        r_pl.raise_for_status()
        df_pl = pd.read_csv(StringIO(r_pl.text))
        df_pl["Data"] = pd.to_datetime(df_pl["Data"], dayfirst=True, errors="coerce")

        data_pl = df_pl["Data"].max()
        pl_fundo = converter_valor_br(df_pl.loc[df_pl["Data"] == data_pl, "PL TOTAL"].values[0])

        st.markdown(f"**PL usado ({fundo_sel} - {data_pl.strftime('%d/%m/%Y')}):** R$ {pl_fundo:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

        # Cedentes
        df_cedentes = df_estoque.groupby(["Cedente", "CNPJ_Cedente"], as_index=False)["Valor"].sum()
        df_cedentes["%PL"] = df_cedentes["Valor"].astype(float) / float(pl_fundo) * 100
        df_cedentes = df_cedentes.sort_values("%PL", ascending=False)

        maior_cedente = df_cedentes.iloc[0]
        top5_cedentes = df_cedentes.head(5)["%PL"].sum()

        st.metric(
            "Maior Cedente",
            f"{maior_cedente['Cedente']} - {maior_cedente['%PL']:.2f}%",
            delta="✅ Enquadrado" if maior_cedente['%PL'] <= limites["maior_cedente"] else "❌ Fora do Limite"
        )
        st.metric(
            "Top 5 Cedentes",
            f"{top5_cedentes:.2f}%",
            delta="✅ Enquadrado" if top5_cedentes <= limites["top_cedentes"] else "❌ Fora do Limite"
        )

        df_cedentes["Valor"] = df_cedentes["Valor"].apply(lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        df_cedentes["%PL"] = df_cedentes["%PL"].apply(lambda x: f"{x:.2f}%")

        st.markdown("#### Cedentes")
        st.dataframe(df_cedentes, use_container_width=True, height=400)

        # Sacados
        df_sacados = df_estoque.groupby(["Sacado", "CNPJ_Sacado"], as_index=False)["Valor"].sum()
        df_sacados["%PL"] = df_sacados["Valor"].astype(float) / float(pl_fundo) * 100
        df_sacados = df_sacados.sort_values("%PL", ascending=False)

        maior_sacado = df_sacados.iloc[0]
        topN_sacados = df_sacados.head(10 if fundo_sel == "Apuama" else 5)["%PL"].sum()

        st.metric(
            "Maior Sacado",
            f"{maior_sacado['Sacado']} - {maior_sacado['%PL']:.2f}%",
            delta="✅ Enquadrado" if maior_sacado['%PL'] <= limites["maior_sacado"] else "❌ Fora do Limite"
        )
        st.metric(
            f"Top {'10' if fundo_sel == 'Apuama' else '5'} Sacados",
            f"{topN_sacados:.2f}%",
            delta="✅ Enquadrado" if topN_sacados <= limites["top_sacados"] else "❌ Fora do Limite"
        )

        df_sacados["Valor"] = df_sacados["Valor"].apply(lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        df_sacados["%PL"] = df_sacados["%PL"].apply(lambda x: f"{x:.2f}%")

        st.markdown("#### Sacados")
        st.dataframe(df_sacados, use_container_width=True, height=400)

    # RODAPÉ
    st.markdown(
        f"""<p style="text-align: right; color: {HONEYDEW}; font-size: 1em;">
            Powered by Juan & Streamlit | <b style="color:{HARVEST_GOLD}">LIBRA CAPITAL</b> 🦁
        </p>""",
        unsafe_allow_html=True,

        
    )
