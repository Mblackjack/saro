# -*- coding: utf-8 -*-
import json
import os
import unicodedata
import streamlit as st
import google.generativeai as genai
import difflib
from typing import Dict, Optional

class ClassificadorDenuncias:
    def __init__(self):
        api_key = st.secrets.get("GOOGLE_API_KEY")
        if not api_key:
            st.error("❌ GOOGLE_API_KEY não configurada nos Secrets.")
            st.stop()

        genai.configure(api_key=api_key)
        
        # Modelo estável para evitar erro 404
        self.model_name = 'gemini-2.5-flash' 
        self.model = genai.GenerativeModel(
            model_name=self.model_name,
            generation_config={
                "temperature": 0.1,
            }
        )
        
        self.base_path = os.path.dirname(os.path.abspath(__file__))
        self.caminho_memoria = os.path.join(self.base_path, "memoria_empresas.json")
        self.carregar_bases()

    def carregar_bases(self):
        try:
            with open(os.path.join(self.base_path, "base_temas_subtemas.json"), 'r', encoding='utf-8') as f:
                self.temas_subtemas = json.load(f)
            with open(os.path.join(self.base_path, "base_promotorias.json"), 'r', encoding='utf-8') as f:
                self.base_promotorias = json.load(f)
            
            # Carregar memória de empresas
            if os.path.exists(self.caminho_memoria):
                with open(self.caminho_memoria, 'r', encoding='utf-8') as f:
                    self.memoria_empresas = json.load(f)
            else:
                self.memoria_empresas = []
        except Exception as e:
            st.error(f"❌ Erro nas bases JSON: {e}")
            st.stop()
            
        self.municipio_para_promotoria = {
            m.upper(): {"promotoria": d["promotoria"], "email": d["email"], "telefone": d["telefone"], "municipio_oficial": m}
            for nucleo, d in self.base_promotorias.items() for m in d["municipios"]
        }

    def padronizar_empresa(self, nome_ia: str) -> str:
        """Aplica lógica de similaridade e formatação de texto"""
        if not nome_ia or nome_ia.lower() in ["não identificada", "n/a", "ignorado"]:
            return "Não identificada"

        # 1. Formatação: Letra Maiúscula no início de cada palavra (Title Case)
        # Mantém preposições curtas em minúsculo se desejar, ou apenas title()
        nome_limpo = nome_ia.strip().title()

        # 2. Busca por similaridade na memória (80% de semelhança)
        similar = difflib.get_close_matches(nome_limpo, self.memoria_empresas, n=1, cutoff=0.8)
        
        if similar:
            return similar[0] # Retorna o nome que já existia
        
        # 3. Se é nova, adiciona na memória e salva
        self.memoria_empresas.append(nome_limpo)
        try:
            with open(self.caminho_memoria, 'w', encoding='utf-8') as f:
                json.dump(list(set(self.memoria_empresas)), f, ensure_ascii=False, indent=4)
        except:
            pass
            
        return nome_limpo

    def remover_acentos(self, texto: str) -> str:
        if not texto: return ""
        return "".join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')

    def processar_denuncia(self, endereco: str, denuncia: str, num_comunicacao: str = "", num_mprj: str = "") -> Dict:
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

        catalogo_txt = ""
        for tema, subtemas in self.temas_subtemas.items():
            catalogo_txt += f"- TEMA: {tema} | SUBTEMAS: {', '.join(subtemas)}\n"
        
        prompt = f"""Responda APENAS com um objeto JSON puro.
        Analise a denúncia: "{denuncia}"
        
        CATÁLOGO OFICIAL:
        {catalogo_txt}
        
        REGRAS:
        1. Escolha TEMA e SUBTEMA do catálogo.
        2. 'resumo' com no MÁXIMO 10 PALAVRAS.
        3. No campo 'empresa', extraia apenas o nome próprio da empresa citada.
        
        JSON esperado:
        {{"tema": "...", "subtema": "...", "empresa": "...", "resumo": "..."}}"""

        try:
            response = self.model.generate_content(prompt)
            res_text = response.text.strip()
            
            # Limpeza de Markdown se houver
            if "```json" in res_text:
                res_text = res_text.split("```json")[1].split("```")[0].strip()
            elif "```" in res_text:
                res_text = res_text.split("```")[1].split("```")[0].strip()
            
            dados_ia = json.loads(res_text)
        except Exception as e:
            st.error(f"Erro na análise: {e}")
            dados_ia = {"tema": "Serviços", "subtema": "Erro técnico", "empresa": "Não identificada", "resumo": "Falha no processamento."}

        # APLICAÇÃO DA NOVA REGRA DE EMPRESA
        empresa_final = self.padronizar_empresa(dados_ia.get("empresa", "Não identificada"))

        return {
            "num_comunicacao": num_comunicacao, "num_mprj": num_mprj,
            "endereco": endereco, "denuncia": denuncia,
            "municipio": prom_info["municipio_oficial"],
            "promotoria": prom_info["promotoria"],
            "email": prom_info["email"],
            "telefone": prom_info["telefone"],
            "tema": dados_ia.get("tema", "Serviços"),
            "subtema": dados_ia.get("subtema", "Não identificado"),
            "empresa": empresa_final,
            "resumo": dados_ia.get("resumo", "Resumo indisponível")
        }

Quero que coloque a parte do excel nele
