import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode

def run():
    opcoes_fundos = {
        "FIDC APUAMA": "Analise_PDD_Apuama",
        "FIDC BRISTOL": "Analise_PDD_Bristol"
    }

    # ========== CORES VISUAL PREMIUM ==========
    SPACE_CADET = "#272846"
    HARVEST_GOLD = "#e5a125"
    HONEYDEW = "#f0f8ea"
    SLATE_GRAY = "#717c89"
    AZUL_MUDANCA = "#3c71e8"

    # ========== CSS VISUAL PREMIUM ==========
    st.set_page_config(page_title="Análise PDD", layout="wide")
    st.markdown(f"""
        <style>
            html, body, .stApp, .block-container {{
                background-color: {SPACE_CADET} !important;
                color: {HARVEST_GOLD} !important;
            }}
            h1, h2, h3, h4, h5, h6, p, span, div {{
                color: {HARVEST_GOLD} !important;
            }}
            .ag-theme-streamlit .ag-header-cell-label {{
                color: {HARVEST_GOLD} !important;
                font-weight: bold;
            }}
            .ag-theme-streamlit .ag-cell {{
                background-color: {SPACE_CADET} !important;
                color: {HONEYDEW} !important;
                font-size: 0.95em;
            }}
            .ag-theme-streamlit .ag-header {{
                background-color: {SLATE_GRAY} !important;
            }}
        </style>
    """, unsafe_allow_html=True)

    st.title("Análise PDD por Cedente e Data")

    # ========== FUNÇÃO DE CARREGAMENTO ==========
    @st.cache_data
    def carregar_dados(sheet_name):
        base = "https://docs.google.com/spreadsheets/d/1F4ziJnyxpLr9VuksbSvL21cjmGzoV0mDPSk7XzX72iQ/gviz/tq?tqx=out:csv&sheet="
        df = pd.read_csv(base + sheet_name)
        df.columns = df.columns.str.strip()
        return df

    # ========== SELEÇÃO DE ABA ==========
    #aba = st.selectbox("Selecione o fundo:", ["Analise_PDD_Apuama", "Analise_PDD_Bristol"])
    fundo_exibido = st.selectbox("Selecione o fundo:", list(opcoes_fundos.keys()))
    aba = opcoes_fundos[fundo_exibido]
    df = carregar_dados(aba)


    # ========== TRATAMENTO DE DADOS ==========
    df.columns = df.columns.str.strip()
    df["Cedente"] = df["Cedente"].astype(str).str.strip()
    df["Data"] = pd.to_datetime(df["Data"], errors="coerce", dayfirst=True)

    df["PDD Prevista"] = (
        df["PDD Prevista"]
        .astype(str)
        .str.replace("\u00A0", "", regex=False)
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False)
    )
    df["PDD Prevista"] = pd.to_numeric(df["PDD Prevista"], errors="coerce").fillna(0.0)

    # ========== AGRUPAMENTO ==========
    df_grouped = df.groupby(["Cedente", "Data"], as_index=False)["PDD Prevista"].sum()

    # ========== PIVOT ==========
    df_pivot = df_grouped.pivot(index="Cedente", columns="Data", values="PDD Prevista").fillna(0)
    datas_ordenadas = sorted(df_pivot.columns)
    df_pivot.columns = [col.strftime('%d/%m/%Y') for col in datas_ordenadas]
    df_pivot.reset_index(inplace=True)

    for col in df_pivot.columns[1:]:
        df_pivot[col] = df_pivot[col].round(2)

    # ========== DETECTAR MUDANÇAS ==========
    cols_data = df_pivot.columns[1:]
    mudou = pd.DataFrame(False, index=df_pivot.index, columns=cols_data)

    for i in range(1, len(cols_data)):
        anterior = cols_data[i - 1]
        atual = cols_data[i]
        mudou[atual] = df_pivot[anterior] != df_pivot[atual]

    df_pivot["_MUDOU"] = mudou.apply(lambda row: [col for col in row.index if row[col]], axis=1)

    # ========== ADICIONAR LINHA TOTAL ==========
    linha_total = {"Cedente": "TOTAL", "_MUDOU": []}
    for col in cols_data:
        linha_total[col] = df_pivot[col].sum()
    df_pivot = pd.concat([df_pivot, pd.DataFrame([linha_total])], ignore_index=True)

    # ========== AGGRID ==========
    gb = GridOptionsBuilder.from_dataframe(df_pivot.drop(columns=["_MUDOU"]))
    gb.configure_default_column(resizable=True, filterable=True, sortable=True)

    for col in df_pivot.columns:
        if col == "Cedente":
            gb.configure_column(col, pinned=True, min_width=200)
        elif col != "_MUDOU":
            js = JsCode(f"""
            function(params) {{
                if (params.data.Cedente === "TOTAL") {{
                    return {{'backgroundColor': '#444444', 'color': 'white', 'fontWeight': 'bold'}};
                }}
                if (params.data._MUDOU && params.data._MUDOU.includes("{col}")) {{
                    return {{'backgroundColor': '{AZUL_MUDANCA}', 'color': '{HONEYDEW}', 'fontWeight': 'bold'}};
                }}
            }}
            """)
            gb.configure_column(
                col,
                min_width=110,
                type=["numericColumn", "customNumericFormat"],
                valueFormatter=JsCode("function(params) { return params.value != null ? params.value.toLocaleString('pt-BR', { minimumFractionDigits: 2 }) : '' }"),
                cellStyle=js
            )

    grid_options = gb.build()

    st.markdown("### Matriz de PDD Prevista (com variações e total por dia)")
    AgGrid(
        df_pivot,
        gridOptions=grid_options,
        height=650,
        allow_unsafe_jscode=True,
        enable_enterprise_modules=True,
        reload_data=True,
    )
