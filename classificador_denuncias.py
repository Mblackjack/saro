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
        # 1. Configuração da API do Gemini via Secrets
        api_key = st.secrets.get("GOOGLE_API_KEY")
        if not api_key:
            st.error("❌ Erro: GOOGLE_API_KEY não configurada nos Secrets do Streamlit.")
            st.stop()

        try:
            genai.configure(api_key=api_key)
            # Uso do modelo estável para evitar Erro 404
            self.model = genai.GenerativeModel('gemini-1.5-flash')
        except Exception as e:
            st.error(f"❌ Erro ao conectar com Google Gemini: {str(e)}")
            st.stop()
        
        self.base_path = os.path.dirname(os.path.abspath(__file__))
        self.carregar_bases()

    def carregar_bases(self):
        """Carrega as bases JSON e cria o vínculo obrigatório Subtema -> Tema"""
        try:
            with open(os.path.join(self.base_path, "base_temas_subtemas.json"), 'r', encoding='utf-8') as f:
                self.temas_subtemas = json.load(f)
            
            with open(os.path.join(self.base_path, "base_promotorias.json"), 'r', encoding='utf-8') as f:
                self.base_promotorias = json.load(f)
                
            # MAPA REVERSO: Se a IA escolher 'Ônibus', o Python garante o tema 'Transporte'
            self.subtema_para_tema = {}
            for tema, subtemas in self.temas_subtemas.items():
                for sub in subtemas:
                    self.subtema_para_tema[sub] = tema

            # Mapeamento de Municípios para Promotorias
            self.municipio_para_promotoria = {}
            for nucleo, dados in self.base_promotorias.items():
                for municipio in dados.get("municipios", []):
                    self.municipio_para_promotoria[self.remover_acentos(municipio.upper())] = {
                        "promotoria": dados["promotoria"],
                        "email": dados["email"],
                        "telefone": dados["telefone"],
                        "municipio_oficial": municipio
                    }
        except Exception as e:
            st.error(f"❌ Erro crítico ao carregar ficheiros JSON: {e}")
            st.stop()

    def remover_acentos(self, texto: str) -> str:
        if not texto: return ""
        return "".join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')

    def processar_denuncia(self, endereco: str, denuncia: str, num_comunicacao: str = "", num_mprj: str = "") -> Dict:
        """Processa a denúncia blindando o retorno contra KeyError e Alucinações"""
        
        # 1. Identificação da Promotoria (Geográfica)
        municipio_info = {"promotoria": "Não identificada", "email": "N/A", "telefone": "N/A", "municipio_oficial": "Não identificado"}
        end_limpo = self.remover_acentos(endereco.upper())
        for m_chave, info in self.municipio_para_promotoria.items():
            if m_chave in end_limpo:
                municipio_info = info
                break

        # 2. CRIAÇÃO DO DICIONÁRIO PADRÃO (Prevenção total contra KeyError)
        # Todas as chaves que o app_web_v2.py pede devem estar aqui
        res_final = {
            "num_comunicacao": num_comunicacao or "N/A",
            "num_mprj": num_mprj or "N/A",
            "endereco": endereco,
            "denuncia": denuncia,
            "municipio": municipio_info["municipio_oficial"],
            "promotoria": municipio_info["promotoria"],
            "email": municipio_info["email"],
            "telefone": municipio_info["telefone"],
            "tema": "Não classificado",
            "subtema": "Não identificado",
            "empresa": "Não identificada",
            "resumo": "A analisar denúncia..."
        }

        # 3. PROMPT DE EXTRAÇÃO RÍGIDA (Foco no catálogo oficial)
        todos_subtemas = list(self.subtema_para_tema.keys())
        prompt = f"""Analise a denúncia e identifique o SUBTEMA EXATO da lista oficial.
        
        REGRAS:
        1. Compare o texto com a LISTA abaixo e escolha o item mais similar (ex: se falar de ônibus, escolha 'Ônibus').
        2. Não invente subtemas. Use apenas os da lista.
        
        LISTA OFICIAL: {todos_subtemas}

        DENÚNCIA: "{denuncia}"

        Responda APENAS um objeto JSON puro:
        {{"subtema": "NOME_EXATO_DA_LISTA", "empresa": "NOME_DA_EMPRESA", "resumo": "RESUMO_CURTO"}}"""

        # 4. CHAMADA À IA COM TRATAMENTO DE ERROS
        try:
            response = self.model.generate_content(prompt)
            # Limpa possíveis blocos de código markdown do JSON
            res_text = response.text.replace('```json', '').replace('```', '').strip()
            dados_ia = json.loads(res_text)
            
            sub_escolhido = dados_ia.get("subtema")
            
            # VÍNCULO AUTOMÁTICO: O Python define o Tema com base no Subtema escolhido
            res_final["subtema"] = sub_escolhido
            res_final["tema"] = self.subtema_para_tema.get(sub_escolhido, "Outros")
            res_final["empresa"] = dados_ia.get("empresa", "Não identificada")
            res_final["resumo"] = dados_ia.get("resumo", "Resumo indisponível")

        except Exception as e:
            # Se a IA falhar (429, 404 ou timeout), o dicionário já tem os campos 'email' e 'telefone'
            res_final["resumo"] = f"⚠️ Falha na análise automática. Tente novamente em 1 minuto."
            res_final["subtema"] = "IA Temporariamente indisponível"

        return res_final
