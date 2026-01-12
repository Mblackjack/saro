#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Aplicação Web Streamlit - Sistema de Classificação de Denúncias MPRJ
"""

import streamlit as st
import json
from classificador_denuncias import ClassificadorDenuncias
from datetime import datetime

# Configurar página
st.set_page_config(
    page_title="MPRJ - Classificador de Denúncias",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS customizado
st.markdown("""
<style>
    .main {
        padding: 2rem;
    }
    .stButton > button {
        width: 100%;
        padding: 0.75rem;
        font-size: 1.1rem;
        font-weight: bold;
    }
    .resultado-box {
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .sucesso {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
    }
    .erro {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
    }
</style>
""", unsafe_allow_html=True)

# Inicializar session state
if 'classificador' not in st.session_state:
    st.session_state.classificador = ClassificadorDenuncias()

if 'resultado' not in st.session_state:
    st.session_state.resultado = None

if 'historico' not in st.session_state:
    st.session_state.historico = []

# Header
st.markdown("# ⚖️ Sistema de Classificação de Denúncias")
st.markdown("### Ministério Público do Rio de Janeiro (MPRJ)")
st.markdown("---")

# Sidebar
with st.sidebar:
    st.markdown("## 📋 Sobre o Sistema")
    st.info("""
    Este sistema classifica automaticamente denúncias recebidas, identificando:
    
    - ✅ Promotoria responsável
    - ✅ Tema da denúncia
    - ✅ Subtema específico
    - ✅ Empresa envolvida
    
    **Cobertura:** Todos os 92 municípios do RJ
    """)
    
    st.markdown("---")
    st.markdown("## 📊 Estatísticas")
    st.metric("Denúncias Processadas", len(st.session_state.historico))
    
    if st.button("🗑️ Limpar Histórico"):
        st.session_state.historico = []
        st.success("Histórico limpo!")

# Formulário principal
st.markdown("## 📝 Formulário de Denúncia")

col1, col2 = st.columns([1, 1])

with col1:
    endereco = st.text_input(
        "📍 Endereço da Denúncia",
        placeholder="Ex: Rua da Conceição, 123 - Centro, Niterói - RJ",
        help="Digite o endereço completo incluindo o município"
    )

with col2:
    st.markdown("### ")
    st.markdown("*Exemplo: Rua X, número - Bairro, Município - RJ*")

denuncia = st.text_area(
    "📝 Descrição da Denúncia",
    placeholder="Descreva detalhadamente o problema/denúncia...",
    height=150,
    help="Forneça o máximo de detalhes possível sobre a denúncia"
)

# Botão de processamento
col1, col2, col3 = st.columns([1, 1, 1])

with col2:
    processar = st.button("🔍 Processar Denúncia", use_container_width=True)

# Processar denúncia
if processar:
    if not endereco or not denuncia:
        st.error("❌ Por favor, preencha todos os campos!")
    else:
        with st.spinner("⏳ Processando denúncia..."):
            try:
                resultado = st.session_state.classificador.processar_denuncia(
                    endereco, denuncia
                )
                st.session_state.resultado = resultado
                
                # Adicionar ao histórico
                resultado_historico = resultado.copy()
                resultado_historico['timestamp'] = datetime.now().isoformat()
                st.session_state.historico.append(resultado_historico)
                
                st.success("✅ Denúncia processada com sucesso!")
            except Exception as e:
                st.error(f"❌ Erro ao processar: {str(e)}")

# Exibir resultado
if st.session_state.resultado:
    resultado = st.session_state.resultado
    
    st.markdown("---")
    st.markdown("## 📊 Resultado da Classificação")
    
    # Informações da denúncia
    with st.expander("📋 Informações da Denúncia", expanded=True):
        st.markdown(f"**Endereço:** {resultado['endereco']}")
        st.markdown(f"**Denúncia:** {resultado['denuncia']}")
    
    # Resultado principal
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("### 🏛️ Promotoria Responsável")
        if resultado['promotoria']:
            st.success(resultado['promotoria'])
            st.markdown(f"📧 **E-mail:** {resultado['email']}")
            st.markdown(f"📞 **Telefone:** {resultado['telefone']}")
        else:
            st.warning("Não foi possível identificar a promotoria")
    
    with col2:
        st.markdown("### 📂 Classificação")
        if resultado['tema']:
            st.info(f"**Tema:** {resultado['tema']}")
            st.info(f"**Subtema:** {resultado['subtema']}")
        else:
            st.warning("Não foi possível classificar a denúncia")
    
    # Empresa
    st.markdown("### 🏢 Empresa Envolvida")
    if resultado['empresa']:
        st.write(f"**{resultado['empresa']}**")
    else:
        st.info("Nenhuma empresa específica foi identificada")
    
    # Botões de ação
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        # Botão para copiar resultado
        resultado_json = json.dumps(resultado, ensure_ascii=False, indent=2)
        st.download_button(
            label="📥 Baixar Resultado (JSON)",
            data=resultado_json,
            file_name=f"denuncia_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )
    
    with col2:
        if st.button("🔄 Nova Denúncia"):
            st.session_state.resultado = None
            st.rerun()

# Histórico
if st.session_state.historico:
    st.markdown("---")
    st.markdown("## 📜 Histórico de Denúncias")
    
    with st.expander(f"Ver histórico ({len(st.session_state.historico)} denúncias)"):
        for i, item in enumerate(reversed(st.session_state.historico), 1):
            with st.container():
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    st.markdown(f"**{i}. {item.get('empresa', 'Empresa não identificada')}**")
                    st.caption(f"Tema: {item.get('tema', 'N/A')} | Subtema: {item.get('subtema', 'N/A')}")
                
                with col2:
                    st.caption(f"📍 {item.get('municipio', 'N/A')}")
                
                with col3:
                    if item.get('timestamp'):
                        st.caption(item['timestamp'][:10])
                
                st.divider()

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: gray; font-size: 0.9rem;">
    <p>Sistema de Classificação Automática de Denúncias - MPRJ</p>
    <p>Desenvolvido com IA para otimizar o processamento de denúncias</p>
    <p>© 2026 Ministério Público do Rio de Janeiro</p>
</div>
""", unsafe_allow_html=True)
