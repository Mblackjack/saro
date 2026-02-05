# -*- coding: utf-8 -*-
import json
import os
import unicodedata
import streamlit as st
from openai import OpenAI  # Biblioteca oficial da OpenAI
from datetime import datetime

class ClassificadorDenuncias:
    def __init__(self):
        # Configuração OpenAI GPT
        api_key = st.secrets.get("OPENAI_API_KEY")
        if not api_key:
            st.error("❌ Erro: OPENAI_API_KEY não encontrada nos Secrets.")
            st.stop()
            
        self.client = OpenAI(api_key=api_key)
        self.model_name = "gpt-4o-mini" # Versão rápida, barata e potente
        
        # Webhook do Power Automate (Link que você gerou)
        self.webhook_url = st.secrets.get("SHAREPOINT_WEBHOOK")
        
        self.base_path = os.path.dirname(os.path.abspath(__file__))
        self.carregar_bases()

    def carregar_bases(self):
        with open(os.path.join(self.base_path, "base_temas_subtemas.json"), 'r', encoding='utf-8') as f:
            self.temas_subtemas = json.load(f)
        with open(os.path.join(self.base_path, "base_promotorias.json"), 'r', encoding='utf-8') as f:
            self.base_promotorias = json.load(f)
        self.municipio_para_promotoria = {
            m.upper(): {"promotoria": d["promotoria"], "municipio_oficial": m}
            for nucleo, d in self.base_promotorias.items() for m in d["municipios"]
        }

    def remover_acentos(self, texto: str) -> str:
        if not texto: return ""
        return "".join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')

    def processar_denuncia(self, endereco, denuncia, num_com, num_mprj, vencedor, responsavel):
        # 1. Identificar Município/Promotoria
        municipio_nome = "Não identificado"
        promotoria = "Não identificada"
        end_upper = self.remover_acentos(endereco.upper())
        for m_chave, info in self.municipio_para_promotoria.items():
            if self.remover_acentos(m_chave) in end_upper:
                municipio_nome = info["municipio_oficial"]
                promotoria = info["promotoria"]
                break

        # 2. Classificação com GPT-4o-mini
        catalogo = json.dumps(self.temas_subtemas, ensure_ascii=False)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": f"Você é um classificador do MPRJ. Use este catálogo: {catalogo}. Responda APENAS JSON."},
                    {"role": "user", "content": f"Classifique: {denuncia}. Retorne chaves: tema, subtema, empresa, resumo (máx 10 palavras)."}
                ],
                response_format={"type": "json_object"}
            )
            dados_ia = json.loads(response.choices[0].message.content)
        except Exception as e:
            dados_ia = {"tema": "Outros", "subtema": "Geral", "empresa": "Não identificada", "resumo": "Erro no GPT"}

        # 3. Montar dados finais
        dados_final = {
            "num_com": num_com,
            "num_mprj": num_mprj,
            "promotoria": promotoria,
            "municipio": municipio_nome,
            "data": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "denuncia": denuncia,
            "resumo": dados_ia.get("resumo"),
            "tema": dados_ia.get("tema"),
            "subtema": dados_ia.get("subtema"),
            "empresa": str(dados_ia.get("empresa")).title(),
            "vencedor": vencedor,
            "responsavel": responsavel
        }

        # 4. Envio para o SharePoint (Power Automate)
        import requests
        sucesso = False
        if self.webhook_url:
            try:
                # Mesmo que o Power Automate peça premium, se você salvou o fluxo, 
                # a URL pode funcionar por um período de teste ou se sua conta tiver crédito.
                resp = requests.post(self.webhook_url, json=dados_final, timeout=15)
                sucesso = resp.status_code in [200, 202]
            except:
                sucesso = False
        
        return dados_final, sucesso
