# Sistema de Classificação Automática de Denúncias - MPRJ

Sistema desenvolvido para o **Ministério Público do Rio de Janeiro (MPRJ)** que processa denúncias automaticamente e identifica:

- ✅ **Promotoria** responsável pelo município
- ✅ **Tema** da denúncia
- ✅ **Subtema** específico
- ✅ **Empresa** envolvida

---

## 📋 Requisitos

O sistema já está configurado e pronto para uso. Requer apenas:

- Python 3.11+
- Biblioteca OpenAI (já instalada)
- Variável de ambiente `OPENAI_API_KEY` (já configurada)

---

## 🚀 Como Usar

### **Opção 1: Interface Interativa (Recomendado)**

Execute o script interativo que solicita os dados passo a passo:

```bash
python3 /home/ubuntu/mprj_denuncias/processar_denuncia.py
```

O sistema irá solicitar:
1. Endereço da denúncia
2. Descrição da denúncia

E retornará automaticamente todos os dados classificados.

---

### **Opção 2: Linha de Comando**

Para processar denúncias via linha de comando:

```bash
python3 /home/ubuntu/mprj_denuncias/classificador_denuncias.py '<endereço>' '<denúncia>'
```

**Exemplo:**

```bash
python3 /home/ubuntu/mprj_denuncias/classificador_denuncias.py \
  "Rua da Conceição, 123 - Centro, Niterói - RJ" \
  "Comprei um celular na loja Magazine Luiza e o produto veio com defeito."
```

---

### **Opção 3: Usar como Biblioteca Python**

Você pode importar o classificador em seus próprios scripts:

```python
from classificador_denuncias import ClassificadorDenuncias

# Inicializar
classificador = ClassificadorDenuncias()

# Processar denúncia
resultado = classificador.processar_denuncia(
    endereco="Av. Rio Branco, 500 - Centro, Rio de Janeiro - RJ",
    denuncia="Meu plano de saúde negou autorização para cirurgia."
)

# Exibir resultado formatado
print(classificador.formatar_resultado(resultado))

# Ou acessar dados individualmente
print(f"Promotoria: {resultado['promotoria']}")
print(f"Tema: {resultado['tema']}")
print(f"Subtema: {resultado['subtema']}")
print(f"Empresa: {resultado['empresa']}")
```

---

## 📂 Estrutura de Arquivos

```
/home/ubuntu/mprj_denuncias/
│
├── classificador_denuncias.py      # Sistema principal de classificação
├── processar_denuncia.py           # Interface interativa
├── base_temas_subtemas.json        # Base de dados de temas e subtemas
├── base_promotorias.json           # Base de dados de promotorias por município
├── temas.txt                       # Lista de temas (referência)
├── subtemas.txt                    # Lista de subtemas (referência)
├── promotorias.txt                 # Lista de promotorias (referência)
├── ultimo_resultado.json           # Último resultado processado
└── README.md                       # Esta documentação
```

---

## 📊 Formato de Saída

O sistema retorna os dados no seguinte formato:

```json
{
  "endereco": "Rua da Conceição, 123 - Centro, Niterói - RJ",
  "denuncia": "Comprei um celular na loja Magazine Luiza...",
  "municipio": "Niterói",
  "promotoria": "PROMOTORIA DE JUSTIÇA DE TUTELA COLETIVA...",
  "email": "pjtccnit@mprj.mp.br",
  "telefone": "2718-9954 / 2717-2209 / 2620-8495",
  "tema": "Comércio",
  "subtema": "Lojas físicas em geral",
  "empresa": "Magazine Luiza",
  "status": "sucesso",
  "mensagem": ""
}
```

O resultado também é salvo automaticamente em `ultimo_resultado.json`.

---

## 🎯 Exemplos de Uso

### **Exemplo 1: Denúncia sobre Comércio**

