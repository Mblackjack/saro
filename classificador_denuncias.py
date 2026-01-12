# -*- coding: utf-8 -*-
import json
import os
import unicodedata
import streamlit as st
from openai import OpenAI

class ClassificadorDenuncias:
    def __init__(self):
        # 1. Tenta pegar a chave de todas as formas possíveis
        api_key = st.secrets.get("OPENAI_API_KEY")
        
        if not api_key:
            st.error("🚨 CHAVE NÃO ENCONTRADA! Verifique o menu 'Secrets' no Streamlit Cloud.")
            st.stop()

        self.client = OpenAI(api_key=api_key)
        self.base_path = os.path.dirname(os.path.abspath(__file__))
        self.carregar_bases()

    def carregar_bases(self):
        try:
            with open(os.path.join(self.base_path, "base_temas_subtemas.json"), 'r', encoding='utf-8') as f:
                self.temas_subtemas = json.load(f)
            with open(os.path.join(self.base_path, "base_promotorias.json"), 'r', encoding='utf-8') as f:
                self.base_promotorias = json.load(f)
        except Exception as e:
            st.error(f"❌ Erro ao carregar arquivos JSON: {e}")
            st.stop()
            
        self.municipio_para_promotoria = {
            m.upper(): {"promotoria": d["promotoria"], "email": d["email"], "telefone": d["telefone"], "municipio_oficial": m}
            for nucleo, d in self.base_promotorias.items() for m in d["municipios"]
        }

    def remover_acentos(self, texto: str):
        if not texto: return ""
        return "".join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')

    def processar_denuncia(self, endereco, denuncia, num_comunicacao="", num_mprj=""):
        # Localização de Município (Local)
        municipio_nome = None
        end_upper = self.remover_acentos(endereco.upper())
        for m_chave in self.municipio_para_promotoria.keys():
            if self.remover_acentos(m_chave) in end_upper:
                municipio_nome = self.municipio_para_promotoria[m_chave]["municipio_oficial"]
                break
        
        promotoria_info = self.municipio_para_promotoria.get(
            municipio_nome.upper() if municipio_nome else "", 
            {"promotoria": "Promotoria não identificada", "email": "N/A", "telefone": "N/A", "municipio_oficial": municipio_nome or "Não identificado"}
        )

        # LISTA DE TEMAS PARA A IA
        temas_lista = list(self.temas_subtemas.keys())

        # PROMPT DE ALTO IMPACTO (Estilo Manus AI)
        prompt = f"""Responda obrigatoriamente em JSON.
Analise a denúncia: "{denuncia}"

Extraia os dados seguindo estas regras:
- tema: Escolha um desta lista: {temas_lista}
- subtema: O problema em 3 palavras.
- empresa: O nome da marca ou empresa citada.
- resumo: Uma frase curta começando com 'Denúncia referente a'.

JSON de saída:"""

        # REMOVEMOS O TRY/EXCEPT PARA O ERRO APARECER NA TELA SE FALHAR
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Você é um robô que só responde JSON técnico."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0
        )
        
        dados_ia = json.loads(response.choices[0].message.content)

        return {
            "num_comunicacao": num_comunicacao,
            "num_mprj": num_mprj,
            "endereco": endereco,
            "denuncia": denuncia,
            "municipio": promotoria_info["municipio_oficial"],
            "promotoria": promotoria_info["promotoria"],
            "email": promotoria_info["email"],
            "telefone": promotoria_info["telefone"],
            "tema": dados_ia.get("tema", "Serviços"),
            "subtema": dados_ia.get("subtema", "Não identificado"),
            "empresa": dados_ia.get("empresa", "Não identificada"),
            "resumo": dados_ia.get("resumo", "Resumo indisponível")
        }
