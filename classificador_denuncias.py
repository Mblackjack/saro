# -*- coding: utf-8 -*-
import json
import os
import unicodedata
import streamlit as st
import google.generativeai as genai
from typing import Dict

class ClassificadorDenuncias:
    def __init__(self):
        # 1. Configuração da API Key (Streamlit Secrets)
        api_key = st.secrets.get("GOOGLE_API_KEY")
        if not api_key:
            st.error("❌ GOOGLE_API_KEY não configurada nos Secrets.")
            st.stop()

        genai.configure(api_key=api_key)
        
        # Modelo 2.0 Flash (O que funcionou na sua cota)
       self.model = models/genai.GenerativeModel('gemini-1.5-flash')
        
        self.base_path = os.path.dirname(os.path.abspath(__file__))
        self.carregar_bases()

    def carregar_bases(self):
        """Carrega as bases de dados locais (Municípios e Temas)"""
        try:
            with open(os.path.join(self.base_path, "base_temas_subtemas.json"), 'r', encoding='utf-8') as f:
                self.temas_subtemas = json.load(f)
            with open(os.path.join(self.base_path, "base_promotorias.json"), 'r', encoding='utf-8') as f:
                self.base_promotorias = json.load(f)
        except Exception as e:
            st.error(f"❌ Erro ao carregar arquivos JSON: {e}")
            st.stop()
            
        # Mapeamento de municípios para promotorias
        self.municipio_para_promotoria = {}
        for nucleo, d in self.base_promotorias.items():
            for m in d["municipios"]:
                self.municipio_para_promotoria[m.upper()] = {
                    "promotoria": d["promotoria"],
                    "email": d["email"],
                    "telefone": d["telefone"],
                    "municipio_oficial": m
                }

    def remover_acentos(self, texto: str) -> str:
        if not texto: return ""
        return "".join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')

    def processar_denuncia(self, endereco: str, denuncia: str, num_comunicacao: str = "", num_mprj: str = "") -> Dict:
        # --- LÓGICA LOCAL: Identificação de Município ---
        municipio_nome = None
        end_upper = self.remover_acentos(endereco.upper())
        for m_chave in self.municipio_para_promotoria.keys():
            if self.remover_acentos(m_chave) in end_upper:
                municipio_nome = self.municipio_para_promotoria[m_chave]["municipio_oficial"]
                break
        
        prom_info = self.municipio_para_promotoria.get(
            municipio_nome.upper() if municipio_nome else "", 
            {"promotoria": "Promotoria não identificada", "email": "N/A", "telefone": "N/A", "municipio_oficial": municipio_nome or "Não identificado"}
        )

        # --- PREPARAÇÃO PARA IA: Hierarquia de Temas ---
        hierarquia_txt = ""
        for tema, subtemas in self.temas_subtemas.items():
            hierarquia_txt += f"- TEMA: {tema} | SUBTEMAS POSSÍVEIS: {', '.join(subtemas)}\n"

        # --- PROMPT DE AJUSTE FINO ---
        prompt = f"""Atue como um analista jurídico especializado em Direito do Consumidor.
Analise a denúncia: "{denuncia}"

### REGRAS CRÍTICAS DE CLASSIFICAÇÃO:
1. TEMA E SUBTEMA: Escolha EXATAMENTE da lista abaixo. Não use sinônimos ou termos novos.
{hierarquia_txt}

2. EMPRESA: Extraia o nome da empresa reclamada (Ex: Light, Enel, Banco Itaú, Samsung, Mercado Livre). 
   - Se houver CNPJ, ignore o número e use o Nome Fantasia.
   - Se não houver nome claro, use "Não identificada".

3. RESUMO: Uma frase técnica e direta.

### FORMATO DE SAÍDA (JSON PURO):
{{
  "tema": "O Tema escolhido",
  "subtema": "O Subtema escolhido",
  "empresa": "Nome da Empresa",
  "resumo": "Texto do resumo"
}}"""

        try:
            response = self.model.generate_content(prompt)
            res_text = response.text.strip()
            
            # Limpeza de Markdown da resposta
            if "```json" in res_text:
                res_text = res_text.split("```json")[1].split("```")[0].strip()
            elif "```" in res_text:
                res_text = res_text.split("```")[1].split("```")[0].strip()
                
            dados_ia = json.loads(res_text)

            # --- TRAVA DE SEGURANÇA: Validação com o JSON Real ---
            tema_final = dados_ia.get("tema")
            subtema_final = dados_ia.get("subtema")

            if tema_final not in self.temas_subtemas:
                tema_final = "Serviços"
                subtema_final = "SAC"
            elif subtema_final not in self.temas_subtemas[tema_final]:
                # Se o tema está certo mas o subtema não, tenta achar o mais próximo ou pega o primeiro
                subtema_final = self.temas_subtemas[tema_final][0]

        except Exception as e:
            st.warning(f"Aviso: IA em ajuste. Detalhe: {e}")
            tema_final, subtema_final = "Serviços", "SAC"
            dados_ia = {"empresa": "Não identificada", "resumo": "Processamento local."}

        return {
            "num_comunicacao": num_comunicacao,
            "num_mprj": num_mprj,
            "endereco": endereco,
            "denuncia": denuncia,
            "municipio": prom_info["municipio_oficial"],
            "promotoria": prom_info["promotoria"],
            "email": prom_info["email"],
            "telefone": prom_info["telefone"],
            "tema": tema_final,
            "subtema": subtema_final,
            "empresa": dados_ia.get("empresa", "Não identificada"),
            "resumo": dados_ia.get("resumo", "Resumo indisponível")
        }
