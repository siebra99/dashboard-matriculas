import streamlit as st
import pandas as pd
import numpy as np
import unicodedata
import re
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# =============================================================================
# CONFIGURAÇÕES DA PÁGINA E ESTILO
# =============================================================================
st.set_page_config(page_title="Gestor F5 - v2.1", layout="wide", page_icon="🚀")

def remover_acentos(texto):
    if not isinstance(texto, str): return str(texto)
    texto_normalizado = unicodedata.normalize('NFD', texto)
    return "".join([c for c in texto_normalizado if unicodedata.category(c) != 'Mn']).upper().strip()

def get_mes_atual():
    meses_map = {4:'Abril', 5:'Maio', 6:'Junho', 7:'Julho', 8:'Agosto', 9:'Setembro'}
    return meses_map.get(datetime.now().month, 'Maio')

# =============================================================================
# CONEXÃO RESILIENTE v2.1
# =============================================================================
try:
    ID_SHEET = "1tv9dTG6H-X_h2reOibL8KB99LIUM_YaR"
    # Nome da aba conforme seu arquivo BASE.xlsx
    NOME_ABA = "DADOS_MATRICULAS"
    
    # URL de exportação direta (Evita erro 404 da API)
    url_export = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/gviz/tq?tqx=out:csv&sheet={NOME_ABA}"
    
    # Lendo os dados via Pandas (Leitura ultra rápida e estável)
    df_dados = pd.read_csv(url_export)
    
    # Tratamento de Colunas
    MESES = ['Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro']
    for m in MESES:
        if m in df_dados.columns:
            df_dados[m] = pd.to_numeric(df_dados[m], errors='coerce').fillna(0)
            
except Exception as e:
    st.error(f"Erro ao carregar dados: {e}")
    st.info("Dica: Verifique se a aba no Google Sheets chama-se exatamente DADOS_MATRICULAS.")
    st.stop()

# =============================================================================
# INTERFACE DO USUÁRIO
# =============================================================================

st.title("🚀 Gestor de Metas F5 - Full Sync")

tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "📝 Lançar Matrícula", "🏆 Ranking"])

# --- TAB 1: DASHBOARD ---
with tab1:
    if not df_dados.empty:
        total_geral = int(df_dados[MESES].sum().sum())
        mes_at = get_mes_atual()
        total_mes = int(df_dados[mes_at].sum()) if mes_at in df_dados.columns else 0
        
        c1, c2 = st.columns(2)
        c1.metric("Acumulado Geral", f"{total_geral} / 325")
        c2.metric(f"Total em {mes_at}", total_mes)

        st.subheader(f"Produção por Curso ({mes_at})")
        col_curso = 'CURSO' if 'CURSO' in df_dados.columns else 'Curso'
        if col_curso in df_dados.columns:
            chart_data = df_dados.groupby(col_curso)[mes_at].sum().sort_values()
            st.bar_chart(chart_data)

# --- TAB 2: LANÇAMENTO (ESCRITA) ---
with tab2:
    st.subheader("Registrar Matrícula")
    texto_input = st.text_area("Cole o texto da matrícula aqui:", height=200)
    
    if st.button("🚀 Salvar na Planilha"):
        if texto_input:
            try:
                # Regex para extração
                m_cons = re.search(r"CONSULTOR RESPONSÁVEL:\s*(.*)", texto_input, re.IGNORECASE)
                m_curs = re.search(r"AREA DESEJADA:\s*(.*)", texto_input, re.IGNORECASE)
                
                if m_cons and m_curs:
                    cons_raw, curs_raw = m_cons.group(1).strip(), m_curs.group(1).strip()
                    cons_n, curs_n = remover_acentos(cons_raw), remover_acentos(curs_raw)
                    
                    df_temp = df_dados.copy()
                    col_c = 'CONSULTOR' if 'CONSULTOR' in df_dados.columns else 'Consultor'
                    col_k = 'CURSO' if 'CURSO' in df_dados.columns else 'Curso'
                    
                    df_temp['C_N'] = df_temp[col_c].apply(remover_acentos)
                    df_temp['K_N'] = df_temp[col_k].apply(remover_acentos)
                    
                    idx = df_temp[(df_temp['C_N'] == cons_n) & (df_temp['K_N'] == curs_n)].index
                    
                    if not idx.empty:
                        df_dados.at[idx[0], mes_at] += 1
                        
                        # Para a ESCRITA, usamos a conexão oficial (Certifique-se de que o Secrets está configurado)
                        conn = st.connection("gsheets", type=GSheetsConnection)
                        conn.update(spreadsheet=f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/edit", 
                                    worksheet=NOME_ABA, data=df_dados)
                        
                        st.success("✅ Matrícula salva com sucesso!")
                        st.balloons()
                        st.rerun()
                    else:
                        st.error("Consultor ou Curso não localizados.")
                else:
                    st.error("Formato de texto inválido.")
            except Exception as e:
                st.error(f"Erro na gravação: {e}")

# --- TAB 3: RANKING ---
with tab3:
    col_c = 'CONSULTOR' if 'CONSULTOR' in df_dados.columns else 'Consultor'
    ranking = df_dados.groupby(col_c)[MESES].sum().sum(axis=1).sort_values(ascending=False).reset_index()
    ranking.columns = ['Consultor', 'Total']
    st.table(ranking)
