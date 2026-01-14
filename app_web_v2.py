# -*- coding: utf-8 -*-
"""
SARO v5.2 - Sistema Automático de Registro de Ouvidorias
Interface Web com Streamlit - Correção de Indentação
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

# Carregar histórico
if os.path.exists(historico_file):
    try:
        with open(historico_file, 'r', encoding='utf-8') as f:
            st.session_state.historico = json.load(f)
    except Exception:
        st.session_state.historico = []

# Cabeçalho
st.title("⚖️ SARO - Sistema Automático de Registro de Ouvidorias")
st.markdown("**Versão 5.2** | Classificação automática de denúncias")
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

# ============ 2. RESULTADO DA CLASSIFICAÇÃO ============
if st.session_state.resultado:
    res = st.session_state.resultado
    st.markdown("### ✅ Resultado da Classificação")
    
    col1, col2 = st.columns(2)
    with col1:
        st.info(f"**Nº Comunicação:** {res['num_comunicacao']}")
    with col2:
        st.info(f"**Nº MPRJ:** {res['num_mprj']}")
    
    st.info(f"**Promotoria Responsável:** {res['promotoria']}")
    st.markdown(f"📧 **E-mail:** {res['email']} | 📞 **Telefone:** {res['telefone']}")
    
    c1, c2, c3 = st.columns(3)
    with c1:
        st.success(f"**Tema:** {res['tema']}")
    with c2:
        st.success(f"**Subtema:** {res['subtema']}")
    with c3:
        st.success(f"**Empresa:** {res['empresa']}")
        
    st.markdown("**Resumo da Ouvidoria:**")
    st.markdown(f'<div class="resumo-box">{res["resumo"]}</div>', unsafe_allow_html=True)
    
    if st.button("➕ Nova Ouvidoria", use_container_width=True):
        st.session_state.resultado = None
        st.rerun()

st.divider()

# ============ 3. REGISTRO DE OUVIDORIAS (TABELA) ============
st.markdown("### 📊 Registro de Ouvidorias")

if not st.session_state.historico:
    st.info("Nenhuma ouvidoria registrada.")
else:
    c1, c2 = st.columns([3, 1])
    search = c1.text_input("🔍 Buscar no histórico")
    filtro_tema = c2.selectbox("Filtrar Tema", ["Todos"] + sorted(list(set(h['tema'] for h in st.session_state.historico))))

    dados = st.session_state.historico
    if search:
        s = search.lower()
        dados = [h for h in dados if s in str(h).lower()]
    if filtro_tema != "Todos":
        dados = [h for h in dados if h['tema'] == filtro_tema]

    st.markdown('<div class="tabela-container">', unsafe_allow_html=True)
    cols = st.columns([1.5, 1.5, 1.5, 2, 1.5, 1, 1])
    cols[0].write("**Nº Com.**"); cols[1].write("**Data**"); cols[2].write("**Empresa**")
    cols[3].write("**Promotoria**"); cols[4].write("**Responsável**"); cols[5].write("**Ver**"); cols[6].write("**Apagar**")
    st.divider()

    for registro in reversed(dados):
        idx_orig = st.session_state.historico.index(registro)
        c = st.columns([1.5, 1.5, 1.5, 2, 1.5, 1, 1])
        c[0].write(registro['num_comunicacao'])
        c[1].write(registro['data'])
        c[2].write(registro['empresa'])
        c[3].write(registro['promotoria'])
        c[4].write(registro['responsavel'])
        
        if c[5].button("👁️", key=f"v_{idx_orig}"):
            st.session_state.visualizando_registro = registro
            st.rerun()
        if c[6].button("🗑️", key=f"d_{idx_orig}"):
            st.session_state.historico.pop(idx_orig)
            with open(historico_file, 'w', encoding='utf-8') as f:
                json.dump(st.session_state.historico, f, ensure_ascii=False, indent=2)
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# ============ 4. DETALHES (ABAIXO DA TABELA) ============
if st.session_state.visualizando_registro is not None:
    st.divider()
    reg = st.session_state.visualizando_registro
    st.markdown("### 📋 Detalhes da Ouvidoria")
    
    st.markdown('<div class="modal-container">', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"**Nº Comunicação:** {reg.get('num_comunicacao')}")
    with col2:
        st.markdown(f"**Nº MPRJ:** {reg.get('num_mprj')}")
    with col3:
        st.markdown(f"**Data:** {reg.get('data')}")
    
    st.markdown(f"**Endereço:** {reg.get('endereco')}")
    st.markdown(f"**Promotoria:** {reg.get('promotoria')} | **Município:** {reg.get('municipio')}")
    st.markdown(f"**Tema:** {reg.get('tema')} | **Subtema:** {reg.get('subtema')} | **Empresa:** {reg.get('empresa')}")
    
    st.info(f"**Resumo:** {reg.get('resumo')}")
    with st.expander("Ver Descrição Completa"):
        st.write(reg.get('denuncia'))
        
    if st.button("❌ Fechar Visualização"):
        st.session_state.visualizando_registro = None
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

st.divider()
st.caption("SARO - Sistema Automático de Registro de Ouvidorias | MPRJ")
