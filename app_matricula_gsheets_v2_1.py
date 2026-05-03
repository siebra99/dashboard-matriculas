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
st.set_page_config(page_title="Gestor F5 - v2.0", layout="wide", page_icon="🚀")

def remover_acentos(texto):
    if not isinstance(texto, str): return str(texto)
    texto_normalizado = unicodedata.normalize('NFD', texto)
    return "".join([c for c in texto_normalizado if unicodedata.category(c) != 'Mn']).upper().strip()

def get_mes_atual():
    meses_map = {4:'Abril', 5:'Maio', 6:'Junho', 7:'Julho', 8:'Agosto', 9:'Setembro'}
    return meses_map.get(datetime.now().month, 'Maio')

# =============================================================================
# CONEXÃO OTIMIZADA v2.0 (SEM ERRO 404)
# =============================================================================
try:
    # Usando apenas o ID fundamental da planilha para evitar erro 404
    ID_PLANILHA = "1tv9dTG6H-X_h2reOibL8KB99LIUM_YaR"
    URL_LIMPA = f"https://docs.google.com/spreadsheets/d/{ID_PLANILHA}/edit"
    NOME_ABA = "DADOS_MATRICULAS" 
    
    conn = st.connection("gsheets", type=GSheetsConnection)
    
    # Leitura forçando o uso da URL limpa
    df_dados = conn.read(spreadsheet=URL_LIMPA, worksheet=NOME_ABA)
    
    # Validação de colunas baseada no seu arquivo BASE.xlsx
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

tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "📝 Lançar Matrícula", "🏆 Ranking"])

with tab1:
    if not df_dados.empty:
        total_geral = int(df_dados[MESES].sum().sum())
        mes_at = get_mes_atual()
        total_mes = int(df_dados[mes_at].sum()) if mes_at in df_dados.columns else 0
        
        c1, c2 = st.columns(2)
        c1.metric("Acumulado Geral", f"{total_geral} / 325")
        c2.metric(f"Total em {mes_at}", total_mes)

        st.subheader(f"Produção por Curso ({mes_at})")
        if 'CURSOR' in df_dados.columns or 'CURSO' in df_dados.columns:
            col_curso = 'CURSO' if 'CURSO' in df_dados.columns else 'CURSOR'
            chart_data = df_dados.groupby(col_curso)[mes_at].sum().sort_values()
            st.bar_chart(chart_data)

with tab2:
    st.subheader("Registrar Matrícula")
    texto_input = st.text_area("Cole o texto da matrícula aqui:", height=200)
    
    if st.button("🚀 Salvar na Planilha"):
        if texto_input:
            try:
                # Regex adaptado para o seu padrão de mensagens
                m_cons = re.search(r"CONSULTOR RESPONSÁVEL:\s*(.*)", texto_input, re.IGNORECASE)
                m_curs = re.search(r"AREA DESEJADA:\s*(.*)", texto_input, re.IGNORECASE)
                
                if m_cons and m_curs:
                    consultor_raw = m_cons.group(1).strip()
                    curso_raw = m_curs.group(1).strip()
                    
                    cons_norm = remover_acentos(consultor_raw)
                    curs_norm = remover_acentos(curso_raw)
                    
                    df_temp = df_dados.copy()
                    # Identifica as colunas Consultor/Curso independente de estarem em maiúsculo
                    col_cons = 'CONSULTOR' if 'CONSULTOR' in df_dados.columns else 'Consultor'
                    col_cur = 'CURSO' if 'CURSO' in df_dados.columns else 'Curso'
                    
                    df_temp['C_N'] = df_temp[col_cons].apply(remover_acentos)
                    df_temp['K_N'] = df_temp[col_cur].apply(remover_acentos)
                    
                    idx = df_temp[(df_temp['C_N'] == cons_norm) & (df_temp['K_N'] == curs_norm)].index
                    
                    if not idx.empty:
                        df_dados.at[idx[0], mes_at] += 1
                        conn.update(spreadsheet=URL_LIMPA, worksheet=NOME_ABA, data=df_dados)
                        st.success(f"Matrícula de {curso_raw} lançada!")
                        st.balloons()
                        st.rerun()
                    else:
                        st.error(f"Não localizado: {consultor_raw} / {curso_raw}")
                else:
                    st.error("Campos não encontrados no texto colado.")
            except Exception as e:
                st.error(f"Erro: {e}")

with tab3:
    col_cons = 'CONSULTOR' if 'CONSULTOR' in df_dados.columns else 'Consultor'
    ranking = df_dados.groupby(col_cons)[MESES].sum().sum(axis=1).sort_values(ascending=False).reset_index()
    ranking.columns = ['Consultor', 'Total']
    st.table(ranking)
