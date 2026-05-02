import streamlit as st
import pandas as pd
import numpy as np
import unicodedata
import re
from datetime import datetime
from streamlit_gsheets import GSheetsConnection
import matplotlib.pyplot as plt

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
    # Mapeamento conforme sua Matriz de Metas de Abril a Setembro
    meses_map = {4:'Abril', 5:'Maio', 6:'Junho', 7:'Julho', 8:'Agosto', 9:'Setembro'}
    return meses_map.get(datetime.now().month, 'Maio')

# =============================================================================
# CONEXÃO COM GOOGLE SHEETS
# =============================================================================
try:
    # URL e Aba configuradas para sua planilha da F5
    URL_PLANILHA = "https://docs.google.com/spreadsheets/d/1tv9dTG6H-X_h2reOibL8KB99LIUM_YaR/edit#gid=0"
    NOME_ABA = "DADOSMATRICULASCONSULTOR"
    
    conn = st.connection("gsheets", type=GSheetsConnection)
    df_dados = conn.read(spreadsheet=URL_PLANILHA, worksheet=NOME_ABA)
    
    MESES = ['Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro']
    for m in MESES:
        if m in df_dados.columns:
            df_dados[m] = pd.to_numeric(df_dados[m], errors='coerce').fillna(0)
            
except Exception as e:
    st.error(f"Erro de Conexão: {e}")
    st.stop()

# =============================================================================
# INTERFACE
# =============================================================================

st.title("🚀 Gestor de Metas F5 - Full Sync")

tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "📝 Lançamento", "🏆 Ranking"])

with tab1:
    total_geral = int(df_dados[MESES].sum().sum())
    mes_at = get_mes_atual()
    total_mes = int(df_dados[mes_at].sum())
    
    col1, col2 = st.columns(2)
    col1.metric("Acumulado 2026.2", f"{total_geral} / 325")
    col2.metric(f"Total em {mes_at}", total_mes)
    
    st.subheader(f"Produção por Curso ({mes_at})")
    chart_data = df_dados.groupby('Curso')[mes_at].sum().sort_values()
    st.bar_chart(chart_data)

with tab2:
    st.subheader("Registrar Matrícula")
    texto_input = st.text_area("Cole o texto da matrícula aqui:", height=200)
    
    if st.button("🚀 Processar e Salvar"):
        if texto_input:
            try:
                # Extração via Regex baseada no seu padrão de Sobral
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
                    # Comando de atualização corrigido
                    conn.update(spreadsheet=URL_PLANILHA, worksheet=NOME_ABA, data=df_dados)
                    st.success(f"Matrícula de {curso_raw} para {consultor_raw} salva!")
                    st.balloons()
                    st.rerun()
                else:
                    st.error("Consultor ou Curso não encontrados na planilha.")
            except Exception as e:
                st.error(f"Erro ao processar: {e}")

with tab3:
    ranking = df_dados.groupby('Consultor')[MESES].sum().sum(axis=1).sort_values(ascending=False).reset_index()
    ranking.columns = ['Consultor', 'Matrículas']
    st.dataframe(ranking, use_container_width=True)
    import urllib.parse

# --- CONEXÃO BLINDADA v1.5 (COM TRATAMENTO DE ESPAÇOS) ---
try:
    URL_PLANILHA = "https://docs.google.com/spreadsheets/d/1tv9dTG6H-X_h2reOibL8KB99LIUM_YaR/edit#gid=0"
    NOME_ABA = "DADOS MATRICULAS CONSULTOR"
    
    # Codifica o nome da aba para transformar espaços em '%20'
    nome_aba_codificado = urllib.parse.quote(NOME_ABA)
    
    conn = st.connection("gsheets", type=GSheetsConnection)
    
    # Lendo os dados com o nome da aba já tratado
    df_dados = conn.read(spreadsheet=URL_PLANILHA, worksheet=nome_aba_codificado)
    
    MESES = ['Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro']
    for m in MESES:
        if m in df_dados.columns:
            df_dados[m] = pd.to_numeric(df_dados[m], errors='coerce').fillna(0)
            
except Exception as e:
    st.error(f"Erro de Conexão na v1.5: {e}")
    st.stop()
