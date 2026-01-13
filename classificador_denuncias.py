import json
import os
import unicodedata
import streamlit as st
import google.generativeai as genai
from google.generativeai.types import RequestOptions
from typing import Dict, Optional

class ClassificadorDenuncias:
    def __init__(self):
        # 1. Configuração da API
        api_key = st.secrets.get("GOOGLE_API_KEY")
        if not api_key:
            st.error("❌ GOOGLE_API_KEY não configurada nos Secrets.")
            st.stop()

        genai.configure(api_key=api_key)
        
        # 2. Especificação do modelo
        # Usamos o nome oficial para a versão v1
        self.model_name = 'gemini-1.5-flash' 
        
        # AJUSTE DE VERSÃO: Forçamos o uso da API v1 para evitar o erro de v1beta
        self.model = genai.GenerativeModel(
            model_name=self.model_name
        )
        
        self.base_path = os.path.dirname(os.path.abspath(__file__))
        self.carregar_bases()

    def carregar_bases(self):
        try:
            with open(os.path.join(self.base_path, "base_temas_subtemas.json"), 'r', encoding='utf-8') as f:
                self.temas_subtemas = json.load(f)
            with open(os.path.join(self.base_path, "base_promotorias.json"), 'r', encoding='utf-8') as f:
                self.base_promotorias = json.load(f)
        except Exception as e:
            st.error(f"❌ Erro nas bases JSON: {e}")
            st.stop()
            
        self.municipio_para_promotoria = {
            m.upper(): {"promotoria": d["promotoria"], "email": d["email"], "telefone": d["telefone"], "municipio_oficial": m}
            for nucleo, d in self.base_promotorias.items() for m in d["municipios"]
        }

    def remover_acentos(self, texto: str) -> str:
        if not texto: return ""
        return "".join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')

    def processar_denuncia(self, endereco: str, denuncia: str, num_comunicacao: str = "", num_mprj: str = "") -> Dict:
        # Identificação de Promotoria
        municipio_nome = None
        end_upper = self.remover_acentos(endereco.upper())
        for m_chave in self.municipio_para_promotoria.keys():
            if self.remover_acentos(m_chave) in end_upper:
                municipio_nome = self.municipio_para_promotoria[m_chave]["municipio_oficial"]
                break
        
        prom_info = self.municipio_para_promotoria.get(
            municipio_nome.upper() if municipio_nome else "", 
            {"promotoria": "Promotoria não identificada", "email": "N/A", "telefone": "N/A", "municipio_oficial": municipio_nome or "Não identificado"}
        )

        # Mapeamento para o Prompt (Subtemas dentro de Temas)
        mapeamento_txt = ""
        for tema, subtemas in self.temas_subtemas.items():
            sub_list = ", ".join(subtemas)
            mapeamento_txt += f"- TEMA: {tema} | SUBTEMAS: [{sub_list}]\n"
        
        prompt = f"""Analise a denúncia: "{denuncia}"
        
        REGRAS:
        1. Escolha um TEMA e um SUBTEMA estritamente da lista abaixo.
        2. O subtema deve pertencer ao tema escolhido.
        3. Identifique a empresa citada.
        
        LISTA OFICIAL:
        {mapeamento_txt}
        
        Responda apenas com JSON:
        {{"tema": "...", "subtema": "...", "empresa": "...", "resumo": "..."}}"""

        try:
            # Usamos request_options para garantir que não haja confusão de versão na chamada
            response = self.model.generate_content(
                prompt,
                request_options=RequestOptions(api_version='v1')
            )
            
            res_text = response.text.strip()
            if "```json" in res_text:
                res_text = res_text.split("```json")[1].split("```")[0].strip()
            elif "```" in res_text:
                res_text = res_text.split("```")[1].split("```")[0].strip()
            
            dados_ia = json.loads(res_text)
        except Exception as e:
            st.error(f"⚠️ Erro na análise da IA: {e}")
            dados_ia = {"tema": "Não classificado", "subtema": "Não classificado", "empresa": "Não identificada", "resumo": "Erro técnico."}

        return {
            "num_comunicacao": num_comunicacao, "num_mprj": num_mprj,
            "endereco": endereco, "denuncia": denuncia,
            "municipio": prom_info["municipio_oficial"],
            "promotoria": prom_info["promotoria"],
            "email": prom_info["email"],
            "telefone": prom_info["telefone"],
            "tema": dados_ia.get("tema", "Não identificado"),
            "subtema": dados_ia.get("subtema", "Não identificado"),
            "empresa": dados_ia.get("empresa", "Não identificada"),
            "resumo": dados_ia.get("resumo", "Resumo indisponível")
        }
