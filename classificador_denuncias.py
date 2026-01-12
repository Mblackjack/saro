# -*- coding: utf-8 -*-
"""
Classificador de Denúncias do Consumidor - SARO v4.2
Versão Corrigida para Produção (Streamlit Cloud)
"""

import json
import os
import re
import unicodedata
import streamlit as st
from typing import Dict, List, Optional
from openai import OpenAI

class ClassificadorDenuncias:
    def __init__(self):
        # SEGURANÇA: Busca a chave nos Secrets do Streamlit ou variáveis de ambiente
        # Isso resolve o erro '401 - Incorrect API key'
        api_key = st.secrets.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
        
        if not api_key:
            st.error("ERRO CRÍTICO: Chave da OpenAI (OPENAI_API_KEY) não configurada nos Secrets do Streamlit.")
            st.stop()

        self.client = OpenAI(api_key=api_key)
        
        # PORTABILIDADE: Define o caminho baseado na localização atual do arquivo
        # Isso resolve o erro 'FileNotFoundError' no Streamlit Cloud
        self.base_path = os.path.dirname(os.path.abspath(__file__))
        
        self.carregar_bases()

    def carregar_bases(self):
        """Carrega as bases de dados de temas, subtemas e promotorias de forma dinâmica"""
        caminho_temas = os.path.join(self.base_path, "base_temas_subtemas.json")
        caminho_promotorias = os.path.join(self.base_path, "base_promotorias.json")

        # Verifica a existência dos arquivos antes de tentar carregar
        if not os.path.exists(caminho_temas) or not os.path.exists(caminho_promotorias):
            st.error(f"ERRO: Arquivos JSON não encontrados em: {self.base_path}")
            st.stop()

        try:
            with open(caminho_temas, 'r', encoding='utf-8') as f:
                self.temas_subtemas = json.load(f)
            
            with open(caminho_promotorias, 'r', encoding='utf-8') as f:
                self.base_promotorias = json.load(f)
        except Exception as e:
            st.error(f"Erro ao ler arquivos JSON: {str(e)}")
            st.stop()
            
        # Criar mapeamento direto de município para dados da promotoria
        self.municipio_para_promotoria = {}
        for nucleo, dados in self.base_promotorias.items():
            for municipio in dados["municipios"]:
                self.municipio_para_promotoria[municipio.upper()] = {
                    "promotoria": dados["promotoria"],
                    "email": dados["email"],
                    "telefone": dados["telefone"],
                    "municipio_oficial": municipio
                }

    def remover_acentos(self, texto: str) -> str:
        """Remove acentos de uma string para facilitar a busca"""
        if not texto: return ""
        return "".join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')

    def extrair_municipio(self, endereco: str) -> Optional[str]:
        """Extrai o município usando busca direta ou fallback com gpt-4o-mini"""
        if not endereco: return None
        
        endereco_upper = self.remover_acentos(endereco.upper())
        
        # Busca direta no dicionário de municípios
        for municipio_chave in self.municipio_para_promotoria.keys():
            municipio_chave_sem_acento = self.remover_acentos(municipio_chave)
            if municipio_chave_sem_acento in endereco_upper:
                return self.municipio_para_promotoria[municipio_chave]["municipio_oficial"]
        
        # Fallback com modelo correto (gpt-4o-mini)
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Você é um assistente que extrai nomes de cidades de endereços brasileiros. Responda APENAS com o nome da cidade, sem explicações."},
                    {"role": "user", "content": f"Qual é a cidade neste endereço? '{endereco}'"}
                ],
                temperature=0.3,
                max_tokens=50
            )
            municipio_extraido = response.choices[0].message.content.strip().upper()
            municipio_extraido_sem_acento = self.remover_acentos(municipio_extraido)
            
            for municipio_chave in self.municipio_para_promotoria.keys():
                if self.remover_acentos(municipio_chave) == municipio_extraido_sem_acento:
                    return self.municipio_para_promotoria[municipio_chave]["municipio_oficial"]
        except Exception:
            pass
        
        return None

    def gerar_resumo(self, denuncia: str) -> str:
        """Gera um resumo conciso da denúncia usando gpt-4o-mini"""
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Você é um assistente que cria resumos concisos de denúncias. Responda com UMA ÚNICA FRASE começando com 'Denúncia referente a'. Máximo 15 palavras."},
                    {"role": "user", "content": f"Resuma esta denúncia: {denuncia}"}
                ],
                temperature=0.3,
                max_tokens=50
            )
            return response.choices[0].message.content.strip()
        except Exception:
            return "Denúncia referente a reclamação do consumidor."

    def classificar_denuncia(self, denuncia: str) -> Dict:
        """Classifica a denúncia retornando obrigatoriamente um objeto JSON"""
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": """Você é um classificador de denúncias. Analise a denúncia e retorne um JSON com:
                    - tema: Alimentação, Comércio, Educação, Finanças, Habitação, Informações, Lazer, Produtos, Saúde, Serviços, Telecomunicações ou Transporte
                    - subtema: O subtema específico dentro do tema
                    - empresa: Nome da empresa mencionada (ou "Não identificada")
                    
                    Responda APENAS com o JSON puro."""},
                    {"role": "user", "content": f"Classifique: {denuncia}"}
                ],
                response_format={"type": "json_object"}, # Garante retorno em JSON
                temperature=0.3
            )
            
            content = response.choices[0].message.content.strip()
            return json.loads(content)
            
        except Exception:
            return {
                "tema": "Serviços",
                "subtema": "Não classificado",
                "empresa": "Não identificada"
            }

    def processar_denuncia(self, endereco: str, denuncia: str, num_comunicacao: str = "", num_mprj: str = "") -> Dict:
        """Fluxo completo de processamento e inteligência da denúncia"""
        municipio = self.extrair_municipio(endereco)
        
        if municipio and municipio.upper() in self.municipio_para_promotoria:
            promotoria_info = self.municipio_para_promotoria[municipio.upper()]
        else:
            promotoria_info = {
                "promotoria": "Promotoria não identificada",
                "email": "N/A",
                "telefone": "N/A",
                "municipio_oficial": municipio or "Não identificado"
            }
        
        classificacao = self.classificar_denuncia(denuncia)
        resumo = self.gerar_resumo(denuncia)
        
        return {
            "num_comunicacao": num_comunicacao or "N/A",
            "num_mprj": num_mprj or "N/A",
            "endereco": endereco,
            "denuncia": denuncia,
            "municipio": promotoria_info.get("municipio_oficial", "Não identificado"),
            "promotoria": promotoria_info.get("promotoria", "Promotoria não identificada"),
            "email": promotoria_info.get("email", "N/A"),
            "telefone": promotoria_info.get("telefone", "N/A"),
            "tema": classificacao.get("tema", "Serviços"),
            "subtema": classificacao.get("subtema", "Não classificado"),
            "empresa": classificacao.get("empresa", "Não identificada"),
            "resumo": resumo
        }