**Entrada:**
- **Endereço:** Rua da Conceição, 123 - Centro, Niterói - RJ
- **Denúncia:** Comprei um celular na loja Magazine Luiza e o produto veio com defeito. Tentei trocar mas a loja se recusou.

**Saída:**
- **Promotoria:** PROMOTORIA DE JUSTIÇA DE TUTELA COLETIVA DE DEFESA DO CONSUMIDOR E DO CONTRIBUINTE DO NÚCLEO NITERÓI
- **Tema:** Comércio
- **Subtema:** Lojas físicas em geral
- **Empresa:** Magazine Luiza

---

### **Exemplo 2: Denúncia sobre Plano de Saúde**

**Entrada:**
- **Endereço:** Av. Rio Branco, 500 - Centro, Rio de Janeiro - RJ
- **Denúncia:** Meu plano de saúde Unimed negou autorização para cirurgia urgente recomendada pelo médico.

**Saída:**
- **Promotoria:** PROTOCOLO DAS PROMOTORIAS DE JUSTIÇA DE TUTELA COLETIVA DE DEFESA DO CONSUMIDOR E DO CONTRIBUINTE DA CAPITAL
- **Tema:** Saúde
- **Subtema:** Planos de Saúde
- **Empresa:** Unimed

---

### **Exemplo 3: Denúncia sobre Telecomunicações**

**Entrada:**
- **Endereço:** Rua dos Pescadores, 89 - Braga, Cabo Frio - RJ
- **Denúncia:** A internet da Claro está com velocidade muito abaixo do contratado há mais de um mês.

**Saída:**
- **Promotoria:** 1ª PROMOTORIA DE JUSTIÇA DE TUTELA COLETIVA DO NÚCLEO CABO FRIO
- **Tema:** Telecomunicações
- **Subtema:** Internet (Conexão)
- **Empresa:** Claro

---

## 🗂️ Base de Dados

### **Temas Disponíveis (12)**

1. Alimentação
2. Comércio
3. Educação
4. Finanças
5. Habitação
6. Informações
7. Lazer
8. Produtos
9. Saúde
10. Serviços
11. Telecomunicações
12. Transporte

### **Promotorias Cobertas (26 Núcleos)**

O sistema cobre todos os municípios do Estado do Rio de Janeiro, incluindo:

- Capital (Rio de Janeiro)
- Angra dos Reis
- Araruama
- Barra do Piraí
- Cabo Frio
- Campos dos Goytacazes
- Cordeiro
- Duque de Caxias
- Itaboraí
- Itaguaí
- Itaperuna
- Macaé
- Magé
- Maricá
- Niterói
- Nova Friburgo
- Nova Iguaçu
- Santo Antônio de Pádua
- Petrópolis
- Resende
- São Gonçalo
- Teresópolis
- Três Rios
- Vassouras
- Volta Redonda

E mais de **90 municípios** associados a esses núcleos.

---

## 🔧 Funcionamento Técnico

O sistema utiliza **Inteligência Artificial (LLM)** para:

1. **Extrair o município** do endereço fornecido
2. **Classificar a denúncia** em tema e subtema apropriados
3. **Identificar a empresa** mencionada na denúncia

A identificação da **promotoria** é feita através de mapeamento direto município → promotoria usando a base de dados estruturada.

---

## ⚠️ Observações Importantes

- O sistema requer conexão com a internet para funcionar (usa API da OpenAI)
- Os resultados são salvos automaticamente em `ultimo_resultado.json`
- Caso o município não seja identificado, o sistema retornará um aviso
- O sistema é sensível a variações de grafia dos municípios

---

## 📞 Suporte

Para dúvidas ou problemas com o sistema, entre em contato com a equipe de desenvolvimento ou consulte a documentação técnica em `classificador_denuncias.py`.

---

## 📄 Licença

Sistema desenvolvido exclusivamente para uso interno do **Ministério Público do Rio de Janeiro (MPRJ)**.

---

**Última atualização:** Janeiro 2026
