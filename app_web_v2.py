# -*- coding: utf-8 -*-
import streamlit as st
import sqlite3
import os
import json
from datetime import datetime
from classificador_denuncias import ClassificadorDenuncias

# Configuração da página
st.set_page_config(page_title="SARO - MPRJ", layout="wide", page_icon="⚖️")

# Estilos Institucionais (Mantendo sua identidade visual #960018)
st.markdown("""
<style>
    .resumo-box {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 8px;
        border-left: 5px solid #960018;
    }
    .titulo-sessao {
        color: #960018;
        font-weight: bold;
        font-size: 1.2rem;
        margin: 20px 0 15px 0;
    }
    .box-destaque {
        border: 1px solid #960018;
        padding: 15px;
        border-radius: 10px;
        border-left: 10px solid #960018;
        margin-bottom: 20px;
        background-color: white;
    }
    .badge-verde {
        background-color: #e8f5e9;
        color: #2e7d32;
        padding: 5px 15px;
        border-radius: 8px;
        font-weight: bold;
        border: 1px solid #c8e6c9;
        display: inline-block;
    }
    div.stButton > button:first-child {
        background-color: #960018 !important;
        color: white !important;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Inicializar estado e classificador
if "resultado" not in st.session_state:
    st.session_state.resultado = None

try:
    classificador = ClassificadorDenuncias()
except Exception as e:
    st.error(f"Erro ao carregar classificador: {e}")
    st.stop()

st.title("⚖️ Sistema Automático de Registro de Ouvidorias (SARO)")
st.markdown("**Versão 2.2** | Banco de Dados Interno & IA OpenAI")
st.divider()

# ============ 1. FORMULÁRIO DE REGISTRO ============
with st.form("form_ouvidoria", clear_on_submit=True):
    st.markdown('<p class="titulo-sessao">📝 Novo Registro de Ouvidoria</p>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        num_com = st.text_input("Nº de Comunicação", placeholder="Ex: 123/2024")
    with col2:
        num_mprj = st.text_input("Nº MPRJ", placeholder="Ex: 2024.001.002")
        
    endereco = st.text_input("Endereço da Denúncia")
    denuncia = st.text_area("Descrição da Ouvidoria", height=150)
    
    col_f1, col_f2 = st.columns(2)
    responsavel = col_f1.radio("Enviado por:", ["Elias", "Matheus", "Ana Beatriz", "Sônia", "Priscila"], horizontal=True)
    consumidor_vencedor = col_f2.radio("Consumidor vencedor?", ["Sim", "Não"], horizontal=True)
    
    if st.form_submit_button("🔍 REGISTRAR OUVIDORIA", use_container_width=True):
        if endereco and denuncia:
            with st.spinner("IA Processando e Salvando..."):
                res, sucesso = classificador.processar_denuncia(endereco, denuncia, num_com, num_mprj, consumidor_vencedor, responsavel)
                st.session_state.resultado = res
                if sucesso:
                    st.success("✅ Registro realizado com sucesso!")
        else:
            st.error("❌ Preencha Endereço e Descrição!")

# ============ 2. RESULTADO DA CLASSIFICAÇÃO ATUAL ============
if st.session_state.resultado:
    res = st.session_state.resultado
    st.divider()
    st.markdown('<p class="titulo-sessao">✅ Resultado da Última Classificação</p>', unsafe_allow_html=True)
    
    st.markdown(f"""
    <div class="box-destaque">
        <div style="display: flex; justify-content: space-between;">
            <span><b>Nº Comunicação:</b> {res['num_com']}</span>
            <span><b>Nº MPRJ:</b> {res['num_mprj']}</span>
        </div>
        <hr>
        <p>📍 <b>Município:</b> {res['municipio']} | 🏛️ <b>Promotoria:</b> {res['promotoria']}</p>
        <p>👤 <b>Responsável:</b> {res['responsavel']} | 🏆 <b>Consumidor Vencedor:</b> {res['vencedor']}</p>
    </div>
    """, unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns(3)
    c1.markdown(f'<div class="badge-verde">Tema: {res["tema"]}</div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="badge-verde">Subtema: {res["subtema"]}</div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="badge-verde">Empresa: {res["empresa"]}</div>', unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(f'**Resumo da IA:** <div class="resumo-box">{res["resumo"]}</div>', unsafe_allow_html=True)

    if st.button("Limpar Tela para Novo Registro"):
        st.session_state.resultado = None
        st.rerun()

st.divider()

# ============ 3. HISTÓRICO DE REGISTROS (COMO ERA ANTERIORMENTE) ============
st.markdown('<p class="titulo-sessao">📊 Histórico de Registros (Banco Local)</p>', unsafe_allow_html=True)

try:
    conn = sqlite3.connect(classificador.db_path)
    # Pegar os 10 últimos registros para não sobrecarregar a página
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM ouvidorias ORDER BY id DESC LIMIT 15")
    colunas = [description[0] for description in cursor.description]
    registros = [dict(zip(colunas, row)) for row in cursor.fetchall()]
    conn.close()

    if not registros:
        st.info("Nenhuma ouvidoria registrada no banco de dados ainda.")
    else:
        for reg in registros:
            # Card de cada registro histórico
            with st.expander(f"📁 {reg['data']} - {reg['num_com']} | {reg['empresa']}"):
                st.markdown(f"""
                **Nº MPRJ:** {reg['num_mprj']} | **Responsável:** {reg['responsavel']}
                
                **Local:** {reg['municipio']} - {reg['promotoria']}
                
                **Classificação:** {reg['tema']} / {reg['subtema']}
                
                **Resumo IA:** {reg['resumo']}
                """)
                st.text_area("Conteúdo Completo da Denúncia", value=reg['denuncia'], height=100, key=f"hist_{reg['id']}")
                st.markdown("---")
        
        st.caption("Exibindo os últimos 15 registros.")

except Exception as e:
    st.error(f"Erro ao carregar histórico: {e}")

st.divider()
st.caption("SARO v2.2 - Sistema Automático de Registro de Ouvidorias | MPRJ")
