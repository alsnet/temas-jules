# Especificações do Projeto "Temas Espíritas"

## Visão Geral

O projeto "Temas Espíritas" é uma aplicação web que gera textos resumidos sobre temas espirituais baseados exclusivamente na Doutrina Kardecista, utilizando tecnologia de IA através do serviço OpenRouter.

## Funcionalidades Principais

### 1. Geração de Textos
- Criação de textos resumidos com vocabulário simples e acessível
- Baseado unicamente nas obras de Allan Kardec
- Utilização de inteligência artificial via OpenRouter
- Respostas em tempo real por streaming

### 2. Interface de Usuário
- Campo de entrada para temas espirituais
- Botão de geração com controle de estado
- Visualização em tempo real do texto sendo gerado
- Download em formato TXT do conteúdo gerado

### 3. Configurações Avançadas
- Seleção de modelo de IA (openrouter/auto, GPT-4o, Claude Sonnet, Gemini Flash)
- Controle de temperatura (criatividade)
- Limites de tokens
- Configuração de API key do OpenRouter
- Roteamento de provedores OpenRouter
- URL da API configurável

### 4. Cache e Performance
- Cache de consultas repetidas na mesma sessão
- Indicador de tempo de execução
- Contagem de tokens utilizados
- Interface intuitiva e responsiva

## Requisitos Técnicos

### Dependências
```
streamlit>=1.28,<2
openai>=1.0,<2
python-dotenv>=1.0,<2
pytest>=7,<9
pytest-mock>=3,<4
```

### Ambiente
- Python 3.12+
- Ambiente virtual recomendado
- Chave de API do OpenRouter

## Arquitetura

### Estrutura do Projeto
```
├── app.py                 # Aplicação principal
├── requirements.txt       # Dependências
├── pytest.ini             # Configuração dos testes
├── .env                   # Chave de API (não versionado)
├── .gitignore             # Arquivos ignorados pelo Git
├── .python-version        # Versão do Python
├── README.md              # Documentação principal
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

### Componentes Principais
1. **Interface Streamlit**: Componente principal de UI
2. **API OpenRouter**: Conexão com serviços de IA
3. **Gerenciamento de Estado**: Cache e session_state para sessão
4. **Validação e Sanitização**: Input validation e sanitization
5. **Configuração**: Gerenciamento de parâmetros de configuração

## Padrões de Desenvolvimento

### Código
- Seguindo PEP 8
- Utilização de type hints
- Nomes descritivos em português ou inglês
- Funções pequenas e com responsabilidade única

### Segurança
- Gerenciamento seguro de API Keys com python-dotenv
- Validação adequada de entrada
- Não exposição de credenciais no código-fonte

## Testes

### Cobertura de Testes
- Unit tests para funções auxiliares (sanitize_filename, validate_theme)
- Mocking de chamadas da API
- Testes de erros específicos da OpenRouter
- Testes de comportamento com cache

### Framework de Testes
- pytest para execução de testes unitários
- pytest-mock para mocking de dependências
- Cobertura de pelo menos 80% dos casos limite

## Performance

### Recursos Principais
- Streaming em tempo real da resposta
- Cache por sessão para consultas repetidas
- Controle fino de tokens e temperatura
- Interface responsiva com indicadores de progresso

### Limitações Conhecidas
- Dependência única do serviço OpenRouter
- Nenhuma persistência de cache entre sessões

## Considerações de Manutenção

### Atualizações Futuras
1. Implementação de novo sistema de cache persistente
2. Expansão das funcionalidades de configuração
3. Adição de mais testes end-to-end
4. Melhorias na interface do usuário

### Documentação
- README detalhado com instalação e uso
- CONTRIBUTING.md com diretrizes de contribuição
- Registro de melhorias em sprints