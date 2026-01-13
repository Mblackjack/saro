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

        genai.configure(api_key=api_key)
        
        # AJUSTE: Usando o nome completo do recurso para evitar o erro 404 de versão
        self.model_name = 'models/gemini-1.5-flash'
        self.model = genai.GenerativeModel(model_name=self.model_name)
        
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
        # Busca Município e Promotoria
        municipio_info = None
        end_upper = self.remover_acentos(endereco.upper())
        for m_chave, info in self.municipio_para_promotoria.items():
            if m_chave in end_upper:
                municipio_info = info
                break
        
        if not municipio_info:
            municipio_info = {"promotoria": "Não identificada", "email": "N/A", "telefone": "N/A", "municipio_oficial": "Não identificado"}

        # Hierarquia de Subtemas para a IA
        mapeamento_txt = ""
        for tema, subs in self.temas_subtemas.items():
            mapeamento_txt += f"- TEMA: {tema} | SUBTEMAS: {', '.join(subs)}\n"

        prompt = f"""Você é um classificador oficial. Analise a denúncia abaixo.
        DENÚNCIA: "{denuncia}"
        
        REGRAS:
        1. Escolha TEMA e SUBTEMA apenas da lista abaixo.
        2. O subtema deve pertencer ao tema escolhido.
        
        LISTA OFICIAL:
        {mapeamento_txt}
        
        Retorne APENAS um JSON puro:
        {{"tema": "...", "subtema": "...", "empresa": "...", "resumo": "..."}}"""

        # Objeto padrão para evitar erro de NoneType
        resultado_final = {
            "num_comunicacao": num_comunicacao, "num_mprj": num_mprj,
            "endereco": endereco, "denuncia": denuncia,
            "municipio": municipio_info["municipio_oficial"],
            "promotoria": municipio_info["promotoria"],
            "email": municipio_info["email"],
            "telefone": municipio_info["telefone"],
            "tema": "Não identificado", "subtema": "Não identificado",
            "empresa": "Não identificada", "resumo": "Erro na IA"
        }

        try:
            # Chamada da IA
            response = self.model.generate_content(prompt)
            res_text = response.text.strip()
            
            # Limpeza de Markdown
            if "```json" in res_text:
                res_text = res_text.split("```json")[1].split("```")[0].strip()
            elif "```" in res_text:
                res_text = res_text.split("```")[1].split("```")[0].strip()
            
            dados_ia = json.loads(res_text)
            resultado_final.update({
                "tema": dados_ia.get("tema", "Não identificado"),
                "subtema": dados_ia.get("subtema", "Não identificado"),
                "empresa": dados_ia.get("empresa", "Não identificada"),
                "resumo": dados_ia.get("resumo", "Resumo indisponível")
            })
        except Exception as e:
            st.warning(f"⚠️ A IA falhou, mas o registro foi criado: {e}")

        return resultado_final
