import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# Configuração da Página
st.set_page_config(page_title="Análise Detalhada: MF vs Sem MF", layout="wide")

st.title("📊 Comparador de Performance: Ex-MF vs Sem MF")

# --- Função de Formatação Brasileira ---
def format_br(valor, tipo):
    if pd.isna(valor):
        return "-"
        
    if tipo == 'dinheiro':
        texto = f"R$ {valor:,.2f}"
        return texto.replace(',', 'X').replace('.', ',').replace('X', '.')
    
    elif tipo == 'porcentagem':
        texto = f"{valor:.1%}"
        return texto.replace('.', ',')
    
    elif tipo == 'decimal':
        texto = f"{valor:,.1f}"
        return texto.replace(',', 'X').replace('.', ',').replace('X', '.')
    
    elif tipo == 'inteiro':
        texto = f"{valor:,.0f}"
        return texto.replace(',', 'X').replace('.', ',').replace('X', '.')
    
    return str(valor)

# --- Função para Normalizar Colunas ---
def normalize_columns(df):
    """
    Padroniza os nomes das colunas de Receita Mediana que vieram diferentes
    nas duas planilhas.
    """
    cols_map = {}
    for col in df.columns:
        if "Receita" in col and "Mediana" in col and ("Exc" in col or "exc" in col):
            cols_map[col] = "Receita Mediana (Exc. desl.)"
            
    if cols_map:
        return df.rename(columns=cols_map)
    return df

# --- Upload de Arquivos ---
st.sidebar.header("📂 Carregar Dados")
file_sem_mf = st.sidebar.file_uploader("Upload: Planilha Sem MF", type=["xlsx", "csv"])
file_mf = st.sidebar.file_uploader("Upload: Planilha Com MF", type=["xlsx", "csv"])

@st.cache_data
def load_data(file):
    try:
        if file.name.endswith('.csv'):
            df = pd.read_csv(file)
        else:
            df = pd.read_excel(file)
        return normalize_columns(df)
    except Exception as e:
        st.error(f"Erro ao ler o arquivo {file.name}: {e}")
        return None

if file_sem_mf and file_mf:
    df_sem_mf = load_data(file_sem_mf)
    df_mf = load_data(file_mf)

    if df_sem_mf is not None and df_mf is not None:
        turmas_sem = set(df_sem_mf['Turma'].unique())
        turmas_mf = set(df_mf['Turma'].unique())
        common_turmas = sorted(list(turmas_sem.intersection(turmas_mf)))

        if not common_turmas:
            st.error("Não foram encontradas Turmas em comum.")
        else:
            # --- Seleção da Safra ---
            st.sidebar.markdown("---")
            selected_turma = st.sidebar.selectbox("Selecione a Safra (Turma)", common_turmas, index=len(common_turmas)-1)
            
            try:
                row_sem = df_sem_mf[df_sem_mf['Turma'] == selected_turma].iloc[0]
                row_mf = df_mf[df_mf['Turma'] == selected_turma].iloc[0]

                st.header(f"🔎 Análise da Turma {selected_turma}")
                
                # --- LISTAS DE INDICADORES ---
                all_metrics = [
                    # Contexto
                    'Entradas Totais',
                    'Ativos(as)',
                    
                    # KPIs Gerais
                    'Sobrevivência (%)',
                    'Tempo Médio (desl.) (meses)',
                    'AuC Total',
                    'Receita Anual (F12M) (0.4%)',
                    
                    # Bloco AuC
                    'AuC Médio (Inc. desl.)',
                    'AuC Mediano (Inc. desl.)',
                    'AuC Médio (Exc. desl.)',
                    'AuC Mediano (Exc. desl.)',
                    
                    # Bloco Receita
                    'Receita Média (Exc. desl.)',
                    'Receita Mediana (Exc. desl.)'
                ]
                
                # --- DEFAULT (ATUALIZADO) ---
                default_metrics = [
                    'Entradas Totais',
                    'Ativos(as)',
                    'AuC Médio (Exc. desl.)',
                    'AuC Mediano (Exc. desl.)',
                    'Receita Média (Exc. desl.)',
                    'Receita Mediana (Exc. desl.)'
                ]

                # --- SELETOR DE DADOS ---
                selected_metrics = st.multiselect(
                    "📌 Selecione os indicadores que deseja visualizar:",
                    options=all_metrics,
                    default=default_metrics
                )
                
                st.markdown("---")

                for metric in selected_metrics:
                    if metric in row_sem and metric in row_mf:
                        
                        val_sem = row_sem[metric]
                        val_mf = row_mf[metric]
                        
                        if pd.notna(val_sem) and pd.notna(val_mf):
                            diff = val_mf - val_sem
                        else:
                            diff = 0
                        
                        # Formatação Inteligente
                        if "(%)" in metric:
                            text_fmt_sem = format_br(val_sem, 'porcentagem')
                            text_fmt_mf = format_br(val_mf, 'porcentagem')
                            text_diff = format_br(diff, 'porcentagem')
                            
                        elif "AuC" in metric or "Receita" in metric:
                            text_fmt_sem = format_br(val_sem, 'dinheiro')
                            text_fmt_mf = format_br(val_mf, 'dinheiro')
                            text_diff = format_br(diff, 'dinheiro').replace("R$ ", "")
                            
                        elif "meses" in metric:
                            text_fmt_sem = f"{format_br(val_sem, 'decimal')} meses"
                            text_fmt_mf = f"{format_br(val_mf, 'decimal')} meses"
                            text_diff = f"{format_br(diff, 'decimal')}"
                            
                        elif metric in ['Entradas Totais', 'Ativos(as)']:
                            text_fmt_sem = format_br(val_sem, 'inteiro')
                            text_fmt_mf = format_br(val_mf, 'inteiro')
                            text_diff = format_br(diff, 'inteiro')
                            
                        else:
                            text_fmt_sem = str(val_sem)
                            text_fmt_mf = str(val_mf)
                            text_diff = str(diff)

                        with st.container():
                            st.subheader(metric)
                            col_graph, col_table = st.columns([2, 1])

                            with col_graph:
                                fig = go.Figure()
                                fig.add_trace(go.Bar(
                                    x=['Sem MF', 'Com MF'],
                                    y=[val_sem, val_mf],
                                    text=[text_fmt_sem, text_fmt_mf],
                                    textposition='auto',
                                    marker_color=['#4c72b0', '#55a868']
                                ))
                                fig.update_layout(
                                    margin=dict(l=20, r=20, t=20, b=20),
                                    height=300,
                                    showlegend=False
                                )
                                # Key única mantida
                                st.plotly_chart(fig, use_container_width=True, key=metric)

                            with col_table:
                                st.markdown("##### Dados Detalhados")
                                df_display = pd.DataFrame({
                                    "Grupo": ["Sem MF", "Com MF"],
                                    "Valor": [text_fmt_sem, text_fmt_mf],
                                    "Diferença Abs.": ["-", text_diff]
                                })
                                st.table(df_display)
                            
                            st.markdown("---")
            except IndexError:
                st.warning("Dados incompletos para a turma selecionada.")
else:
    st.info("👈 Por favor, faça o upload das planilhas 'Sem MF' e 'Com MF' para iniciar a análise.")
