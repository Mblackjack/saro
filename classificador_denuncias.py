# -*- coding: utf-8 -*-
import json
import os
import unicodedata
import streamlit as st
import random
from typing import Dict, Optional

class ClassificadorDenuncias:
    def __init__(self):
        # No modo simulação, não precisamos travar se a chave estiver vazia
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
        """
        MODO SIMULAÇÃO: Este método finge que chama a IA.
        """
        # 1. Identificação de Município (Lógica local - continua funcionando real)
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

        # 2. SIMULAÇÃO DE INTELIGÊNCIA ARTIFICIAL
        # Aqui sorteamos um tema real da sua base para simular a classificação
        temas_reais = list(self.temas_subtemas.keys())
        tema_simulado = random.choice(temas_reais) if temas_reais else "Serviços"
        
        # Simulamos a extração de uma empresa (pegando a primeira palavra em maiúscula, por exemplo)
        palavras = denuncia.split()
        empresa_simulada = "Empresa Teste SA"
        for p in palavras:
            if p.istitle() and len(p) > 3: # Se a palavra começar com maiúscula
                empresa_simulada = p
                break

        dados_ia = {
            "tema": tema_simulado,
            "subtema": "Simulação de Problema",
            "empresa": empresa_simulada,
            "resumo": f"Denúncia referente a {tema_simulado.lower()} identificada no modo de teste."
        }

        # Simula um pequeno delay para parecer real
        import time
        time.sleep(1) 

        return {
            "num_comunicacao": num_comunicacao,
            "num_mprj": num_mprj,
            "endereco": endereco,
            "denuncia": denuncia,
            "municipio": promotoria_info["municipio_oficial"],
            "promotoria": promotoria_info["promotoria"],
            "email": promotoria_info["email"],
            "telefone": promotoria_info["telefone"],
            "tema": dados_ia["tema"],
            "subtema": dados_ia["subtema"],
            "empresa": dados_ia["empresa"],
            "resumo": dados_ia["resumo"]
        }
