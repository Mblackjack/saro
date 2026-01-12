# -*- coding: utf-8 -*-
import json
import os
import unicodedata
import streamlit as st
from typing import Dict, Optional
from openai import OpenAI

class ClassificadorDenuncias:
    def __init__(self):
        # Busca a chave nos Secrets do Streamlit
        api_key = st.secrets.get("OPENAI_API_KEY")
        if not api_key:
            st.error("❌ ERRO: OPENAI_API_KEY não encontrada nos Secrets.")
            st.stop()

        self.client = OpenAI(api_key=api_key)
        self.base_path = os.path.dirname(os.path.abspath(__file__))
        self.carregar_bases()

    def carregar_bases(self):
        """Carrega os arquivos JSON locais"""
        try:
            with open(os.path.join(self.base_path, "base_temas_subtemas.json"), 'r', encoding='utf-8') as f:
                self.temas_subtemas = json.load(f)
            with open(os.path.join(self.base_path, "base_promotorias.json"), 'r', encoding='utf-8') as f:
                self.base_promotorias = json.load(f)
        except Exception as e:
            st.error(f"❌ Erro ao carregar bases JSON: {e}")
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

    def processar_denuncia(self, endereco: str, denuncia: str, num_comunicacao: str = "", num_mprj: str = "") -> Dict:
        """Processa a denúncia usando uma única chamada de IA para evitar falhas parciais"""
        
        # 1. Identifica Município (Lógica local)
        municipio_nome = None
        end_upper = self.remover_acentos(endereco.upper())
        for m_chave in self.municipio_para_promotoria.keys():
            if self.remover_acentos(m_chave) in end_upper:
                municipio_nome = self.municipio_para_promotoria[m_chave]["municipio_oficial"]
                break
        
        promotoria_info = self.municipio_para_promotoria.get(
            municipio_nome.upper() if municipio_nome else "", 
            {"promotoria": "Promotoria não identificada", "email": "N/A", "telefone": "N/A", "municipio_oficial": municipio_nome or "Não identificado"}
        )

        # 2. Chamada Única para a IA
        temas_validos = list(self.temas_subtemas.keys())
        
        prompt = f"""Você é um triador do Ministério Público. Analise a DENÚNCIA abaixo.

LISTA DE TEMAS PERMITIDOS:
{temas_validos}

OBJETIVOS:
1. TEMA: Escolha o mais adequado da lista acima.
2. SUBTEMA: Identifique o problema central em 3 palavras.
3. EMPRESA: Extraia o nome da empresa reclamada (ex: Enel, Light, Samsung, Banco Itaú).
4. RESUMO: Escreva um resumo técnico de até 15 palavras começando com 'Denúncia referente a'.

DENÚNCIA: "{denuncia}"

Responda APENAS um objeto JSON assim:
{{"tema": "TEMA ESCOLHIDO", "subtema": "SUBTEMA", "empresa": "NOME DA EMPRESA", "resumo": "RESUMO"}}"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "system", "content": "Você é um classificador de dados puramente JSON."},
                          {"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0
            )
            dados_ia = json.loads(response.choices[0].message.content)
        except Exception as e:
            st.error(f"Erro na IA: {e}")
            dados_ia = {
                "tema": "Serviços", 
                "subtema": "Erro de análise", 
                "empresa": "Não identificada", 
                "resumo": "Falha na comunicação com o cérebro da IA."
            }

        return {
            "num_comunicacao": num_comunicacao,
            "num_mprj": num_mprj,
            "endereco": endereco,
            "denuncia": denuncia,
            "municipio": promotoria_info["municipio_oficial"],
            "promotoria": promotoria_info["promotoria"],
            "email": promotoria_info["email"],
            "telefone": promotoria_info["telefone"],
            "tema": dados_ia.get("tema", "Serviços"),
            "subtema": dados_ia.get("subtema", "Não identificado"),
            "empresa": dados_ia.get("empresa", "Não identificada"),
            "resumo": dados_ia.get("resumo", "Resumo indisponível")
        }
