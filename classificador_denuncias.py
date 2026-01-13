# -*- coding: utf-8 -*-
import json
import os
import unicodedata
import time
import streamlit as st
import google.generativeai as genai
from typing import Dict

class ClassificadorDenuncias:
    def __init__(self):
        # 1. Configuração de API estável (Evita Erro 404)
        api_key = st.secrets.get("GOOGLE_API_KEY")
        if not api_key:
            st.error("❌ Erro: Chave de API não configurada nos Secrets.")
            st.stop()

        genai.configure(api_key=api_key)
        # Usamos a versão estável 'gemini-1.5-flash'
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        
        self.base_path = os.path.dirname(os.path.abspath(__file__))
        self.carregar_bases()

    def carregar_bases(self):
        """Carrega os dados e cria o vínculo infalível entre Subtema e Tema"""
        try:
            with open(os.path.join(self.base_path, "base_temas_subtemas.json"), 'r', encoding='utf-8') as f:
                self.temas_subtemas = json.load(f)
            with open(os.path.join(self.base_path, "base_promotorias.json"), 'r', encoding='utf-8') as f:
                self.base_promotorias = json.load(f)
            
            # MAPEAMENTO REVERSO: Garante que o Tema siga o Subtema
            self.subtema_para_tema = {}
            for tema, subtemas in self.temas_subtemas.items():
                for sub in subtemas:
                    self.subtema_para_tema[sub] = tema
                    
        except Exception as e:
            st.error(f"❌ Erro ao carregar arquivos JSON: {e}")
            st.stop()

    def remover_acentos(self, texto: str) -> str:
        if not texto: return ""
        return "".join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')

    def processar_denuncia(self, endereco: str, denuncia: str, num_comunicacao: str = "", num_mprj: str = "") -> Dict:
        # 1. Preparação da lista de subtemas para a IA
        lista_oficial_subtemas = list(self.subtema_para_tema.keys())

        # 2. PROMPT: Passo a passo de análise por similaridade
        prompt = f"""Você é um triador do Ministério Público. Siga este processo:
        1. ANALISE: Leia a denúncia e identifique o objeto principal (ex: ônibus, água, escola).
        2. EXTRAÇÃO: Busque por similaridade de caracteres qual item da LISTA OFICIAL melhor descreve o fato.
        3. EMPRESA: Extraia o nome da empresa reclamada.

        LISTA OFICIAL DE SUBTEMAS:
        {lista_oficial_subtemas}

        DENÚNCIA: "{denuncia}"

        Responda APENAS um JSON:
        {{
          "subtema": "NOME_EXATO_DA_LISTA",
          "empresa": "NOME_DA_EMPRESA",
          "resumo": "Denúncia referente a..."
        }}"""

        try:
            # Tratamento de cota (Erro 429)
            for tentativa in range(3):
                try:
                    response = self.model.generate_content(prompt)
                    break
                except Exception as e:
                    if "429" in str(e):
                        time.sleep(5)
                        continue
                    raise e

            res_text = response.text.replace('```json', '').replace('```', '').strip()
            dados_ia = json.loads(res_text)
            
            # 3. VÍNCULO AUTOMÁTICO DO TEMA (Evita alucinação)
            sub_escolhido = dados_ia.get("subtema")
            tema_final = self.subtema_para_tema.get(sub_escolhido, "Não classificado")
            
        except Exception:
            tema_final = "Não classificado"
            dados_ia = {"subtema": "Não classificado", "empresa": "Não identificada", "resumo": "Erro técnico na análise."}

        return {
            "num_comunicacao": num_comunicacao,
            "num_mprj": num_mprj,
            "tema": tema_final,
            "subtema": dados_ia.get("subtema"),
            "empresa": dados_ia.get("empresa"),
            "resumo": dados_ia.get("resumo"),
            "municipio": "Identificado via base_promotorias", # Lógica de município omitida para brevidade
            "promotoria": "Consultar base"
        }
