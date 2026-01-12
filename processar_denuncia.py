#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Interface Simplificada para Processamento de Denúncias - MPRJ
"""

from classificador_denuncias import ClassificadorDenuncias
import json

def main():
    print("=" * 80)
    print("SISTEMA DE PROCESSAMENTO DE DENÚNCIAS - MPRJ")
    print("Ministério Público do Rio de Janeiro")
    print("=" * 80)
    print()
    
    # Inicializar classificador
    classificador = ClassificadorDenuncias()
    
    # Coletar dados
    print("📍 ENDEREÇO DA DENÚNCIA:")
    endereco = input("   Digite o endereço completo: ").strip()
    print()
    
    print("📝 DESCRIÇÃO DA DENÚNCIA:")
    denuncia = input("   Digite a denúncia: ").strip()
    print()
    
    if not endereco or not denuncia:
        print("❌ Erro: Endereço e denúncia são obrigatórios!")
        return
    
    print("⏳ Processando denúncia...")
    print()
    
    # Processar denúncia
    resultado = classificador.processar_denuncia(endereco, denuncia)
    
    # Exibir resultado formatado
    print(classificador.formatar_resultado(resultado))
    
    # Salvar resultado
    with open('/home/ubuntu/mprj_denuncias/ultimo_resultado.json', 'w', encoding='utf-8') as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)
    
    print("💾 Resultado salvo em: /home/ubuntu/mprj_denuncias/ultimo_resultado.json")
    print()

if __name__ == "__main__":
    main()
