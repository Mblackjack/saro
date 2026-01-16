# -*- coding: utf-8 -*-
import json
import os
import unicodedata
import streamlit as st
from typing import Dict, Optional

try:
    from openai import OpenAI
except ImportError:
    st.error("❌ Biblioteca OpenAI não instalada. Adicione 'openai' ao requirements.txt")
    st.stop()

class ClassificadorDenuncias:
    def __init__(self):
        # 1. Busca a chave nos Secrets do Streamlit
        self.api_key = st.secrets.get("OPENAI_API_KEY")
        
        if not self.api_key:
            st.error("❌ OPENAI_API_KEY não encontrada nos Secrets.")
            st.stop()
        
        try:
            self.client = OpenAI(api_key=self.api_key)
        except Exception as e:
            st.error(f"❌ Erro na conexão OpenAI: {e}")
            st.stop()
        
        self.model_name = "gpt-4o-mini"
        self.base_path = os.path.dirname(os.path.abspath(__file__))
        self.carregar_bases()

    def carregar_bases(self):
        try:
            caminho_temas = os.path.join(self.base_path, "base_temas_subtemas.json")
            caminho_proms = os.path.join(self.base_path, "base_promotorias.json")
            
            with open(caminho_temas, 'r', encoding='utf-8') as f:
                self.temas_subtemas = json.load(f)
            with open(caminho_proms, 'r', encoding='utf-8') as f:
                self.base_promotorias = json.load(f)
        except Exception as e:
            st.error(f"❌ Erro ao carregar JSONs: {e}")
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
        end_up = self.remover_acentos(endereco.upper())
        for m_chave, info in self.municipio_para_promotoria.items():
            if self.remover_acentos(m_chave) in end_up:
                return info["municipio_oficial"]
        return None

    def processar_denuncia(self, endereco: str, denuncia: str, num_com: str = "", num_mprj: str = "") -> Dict:
        municipio = self.extrair_municipio(endereco)
        prom_info = self.municipio_para_promotoria.get(
            municipio.upper() if municipio else "",
            {"promotoria": "Não identificada", "email": "N/A", "telefone": "N/A", "municipio_oficial": "Não identificado"}
        )

        catalogo = ""
        for t, s in self.temas_subtemas.items():
            catalogo += f"TEMA: {t} | SUBTEMAS: {', '.join(s)}\n"

        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": f"Você é um classificador do MPRJ. Use este catálogo:\n{catalogo}"},
                    {"role": "user", "content": f"Retorne APENAS um JSON para esta denúncia: {denuncia}\nFormato: {{\"tema\": \"...\", \"subtema\": \"...\", \"empresa\": \"...\", \"resumo\": \"máx 10 palavras\"}}"}
                ],
                response_format={"type": "json_object"},
                temperature=0
            )
            dados_ia = json.loads(response.choices[0].message.content)
        except Exception as e:
            st.warning(f"Erro na IA: {e}")
            dados_ia = {"tema": "Diversos", "subtema": "Outros", "empresa": "Não identificada", "resumo": "Erro no processamento."}

        return {
            "num_comunicacao": num_com, "num_mprj": num_mprj,
            "endereco": endereco, "denuncia": denuncia,
            "municipio": prom_info["municipio_oficial"],
            "promotoria": prom_info["promotoria"],
            "email": prom_info["email"], "telefone": prom_info["telefone"],
            "tema": dados_ia.get("tema", "Diversos"),
            "subtema": dados_ia.get("subtema", "Outros"),
            "empresa": dados_ia.get("empresa", "Não identificada"),
            "resumo": dados_ia.get("resumo", "Sem resumo")
        }
