# -*- coding: utf-8 -*-
import json
import os
import unicodedata
import streamlit as st
import google.generativeai as genai
from typing import Dict, Optional

class ClassificadorDenuncias:
    def __init__(self):
        # 1. Recupera a chave do Google nos Secrets
        api_key = st.secrets.get("GOOGLE_API_KEY")
        
        if not api_key:
            st.error("❌ ERRO: GOOGLE_API_KEY não encontrada nos Secrets do Streamlit.")
            st.stop()

        # Configura o Gemini
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        
        self.base_path = os.path.dirname(os.path.abspath(__file__))
        self.carregar_bases()

    def carregar_bases(self):
        """Carrega as bases de dados locais"""
        try:
            with open(os.path.join(self.base_path, "base_temas_subtemas.json"), 'r', encoding='utf-8') as f:
                self.temas_subtemas = json.load(f)
            with open(os.path.join(self.base_path, "base_promotorias.json"), 'r', encoding='utf-8') as f:
                self.base_promotorias = json.load(f)
        except Exception as e:
            st.error(f"❌ Erro ao ler bases JSON: {e}")
            st.stop()
            
        self.municipio_para_promotoria = {}
        for nucleo, dados in self.base_promotorias.items():
            for municipio in dados["municipios"]:
                self.municipio_para_promotoria[municipio.upper()] = {
                    "promotoria": dados["promotoria"], "email": dados["email"],
                    "telefone": dados["telefone"], "municipio_oficial": municipio
                }

    def remover_acentos(self, texto: str) -> str:
        if not texto: return ""
        return "".join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')

    def processar_denuncia(self, endereco: str, denuncia: str, num_comunicacao: str = "", num_mprj: str = "") -> Dict:
        # Identificação de Município (Lógica local)
        municipio_nome = None
        end_upper = self.remover_acentos(endereco.upper())
        for m_chave in self.municipio_para_promotoria.keys():
            if self.remover_acentos(m_chave) in end_upper:
                municipio_nome = self.municipio_para_promotoria[m_chave]["municipio_oficial"]
                break
        
        promotoria_info = self.municipio_para_promotoria.get(
            municipio_nome.upper() if municipio_nome else "", 
            {"promotoria": "Promotoria não identificada", "email": "N/A", "telefone": "N/A", "municipio_oficial": municipio_nome or "Não identificado"}
        )

        # Preparação dos Temas
        temas_validos = ", ".join(self.temas_subtemas.keys())
        
        prompt = f"""Analise esta denúncia do consumidor e extraia os dados estritamente em formato JSON.
        LISTA DE TEMAS: {temas_validos}
        
        DENÚNCIA: "{denuncia}"
        
        Responda apenas com o JSON contendo:
        {{
          "tema": "Escolha um da lista",
          "subtema": "Resumo do problema em 3 palavras",
          "empresa": "Nome da empresa reclamada",
          "resumo": "Frase curta começando com 'Denúncia referente a'"
        }}"""

        try:
            # Chamada ao Gemini
            response = self.model.generate_content(prompt)
            # Limpa a resposta para garantir que seja um JSON puro
            texto_resposta = response.text.replace('```json', '').replace('```', '').strip()
            dados_ia = json.loads(texto_resposta)
        except Exception as e:
            st.warning(f"Aviso: IA em modo de segurança. Detalhe: {e}")
            dados_ia = {"tema": "Serviços", "subtema": "Análise Pendente", "empresa": "Não identificada", "resumo": "Processamento local."}

        return {
            "num_comunicacao": num_comunicacao, "num_mprj": num_mprj,
            "endereco": endereco, "denuncia": denuncia,
            "municipio": promotoria_info["municipio_oficial"],
            "promotoria": promotoria_info["promotoria"],
            "email": promotoria_info["email"],
            "telefone": promotoria_info["telefone"],
            "tema": dados_ia.get("tema", "Serviços"),
            "subtema": dados_ia.get("subtema", "Análise Pendente"),
            "empresa": dados_ia.get("empresa", "Não identificada"),
            "resumo": dados_ia.get("resumo", "Resumo indisponível")
        }
