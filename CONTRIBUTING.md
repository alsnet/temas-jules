# Contribuindo para o Essência Espírita

Obrigado pelo interesse em contribuir! Este documento estabelece as diretrizes para contribuir com o projeto.

## Como Relatar Issues

1. Verifique se a issue já não foi reportada
2. Use um título claro e descritivo
3. Descreva o comportamento esperado vs. observado
4. Inclua passos para reproduzir o problema
5. Informe o ambiente (SO, versão do Python, versão do Streamlit)

## Como Propor Melhorias

Antes de implementar, abra uma issue para discutir a proposta. Isso evita trabalho duplicado e garante alinhamento com os objetivos do projeto.

## Padrão de Código

- Siga **PEP 8** para estilo de código
- Use **type hints** em todas as funções e métodos
- Utilize nomes descritivos em português ou inglês (já estabelecido no código)
- Mantenha as funções pequenas e com responsabilidade única
- Documente com docstrings quando a lógica não for óbvia

## Executando Testes

Todos os testes devem passar antes de submeter uma contribuição:

```bash
python -m pytest -v
```

Para verificar cobertura (opcional):

```bash
pip install pytest-cov
python -m pytest --cov=.
```

## Processo de Pull Request

1. Fork o repositório
2. Crie um branch descritivo: `git checkout -b feat/minha-melhoria`
3. Faça suas alterações
4. Execute os testes localmente: `python -m pytest`
5. Commit com mensagem clara (prefixos sugeridos: `feat:`, `fix:`, `refactor:`, `docs:`, `test:`)
6. Push para o branch: `git push origin feat/minha-melhoria`
7. Abra um Pull Request descrevendo as mudanças e referenciando a issue relacionada

## Revisão

Mantenedores do projeto revisarão o PR. Podem ser solicitadas alterações. Discussões construtivas são bem-vindas.
