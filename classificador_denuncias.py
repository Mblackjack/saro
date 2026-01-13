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
        # 1. Configuração da API
        api_key = st.secrets.get("GOOGLE_API_KEY")
        if not api_key:
            st.error("❌ GOOGLE_API_KEY não configurada.")
            st.stop()

        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        
        self.base_path = os.path.dirname(os.path.abspath(__file__))
        self.carregar_bases()

    def carregar_bases(self):
        """Carrega as bases e cria o mapeamento reverso para o Tema"""
        try:
            with open(os.path.join(self.base_path, "base_temas_subtemas.json"), 'r', encoding='utf-8') as f:
                self.temas_subtemas = json.load(f)
            with open(os.path.join(self.base_path, "base_promotorias.json"), 'r', encoding='utf-8') as f:
                self.base_promotorias = json.load(f)
            
            # MAPEAMENTO REVERSO: Se a IA achar o Subtema, o Python acha o Tema.
            self.subtema_para_tema = {}
            for tema, subtemas in self.temas_subtemas.items():
                for sub in subtemas:
                    self.subtema_para_tema[sub] = tema
                    
            # Mapeamento de municípios para promotorias
            self.municipio_para_promotoria = {}
            for nucleo, d in self.base_promotorias.items():
                for m in d.get("municipios", []):
                    self.municipio_para_promotoria[self.remover_acentos(m.upper())] = {
                        "promotoria": d["promotoria"],
                        "email": d["email"],
                        "telefone": d["telefone"],
                        "municipio_oficial": m
                    }
        except Exception as e:
            st.error(f"❌ Erro ao carregar bases: {e}")
            st.stop()

    def remover_acentos(self, texto: str) -> str:
        if not texto: return ""
        return "".join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')

    def processar_denuncia(self, endereco: str, denuncia: str, num_comunicacao: str = "", num_mprj: str = "") -> Dict:
        # 1. Identificação Geográfica
        municipio_info = {"promotoria": "Não identificada", "email": "N/A", "telefone": "N/A", "municipio_oficial": "Não identificado"}
        end_limpo = self.remover_acentos(endereco.upper())
        for m_chave, info in self.municipio_para_promotoria.items():
            if m_chave in end_limpo:
                municipio_info = info
                break

        # 2. Preparação do Prompt focado em SUBTEMA (Evita Alucinação)
        todos_subtemas = list(self.subtema_para_tema.keys())
        prompt = f"""Analise a denúncia e identifique o SUBTEMA EXATO da lista oficial.
        
        REGRAS:
        1. Escolha o SUBTEMA por similaridade de caracteres (Ex: se citar 'ônibus', escolha 'Ônibus').
        2. Use APENAS itens desta lista: {todos_subtemas}
        
        DENÚNCIA: "{denuncia}"

        Responda APENAS um JSON:
        {{"subtema": "NOME_DO_SUBTEMA", "empresa": "NOME_DA_EMPRESA", "resumo": "Denúncia referente a..."}}"""

        # 3. Execução com Fallback para evitar o KeyError
        # Criamos o dicionário com TODAS as chaves necessárias antes de tentar a IA
        resultado = {
            "num_comunicacao": num_comunicacao or "N/A",
            "num_mprj": num_mprj or "
