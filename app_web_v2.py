# -*- coding: utf-8 -*-
"""
SARO v5.2 - Sistema Automático de Registro de Ouvidorias
Interface Web com Streamlit - Layout de Resultados e Detalhes Ajustado
"""

import streamlit as st
import json
import os
from datetime import datetime
from classificador_denuncias import ClassificadorDenuncias

# Configuração da página
st.set_page_config(page_title="SARO - Sistema de Ouvidorias", layout="wide")

# ============ AJUSTE DE CAMINHOS ============
base_path = os.path.dirname(os.path.abspath(__file__))
historico_file = os.path.join(base_path, "historico_denuncias.json")

# CSS customizado
st.markdown("""
<style>
    .resumo-box {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid #1f77b4;
    }
    .tabela-container {
        max-height: 500px;
        overflow-y: auto;
        border: 1px solid #ddd;
        border-radius: 5px;
        padding: 10px;
        background-color: white;
    }
    .modal-container {
        background-color: #f9f9f9;
        border: 2px solid #1f77b4;
        border-radius: 8px;
        padding: 20px;
        margin-top: 20px;
    }
</style>
""", unsafe_allow_html=True)

# Inicializar estado da sessão
if "resultado" not in st.session_state:
    st.session_state.resultado = None
if "historico" not in st.session_state:
    st.session_state.historico = []
if "visualizando_registro" not in st.session_state:
    st.session_state.visualizando_registro = None

# Carregar histórico do arquivo
if os.path.exists(historico_file):
    try:
        with open(historico_file, 'r', encoding='utf-8') as f:
            st.session_state.historico = json.load(f)
    except Exception:
        st.session_state.historico = []

# Cabeçalho
st.title("⚖️ SARO - Sistema Automático de Registro de Ouvidorias")
st.markdown("**Versão 5.2** | Classificação automática de denúncias e encaminhamento para promotorias do MPRJ")
st.divider()

# Inicializar classificador
try:
    classificador = ClassificadorDenuncias()
except Exception as e:
    st.error(f"Erro ao carregar classificador: {e}")
    st.stop()

# ============ 1. FORMULÁRIO DE OUVIDORIA ============
with st.form("form_ouvidoria", clear_on_submit=True):
    st.markdown("### 📝 Formulário de Ouvidoria")
    
    col1, col2 = st.columns(2)
    with col1:
        num_comunicacao = st.text_input("Nº de Comunicação", placeholder="Ex: 123/2024")
    with col2:
        num_mprj = st.text_input("Nº MPRJ", placeholder="Ex: 2024.001.002")
        
    endereco = st.text_input("Endereço da Denúncia", placeholder="Rua, Número, Bairro, Cidade - RJ")
    denuncia = st.text_area("Descrição da Ouvidoria", placeholder="Descreva aqui o teor da denúncia...")
    
    col1, col2 = st.columns(2)
    with col1:
        responsavel = st.radio("Enviado por:", options=["Elias", "Matheus", "Ana Beatriz", "Sônia", "Priscila"], horizontal=True)
    with col2:
        consumidor_vencedor = st.radio("Consumidor vencedor?", options=["Sim", "Não"], horizontal=True)
        
    submit = st.form_submit_button("🔍 Processar Ouvidoria", use_container_width=True, type="primary")

if submit:
    if not endereco or not denuncia:
        st.error("❌ Preencha os campos obrigatórios!")
    else:
        with st.spinner("IA Processando..."):
            try:
                resultado = classificador.processar_denuncia(endereco, denuncia, num_comunicacao, num_mprj)
                resultado.update({
                    "responsavel": responsavel,
                    "consumidor_vencedor": consumidor_vencedor,
                    "data": datetime.now().strftime("%d/%m/%Y %H:%M")
                })
                st.session_state.resultado = resultado
                st.session_state.historico.append(resultado)
                with open(historico_file, 'w', encoding='utf-8') as f:
                    json.dump(st.session_state.historico, f, ensure_ascii=False, indent=2)
                st.success("✅ Processado com sucesso!")
            except Exception as e:
                st.error(f"Erro: {e}")

st.divider()

# ============ 2. RESULTADO DA CLASSIFICAÇÃO (Imediato após envio) ============
if st.session_state.resultado:
    res = st.session_state.resultado
    st.markdown("### ✅ Resultado da Classificação")
    
    # Linha 1: Números e Identificação
    col1, col2 = st.columns(2)
    with col1:
        st.info(f"**Nº Comunicação:** {res['num_comunicacao']}")
    with col2:
        st.info(f"**Nº MPRJ:** {res['num_mprj']}")
    
    # Linha 2: Promotoria Responsável
    st.info(f"**Promotoria Responsável:** {res['promotoria']}")
    st.markdown(f"📧 **E-mail:** {res['email']} | 📞 **Telefone:** {res['telefone']}")
    
    # Linha 3: Classificação
    col1, col2, col3 = st.columns(3)
    with col1:
        st.success(f"**Tema:** {res['tema']}")
    with col2:
        st.success(f"**Subtema:** {res['subtema']}")
    with col3:
