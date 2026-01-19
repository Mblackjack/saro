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
        # Configuração da API
        api_key = st.secrets.get("GOOGLE_API_KEY")
        if not api_key:
            st.error("ERRO: GOOGLE_API_KEY não encontrada nos Secrets.")
            st.stop()
            
        genai.configure(api_key=api_key)
        
        # Inicialização do Modelo (Gemini 1.5 Flash)
        self.model = genai.GenerativeModel(
            model_name='gemini-1.5-flash',
            generation_config={"temperature": 0.1}
        )

        self.base_path = os.path.dirname(os.path.abspath(__file__))
        self.caminho_excel = os.path.join(self.base_path, "Ouvidorias_SARO_Oficial.xlsx")
        self.carregar_bases()

    def carregar_bases(self):
        """Carrega as bases de dados JSON para apoio à classificação e geolocalização"""
        try:
            with open(os.path.join(self.base_path, "base_temas_subtemas.json"), 'r', encoding='utf-8') as f:
                self.temas_subtemas = json.load(f)
            with open(os.path.join(self.base_path, "base_promotorias.json"), 'r', encoding='utf-8') as f:
                self.base_promotorias = json.load(f)
        except Exception as e:
            st.error(f"Erro ao carregar arquivos JSON: {e}")
            st.stop()
            
        self.municipio_para_promotoria = {
            m.upper(): {"promotoria": d["promotoria"], "municipio_oficial": m}
            for nucleo, d in self.base_promotorias.items() for m in d["municipios"]
        }

    def remover_acentos(self, texto: str) -> str:
        if not texto: return ""
        return "".join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')

    def salvar_no_excel(self, dados: dict):
        """Salva a linha de dados no arquivo Excel local do servidor"""
        try:
            # Garante que as colunas estejam na ordem correta solicitada
            ordem_colunas = [
                "Nº Comunicação", "Nº MPRJ", "Promotoria", "Município", 
                "Data", "Denúncia", "Resumo", "Tema", "Subtema", 
                "Empresa", "É Consumidor Vencedor?", "Enviado por:"
            ]
            
            df_novo = pd.DataFrame([dados])[ordem_colunas]
            
            if os.path.exists(self.caminho_excel):
                df_antigo = pd.read_excel(self.caminho_excel)
                df_final = pd.concat([df_antigo, df_novo], ignore_index=True)
            else:
                df_final = df_novo
            
            df_final.to_excel(self.caminho_excel, index=False)
            return True
        except Exception as e:
            st.error(f"Erro ao salvar no Excel: {e}")
            return False

    def processar_denuncia(self, endereco, denuncia, num_com, num_mprj, vencedor, responsavel):
        # 1. Identificação da Promotoria e Município
        municipio_nome = "Não identificado"
        promotoria = "Não identificada"
        end_upper = self.remover_acentos(endereco.upper())
        for m_chave, info in self.municipio_para_promotoria.items():
            if self.remover_acentos(m_chave) in end_upper:
                municipio_nome = info["municipio_oficial"]
                promotoria = info["promotoria"]
                break

        # 2. Inteligência Artificial (Classificação)
        catalogo_txt = json.dumps(self.temas_subtemas, ensure_ascii=False)
        prompt = f"""
        Você é um assistente jurídico do Ministério Público especializado em Consumidor.
        Analise a denúncia: "{denuncia}"

        TAREFAS:
        1. Escolha o TEMA e SUBTEMA baseando-se NESTE catálogo: {catalogo_txt}
        2. Identifique a EMPRESA ou ÓRGÃO reclamado.
        3. Escreva um RESUMO dos fatos em NO MÁXIMO 10 palavras.

        Responda APENAS em JSON puro:
        {{
            "tema": "nome do tema",
            "subtema": "nome do subtema",
            "empresa": "nome da empresa",
            "resumo": "seu resumo curto"
        }}
        """

        try:
            res = self.model.generate_content(prompt)
            # Limpeza de possíveis marcações Markdown da IA
            json_text = res.text.replace('```json', '').replace('```', '').strip()
            dados_ia = json.loads(json_text)
        except:
            dados_ia = {"tema": "Outros", "subtema": "Geral", "empresa": "Não identificada", "resumo": "Erro no processamento IA"}

        # 3. Montagem do Resultado Final (Ordem do Usuário)
        resultado = {
            "Nº Comunicação": num_com,
            "Nº MPRJ": num_mprj,
            "Promotoria": promotoria,
            "Município": municipio_nome,
            "Data": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "Denúncia": denuncia,
            "Resumo": dados_ia.get("resumo", ""),
            "Tema": dados_ia.get("tema", "Outros"),
            "Subtema": dados_ia.get("subtema", "Geral"),
            "Empresa": str(dados_ia.get("empresa", "Não identificada")).strip().title(),
            "É Consumidor Vencedor?": vencedor,
            "Enviado por:": responsavel
        }

        # Salva no arquivo para posterior download
        self.salvar_no_excel(resultado)
        return resultado
