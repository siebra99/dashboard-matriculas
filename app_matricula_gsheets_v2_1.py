import streamlit as st
import pandas as pd
import numpy as np
import unicodedata
import re
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# =============================================================================
# CONFIGURAÇÕES DA PÁGINA
# =============================================================================
st.set_page_config(page_title="Gestor de Metas F5 - v1.6", layout="wide", page_icon="🚀")

# =============================================================================
# FUNÇÕES DE UTILIDADE
# =============================================================================

def remover_acentos(texto):
    if not isinstance(texto, str): return str(texto)
    texto_normalizado = unicodedata.normalize('NFD', texto)
    return "".join([c for c in texto_normalizado if unicodedata.category(c) != 'Mn']).upper().strip()

def get_mes_atual():
    # Sincronizado com o calendário de Sobral e metas da faculdade
    meses_map = {4:'Abril', 5:'Maio', 6:'Junho', 7:'Julho', 8:'Agosto', 9:'Setembro'}
    return meses_map.get(datetime.now().month, 'Maio')

# =============================================================================
# CONEXÃO DIRETA v1.6
# =============================================================================
try:
    # URL e Nome da Aba Simplificado (Sem espaços para evitar erro 404)
    URL_BASE = "https://docs.google.com/spreadsheets/d/1tv9dTG6H-X_h2reOibL8KB99LIUM_YaR/edit#gid=0"
    NOME_ABA = "DADOS_MATRICULAS" 
    
    conn = st.connection("gsheets", type=GSheetsConnection)
    
    # Leitura dos dados
    df_dados = conn.read(spreadsheet=URL_BASE, worksheet=NOME_ABA)
    
    MESES = ['Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro']
    for m in MESES:
        if m in df_dados.columns:
            df_dados[m] = pd.to_numeric(df_dados[m], errors='coerce').fillna(0)
            
except Exception as e:
    st.error(f"Erro de Conexão: {e}")
    st.info("Verifique se renomeou a aba para 'DADOS_MATRICULAS' no Google Sheets.")
    st.stop()

# =============================================================================
# INTERFACE
# =============================================================================

st.title("🚀 Gestor de Metas F5 - Full Sync")

tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "📝 Lançar Matrícula", "🏆 Ranking"])

with tab1:
    total_geral = int(df_dados[MESES].sum().sum())
    mes_at = get_mes_atual()
    total_mes = int(df_dados[mes_at].sum())
    
    col1, col2 = st.columns(2)
    col1.metric("Acumulado Geral", f"{total_geral} / 325")
    col2.metric(f"Total em {mes_at}", total_mes)

    st.subheader(f"Produção por Curso ({mes_at})")
    chart_data = df_dados.groupby('Curso')[mes_at].sum().sort_values()
    st.bar_chart(chart_data)

with tab2:
    st.subheader("Registrar Matrícula")
    texto_input = st.text_area("Cole os dados aqui:", height=200)
    
    if st.button("🚀 Salvar na Planilha"):
        if texto_input:
            try:
                # Extração Regex baseada no seu padrão de Sobral
                consultor_raw = re.search(r"CONSULTOR RESPONSÁVEL:\s*(.*)", texto_input, re.IGNORECASE).group(1).strip()
                curso_raw = re.search(r"AREA DESEJADA:\s*(.*)", texto_input, re.IGNORECASE).group(1).strip()
                
                cons_norm = remover_acentos(consultor_raw)
                curs_norm = remover_acentos(curso_raw)
                
                df_temp = df_dados.copy()
                df_temp['C_N'] = df_temp['Consultor'].apply(remover_acentos)
                df_temp['K_N'] = df_temp['Curso'].apply(remover_acentos)
                
                idx = df_temp[(df_temp['C_N'] == cons_norm) & (df_temp['K_N'] == curs_norm)].index
                
                if not idx.empty:
                    df_dados.at[idx[0], mes_at] += 1
                    conn.update(spreadsheet=URL_BASE, worksheet=NOME_ABA, data=df_dados)
                    st.success(f"Matrícula salva com sucesso!")
                    st.balloons()
                    st.rerun()
                else:
                    st.error("Consultor ou Curso não localizados.")
            except Exception as e:
                st.error(f"Erro: {e}")

with tab3:
    ranking = df_dados.groupby('Consultor')[MESES].sum().sum(axis=1).sort_values(ascending=False).reset_index()
    ranking.columns = ['Consultor', 'Total']
    st.dataframe(ranking, use_container_width=True)
