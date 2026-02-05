# -*- coding: utf-8 -*-
import json
import os
import sqlite3
import unicodedata
import streamlit as st
from openai import OpenAI
from datetime import datetime

class ClassificadorDenuncias:
    def __init__(self):
        # 1. Definir caminhos primeiro
        self.base_path = os.path.dirname(os.path.abspath(__file__))
        self.db_path = os.path.join(self.base_path, "saro_database.db")
        
        # 2. Configuração OpenAI
        api_key = st.secrets.get("OPENAI_API_KEY")
        if not api_key:
            st.error("❌ Erro: OPENAI_API_KEY não encontrada.")
            st.stop()
            
        self.client = OpenAI(api_key=api_key)
        self.model_name = "gpt-4o-mini"
        
        # 3. Inicializar dados
        self.carregar_bases()
        self.inicializar_banco()

    def inicializar_banco(self):
        """Cria a tabela no banco de dados se ela não existir"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ouvidorias (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                num_com TEXT,
                num_mprj TEXT,
                data TEXT,
                municipio TEXT,
                promotoria TEXT,
                tema TEXT,
                subtema TEXT,
                empresa TEXT,
                denuncia TEXT,
                resumo TEXT,
                vencedor TEXT,
                responsavel TEXT
            )
        ''')
        conn.commit()
        conn.close()

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

    def salvar_no_banco(self, d):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO ouvidorias (num_com, num_mprj, data, municipio, promotoria, tema, subtema, empresa, denuncia, resumo, vencedor, responsavel)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (d['num_com'], d['num_mprj'], d['data'], d['municipio'], d['promotoria'], d['tema'], d['subtema'], d['empresa'], d['denuncia'], d['resumo'], d['vencedor'], d['responsavel']))
            conn.commit()
            conn.close()
            return True
        except:
            return False

    def processar_denuncia(self, endereco, denuncia, num_com, num_mprj, vencedor, responsavel):
        # Localidade
        municipio_nome = "Não identificado"
        promotoria = "Não identificada"
        end_upper = self.remover_acentos(endereco.upper())
        for m_chave, info in self.municipio_para_promotoria.items():
            if self.remover_acentos(m_chave) in end_upper:
                municipio_nome = info["municipio_oficial"]
                promotoria = info["promotoria"]
                break

        # IA GPT
        catalogo = json.dumps(self.temas_subtemas, ensure_ascii=False)
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": f"Você é um classificador do MPRJ. Use este catálogo: {catalogo}. Responda APENAS JSON puro."},
                    {"role": "user", "content": f"Classifique: {denuncia}. Retorne chaves: tema, subtema, empresa, resumo (máx 10 palavras)."}
                ],
                response_format={"type": "json_object"}
            )
            dados_ia = json.loads(response.choices[0].message.content)
        except:
            dados_ia = {"tema": "Outros", "subtema": "Geral", "empresa": "N/D", "resumo": "Erro IA"}

        dados_final = {
            "num_com": num_com, "num_mprj": num_mprj, "promotoria": promotoria,
            "municipio": municipio_nome, "data": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "denuncia": denuncia, "resumo": dados_ia.get("resumo"),
            "tema": dados_ia.get("tema"), "subtema": dados_ia.get("subtema"),
            "empresa": str(dados_ia.get("empresa")).title(),
            "vencedor": vencedor, "responsavel": responsavel
        }

        sucesso = self.salvar_no_banco(dados_final)
        return dados_final, sucesso
