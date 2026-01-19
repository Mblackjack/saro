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
        margin-bottom: 15px;
        margin-top: 10px;
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
        background-color: white;
    }}
    /* Botão Primário Customizado */
    div.stButton > button:first-child {{
        background-color: #960018 !important;
        color: white !important;
        border: none;
    }}
    /* Ajuste de cabeçalho da tabela */
    .header-text {{
        font-weight: bold;
        color: #333;
        font-size: 0.9rem;
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
st.title("⚖️Sistema Automático de Registro de Ouvidorias (SARO)")
st.markdown("**Versão 1.0** | Registro e Gestão de Ouvidorias com auxílio de Inteligência Artificial")
st.divider()

# Inicializar classificador
try:
    classificador = ClassificadorDenuncias()
except Exception as e:
    st.error(f"Erro ao carregar classificador: {e}")
    st.stop()

# ============ 1. FORMULÁRIO DE OUVIDORIA ============
with st.form("form_ouvidoria", clear_on_submit=True):
    st.markdown('<p class="titulo-sessao">📝 Novo Registro de Ouvidoria</p>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        num_comunicacao = st.text_input("Nº de Comunicação", placeholder="Ex: 123/2024")
    with col2:
        num_mprj = st.text_input("Nº MPRJ", placeholder="Ex: 2024.001.002")
        
    endereco = st.text_input("Endereço da Denúncia", placeholder="Rua, Número, Bairro, Cidade - RJ")
    denuncia = st.text_area("Descrição da Ouvidoria", placeholder="Descreva aqui o teor da denúncia...")
    
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        responsavel = st.radio("Enviado por:", options=["Elias", "Matheus", "Ana Beatriz", "Sônia", "Priscila"], horizontal=True)
    with col_f2:
        consumidor_vencedor = st.radio("Consumidor vencedor?", options=["Sim", "Não"], horizontal=True)
        
    submit = st.form_submit_button("🔍 Registre a Ouvidoria", use_container_width=True)

if submit:
    if not endereco or not denuncia:
        st.error("❌ Preencha os campos obrigatórios (Endereço e Descrição)!")
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
                st.success("✅ Denúncia processada e salva no histórico!")
            except Exception as e:
                st.error(f"Erro no processamento: {e}")

# ============ 2. RESULTADO DA CLASSIFICAÇÃO ============
if st.session_state.resultado:
    st.divider()
    res = st.session_state.resultado
    st.markdown('<p class="titulo-sessao">✅ Resultado da Classificação Atual</p>', unsafe_allow_html=True)
    
    # BOX DESTAQUE: Trazendo os números de registro e dados geográficos
    st.markdown(f"""
    <div class="box-destaque">
        <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
            <span><b style="color: #960018;">Nº Comunicação:</b> {res.get('num_comunicacao', 'N/A')}</span>
            <span><b style="color: #960018;">Nº MPRJ:</b> {res.get('num_mprj', 'N/A')}</span>
        </div>
        <hr style="border: 0; border-top: 1px solid #eee; margin: 10px 0;">
        <span style="color: #960018; font-weight: bold;">📍 Município:</span> {res.get('municipio', 'Não identificado')}<br>
        <span style="color: #960018; font-weight: bold;">🏛️ Promotoria Responsável:</span> {res.get('promotoria', 'Não identificada')}
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"📧 **E-mail:** {res.get('email', 'N/A')} | 📞 **Telefone:** {res.get('telefone', 'N/A')}")
    
    c1, c2, c3 = st.columns(3)
    with c1: st.success(f"**Tema:** {res.get('tema')}")
    with c2: st.success(f"**Subtema:** {res.get('subtema')}")
    with c3: st.success(f"**Empresa:** {res.get('empresa')}")
        
    st.markdown("**Resumo da IA (Máximo 10 palavras):**")
    st.markdown(f'<div class="resumo-box">{res.get("resumo")}</div>', unsafe_allow_html=True)
    
    # Dropdown com descrição completa solicitado
    with st.expander("📄 Ver Descrição da Ouvidoria"):
        st.write(res.get('denuncia'))

    if st.button("➕ Limpar e Nova Ouvidoria", use_container_width=True):
        st.session_state.resultado = None
        st.rerun()

st.divider()

# ============ 3. REGISTRO DE OUVIDORIAS (HISTÓRICO) ============
st.markdown('<p class="titulo-sessao">📊 Histórico de Registros</p>', unsafe_allow_html=True)

if not st.session_state.historico:
    st.info("Nenhuma ouvidoria registrada no arquivo local.")
else:
    # Filtros de Busca
    c_f1, c_f2 = st.columns([3, 1])
    search = c_f1.text_input("🔍 Pesquisar por Nº, Empresa ou Texto")
    
    dados = st.session_state.historico
    if search:
        s = search.lower()
        dados = [h for h in dados if s in str(h).lower()]

    # Mostrar Mais/Menos
    mostrar_tudo = st.checkbox(f"Mostrar todos os {len(dados)} registros", value=False)
    dados_exibicao = list(reversed(dados)) if mostrar_tudo else list(reversed(dados))[:5]

    if not mostrar_tudo:
        st.caption("Exibindo os 5 registros mais recentes.")

    # Container da Tabela com Rolagem
    st.markdown('<div class="tabela-horizontal">', unsafe_allow_html=True)
    
    h_cols = st.columns([0.8, 1.2, 1.2, 1.2, 2, 1.5, 1.2, 1.2, 1.2, 1, 1])
    headers = ["Ações", "Nº Com.", "Nº MPRJ", "Data", "Denúncia", "Resumo", "Tema", "Subtema", "Empresa", "Cons. Vencedor?", "Usuário"]
    for col, nome in zip(h_cols, headers):
        col.markdown(f'<p class="header-text">{nome}</p>', unsafe_allow_html=True)
    
    st.divider()

    for idx, registro in enumerate(dados_exibicao):
        idx_orig = st.session_state.historico.index(registro)
        row = st.columns([0.8, 1.2, 1.2, 1.2, 2, 1.5, 1.2, 1.2, 1.2, 1, 1])
        
        # Botão Apagar
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

        # DETALHES COMPLETOS (Dropdown)
        with st.expander("🔽 Ver Detalhes Completos"):
            st.markdown(f"#### 🔍 Detalhes - Registro {registro.get('num_comunicacao')}")
            d_col1, d_col2 = st.columns(2)
            with d_col1:
                st.write(f"**Nº de Comunicação:** {registro.get('num_comunicacao')}")
                st.write(f"**Nº MPRJ:** {registro.get('num_mprj')}")
                st.write(f"**Data de Registro:** {registro.get('data_envio')}")
                st.write(f"**Endereço Informado:** {registro.get('endereco')}")
                st.write(f"**Município Detectado:** {registro.get('municipio')}")
            with d_col2:
                st.write(f"**Promotoria Responsável:** {registro.get('promotoria')}")
                st.write(f"**Tema:** {registro.get('tema')}")
                st.write(f"**Subtema:** {registro.get('subtema')}")
                st.write(f"**Empresa/Órgão:** {registro.get('empresa')}")
                st.write(f"**Usuário Responsável:** {registro.get('responsavel')}")
            
            # Adicionado o Resumo nos detalhes solicitado
            st.info(f"**Resumo Classificatório:** {registro.get('resumo')}")
            st.text_area("Descrição Completa da Denúncia", value=registro.get('denuncia'), height=150, key=f"text_{idx_orig}")
        
        st.markdown('<hr style="margin:0; border-top: 1px solid #f0f2f6;">', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

st.divider()
st.caption("SARO v1.0 - Sistema Automático de Registro de Ouvidorias | Ministério Público do Rio de Janeiro (Created by Matheus Pereira Barreto [62006659])")

Melhore a identação desse código
