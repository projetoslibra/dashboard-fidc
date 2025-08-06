import streamlit as st
import pandas as pd


def run():
    # ========== CORES VISUAL PREMIUM ==========
    SPACE_CADET = "#042F3C"
    HARVEST_GOLD = "#C66300"
    HONEYDEW = "#FFF4E3"
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
    def carregar_dados(sheet_name: str) -> pd.DataFrame:
        base = "https://docs.google.com/spreadsheets/d/1F4ziJnyxpLr9VuksbSvL21cjmGzoV0mDPSk7XzX72iQ/gviz/tq?tqx=out:csv&sheet="
        df = pd.read_csv(base + sheet_name)
        # Normaliza nomes de colunas e garante colunas esperadas
        df.columns = df.columns.str.strip()
        # Padroniza nomes exatamente como combinamos
        rename_map = {
            "Data": "Data",
            "Cedente": "Cedente",
            "NOME_SACADO": "NOME_SACADO",
            "PDD Prevista": "PDD Prevista"
        }
        df = df.rename(columns=rename_map)
        # Sanitização dos campos usados
        df["Cedente"] = df["Cedente"].astype(str).str.strip()
        df["NOME_SACADO"] = df.get("NOME_SACADO", "").astype(str).str.strip()
        df["Data"] = pd.to_datetime(df["Data"], errors="coerce", dayfirst=True)
        df["PDD Prevista"] = (
            df["PDD Prevista"]
            .astype(str)
            .str.replace("\u00A0", "")
            .str.replace(".", "", regex=False)
            .str.replace(",", ".", regex=False)
        )
        df["PDD Prevista"] = pd.to_numeric(df["PDD Prevista"], errors="coerce").fillna(0.0)
        return df

    fundo_exibido = st.selectbox("Selecione o fundo:", list(opcoes_fundos.keys()))
    aba = opcoes_fundos[fundo_exibido]
    df = carregar_dados(aba)

    # ========== FUNÇÕES AUXILIARES ==========
    def montar_pivot_com_mudancas(df_base: pd.DataFrame, indice: str) -> pd.DataFrame:
        """
        Gera pivot (linhas=indice, colunas=Data) com soma de PDD,
        marca colunas que mudaram vs dia anterior em _MUDOU e
        adiciona linha TOTAL no final.
        """
        df_grouped = df_base.groupby([indice, "Data"], as_index=False)["PDD Prevista"].sum()
        pivot = df_grouped.pivot(index=indice, columns="Data", values="PDD Prevista").fillna(0)

        # Ordena as datas e formata cabeçalho dd/mm/yyyy
        pivot = pivot.reindex(sorted(pivot.columns), axis=1)
        pivot.columns = [col.strftime('%d/%m/%Y') for col in pivot.columns]
        pivot.reset_index(inplace=True)

        # Detecta mudanças coluna a coluna (vs dia anterior)
        cols_data = pivot.columns[1:]
        mudou = pd.DataFrame(False, index=pivot.index, columns=cols_data)
        for i in range(1, len(cols_data)):
            mudou[cols_data[i]] = pivot[cols_data[i]] != pivot[cols_data[i - 1]]
        pivot["_MUDOU"] = mudou.apply(lambda row: [col for col in row.index if row[col]], axis=1)

        # Linha TOTAL
        linha_total = {indice: "TOTAL", "_MUDOU": []}
        for col in cols_data:
            linha_total[col] = pivot[col].sum()
        pivot = pd.concat([pivot, pd.DataFrame([linha_total])], ignore_index=True)
        return pivot

    def estilizar_tabela(pivot_df: pd.DataFrame, indice: str):
        """Aplica destaque de mudanças e formatação numérica."""
        cols_data = [c for c in pivot_df.columns if c not in (indice, "_MUDOU")]

        def highlight_changes(row):
            mudou_cols = pivot_df.loc[row.name, "_MUDOU"] if "_MUDOU" in pivot_df.columns else []
            is_total = row[indice] == "TOTAL"
            styles = []
            for col in row.index:
                if col == indice:
                    styles.append("font-weight: bold" if is_total else "")
                elif col in mudou_cols:
                    styles.append(f"background-color: {AZUL_MUDANCA}; color: {HONEYDEW}; font-weight: bold")
                else:
                    styles.append(f"background-color: #444444; color: white; font-weight: bold" if is_total else "")
            return styles

        df_display = pivot_df.drop(columns=["_MUDOU"])
        return df_display.style.apply(highlight_changes, axis=1).format(precision=2, thousands='.', decimal=',')

    # ========== NIVEL 1: CEDENTE ==========
    pivot_cedente = montar_pivot_com_mudancas(df, "Cedente")
    styled_cedente = estilizar_tabela(pivot_cedente, "Cedente")

    st.markdown("### Matriz de PDD Prevista por **Cedente** (com variações e total por dia)")
    st.dataframe(styled_cedente, use_container_width=True, height=600)

    # ========== DRILL-DOWN: NOME_SACADO ==========
    st.markdown("---")
    st.subheader("🔎 Abrir detalhes por Cedente (composição por NOME_SACADO)")

    cedentes_disponiveis = sorted([c for c in pivot_cedente["Cedente"].unique() if c != "TOTAL"])
    cedentes_escolhidos = st.multiselect(
        "Abrir cedente(s) para detalhar:",
        options=cedentes_disponiveis,
        default=[],
        placeholder="Selecione um ou mais cedentes para ver a composição por sacado..."
    )

    @st.cache_data
    def pivot_por_sacado(df_base: pd.DataFrame, cedente: str) -> pd.DataFrame:
        filtro = df_base[df_base["Cedente"] == cedente].copy()
        if filtro.empty:
            # Garante estrutura vazia coerente
            return montar_pivot_com_mudancas(
                df_base[df_base["Cedente"] == "__NUNCA__"], "NOME_SACADO"
            )
        return montar_pivot_com_mudancas(filtro, "NOME_SACADO")

    for ced in cedentes_escolhidos:
        with st.expander(f"Detalhe de {ced} — NOME_SACADO x Data (PDD Prevista)", expanded=False):
            pivot_sacado = pivot_por_sacado(df, ced)
            styled_sacado = estilizar_tabela(pivot_sacado, "NOME_SACADO")
            st.dataframe(styled_sacado, use_container_width=True, height=500)
