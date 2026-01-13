# -*- coding: utf-8 -*-
"""
Classificador de Denúncias do Consumidor - SARO v5.4
Restrição rigorosa ao catálogo oficial e compatibilidade total com Streamlit Cloud.
"""

import json
import os
import re
import unicodedata
from typing import Dict, List, Optional
import streamlit as st

# Importar OpenAI com tratamento de erro
try:
    from openai import OpenAI
except ImportError:
    st.error("❌ Erro: Biblioteca OpenAI não instalada. Por favor, aguarde o redeploy automático.")
    st.stop()

class ClassificadorDenuncias:
    def __init__(self):
        # Obter chave da API de forma robusta
        api_key = self._obter_api_key()
        
        if not api_key:
            st.error(
                "❌ **Chave da OpenAI não configurada!**\n\n"
                "Para usar o SARO, siga estes passos:\n\n"
                "1️⃣ Acesse o painel do seu app no Streamlit Cloud\n"
                "2️⃣ Clique em **'Manage app'** (canto inferior direito)\n"
                "3️⃣ Vá em **Settings > Secrets**\n"
                "4️⃣ Cole exatamente isto:\n"
                "```\n"
                "OPENAI_API_KEY = \"sua-chave-aqui\"\n"
                "```\n"
                "5️⃣ Clique em **Save**\n\n"
                "**Gerar chave:** https://platform.openai.com/api-keys"
            )
            st.stop()
        
        try:
            self.client = OpenAI(api_key=api_key)
        except Exception as e:
            st.error(f"❌ Erro ao conectar com OpenAI: {str(e)}")
            st.stop()
        
        self.base_path = os.path.dirname(os.path.abspath(__file__))
        self.carregar_bases()

    def _obter_api_key(self) -> Optional[str]:
        """Tenta obter a chave de API de múltiplas fontes"""
        # 1. Tentar Secrets do Streamlit (Recomendado para Cloud)
        try:
            if "OPENAI_API_KEY" in st.secrets:
                return st.secrets["OPENAI_API_KEY"]
        except:
            pass
            
        # 2. Tentar Variável de Ambiente
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            return api_key
            
        return None

    def carregar_bases(self):
        """Carrega as bases de dados de temas, subtemas e promotorias"""
        with open(f"{self.base_path}/base_temas_subtemas.json", 'r', encoding='utf-8') as f:
            self.temas_subtemas = json.load(f)
        
        with open(f"{self.base_path}/base_promotorias.json", 'r', encoding='utf-8') as f:
            self.base_promotorias = json.load(f)
            
        # Criar mapeamento direto de município para dados da promotoria
        self.municipio_para_promotoria = {}
        for nucleo, dados in self.base_promotorias.items():
            for municipio in dados["municipios"]:
                self.municipio_para_promotoria[municipio.upper()] = {
                    "promotoria": dados["promotoria"],
                    "email": dados["email"],
                    "telefone": dados["telefone"],
                    "municipio_oficial": municipio
                }

    def remover_acentos(self, texto: str) -> str:
        """Remove acentos de uma string"""
        if not texto: return ""
        return "".join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')

    def extrair_municipio(self, endereco: str) -> Optional[str]:
        """Extrai o município do endereço fornecido usando busca textual e LLM como fallback"""
        if not endereco: return None
        
        endereco_upper = self.remover_acentos(endereco.upper())
        
        # Busca direta
        for municipio_chave in self.municipio_para_promotoria.keys():
            municipio_chave_sem_acento = self.remover_acentos(municipio_chave)
            if municipio_chave_sem_acento in endereco_upper:
                return self.municipio_para_promotoria[municipio_chave]["municipio_oficial"]
        
        # Fallback com LLM
        try:
            response = self.client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {"role": "system", "content": "Você é um assistente que extrai nomes de cidades de endereços brasileiros. Responda APENAS com o nome da cidade, sem explicações."},
                    {"role": "user", "content": f"Qual é a cidade neste endereço? '{endereco}'"}
                ],
                temperature=0.0,
                max_tokens=50
            )
            municipio_extraido = response.choices[0].message.content.strip().upper()
            municipio_extraido_sem_acento = self.remover_acentos(municipio_extraido)
            
            for municipio_chave in self.municipio_para_promotoria.keys():
                municipio_chave_sem_acento = self.remover_acentos(municipio_chave)
                if municipio_chave_sem_acento == municipio_extraido_sem_acento:
                    return self.municipio_para_promotoria[municipio_chave]["municipio_oficial"]
        except Exception:
            pass
        
        return None

    def gerar_resumo(self, denuncia: str) -> str:
        """Gera um resumo de uma frase da denúncia"""
        try:
            response = self.client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {"role": "system", "content": "Você é um assistente que cria resumos concisos de denúncias. Responda com UMA ÚNICA FRASE começando com 'Denúncia referente a'. Máximo 15 palavras."},
                    {"role": "user", "content": f"Resuma esta denúncia: {denuncia}"}
                ],
                temperature=0.0,
                max_tokens=50
            )
            return response.choices[0].message.content.strip()
        except Exception:
            return "Denúncia referente a reclamação do consumidor."

    def classificar_denuncia(self, denuncia: str) -> Dict:
        """Classifica a denúncia usando LLM com restrição rigorosa ao catálogo"""
        # Preparar catálogo para o prompt
        catalogo_str = ""
        for tema, subtemas in self.temas_subtemas.items():
            catalogo_str += f"- TEMA: {tema}\n  SUBTEMAS: {', '.join(subtemas)}\n"

        try:
            response = self.client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {"role": "system", "content": f"""Você é um classificador de denúncias do MPRJ. 
                    Sua tarefa é classificar a denúncia EXATAMENTE de acordo com o catálogo oficial abaixo.
                    
                    REGRAS OBRIGATÓRIAS:
                    1. Escolha APENAS um TEMA da lista fornecida.
                    2. Escolha APENAS um SUBTEMA que pertença ao TEMA escolhido.
                    3. NUNCA crie temas ou subtemas novos. Se estiver em dúvida, escolha o mais próximo.
                    4. Identifique a empresa mencionada. Se não houver, use "Empresa não identificada".
                    
                    CATÁLOGO OFICIAL:
                    {catalogo_str}
                    
                    Retorne APENAS um JSON no formato:
                    {{"tema": "NOME_DO_TEMA", "subtema": "NOME_DO_SUBTEMA", "empresa": "NOME_DA_EMPRESA"}}"""},
                    {"role": "user", "content": f"Classifique esta denúncia: {denuncia}"}
                ],
                temperature=0.0,
                max_tokens=200
            )
            
            try:
                resultado = json.loads(response.choices[0].message.content.strip())
                
                # Validação final contra o catálogo
                tema_escolhido = resultado.get("tema", "Serviços")
                if tema_escolhido not in self.temas_subtemas:
                    tema_escolhido = "Serviços"
                
                subtemas_validos = self.temas_subtemas[tema_escolhido]
                subtema_escolhido = resultado.get("subtema", subtemas_validos[0])
                
                if subtema_escolhido not in subtemas_validos:
                    # Tentar encontrar o subtema mais próximo ou usar o primeiro da lista
                    subtema_escolhido = subtemas_validos[0]
                
                return {
                    "tema": tema_escolhido,
                    "subtema": subtema_escolhido,
                    "empresa": resultado.get("empresa", "Empresa não identificada")
                }
            except Exception:
                return {
                    "tema": "Serviços",
                    "subtema": "Serviços On-line (E-mails, Aplicativos, Redes Sociais, Hospedagem de Sites, etc.)",
                    "empresa": "Empresa não identificada"
                }
        except Exception:
            return {
                "tema": "Serviços",
                "subtema": "Serviços On-line (E-mails, Aplicativos, Redes Sociais, Hospedagem de Sites, etc.)",
                "empresa": "Empresa não identificada"
            }

    def processar_denuncia(self, endereco: str, denuncia: str, num_comunicacao: str = "", num_mprj: str = "") -> Dict:
        """Processa uma denúncia completa"""
        municipio = self.extrair_municipio(endereco)
        
        if municipio and municipio.upper() in self.municipio_para_promotoria:
            promotoria_info = self.municipio_para_promotoria[municipio.upper()]
        else:
            promotoria_info = {
                "promotoria": "Promotoria não identificada",
                "email": "N/A",
                "telefone": "N/A",
                "municipio_oficial": municipio or "Não identificado"
            }
        
        classificacao = self.classificar_denuncia(denuncia)
        resumo = self.gerar_resumo(denuncia)
        
        return {
            "num_comunicacao": num_comunicacao or "N/A",
            "num_mprj": num_mprj or "N/A",
            "endereco": endereco,
            "denuncia": denuncia,
            "municipio": promotoria_info.get("municipio_oficial", "Não identificado"),
            "promotoria": promotoria_info.get("promotoria", "Promotoria não identificada"),
            "email": promotoria_info.get("email", "N/A"),
            "telefone": promotoria_info.get("telefone", "N/A"),
            "tema": classificacao.get("tema", "Serviços"),
            "subtema": classificacao.get("subtema", "Não classificado"),
            "empresa": classificacao.get("empresa", "Empresa não identificada"),
            "resumo": resumo
        }
