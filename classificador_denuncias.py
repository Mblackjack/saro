# -*- coding: utf-8 -*-
"""
Classificador de Denúncias do Consumidor - SARO v5.9
Sistema Híbrido: OpenAI (Principal) com Fallback para Gemini ou Modo Manual.
Trata erros de cota (429) de forma graciosa.
"""

import json
import os
import unicodedata
import streamlit as st
from typing import Dict, Optional

# Importações condicionais para evitar quebra se as libs não estiverem instaladas
try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

try:
    import google.generativeai as genai
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False

class ClassificadorDenuncias:
    def __init__(self):
        self.base_path = os.path.dirname(os.path.abspath(__file__))
        self.carregar_bases()
        
        # Inicializar clientes
        self.client_openai = None
        self.model_gemini = None
        
        # Configurar OpenAI
        openai_key = st.secrets.get("OPENAI_API_KEY")
        if HAS_OPENAI and openai_key:
            try:
                self.client_openai = OpenAI(api_key=openai_key)
            except:
                pass

        # Configurar Gemini (como backup)
        gemini_key = st.secrets.get("GOOGLE_API_KEY")
        if HAS_GEMINI and gemini_key:
            try:
                genai.configure(api_key=gemini_key)
                # Usando o nome de modelo mais estável para evitar 404
                self.model_gemini = genai.GenerativeModel('gemini-1.5-flash')
            except:
                pass

    def carregar_bases(self):
        try:
            with open(f"{self.base_path}/base_temas_subtemas.json", 'r', encoding='utf-8') as f:
                self.temas_subtemas = json.load(f)
            with open(f"{self.base_path}/base_promotorias.json", 'r', encoding='utf-8') as f:
                self.base_promotorias = json.load(f)
        except Exception as e:
            st.error(f"❌ Erro ao carregar bases: {e}")
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
        for m_chave in self.municipio_para_promotoria.keys():
            if self.remover_acentos(m_chave) in endereco_upper:
                return self.municipio_para_promotoria[m_chave]["municipio_oficial"]
        return None

    def _chamar_ia(self, prompt: str, system_prompt: str = "") -> Optional[str]:
        """Tenta chamar OpenAI, depois Gemini, e trata erros de cota"""
        
        # 1. Tentar OpenAI
        if self.client_openai:
            try:
                response = self.client_openai.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.0,
                    max_tokens=300
                )
                return response.choices[0].message.content.strip()
            except Exception as e:
                if "insufficient_quota" in str(e) or "429" in str(e):
                    st.warning("⚠️ OpenAI sem créditos. Tentando backup...")
                else:
                    st.error(f"Erro OpenAI: {e}")

        # 2. Tentar Gemini (Backup)
        if self.model_gemini:
            try:
                full_prompt = f"{system_prompt}\n\n{prompt}"
                response = self.model_gemini.generate_content(full_prompt)
                return response.text.strip()
            except Exception as e:
                st.warning(f"⚠️ Backup Gemini também falhou: {e}")

        return None

    def processar_denuncia(self, endereco: str, denuncia: str, num_comunicacao: str = "", num_mprj: str = "") -> Dict:
        municipio = self.extrair_municipio(endereco)
        promotoria_info = self.municipio_para_promotoria.get(
            municipio.upper() if municipio else "", 
            {"promotoria": "Selecione manualmente", "email": "N/A", "telefone": "N/A", "municipio_oficial": municipio or "Não identificado"}
        )

        catalogo_str = "\n".join([f"- {t}: {', '.join(s)}" for t, s in self.temas_subtemas.items()])
        
        system_prompt = f"""Você é um classificador do MPRJ. Use o catálogo:
        {catalogo_str}
        Retorne APENAS um JSON: {{"tema": "...", "subtema": "...", "empresa": "...", "resumo": "uma frase curta"}}"""
        
        res_ia = self._chamar_ia(f"Denúncia: {denuncia}", system_prompt)
        
        dados_ia = {}
        if res_ia:
            try:
                # Limpeza básica de markdown
                res_ia = res_ia.replace("```json", "").replace("```", "").strip()
                dados_ia = json.loads(res_ia)
            except:
                pass

        # Fallback para valores padrão se a IA falhar totalmente
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
            "subtema": dados_ia.get("subtema", "Outros"),
            "empresa": dados_ia.get("empresa", "Não identificada"),
            "resumo": dados_ia.get("resumo", "Processamento manual necessário (Cota de IA excedida).")
        }
