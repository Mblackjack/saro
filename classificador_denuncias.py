# -*- coding: utf-8 -*-
"""
Classificador de Denúncias do Consumidor - SARO v5.8
Versão corrigida para máxima compatibilidade com OpenAI GPT-4o-Mini
"""

import json
import os
import unicodedata
import streamlit as st
from typing import Dict, Optional

# Garantir que a biblioteca está instalada
try:
    from openai import OpenAI
except ImportError:
    st.error("❌ Erro: Biblioteca OpenAI não instalada. Execute 'pip install openai' no terminal.")
    st.stop()

class ClassificadorDenuncias:
    def __init__(self):
        # 1. Obter chave da API
        api_key = self._obter_api_key()
        
        if not api_key:
            st.error("❌ **Chave da OpenAI não configurada nos Secrets do Streamlit!**")
            st.stop()
        
        try:
            # Inicializa o cliente oficial da OpenAI
            self.client = OpenAI(api_key=api_key)
        except Exception as e:
            st.error(f"❌ Erro ao conectar com OpenAI: {str(e)}")
            st.stop()
        
        # Define o modelo padrão (gpt-4o-mini é o melhor custo-benefício)
        self.model_name = "gpt-4o-mini"
        
        # Caminho absoluto para os JSONs
        self.base_path = os.path.dirname(os.path.abspath(__file__))
        self.carregar_bases()

    def _obter_api_key(self) -> Optional[str]:
        """Tenta obter a chave de API de múltiplas fontes"""
        if "OPENAI_API_KEY" in st.secrets:
            return st.secrets["OPENAI_API_KEY"]
        return os.getenv("OPENAI_API_KEY")

    def carregar_bases(self):
        """Carrega as bases de dados de temas, subtemas e promotorias"""
        try:
            with open(os.path.join(self.base_path, "base_temas_subtemas.json"), 'r', encoding='utf-8') as f:
                self.temas_subtemas = json.load(f)
            
            with open(os.path.join(self.base_path, "base_promotorias.json"), 'r', encoding='utf-8') as f:
                self.base_promotorias = json.load(f)
        except Exception as e:
            st.error(f"❌ Erro ao carregar bases de dados JSON: {e}")
            st.stop()
            
        self.municipio_para_promotoria = {}
        for nucleo, dados in self.base_promotorias.items():
            for municipio in dados["municipios"]:
                self.municipio_para_promotoria[municipio.upper()] = {
                    "promotoria": dados["promotoria"],
                    "email": dados.get("email", "N/A"),
                    "telefone": dados.get("telefone", "N/A"),
                    "municipio_oficial": municipio
                }

    def remover_acentos(self, texto: str) -> str:
        if not texto: return ""
        return "".join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')

    def extrair_municipio(self, endereco: str) -> Optional[str]:
        if not endereco: return None
        endereco_upper = self.remover_acentos(endereco.upper())
        
        # Busca direta no dicionário (mais rápido e grátis)
        for municipio_chave in self.municipio_para_promotoria.keys():
            if self.remover_acentos(municipio_chave) in endereco_upper:
                return self.municipio_para_promotoria[municipio_chave]["municipio_oficial"]
        
        # Fallback IA (apenas se a busca direta falhar)
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "Extraia apenas o nome da cidade deste endereço. Responda apenas o nome puro."},
                    {"role": "user", "content": endereco}
