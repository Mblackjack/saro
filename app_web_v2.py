# -*- coding: utf-8 -*-
import streamlit as st
from classificador_denuncias import ClassificadorDenuncias

st.set_page_config(page_title="SARO - MPRJ", layout="wide")

# Estilo MPRJ
st.markdown("""
<style>
    .resumo-box { background-color: #f0f2f6; padding: 15px; border-radius: 8px; border-left: 5px solid #960018; }
    div.stButton > button:first-child { background-color: #960018 !important; color: white !important; }
</style>
""", unsafe_allow_html=True)

if "resultado" not in st.session_state:
    st.session_state.resultado = None

# Sidebar com link direto para o Excel
st.sidebar.image("https://www.mprj.mp.br/mprj-theme/images/mprj/logo_mprj.png", width=150)
st.sidebar.markdown(f"### [📊 Abrir Excel Online]({st.secrets.get('GSHEET_URL')})")

try:
    classificador = ClassificadorDenuncias()
except Exception as e:
    st.error("Erro de configuração. Verifique os Secrets.")
    st.stop()

st.title("⚖️ Registro de Ouvidorias (SARO)")

with st.form("form_saro", clear_on_submit=True):
    st.subheader("📝 Nova Denúncia")
    c1, c2 = st.columns(2)
    num_com = c1.text_input("Nº de Comunicação")
    num_mprj = c2.text_input("Nº MPRJ")
    endereco = st.text_input("Endereço Completo")
    denuncia = st.text_area("Descrição da Denúncia")
    
    cf1, cf2 = st.columns(2)
    responsavel = cf1.radio("Enviado por:", ["Elias", "Matheus", "Ana Beatriz", "Sônia", "Priscila"], horizontal=True)
    vencedor = cf2.radio("Consumidor vencedor?", ["Sim", "Não"], horizontal=True)
    
    if st.form_submit_button("Registrar e Enviar para Excel Online", use_container_width=True):
        if endereco and denuncia:
            with st.spinner("Sincronizando com Excel Online..."):
                st.session_state.resultado = classificador.processar_denuncia(endereco, denuncia, num_com, num_mprj, vencedor, responsavel)
                st.success("✅ Enviado para a planilha online!")
        else:
            st.error("Preencha Endereço e Denúncia.")

if st.session_state.resultado:
    res = st.session_state.resultado
    st.divider()
    st.markdown("### ✅ Resultado da Classificação")
    col1, col2 = st.columns(2)
    col1.write(f"**🏛️ Promotoria:** {res['Promotoria']}")
    col2.write(f"**Tema:** {res['Tema']}")
    st.markdown(f"**Resumo:**")
    st.markdown(f'<div class="resumo-box">{res["Resumo"]}</div>', unsafe_allow_html=True)

st.caption("SARO v2.0 - Ministério Público do Rio de Janeiro")
