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
st.set_page_config(page_title="Gestor de Metas F5 - Blindado", layout="wide", page_icon="🚀")

# CSS para estilo visual
st.markdown("""
    <style>
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .main { background-color: #f8f9fa; }
    </style>
    """, unsafe_allow_html=True)

# =============================================================================
# FUNÇÕES DE UTILIDADE
# =============================================================================

def remover_acentos(texto):
    if not isinstance(texto, str): return str(texto)
    texto_normalizado = unicodedata.normalize('NFD', texto)
    return "".join([c for c in texto_normalizado if unicodedata.category(c) != 'Mn']).upper().strip()

def get_mes_atual():
    # Mapeamento de meses (Abril a Setembro conforme sua matriz)
    meses_map = {4:'Abril', 5:'Maio', 6:'Junho', 7:'Julho', 8:'Agosto', 9:'Setembro'}
    # Retorna o mês atual ou 'Maio' como padrão de segurança
    return meses_map.get(datetime.now().month, 'Maio')

# =============================================================================
# CONEXÃO BLINDADA COM GOOGLE SHEETS (v1.4)
# =============================================================================
try:
    # URL Direta para evitar erros de caracteres nos Secrets
    URL_PLANILHA = "https://docs.google.com/spreadsheets/d/1tv9dTG6H-X_h2reOibL8KB99LIUM_YaR/edit?gid=1895700493#gid=1895700493"
    NOME_ABA = "DADOS MATRICULAS CONSULTOR"
    
    conn = st.connection("gsheets", type=GSheetsConnection)
    
    # Leitura direta ignorando configurações externas de URL
    df_dados = conn.read(spreadsheet=URL_PLANILHA, worksheet=NOME_ABA)
    
    # Conversão de colunas de meses para números (garantindo que cálculos funcionem)
    MESES = ['Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro']
    for m in MESES:
        if m in df_dados.columns:
            df_dados[m] = pd.to_numeric(df_dados[m], errors='coerce').fillna(0)
            
except Exception as e:
    st.error(f"❌ Erro de Conexão na v1.4: {e}")
    st.info(f"Certifique-se de que a aba da planilha se chama exatamente: '{NOME_ABA}'")
    st.stop()

# =============================================================================
# INTERFACE DO DASHBOARD
# =============================================================================

st.title("🚀 Gestor de Metas F5 - Full Sync")

tab1, tab2, tab3 = st.tabs(["📊 Dashboard Geral", "📝 Lançamento Rápido", "🏆 Ranking"])

# --- TAB 1: DASHBOARD ---
with tab1:
    col1, col2, col3 = st.columns(3)
    
    total_geral = int(df_dados[MESES].sum().sum())
    mes_at = get_mes_atual()
    total_mes = int(df_dados[mes_at].sum())
    meta_objetivo = 325
    
    col1.metric("Acumulado 2026.2", f"{total_geral} / {meta_objetivo}")
    col2.metric(f"Matrículas em {mes_at}", total_mes)
    col3.metric("Status da Meta", f"{(total_geral/meta_objetivo)*100:.1f}%")

    st.divider()
    st.subheader(f"📊 Produção por Curso ({mes_at})")
    chart_data = df_dados.groupby('Curso')[mes_at].sum().sort_values(ascending=True)
    st.bar_chart(chart_data)

# --- TAB 2: LANÇAMENTO RÁPIDO ---
with tab2:
    st.subheader("📝 Registrar Matrícula Automaticamente")
    texto_input = st.text_area("Cole o texto da matrícula aqui:", height=200)
    
    if st.button("🚀 Processar e Atualizar Planilha", type="primary"):
        if texto_input:
            try:
                # Extração via Regex
                consultor_raw = re.search(r"CONSULTOR RESPONSÁVEL:\s*(.*)", texto_input, re.IGNORECASE).group(1).strip()
                curso_raw = re.search(r"AREA DESEJADA:\s*(.*)", texto_input, re.IGNORECASE).group(1).strip()
                
                # Normalização para comparação
                cons_norm = remover_acentos(consultor_raw)
                curs_norm = remover_acentos(curso_raw)
                
                # Busca na planilha
                df_temp = df_dados.copy()
                df_temp['C_N'] = df_temp['Consultor'].apply(remover_acentos)
                df_temp['K_N'] = df_temp['Curso'].apply(remover_acentos)
                
                idx = df_temp[(df_temp['C_N'] == cons_norm) & (df_temp['K_N'] == curs_norm)].index
                
                if not idx.empty:
                    # Soma +1 na memória
                    df_dados.at[idx[0], mes_at] += 1
                    
                    # Salva no Google Sheets (
