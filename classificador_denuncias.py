import json
import os
import unicodedata
import streamlit as st
import google.generativeai as genai
from typing import Dict, Optional

class ClassificadorDenuncias:
    def __init__(self):
        # Busca a chave nos Secrets do Streamlit
        api_key = st.secrets.get("GOOGLE_API_KEY")
        if not api_key:
            st.error("❌ GOOGLE_API_KEY não configurada nos Secrets.")
            st.stop()

        genai.configure(api_key=api_key)
        
        # AJUSTE FINAL: Nome absoluto do modelo para compatibilidade total
        self.model_name = 'models/gemini-1.5-flash' 
        self.model = genai.GenerativeModel(self.model_name)
        
        self.base_path = os.path.dirname(os.path.abspath(__file__))
        self.carregar_bases()

    def carregar_bases(self):
        """Carrega os arquivos JSON de suporte."""
        try:
            with open(os.path.join(self.base_path, "base_temas_subtemas.json"), 'r', encoding='utf-8') as f:
                self.temas_subtemas = json.load(f)
            with open(os.path.join(self.base_path, "base_promotorias.json"), 'r', encoding='utf-8') as f:
                self.base_promotorias = json.load(f)
        except Exception as e:
            st.error(f"❌ Erro ao carregar as bases JSON: {e}")
            st.stop()
            
        # Mapeia municípios para promotorias
        self.municipio_para_promotoria = {
            m.upper(): {
                "promotoria": d["promotoria"], 
                "email": d["email"], 
                "telefone": d["telefone"], 
                "municipio_oficial": m
            }
            for nucleo, d in self.base_promotorias.items() for m in d["municipios"]
        }

    def remover_acentos(self, texto: str) -> str:
        """Remove acentuação para facilitar a busca por município."""
        if not texto: return ""
        return "".join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')

    def processar_denuncia(self, endereco: str, denuncia: str, num_comunicacao: str = "", num_mprj: str = "") -> Dict:
        """Processa a denúncia usando IA e identifica a promotoria local."""
        
        # 1. Identificação do Município (Baseado no Endereço)
        municipio_nome = None
        end_upper = self.remover_acentos(endereco.upper())
        for m_chave in self.municipio_para_promotoria.keys():
            if self.remover_acentos(m_chave) in end_upper:
                municipio_nome = self.municipio_para_promotoria[m_chave]["municipio_oficial"]
                break
        
        prom_info = self.municipio_para_promotoria.get(
            municipio_nome.upper() if municipio_nome else "", 
            {
                "promotoria": "Promotoria não identificada", 
                "email": "N/A", 
                "telefone": "N/A", 
                "municipio_oficial": municipio_nome or "Não identificado"
            }
        )

        # 2. Preparação da Hierarquia de Temas/Subtemas para forçar a IA
        mapeamento_txt = ""
        for tema, subtemas in self.temas_subtemas.items():
            sub_list = ", ".join(subtemas)
            mapeamento_txt += f"- TEMA: {tema} | SUBTEMAS PERMITIDOS: [{sub_list}]\n"
        
        # 3. Construção do Prompt com regras rígidas
        prompt = f"""Você é um assistente jurídico especializado em triagem de ouvidorias do Ministério Público.
Sua tarefa é classificar a denúncia abaixo seguindo RIGOROSAMENTE as listas fornecidas.

DENÚNCIA: "{denuncia}"

REGRAS CRÍTICAS:
1. Escolha UM TEMA da lista oficial.
2. Escolha UM SUBTEMA que esteja explicitamente listado DENTRO do TEMA selecionado. É PROIBIDO cruzar subtemas de temas diferentes.
3. Se a denúncia citar uma empresa, identifique-a. Caso contrário, use 'Não identificada'.
4. Escreva um resumo executivo curto (máximo 3 linhas).

LISTA DE TEMAS E SUBTEMAS PERMITIDOS:
{mapeamento_txt}

RESPONDA APENAS com um objeto JSON puro (sem comentários ou markdown):
{{
  "tema": "NOME DO TEMA",
  "subtema": "NOME DO SUBTEMA",
  "empresa": "NOME DA EMPRESA",
  "resumo": "RESUMO DA DENÚNCIA"
}}"""

        try:
            # Chamada ao Gemini
            response = self.model.generate_content(prompt)
            res_text = response.text.strip()
            
            # Limpeza de blocos de código Markdown
            if "```json" in res_text:
                res_text = res_text.split("```json")[1].split("```")[0].strip()
            elif "```" in res_text:
                res_text = res_text.split("```")[1].split("```")[0].strip()
            
            dados_ia = json.loads(res_text)
        except Exception as e:
            st.error(f"⚠️ Erro na análise da IA: {e}")
            dados_ia = {
                "tema": "Não identificado", 
                "subtema": "Não identificado", 
                "empresa": "Não identificada", 
                "resumo": "Falha ao processar a descrição da denúncia."
            }

        return {
            "num_comunicacao": num_comunicacao,
            "num_mprj": num_mprj,
            "endereco": endereco,
            "denuncia": denuncia,
            "municipio": prom_info["municipio_oficial"],
            "promotoria": prom_info["promotoria"],
            "email": prom_info["email"],
            "telefone": prom_info["telefone"],
            "tema": dados_ia.get("tema", "Não identificado"),
            "subtema": dados_ia.get("subtema", "Não identificado"),
            "empresa": dados_ia.get("empresa", "Não identificada"),
            "resumo": dados_ia.get("resumo", "Resumo indisponível")
        }
