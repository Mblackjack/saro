# 🚀 Guia Rápido - Sistema de Classificação de Denúncias MPRJ

## Como Usar (Modo Mais Simples)

### 1️⃣ Execute o programa interativo:

```bash
python3 /home/ubuntu/mprj_denuncias/processar_denuncia.py
```

### 2️⃣ Digite o endereço quando solicitado:

```
📍 ENDEREÇO DA DENÚNCIA:
   Digite o endereço completo: Rua da Conceição, 123 - Centro, Niterói - RJ
```

### 3️⃣ Digite a denúncia quando solicitado:

```
📝 DESCRIÇÃO DA DENÚNCIA:
   Digite a denúncia: Comprei um celular na loja Magazine Luiza e o produto veio com defeito.
```

### 4️⃣ O sistema retorna automaticamente:

```
✅ CLASSIFICAÇÃO REALIZADA COM SUCESSO

🏛️  PROMOTORIA: PROMOTORIA DE JUSTIÇA DE TUTELA COLETIVA...
📧 E-MAIL: pjtccnit@mprj.mp.br
📞 TELEFONE: 2718-9954 / 2717-2209 / 2620-8495

📂 TEMA: Comércio
📑 SUBTEMA: Lojas físicas em geral

🏢 EMPRESA: Magazine Luiza
```

---

## Modo Linha de Comando (Para Usuários Avançados)

```bash
python3 /home/ubuntu/mprj_denuncias/classificador_denuncias.py \
  "Rua da Conceição, 123 - Centro, Niterói - RJ" \
  "Comprei um celular na loja Magazine Luiza e o produto veio com defeito."
```

---

## 📋 O que você precisa fornecer:

1. **Endereço** - Endereço completo com município do Rio de Janeiro
2. **Denúncia** - Descrição do problema/denúncia

## 📤 O que o sistema retorna:

1. **Promotoria** - Promotoria responsável pelo município
2. **Tema** - Categoria principal da denúncia
3. **Subtema** - Subcategoria específica
4. **Empresa** - Nome da empresa envolvida (se mencionada)

---

## 💾 Onde encontrar os resultados:

Os resultados são salvos automaticamente em:
```
/home/ubuntu/mprj_denuncias/ultimo_resultado.json
```

---

## ❓ Dúvidas?

Consulte a documentação completa em:
```
/home/ubuntu/mprj_denuncias/README.md
```
