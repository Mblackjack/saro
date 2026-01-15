# -*- coding: utf-8 -*-
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

# CSS customizado com a cor institucional #960018
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
        margin-bottom: 10px;
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
    }}
    /* Cor do botão primário */
    div.stButton > button:first-child {{
        background-color: #960018;
        color: white;
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
st.title("⚖️ SARO - Sistema Automático de Registro de Ouvidorias")
st.markdown("**Versão 6.1** | Gestão Institucional MPRJ")
st.divider()

# Inicializar classificador
try:
    classificador = ClassificadorDenuncias()
except Exception as e:
    st.error(f"Erro ao carregar classificador: {e}")
    st.stop()

# ============ 1. FORMULÁRIO DE OUVIDORIA ============
with st.form("form_ouvidoria", clear_on_submit=True):
    st.markdown('<p class="titulo-sessao">📝 Formulário de Ouvidoria</p>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        num_comunicacao = st.text_input("Nº de Comunicação", placeholder="Ex: 123/2024")
    with col2:
        num_mprj = st.text_input("Nº MPRJ", placeholder="Ex: 2024.001.002")
        
    endereco = st.text_input("Endereço da Denúncia", placeholder="Rua, Número, Bairro, Cidade - RJ")
    denuncia = st.text_area("Descrição da Ouvidoria", placeholder="Descreva aqui o teor da denúncia...")
    
    col1, col2 = st.columns(2)
    with col1:
        responsavel = st.radio("Enviado por:", options=["Elias", "Matheus", "Ana Beatriz", "Sônia", "Priscila"], horizontal=True)
    with col2:
        consumidor_vencedor = st.radio("Consumidor vencedor?", options=["Sim", "Não"], horizontal=True)
        
    submit = st.form_submit_button("🔍 Processar Ouvidoria", use_container_width=True)

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
                st.success("✅ Processado com sucesso!")
            except Exception as e:
                st.error(f"Erro: {e}")

# ============ 2. RESULTADO DA CLASSIFICAÇÃO ============
if st.session_state.resultado:
    st.divider()
    res = st.session_state.resultado
    st.markdown('<p class="titulo-sessao">✅ Resultado da Classificação</p>', unsafe_allow_html=True)
    
    # Box Destaque com Cor Institucional
    st.markdown(f"""
    <div class="box-destaque">
        <span style="color: #960018; font-weight: bold;">📍 Município:</span> {res['municipio']}<br>
        <span style="color: #960018; font-weight: bold;">🏛️ Promotoria Responsável:</span> {res['promotoria']}
    </div>
    """, unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns(3)
    with c1: st.success(f"**Tema:** {res['tema']}")
    with c2: st.success(f"**Subtema:** {res['subtema']}")
    with c3: st.success(f"**Empresa:** {res['empresa']}")
        
    st.markdown("**Resumo da Ouvidoria:**")
    st.markdown(f'<div class="resumo-box">{res["resumo"]}</div>', unsafe_allow_html=True)
    
    # NOVIDADE: Dropdown com descrição completa antes do botão
    with st.expander("📄 Ver Descrição da Ouvidoria"):
        st.write(res['denuncia'])

    if st.button("➕ Nova Ouvidoria", use_container_width=True):
        st.session_state.resultado = None
        st.rerun()

st.divider()

# ============ 3. REGISTRO DE OUVIDORIAS ============
st.markdown('<p class="titulo-sessao">📊 Registro de Ouvidorias</p>', unsafe_allow_html=True)

if not st.session_state.historico:
    st.info("Nenhuma ouvidoria registrada.")
else:
    # Lógica de Busca e Filtro (Omitida para brevidade, mas mantida igual)
    dados = st.session_state.historico
    mostrar_tudo = st.checkbox(f"Mostrar todos os {len(dados)} registros", value=False)
    dados_exibicao = list(reversed(dados)) if mostrar_tudo else list(reversed(dados))[:5]

    st.markdown('<div class="tabela-horizontal">', unsafe_allow_html=True)
    h_cols = st.columns([0.8, 1.2, 1.2, 1.2, 2, 1.5, 1.2, 1.2, 1.2, 1, 1])
    headers = ["Ações", "Nº Com.", "Nº MPRJ", "Data Envio", "Denúncia", "Resumo", "Tema", "Subtema", "Empresa", "Vencedor?", "Usuário"]
    for col, nome in zip(h_cols, headers): col.markdown(f"**{nome}**")
    
    st.divider()

    for idx, registro in enumerate(dados_exibicao):
        idx_orig = st.session_state.historico.index(registro)
        row = st.columns([0.8, 1.2, 1.2, 1.2, 2, 1.5, 1.2, 1.2, 1.2, 1, 1])
        
        if row[0].button("🗑️", key=f"del_{idx_orig}"):
            st.session_state.historico.pop(idx_orig)
            with open(historico_file, 'w', encoding='utf-8') as f:
                json.dump(st.session_state.historico, f, ensure_ascii=False, indent=2)
            st.rerun()
            
        row[1].write(registro.get('num_comunicacao', 'N/A'))
        row[2].write(registro.get('num_mprj', 'N/A'))
        row[3].write(registro.get('data_envio', 'N/A'))
        row[4].write(registro.get('denuncia', '')[:30] + '...')
        row[5].write(registro.get('resumo', 'N/A'))
        row[6].write(registro.get('tema', 'N/A'))
        row[7].write(registro.get('subtema', 'N/A'))
        row[8].write(registro.get('empresa', 'N/A'))
        row[9].write(registro.get('consumidor_vencedor', 'N/A'))
        row[10].write(registro.get('responsavel', 'N/A'))

        # DROPDOWN "VER DETALHES COMPLETOS"
        with st.expander("🔽 Ver Detalhes Completos"):
            st.markdown("#### 🔍 Detalhes da Ouvidoria")
            d_col1, d_col2 = st.columns(2)
            with d_col1:
                st.write(f"**Nº de Comunicação:** {registro.get('num_comunicacao')}")
                st.write(f"**Nº MPRJ:** {registro.get('num_mprj')}")
                st.write(f"**Data:** {registro.get('data_envio')}")
                st.write(f"**Endereço:** {registro.get('endereco')}")
                st.write(f"**Município:** {registro.get('municipio')}")
            with d_col2:
                st.write(f"**Promotoria:** {registro.get('promotoria')}")
                st.write(f"**Tema:** {registro.get('tema')}")
                st.write(f"**Subtema:** {registro.get('subtema')}")
                st.write(f"**Empresa:** {registro.get('empresa')}")
            
            # NOVIDADE: Adicionado o Resumo nos detalhes
            st.markdown(f"**Resumo Gerado:** {registro.get('resumo')}")
            st.text_area("Descrição Completa", value=registro.get('denuncia'), height=150, key=f"t_{idx_orig}")
        
        st.markdown('<hr style="margin:0; border-top: 1px solid #f0f2f6;">', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

st.divider()
st.caption("SARO v6.1 - Sistema Automático de Registro de Ouvidorias | MPRJ")
