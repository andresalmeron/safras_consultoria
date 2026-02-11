import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# Configuração da Página
st.set_page_config(page_title="Análise Detalhada: MF vs Sem MF", layout="wide")

st.title("📊 Comparador de Performance: Ex-MF vs Sem MF (Geeko Mode 🦎)")

# --- Função de Formatação Brasileira ---
def format_br(valor, tipo):
    """
    Formata números para o padrão brasileiro (1.000,00).
    tipo: 'dinheiro', 'porcentagem', 'decimal'
    """
    if pd.isna(valor):
        return "-"
        
    if tipo == 'dinheiro':
        # Ex: 1234.56 -> R$ 1.234,56
        texto = f"R$ {valor:,.2f}"
        return texto.replace(',', 'X').replace('.', ',').replace('X', '.')
    
    elif tipo == 'porcentagem':
        # Ex: 0.50 -> 50,0%
        texto = f"{valor:.1%}"
        return texto.replace('.', ',')
    
    elif tipo == 'decimal':
        # Ex: 1234.5 -> 1.234,5
        texto = f"{valor:,.1f}"
        return texto.replace(',', 'X').replace('.', ',').replace('X', '.')
    
    return str(valor)

# --- Upload de Arquivos ---
st.sidebar.header("📂 Carregar Dados")
file_sem_mf = st.sidebar.file_uploader("Upload: Planilha Sem MF", type=["xlsx", "csv"])
file_mf = st.sidebar.file_uploader("Upload: Planilha Com MF", type=["xlsx", "csv"])

@st.cache_data
def load_data(file):
    try:
        if file.name.endswith('.csv'):
            return pd.read_csv(file)
        else:
            return pd.read_excel(file)
    except Exception as e:
        st.error(f"Erro ao ler o arquivo {file.name}: {e}")
        return None

if file_sem_mf and file_mf:
    df_sem_mf = load_data(file_sem_mf)
    df_mf = load_data(file_mf)

    if df_sem_mf is not None and df_mf is not None:
        # Encontrar turmas em comum
        turmas_sem = set(df_sem_mf['Turma'].unique())
        turmas_mf = set(df_mf['Turma'].unique())
        common_turmas = sorted(list(turmas_sem.intersection(turmas_mf)))

        if not common_turmas:
            st.error("Não foram encontradas Turmas em comum nos arquivos carregados.")
        else:
            # --- Seleção da Safra ---
            st.sidebar.markdown("---")
            selected_turma = st.sidebar.selectbox("Selecione a Safra (Turma)", common_turmas, index=len(common_turmas)-1)
            
            try:
                # Filtrar dados para a turma selecionada
                row_sem = df_sem_mf[df_sem_mf['Turma'] == selected_turma].iloc[0]
                row_mf = df_mf[df_mf['Turma'] == selected_turma].iloc[0]

                st.header(f"🔎 Análise da Turma {selected_turma}")
                st.markdown(f"Comparativo direto indicador por indicador.")
                st.markdown("---")

                # Lista Reordenada: Pares de Média e Mediana
                metrics_to_plot = [
                    # KPIs Gerais
                    'Sobrevivência (%)',
                    'Tempo Médio (desl.) (meses)',
                    'AuC Total',
                    'Receita Anual (F12M) (0.4%)',
                    
                    # Bloco AuC (Média vs Mediana)
                    'AuC Médio (Inc. desl.)',
                    'AuC Mediano (Inc. desl.)',
                    'AuC Médio (Exc. desl.)',
                    'AuC Mediano (Exc. desl.)',
                    
                    # Bloco Receita (Média vs Mediana)
                    'Receita Média (Exc. desl.)',
                    'Receita - Mediana (exc. Desl.)' # Nova Coluna
                ]

                color_sem_mf = '#4c72b0' # Azul
                color_mf = '#55a868'     # Verde

                for metric in metrics_to_plot:
                    # Verifica se a coluna existe no dataframe carregado
                    if metric in row_sem and metric in row_mf:
                        
                        val_sem = row_sem[metric]
                        val_mf = row_mf[metric]
                        
                        # Cálculo da diferença (tratando possíveis nulos)
                        if pd.notna(val_sem) and pd.notna(val_mf):
                            diff = val_mf - val_sem
                        else:
                            diff = 0
                        
                        # Definição de formatação
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
                        else:
                            text_fmt_sem = str(val_sem)
                            text_fmt_mf = str(val_mf)
                            text_diff = str(diff)

                        # Container para o bloco do indicador
                        with st.container():
                            st.subheader(metric)
                            col_graph, col_table = st.columns([2, 1])

                            # --- Coluna 1: Gráfico ---
                            with col_graph:
                                fig = go.Figure()
                                fig.add_trace(go.Bar(
                                    x=['Sem MF', 'Com MF'],
                                    y=[val_sem, val_mf],
                                    text=[text_fmt_sem, text_fmt_mf],
                                    textposition='auto',
                                    marker_color=[color_sem_mf, color_mf]
                                ))
                                fig.update_layout(
                                    margin=dict(l=20, r=20, t=20, b=20),
                                    height=300,
                                    showlegend=False
                                )
                                st.plotly_chart(fig, use_container_width=True)

                            # --- Coluna 2: Tabela ---
                            with col_table:
                                st.markdown("##### Dados Detalhados")
                                df_display = pd.DataFrame({
                                    "Grupo": ["Sem MF", "Com MF"],
                                    "Valor": [text_fmt_sem, text_fmt_mf],
                                    "Diferença Abs.": ["-", text_diff]
                                })
                                st.table(df_display)
                            
                            st.markdown("---")
                    else:
                        # Aviso discreto se a coluna nova ainda não estiver na planilha antiga
                        # st.warning(f"Indicador '{metric}' não encontrado.") # Comentado para não poluir se usar planilha antiga
                        pass

            except IndexError:
                st.warning("Dados incompletos para a turma selecionada.")
else:
    st.info("👈 Por favor, faça o upload das planilhas 'Sem MF' e 'Com MF' para iniciar a análise.")
