# -*- coding: utf-8 -*-
"""
SARO v6.2 - Sistema Automático de Registro de Ouvidorias
Versão Final - Identidade Visual MPRJ (#960018)
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

# Carregar histórico
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
        st.error("❌ Preencha os campos obrigatórios!")
    else:
        with st.spinner("IA Processando..."):
            try:
                resultado = classificador.processar_denuncia(endereco, denuncia, num_comunicacao, num_mprj)
                resultado.update({
                    "responsavel": responsavel,
                    "consumidor_vencedor": consumidor_vencedor,
                    "data_envio": datetime.now().strftime("%d/%m/%Y %H:%M")
                })
                st.session_state.resultado = resultado
                st.session_state.historico.append(resultado)
                with open(historico_file, 'w', encoding='utf-8') as f:
                    json.dump(st.session_state.historico, f, ensure_ascii=False, indent=2)
                st.success("✅ Denúncia processada!")
            except Exception as e:
                st.error(f"Erro no processamento: {e}")

# ============ 2. RESULTADO DA CLASSIFICAÇÃO ============
if st.session_state.resultado:
    st.divider()
    res = st.session_state.resultado
    st.markdown('<p class="titulo-sessao">✅ Resultado da Classificação Atual</p>', unsafe_allow_html=True)
    
    st.markdown(f"""
    <div class="box-destaque">
        <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
            <span><b style="color: #960018;">Nº Comunicação:</b> {res.get('num_comunicacao', 'N/A')}</span>
            <span><b style="color: #960018;">Nº MPRJ:</b> {res.get('num_mprj', 'N/A')}</span>
        </div>
        <hr style="border: 0; border-top: 1px solid #eee; margin: 10px 0;">
        <span style="color: #960018; font-weight: bold;">📍 Município:</span> {res.get('municipio', 'Não identificado')}<br>
        <span style="color: #960018; font-weight: bold;">🏛️ Promotoria Responsável:</span> {res.get('promotoria', 'Não identificada')}
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"📧 **E-mail:** {res.get('email', 'N/A')} | 📞 **Telefone:** {res.get('telefone', 'N/A')}")
    
    c1, c2, c3 = st.columns(3)
    with c1: st.success(f"**Tema:** {res.get('tema')}")
    with c2: st.success(f"**Subtema:** {res.get('subtema')}")
    with c3: st.success(f"**Empresa:** {res.get('empresa')}")
        
    st.markdown("**Resumo da IA:**")
    st.markdown(f'<div class="resumo-box">{res.get("resumo")}</div>', unsafe_allow_html=True)

    if st.button("➕ Limpar e Nova Ouvidoria", use_container_width=True):
        st.session_state.resultado = None
        st.rerun()

st.divider()

# ============ 3. HISTÓRICO ============
st.markdown('<p class="titulo-sessao">📊 Histórico de Registros</p>', unsafe_allow_html=True)

if not st.session_state.historico:
    st.info("Nenhuma ouvidoria registrada.")
else:
    search = st.text_input("🔍 Pesquisar")
    dados = st.session_state.historico
    if search:
        dados = [h for h in dados if search.lower() in str(h).lower()]

    mostrar_tudo = st.checkbox(f"Mostrar todos ({len(dados)})", value=False)
    dados_exibicao = list(reversed(dados)) if mostrar_tudo else list(reversed(dados))[:5]

    for idx, registro in enumerate(dados_exibicao):
        idx_orig = st.session_state.historico.index(registro)
        with st.expander(f"Registro {registro.get('num_comunicacao')} - {registro.get('empresa')}"):
            st.write(f"**Data:** {registro.get('data_envio')}")
            st.write(f"**Promotoria:** {registro.get('promotoria')}")
            st.info(f"**Resumo:** {registro.get('resumo')}")
            if st.button("🗑️ Apagar", key=f"del_{idx_orig}"):
                st.session_state.historico.pop(idx_orig)
                with open(historico_file, 'w', encoding='utf-8') as f:
                    json.dump(st.session_state.historico, f, ensure_ascii=False, indent=2)
                st.rerun()

st.caption("SARO v1.0 | Ministério Público do Rio de Janeiro")
