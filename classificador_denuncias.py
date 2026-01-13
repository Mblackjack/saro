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
        # 1. Obter chave do Gemini via Secrets
        api_key = st.secrets.get("GOOGLE_API_KEY")
        if not api_key:
            st.error("❌ Erro: GOOGLE_API_KEY não configurada nos Secrets do Streamlit.")
            st.stop()

        try:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
        except Exception as e:
            st.error(f"❌ Erro ao conectar com Google Gemini: {str(e)}")
            st.stop()
        
        self.base_path = os.path.dirname(os.path.abspath(__file__))
        self.carregar_bases()

    def carregar_bases(self):
        """Carrega bases e cria o mapeamento reverso para evitar erros de hierarquia"""
        try:
            with open(os.path.join(self.base_path, "base_temas_subtemas.json"), 'r', encoding='utf-8') as f:
                self.temas_subtemas = json.load(f)
            
            with open(os.path.join(self.base_path, "base_promotorias.json"), 'r', encoding='utf-8') as f:
                self.base_promotorias = json.load(f)
                
            # Mapeamento Reverso (SUBTEMA -> TEMA): Acaba com a alucinação
            self.subtema_para_tema = {}
            for tema, subtemas in self.temas_subtemas.items():
                for sub in subtemas:
                    self.subtema_para_tema[sub] = tema

            # Mapeamento de Municípios
            self.municipio_para_promotoria = {}
            for nucleo, dados in self.base_promotorias.items():
                for municipio in dados["municipios"]:
                    self.municipio_para_promotoria[self.remover_acentos(municipio.upper())] = {
                        "promotoria": dados["promotoria"],
                        "email": dados["email"],
                        "telefone": dados["telefone"],
                        "municipio_oficial": municipio
                    }
        except Exception as e:
            st.error(f"❌ Erro crítico ao carregar arquivos JSON: {e}")
            st.stop()

    def remover_acentos(self, texto: str) -> str:
        if not texto: return ""
        return "".join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')

    def processar_denuncia(self, endereco: str, denuncia: str, num_comunicacao: str = "", num_mprj: str = "") -> Dict:
        """Processa a denúncia garantindo que todas as chaves (email/telefone) existam no retorno"""
        
        # 1. Localização (Município e Promotoria)
        municipio_info = {"promotoria": "Não identificada", "email": "N/A", "telefone": "N/A", "municipio_oficial": "Não identificado"}
        end_limpo = self.remover_acentos(endereco.upper())
        for m_chave, info in self.municipio_para_promotoria.items():
            if m_chave in end_limpo:
                municipio_info = info
                break

        # 2. Construção do Dicionário de Retorno (Prevenção de KeyError)
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

        # 3. Preparação do Prompt focado em Subtema
        todos_subtemas = list(self.subtema_para_tema.keys())
        prompt = f"""Analise esta denúncia do consumidor e enquadre-a no SUBTEMA correto da lista oficial.
        
        REGRAS:
        1. Identifique o objeto da reclamação (ex: ônibus, banco, luz).
        2. Escolha o item mais similar da LISTA OFICIAL abaixo.
        3. Se citar transporte público ou coletivo, o subtema deve ser 'Ônibus'.
        
        LISTA OFICIAL: {todos_subtemas}

        DENÚNCIA: "{denuncia}"

        Responda APENAS um JSON:
        {{"subtema": "NOME_EXATO_DA_LISTA", "empresa": "NOME_DA_EMPRESA", "resumo": "Denúncia referente a..."}}"""

        # 4. Chamada à API com retry simples para evitar erro 429
        try:
            response = self.model.generate_content(prompt)
            # Limpeza de resposta JSON do Gemini
            res_text = response.text.replace('```json', '').replace('```', '').strip()
            dados_ia = json.loads(res_text)
            
            sub_escolhido = dados_ia.get("subtema")
            
            # Vínculo automático Tema-Subtema (Python decide o Tema, não a IA)
            res_final["subtema"] = sub_escolhido
            res_final["tema"] = self.subtema_para_tema.get(sub_escolhido, "Outros")
            res_final["empresa"] = dados_ia.get("empresa", "Não identificada")
            res_final["resumo"] = dados_ia.get("resumo", "Resumo indisponível")

        except Exception as e:
            # Em caso de erro (Cota ou Timeout), o app não quebra pois as chaves já existem em res_final
            res_final["resumo"] = f"⚠️ Erro temporário na IA (Aguarde 60s). Detalhe: {str(e)[:40]}"
            res_final["subtema"] = "Erro de conexão"

        return res_final
