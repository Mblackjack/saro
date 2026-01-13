# -*- coding: utf-8 -*-
"""
Classificador de Denúncias do Consumidor - SARO v6.0
Motor: Google Gemini 1.5 Flash
Garantia de hierarquia rígida via Mapeamento Reverso.
"""

import json
import os
import unicodedata
import time
from typing import Dict, List, Optional
import streamlit as st

# Importar Google Generative AI
try:
    import google.generativeai as genai
except ImportError:
    st.error("❌ Erro: Biblioteca 'google-generativeai' não instalada. Adicione ao requirements.txt.")
    st.stop()

class ClassificadorDenuncias:
    def __init__(self):
        # 1. Configuração da API do Gemini via Secrets
        api_key = st.secrets.get("GOOGLE_API_KEY")
        
        if not api_key:
            st.error(
                "❌ **GOOGLE_API_KEY não configurada!**\n\n"
                "Vá em Settings > Secrets no Streamlit e adicione:\n"
                "```\n"
                "GOOGLE_API_KEY = \"sua-chave-aqui\"\n"
                "```"
            )
            st.stop()
        
        try:
            genai.configure(api_key=api_key)
            # Uso do modelo estável para evitar Erro 404 (conforme visto nas imagens)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
        except Exception as e:
            st.error(f"❌ Erro ao conectar com Google Gemini: {str(e)}")
            st.stop()
        
        self.base_path = os.path.dirname(os.path.abspath(__file__))
        self.carregar_bases()

    def carregar_bases(self):
        """Carrega bases e cria o vínculo obrigatório Subtema -> Tema"""
        try:
            with open(os.path.join(self.base_path, "base_temas_subtemas.json"), 'r', encoding='utf-8') as f:
                self.temas_subtemas = json.load(f)
            
            with open(os.path.join(self.base_path, "base_promotorias.json"), 'r', encoding='utf-8') as f:
                self.base_promotorias = json.load(f)
                
            # MAPEAMENTO REVERSO: Garante que se a IA escolher o Subtema, o Python força o Tema correto.
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

    def chamar_ia_com_retry(self, prompt: str) -> Optional[str]:
        """Tenta chamar a IA com tratamento de cota (Erro 429)"""
        for tentativa in range(3):
            try:
                response = self.model.generate_content(prompt)
                return response.text
            except Exception as e:
                if "429" in str(e):
                    time.sleep(5) 
                    continue
                return None
        return None

    def extrair_municipio(self, endereco: str) -> Optional[str]:
        if not endereco: return None
        endereco_upper = self.remover_acentos(endereco.upper())
        
        for m_chave, info in self.municipio_para_promotoria.items():
            if m_chave in endereco_upper:
                return info["municipio_oficial"]
        
        prompt = f"Extraia apenas o nome da cidade deste endereço: '{endereco}'. Responda apenas o nome da cidade."
        cidade_ia = self.chamar_ia_com_retry(prompt)
        if cidade_ia:
            cidade_limpa = self.remover_acentos(cidade_ia.strip().upper())
            for m_chave, info in self.municipio_para_promotoria.items():
                if m_chave == cidade_limpa:
                    return info["municipio_oficial"]
        return None

    def classificar_denuncia(self, denuncia: str) -> Dict:
        """Classifica a denúncia focando no SUBTEMA para evitar alucinação"""
        todos_subtemas = list(self.subtema_para_tema.keys())
        
        prompt = f"""Analise a denúncia e identifique o SUBTEMA EXATO da lista oficial.
        LISTA OFICIAL: {todos_subtemas}
        
        DENÚNCIA: "{denuncia}"

        Responda APENAS um JSON no formato:
        {{"subtema": "NOME_EXATO_DA_LISTA", "empresa": "NOME_DA_EMPRESA", "resumo": "RESUMO_CURTO"}}"""

        try:
            res_text = self.chamar_ia_com_retry(prompt)
            if not res_text: raise Exception("IA Indisponível")
            
            res_text = res_text.replace('```json', '').replace('```', '').strip()
            dados_ia = json.loads(res_text)
            
            sub_escolhido = dados_ia.get("subtema")
            # VÍNCULO AUTOMÁTICO: O Python define o tema baseado no subtema escolhido
            tema_final = self.subtema_para_tema.get(sub_escolhido, "Serviços")
            
            return {
                "tema": tema_final,
                "subtema": sub_escolhido if sub_escolhido in self.subtema_para_tema else "Não classificado",
                "empresa": dados_ia.get("empresa", "Não identificada"),
                "resumo": dados_ia.get("resumo", "Resumo automático indisponível")
            }
        except:
            return {
                "tema": "Serviços", 
                "subtema": "Não classificado", 
                "empresa": "Não identificada", 
                "resumo": "Falha na análise automática (Verifique a conexão)."
            }

    def processar_denuncia(self, endereco: str, denuncia: str, num_comunicacao: str = "", num_mprj: str = "") -> Dict:
        # 1. Identificar Localidade e Promotoria (Evita KeyError de e-mail/telefone)
        municipio = self.extrair_municipio(endereco)
        municipio_chave = self.remover_acentos(municipio.upper()) if municipio else ""
        
        info_prom = self.municipio_para_promotoria.get(
            municipio_chave, 
            {"promotoria": "Não identificada", "email": "N/A", "telefone": "N/A", "municipio_oficial": municipio or "Não identificado"}
        )

        # 2. Classificar Denúncia com IA
        classificacao = self.classificar_denuncia(denuncia)
        
        # 3. Retorno Garantido com todos os campos necessários
        return {
            "num_comunicacao": num_comunicacao or "N/A",
            "num_mprj": num_mprj or "N/A",
            "endereco": endereco,
            "denuncia": denuncia,
            "municipio": info_prom["municipio_oficial"],
            "promotoria": info_prom["promotoria"],
            "email": info_prom["email"],
            "telefone": info_prom["telefone"],
            "tema": classificacao["tema"],
            "subtema": classificacao["subtema"],
            "empresa": classificacao["empresa"],
            "resumo": classificacao["resumo"]
        }
