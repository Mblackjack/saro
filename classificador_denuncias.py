import json
import os
import unicodedata
import streamlit as st
import google.generativeai as genai
from typing import Dict

class ClassificadorDenuncias:
    def __init__(self):
        # 1. Configuração da API via Secrets do Streamlit
        api_key = st.secrets.get("GOOGLE_API_KEY")
        if not api_key:
            st.error("❌ GOOGLE_API_KEY não encontrada nos Secrets.")
            st.stop()

        genai.configure(api_key=api_key)
        
        # Nome estável do modelo
        self.model_name = 'gemini-1.5-flash'
        self.model = genai.GenerativeModel(self.model_name)
        
        self.base_path = os.path.dirname(os.path.abspath(__file__))
        self.carregar_bases()

    def carregar_bases(self):
        """Carrega os arquivos JSON de suporte."""
        try:
            path_temas = os.path.join(self.base_path, "base_temas_subtemas.json")
            path_proms = os.path.join(self.base_path, "base_promotorias.json")
            
            with open(path_temas, 'r', encoding='utf-8') as f:
                self.temas_subtemas = json.load(f)
            with open(path_proms, 'r', encoding='utf-8') as f:
                self.base_promotorias = json.load(f)
        except Exception as e:
            st.error(f"❌ Erro ao ler arquivos JSON: {e}")
            st.stop()
            
        # Mapeamento de municípios
        self.municipio_para_promotoria = {}
        for nucleo, dados in self.base_promotorias.items():
            for m in dados.get("municipios", []):
                self.municipio_para_promotoria[m.upper()] = {
                    "promotoria": dados.get("promotoria"),
                    "email": dados.get("email"),
                    "telefone": dados.get("telefone"),
                    "municipio_oficial": m
                }

    def remover_acentos(self, texto: str) -> str:
        if not texto: return ""
        return "".join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')

    def processar_denuncia(self, endereco: str, denuncia: str, num_comunicacao: str = "", num_mprj: str = "") -> Dict:
        # Busca município no endereço
        municipio_identificado = None
        end_limpo = self.remover_acentos(endereco.upper())
        
        for m_chave in self.municipio_para_promotoria.keys():
            if self.remover_acentos(m_chave) in end_limpo:
                municipio_identificado = self.municipio_para_promotoria[m_chave]
                break
        
        if not municipio_identificado:
            municipio_identificado = {
                "promotoria": "Promotoria não identificada",
                "email": "N/A",
                "telefone": "N/A",
                "municipio_oficial": "Não identificado"
            }

        # Constrói a lista de Temas e Subtemas para a IA
        mapeamento_txt = ""
        for tema, subtemas in self.temas_subtemas.items():
            mapeamento_txt += f"- TEMA: {tema} | SUBTEMAS: {', '.join(subtemas)}\
