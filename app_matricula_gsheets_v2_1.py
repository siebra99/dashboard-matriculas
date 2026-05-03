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
st.set_page_config(page_title="Gestor F5 - Full Analytics", layout="wide", page_icon="📊")

# Estilo CSS para melhorar a visualização (baseado no seu código original)
st.markdown("""
    <style>
    .main { background-color: #f0f2f6; }
    .stMetric { background-color: #ffffff; padding: 10px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

# =============================================================================
# FUNÇÕES DE APOIO
# =============================================================================

def remover_acentos(texto):
    if not isinstance(texto, str): return str(texto)
    texto_normalizado = unicodedata.normalize('NFD', texto)
    return "".join([c for c in texto_normalizado if unicodedata.category(c) != 'Mn']).upper().strip()

def get_mes_atual():
    meses_map = {4:'Abril', 5:'Maio', 6:'Junho', 7:'Julho', 8:'Agosto', 9:'Setembro'}
    return meses_map.get(datetime.now().month, 'Maio')

# =============================================================================
# CONEXÃO RESILIENTE (LEITURA VIA CSV EXPORT / ESCRITA VIA GSHEETS)
# =============================================================================
try:
    ID_SHEET = "1tv9dTG6H-X_h2reOibL8KB99LIUM_YaR"
    NOME_ABA = "DADOS_MATRICULAS"
    url_export = f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/gviz/tq?tqx=out:csv&sheet={NOME_ABA}"
    
    # Lendo os dados
    df_dados = pd.read_csv(url_export)
    
    # Tratamento de Colunas
    MESES = ['Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro']
    for m in MESES:
        if m in df_dados.columns:
            df_dados[m] = pd.to_numeric(df_dados[m], errors='coerce').fillna(0)
            
    # Identificando colunas de texto (Consultor/Curso) independente de maiúsculas
    col_c = next((c for c in df_dados.columns if c.upper() == 'CONSULTOR'), 'Consultor')
    col_k = next((c for c in df_dados.columns if c.upper() == 'CURSO'), 'Curso')
    
except Exception as e:
    st.error(f"Erro ao carregar banco de dados: {e}")
    st.stop()

# =============================================================================
# INTERFACE PRINCIPAL (REPRODUZINDO AS ABAS DO CÓDIGO ORIGINAL)
# =============================================================================

st.title("🚀 Sistema de Gestão de Metas - Faculdade 5 de Julho")
st.markdown(f"**Status:** Online 🟢 | **Mês de Referência:** {get_mes_atual()}")

# Abas baseadas no seu código v11_4
tabs = st.tabs(["📊 Visão Geral", "👤 Análise por Consultor", "📝 Lançamento Rápido", "🏆 Ranking & Metas"])

# --- TAB 1: VISÃO GERAL ---
with tabs[0]:
    total_geral = int(df_dados[MESES].sum().sum())
    meta_global = 325
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Matrículas Totais", total_geral)
    c2.metric("Meta Global", meta_global)
    c3.metric("Faltam", max(0, meta_global - total_geral))
    
    st.divider()
    
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.subheader("📈 Produção por Curso")
        prod_curso = df_dados.groupby(col_k)[MESES].sum().sum(axis=1).sort_values()
        st.bar_chart(prod_curso)
        
    with col_right:
        st.subheader("🍕 Distribuição Percentual")
        # Gráfico de pizza simulado com barras horizontais para melhor leitura no Streamlit
        st.write("Participação de cada curso no total:")
        st.dataframe(prod_curso.apply(lambda x: f"{(x/total_geral)*100:.1f}%" if total_geral > 0 else "0%"))

# --- TAB 2: ANÁLISE POR CONSULTOR ---
with tabs[1]:
    st.subheader("🔍 Filtro por Consultor")
    lista_consultores = sorted(df_dados[col_c].unique())
    escolha = st.selectbox("Selecione um consultor:", lista_consultores)
    
    if escolha:
        dados_con = df_dados[df_dados[col_c] == escolha]
        total_con = dados_con[MESES].sum().sum()
        
        st.write(f"### Desempenho de {escolha}")
        st.metric("Total Individual", int(total_con))
        
        st.write("**Detalhamento por Curso:**")
        st.table(dados_con[[col_k] + MESES])

# --- TAB 3: LANÇAMENTO RÁPIDO (COM A LÓGICA DE REGEX ATUALIZADA) ---
with tabs[2]:
    st.subheader("📝 Registrar Nova Matrícula")
    st.info("Cole abaixo o texto padrão (ex: NOME DO ALUNO..., AREA DESEJADA..., CONSULTOR...)")
    
    texto_input = st.text_area("Área de Colagem:", height=200)
    
    if st.button("Confirmar e Sincronizar"):
        if texto_input:
            try:
                # Extração
                m_cons = re.search(r"CONSULTOR RESPONSÁVEL:\s*(.*)", texto_input, re.IGNORECASE)
                m_curs = re.search(r"AREA DESEJADA:\s*(.*)", texto_input, re.IGNORECASE)
                
                if m_cons and m_curs:
                    cons_raw, curs_raw = m_cons.group(1).strip(), m_curs.group(1).strip()
                    cons_n, curs_n = remover_acentos(cons_raw), remover_acentos(curs_raw)
                    
                    # Busca
                    df_temp = df_dados.copy()
                    df_temp['BUSCA_C'] = df_temp[col_c].apply(remover_acentos)
                    df_temp['BUSCA_K'] = df_temp[col_k].apply(remover_acentos)
                    
                    idx = df_temp[(df_temp['BUSCA_C'] == cons_n) & (df_temp['BUSCA_K'] == curs_n)].index
                    
                    if not idx.empty:
                        mes_at = get_mes_atual()
                        df_dados.at[idx[0], mes_at] += 1
                        
                        # Escrita via GSheetsConnection
                        conn = st.connection("gsheets", type=GSheetsConnection)
                        conn.update(spreadsheet=f"https://docs.google.com/spreadsheets/d/{ID_SHEET}/edit", 
                                    worksheet=NOME_ABA, data=df_dados)
                        
                        st.success(f"✅ Lançamento realizado! {curs_raw} -> {cons_raw}")
                        st.balloons()
                        st.rerun()
                    else:
                        st.error(f"Erro: Não encontrei a combinação '{cons_raw}' + '{curs_raw}' na planilha.")
                else:
                    st.error("Campos obrigatórios (CONSULTOR/AREA) não encontrados.")
            except Exception as e:
                st.error(f"Erro técnico no lançamento: {e}")

# --- TAB 4: RANKING & METAS ---
with tabs[3]:
    st.subheader("🏆 Ranking Geral de Consultores")
    ranking = df_dados.groupby(col_c)[MESES].sum().sum(axis=1).sort_values(ascending=False).reset_index()
    ranking.columns = ['Consultor', 'Matrículas']
    
    # Adicionando visualização de barra no dataframe
    st.dataframe(ranking, use_container_width=True)
    
    st.subheader("📅 Evolução Mensal")
    evolucao = df_dados[MESES].sum()
    st.line_chart(evolucao)
