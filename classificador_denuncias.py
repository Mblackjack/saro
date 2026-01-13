# -*- coding: utf-8 -*-
import json
import os
import unicodedata
import time
import streamlit as st
import google.generativeai as genai
from typing import Dict, Optional

class ClassificadorDenuncias:
    def __init__(self):
        # 1. Configuração Robusta da API
        api_key = st.secrets.get("GOOGLE_API_KEY")
        if not api_key:
            st.error("❌ GOOGLE_API_KEY não configurada nos Secrets.")
            st.stop()

        genai.configure(api_key=api_key)
        # Usamos o 1.5-flash que é mais rápido e econômico
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        
        self.base_path = os.path.dirname(os.path.abspath(__file__))
        self.carregar_bases()

    def carregar_bases(self):
        """Carrega bases e cria mapeamento reverso para evitar alucinação"""
        try:
            with open(os.path.join(self.base_path, "base_temas_subtemas.json"), 'r', encoding='utf-8') as f:
                self.temas_subtemas = json.load(f)
            with open(os.path.join(self.base_path, "base_promotorias.json"), 'r', encoding='utf-8') as f:
                self.base_promotorias = json.load(f)
            
            # MAPEAMENTO REVERSO: Subtema -> Tema (O segredo contra alucinação)
            self.subtema_para_tema = {}
            for tema, subtemas in self.temas_subtemas.items():
                for sub in subtemas:
                    self.subtema_para_tema[sub] = tema
                    
        except Exception as e:
            st.error(f"❌ Erro ao carregar bases JSON: {e}")
            st.stop()

        # Mapeamento de municípios
        self.municipio_para_promotoria = {}
        for nucleo, dados in self.base_promotorias.items():
            for m in dados["municipios"]:
                self.municipio_para_promotoria[self.remover_acentos(m.upper())] = {
                    "promotoria": dados["promotoria"],
                    "email": dados["email"],
                    "telefone": dados["telefone"],
                    "municipio_oficial": m
                }

    def remover_acentos(self, texto: str) -> str:
        if not texto: return ""
        return "".join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')

    def processar_denuncia(self, endereco: str, denuncia: str, num_comunicacao: str = "", num_mprj: str = "") -> Dict:
        """Processo completo: Localização -> Extração -> Classificação Hierárquica"""
        
        # 1. Identificar Município/Promotoria
        municipio_info = {"promotoria": "Não identificada", "email": "N/A", "telefone": "N/A", "municipio_oficial": "Não identificado"}
        end_limpo = self.remover_acentos(endereco.upper())
        for m_chave, info in self.municipio_para_promotoria.items():
            if m_chave in end_limpo:
                municipio_info = info
                break

        # 2. Preparar lista de subtemas para a IA
        todos_subtemas = list(self.subtema_para_tema.keys())

        # PROMPT FOCO EM SUBTEMA (Evita que a IA tente 'adivinhar' categorias largas)
        prompt = f"""Analise a denúncia e identifique o SUBTEMA EXATO da lista oficial.
        
        REGRAS:
        1. Escolha o SUBTEMA por similaridade de palavras (Ex: se citar 'ônibus', escolha 'Ônibus').
        2. Use APENAS itens desta lista: {todos_subtemas}
        
        DENÚNCIA: "{denuncia}"

        Responda APENAS um JSON:
        {{"subtema": "NOME_DO_SUBTEMA", "empresa": "NOME_DA_EMPRESA", "resumo": "Denúncia referente a..."}}"""

        # 3. Chamada com tratamento de cota
        try:
            response = self.model.generate_content(prompt)
            res_text = response.text.replace('```json', '').replace('```', '').strip()
            dados_ia = json.loads(res_text)
            
            sub_escolhido = dados_ia.get("subtema")
            # O TEMA é puxado do dicionário, não da IA (Segurança total)
            tema_final = self.subtema_para_tema.get(sub_escolhido, "Serviços")
            
        except Exception as e:
            if "429" in str(e):
                st.warning("⏳ Limite de requisições atingido. Aguardando 10 segundos...")
                time.sleep(10) # Pausa para recuperar cota
            tema_final = "Serviços"
            dados_ia = {"subtema": "Não classificado", "empresa": "Não identificada", "resumo": "Erro técnico na IA."}

        return {
            "num_comunicacao": num_comunicacao or "N/A",
            "num_mprj": num_mprj or "N/A",
            "endereco": endereco,
            "denuncia": denuncia,
            "municipio": municipio_info["municipio_oficial"],
            "promotoria": municipio_info["promotoria"],
            "email": municipio_info["email"],
            "telefone": municipio_info["telefone"],
            "tema": tema_final,
            "subtema": dados_ia.get("subtema"),
            "empresa": dados_ia.get("empresa"),
            "resumo": dados_ia.get("resumo")
        }
