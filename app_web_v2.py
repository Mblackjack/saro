# -*- coding: utf-8 -*-
"""
SARO v5.2 - Sistema Automático de Registro de Ouvidorias
Interface Web com Streamlit - Visualização de Detalhes no Rodapé
"""

import streamlit as st
import json
import os
from datetime import datetime

# Configuração da página (deve ser a primeira chamada Streamlit)
st.set_page_config(page_title="SARO - Sistema de Ouvidorias", layout="wide")

# ============ AJUSTE DE CAMINHOS DINÂMICOS ============
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

# CARREGAMENTO SEGURO DO HISTÓRICO
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

# INICIALIZAÇÃO SEGURA DO CLASSIFICADOR
try:
    from classificador_denuncias import ClassificadorDenuncias
    classificador = ClassificadorDenuncias()
except Exception as e:
    st.error("⚠️ Erro ao inicializar o Classificador de IA.")
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
    denuncia = st.text_area("Descrição da Ouvidoria", placeholder="Descreva aqui o teor da denúncia recebida...")
    
    col1, col2 = st.columns(2)
    with col1:
        responsavel = st.radio("Enviado por:", options=["Elias", "Matheus", "Ana Beatriz", "Sônia", "Priscila"], horizontal=True)
    with col2:
        consumidor_vencedor = st.radio("É consumidor vencedor?", options=["Sim", "Não"], horizontal=True)
        
    submit = st.form_submit_button("🔍 Processar Ouvidoria", use_container_width=True, type="primary")

if submit:
    if not endereco or not denuncia:
        st.error("❌ Por favor, preencha o Endereço e a Descrição!")
    else:
        with st.spinner("IA Processando..."):
            try:
                resultado = classificador.processar_denuncia(endereco, denuncia, num_comunicacao, num_mprj)
                resultado["responsavel"] = responsavel
                resultado["consumidor_vencedor"] = consumidor_vencedor
                resultado["data"] = datetime.now().strftime("%d/%m/%Y %H:%M")
                
                st.session_state.resultado = resultado
                st.session_state.historico.append(resultado)
                
                with open(historico_file, 'w', encoding='utf-8') as f:
                    json.dump(st.session_state.historico, f, ensure_ascii=False, indent=2)
                
                st.success("✅ Ouvidoria processada!")
            except Exception as e:
                st.error(f"Erro ao processar: {e}")

# ============ 2. RESULTADO DA ÚLTIMA CLASSIFICAÇÃO ============
if st.session_state.resultado:
    res = st.session_state.resultado
    with st.expander("✨ Ver Resultado da Última Classificação", expanded=True):
        st.write(f"**Empresa:** {res['empresa']} | **Tema:** {res['tema']} | **Subtema:** {res['subtema']}")
        st.info(f"**Resumo:** {res['resumo']}")

st.divider()

# ============ 3. REGISTRO DE OUVIDORIAS (TABELA HISTÓRICA) ============
st.markdown("### 📊 Registro de Ouvidorias")

if not st.session_state.historico:
    st.info("Nenhuma ouvidoria registrada ainda.")
else:
    # Filtros e Busca
    c1, c2 = st.columns([3, 1])
    search = c1.text_input("🔍 Buscar no histórico")
    filtro_tema = c2.selectbox("Filtrar por Tema", ["Todos"] + sorted(list(set(h['tema'] for h in st.session_state.historico))))

    dados_filtrados = st.session_state.historico
    if search:
        s = search.lower()
        dados_filtrados = [h for h in dados_filtrados if s in str(h).lower()]
    if filtro_tema != "Todos":
        dados_filtrados = [h for h in dados_filtrados if h['tema'] == filtro_tema]

    # Renderização da Tabela
    st.markdown('<div class="tabela-container">', unsafe_allow_html=True)
    cols = st.columns([1.5, 1.5, 1.5, 2, 1.5, 1, 1])
    cols[0].write("**Nº Com.**"); cols[1].write("**Data**"); cols[2].write("**Empresa**")
    cols[3].write("**Promotoria**"); cols[4].write("**Responsável**"); cols[5].write("**Ver**"); cols[6].write("**Apagar**")
    st.divider()

    for registro in reversed(dados_filtrados):
        idx_original = st.session_state.historico.index(registro)
        c = st.columns([1.5, 1.5, 1.5, 2, 1.5, 1, 1])
        c[0].write(registro.get('num_comunicacao', 'N/A'))
        c[1].write(registro.get('data', 'N/A'))
        c[2].write(registro.get('empresa', 'N/A'))
        c[3].write(registro.get('promotoria', 'N/A'))
        c[4].write(registro.get('responsavel', 'N/A'))
        
        if c[5].button("👁️", key=f"v_{idx_original}"):
            st.session_state.visualizando_registro = registro
            st.rerun()
            
        if c[6].button("🗑️", key=f"d_{idx_original}"):
            st.session_state.historico.pop(idx_original)
            with open(historico_file, 'w', encoding='utf-8') as f:
                json.dump(st.session_state.historico, f, ensure_ascii=False, indent=2)
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# ============ 4. DETALHES DA OUVIDORIA (AGORA NO FINAL) ============
if st.session_state.visualizando_registro is not None:
    st.divider()
    reg = st.session_state.visualizando_registro
    st.markdown("### 🔍 Detalhes da Ouvidoria Selecionada")
    
    st.markdown('<div class="modal-container">', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    col1.markdown(f"**Nº Comunicação:** {reg.get('num_comunicacao')}")
    col2.markdown(f"**Nº MPRJ:** {reg.get('num_mprj')}")
    col3.markdown(f"**Data:** {reg.get('data')}")
    
    st.markdown(f"**Endereço:** {reg.get('endereco')}")
    st.markdown(f"**Promotoria:** {reg.get('promotoria')} ({reg.get('municipio')})")
    st.markdown(f"**Tema:** {reg.get('tema')} | **Subtema:** {reg.get('subtema')} | **Empresa:** {reg.get('empresa')}")
    
    st.markdown("**Resumo:**")
    st.info(reg.get('resumo'))
    
    with st.expander("Ver Descrição Completa"):
        st.write(reg.get('denuncia'))
        
    if st.button("❌ Fechar Detalhes"):
        st.session_state.visualizando_registro = None
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

st.divider()
st.caption("SARO - Sistema Automático de Registro de Ouvidorias | MPRJ")
