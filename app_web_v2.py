# -*- coding: utf-8 -*-
"""
SARO v2.0 - Sistema Automático de Registro de Ouvidorias
Focado em Registro Local e Gestão via Excel
"""

import streamlit as st
import os
from classificador_denuncias import ClassificadorDenuncias

# Configuração da Página
st.set_page_config(page_title="SARO - MPRJ", layout="wide", page_icon="⚖️")

# CSS para Identidade Visual #960018
st.markdown("""
<style>
    .resumo-box { 
        background-color: #f0f2f6; 
        padding: 15px; 
        border-radius: 8px; 
        border-left: 5px solid #960018;
        font-size: 1.1rem;
    }
    .stButton > button {
        background-color: #960018 !important;
        color: white !important;
        font-weight: bold;
    }
    .titulo-custom { color: #960018; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# Estado da Sessão
if "resultado" not in st.session_state:
    st.session_state.resultado = None

# Inicializar Classificador
try:
    classificador = ClassificadorDenuncias()
except Exception as e:
    st.error(f"Erro ao iniciar sistema: {e}")
    st.stop()

# --- BARRA LATERAL ---
st.sidebar.image("https://www.mprj.mp.br/mprj-theme/images/mprj/logo_mprj.png", width=180)
st.sidebar.markdown("---")
st.sidebar.subheader("📥 Exportação de Dados")

excel_path = "Ouvidorias_SARO_Oficial.xlsx"
if os.path.exists(excel_path):
    with open(excel_path, "rb") as f:
        st.sidebar.download_button(
            label="Baixar Planilha Atualizada",
            data=f,
            file_name="Ouvidorias_SARO.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    st.sidebar.success("O arquivo Excel contém todos os registros desta sessão.")
else:
    st.sidebar.info("Aguardando primeiro registro para gerar o Excel.")

# --- CORPO PRINCIPAL ---
st.title("⚖️ Sistema de Registro de Ouvidoria (SARO)")
st.markdown("Preencha os dados abaixo para registrar a denúncia e gerar a classificação automática.")

with st.form("form_registro", clear_on_submit=True):
    st.markdown('<p class="titulo-custom">📝 Dados da Ouvidoria</p>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    num_com = col1.text_input("Nº de Comunicação", placeholder="Ex: 001/2026")
    num_mprj = col2.text_input("Nº MPRJ", placeholder="Ex: 2026.0001.0002")
    
    endereco = st.text_input("Endereço Completo (Rua, Bairro, Município)", placeholder="Obrigatório para identificar a Promotoria")
    denuncia = st.text_area("Descrição/Teor da Denúncia", placeholder="Cole aqui o texto da ouvidoria...")
    
    st.markdown("---")
    f_col1, f_col2 = st.columns(2)
    responsavel = f_col1.radio("Responsável pelo Registro:", ["Elias", "Matheus", "Ana Beatriz", "Sônia", "Priscila"], horizontal=True)
    vencedor = f_col2.radio("O Consumidor é vencedor?", ["Sim", "Não"], horizontal=True)
    
    submit = st.form_submit_button("REGISTRAR OUVIDORIA", use_container_width=True)

if submit:
    if not endereco or not denuncia:
        st.error("❌ Por favor, preencha o Endereço e a Descrição da Denúncia.")
    else:
        with st.spinner("IA classificando denúncia..."):
            resultado = classificador.processar_denuncia(endereco, denuncia, num_com, num_mprj, vencedor, responsavel)
            st.session_state.resultado = resultado
            st.success("✅ Denúncia registrada com sucesso!")
            st.rerun()

# --- RESULTADO DA CLASSIFICAÇÃO ---
if st.session_state.resultado:
    res = st.session_state.resultado
    st.divider()
    st.markdown('<p class="titulo-custom">🔍 Resultado da Classificação Inteligente</p>', unsafe_allow_html=True)
    
    c_res1, c_res2, c_res3 = st.columns(3)
    c_res1.metric("Empresa", res["Empresa"])
    c_res2.metric("Tema", res["Tema"])
    c_res3.metric("Município", res["Município"])
    
    st.info(f"**🏛️ Promotoria Destino:** {res['Promotoria']}")
    
    st.markdown("**Resumo Gerado pela IA:**")
    st.markdown(f'<div class="resumo-box">{res["Resumo"]}</div>', unsafe_allow_html=True)
    
    if st.button("Limpar Tela para Novo Registro"):
        st.session_state.resultado = None
        st.rerun()

st.divider()
st.caption("SARO v2.0 - Desenvolvido para MPRJ")
