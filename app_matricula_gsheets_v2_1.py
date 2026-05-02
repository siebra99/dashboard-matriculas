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

# CSS Customizado para cartões de métricas
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
    # Mapeamento de meses para a planilha
    meses_map = {4:'Abril', 5:'Maio', 6:'Junho', 7:'Julho', 8:'Agosto', 9:'Setembro'}
    return meses_map.get(datetime.now().month, 'Maio')

# =============================================================================
# CONEXÃO COM GOOGLE SHEETS
# =============================================================================
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    
    # AJUSTE DE SEGURANÇA: Limpa a URL de qualquer espaço invisível vindo dos Secrets
    url_planilha = st.secrets["connections"]["gsheets"]["spreadsheet"].strip()
    
    # Lendo os dados da aba específica
    df_dados = conn.read(spreadsheet=url_planilha, worksheet="DADOS MATRICULAS CONSULTOR")
    
    # Conversão de colunas de meses para numérico
    MESES = ['Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro']
    for m in MESES:
        if m in df_dados.columns:
            df_dados[m] = pd.to_numeric(df_dados[m], errors='coerce').fillna(0)
            
except Exception as e:
    st.error(f"Erro crítico de conexão: {e}")
    st.info("Dica: Verifique se a URL nos Secrets está correta e se o nome da aba no Google Sheets é 'DADOS MATRICULAS CONSULTOR'.")
    st.stop()

# =============================================================================
# INTERFACE DO USUÁRIO
# =============================================================================

st.title("🚀 Gestor de Metas F5 - Dashboard HTTPS")

tab1, tab2, tab3 = st.tabs(["📊 Dashboard Geral", "📝 Lançamento Rápido", "🏆 Ranking de Consultores"])

# --- TAB 1: DASHBOARD ---
with tab1:
    col1, col2, col3 = st.columns(3)
    
    total_geral = int(df_dados[MESES].sum().sum())
    mes_at = get_mes_atual()
    total_mes = int(df_dados[mes_at].sum())
    meta_objetivo = 325
    progresso = (total_geral / meta_objetivo) * 100
    
    col1.metric("Total Acumulado", f"{total_geral} / {meta_objetivo}")
    col2.metric(f"Matrículas em {mes_at}", total_mes)
    col3.metric("Progresso da Meta", f"{progresso:.1f}%")

    st.divider()
    
    st.subheader(f"📈 Produção Mensal ({mes_at})")
    chart_data = df_dados.groupby('Curso')[mes_at].sum().sort_values(ascending=True)
    st.bar_chart(chart_data)

# --- TAB 2: LANÇAMENTO RÁPIDO ---
with tab2:
    st.subheader("📝 Registrar Nova Matrícula")
    st.write("Cole o texto padrão da matrícula abaixo para atualizar a planilha automaticamente.")
    
    texto_input = st.text_area("Dados do Aluno:", height=200, help="Cole o texto que contém 'AREA DESEJADA' e 'CONSULTOR RESPONSÁVEL'")
    
    if st.button("🚀 Processar e Salvar", type="primary"):
        if texto_input:
            try:
                # Extração dos dados usando Regex
                consultor_raw = re.search(r"CONSULTOR RESPONSÁVEL:\s*(.*)", texto_input, re.IGNORECASE).group(1).strip()
                curso_raw = re.search(r"AREA DESEJADA:\s*(.*)", texto_input, re.IGNORECASE).group(1).strip()
                
                # Normalização para comparação (Remove acentos e espaços)
                cons_norm = remover_acentos(consultor_raw)
                curs_norm = remover_acentos(curso_raw)
                
                # Criar colunas temporárias de comparação no dataframe
                df_temp = df_dados.copy()
                df_temp['CONS_N'] = df_temp['Consultor'].apply(remover_acentos)
                df_temp['CURS_N'] = df_temp['Curso'].apply(remover_acentos)
                
                # Localizar a linha
                idx = df_temp[(df_temp['CONS_N'] == cons_norm) & (df_temp['CURS_N'] == curs_norm)].index
                
                if not idx.empty:
                    # Incrementa +1 no mês atual
                    df_dados.at[idx[0], mes_at] += 1
                    
                    # Salva a alteração no Google Sheets
                    conn.update(spreadsheet=url_planilha, worksheet="DADOS MATRICULAS CONSULTOR", data=df_dados)
                    
                    st.success(f"✅ Matrícula de {curso_raw} para o consultor {consultor_raw} registrada!")
                    st.balloons()
                    st.rerun() # Recarrega para atualizar os números do dashboard
                else:
                    st.error(f"❌ Não encontrado: Verifique se '{consultor_raw}' e '{curso_raw}' estão escritos corretamente na planilha.")
            
            except AttributeError:
                st.error
