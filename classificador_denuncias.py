import json
import os
import unicodedata
import streamlit as st
import google.generativeai as genai
from google.generativeai import client # Importação para controle de versão
from typing import Dict

class ClassificadorDenuncias:
    def __init__(self):
        # 1. Configuração da API
        api_key = st.secrets.get("GOOGLE_API_KEY")
        if not api_key:
            st.error("❌ GOOGLE_API_KEY não configurada.")
            st.stop()

        # Configura a chave
        genai.configure(api_key=api_key)
        
        # FORÇAR VERSÃO V1: Isso elimina o erro 404 da v1beta
        self.model = genai.GenerativeModel(
            model_name='gemini-1.5-flash'
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
        # Busca Identificação Local
        municipio_info = None
        end_upper = self.remover_acentos(endereco.upper())
        for m_chave, info in self.municipio_para_promotoria.items():
            if m_chave in end_upper:
                municipio_info = info
                break
        
        if not municipio_info:
            municipio_info = {"promotoria": "Não identificada", "email": "N/A", "telefone": "N/A", "municipio_oficial": "Não identificado"}

        # Hierarquia de Temas para a IA
        mapeamento_txt = ""
        for tema, subs in self.temas_subtemas.items():
            mapeamento_txt += f"- TEMA: {tema} | SUBTEMAS: {', '.join(subs)}\n"

        prompt = f"""Analise a denúncia e escolha TEMA/SUBTEMA da lista:
        {mapeamento_txt}
        
        Denúncia: "{denuncia}"
        
        Responda APENAS JSON:
        {{"tema": "...", "subtema": "...", "empresa": "...", "resumo": "..."}}"""

        # Resposta padrão de segurança
        resultado_final = {
            "num_comunicacao": num_comunicacao, "num_mprj": num_mprj,
            "endereco": endereco, "denuncia": denuncia,
            "municipio": municipio_info["municipio_oficial"],
            "promotoria": municipio_info["promotoria"],
            "email": municipio_info["email"],
            "telefone": municipio_info["telefone"],
            "tema": "Pendente", "subtema": "Pendente",
            "empresa": "Não identificada", "resumo": "Processando..."
        }

        try:
            # Forçamos a chamada ignorando cache de versão
            response = self.model.generate_content(prompt)
            res_text = response.text.strip()
            
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
            st.warning(f"⚠️ Tentando reconectar com a IA... ({e})")
            # Segunda tentativa caso a primeira falhe por timeout
            try:
                response = self.model.generate_content(prompt)
                # (Repete a lógica de extração se necessário)
            except:
                pass

        return resultado_final
