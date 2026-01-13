# -*- coding: utf-8 -*-
import json
import os
import unicodedata
import streamlit as st
import google.generativeai as genai
from typing import Dict, Optional

class ClassificadorDenuncias:
    def __init__(self):
        api_key = st.secrets.get("GOOGLE_API_KEY")
        if not api_key:
            st.error("❌ GOOGLE_API_KEY não configurada nos Secrets.")
            st.stop()

        genai.configure(api_key=api_key)
        
        # AJUSTE AQUI: Usando o nome completo do modelo para evitar o erro 404
        self.model = genai.GenerativeModel('gemini-1.5-flash-latest')
        
        self.base_path = os.path.dirname(os.path.abspath(__file__))
        self.carregar_bases()

    def carregar_bases(self):
        try:
            with open(os.path.join(self.base_path, "base_temas_subtemas.json"), 'r', encoding='utf-8') as f:
                self.temas_subtemas = json.load(f)
            with open(os.path.join(self.base_path, "base_promotorias.json"), 'r', encoding='utf-8') as f:
                self.base_promotorias = json.load(f)
        except Exception as e:
            st.error(f"❌ Erro ao ler bases JSON: {e}")
            st.stop()
            
        self.municipio_para_promotoria = {
            m.upper(): {"promotoria": d["promotoria"], "email": d["email"], "telefone": d["telefone"], "municipio_oficial": m}
            for nucleo, d in self.base_promotorias.items() for m in d["municipios"]
        }

    def remover_acentos(self, texto: str) -> str:
        if not texto: return ""
        return "".join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')

    def processar_denuncia(self, endereco: str, denuncia: str, num_comunicacao: str = "", num_mprj: str = "") -> Dict:
        # Lógica de Município (Local)
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

        temas_validos = ", ".join(self.temas_subtemas.keys())
        
        # PROMPT OTIMIZADO PARA GEMINI
        prompt = f"""Atue como um analista de dados. Analise a denúncia e retorne APENAS um JSON.
        LISTA DE TEMAS: {temas_validos}
        
        DENÚNCIA: "{denuncia}"
        
        JSON esperado:
        {{
          "tema": "Escolha um da lista",
          "subtema": "3 palavras sobre o problema",
          "empresa": "Nome da empresa",
          "resumo": "Denúncia referente a..."
        }}"""

        try:
            # Configuração para evitar que o filtro de segurança bloqueie palavras comuns em denúncias
            safety_settings = [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
            ]

            response = self.model.generate_content(prompt, safety_settings=safety_settings)
            
            # Limpeza de markdown da resposta do Gemini
            res_text = response.text.strip()
            if "```json" in res_text:
                res_text = res_text.split("```json")[1].split("```")[0].strip()
            elif "```" in res_text:
                res_text = res_text.split("```")[1].split("```")[0].strip()
                
            dados_ia = json.loads(res_text)
        except Exception as e:
            st.error(f"Erro detalhado na IA: {e}")
            dados_ia = {"tema": "Serviços", "subtema": "Erro no Gemini", "empresa": "Não identificada", "resumo": "Erro técnico ao processar."}

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
