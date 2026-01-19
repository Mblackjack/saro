# -*- coding: utf-8 -*-
import streamlit as st
import json
import os
from datetime import datetime

# Tenta importar o classificador local
try:
    from classificador_denuncias import ClassificadorDenuncias
except ImportError:
    st.error("Erro: O arquivo 'classificador_denuncias.py' não foi encontrado na mesma pasta.")
    st.stop()

# Configuração da página
st.set_page_config(page_title="SARO - MPRJ", layout="wide")

# Caminhos
base_path = os.path.dirname(os.path.abspath(__file__))
historico_file = os.path.join(base_path, "historico_denuncias.json")

# CSS Institucional
st.markdown("""
<style>
    .resumo-box { background-color: #f0f2f6; padding: 15px; border-radius: 8px; border-left: 5px solid #960018; }
    .titulo-sessao { color: #960018; font-weight: bold; font-size: 1.2rem; margin: 10px 0; }
    .box-destaque { border: 1px solid #960018; padding: 15px; border-radius: 10px; border-left: 10px solid #960018; background-color: white; }
    div.stButton > button:first-child { background-color: #960018 !important; color: white !important; }
</style>
""", unsafe_allow_html=True)

# Inicialização do Estado
if "resultado" not in st.session_state: st.session_state.resultado = None
if "historico" not in st.session_state:
    if os.path.exists(historico_file):
        with open(historico_file, 'r', encoding='utf-8') as f:
            st.session_state.historico = json.load(f)
    else:
        st.session_state.historico = []

# Cabeçalho
st.title("⚖️ SARO - Registro de Ouvidorias")
st.divider()

# Instanciar Classificador
classificador = ClassificadorDenuncias()

# Formulário
with st.form("form_ouvidoria", clear_on_submit=True):
    st.markdown('<p class="titulo-sessao">📝 Novo Registro</p>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    num_com = c1.text_input("Nº Comunicação")
    num_mprj = c2.text_input("Nº MPRJ")
    end = st.text_input("Endereço")
    desc = st.text_area("Descrição")
    
    f1, f2 = st.columns(2)
    resp = f1.radio("Responsável", ["Elias", "Matheus", "Ana Beatriz", "Sônia", "Priscila"], horizontal=True)
    venc = f2.radio("Consumidor Vencedor?", ["Sim", "Não"], horizontal=True)
    
    if st.form_submit_button("Registrar", use_container_width=True):
        if end and desc:
            res = classificador.processar_denuncia(end, desc, num_com, num_mprj)
            res.update({"responsavel": resp, "consumidor_vencedor": venc, "data_envio": datetime.now().strftime("%d/%m/%Y %H:%M"), "denuncia": desc})
            st.session_state.resultado = res
            st.session_state.historico.append(res)
            with open(historico_file, 'w', encoding='utf-8') as f:
                json.dump(st.session_state.historico, f, ensure_ascii=False, indent=2)
            st.rerun()

# Histórico simplificado
st.divider()
st.markdown('<p class="titulo-sessao">📊 Histórico</p>', unsafe_allow_html=True)
for i, r in enumerate(reversed(st.session_state.historico)):
    with st.expander(f"{r.get('data_envio')} - {r.get('empresa')}"):
        st.write(f"**Tema:** {r.get('tema')} | **Resumo:** {r.get('resumo')}")
