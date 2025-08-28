import streamlit as st
import pandas as pd
from io import BytesIO

def run():
    # ========== CORES VISUAL PREMIUM ==========
    SPACE_CADET = "#042F3C"
    HARVEST_GOLD = "#C66300"
    HONEYDEW = "#FFF4E3"
    SLATE_GRAY = "#717c89"
    AZUL_MUDANCA = "#3c71e8"

    # ========== CSS VISUAL PREMIUM ==========
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

    try:
        df = carregar_dados(aba)
    except Exception as e:
        st.error(f"Falha ao carregar dados da planilha: {e}")
        st.stop()

    # ========== TRATAMENTO ==========
    df["Cedente"] = df["Cedente"].astype(str).str.strip()
    if "NOME_SACADO" not in df.columns:
        df["NOME_SACADO"] = ""
    else:
        df["NOME_SACADO"] = df["NOME_SACADO"].astype(str).str.strip()

    df["Data"] = pd.to_datetime(df["Data"], errors="coerce", dayfirst=True)
    df["PDD Prevista"] = (
        df["PDD Prevista"].astype(str)
        .str.replace("\u00A0", "")
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False)
    )
    df["PDD Prevista"] = pd.to_numeric(df["PDD Prevista"], errors="coerce").fillna(0.0)

    # ========= DRILL-DOWN AGGRID (Cedente -> NOME_SACADO) =========
    st.subheader("🔁 PDD por Cedente e Sacado (com variação diária)")

    # Linhas = (Cedente, NOME_SACADO), Colunas = Datas
    df_group2 = df.groupby(["Cedente", "NOME_SACADO", "Data"], as_index=False)["PDD Prevista"].sum()
    pivot_sacado = df_group2.pivot(index=["Cedente", "NOME_SACADO"], columns="Data", values="PDD Prevista").fillna(0)
    pivot_sacado = pivot_sacado.reindex(sorted(pivot_sacado.columns), axis=1)
    date_cols_fmt = [c.strftime("%d/%m/%Y") for c in pivot_sacado.columns]
    pivot_sacado.columns = date_cols_fmt
    pivot_sacado.reset_index(inplace=True)

    grid_response = None  # vamos tentar capturar os dados exibidos no AgGrid

    # --- AgGrid ---
    try:
        from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, JsCode

        # Formatador numérico pt-BR
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

        DATE_COL_MIN_WIDTH = 110
        for i, col in enumerate(date_cols_fmt):
            gb.configure_column(
                col,
                type=["numericColumn", "rightAligned"],
                enableValue=True,           # <- garante agregação no grupo
                aggFunc="sum",
                valueFormatter=br_value_formatter,
                minWidth=DATE_COL_MIN_WIDTH,
                resizable=True
            )
            if i > 0:
                prev_col = date_cols_fmt[i - 1]
                rule_js = JsCode(f"""
                    function(params) {{
                        if (params.node && (params.node.rowPinned || params.node.footer)) return false;

                        if (!params.node || !params.node.group) {{
                            var curr = params.data['{col}'];
                            var prev = params.data['{prev_col}'];
                            if (curr == null || prev == null) return false;
                            return curr !== prev;
                        }}

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
            groupIncludeFooter=False,
            groupIncludeTotalFooter=False,
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

        # Linha TOTAL fixada no rodapé
        totals = {"Cedente": "TOTAL", "NOME_SACADO": ""}
        for c in date_cols_fmt:
            totals[c] = float(pivot_sacado[c].sum()) if c in pivot_sacado.columns else 0.0
        grid_options["pinnedBottomRowData"] = [totals]

        # CSS (radius + destaque azul + rodapé)
        custom_css = {
            ".ag-root-wrapper": {
                "border-radius": "14px",
                "overflow": "hidden",
                "border": "1px solid rgba(255,255,255,0.18)",
                "box-shadow": "0 8px 24px rgba(0,0,0,0.35)"
            },
            ".ag-cell.changed-cell": {
                "background-color": AZUL_MUDANCA,
                "color": HONEYDEW,
                "font-weight": "bold"
            },
            ".ag-floating-bottom .ag-cell": {
                "background-color": "#1f3440",
                "color": HONEYDEW,
                "font-weight": "bold",
                "border-top": "1px solid rgba(255,255,255,0.25)"
            },
            ".ag-header, .ag-floating-bottom": { "border": "none" }
        }

        grid_response = AgGrid(
            pivot_sacado,
            gridOptions=grid_options,
            update_mode=GridUpdateMode.MODEL_CHANGED,  # <- captura filtros/edições
            data_return_mode="AS_INPUT",
            enable_enterprise_modules=True,
            fit_columns_on_grid_load=False,
            height=560,
            allow_unsafe_jscode=True,
            custom_css=custom_css,
        )

    except Exception as e:
        st.warning(f"AgGrid não pôde ser carregado ({e}). Exibindo fallback simples por cedente.")
        st.dataframe(
            pivot_sacado.style.format(precision=2, thousands='.', decimal=','),
            use_container_width=True, height=560
        )

    # ========== EXPORTAR PARA EXCEL ==========
    def montar_excel(df_export: pd.DataFrame) -> bytes:
        """
        Gera um .xlsx em memória, com formatação numérica para as colunas de data,
        e inclui uma linha TOTAL (como no grid).
        """
        # garante existência das colunas chave
        for col in ["Cedente", "NOME_SACADO"]:
            if col not in df_export.columns:
                df_export[col] = ""  # evita erro se usuário filtrou algo estranho

        # adiciona TOTAL ao dataframe exportado
        total_row = {col: "" for col in df_export.columns}
        total_row["Cedente"] = "TOTAL"
        if len(date_cols_fmt) > 0:
            for c in date_cols_fmt:
                if c in df_export.columns:
                    total_row[c] = pd.to_numeric(df_export[c], errors="coerce").fillna(0).sum()
        df_out = pd.concat([df_export, pd.DataFrame([total_row])], ignore_index=True)

        # escreve em memória
        buf = BytesIO()
        with pd.ExcelWriter(buf, engine="xlsxwriter") as writer:
            df_out.to_excel(writer, index=False, sheet_name="PDD")
            wb  = writer.book
            ws  = writer.sheets["PDD"]

            # formatos
            fmt_num = wb.add_format({"num_format": "#,##0.00"})
            fmt_header = wb.add_format({"bold": True})
            fmt_total = wb.add_format({"bold": True})

            # cabeçalhos em bold
            ws.set_row(0, None, fmt_header)

            # largura automática simples
            for i, col in enumerate(df_out.columns):
                col_series = df_out[col].astype(str)
                max_len = max(12, min(60, col_series.map(len).max() + 2))
                ws.set_column(i, i, max_len)

            # aplica formato numérico nas colunas de datas
            for i, col in enumerate(df_out.columns):
                if col in date_cols_fmt:
                    ws.set_column(i, i, None, fmt_num)

            # destaca linha TOTAL (última)
            total_row_idx = len(df_out)  # 1-based + header; ajustaremos abaixo
            ws.set_row(total_row_idx, None, fmt_total)  # total_row_idx já está correto: header é linha 0 no pandas/xlsxwriter

        buf.seek(0)
        return buf.getvalue()

    # decide o que exportar: dados do grid (respeita filtros) ou a pivot original
    if grid_response and "data" in grid_response and grid_response["data"] is not None:
        df_para_exportar = pd.DataFrame(grid_response["data"])
    else:
        df_para_exportar = pivot_sacado.copy()

    arquivo = montar_excel(df_para_exportar)
    nome_arquivo = f"PDD_{fundo_exibido.replace(' ', '_')}_{pd.Timestamp.today().strftime('%Y-%m-%d')}.xlsx"

    st.download_button(
        "⬇️ Baixar Excel da Tabela",
        data=arquivo,
        file_name=nome_arquivo,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        help="Exporta a tabela atual (respeita filtros feitos no grid) com linha TOTAL."
    )
