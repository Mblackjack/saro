import json
import os
import unicodedata
import streamlit as st
import google.generativeai as genai
from typing import Dict

class ClassificadorDenuncias:
    def __init__(self):
        api_key = st.secrets.get("GOOGLE_API_KEY")
        if not api_key:
            st.error("❌ GOOGLE_API_KEY não configurada.")
            st.stop()

        genai.configure(api_key=api_key)
        
        # Tentativa sequencial de modelos para evitar o erro 404
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
        # Busca Município/Promotoria (Como na imagem que você enviou)
        municipio_info = None
        end_upper = self.remover_acentos(endereco.upper())
        for m_chave, info in self.municipio_para_promotoria.items():
            if m_chave in end_upper:
                municipio_info = info
                break
        
        if not municipio_info:
            municipio_info = {"promotoria": "Não identificada", "email": "N/A", "telefone": "N/A", "municipio_oficial": "Não identificado"}

        # Hierarquia de Temas para evitar subtemas errados
        mapeamento_txt = ""
        for tema, subs in self.temas_subtemas.items():
            mapeamento_txt += f"- TEMA: {tema} | SUBTEMAS: {', '.join(subs)}\n"

        prompt = f"""Analise a denúncia: "{denuncia}"
        Use apenas esta lista:
        {mapeamento_txt}
        
        Responda APENAS um JSON:
        {{"tema": "...", "subtema": "...", "empresa": "...", "resumo": "..."}}"""

        resultado_final = {
            "num_comunicacao": num_comunicacao, "num_mprj": num_mprj,
            "endereco": endereco, "denuncia": denuncia,
            "municipio": municipio_info["municipio_oficial"],
            "promotoria": municipio_info["promotoria"],
            "email": municipio_info["email"],
            "telefone": municipio_info["telefone"],
            "tema": "Não classificado", "subtema": "Não classificado",
            "empresa": "Não identificada", "resumo": "Erro na análise da IA"
        }

        try:
            # Chamada principal
            response = self.model.generate_content(prompt)
            txt = response.text.replace('```json', '').replace('```', '').strip()
            dados_ia = json.loads(txt)
            resultado_final.update(dados_ia)
        except:
            pass # Mantém o resultado_final padrão se a IA falhar

        return resultado_final
