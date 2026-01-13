import json
import os
import unicodedata
import streamlit as st
import google.generativeai as genai
from typing import Dict, Optional

class ClassificadorDenuncias:
    def __init__(self):
        # A identação deve ser uniforme (4 espaços)
        api_key = st.secrets.get("GOOGLE_API_KEY")
        if not api_key:
            st.error("❌ GOOGLE_API_KEY não configurada nos Secrets.")
            st.stop()

        genai.configure(api_key=api_key)
        
        # Uso do modelo estável para evitar erro 404
        self.model_name = 'gemini-1.5-flash' 
        self.model = genai.GenerativeModel(self.model_name)
        
        self.base_path = os.path.dirname(os.path.abspath(__file__))
        self.carregar_bases()

    def carregar_bases(self):
        try:
            with open(os.path.join(self.base_path, "base_temas_subtemas.json"), 'r', encoding='utf-8') as f:
                self.temas_subtemas = json.load(f)
            with open(os.path.join(self.base_path, "base_promotorias.json"), 'r', encoding='utf-8') as f:
                self.base_promotorias = json.load(f)
        except Exception as e:
            st.error(f"❌ Erro nas bases JSON: {e}")
            st.stop()
            
        # Mapeamento corrigido de municípios
        self.municipio_para_promotoria = {}
        for nucleo, d in self.base_promotorias.items():
            for m in d.get("municipios", []):
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
        # 1. Busca de Município/Promotoria
        municipio_nome = None
        end_upper = self.remover_acentos(endereco.upper())
        for m_chave in self.municipio_para_promotoria.keys():
            if self.remover_acentos(m_chave) in end_upper:
                municipio_nome = self.municipio_para_promotoria[m_chave]["municipio_oficial"]
                break
        
        prom_info = self.municipio_para_promotoria.get(
            municipio_nome.upper() if municipio_nome else "", 
            {"promotoria": "Não identificada", "email": "N/A", "telefone": "N/A", "municipio_oficial": "Não identificado"}
        )

        # 2. Preparação do Guia Hierárquico para a IA (Passo a passo solicitado)
        guia_hierarquico = ""
        for tema, subtemas in self.temas_subtemas.items():
            guia_
