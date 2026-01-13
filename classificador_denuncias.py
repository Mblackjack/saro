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
        
        # Tentamos usar o modelo estável
        try:
            self.model = genai.GenerativeModel('gemini-1.5-flash')
        except:
            st.error("❌ Erro ao inicializar o modelo Gemini.")
            st.stop()
            
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
        # 1. Identificação da Promotoria
        municipio_info = None
        end_upper = self.remover_acentos(endereco.upper())
        for m_chave, info in self.municipio_para_promotoria.items():
            if m_chave in end_upper:
                municipio_info = info
                break
        
        if not municipio_info:
            municipio_info = {"promotoria": "Não identificada", "email": "N/A", "telefone": "N/A", "municipio_oficial": "Não identificado"}

        # 2. Formatação das Regras para a IA
        lista_regras = ""
        for tema, subs in self.temas_subtemas.items():
            lista_regras += f"- {tema}: {', '.join(subs)}\n"

        prompt = f"""Analise a denúncia: {denuncia}
        REGRAS:
        1. Escolha TEMA e SUBTEMA apenas da lista: {lista_regras}
        2. Responda APENAS um JSON:
        {{"tema": "...", "subtema": "...", "empresa": "...", "resumo": "..."}}"""

        # VALOR PADRÃO (Caso a IA falhe, o código não quebra)
        resultado_final = {
            "num_comunicacao": num_comunicacao,
            "num_mprj": num_mprj,
            "endereco": endereco,
            "denuncia": denuncia,
            "municipio": municipio_info["municipio_oficial"],
            "promotoria": municipio_info["promotoria"],
            "email": municipio_info["email"],
            "telefone": municipio_info["telefone"],
            "tema": "Não classificado",
            "subtema": "Não classificado",
            "empresa": "Não identificada",
            "resumo": "A IA não conseguiu processar esta denúncia no momento."
        }

        try:
            response = self.model.generate_content(prompt)
            res_text = response.text.strip()
            
            # Limpeza de Markdown
            if "```json" in res_text:
                res_text = res_text.split("```json")[1].split("```")[0].strip()
            
            dados_ia = json.loads(res_text)
            
            # Atualiza o resultado padrão com o que a IA mandou
            resultado_final.update({
                "tema": dados_ia.get("tema", "Não classificado"),
                "subtema": dados_ia.get("subtema", "Não identificado"),
                "empresa": dados_ia.get("empresa", "Não identificada"),
                "resumo": dados_ia.get("resumo", "Resumo indisponível")
            })
        except Exception as e:
            st.warning(f"⚠️ A IA falhou, mas o registro foi criado: {e}")

        return resultado_final
