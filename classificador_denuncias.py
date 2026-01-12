# -*- coding: utf-8 -*-
"""
Classificador de Denúncias do Consumidor - SARO v5.0
Versão Otimizada com Cadeia de Pensamento para Máxima Precisão
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
        # SEGURANÇA: Busca a chave nos Secrets do Streamlit
        api_key = st.secrets.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
        
        if not api_key:
            st.error("ERRO CRÍTICO: Chave da OpenAI não configurada nos Secrets.")
            st.stop()

        self.client = OpenAI(api_key=api_key)
        self.base_path = os.path.dirname(os.path.abspath(__file__))
        self.carregar_bases()

    def carregar_bases(self):
        """Carrega as bases de dados de temas, subtemas e promotorias"""
        caminho_temas = os.path.join(self.base_path, "base_temas_subtemas.json")
        caminho_promotorias = os.path.join(self.base_path, "base_promotorias.json")

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
        if not texto: return ""
        return "".join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')

    def extrair_municipio(self, endereco: str) -> Optional[str]:
        """Extrai o município usando busca direta ou fallback com gpt-4o-mini"""
        if not endereco: return None
        endereco_upper = self.remover_acentos(endereco.upper())
        
        for municipio_chave in self.municipio_para_promotoria.keys():
            if self.remover_acentos(municipio_chave) in endereco_upper:
                return self.municipio_para_promotoria[municipio_chave]["municipio_oficial"]
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Você extrai nomes de cidades de endereços. Responda APENAS o nome da cidade."},
                    {"role": "user", "content": f"Cidade deste endereço: '{endereco}'"}
                ],
                temperature=0,
                max_tokens=30
            )
            municipio_extraido = response.choices[0].message.content.strip().upper()
            m_extraido_sem_acento = self.remover_acentos(municipio_extraido)
            
            for municipio_chave in self.municipio_para_promotoria.keys():
                if self.remover_acentos(municipio_chave) == m_extraido_sem_acento:
                    return self.municipio_para_promotoria[municipio_chave]["municipio_oficial"]
        except: pass
        return None

    def gerar_resumo(self, denuncia: str) -> str:
        """Gera um resumo técnico e conciso"""
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Você é um triador do Ministério Público. Resuma a denúncia em no máximo 15 palavras, começando com 'Denúncia referente a...'."},
                    {"role": "user", "content": denuncia}
                ],
                temperature=0.2
            )
            return response.choices[0].message.content.strip()
        except:
            return "Denúncia referente a reclamação do consumidor."

    def classificar_denuncia(self, denuncia: str) -> Dict:
        """Classifica a denúncia usando instruções reforçadas"""
        try:
            lista_temas = ", ".join(self.temas_subtemas.keys())
            
            # PROMPT REFORÇADO: Instruímos a IA a pensar antes de responder
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": f"""Você é um analista jurídico do MPRJ. 
                    Analise a denúncia passo a passo:
                    1. Identifique qual empresa está sendo acusada.
                    2. Identifique o problema central.
                    3. Escolha o TEMA estritamente desta lista: {lista_temas}.
                    
                    Responda obrigatoriamente em formato JSON com as chaves: 
                    "tema", "subtema", "empresa"."""},
                    {"role": "user", "content": f"Denúncia: {denuncia}"}
                ],
                response_format={"type": "json_object"},
                temperature=0.1
            )
            
            resultado = json.loads(response.choices[0].message.content)
            
            # Garantia de que os campos não venham vazios
            return {
                "tema": resultado.get("tema", "Serviços"),
                "subtema": resultado.get("subtema", "Não identificado"),
                "empresa": resultado.get("empresa", "Não identificada")
            }
        except Exception:
            return {"tema": "Serviços", "subtema": "Erro na análise", "empresa": "Não identificada"}

    def processar_denuncia(self, endereco: str, denuncia: str, num_comunicacao: str = "", num_mprj: str = "") -> Dict:
        """Processa a denúncia completa combinando extrações manuais e IA"""
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
        
        # Consolidação final dos dados
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
