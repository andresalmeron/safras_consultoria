import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Configuração da Página
st.set_page_config(page_title="Análise de Safras: MF vs Sem MF", layout="wide")

st.title("📊 Comparador de Performance: Ex-MF vs Sem MF")
st.markdown("""
Este painel permite a comparação direta de indicadores de performance entre consultores com experiência prévia no mercado financeiro (**Com MF**) e sem experiência (**Sem MF**), segregados por safra (Turma).
""")

# --- Upload de Arquivos ---
st.sidebar.header("📂 Carregar Dados")
file_sem_mf = st.sidebar.file_uploader("Upload: Planilha Sem MF", type=["xlsx", "csv"])
file_mf = st.sidebar.file_uploader("Upload: Planilha Com MF", type=["xlsx", "csv"])

@st.cache_data
def load_data(file):
    """Função auxiliar para carregar CSV ou Excel"""
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
        # Encontrar turmas em comum para permitir a seleção
        turmas_sem = set(df_sem_mf['Turma'].unique())
        turmas_mf = set(df_mf['Turma'].unique())
        common_turmas = sorted(list(turmas_sem.intersection(turmas_mf)))

        if not common_turmas:
            st.error("Não foram encontradas Turmas em comum nos arquivos carregados.")
        else:
            # --- Seleção da Safra ---
            st.sidebar.markdown("---")
            selected_turma = st.sidebar.selectbox("Selecione a Safra (Turma)", common_turmas, index=len(common_turmas)-1)
            
            # Filtrar dados para a turma selecionada
            try:
                row_sem = df_sem_mf[df_sem_mf['Turma'] == selected_turma].iloc[0]
                row_mf = df_mf[df_mf['Turma'] == selected_turma].iloc[0]

                st.header(f"🔎 Análise Detalhada: Turma {selected_turma}")
                st.markdown("---")

                # --- KPIs Principais (Cards) ---
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.metric(
                        label="Entradas (Sem MF)", 
                        value=row_sem['Entradas Totais']
                    )
                    st.metric(
                        label="Entradas (MF)", 
                        value=row_mf['Entradas Totais'],
                        delta=int(row_mf['Entradas Totais'] - row_sem['Entradas Totais'])
                    )

                with col2:
                    st.metric(
                        label="Sobrevivência (Sem MF)", 
                        value=f"{row_sem['Sobrevivência (%)']:.1%}"
                    )
                    st.metric(
                        label="Sobrevivência (MF)", 
                        value=f"{row_mf['Sobrevivência (%)']:.1%}",
                        delta=f"{(row_mf['Sobrevivência (%)'] - row_sem['Sobrevivência (%)']):.1%}"
                    )

                with col3:
                    st.metric(
                        label="Tempo Médio Deslig. (Sem MF)", 
                        value=f"{row_sem['Tempo Médio (desl.) (meses)']} m"
                    )
                    st.metric(
                        label="Tempo Médio Deslig. (MF)", 
                        value=f"{row_mf['Tempo Médio (desl.) (meses)']} m",
                        delta=f"{(row_mf['Tempo Médio (desl.) (meses)'] - row_sem['Tempo Médio (desl.) (meses)']):.1f} m"
                    )
                
                with col4:
                    st.metric(
                        label="Ativos Atuais (Sem MF)",
                        value=row_sem['Ativos(as)']
                    )
                    st.metric(
                        label="Ativos Atuais (MF)",
                        value=row_mf['Ativos(as)'],
                        delta=int(row_mf['Ativos(as)'] - row_sem['Ativos(as)'])
                    )

                st.markdown("---")

                # --- Gráficos Comparativos ---
                c_chart1, c_chart2 = st.columns(2)

                # Gráfico 1: Comparativo Financeiro (AuC e Receita Médios)
                # Normalizando dados para plotagem
                metrics_fin = ['AuC Médio (Exc. desl.)', 'Receita Média (Exc. desl.)']
                
                fig_auc = go.Figure(data=[
                    go.Bar(name='Sem MF', x=metrics_fin, y=[row_sem[m] for m in metrics_fin], text=[f"R$ {row_sem[m]:,.0f}" for m in metrics_fin], textposition='auto', marker_color='#4c72b0'),
                    go.Bar(name='Com MF', x=metrics_fin, y=[row_mf[m] for m in metrics_fin], text=[f"R$ {row_mf[m]:,.0f}" for m in metrics_fin], textposition='auto', marker_color='#55a868')
                ])
                fig_auc.update_layout(title_text='Comparativo Médio: AuC e Receita', barmode='group')
                
                with c_chart1:
                    st.plotly_chart(fig_auc, use_container_width=True)

                # Gráfico 2: AuC Total da Safra
                fig_total = go.Figure(data=[
                    go.Bar(name='Sem MF', x=['AuC Total'], y=[row_sem['AuC Total']], text=f"R$ {row_sem['AuC Total']:,.0f}", textposition='auto', marker_color='#4c72b0'),
                    go.Bar(name='Com MF', x=['AuC Total'], y=[row_mf['AuC Total']], text=f"R$ {row_mf['AuC Total']:,.0f}", textposition='auto', marker_color='#55a868')
                ])
                fig_total.update_layout(title_text='AuC Total Acumulado da Safra', barmode='group')

                with c_chart2:
                    st.plotly_chart(fig_total, use_container_width=True)

                # --- Tabela de Dados Brutos ---
                with st.expander("Ver Dados Brutos da Safra Selecionada"):
                    st.write("**Sem MF**")
                    st.dataframe(row_sem.to_frame().T)
                    st.write("**Com MF**")
                    st.dataframe(row_mf.to_frame().T)

            except IndexError:
                st.warning("Dados incompletos para a turma selecionada em um dos arquivos.")
else:
    st.info("👈 Por favor, faça o upload das planilhas 'Sem MF' e 'Com MF' na barra lateral para iniciar a análise.")
