# -*- coding: utf-8 -*-
import json
import os
import unicodedata
import streamlit as st
import google.generativeai as genai
import pandas as pd
from datetime import datetime

class ClassificadorDenuncias:
    def __init__(self):
        api_key = st.secrets.get("GOOGLE_API_KEY")
        genai.configure(api_key=api_key)
        
        self.model = genai.GenerativeModel(
            model_name='gemini-1.5-flash',
            generation_config={"temperature": 0.1}
        )

        self.base_path = os.path.dirname(os.path.abspath(__file__))
        self.caminho_excel = os.path.join(self.base_path, "Ouvidorias_SARO_Oficial.xlsx")
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

    def salvar_no_excel(self, dados: dict):
        """Salva localmente no servidor do Streamlit"""
        try:
            df_novo = pd.DataFrame([dados])
            if os.path.exists(self.caminho_excel):
                df_antigo = pd.read_excel(self.caminho_excel)
                df_final = pd.concat([df_antigo, df_novo], ignore_index=True)
            else:
                df_final = df_novo
            
            df_final.to_excel(self.caminho_excel, index=False)
            return True
        except Exception as e:
            st.error(f"Erro ao salvar arquivo: {e}")
            return False

    def processar_denuncia(self, endereco, denuncia, num_com, num_mprj, vencedor, responsavel):
        # 1. Localização
        municipio_nome = "Não identificado"
        promotoria = "Não identificada"
        end_upper = self.remover_acentos(endereco.upper())
        for m_chave, info in self.municipio_para_promotoria.items():
            if self.remover_acentos(m_chave) in end_upper:
                municipio_nome = info["municipio_oficial"]
                promotoria = info["promotoria"]
                break

        # 2. IA
        prompt = f"Analise esta denúncia e retorne APENAS um JSON com tema, subtema, empresa e resumo (máx 10 palavras): {denuncia}"
        try:
            res = self.model.generate_content(prompt)
            # Limpeza básica do texto para garantir o JSON
            json_text = res.text.replace('```json', '').replace('```', '').strip()
            dados_ia = json.loads(json_text)
        except:
            dados_ia = {"tema": "Outros", "subtema": "Geral", "empresa": "Não identificada", "resumo": "Verificar descrição"}

        # 3. Formatação conforme sua solicitação
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

        self.salvar_no_excel(resultado)
        return resultado
