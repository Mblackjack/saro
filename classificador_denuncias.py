# -*- coding: utf-8 -*-
import json
import os
import unicodedata
import streamlit as st
from typing import Dict, Optional
from openai import OpenAI

class ClassificadorDenuncias:
    def __init__(self):
        # 1. Recupera a chave com prioridade para o Secrets do Streamlit
        api_key = st.secrets.get("OPENAI_API_KEY")
        
        if not api_key:
            st.error("❌ ERRO: Chave OPENAI_API_KEY não encontrada nos Secrets do Streamlit.")
            st.stop()

        self.client = OpenAI(api_key=api_key)
        self.base_path = os.path.dirname(os.path.abspath(__file__))
        self.carregar_bases()

    def carregar_bases(self):
        """Carrega os arquivos JSON de suporte"""
        caminho_temas = os.path.join(self.base_path, "base_temas_subtemas.json")
        caminho_promotorias = os.path.join(self.base_path, "base_promotorias.json")

        try:
            with open(caminho_temas, 'r', encoding='utf-8') as f:
                self.temas_subtemas = json.load(f)
            with open(caminho_promotorias, 'r', encoding='utf-8') as f:
                self.base_promotorias = json.load(f)
        except Exception as e:
            st.error(f"❌ Erro ao ler bases JSON: {e}")
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
        if not endereco: return None
        end_upper = self.remover_acentos(endereco.upper())
        for m_chave, dados in self.municipio_para_promotoria.items():
            if self.remover_acentos(m_chave) in end_upper:
                return dados["municipio_oficial"]
        return None

    def processar_denuncia(self, endereco: str, denuncia: str, num_comunicacao: str = "", num_mprj: str = "") -> Dict:
        """
        Função principal que faz a chamada à IA e organiza os dados.
        """
        # Identificação de Município (Lógica local)
        municipio_nome = self.extrair_municipio(endereco)
        promotoria_info = self.municipio_para_promotoria.get(
            municipio_nome.upper() if municipio_nome else "", 
            {"promotoria": "Promotoria não identificada", "email": "N/A", "telefone": "N/A", "municipio_oficial": municipio_nome or "Não identificado"}
        )

        # PREPARAÇÃO DO PROMPT
        temas_validos = list(self.temas_subtemas.keys())
        
        prompt_sistema = f"""Você é um especialista em triagem de denúncias do Ministério Público.
Analise o relato do consumidor e extraia rigorosamente os dados solicitados.

LISTA DE TEMAS VÁLIDOS (Escolha apenas um desta lista):
{", ".join(temas_validos)}

INSTRUÇÕES:
1. TEMA: Escolha o que melhor se adapta à denúncia na lista acima.
2. SUBTEMA: Descreva o problema em até 4 palavras (ex: Cobrança Indevida, Falta de Luz).
3. EMPRESA: Extraia o nome da empresa reclamada. Procure por nomes próprios como 'Enel', 'Light', 'Samsung', etc.
4. RESUMO: Resuma o fato em uma frase curta começando com 'Denúncia referente a'.

RESPONDA APENAS EM JSON PURO:
{{
  "tema": "...",
  "subtema": "...",
  "empresa": "...",
  "resumo": "..."
}}"""

        try:
            # Chamada principal para a IA (GPT-4o-mini)
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": prompt_sistema},
                    {"role": "user", "content": f"DENÚNCIA: {denuncia}"}
                ],
                response_format={"type": "json_object"},
                temperature=0
            )
            
            dados_ia = json.loads(response.choices[0].message.content)
            
        except Exception as e:
            # Se der erro, vamos mostrar o erro real para depuração
            st.error(f"⚠️ Erro na comunicação com a IA: {str(e)}")
            dados_ia = {
                "tema": "Erro Técnico",
                "subtema": "Verificar Logs",
                "empresa": "Erro de Conexão",
                "resumo": f"Erro: {str(e)}"
            }

        return {
            "num_comunicacao": num_comunicacao or "N/A",
            "num_mprj": num_mprj or "N/A",
            "endereco": endereco,
            "denuncia": denuncia,
            "municipio": promotoria_info["municipio_oficial"],
            "promotoria": promotoria_info["promotoria"],
            "email": promotoria_info["email"],
            "telefone": promotoria_info["telefone"],
            "tema": dados_ia.get("tema", "Serviços"),
            "subtema": dados_ia.get("subtema", "Análise Pendente"),
            "empresa": dados_ia.get("empresa", "Não identificada"),
            "resumo": dados_ia.get("resumo", "Resumo não gerado")
        }
