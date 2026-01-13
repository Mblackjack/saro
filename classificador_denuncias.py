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
        
        # Usamos o modelo Flash de forma direta para evitar o erro 404
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        
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
            st.error(f"❌ Erro ao carregar as bases: {e}")
            st.stop()
            
        # Mapeia municípios para promotorias
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
        # Identificação de Promotoria por Município
        municipio_info = None
        end_upper = self.remover_acentos(endereco.upper())
        for m_chave, info in self.municipio_para_promotoria.items():
            if m_chave in end_upper:
                municipio_info = info
                break
        
        if not municipio_info:
            municipio_info = {"promotoria": "Não identificada", "email": "N/A", "telefone": "N/A", "municipio_oficial": "Não identificado"}

        # Criando o guia de Temas/Subtemas para a IA
        mapeamento_txt = ""
        for tema, subs in self.temas_subtemas.items():
            mapeamento_txt += f"TEMA: {tema} | SUBTEMAS POSSÍVEIS: [{', '.join(subs)}]\n"

        prompt = f"""Você é um especialista em triagem do Ministério Público. 
        Analise a denúncia: "{denuncia}"
        
        REGRAS:
        1. Classifique usando APENAS a lista oficial abaixo.
        2. O subtema escolhido DEVE obrigatoriamente pertencer ao tema escolhido.
        
        LISTA OFICIAL:
        {mapeamento_txt}
        
        Retorne APENAS um JSON:
        {{"tema": "TEMA ESCOLHIDO", "subtema": "SUBTEMA ESCOLHIDO", "empresa": "NOME DA EMPRESA OU NÃO IDENTIFICADA", "resumo": "RESUMO CURTO"}}"""

        # Resposta padrão em caso de falha (evita o "A definir")
        resultado_final = {
            "num_comunicacao": num_comunicacao, "num_mprj": num_mprj,
            "endereco": endereco, "denuncia": denuncia,
            "municipio": municipio_info["municipio_oficial"],
            "promotoria": municipio_info["promotoria"],
            "email": municipio_info["email"],
            "telefone": municipio_info["telefone"],
            "tema": "Pendente de Classificação",
            "subtema": "Pendente de Classificação",
            "empresa": "Não identificada",
            "resumo": "A IA não conseguiu processar este texto no momento."
        }

        try:
            response = self.model.generate_content(prompt)
            # Limpa e converte o JSON da IA
            res_text = response.text.replace('```json', '').replace('```', '').strip()
            dados_ia = json.loads(res_text)
            
            resultado_final.update({
                "tema": dados_ia.get("tema"),
                "subtema": dados_ia.get("subtema"),
                "empresa": dados_ia.get("empresa"),
                "resumo": dados_ia.get("resumo")
            })
        except Exception as e:
            st.warning(f"⚠️ A IA está temporariamente indisponível (Erro 404). Tente novamente em instantes.")

        return resultado_final
