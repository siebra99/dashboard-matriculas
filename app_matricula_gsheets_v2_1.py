import streamlit as st
import pandas as pd
import numpy as np
import unicodedata
import re
from datetime import datetime
from streamlit_gsheets import GSheetsConnection
import urllib.parse

# =============================================================================
# CONFIGURAÇÕES DA PÁGINA
# =============================================================================
st.set_page_config(page_title="Gestor de Metas F5", layout="wide", page_icon="🚀")

# =============================================================================
# FUNÇÕES DE UTILIDADE
# =============================================================================

def remover_acentos(texto):
    if not isinstance(texto, str): return str(texto)
    texto_normalizado = unicodedata.normalize('NFD', texto)
    return "".join([c for c in texto_normalizado if unicodedata.category(c) != 'Mn']).upper().strip()

def get_mes_atual():
    meses_map = {4:'Abril', 5:'Maio', 6:'Junho', 7:'Julho', 8:'Agosto', 9:'Setembro'}
    return meses_map.get(datetime.now().month, 'Maio')

# =============================================================================
# CONEXÃO BLINDADA v1.5 (TRATAMENTO DE URL E ESPAÇOS)
# =============================================================================
try:
    # URL e Nome da Aba
    URL_BASE = "https://docs.google.com/spreadsheets/d/1tv9dTG6H-X_h2reOibL8KB99LIUM_YaR/edit?usp=sharing&ouid=115939420972517598197&rtpof=true&sd=true"
    NOME_ABA_ORIGINAL = "DADOS_MATRICULAS_CONSULTOR"
    
    # Codificação para evitar erro de 'control characters' devido aos espaços
    nome_aba_url = urllib.parse.quote(NOME_ABA_ORIGINAL)
    
    conn = st.connection("gsheets", type=GSheetsConnection)
    
    # Leitura dos dados
    df_dados = conn.read(spreadsheet=URL_BASE, worksheet=nome_aba_url)
    
    # Garantir que colunas de meses sejam numéricas
    MESES = ['Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro']
    for m in MESES:
        if m in df_dados.columns:
            df_dados[m] = pd.to_numeric(df_dados[m], errors='coerce').fillna(0)
            
except Exception as e:
    st.error(f"Erro de Conexão na v1.5: {e}")
    st.info("Dica: Verifique se o nome da aba no Google Sheets não possui espaços extras no final.")
    st.stop()

# =============================================================================
# INTERFACE DO USUÁRIO
# =============================================================================

st.title("🚀 Gestor de Metas F5 - Conexão Segura")

tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "📝 Lançar Matrícula", "🏆 Ranking"])

with tab1:
    col1, col2, col3 = st.columns(3)
    
    total_geral = int(df_dados[MESES].sum().sum())
    mes_at = get_mes_atual()
    total_mes = int(df_dados[mes_at].sum())
    
    col1.metric("Acumulado Geral", f"{total_geral} / 325")
    col2.metric(f"Total em {mes_at}", total_mes)
    col3.metric("Progresso", f"{(total_geral/325)*100:.1f}%")

    st.subheader(f"Desempenho por Curso ({mes_at})")
    chart_data = df_dados.groupby('Curso')[mes_at].sum().sort_values()
    st.bar_chart(chart_data)

with tab2:
    st.subheader("Registrar Nova Matrícula")
    texto_input = st.text_area("Cole os dados aqui:", height=200)
    
    if st.button("🚀 Confirmar e Salvar na Planilha"):
        if texto_input:
            try:
                # Extração via Regex
                consultor_raw = re.search(r"CONSULTOR RESPONSÁVEL:\s*(.*)", texto_input, re.IGNORECASE).group(1).strip()
                curso_raw = re.search(r"AREA DESEJADA:\s*(.*)", texto_input, re.IGNORECASE).group(1).strip()
                
                # Normalização para busca
                cons_norm = remover_acentos(consultor_raw)
                curs_norm = remover_acentos(curso_raw)
                
                df_temp = df_dados.copy()
                df_temp['C_N'] = df_temp['Consultor'].apply(remover_acentos)
                df_temp['K_N'] = df_temp['Curso'].apply(remover_acentos)
                
                idx = df_temp[(df_temp['C_N'] == cons_norm) & (df_temp['K_N'] == curs_norm)].index
                
                if not idx.empty:
                    df_dados.at[idx[0], mes_at] += 1
                    
                    # Atualização no Google Sheets usando o nome original (a lib trata a escrita)
                    conn.update(spreadsheet=URL_BASE, worksheet=NOME_ABA_ORIGINAL, data=df_dados)
                    
                    st.success(f"Matrícula de {curso_raw} ({consultor_raw}) salva com sucesso!")
                    st.balloons()
                    st.rerun()
                else:
                    st.error("Consultor ou Curso não localizados na planilha.")
            except Exception as e:
                st.error(f"Erro no processamento: {e}")

with tab3:
    st.subheader("🏆 Ranking de Consultores")
    ranking = df_dados.groupby('Consultor')[MESES].sum().sum(axis=1).sort_values(ascending=False).reset_index()
    ranking.columns = ['Consultor', 'Matrículas']
    st.dataframe(ranking, use_container_width=True)
