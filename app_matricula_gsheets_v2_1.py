import streamlit as st
import pandas as pd
import numpy as np
import unicodedata
import re
from datetime import datetime
from collections import Counter
import matplotlib.pyplot as plt
from streamlit_gsheets import GSheetsConnection

# =============================================================================
# CONFIGURAÇÕES DA PÁGINA
# =============================================================================
st.set_page_config(page_title="Gestor de Metas F5 - Full Sync", layout="wide", page_icon="🚀")

# CSS Customizado para Alertas e Estilo
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .critico { color: #e74c3c; font-weight: bold; }
    .atencao { color: #f1c40f; font-weight: bold; }
    .sucesso { color: #2ecc71; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# =============================================================================
# FUNÇÕES DE UTILIDADE
# =============================================================================

def remover_acentos(texto):
    if not isinstance(texto, str): return str(texto)
    texto_normalizado = unicodedata.normalize('NFD', texto)
    texto_sem_acentos = "".join([c for c in texto_normalizado if unicodedata.category(c) != 'Mn'])
    return " ".join(texto_sem_acentos.upper().split())

def get_mes_atual():
    return {4:'Abril', 5:'Maio', 6:'Junho', 7:'Julho', 8:'Agosto', 9:'Setembro'}.get(datetime.now().month, 'Abril')

# =============================================================================
# CONSTANTES E METAS
# =============================================================================
MESES = ['Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro']
META_GERAL_2026 = 325
METAS_MENSAIS_GLOBAIS = {'Abril': 17, 'Maio': 51, 'Junho': 68, 'Julho': 120, 'Agosto': 51, 'Setembro': 18}
MATRIZ_METAS = {
    'ADMINISTRACAO': {'Abril': 1, 'Maio': 5, 'Junho': 6, 'Julho': 11, 'Agosto': 5, 'Setembro': 2},
    'ARQUITETURA': {'Abril': 1, 'Maio': 4, 'Junho': 6, 'Julho': 9, 'Agosto': 4, 'Setembro': 1},
    'DIREITO - MANHA': {'Abril': 1, 'Maio': 4, 'Junho': 5, 'Julho': 9, 'Agosto': 4, 'Setembro': 2},
    'DIREITO - NOITE': {'Abril': 2, 'Maio': 7, 'Junho': 11, 'Julho': 19, 'Agosto': 8, 'Setembro': 3},
    'ENFERMAGEM - MANHA': {'Abril': 1, 'Maio': 4, 'Junho': 6, 'Julho': 9, 'Agosto': 4, 'Setembro': 1},
    'ENFERMAGEM - NOITE': {'Abril': 3, 'Maio': 7, 'Junho': 10, 'Julho': 19, 'Agosto': 8, 'Setembro': 3},
    'ENGENHARIA': {'Abril': 2, 'Maio': 4, 'Junho': 5, 'Julho': 9, 'Agosto': 4, 'Setembro': 1},
    'FISIOTERAPIA': {'Abril': 2, 'Maio': 6, 'Junho': 7, 'Julho': 13, 'Agosto': 5, 'Setembro': 2},
    'ODONTOLOGIA': {'Abril': 2, 'Maio': 4, 'Junho': 5, 'Julho': 9, 'Agosto': 4, 'Setembro': 1},
    'PSICOLOGIA': {'Abril': 2, 'Maio': 6, 'Junho': 7, 'Julho': 13, 'Agosto': 5, 'Setembro': 2}
}

# =============================================================================
# CONEXÃO COM GOOGLE SHEETS
# =============================================================================

st.title("🚀 Gestor de Metas F5 - Full Sync Edition")

# URL da sua planilha (Substitua pela sua URL real)
URL_SHEET = "SUA_URL_DO_GOOGLE_SHEETS"

with st.sidebar:
    st.header("🔗 Conexão")
    if URL_SHEET == "SUA_URL_DO_GOOGLE_SHEETS":
        st.warning("Por favor, insira a URL da sua planilha no código ou abaixo:")
        url_input = st.text_input("URL do Google Sheets:", key="url_gsheets_input")
        if url_input:
            URL_SHEET = url_input
    
    if st.button("🔄 Atualizar Dashboard", key="btn_refresh"):
        st.cache_data.clear()
        st.rerun()

# Lógica de Leitura e Escrita
if URL_SHEET and URL_SHEET != "SUA_URL_DO_GOOGLE_SHEETS":
    try:
        # Criando a conexão
        conn = st.connection("gsheets", type=GSheetsConnection)
        
        # Lendo os dados da aba específica
        df_full = conn.read(spreadsheet=URL_SHEET, worksheet="DADOS MATRICULAS CONSULTOR")
        
        # Limpeza e Conversão para exibição
        df_display = df_full.copy()
        for m in MESES:
            if m in df_display.columns:
                df_display[m] = pd.to_numeric(df_display[m], errors='coerce').fillna(0)
        
        df_dados = df_display.dropna(subset=['Consultor', 'Curso']).copy()
        df_dados = df_dados[~df_dados['Consultor'].isin(['TOTAL', 'TOTAL GERAL', 'Curso / turno'])]
        df_dados['Total_Calc'] = df_dados[MESES].sum(axis=1)
        
        # --- ABAS DO STREAMLIT ---
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Dashboard", "🎯 Metas Consultores", "📅 Metas Mensais", "💰 Pagamentos", "🏆 Rankings"])

        # TAB 1: DASHBOARD
        with tab1:
            col1, col2, col3, col4 = st.columns(4)
            total_geral = int(df_dados['Total_Calc'].sum())
            perc_geral = (total_geral / META_GERAL_2026) * 100
            mes_at = get_mes_atual()
            total_mes = int(df_dados[mes_at].sum())
            
            col1.metric("Total Geral", total_geral)
            col2.metric("% Meta 2026.2", f"{perc_geral:.1f}%")
            col3.metric(f"Total {mes_at}", total_mes)
            
            stats_cons = df_dados.groupby('Consultor')['Total_Calc'].sum().sort_values(ascending=False)
            if not stats_cons.empty:
                col4.metric("Top Consultor", stats_cons.index[0], int(stats_cons.iloc[0]))

            # Lançamento Rápido com Escrita no GSheets (Lógica Refinada)
            st.subheader("📝 Lançamento Rápido")
            texto_input = st.text_area("Cole o texto da matrícula aqui:", height=150, placeholder="SEGUE MATRICULA - ...", key="txt_area_lancamento")
            
            if st.button("Lançar Matrícula", key="btn_lancar_matricula"):
                if texto_input:
                    try:
                        # 1. Extração por Regex baseada no seu padrão de texto
                        consultor = re.search(r"CONSULTOR RESPONSÁVEL:\s*(.*)", texto_input, re.IGNORECASE).group(1).strip()
                        curso = re.search(r"AREA DESEJADA:\s*(.*)", texto_input, re.IGNORECASE).group(1).strip()
                        
                        # 2. Normalização para garantir o "match" com a planilha
                        consultor_norm = remover_acentos(consultor)
                        curso_norm = remover_acentos(curso)
                        
                        mes_atual_lanc = get_mes_atual()
                        
                        # 3. Localização na Planilha (usando os nomes normalizados)
                        # Criamos cópias temporárias das colunas para comparação sem acentos
                        df_comp = df_full.copy()
                        df_comp['Consultor_Norm'] = df_comp['Consultor'].apply(remover_acentos)
                        df_comp['Curso_Norm'] = df_comp['Curso'].apply(remover_acentos)
                        
                        idx = df_comp[(df_comp['Consultor_Norm'] == consultor_norm) & 
                                     (df_comp['Curso_Norm'] == curso_norm)].index
                        
                        if not idx.empty:
                            # 4. Atualização do valor (+1 na célula do mês)
                            # Garante que o valor atual seja numérico antes de somar
                            valor_atual = pd.to_numeric(df_full.at[idx[0], mes_atual_lanc], errors='coerce')
                            if np.isnan(valor_atual): valor_atual = 0
                            df_full.at[idx[0], mes_atual_lanc] = valor_atual + 1
                            
                            # 5. Envio imediato para o Google Sheets via HTTPS
                            conn.update(worksheet="DADOS MATRICULAS CONSULTOR", data=df_full)
                            
                            st.success(f"✅ Sucesso! Matrícula de {curso} (Consultor: {consultor}) computada em {mes_atual_lanc}.")
                            st.balloons() # Um toque de comemoração!
                            
                            # Limpa o cache e recarrega para mostrar os novos dados
                            st.cache_data.clear()
                            st.rerun()
                        else:
                            st.error(f"❌ Erro: Não encontrei a combinação '{consultor}' + '{curso}' na planilha.")
                            
                    except Exception as e:
                        st.error(f"⚠️ Erro ao processar o texto: Verifique se todos os campos estão presentes.")
                else:
                    st.warning("⚠️ Por favor, cole o texto da matrícula primeiro.")

            # Alertas de Cursos Críticos
            st.subheader("⚠️ Alertas de Atenção (Cursos < 50% da Meta)")
            cursos_stats = df_dados.groupby('Curso')['Total_Calc'].sum().reset_index()
            alertas = []
            for _, row in cursos_stats.iterrows():
                c_norm = remover_acentos(row['Curso'])
                meta_curso = 25
                for k, v in MATRIZ_METAS.items():
                    if remover_acentos(k) in c_norm: meta_curso = sum(v.values()); break
                perc = (row['Total_Calc'] / meta_curso) * 100 if meta_curso > 0 else 100
                if perc < 50:
                    alertas.append({"Curso": row['Curso'], "Realizado": int(row['Total_Calc']), "Meta": meta_curso, "Progresso": f"{perc:.1f}%"})
            if alertas: st.table(pd.DataFrame(alertas))
            else: st.success("Todos os cursos estão com bom desempenho!")

        # TAB 2: METAS CONSULTORES
        with tab2:
            st.subheader("🎯 Acompanhamento por Consultor (Meta: 25)")
            df_cons = stats_cons.reset_index()
            df_cons['Meta'] = 25
            df_cons['% Atingido'] = (df_cons['Total_Calc'] / 25) * 100
            df_cons['Falta'] = (25 - df_cons['Total_Calc']).clip(lower=0)
            def color_status(val):
                if val < 50: return 'background-color: #ffcccc'
                if val <= 80: return 'background-color: #fff3cd'
                return 'background-color: #d4edda'
            st.dataframe(df_cons.style.applymap(color_status, subset=['% Atingido']).format({'% Atingido': '{:.1f}%'}), use_container_width=True)

        # TAB 3: METAS MENSAIS
        with tab3:
            st.subheader("📅 Meta Mensal Global")
            vendas_mes = df_dados[MESES].sum()
            resumo_mes = []
            for m in MESES:
                meta = METAS_MENSAIS_GLOBAIS[m]
                real = int(vendas_mes[m])
                resumo_mes.append({"Mês": m, "Meta": meta, "Realizado": real, "Gap": real - meta})
            st.table(pd.DataFrame(resumo_mes))

        # TAB 4: PAGAMENTOS
        with tab4:
            st.subheader("💰 Distribuição de Pagamentos")
            st.info("Gráfico baseado nos dados gerais da planilha.")
            fig_pag, ax_pag = plt.subplots()
            ax_pag.pie([33, 33, 34], labels=['FIES', 'PROUNI', 'PARTICULAR'], autopct='%1.1f%%')
            st.pyplot(fig_pag)

        # TAB 5: RANKINGS
        with tab5:
            st.subheader("🏆 Ranking de Cursos")
            rank_df = df_dados.groupby('Curso')['Total_Calc'].sum().sort_values(ascending=False).reset_index()
            rank_df.index = rank_df.index + 1
            st.dataframe(rank_df, use_container_width=True)

    except Exception as e:
        st.error(f"Erro ao conectar com Google Sheets: {e}")
        st.info("Certifique-se de que a planilha está compartilhada corretamente.")

else:
    st.info("Aguardando configuração da URL do Google Sheets para carregar o Dashboard...")
