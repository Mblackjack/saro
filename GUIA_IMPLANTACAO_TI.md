# 🛠️ Guia de Implantação Técnica - Sistema de Denúncias MPRJ

Este documento contém as instruções para a equipe de TI do MPRJ realizar o deploy permanente da aplicação.

## 📋 Pré-requisitos
- Servidor Linux (Ubuntu recomendado) ou Windows Server.
- Python 3.11 ou superior instalado.
- Acesso à internet (para chamadas à API da OpenAI).
- Uma chave de API da OpenAI configurada como variável de ambiente.

---

## 🚀 Passo a Passo para Implantação

### 1. Preparar o Ambiente
Extraia o conteúdo do arquivo `sistema_denuncias_mprj.zip` no diretório de destino.

```bash
# Criar ambiente virtual (recomendado)
python3 -m venv venv
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt
```

### 2. Configurar Variáveis de Ambiente
O sistema utiliza a API da OpenAI para a classificação inteligente. É necessário configurar a chave:

```bash
export OPENAI_API_KEY='sua_chave_aqui'
```

### 3. Executar a Aplicação
Para rodar em modo de produção, recomenda-se usar o Streamlit com um gerenciador de processos como o `pm2` ou criar um serviço no `systemd`.

**Comando básico:**
```bash
streamlit run app_web.py --server.port 80 --server.address 0.0.0.0
```

---

## 🐳 Opção com Docker (Recomendado para Produção)

Se preferirem usar Docker, aqui está um exemplo de `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8501

ENV OPENAI_API_KEY="sua_chave_aqui"

ENTRYPOINT ["streamlit", "run", "app_web.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

---

## 📂 Estrutura do Projeto
- `app_web.py`: Interface Streamlit.
- `classificador_denuncias.py`: Lógica de negócio e integração com IA.
- `base_promotorias.json`: Mapeamento de municípios e promotorias.
- `base_temas_subtemas.json`: Árvore de classificação de temas.

---

## 📞 Suporte Técnico
O código foi estruturado de forma modular. A lógica de classificação está separada da interface, permitindo que a TI integre a inteligência em outros sistemas (como o MGP) via API se desejar no futuro.
