# -*- coding: utf-8 -*-
"""
Classificador de Denúncias do Consumidor - SARO v4.2
Melhoria na identificação de municípios e promotorias.
"""

import json
import os
import re
import unicodedata
from typing import Dict, List, Optional
from openai import OpenAI

class ClassificadorDenuncias:
    def __init__(self):
        self.client = OpenAI()
        self.base_path = "/home/ubuntu/mprj_denuncias"
        self.carregar_bases()

    def carregar_bases(self):
        """Carrega as bases de dados de temas, subtemas e promotorias"""
        with open(f"{self.base_path}/base_temas_subtemas.json", 'r', encoding='utf-8') as f:
            self.temas_subtemas = json.load(f)
        
        with open(f"{self.base_path}/base_promotorias.json", 'r', encoding='utf-8') as f:
            self.base_promotorias = json.load(f)
            
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
        """Remove acentos de uma string"""
        if not texto: return ""
        return "".join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')

    def extrair_municipio(self, endereco: str) -> Optional[str]:
        """Extrai o município do endereço fornecido usando busca textual e LLM como fallback"""
        if not endereco: return None
        
        endereco_upper = self.remover_acentos(endereco.upper())
        
        # Busca direta
        for municipio_chave in self.municipio_para_promotoria.keys():
            municipio_chave_sem_acento = self.remover_acentos(municipio_chave)
            if municipio_chave_sem_acento in endereco_upper:
                return self.municipio_para_promotoria[municipio_chave]["municipio_oficial"]
        
        # Fallback com LLM
        try:
            response = self.client.chat.completions.create(
                model="gpt-4.1-mini",
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
                municipio_chave_sem_acento = self.remover_acentos(municipio_chave)
                if municipio_chave_sem_acento == municipio_extraido_sem_acento:
                    return self.municipio_para_promotoria[municipio_chave]["municipio_oficial"]
        except Exception:
            pass
        
        return None

    def gerar_resumo(self, denuncia: str) -> str:
        """Gera um resumo de uma frase da denúncia"""
        try:
            response = self.client.chat.completions.create(
                model="gpt-4.1-mini",
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
        """Classifica a denúncia usando LLM"""
        try:
            response = self.client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {"role": "system", "content": """Você é um classificador de denúncias. Analise a denúncia e retorne um JSON com:
                    - tema: Um dos seguintes: Alimentação, Comércio, Educação, Finanças, Habitação, Informações, Lazer, Produtos, Saúde, Serviços, Telecomunicações, Transporte
                    - subtema: O subtema específico dentro do tema
                    - empresa: Nome da empresa mencionada (ou "Não identificada")
                    
                    Responda APENAS com o JSON, sem explicações."""},
                    {"role": "user", "content": f"Classifique: {denuncia}"}
                ],
                temperature=0.3,
                max_tokens=200
            )
            
            try:
                resultado = json.loads(response.choices[0].message.content.strip())
                return resultado
            except json.JSONDecodeError:
                return {
                    "tema": "Serviços",
                    "subtema": "Serviços On-line (E-mails, Aplicativos, Redes Sociais, Hospedagem de Sites, etc.)",
                    "empresa": "Não identificada"
                }
        except Exception:
            return {
                "tema": "Serviços",
                "subtema": "Serviços On-line (E-mails, Aplicativos, Redes Sociais, Hospedagem de Sites, etc.)",
                "empresa": "Não identificada"
            }

    def processar_denuncia(self, endereco: str, denuncia: str, num_comunicacao: str = "", num_mprj: str = "") -> Dict:
        """Processa uma denúncia completa"""
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
