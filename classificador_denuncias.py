import json
import os
import unicodedata
import streamlit as st
import google.generativeai as genai
from typing import Dict

class ClassificadorDenuncias:
    def __init__(self):
        # 1. Configuração da API
        api_key = st.secrets.get("GOOGLE_API_KEY")
        if not api_key:
            st.error("❌ GOOGLE_API_KEY não configurada nos Secrets.")
            st.stop()

        # Configuração Direta para evitar v1beta
        genai.configure(api_key=api_key)
        
        # AJUSTE DEFINITIVO: Tentando inicializar o modelo de forma simples
        # Se o gemini-pro falhar, ele tentará o gemini-1.5-flash como backup
        try:
            self.model = genai.GenerativeModel('gemini-1.5-flash')
        except:
            self.model = genai.GenerativeModel('gemini-pro')
            
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
            
        self.municipio_para_promotoria = {}
        for d in self.base_promotorias.values():
            for m in d.get("municipios", []):
                self.municipio_para_promotoria[self.remover_acentos(m.upper())] = {
                    "promotoria": d["promotoria"],
                    "email": d["email"],
                    "telefone": d["telefone"],
                    "municipio_oficial": m
                }

    def remover_acentos(self, texto: str) -> str:
        if not texto: return ""
        return "".join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')

    def processar_denuncia(self, endereco: str, denuncia: str, num_comunicacao: str = "", num_mprj: str = "") -> Dict:
        # Identificação de Promotoria (Funcionando conforme imagem)
        municipio_info = None
        end_upper = self.remover_acentos(endereco.upper())
        for m_chave, info in self.municipio_para_promotoria.items():
            if m_chave in end_upper:
                municipio_info = info
                break
        
        if not municipio_info:
            municipio_info = {"promotoria": "Não identificada", "email": "N/A", "telefone": "N/A", "municipio_oficial": "Não identificado"}

        # Mapeamento de Temas/Subtemas para a IA
        mapeamento_txt = ""
        for tema, subs in self.temas_subtemas.items():
            mapeamento_txt += f"- TEMA: {tema} | SUBTEMAS: {', '.join(subs)}\n"

        prompt = f"""Analise a denúncia e classifique em TEMA e SUBTEMA da lista oficial.
        LISTA:
        {mapeamento_txt}
        
        DENÚNCIA: "{denuncia}"
        
        Retorne APENAS um JSON:
        {{"tema": "...", "subtema": "...", "empresa": "...", "resumo": "..."}}"""

        # Resposta de fallback (que você viu na imagem como 'A definir')
        resultado_final = {
            "num_comunicacao": num_comunicacao, "num_mprj": num_mprj,
            "endereco": endereco, "denuncia": denuncia,
            "municipio": municipio_info["municipio_oficial"],
            "promotoria": municipio_info["promotoria"],
            "email": municipio_info["email"],
            "telefone": municipio_info["telefone"],
            "tema": "A definir", "subtema": "A definir",
            "empresa": "Não identificada", "resumo": "Aguardando processamento"
        }

        try:
            # A chamada generate_content pode aceitar a versão da API em algumas versões do SDK
            response = self.model.generate_content(prompt)
            res_text = response.text.strip()
            
            if "```json" in res_text:
                res_text = res_text.split("```json")[1].split("```")[0].strip()
            
            dados_ia = json.loads(res_text)
            resultado_final.update({
                "tema": dados_ia.get("tema", "Não identificado"),
                "subtema": dados_ia.get("subtema", "Não identificado"),
                "empresa": dados_ia.get("empresa", "Não identificada"),
                "resumo": dados_ia.get("resumo", "Resumo indisponível")
            })
        except Exception as e:
            st.error(f"⚠️ Erro de API: {e}")

        return resultado_final
