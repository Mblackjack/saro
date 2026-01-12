# -*- coding: utf-8 -*-
"""
SARO v5.1 - Sistema Automático de Registro de Ouvidorias
Interface Web com Streamlit - Versão Otimizada com Visualização Enxuta
"""

import streamlit as st
import json
import os
from datetime import datetime

# Configuração da página (deve ser a primeira chamada Streamlit)
st.set_page_config(page_title="SARO - Sistema de Ouvidorias", layout="wide")

# ============ AJUSTE DE CAMINHOS DINÂMICOS ============
# Isso resolve o FileNotFoundError no Streamlit Cloud
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
    .resultado-box {
        background-color: #e8f4f8;
        padding: 15px;
        border-radius: 8px;
        margin: 10px 0;
    }
    .tabela-container {
        max-height: 700px;
        overflow-y: auto;
        overflow-x: auto;
        border: 1px solid #ddd;
        border-radius: 5px;
        padding: 10px;
    }
    .modal-container {
        background-color: #f9f9f9;
        border: 2px solid #1f77b4;
        border-radius: 8px;
        padding: 20px;
        margin: 20px 0;
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
st.markdown("**Versão 5.1** | Classificação automática de denúncias e encaminhamento para promotorias do MPRJ")
st.divider()

# INICIALIZAÇÃO SEGURA DO CLASSIFICADOR
try:
    from classificador_denuncias import ClassificadorDenuncias
    classificador = ClassificadorDenuncias()
except Exception as e:
    st.error("⚠️ Erro ao inicializar o Classificador de IA.")
    st.info("Verifique se a chave OPENAI_API_KEY está configurada nos 'Secrets' do Streamlit.")
    st.stop()

# ============ VISUALIZAÇÃO ENXUTA DE REGISTRO (MODAL) ============
if st.session_state.visualizando_registro is not None:
    registro = st.session_state.visualizando_registro
    
    st.markdown("### 📋 Detalhes da Ouvidoria")
    
    with st.container():
        st.markdown('<div class="modal-container">', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"**Nº Comunicação:** {registro.get('num_comunicacao', 'N/A')}")
        with col2:
            st.markdown(f"**Nº MPRJ:** {registro.get('num_mprj', 'N/A')}")
        with col3:
            st.markdown(f"**Data:** {registro.get('data', 'N/A')}")
            
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**Responsável pelo Envio:** {registro.get('responsavel', 'N/A')}")
        with col2:
            st.markdown(f"**Consumidor Vencedor:** {registro.get('consumidor_vencedor', 'N/A')}")
            
        st.markdown(f"**Endereço:** {registro.get('endereco', 'N/A')}")
        st.markdown(f"**Município:** {registro.get('municipio', 'N/A')}")
        st.markdown(f"**Promotoria:** {registro.get('promotoria', 'N/A')}")
        st.markdown(f"📧 **E-mail:** {registro.get('email', 'N/A')} | 📞 **Telefone:** {registro.get('telefone', 'N/A')}")
        
        st.markdown(f"**Tema:** {registro.get('tema', 'N/A')} | **Subtema:** {registro.get('subtema', 'N/A')} | **Empresa:** {registro.get('empresa', 'N/A')}")
        
        st.markdown("**Resumo:**")
        st.info(registro.get('resumo', 'N/A'))
        
        with st.expander("Ver Descrição Completa da Ouvidoria"):
            st.write(registro.get('denuncia', 'N/A'))
            
        if st.button("❌ Fechar Visualização"):
            st.session_state.visualizando_registro = None
            st.rerun()
            
        st.markdown('</div>', unsafe_allow_html=True)
    st.divider()

# ============ FORMULÁRIO DE OUVIDORIA ============
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
        responsavel = st.radio(
            "Enviado por:", 
            options=["Elias", "Matheus", "Ana Beatriz", "Sônia", "Priscila"],
            horizontal=True
        )
    with col2:
        consumidor_vencedor = st.radio(
            "É consumidor vencedor?", 
            options=["Sim", "Não"],
            horizontal=True
        )
        
    submit = st.form_submit_button("🔍 Processar Ouvidoria", use_container_width=True, type="primary")

if submit:
    if not endereco or not denuncia:
        st.error("❌ Por favor, preencha o Endereço e a Descrição da Ouvidoria!")
    else:
        with st.spinner("IA Processando ouvidoria..."):
            try:
                resultado = classificador.processar_denuncia(
                    endereco=endereco,
                    denuncia=denuncia,
                    num_comunicacao=num_comunicacao,
                    num_mprj=num_mprj
                )
                resultado["responsavel"] = responsavel
                resultado["consumidor_vencedor"] = consumidor_vencedor
                resultado["data"] = datetime.now().strftime("%d/%m/%Y %H:%M")
                
                st.session_state.resultado = resultado
                st.session_state.historico.append(resultado)
                
                # SALVAMENTO SEGURO
                with open(historico_file, 'w', encoding='utf-8') as f:
                    json.dump(st.session_state.historico, f, ensure_ascii=False, indent=2)
                
                st.success("✅ Ouvidoria processada e salva com sucesso!")
            except Exception as e:
                st.error(f"Erro ao processar: {e}")

st.divider()

# ============ RESULTADO DA CLASSIFICAÇÃO ============
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
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.success(f"**Tema:** {res['tema']}")
    with col2:
        st.success(f"**Subtema:** {res['subtema']}")
    with col3:
        st.success(f"**Empresa:** {res['empresa']}")
        
    st.markdown("**Resumo da Ouvidoria:**")
    st.markdown(f'<div class="resumo-box">{res["resumo"]}</div>', unsafe_allow_html=True)
    
    if st.button("➕ Nova Ouvidoria", use_container_width=True):
        st.session_state.resultado = None
        st.rerun()

st.divider()

# ============ REGISTRO DE OUVIDORIAS (HISTÓRICO) ============
st.markdown("### 📊 Registro de Ouvidoria")

if not st.session_state.historico:
    st.info("Nenhuma ouvidoria registrada ainda.")
else:
    col1, col2 = st.columns([3, 1])
    with col1:
        search = st.text_input("🔍 Buscar no histórico", placeholder="Pesquise por número, empresa, município...")
    with col2:
        filtro_tema = st.selectbox("Filtrar por Tema", ["Todos"] + sorted(list(set(h['tema'] for h in st.session_state.historico))))

    dados_filtrados = st.session_state.historico
    if search:
        search = search.lower()
        dados_filtrados = [h for h in dados_filtrados if 
                          search in h['num_comunicacao'].lower() or 
                          search in h['num_mprj'].lower() or 
                          search in h['empresa'].lower() or 
                          search in h['municipio'].lower()]
    
    if filtro_tema != "Todos":
        dados_filtrados = [h for h in dados_filtrados if h['tema'] == filtro_tema]

    st.markdown('<div class="tabela-container">', unsafe_allow_html=True)
    
    # Cabeçalho da tabela
    cols = st.columns([1.5, 1.5, 1.5, 2, 1.5, 1.5, 1.5, 1, 1])
    cols[0].write("**Nº Com.**")
    cols[1].write("**Nº MPRJ**")
    cols[2].write("**Data**")
    cols[3].write("**Promotoria**")
    cols[4].write("**Município**")
    cols[5].write("**Cons. Venc.**")
    cols[6].write("**Responsável**")
    cols[7].write("**Ver**")
    cols[8].write("**Apagar**")
    
    st.divider()
    
    for i, registro in enumerate(reversed(dados_filtrados)):
        idx_original = st.session_state.historico.index(registro)
        cols = st.columns([1.5, 1.5, 1.5, 2, 1.5, 1.5, 1.5, 1, 1])
        
        cols[0].write(registro.get('num_comunicacao', 'N/A'))
        cols[1].write(registro.get('num_mprj', 'N/A'))
        cols[2].write(registro.get('data', 'N/A'))
        cols[3].write(registro.get('promotoria', 'N/A'))
        cols[4].write(registro.get('municipio', 'N/A'))
        cols[5].write(registro.get('consumidor_vencedor', 'N/A'))
        cols[6].write(registro.get('responsavel', 'N/A'))
        
        if cols[7].button("👁️", key=f"ver_{idx_original}"):
            st.session_state.visualizando_registro = registro
            st.rerun()
            
        if cols[8].button("🗑️", key=f"del_{idx_original}"):
            st.session_state.historico.pop(idx_original)
            with open(historico_file, 'w', encoding='utf-8') as f:
                json.dump(st.session_state.historico, f, ensure_ascii=False, indent=2)
            st.rerun()
            
    st.markdown('</div>', unsafe_allow_html=True)

st.divider()
st.caption("SARO - Sistema Automático de Registro de Ouvidorias | Desenvolvido para o MPRJ")
