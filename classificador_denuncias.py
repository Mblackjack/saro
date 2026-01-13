# -*- coding: utf-8 -*-
import json
import os
import unicodedata
import streamlit as st
import random
import time
from typing import Dict, Optional

class ClassificadorDenuncias:
    def __init__(self):
        # No modo simulação, apenas carregamos as bases locais
        self.base_path = os.path.dirname(os.path.abspath(__file__))
        self.carregar_bases()

    def carregar_bases(self):
        """Carrega os arquivos JSON para garantir que o sistema de promotorias funcione"""
        try:
            with open(os.path.join(self.base_path, "base_temas_subtemas.json"), 'r', encoding='utf-8') as f:
                self.temas_subtemas = json.load(f)
            with open(os.path.join(self.base_path, "base_promotorias.json"), 'r', encoding='utf-8') as f:
                self.base_promotorias = json.load(f)
        except Exception as e:
            st.error(f"❌ Erro ao carregar bases JSON: {e}")
            st.stop()
            
        # Mapeamento real de municípios (isso continuará funcionando 100%)
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
        if not texto: return ""
        return "".join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')

    def processar_denuncia(self, endereco: str, denuncia: str, num_comunicacao: str = "", num_mprj: str = "") -> Dict:
        """
        MODO SIMULAÇÃO: Ignora a OpenAI e gera dados fictícios baseados no seu JSON.
        """
        # 1. Identificação de Município (Lógica local - continua REAL)
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

        # 2. SIMULAÇÃO DE IA (Mock)
        # Sorteia um tema real do seu JSON
        temas_disponiveis = list(self.temas_subtemas.keys())
        tema_fake = random.choice(temas_disponiveis) if temas_disponiveis else "Serviços"
        
        # Tenta pegar a primeira palavra em maiúscula para fingir que achou a empresa
        palavras = denuncia.split()
        empresa_fake = "Empresa Identificada (Simulação)"
        for p in palavras:
            if len(p) > 3 and p[0].isupper() and p.isalpha():
                empresa_fake = p
                break

        # Simula o tempo de resposta da IA
        time.sleep(0.8)

        return {
            "num_comunicacao": num_comunicacao or "N/A",
            "num_mprj": num_mprj or "N/A",
            "endereco": endereco,
            "denuncia": denuncia,
            "municipio": promotoria_info["municipio_oficial"],
            "promotoria": promotoria_info["promotoria"],
            "email": promotoria_info["email"],
            "telefone": promotoria_info["telefone"],
            "tema": tema_fake,
            "subtema": "Problema Identificado (Modo Teste)",
            "empresa": empresa_fake,
            "resumo": f"Denúncia referente a {tema_fake.lower()} (Simulação de processamento offline)."
        }
