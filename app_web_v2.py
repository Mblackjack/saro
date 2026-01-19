# -*- coding: utf-8 -*-
"""
SARO v6.2 - Sistema Automático de Registro de Ouvidorias
Versão Final Corrigida - Identidade Visual MPRJ (#960018)
"""

import streamlit as st
import json
import os
import pandas as pd  # Adicionado para suporte ao Excel
from datetime import datetime
from classificador_denuncias import ClassificadorDenuncias

# Configuração da página
st.set_page_config(page_title="SARO - Sistema de Ouvidorias", layout="wide")

# ============ AJUSTE DE CAMINHOS ============
base_path = os.path.dirname(os.path.abspath(__file__))
historico_file = os.path.join(base_path, "historico_denuncias.json")
excel_file = os.path.join(base_path, "registros_ouvidoria.xlsx") # Caminho do Excel

# CSS customizado com a cor institucional #960018
st.markdown(f"""
<style>
    .resumo-box {{
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 8px;
        border-left: 5px solid #960018;
    }}
    .titulo-sessao {{
        color: #960018;
        font-weight: bold;
        font-size: 1.2rem;
        margin-bottom: 15px;
        margin-top: 10px;
    }}
    .box-destaque {{
        border: 1px solid #960018;
        padding: 15px;
        border-radius: 10px;
        border-left: 10px solid #960018;
        margin-bottom: 20px;
        background-color: white;
    }}
    .tabela-horizontal {{
        overflow-x: auto;
        width: 100%;
        border: 1px solid #e6e9ef;
        border-radius: 8px;
        background-color: white;
    }}
    div.stButton > button:first-child {{
        background-color: #960018 !important;
        color: white !important;
        border: none;
    }}
    .header-text {{
        font-weight: bold;
        color: #333;
        font-size: 0.9rem;
    }}
</style>
""", unsafe_allow_html=True)

# Inicializar estado da sessão
if "resultado" not in st.session_state:
    st.session_state.resultado = None
if "historico" not in st.session_state:
    st.session_state.historico = []

# Carregar histórico JSON
if os.path.exists(historico_file):
    try:
        with open(historico_file, 'r', encoding='utf-8') as f:
            st.session_state.historico = json.load(f)
    except Exception:
        st.session_state.historico = []

# Cabeçalho
st.title("⚖️ Sistema Automático de Registro de Ouvidorias (SARO)")
st.markdown("**Versão 1.0** | Registro e Gestão de Ouvidorias com auxílio de Inteligência Artificial")
st.divider()

# ============ BARRA LATERAL (LINK EXCEL) ============
st.sidebar.image("https://www.mprj.mp.br/mprj-theme/images/mprj/logo_mprj.png", width=200) # Opcional: Logo MPRJ
st.sidebar.markdown('<p class="titulo-sessao">📊 Exportar Dados</p>', unsafe_allow_html=True)

if os.path.exists(excel_file):
    with open(excel_file, "rb") as f:
        st.sidebar.download_button(
            label="📥 Baixar Base Excel Completa",
            data=f,
            file_name=f"Relatorio_SARO_{datetime.now().strftime('%d_%m_%Y')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            help="Clique aqui para baixar todos os registros salvos em formato Excel."
        )
    st.sidebar.success("Arquivo pronto para download!")
else:
    st.sidebar.info("Aguardando o primeiro registro para gerar o Excel.")

# Inicializar classificador
try:
    classificador = ClassificadorDenuncias()
except Exception as e:
    st.error(f"Erro ao carregar classificador: {e}")
    st.stop()

# ============ 1. FORMULÁRIO DE OUVIDORIA ============
with st.form("form_ouvidoria", clear_on_submit=True):
    st.markdown('<p class="titulo-sessao">📝 Novo Registro de Ouvidoria</p>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        num_comunicacao = st.text_input("Nº de Comunicação", placeholder="Ex: 123/2024")
    with col2:
        num_mprj = st.text_input("Nº MPRJ", placeholder="Ex: 2024.001.002")
        
    endereco = st.text_input("Endereço da Denúncia", placeholder="Rua, Número, Bairro, Cidade - RJ")
    denuncia = st.text_area("Descrição da Ouvidoria", placeholder="Descreva aqui o teor da denúncia...")
    
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        responsavel = st.radio("Enviado por:", options=["Elias", "Matheus", "Ana Beatriz", "Sônia", "Priscila"], horizontal=True)
    with col_f2:
        consumidor_vencedor = st.radio("Consumidor vencedor?", options=["Sim", "Não"], horizontal=True)
        
    submit = st.form_submit_button("🔍 Registre a Ouvidoria", use_container_width=True)

if submit:
    if not endereco or not denuncia:
        st.error("❌ Preencha os campos obrigatórios (Endereço e Descrição)!")
    else:
        with st.spinner("IA Processando e salvando no Excel..."):
            try:
                # O método processar_denuncia já deve conter a lógica de salvar_no_excel()
                resultado = classificador.processar_denuncia(endereco, denuncia, num_comunicacao, num_mprj)
                
                # Adicionar campos extras que são específicos da UI do app.py
                resultado.update({
                    "responsavel": responsavel,
                    "consumidor_vencedor": consumidor_vencedor,
                    "data_envio": datetime.now().strftime("%d/%m/%Y %H:%M")
                })
                
                # Atualizar histórico JSON
                st.session_state.resultado = resultado
                st.session_state.historico.append(resultado)
                with open(historico_file, 'w', encoding='utf-8') as f:
                    json.dump(st.session_state.historico, f, ensure_ascii=False, indent=2)
                
                st.success("✅ Denúncia processada, salva no histórico e registrada no Excel!")
                st.rerun() # Recarrega para o botão de download do Excel atualizar
            except Exception as e:
                st.error(f"Erro no processamento: {e}")

# ... (Restante do código de exibição de resultados e histórico permanece igual) ...
