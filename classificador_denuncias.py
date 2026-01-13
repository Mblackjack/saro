import json
import os
import unicodedata
import streamlit as st
import google.generativeai as genai
from typing import Dict

class ClassificadorDenuncias:
    def __init__(self):
        # 1. Configuração de API (Evita erro 404 de versão)
        api_key = st.secrets.get("GOOGLE_API_KEY")
        if not api_key:
            st.error("❌ Erro: Chave de API não configurada.")
            st.stop()

        genai.configure(api_key=api_key)
        # Usamos o modelo Flash por ser mais rápido na extração de dados
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        
        self.base_path = os.path.dirname(os.path.abspath(__file__))
        self.carregar_bases()

    def carregar_bases(self):
        try:
            with open(os.path.join(self.base_path, "base_temas_subtemas.json"), 'r', encoding='utf-8') as f:
                self.temas_subtemas = json.load(f)
            with open(os.path.join(self.base_path, "base_promotorias.json"), 'r', encoding='utf-8') as f:
                self.base_promotorias = json.load(f)
        except Exception as e:
            st.error(f"❌ Erro ao carregar bases JSON: {e}")
            st.stop()
            
        self.municipio_para_promotoria = {}
        for d in self.base_promotorias.values():
            for m in d.get("municipios", []):
                self.municipio_para_promotoria[self.remover_acentos(m.upper())] = {
                    "promotoria": d["promotoria"],
                    "email": d["email"],
                    "telefone": d["telefone"],
                    "municipio_oficial": m
                }

    def remover_acentos(self, texto: str) -> str:
        if not texto: return ""
        return "".join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')

    def processar_denuncia(self, endereco: str, denuncia: str, num_comunicacao: str = "", num_mprj: str = "") -> Dict:
        # Identificação Geográfica (Promotoria)
        municipio_info = None
        end_limpo = self.remover_acentos(endereco.upper())
        for m_chave, info in self.municipio_para_promotoria.items():
            if m_chave in end_limpo:
                municipio_info = info
                break
        
        if not municipio_info:
            municipio_info = {"promotoria": "Não identificada", "email": "N/A", "telefone": "N/A", "municipio_oficial": "Não identificado"}

        # Preparação do dicionário de regras para a IA (Extração por similaridade)
        regras_hierarquicas = ""
        for tema, subtemas in self.temas_subtemas.items():
            regras_hierarquicas += f"TEMA: {tema} | SUBTEMAS POSSÍVEIS: {subtemas}\n"

        # PROMPT COM O PASSO A PASSO SOLICITADO
        prompt = f"""Você é um analista de triagem do Ministério Público. Siga rigorosamente este processo:

        1. ANÁLISE: Leia a denúncia abaixo.
        2. EXTRAÇÃO: Identifique palavras-chave e caracteres que indiquem o assunto.
        3. ENQUADRAMENTO DE TEMA: Escolha o tema mais similar da lista fornecida.
        4. ENQUADRAMENTO DE SUBTEMA: Escolha obrigatoriamente um subtema que esteja DENTRO do array do tema escolhido.

        LISTA OFICIAL DE TEMAS E ARRAYS DE SUBTEMAS:
        {regras_hierarquicas}

        DENÚNCIA: "{denuncia}"

        RESPOSTA: Retorne APENAS um JSON com os campos: 
        {{"tema": "...", "subtema": "...", "empresa": "...", "resumo": "..."}}
        """

        resultado = {
            "num_comunicacao": num_comunicacao, "num_mprj": num_mprj,
            "endereco": endereco, "denuncia": denuncia,
            "municipio": municipio_info["municipio_oficial"],
            "promotoria": municipio_info["promotoria"],
            "email": municipio_info["email"],
            "telefone": municipio_info["telefone"],
            "tema": "A definir", "subtema": "A definir",
            "empresa": "Não identificada", "resumo": "Processando..."
        }

        try:
            response = self.model.generate_content(prompt)
            # Limpeza de caracteres markdown do JSON
            raw_json = response.text.replace('```json', '').replace('```', '').strip()
            dados_ia = json.loads(raw_json)
            
            # Validação: Garante que o subtema pertence ao array do tema no JSON
            tema_ia = dados_ia.get("tema")
            subtema_ia = dados_ia.get("subtema")
            
            if tema_ia in self.temas_subtemas and subtema_ia in self.temas_subtemas[tema_ia]:
                resultado.update(dados_ia)
            else:
                # Se a IA errou o subtema, tentamos forçar o primeiro do array ou manter erro
                resultado["tema"] = tema_ia if tema_ia in self.temas_subtemas else "Outros"
                resultado["subtema"] = subtema_ia # Mantém o que ela enviou para você ver o erro, ou poderia forçar 'Não classificado'
                resultado["empresa"] = dados_ia.get("empresa", "Não identificada")
                resultado["resumo"] = dados_ia.get("resumo", "")
                
        except Exception as e:
            st.error(f"Erro no processamento: {e}")

        return resultado
