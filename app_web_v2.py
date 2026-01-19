# -*- coding: utf-8 -*-
import streamlit as st
import os
from classificador_denuncias import ClassificadorDenuncias

st.set_page_config(page_title="SARO - Excel Online", layout="wide")

# CSS Institucional
st.markdown("""
<style>
    .resumo-box { background-color: #f0f2f6; padding: 15px; border-radius: 8px; border-left: 5px solid #960018; }
    .titulo-sessao { color: #960018; font-weight: bold; font-size: 1.2rem; }
    div.stButton > button:first-child { background-color: #960018 !important; color: white !important; }
</style>
""", unsafe_allow_html=True)

if "resultado" not in st.session_state:
    st.session_state.resultado = None

# Inicialização
try:
    classificador = ClassificadorDenuncias()
except Exception as e:
    st.error(f"Erro: {e}")
    st.stop()

st.title("⚖️ SARO - Registro em Excel Online")
st.sidebar.markdown(f"### [🔗 Abrir Excel Online]({st.secrets.get('GSHEET_URL')})")

# Formulário
with st.form("form_ouvidoria", clear_on_submit=True):
    st.markdown('<p class="titulo-sessao">📝 Novo Registro</p>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    num_com = c1.text_input("Nº de Comunicação")
    num_mprj = c2.text_input("Nº MPRJ")
    endereco = st.text_input("Endereço da Denúncia")
    denuncia = st.text_area("Descrição da Ouvidoria")
    
    cf1, cf2 = st.columns(2)
    responsavel = cf1.radio("Enviado por:", ["Elias", "Matheus", "Ana Beatriz", "Sônia", "Priscila"], horizontal=True)
    vencedor = cf2.radio("Consumidor vencedor?", ["Sim", "Não"], horizontal=True)
    
    if st.form_submit_button("🔍 Registrar e Enviar para Excel Online", use_container_width=True):
        if endereco and denuncia:
            with st.spinner("Classificando e salvando na nuvem..."):
                res = classificador.processar_denuncia(endereco, denuncia, num_com, num_mprj, vencedor, responsavel)
                st.session_state.resultado = res
                st.success("✅ Registrado com sucesso no Google Sheets!")
        else:
            st.error("Preencha os campos obrigatórios.")

# Resultado da Classificação (Aparece na tela para conferência)
if st.session_state.resultado:
    res = st.session_state.resultado
    st.divider()
    st.markdown('<p class="titulo-sessao">✅ Resultado da Classificação Atual</p>', unsafe_allow_html=True)
    
    col_a, col_b = st.columns(2)
    with col_a:
        st.write(f"**🏛️ Promotoria:** {res['Promotoria']}")
        st.write(f"**📍 Município:** {res['Município']}")
    with col_b:
        st.write(f"**Tema:** {res['Tema']}")
        st.write(f"**Empresa:** {res['Empresa']}")
    
    st.markdown(f"**Resumo:**")
    st.markdown(f'<div class="resumo-box">{res["Resumo"]}</div>', unsafe_allow_html=True)
    
    if st.button("➕ Nova Denúncia"):
        st.session_state.resultado = None
        st.rerun()

st.caption("SARO v2.0 | Dados sincronizados com Google Sheets Online")
