# -*- coding: utf-8 -*-
import streamlit as st
import os
from classificador_denuncias import ClassificadorDenuncias

st.set_page_config(page_title="SARO - MPRJ", layout="wide")

# Estilo Institucional
st.markdown("""
<style>
    .resumo-box { background-color: #f0f2f6; padding: 15px; border-radius: 8px; border-left: 5px solid #960018; }
    div.stButton > button:first-child { background-color: #960018 !important; color: white !important; }
</style>
""", unsafe_allow_html=True)

if "resultado" not in st.session_state:
    st.session_state.resultado = None

# Sidebar com Botão de Download do Excel
st.sidebar.image("https://www.mprj.mp.br/mprj-theme/images/mprj/logo_mprj.png", width=180)
st.sidebar.divider()
st.sidebar.subheader("📂 Base de Dados")

excel_path = "Ouvidorias_SARO_Oficial.xlsx"
if os.path.exists(excel_path):
    with open(excel_path, "rb") as f:
        st.sidebar.download_button(
            label="📥 Baixar Excel Atualizado",
            data=f,
            file_name="Ouvidorias_SARO.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    st.sidebar.info("Clique acima para baixar os registros e anexar ao seu link do SharePoint.")
else:
    st.sidebar.warning("Nenhum registro encontrado ainda.")

# Inicializar sistema
try:
    classificador = ClassificadorDenuncias()
except Exception as e:
    st.error("Erro ao carregar sistema. Verifique a chave da API.")
    st.stop()

st.title("⚖️ Registro de Ouvidorias (SARO)")

with st.form("form_saro", clear_on_submit=True):
    st.subheader("📝 Nova Entrada")
    c1, c2 = st.columns(2)
    num_com = c1.text_input("Nº de Comunicação")
    num_mprj = c2.text_input("Nº MPRJ")
    endereco = st.text_input("Endereço (Para detecção de Município/Promotoria)")
    denuncia = st.text_area("Teor da Ouvidoria")
    
    cf1, cf2 = st.columns(2)
    responsavel = cf1.radio("Enviado por:", ["Elias", "Matheus", "Ana Beatriz", "Sônia", "Priscila"], horizontal=True)
    vencedor = cf2.radio("Consumidor vencedor?", ["Sim", "Não"], horizontal=True)
    
    if st.form_submit_button("Registrar Ouvidoria", use_container_width=True):
        if endereco and denuncia:
            with st.spinner("Processando..."):
                st.session_state.resultado = classificador.processar_denuncia(endereco, denuncia, num_com, num_mprj, vencedor, responsavel)
                st.success("✅ Registro concluído e salvo no arquivo Excel do sistema!")
                st.rerun() # Para atualizar o botão de download na lateral
        else:
            st.error("Por favor, preencha o Endereço e a Descrição.")

# Exibição do Resultado na Tela
if st.session_state.resultado:
    res = st.session_state.resultado
    st.divider()
    st.markdown("### ✅ Detalhes da Classificação")
    
    col_x, col_y = st.columns(2)
    with col_x:
        st.write(f"**🏛️ Promotoria:** {res['Promotoria']}")
        st.write(f"**📍 Município:** {res['Município']}")
    with col_y:
        st.write(f"**Tema:** {res['Tema']}")
        st.write(f"**Empresa:** {res['Empresa']}")
    
    st.markdown(f"**Resumo da Ouvidoria:**")
    st.markdown(f'<div class="resumo-box">{res["Resumo"]}</div>', unsafe_allow_html=True)

st.caption("SARO v2.0 - Ministério Público do Rio de Janeiro")
