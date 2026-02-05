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
        self.base_path = os.path.dirname(os.path.abspath(__file__))
        self.db_path = os.path.join(self.base_path, "saro_database.db")
        
        # Pega a chave dos Secrets do Streamlit
        api_key = st.secrets.get("OPENAI_API_KEY")
        if not api_key:
            st.error("❌ Erro: Chave 'OPENAI_API_KEY' não encontrada nos Secrets do Streamlit.")
            st.stop()
            
        self.client = OpenAI(api_key=api_key)
        self.model_name = "gpt-4o-mini"
        
        self.carregar_bases()
        self.inicializar_banco()

    # ... (mantenha as funções inicializar_banco, carregar_bases e remover_acentos como estão)

    def processar_denuncia(self, endereco, denuncia, num_com, num_mprj, vencedor, responsavel):
        # 1. Lógica de Localidade
        municipio_nome = "Não identificado"
        promotoria = "Não identificada"
        end_upper = self.remover_acentos(endereco.upper())
        for m_chave, info in self.municipio_para_promotoria.items():
            if self.remover_acentos(m_chave) in end_upper:
                municipio_nome = info["municipio_oficial"]
                promotoria = info["promotoria"]
                break

        # 2. Chamada à IA (OpenAI)
        catalogo = json.dumps(self.temas_subtemas, ensure_ascii=False)
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": f"Você é um classificador do MPRJ. Use estritamente este catálogo JSON para classificar: {catalogo}. Responda apenas com um objeto JSON contendo as chaves: tema, subtema, empresa, resumo (máximo 10 palavras)."},
                    {"role": "user", "content": f"Denúncia: {denuncia}"}
                ],
                response_format={"type": "json_object"} # Isso força a OpenAI a devolver um JSON válido
            )
            
            conteudo_resposta = response.choices[0].message.content
            dados_ia = json.loads(conteudo_resposta)
            
        except Exception as e:
            # Se der erro, ele vai mostrar no console do Streamlit para você investigar
            st.sidebar.error(f"Detalhe técnico do erro: {e}")
            dados_ia = {
                "tema": "Outros", 
                "subtema": "Geral", 
                "empresa": "N/D", 
                "resumo": f"Erro técnico na IA: {str(e)[:50]}"
            }

        # 3. Montar dados finais para o Banco
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

        # 4. Salvar no Banco SQLite
        sucesso = self.salvar_no_banco(dados_final)
        
        return dados_final, sucesso

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
        except Exception as e:
            st.error(f"Erro ao salvar no banco: {e}")
            return False
