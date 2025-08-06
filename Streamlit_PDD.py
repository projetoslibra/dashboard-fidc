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
    # NOME_SACADO pode não existir em versões antigas — garante a coluna
    if "NOME_SACADO" not in df.columns:
        df["NOME_SACADO"] = ""
    else:
        df["NOME_SACADO"] = df["NOME_SACADO"].astype(str).str.strip()

    df["Data"] = pd.to_datetime(df["Data"], errors="coerce", dayfirst=True)
    df["PDD Prevista"] = (
        df["PDD Prevista"]
        .astype(str)
        .str.replace("\u00A0", "")
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False)
    )
    df["PDD Prevista"] = pd.to_numeric(df["PDD Prevista"], errors="coerce").fillna(0.0)

    # ========= MATRIZ ORIGINAL POR CEDENTE (mantida) =========
    df_grouped = df.groupby(["Cedente", "Data"], as_index=False)["PDD Prevista"].sum()
    df_pivot = df_grouped.pivot(index="Cedente", columns="Data", values="PDD Prevista").fillna(0)
    # ordena datas
    df_pivot = df_pivot.reindex(sorted(df_pivot.columns), axis=1)
    df_pivot.columns = [col.strftime('%d/%m/%Y') for col in df_pivot.columns]
    df_pivot.reset_index(inplace=True)

    # MUDANÇAS
    cols_data = df_pivot.columns[1:]
    mudou = pd.DataFrame(False, index=df_pivot.index, columns=cols_data)
    for i in range(1, len(cols_data)):
        mudou[cols_data[i]] = df_pivot[cols_data[i]] != df_pivot[cols_data[i - 1]]
    df_pivot["_MUDOU"] = mudou.apply(lambda row: [col for col in row.index if row[col]], axis=1)

    # TOTAL
    linha_total = {"Cedente": "TOTAL", "_MUDOU": []}
    for col in cols_data:
        linha_total[col] = df_pivot[col].sum()
    df_pivot = pd.concat([df_pivot, pd.DataFrame([linha_total])], ignore_index=True)

    # ESTILO
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

    df_display = df_pivot.drop(columns=["_MUDOU"])
    styled_df = df_display.style.apply(highlight_changes, axis=1).format(precision=2, thousands='.', decimal=',')

    st.markdown("### Matriz de PDD Prevista (com variações e total por dia) — **Cedente**")
    st.dataframe(styled_df, use_container_width=True, height=520)

    # ========= DRILL-DOWN AGGRID (Cedente -> NOME_SACADO) =========
    st.markdown("---")
    st.subheader("🔁 Drill-down por NOME_SACADO (AgGrid)")

    # Prepara dados: linhas = (Cedente, NOME_SACADO), colunas = Data
    df_group2 = df.groupby(["Cedente", "NOME_SACADO", "Data"], as_index=False)["PDD Prevista"].sum()
    pivot_sacado = df_group2.pivot(index=["Cedente", "NOME_SACADO"], columns="Data", values="PDD Prevista").fillna(0)
    # ordena datas e formata cabeçalho
    pivot_sacado = pivot_sacado.reindex(sorted(pivot_sacado.columns), axis=1)
    date_cols_fmt = [c.strftime("%d/%m/%Y") for c in pivot_sacado.columns]
    pivot_sacado.columns = date_cols_fmt
    pivot_sacado.reset_index(inplace=True)
















    # --- AgGrid ---
    try:
        from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, JsCode

        # Formatação numérica pt-BR
        br_value_formatter = JsCode("""
            function(params) {
                if (params.value == null) { return ''; }
                return params.value.toLocaleString('pt-BR', {minimumFractionDigits: 2, maximumFractionDigits: 2});
            }
        """)

        # Auto-ajuste das colunas ao carregar
        on_first_data_rendered = JsCode("""
            function(params) {
                var allColIds = [];
                var allColumns = params.columnApi.getAllColumns();
                for (var i = 0; i < allColumns.length; i++) {
                    allColIds.push(allColumns[i].getColId());
                }
                params.columnApi.autoSizeColumns(allColIds, false);
            }
        """)

        gb = GridOptionsBuilder.from_dataframe(pivot_sacado)

        DATE_COL_MIN_WIDTH = 110  # ajuste conforme desejar
        for i, col in enumerate(date_cols_fmt):
            # configura coluna de data como numérica somável
            gb.configure_column(
                col,
                type=["numericColumn", "rightAligned"],
                aggFunc="sum",
                valueFormatter=br_value_formatter,
                minWidth=DATE_COL_MIN_WIDTH,
                resizable=True
            )
            # regra de cor azul quando muda vs. dia anterior (linha folha e linha de grupo)
            if i > 0:
                prev_col = date_cols_fmt[i - 1]
                rule_js = JsCode(f"""
                    function(params) {{
                        // ignora total fixado e footers
                        if (params.node && (params.node.rowPinned || params.node.footer)) return false;

                        // 1) Linha folha (Sacado)
                        if (!params.node || !params.node.group) {{
                            var curr = params.data['{col}'];
                            var prev = params.data['{prev_col}'];
                            if (curr == null || prev == null) return false;
                            return curr !== prev;
                        }}

                        // 2) Linha de grupo (Cedente): soma filhos filtrados
                        var kids = params.node.childrenAfterFilter || params.node.allLeafChildren || [];
                        var currSum = 0, prevSum = 0;
                        for (var j = 0; j < kids.length; j++) {{
                            var d = kids[j].data;
                            if (!d) continue;
                            var cv = Number(d['{col}']) || 0;
                            var pv = Number(d['{prev_col}']) || 0;
                            currSum += cv;
                            prevSum += pv;
                        }}
                        return currSum !== prevSum;
                    }}
                """)
                gb.configure_column(col, cellClassRules={"changed-cell": rule_js})

        # Agrupamento por Cedente
        gb.configure_column("Cedente", rowGroup=True, hide=True)
        gb.configure_column("NOME_SACADO", headerName="Sacado", minWidth=180, resizable=True)

        gb.configure_grid_options(
            groupIncludeFooter=True,          # subtotal por cedente
            groupIncludeTotalFooter=False,    # total geral ficará na linha fixada
            suppressAggFuncInHeader=True,
            animateRows=True,
            groupDefaultExpanded=0,
            headerHeight=32,
            rowHeight=30,
            onFirstDataRendered=on_first_data_rendered,
            autoGroupColumnDef={
                "headerName": "Cedente",
                "minWidth": 220,
                "cellRendererParams": {"suppressCount": False}
            }
        )

        grid_options = gb.build()

        # === Linha TOTAL fixada no rodapé (soma por data) ===
        totals = {"Cedente": "TOTAL", "NOME_SACADO": ""}
        for c in date_cols_fmt:
            totals[c] = float(pivot_sacado[c].sum()) if c in pivot_sacado.columns else 0.0
        grid_options["pinnedBottomRowData"] = [totals]

        # Estilos da célula alterada (AZUL) e do rodapé TOTAL
        custom_css = {
            # Container principal da grid
            ".ag-root-wrapper": {
                "border-radius": "14px",
                "overflow": "hidden",  # importante pra cortar as quinas internas
                "border": "1px solid rgba(255,255,255,0.18)",
                "box-shadow": "0 8px 24px rgba(0,0,0,0.35)"
            },

            # Mantém sua regra de célula alterada (AZUL)
            ".ag-cell.changed-cell": {
                "background-color": AZUL_MUDANCA,
                "color": HONEYDEW,
                "font-weight": "bold"
            },

            # Linha TOTAL (pinned bottom)
            ".ag-floating-bottom .ag-cell": {
                "background-color": "#1f3440",
                "color": HONEYDEW,
                "font-weight": "bold",
                "border-top": "1px solid rgba(255,255,255,0.25)"
            },

            # Remove bordas internas do header/rodapé para ficar limpo com o radius
            ".ag-header, .ag-floating-bottom": {
                "border": "none"
            }
        }

        AgGrid(
            pivot_sacado,
            gridOptions=grid_options,
            update_mode=GridUpdateMode.NO_UPDATE,
            enable_enterprise_modules=True,
            fit_columns_on_grid_load=False,
            height=560,
            allow_unsafe_jscode=True,
            custom_css=custom_css,
            theme="streamlit",
        )

    except Exception as e:
        st.warning(f"AgGrid não pôde ser carregado ({e}). Exibindo fallback simples por cedente.")
        st.dataframe(
            pivot_sacado.style.format(precision=2, thousands='.', decimal=','),
            use_container_width=True, height=560
        )


run()
