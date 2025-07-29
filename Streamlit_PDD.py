import streamlit as st
import pandas as pd


def run():
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
            .stDataFrame th {{
                background-color: {SLATE_GRAY} !important;
                color: {HONEYDEW} !important;
                font-weight: bold;
            }}
        </style>
    """, unsafe_allow_html=True)

    st.title("Análise PDD por Cedente e Data")

    # ========== FUNDO ==========
    opcoes_fundos = {
        "FIDC APUAMA": "Analise_PDD_Apuama",
        "FIDC BRISTOL": "Analise_PDD_Bristol"
    }

    @st.cache_data
    def carregar_dados(sheet_name):
        base = "https://docs.google.com/spreadsheets/d/1F4ziJnyxpLr9VuksbSvL21cjmGzoV0mDPSk7XzX72iQ/gviz/tq?tqx=out:csv&sheet="
        df = pd.read_csv(base + sheet_name)
        df.columns = df.columns.str.strip()
        return df

    fundo_exibido = st.selectbox("Selecione o fundo:", list(opcoes_fundos.keys()))
    aba = opcoes_fundos[fundo_exibido]
    df = carregar_dados(aba)

    # ========== TRATAMENTO ==========
    df["Cedente"] = df["Cedente"].astype(str).str.strip()
    df["Data"] = pd.to_datetime(df["Data"], errors="coerce", dayfirst=True)
    df["PDD Prevista"] = (
        df["PDD Prevista"]
        .astype(str)
        .str.replace("\u00A0", "")
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False)
    )
    df["PDD Prevista"] = pd.to_numeric(df["PDD Prevista"], errors="coerce").fillna(0.0)

    df_grouped = df.groupby(["Cedente", "Data"], as_index=False)["PDD Prevista"].sum()
    df_pivot = df_grouped.pivot(index="Cedente", columns="Data", values="PDD Prevista").fillna(0)
    df_pivot.columns = [col.strftime('%d/%m/%Y') for col in df_pivot.columns]
    df_pivot.reset_index(inplace=True)

    # ========== MUDANÇAS ==========
    cols_data = df_pivot.columns[1:]
    mudou = pd.DataFrame(False, index=df_pivot.index, columns=cols_data)
    for i in range(1, len(cols_data)):
        mudou[cols_data[i]] = df_pivot[cols_data[i]] != df_pivot[cols_data[i - 1]]
    df_pivot["_MUDOU"] = mudou.apply(lambda row: [col for col in row.index if row[col]], axis=1)

    # ========== TOTAL ==========
    linha_total = {"Cedente": "TOTAL", "_MUDOU": []}
    for col in cols_data:
        linha_total[col] = df_pivot[col].sum()
    df_pivot = pd.concat([df_pivot, pd.DataFrame([linha_total])], ignore_index=True)

    # ========== ESTILO ==========
    def highlight_changes(row):
        mudou_cols = df_pivot.loc[row.name, "_MUDOU"] if "_MUDOU" in df_pivot.columns else []
        is_total = row["Cedente"] == "TOTAL"
        styles = []
        for col in row.index:
            if col == "Cedente":
                styles.append("font-weight: bold" if is_total else "")
            elif col in mudou_cols:
                styles.append(f"background-color: {AZUL_MUDANCA}; color: {HONEYDEW}; font-weight: bold")
            else:
                styles.append(f"background-color: #444444; color: white; font-weight: bold" if is_total else "")
        return styles

    # Criar nova versão sem coluna "_MUDOU"
    df_display = df_pivot.drop(columns=["_MUDOU"])

    # Aplicar estilo
    styled_df = df_display.style.apply(highlight_changes, axis=1).format(precision=2, thousands='.', decimal=',')

    st.markdown("### Matriz de PDD Prevista (com variações e total por dia)")
    st.dataframe(styled_df, use_container_width=True, height=700)