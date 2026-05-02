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
st.set_page_config(page_title="Gestor de Metas F5 - Nuvem", layout="wide", page_icon="🚀")

# CSS Customizado
st.markdown("""
    <style>
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .sucesso-card { padding: 20px; border-radius: 10px; background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
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
    # Mapeamento conforme sua Matriz de Metas
    meses_map = {4:'Abril', 5:'Maio', 6:'Junho', 7:'Julho', 8:'Agosto', 9:'Setembro'}
    return meses_map.get(datetime.now().month, 'Maio')

# =============================================================================
# CONEXÃO COM GOOGLE SHEETS (OPÇÃO B)
# =============================================================================
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    # O Streamlit buscará a URL nos 'Secrets' que configuramos
    df_dados = conn.read(worksheet="DADOS MATRICULAS CONSULTOR")
    
    # Limpeza básica de dados da planilha
    MESES = ['Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro']
    for m in MESES:
        if m in df_dados.columns:
            df_dados[m] = pd.to_numeric(df_dados[m], errors='coerce').fillna(0)
except Exception as e:
    st.error(f"Erro ao conectar com Google Sheets: {e}")
    st.stop()

# =============================================================================
# LÓGICA DE INTERFACE
# =============================================================================

st.title("🚀 Gestor de Metas F5 - Dashboard HTTPS")

tab1, tab2, tab3 = st.tabs(["📊 Dashboard Real-time", "📝 Lançamento Rápido", "🏆 Rankings"])

# TAB 1: DASHBOARD
with tab1:
    total_geral = int(df_dados[MESES].sum().sum())
    mes_at = get_mes_atual()
    total_mes = int(df_dados[mes_at].sum())
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Geral (Acumulado)", total_geral)
    col2.metric(f"Total em {mes_at}", total_mes)
    col3.metric("Meta Global 2026", "325")

    st.subheader("📈 Desempenho por Curso")
    chart_data = df_dados.groupby('Curso')[MESES].sum().sum(axis=1).sort_values()
    st.bar_chart(chart_data)

# TAB 2: LANÇAMENTO RÁPIDO (A MÁGICA DO PASSO 4)
with tab2:
    st.subheader("📝 Registrar Nova Matrícula")
    texto_input = st.text_area("Cole aqui os dados do aluno:", height=200, placeholder="NOME DO ALUNO: ...\nAREA DESEJADA: ...\nCONSULTOR RESPONSÁVEL: ...")
    
    if st.button("Confirmar Lançamento", type="primary"):
        if texto_input:
            try:
                # Extração via Regex (Padrão F5)
                consultor_raw = re.search(r"CONSULTOR RESPONSÁVEL:\s*(.*)", texto_input, re.IGNORECASE).group(1).strip()
                curso_raw = re.search(r"AREA DESEJADA:\s*(.*)", texto_input, re.IGNORECASE).group(1).strip()
                
                # Normalização
                cons_norm = remover_acentos(consultor_raw)
                curs_norm = remover_acentos(curso_raw)
                
                # Busca na Planilha
                df_temp = df_dados.copy()
                df_temp['C_NORM'] = df_temp['Consultor'].apply(remover_acentos)
                df_temp['K_NORM'] = df_temp['Curso'].apply(remover_acentos)
                
                idx = df_temp[(df_temp['C_NORM'] == cons_norm) & (df_temp['K_NORM'] == curs_norm)].index
                
                if not idx.empty:
                    # Atualiza o DataFrame na memória
                    df_dados.at[idx[0], mes_at] += 1
                    
                    # ENVIO PARA O GOOGLE SHEETS
                    conn.update(worksheet="DADOS MATRICULAS CONSULTOR", data=df_dados)
                    
                    st.success(f"Matrícula processada! +1 para {consultor_raw} em {curso_raw} ({mes_at})")
                    st.balloons()
                    st.rerun() # Atualiza o dashboard
                else:
                    st.error(f"Não encontramos '{consultor_raw}' no curso '{curso_raw}' na planilha mestra.")
            except Exception as e:
                st.error("Não foi possível ler os campos. Verifique se o texto colado segue o padrão.")
        else:
            st.warning("O campo de texto está vazio.")

# TAB 3: RANKINGS
with tab3:
    st.subheader("🏆 Melhores Consultores")
    ranking = df_dados.groupby('Consultor')[MESES].sum().sum(axis=1).sort_values(ascending=False)
    st.dataframe(ranking, use_container_width=True)
