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
st.set_page_config(page_title="Gestor F5", layout="wide", page_icon="🚀")

def remover_acentos(texto):
    if not isinstance(texto, str): return str(texto)
    texto_normalizado = unicodedata.normalize('NFD', texto)
    return "".join([c for c in texto_normalizado if unicodedata.category(c) != 'Mn']).upper().strip()

def get_mes_atual():
    meses_map = {4:'Abril', 5:'Maio', 6:'Junho', 7:'Julho', 8:'Agosto', 9:'Setembro'}
    return meses_map.get(datetime.now().month, 'Maio')

# =============================================================================
# CONEXÃO OTIMIZADA v1.9
# =============================================================================
try:
    # URL LIMPA: Removi o #gid=0 para evitar o erro 404 de conflito de aba
    URL_PLANILHA = "https://docs.google.com/spreadsheets/d/1tv9dTG6H-X_h2reOibL8KB99LIUM_YaR/edit?usp=sharing&ouid=115939420972517598197&rtpof=true&sd=true"
    NOME_ABA = "DADOS_MATRICULAS" 
    
    conn = st.connection("gsheets", type=GSheetsConnection)
    
    # Tentativa de leitura robusta
    df_dados = conn.read(spreadsheet=URL_PLANILHA, worksheet=NOME_ABA)
    
    # Conversão de colunas (Meses)
    MESES = ['Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro']
    for m in MESES:
        if m in df_dados.columns:
            df_dados[m] = pd.to_numeric(df_dados[m], errors='coerce').fillna(0)
            
except Exception as e:
    st.error(f"Erro de Conexão: {e}")
    st.info("Dica: No Google Sheets, clique em 'Compartilhar' e garanta que está como 'Qualquer pessoa com o link' pode ser 'Editor'.")
    st.stop()

# =============================================================================
# INTERFACE
# =============================================================================

st.title("🚀 Gestor de Metas F5")

tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "📝 Lançar", "🏆 Ranking"])

with tab1:
    # Verificação de segurança para as métricas
    if not df_dados.empty:
        total_geral = int(df_dados[MESES].sum().sum())
        mes_at = get_mes_atual()
        total_mes = int(df_dados[mes_at].sum()) if mes_at in df_dados.columns else 0
        
        c1, c2 = st.columns(2)
        c1.metric("Acumulado Geral", f"{total_geral} / 325")
        c2.metric(f"Total em {mes_at}", total_mes)

        st.subheader(f"Produção por Curso ({mes_at})")
        if 'Curso' in df_dados.columns:
            chart_data = df_dados.groupby('Curso')[mes_at].sum().sort_values()
            st.bar_chart(chart_data)

with tab2:
    st.subheader("Registrar Matrícula")
    texto_input = st.text_area("Cole o texto da matrícula aqui:", height=200)
    
    if st.button("🚀 Salvar na Planilha"):
        if texto_input:
            try:
                # Captura Consultor e Curso do texto colado
                m_cons = re.search(r"CONSULTOR RESPONSÁVEL:\s*(.*)", texto_input, re.IGNORECASE)
                m_curs = re.search(r"AREA DESEJADA:\s*(.*)", texto_input, re.IGNORECASE)
                
                if m_cons and m_curs:
                    consultor_raw = m_cons.group(1).strip()
                    curso_raw = m_curs.group(1).strip()
                    
                    cons_norm = remover_acentos(consultor_raw)
                    curs_norm = remover_acentos(curso_raw)
                    
                    # Preparação para busca
                    df_temp = df_dados.copy()
                    df_temp['C_N'] = df_temp['Consultor'].apply(remover_acentos)
                    df_temp['K_N'] = df_temp['Curso'].apply(remover_acentos)
                    
                    idx = df_temp[(df_temp['C_N'] == cons_norm) & (df_temp['K_N'] == curs_norm)].index
                    
                    if not idx.empty:
                        mes_at = get_mes_atual()
                        df_dados.at[idx[0], mes_at] += 1
                        
                        # Escrita de volta para o Google Sheets
                        conn.update(spreadsheet=URL_PLANILHA, worksheet=NOME_ABA, data=df_dados)
                        st.success(f"Matrícula de {curso_raw} lançada com sucesso!")
                        st.balloons()
                        st.rerun()
                    else:
                        st.error(f"Não encontramos '{consultor_raw}' no curso '{curso_raw}'.")
                else:
                    st.error("Campos obrigatórios não encontrados no texto.")
            except Exception as e:
                st.error(f"Erro ao processar: {e}")

with tab3:
    if 'Consultor' in df_dados.columns:
        ranking = df_dados.groupby('Consultor')[MESES].sum().sum(axis=1).sort_values(ascending=False).reset_index()
        ranking.columns = ['Consultor', 'Total Matrículas']
        st.table(ranking)
