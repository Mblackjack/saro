# -*- coding: utf-8 -*-
"""
SARO v5.2 - Sistema Automático de Registro de Ouvidorias
Interface Web com Streamlit - Visualização de Detalhes no Rodapé
"""

import streamlit as st
import json
import os
from datetime import datetime

# Configuração da página
st.set_page_config(page_title="SARO - Sistema de Ouvidorias", layout="wide")

# ============ AJUSTE DE CAMINHOS DINÂMICOS ============
base_path = os.path.dirname(os.path.abspath(__file__))
historico_file = os.path.join(base_path, "historico_denuncias.json")

# CSS customizado
st.markdown("""
<style>
    .resumo-box { background-color: #f0f2f6; padding: 15px; border-radius: 8px; border-left: 4px solid #1f77b4; }
    .tabela-container { border: 1px solid #ddd; border-radius: 5px; padding: 10px; background-color: white; }
    .modal-container { background-color: #fdfdfd; border: 1px solid #1f77b4; border-radius: 8px; padding: 20px; margin-top: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
</style>
""", unsafe_allow_html=True)

# Inicializar estado da sessão
if "resultado" not in st.session_state: st.session_state.resultado = None
if "historico" not in st.session_state: st.session_state.historico = []
if "visualizando_registro" not in st.session_state: st.session_state.visualizando_registro = None

# CARREGAMENTO SEGURO DO HISTÓRICO
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

# INICIALIZAÇÃO SEGURA DO CLASSIFICADOR
try:
    from classificador_denuncias import ClassificadorDenuncias
    classificador = ClassificadorDenuncias()
except Exception as e:
    st.error(f"⚠️ Erro ao inicializar o Classificador: {e}")
    st.stop()

# ============ 1. FORMULÁRIO DE OUVIDORIA ============
with st.form("form_ouvidoria", clear_on_submit=True):
    st.markdown("### 📝 Formulário de Entrada")
    col1, col2 = st.columns(2)
    with col1: num_comunicacao = st.text_input("Nº de Comunicação")
    with col2: num_mprj = st.text_input("Nº MPRJ")
    endereco = st.text_input("Endereço da Denúncia")
    denuncia = st.text_area("Descrição da Ouvidoria")
    col1, col2 = st.columns(2)
    with col1: responsavel = st.radio("Enviado por:", options=["Elias", "Matheus", "Ana Beatriz", "Sônia", "Priscila"], horizontal=True)
    with col2: consumidor_vencedor = st.radio("Consumidor vencedor?", options=["Sim", "Não"], horizontal=True)
    submit = st.form_submit_button("🔍 Processar Ouvidoria", use_container_width=True, type="primary")

if submit:
    if not endereco or not denuncia:
        st.error("❌ Preencha os campos obrigatórios!")
    else:
        with st.spinner("IA Processando..."):
            try:
                resultado = classificador.processar_denuncia(endereco, denuncia, num_comunicacao, num_mprj)
                resultado.update({"responsavel": responsavel, "consumidor_vencedor": consumidor_vencedor, "data": datetime.now().strftime("%d/%m/%Y %H:%M")})
                st.session_state.resultado = resultado
                st.session_state.historico.append(resultado)
                with open(historico_file, 'w', encoding='utf-8') as f:
                    json.dump(st.session_state.historico, f, ensure_ascii=False, indent=2)
                st.success("✅ Processado!")
            except Exception as e:
                st.error(f"Erro: {e}")

# ============ 2. RESULTADO IMEDIATO ============
if st.session_state.resultado:
    res = st.session_state.resultado
    with st.expander("Ver Último Resultado Processado", expanded=True):
        st.write(f"**Tema:** {res['tema']} | **Subtema:** {res['subtema']} | **Empresa:** {res['empresa']}")
        st.info(f"**Resumo:** {res['resumo']}")
        if st.button("Limpar Tela"):
            st.session_state.resultado = None
            st.rerun()

st.divider()

# ============ 3. REGISTRO (TABELA HISTÓRICA) ============
st.markdown("### 📊 Registro de Ouvidoria")
if not st.session_state.historico:
    st.info("Nenhuma ouvidoria registrada.")
else:
    # Filtros
    c1, c2 = st.columns([3, 1])
    search = c1.text_input("🔍 Buscar", placeholder="Empresa, número...")
    filtro_tema = c2.selectbox("Tema", ["Todos"] + sorted(list(set(h['tema'] for h in st.session_state.historico))))

    dados = st.session_state.historico
    if search:
        s = search.lower()
        dados = [h for h in dados if s in str(h).lower()]
    if filtro_tema != "Todos":
        dados = [h for h in dados if h['tema'] == filtro_tema]

    # Renderização da Tabela
    st.markdown('<div class="tabela-container">', unsafe_allow_html=True)
    cols = st.columns([1.5, 1.5, 1.5, 2, 1.5, 1, 1])
    cols[0].write("**Nº Com.**"); cols[1].write("**Data**"); cols[2].write("**Empresa**"); 
    cols[3].write("**Promotoria**"); cols[4].write("**Responsável**"); cols[5].write("**Ver**"); cols[6].write("**Apagar**")
    
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

# ============ 4. DETALHES (AGORA NO FINAL DA PÁGINA) ============
if st.session_state.visualizando_registro:
    st.divider()
    reg = st.session_state.visualizando_registro
    st.markdown(f"### 🔍 Detalhes: {reg['num_comunicacao']}")
    
    with st.container():
        st.markdown('<div class="modal-container">', unsafe_allow_html=True)
        col1, col2, col3 = st.columns(3)
        col1.metric("Empresa", reg['empresa'])
        col2.metric("Município", reg['municipio'])
        col3.metric("Data", reg['data'])
        
        c1, c2 = st.columns(2)
        with c1:
            st.write(f"**Tema:** {reg['tema']}")
            st.write(f"**Subtema:** {reg['subtema']}")
            st.write(f"**Promotoria:** {reg['promotoria']}")
        with c2:
            st.write(f"**E-mail:** {reg['email']}")
            st.write(f"**Vencedor:** {reg['consumidor_vencedor']}")
            st.write(f"**Responsável:** {reg['responsavel']}")

        st.info(f"**Resumo da IA:** {reg['resumo']}")
        with st.expander("Ver Texto Completo da Denúncia"):
            st.write(reg['denuncia'])
            
        if st.button("🔼 Fechar Detalhes"):
            st.session_state.visualizando_registro = None
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

st.caption("SARO | MPRJ")
