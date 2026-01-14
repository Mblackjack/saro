# -*- coding: utf-8 -*-
"""
SARO v6.0 - Sistema Automático de Registro de Ouvidorias
Interface Web com Tabela Responsiva e Dropdown de Detalhes
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

# CSS customizado para Tabela e Responsividade
st.markdown("""
<style>
    .resumo-box {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid #1f77b4;
    }
    /* Container com rolagem horizontal */
    .tabela-horizontal {
        overflow-x: auto;
        width: 100%;
        border: 1px solid #e6e9ef;
        border-radius: 8px;
    }
    /* Estilização das "linhas" da tabela */
    .row-style {
        padding: 10px;
        border-bottom: 1px solid #f0f2f6;
        transition: background-color 0.3s;
    }
    .row-style:hover {
        background-color: #f8f9fb;
    }
    .header-style {
        background-color: #f0f2f6;
        font-weight: bold;
        padding: 10px;
        border-radius: 8px 8px 0 0;
    }
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
st.markdown("**Versão 6.0** | Classificação automática e Gestão de Dados")
st.divider()

# Inicializar classificador
try:
    classificador = ClassificadorDenuncias()
except Exception as e:
    st.error(f"Erro ao carregar classificador: {e}")
    st.stop()

# ============ 1. FORMULÁRIO DE OUVIDORIA ============
with st.form("form_ouvidoria", clear_on_submit=True):
    st.markdown("### 📝 Formulário de Ouvidoria")
    
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
        
    submit = st.form_submit_button("🔍 Processar Ouvidoria", use_container_width=True, type="primary")

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
    st.markdown("### ✅ Resultado da Classificação")
    
    col_r1, col_r2 = st.columns(2)
    with col_r1:
        st.info(f"**Nº Comunicação:** {res['num_comunicacao']}")
    with col_r2:
        st.info(f"**Nº MPRJ:** {res['num_mprj']}")
    
    # Exibição da Promotoria e Município como solicitado
    st.info(f"📍 **Município:** {res['municipio']}\n\n🏛️ **Promotoria Responsável:** {res['promotoria']}")
    st.markdown(f"📧 **E-mail:** {res['email']} | 📞 **Telefone:** {res['telefone']}")
    
    c1, c2, c3 = st.columns(3)
    with c1:
        st.success(f"**Tema:** {res['tema']}")
    with c2:
        st.success(f"**Subtema:** {res['subtema']}")
    with c3:
        st.success(f"**Empresa:** {res['empresa']}")
        
    st.markdown("**Resumo da Ouvidoria:**")
    st.markdown(f'<div class="resumo-box">{res["resumo"]}</div>', unsafe_allow_html=True)
    
    if st.button("➕ Nova Ouvidoria", use_container_width=True):
        st.session_state.resultado = None
        st.rerun()

st.divider()

# ============ 3. REGISTRO DE OUVIDORIAS (TABELA COMPLETA) ============
st.markdown("### 📊 Registro de Ouvidorias")

if not st.session_state.historico:
    st.info("Nenhuma ouvidoria registrada.")
else:
    # Filtros
    c_f1, c_f2 = st.columns([3, 1])
    search = c_f1.text_input("🔍 Buscar no histórico (Nº, Empresa, Descrição...)")
    filtro_tema = c_f2.selectbox("Filtrar Tema", ["Todos"] + sorted(list(set(h['tema'] for h in st.session_state.historico))))

    dados = st.session_state.historico
    if search:
        s = search.lower()
        dados = [h for h in dados if s in str(h).lower()]
    if filtro_tema != "Todos":
        dados = [h for h in dados if h['tema'] == filtro_tema]

    # Botão Mostrar Mais / Menos
    total_registros = len(dados)
    limite = 5
    mostrar_tudo = st.checkbox(f"Mostrar todos os {total_registros} registros", value=False)
    
    if not mostrar_tudo:
        dados_exibicao = list(reversed(dados))[:limite]
        st.caption(f"Exibindo os {limite} mais recentes.")
    else:
        dados_exibicao = list(reversed(dados))

    # --- INÍCIO DA TABELA COM ROLAGEM ---
    st.markdown('<div class="tabela-horizontal">', unsafe_allow_html=True)
    
    # Cabeçalho da Tabela
    # Ordem: Ver/Apagar, Nº Com, Nº MPRJ, Data, Denúncia, Resumo, Tema, Subtema, Empresa, Consumidor Vencedor, Enviado por
    h_cols = st.columns([0.8, 1.2, 1.2, 1.2, 2, 1.5, 1.2, 1.2, 1.2, 1, 1])
    headers = ["Ações", "Nº Com.", "Nº MPRJ", "Data Envio", "Denúncia", "Resumo", "Tema", "Subtema", "Empresa", "Vencedor?", "Usuário"]
    for col, nome in zip(h_cols, headers):
        col.markdown(f"**{nome}**")
    
    st.divider()

    for idx, registro in enumerate(dados_exibicao):
        idx_orig = st.session_state.historico.index(registro)
        
        # Linha de dados
        row = st.columns([0.8, 1.2, 1.2, 1.2, 2, 1.5, 1.2, 1.2, 1.2, 1, 1])
        
        # Coluna Ações (Apagar)
        if row[0].button("🗑️", key=f"del_{idx_orig}"):
            st.session_state.historico.pop(idx_orig)
            with open(historico_file, 'w', encoding='utf-8') as f:
                json.dump(st.session_state.historico, f, ensure_ascii=False, indent=2)
            st.rerun()
            
        row[1].write(registro.get('num_comunicacao', 'N/A'))
        row[2].write(registro.get('num_mprj', 'N/A'))
        row[3].write(registro.get('data_envio', 'N/A'))
        
        # Preview da denúncia (curto)
        denuncia_curta = (registro.get('denuncia', '')[:30] + '...') if len(registro.get('denuncia', '')) > 30 else registro.get('denuncia', '')
        row[4].write(denuncia_curta)
        
        row[5].write(registro.get('resumo', 'N/A'))
        row[6].write(registro.get('tema', 'N/A'))
        row[7].write(registro.get('subtema', 'N/A'))
        row[8].write(registro.get('empresa', 'N/A'))
        row[9].write(registro.get('consumidor_vencedor', 'N/A'))
        row[10].write(registro.get('responsavel', 'N/A'))

        # DROPDOWN "VER" (Detalhes da Ouvidoria)
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
                st.write(f"**Enviado por:** {registro.get('responsavel')}")
            
            st.text_area("Descrição Completa", value=registro.get('denuncia'), height=150, key=f"text_{idx_orig}")
        
        st.markdown('<hr style="margin:0; border-top: 1px solid #f0f2f6;">', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

st.divider()
st.caption("SARO v6.0 - Sistema Automático de Registro de Ouvidorias | MPRJ")
