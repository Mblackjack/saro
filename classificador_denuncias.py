# -*- coding: utf-8 -*-
import streamlit as st
import os
from classificador_denuncias import ClassificadorDenuncias

st.set_page_config(page_title="SARO - MPRJ", layout="wide")

st.markdown("""
<style>
    .resumo-box { background-color: #f0f2f6; padding: 15px; border-radius: 8px; border-left: 5px solid #960018; }
    div.stButton > button:first-child { background-color: #960018 !important; color: white !important; font-weight: bold; }
    .titulo-custom { color: #960018; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

if "resultado" not in st.session_state:
    st.session_state.resultado = None

try:
    classificador = ClassificadorDenuncias()
except Exception as e:
    st.error(f"Erro ao iniciar sistema: {e}")
    st.stop()

# Sidebar para Download
st.sidebar.image("https://www.mprj.mp.br/mprj-theme/images/mprj/logo_mprj.png", width=180)
st.sidebar.markdown("---")
st.sidebar.subheader("📂 Base de Dados Excel")

excel_path = os.path.join(os.path.dirname(__file__), "Ouvidorias_SARO_Oficial.xlsx")
if os.path.exists(excel_path):
    with open(excel_path, "rb") as f:
        st.sidebar.download_button(
            label="📥 Baixar Excel Atualizado",
            data=f,
            file_name="Ouvidorias_SARO.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
else:
    st.sidebar.info("O Excel será gerado após o primeiro registro.")

st.title("⚖️ Sistema Automático de Registro de Ouvidorias (SARO)")

with st.form("form_registro", clear_on_submit=True):
    st.markdown('<p class="titulo-custom">📝 Novo Registro</p>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    num_com = c1.text_input("Nº de Comunicação")
    num_mprj = c2.text_input("Nº MPRJ")
    endereco = st.text_input("Endereço Completo")
    denuncia = st.text_area("Descrição da Ouvidoria")
    
    f1, f2 = st.columns(2)
    responsavel = f1.radio("Enviado por:", ["Elias", "Matheus", "Ana Beatriz", "Sônia", "Priscila"], horizontal=True)
    vencedor = f2.radio("Consumidor vencedor?", ["Sim", "Não"], horizontal=True)
    
    if st.form_submit_button("REGISTRAR E SALVAR", use_container_width=True):
        if endereco and denuncia:
            with st.spinner("Processando..."):
                st.session_state.resultado = classificador.processar_denuncia(endereco, denuncia, num_com, num_mprj, vencedor, responsavel)
                st.success("✅ Registrado com sucesso!")
                st.rerun()
        else:
            st.error("Preencha Endereço e Denúncia.")

if st.session_state.resultado:
    res = st.session_state.resultado
    st.divider()
    st.markdown('<p class="titulo-custom">✅ Resultado da Classificação Atual</p>', unsafe_allow_html=True)
    
    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Empresa", res["Empresa"])
    col_b.metric("Tema", res["Tema"])
    col_c.metric("Município", res["Município"])
    
    st.write(f"**🏛️ Promotoria:** {res['Promotoria']}")
    st.markdown(f"**Resumo da IA:**")
    st.markdown(f'<div class="resumo-box">{res["Resumo"]}</div>', unsafe_allow_html=True)

st.caption("SARO v2.0 - Ministério Público do Rio de Janeiro")
