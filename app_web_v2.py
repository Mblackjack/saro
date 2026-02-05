# -*- coding: utf-8 -*-
import streamlit as st
import json
import os
from datetime import datetime
from classificador_denuncias import ClassificadorDenuncias

st.set_page_config(page_title="SARO - MPRJ", layout="wide", page_icon="⚖️")

# Estilos Institucionais
st.markdown("""
<style>
    .resumo-box { background-color: #f0f2f6; padding: 15px; border-radius: 8px; border-left: 5px solid #960018; }
    .titulo-sessao { color: #960018; font-weight: bold; font-size: 1.2rem; margin: 10px 0 15px 0; }
    .box-destaque { border: 1px solid #960018; padding: 15px; border-radius: 10px; border-left: 10px solid #960018; background-color: white; margin-bottom: 20px; }
    div.stButton > button:first-child { background-color: #960018 !important; color: white !important; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

if "resultado" not in st.session_state:
    st.session_state.resultado = None

try:
    classificador = ClassificadorDenuncias()
except Exception as e:
    st.error(f"Erro ao carregar classificador: {e}")
    st.stop()

st.title("⚖️ Sistema Automático de Registro de Ouvidorias (SARO)")
st.markdown("**Versão 2.0** | GPT-4o-mini & Integração SharePoint")
st.divider()

# ============ FORMULÁRIO ============
with st.form("form_ouvidoria", clear_on_submit=True):
    st.markdown('<p class="titulo-sessao">📝 Novo Registro de Ouvidoria</p>', unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    num_comunicacao = c1.text_input("Nº de Comunicação")
    num_mprj = c2.text_input("Nº MPRJ")
    
    endereco = st.text_input("Endereço da Denúncia")
    denuncia = st.text_area("Descrição da Ouvidoria", height=150)
    
    f1, f2 = st.columns(2)
    responsavel = f1.radio("Enviado por:", ["Elias", "Matheus", "Ana Beatriz", "Sônia", "Priscila"], horizontal=True)
    vencedor = f2.radio("Consumidor vencedor?", ["Sim", "Não"], horizontal=True)
    
    submit = st.form_submit_button("🔍 REGISTRAR NO SHAREPOINT", use_container_width=True)

if submit:
    if not endereco or not denuncia:
        st.error("❌ Preencha os campos obrigatórios!")
    else:
        with st.spinner("IA Processando e Enviando..."):
            # CORREÇÃO: Passando os 6 argumentos necessários
            resultado, sucesso = classificador.processar_denuncia(
                endereco, denuncia, num_comunicacao, num_mprj, vencedor, responsavel
            )
            st.session_state.resultado = resultado
            if sucesso:
                st.success("✅ Denúncia registrada com sucesso no SharePoint!")
            else:
                st.warning("⚠️ Classificado, mas o SharePoint não respondeu. Verifique o link do Power Automate.")

# ============ EXIBIÇÃO DO RESULTADO ATUAL ============
if st.session_state.resultado:
    res = st.session_state.resultado
    st.divider()
    st.markdown(f"""
    <div class="box-destaque">
        <p><b style="color: #960018;">Nº Comunicação:</b> {res['num_com']} | <b style="color: #960018;">Nº MPRJ:</b> {res['num_mprj']}</p>
        <p>📍 <b>Município:</b> {res['municipio']} | 🏛️ <b>Promotoria:</b> {res['promotoria']}</p>
        <p>👤 <b>Responsável:</b> {res['responsavel']} | 🏆 <b>Vencedor:</b> {res['vencedor']}</p>
    </div>
    """, unsafe_allow_html=True)
    
    col_t1, col_t2, col_t3 = st.columns(3)
    col_t1.info(f"**Tema:** {res['tema']}")
    col_t2.info(f"**Subtema:** {res['subtema']}")
    col_t3.info(f"**Empresa:** {res['empresa']}")
    
    st.markdown(f'**Resumo IA:** <div class="resumo-box">{res["resumo"]}</div>', unsafe_allow_html=True)
    
    if st.button("➕ Nova Ouvidoria", use_container_width=True):
        st.session_state.resultado = None
        st.rerun()

st.divider()
st.caption("SARO v2.0 - Matheus Pereira Barreto | MPRJ")
