# -*- coding: utf-8 -*-
import json
import os
import unicodedata
import streamlit as st
import google.generativeai as genai
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime

class ClassificadorDenuncias:
    def __init__(self):
        api_key = st.secrets.get("GOOGLE_API_KEY")
        if not api_key:
            st.error("❌ GOOGLE_API_KEY não configurada.")
            st.stop()

        genai.configure(api_key=api_key)
        
        # Fallback de modelos
        self.model = None
        for nome in ['gemini-1.5-flash', 'models/gemini-1.5-flash', 'gemini-1.5-flash-latest']:
            try:
                self.model = genai.GenerativeModel(model_name=nome, generation_config={"temperature": 0.1})
                break
            except:
                continue

        self.base_path = os.path.dirname(os.path.abspath(__file__))
        self.carregar_bases()
        
        # Conexão com Google Sheets
        self.conn = st.connection("gsheets", type=GSheetsConnection)

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

    def salvar_na_planilha_online(self, dados: dict):
        """Adiciona os dados na planilha Google Sheets Online"""
        try:
            url = st.secrets.get("GSHEET_URL")
            # Lê os dados atuais
            df_atual = self.conn.read(spreadsheet=url, usecols=list(range(12)))
            # Cria nova linha
            nova_linha = pd.DataFrame([dados])
            # Concatena e atualiza
            df_final = pd.concat([df_atual, nova_linha], ignore_index=True)
            self.conn.update(spreadsheet=url, data=df_final)
        except Exception as e:
            st.warning(f"⚠️ Erro ao sincronizar com Excel Online: {e}")

    def processar_denuncia(self, endereco, denuncia, num_com, num_mprj, vencedor, responsavel):
        # Localização
        municipio_nome = "Não identificado"
        promotoria = "Não identificada"
        end_upper = self.remover_acentos(endereco.upper())
        for m_chave, info in self.municipio_para_promotoria.items():
            if self.remover_acentos(m_chave) in end_upper:
                municipio_nome = info["municipio_oficial"]
                promotoria = info["promotoria"]
                break

        # IA
        catalogo = json.dumps(self.temas_subtemas, ensure_ascii=False)
        prompt = f"Analise em JSON: {denuncia}. Catálogo: {catalogo}. Retorne: tema, subtema, empresa, resumo(10 palavras)."
        
        try:
            res = self.model.generate_content(prompt)
            dados_ia = json.loads(res.text.replace('```json', '').replace('```', ''))
        except:
            dados_ia = {"tema": "Outros", "subtema": "Geral", "empresa": "Não identificada", "resumo": "Processado manualmente"}

        # Resultado final formatado para a Planilha
        resultado = {
            "Nº Comunicação": num_com,
            "Nº MPRJ": num_mprj,
            "Promotoria": promotoria,
            "Município": municipio_nome,
            "Data": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "Denúncia": denuncia,
            "Resumo": dados_ia.get("resumo"),
            "Tema": dados_ia.get("tema"),
            "Subtema": dados_ia.get("subtema"),
            "Empresa": dados_ia.get("empresa", "").strip().title(),
            "É Consumidor Vencedor?": vencedor,
            "Enviado por:": responsavel
        }

        # Envia para o Excel Online
        self.salvar_na_planilha_online(resultado)
        
        return resultado
