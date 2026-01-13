# -*- coding: utf-8 -*-
import json
import os
import unicodedata
import streamlit as st
import google.generativeai as genai
from typing import Dict

class ClassificadorDenuncias:
    def __init__(self):
        # Configuração da API via Secrets
        api_key = st.secrets.get("GOOGLE_API_KEY")
        if not api_key:
            st.error("❌ GOOGLE_API_KEY não configurada.")
            st.stop()

        try:
            genai.configure(api_key=api_key)
            # Versão estável para evitar Erro 404
            self.model = genai.GenerativeModel('gemini-1.5-flash')
        except Exception as e:
            st.error(f"❌ Erro na conexão Gemini: {e}")
            st.stop()
        
        self.base_path = os.path.dirname(os.path.abspath(__file__))
        self.carregar_bases()

    def carregar_bases(self):
        """Carrega bases e cria o mapa Tema-Subtema rigoroso"""
        try:
            with open(os.path.join(self.base_path, "base_temas_subtemas.json"), 'r', encoding='utf-8') as f:
                self.temas_subtemas = json.load(f)
            
            with open(os.path.join(self.base_path, "base_promotorias.json"), 'r', encoding='utf-8') as f:
                self.base_promotorias = json.load(f)
                
            # Mapeamento Reverso: Acaba com a alucinação (Subtema -> Tema)
            self.subtema_para_tema = {}
            for tema, subtemas in self.temas_subtemas.items():
                for sub in subtemas:
                    self.subtema_para_tema[sub] = tema

            # Mapeamento de Municípios
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
            st.error(f"❌ Erro crítico nos ficheiros JSON: {e}")
            st.stop()

    def remover_acentos(self, texto: str) -> str:
        if not texto: return ""
        return "".join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')

    def processar_denuncia(self, endereco: str, denuncia: str, num_comunicacao: str = "", num_mprj: str = "") -> Dict:
        # 1. Busca Geográfica (Município/Promotoria)
        municipio_info = {"promotoria": "Não identificada", "email": "N/A", "telefone": "N/A", "municipio_oficial": "Não identificado"}
        end_limpo = self.remover_acentos(endereco.upper())
        for m_chave, info in self.municipio_para_promotoria.items():
            if m_chave in end_limpo:
                municipio_info = info
                break

        # 2. DICIONÁRIO PADRÃO: Resolve o erro "KeyError: 'email'"
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
            "resumo": "Processando análise..."
        }

        # 3. EXTRAÇÃO RÍGIDA: Envia apenas subtemas para a IA
        lista_subtemas = list(self.subtema_para_tema.keys())
        prompt = f"""Analise a denúncia e escolha o SUBTEMA EXATO da lista oficial.
        LISTA: {lista_subtemas}
        DENÚNCIA: "{denuncia}"
        Responda APENAS um JSON puro: {{"subtema": "NOME_EXATO", "empresa": "NOME", "resumo": "RESUMO_CURTO"}}"""

        try:
            response = self.model.generate_content(prompt)
            res_text = response.text.replace('```json', '').replace('```', '').strip()
            dados_ia = json.loads(res_text)
            
            sub = dados_ia.get("subtema")
            # O Python define o Tema baseado no JSON (Vínculo infalível)
            res_final["subtema"] = sub
            res_final["tema"] = self.subtema_para_tema.get(sub, "Outros")
            res_final["empresa"] = dados_ia.get("empresa", "Não identificada")
            res_final["resumo"] = dados_ia.get("resumo", "Resumo indisponível")

        except Exception:
            res_final["resumo"] = "⚠️ Falha na análise automática. Tente novamente em 1 minuto."
            res_final["subtema"] = "IA Indisponível"

        return res_final
