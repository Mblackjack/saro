# -*- coding: utf-8 -*-
"""
SARO v6.2 - Sistema Automático de Registro de Ouvidorias
Versão Final Corrigida - Identidade Visual MPRJ (#960018)
"""

import streamlit as st
import json
import os
from datetime import datetime
from classificador_denuncias import ClassificadorDenuncias

# ============ 1. CONFIGURAÇÃO DA PÁGINA ============
st.set_page_config(
    page_title="SARO - Sistema de Ouvidorias",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Caminhos de arquivos
base_path = os.path.dirname(os.path.abspath(__file__))
historico_file = os.path.join(base_path, "historico_denuncias.json")

# ============ 2. ESTILIZAÇÃO (CSS) ============
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
        margin-bottom: 15px;
        margin-top: 10px;
    }
    .box-destaque {
        border: 1px solid #960018;
        padding: 15px;
        border-radius: 10px;
        border-left: 10px solid #960018;
        margin-bottom: 20px;
        background-color: white;
    }
    .tabela-horizontal {
        overflow-x: auto;
        width: 100%;
        border: 1px solid #e6e9ef;
        border-radius: 8px;
        background-color: white;
    }
    div.stButton > button:first-child {
        background-color: #960018 !important;
        color: white !important;
        border: none;
    }
    .header-text {
        font-weight: bold;
        color: #333;
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)

# ============ 3. GESTÃO DE ESTADO E DADOS ============
if "resultado" not in st.session_state:
    st.session_state.resultado = None

if "historico" not in st.session_state:
    st.session_state.historico = []

# Função para carregar histórico com tratamento de erro
def carregar_historico():
    if os.path.exists(historico_file):
        try:
            with open(historico_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return []
    return []

st.session_state.historico = carregar_historico()

# ============ 4. LÓGICA DE NEGÓCIO ============
try:
    classificador = ClassificadorDenuncias()
except Exception as e:
    st.error(f"Erro crítico ao carregar classificador: {e}")
    st.stop()

# ============ 5. INTERFACE DO USUÁRIO ============
st.title("⚖️ Sistema Automático de Registro de Ouvidorias (SARO)")
st.markdown("**Versão 1.0** | Inteligência Artificial aplicada ao MPRJ")
st.divider()

# Formulário de Entrada
with st.form("form_ouvidoria", clear_on_submit=True):
    st.markdown('<p class="titulo-sessao">📝 Novo Registro de Ouvidoria</p>', unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    with c1:
        num_comunicacao = st.text_input("Nº de Comunicação", placeholder="Ex: 123/2024")
    with c2:
        num_mprj = st.text_input("Nº MPRJ", placeholder="Ex: 2024.001.002")
        
    endereco = st.text_input("Endereço da Denúncia", placeholder="Rua, Número, Bairro, Cidade - RJ")
    denuncia = st.text_area("Descrição da Ouvidoria", placeholder="Descreva aqui o teor da denúncia...")
    
    f1, f2 = st.columns(2)
    with f1:
        responsavel = st.radio("Enviado por:", options=["Elias", "Matheus", "Ana Beatriz", "Sônia", "Priscila"], horizontal=True)
    with f2:
        consumidor_vencedor = st.radio("Consumidor vencedor?", options=["Sim", "Não"], horizontal=True)
        
    submit = st.form_submit_button("🔍 Processar e Registrar", use_container_width=True)

# Processamento do formulário
if submit:
    if not endereco or not denuncia:
        st.error("❌ Por favor, preencha o endereço e a descrição da denúncia.")
    else:
        with st.spinner("A Inteligência Artificial está analisando os dados..."):
            try:
                res = classificador.processar_denuncia(endereco, denuncia, num_comunicacao, num_mprj)
                res.update({
                    "responsavel": responsavel,
                    "consumidor_vencedor": consumidor_vencedor,
                    "data_envio": datetime.now().strftime("%d/%m/%Y %H:%M"),
                    "denuncia": denuncia,
                    "endereco": endereco
                })
                
                st.session_state.resultado = res
                st.session_state.historico.append(res)
                
                with open(historico_file, 'w', encoding='utf-8') as f:
                    json.dump(st.session_state.historico, f, ensure_ascii=False, indent=2)
                
                st.success("✅ Registro concluído com sucesso!")
            except Exception as e:
                st.error(f"Erro no processamento da IA: {e}")

# Exibição do Resultado Atual
if st.session_state.resultado:
    st.divider()
    res = st.session_state.resultado
    st.markdown('<p class="titulo-sessao">✅ Detalhes da Classificação</p>', unsafe_allow_html=True)
    
    st.markdown(f"""
    <div class="box-destaque">
        <div style="display: flex; justify-content: space-between;">
            <span><b>Nº COM:</b> {res.get('num_comunicacao')}</span>
            <span><b>Nº MPRJ:</b> {res.get('num_mprj')}</span>
        </div>
        <hr>
        <b>📍 Localidade:</b> {res.get('municipio', 'N/D')} | <b>🏛️ Órgão:</b> {res.get('promotoria', 'N/D')}
    </div>
    """, unsafe_allow_html=True)
    
    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Tema", res.get('tema'))
    col_b.metric("Subtema", res.get('subtema'))
    col_c.metric("Empresa", res.get('empresa'))
    
    st.markdown(f'<div class="resumo-box"><b>Resumo IA:</b> {res.get("resumo")}</div>', unsafe_allow_html=True)
    
    if st.button("➕ Novo Registro"):
        st.session_state.resultado = None
        st.rerun()

# ============ 6. HISTÓRICO DE REGISTROS ============
st.divider()
st.markdown('<p class="titulo-sessao">📊 Histórico de Atividades</p>', unsafe_allow_html=True)

if not st.session_state.historico:
    st.info("O histórico está vazio.")
else:
    busca = st.text_input("🔍 Filtrar histórico (Empresa, Nº, Tema...)", "").lower()
    
    # Filtragem e inversão para mostrar os mais recentes primeiro
    dados_filtrados = [r for r in st.session_state.historico if busca in str(r).lower()]
    dados_exibicao = list(reversed(dados_filtrados))

    for idx, reg in enumerate(dados_exibicao):
        with st.expander(f"📁 {reg.get('data_envio')} | {reg.get('empresa')} | {reg.get('num_mprj')}"):
            col_d1, col_d2 = st.columns(2)
            with col_d1:
                st.write(f"**Usuário:** {reg.get('responsavel')}")
                st.write(f"**Vencedor:** {reg.get('consumidor_vencedor')}")
                st.write(f"**Endereço:** {reg.get('endereco')}")
            with col_d2:
                st.write(f"**Tema:** {reg.get('tema')}")
                st.write(f"**Subtema:** {reg.get('subtema')}")
                st.write(f"**Promotoria:** {reg.get('promotoria')}")
            
            st.info(f"**Resumo:** {reg.get('resumo')}")
            st.text_area("Teor da Denúncia", reg.get('denuncia'), height=100, key=f"hist_{idx}")
            
            if st.button("Remover Registro", key=f"btn_del_{idx}"):
                # Encontra o índice real no histórico original para remover
                indice_real = st.session_state.historico.index(reg)
                st.session_state.historico.pop(indice_real)
                with open(historico_file, 'w', encoding='utf-8') as f:
                    json.dump(st.session_state.historico, f, ensure_ascii=False, indent=2)
                st.rerun()

st.caption("SARO v1.0 | Desenvolvido para o MPRJ")
