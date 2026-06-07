# 🕊️ Estudos Doutrinários - Gerador de Textos Simples

Aplicação web que gera textos resumidos com vocabulário simples, baseados exclusivamente na **Doutrina Espírita Kardecista** (obras de Allan Kardec), utilizando IA via OpenRouter.

## Funcionalidades

- Geração de textos doutrinários sobre temas definidos pelo usuário
- Streaming da resposta em tempo real
- Cache de consultas repetidas na mesma sessão
- Configurações ocultas em menu popover (modelo, temperatura, tokens, chave API)
- Seleção de modelo de IA (`openrouter/auto`, `GPT-4o`, `Claude Sonnet`, `Gemini Flash`)
- Controle de temperatura (criatividade) e limite de tokens
- URL da API configurável (útil para proxies ou APIs alternativas)
- Timer de execução e contagem de tokens
- Download do texto gerado em arquivo `.txt`
- Validação e sanitização de entrada
- Interface limpa — configurações ocultas em menu popover

## Tech Stack

- **Python 3.12+**
- **Streamlit** (interface web)
- **OpenAI Python SDK** (comunicação com OpenRouter)
- **python-dotenv** (variáveis de ambiente)
- **pytest** (testes automatizados)

## Pré-requisitos

- Python 3.12 ou superior
- pip
- Uma chave de API do [OpenRouter](https://openrouter.ai/)

## Instalação

```bash
# Clone o repositório
git clone https://github.com/jules-agent/spiritist-app.git
cd spiritist-app

# Crie e ative um ambiente virtual
python -m venv venv

# Windows:
venv\Scripts\activate
# Linux/Mac:
# source venv/bin/activate

# Instale as dependências
pip install -r requirements.txt
```

## Configuração

1. Acesse [openrouter.ai/keys](https://openrouter.ai/keys) e crie uma chave de API
2. Crie um arquivo `.env` na raiz do projeto (não versionado):

```env
OPENROUTER_API_KEY=sk-or-v1-sua-chave-aqui
```

> ⚠️ **Nunca compartilhe sua chave de API.** O arquivo `.env` está no `.gitignore` e não será commitado.

## Execução

```bash
python -m streamlit run app.py
```

O aplicativo abrirá em `http://localhost:8501`. Clique no botão **⚙️ Configurações** para inserir sua chave da OpenRouter e ajustar parâmetros.

## Uso

1. Digite um tema espiritual (ex: "Reencarnação", "Lei de Causa e Efeito", "Prece")
2. Ajuste modelo, temperatura e tokens no menu **⚙️ Configurações** (opcional)
3. Clique em **Gerar Texto**
4. O texto aparecerá em tempo real com streaming
5. Faça o download em `.txt` se desejar
6. Consultas repetidas ao mesmo tema usam cache instantâneo

## Estrutura do Projeto

```
├── app.py                 # Aplicação principal
├── requirements.txt       # Dependências
├── pytest.ini             # Configuração dos testes
├── .env                   # Chave de API (não versionado)
├── .gitignore             # Arquivos ignorados pelo Git
├── .python-version        # Versão do Python
├── README.md              # Este arquivo
├── LICENSE                # Licença MIT
├── CONTRIBUTING.md        # Guia de contribuição
├── sprints/               # Plano de melhorias (sprints)
│   ├── .log
│   ├── sprint-01-*.log
│   └── ...
└── tests/                 # Testes automatizados
    ├── __init__.py
    ├── conftest.py
    └── test_app.py
```

## Tecnologias Utilizadas

- [Streamlit](https://streamlit.io/) — Framework web Python para apps de dados
- [OpenRouter](https://openrouter.ai/) — Roteador unificado de APIs de IA
- [OpenAI Python SDK](https://github.com/openai/openai-python) — Cliente oficial da API OpenAI
- [python-dotenv](https://github.com/theskumar/python-dotenv) — Gerenciamento de variáveis de ambiente
- [pytest](https://docs.pytest.org/) — Framework de testes

## Licença

Distribuído sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.
