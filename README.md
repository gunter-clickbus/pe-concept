# pe-concept - Cliente simples para Amazon Q (qbusiness)

Este repositório contém um cliente CLI mínimo em Python (`q.py`) que pergunta a uma aplicação do Amazon Q (serviço "qbusiness") usando a API `chat_sync`. O script foi pensado como prova de conceito para enviar prompts e formatar a resposta com possíveis fontes/trechos citados.

## Principais características
- Envia um prompt para uma aplicação Amazon Q via API `qbusiness.chat_sync`.
- Exibe a mensagem do sistema retornada e as "source attributions" (títulos, snippets e URLs) quando presentes.
- Permite configurar application-id, região AWS, profile, prompt e modo debug via CLI ou variáveis de ambiente.
- Boas práticas básicas: tratamento de exceções, logging e configuração de retries do cliente boto3.

## Requisitos
- Python 3.8+ (recomendado)
- boto3
- botocore

Instale dependências com pip:
```
pip install boto3 botocore
```

(Se preferir usar um virtualenv/venv, crie e ative antes.)

## Arquivo principal
- `q.py` — cliente CLI que encapsula a chamada ao Amazon Q.

## Uso
Forma geral:
```
python q.py [--application-id APPLICATION_ID] [--prompt PROMPT] [--region REGION] [--profile PROFILE] [--debug]
```

Opções:
- `--application-id`, `-a`: ID da aplicação Amazon Q. Também pode ser informado pela variável de ambiente `APPLICATION_ID`. Valor default presente no script.
- `--prompt`, `-p`: Texto a ser enviado como prompt. Também pode ser informado pela variável de ambiente `Q_PROMPT`.
- `--region`, `-r`: Região AWS (ou `AWS_REGION` via env). Default: `us-east-1`.
- `--profile`: Nome do profile do AWS CLI a ser usado (opcional).
- `--debug`: Ativa logging em nível DEBUG.

Exemplo simples:
```
python q.py -a 0e33f74d-01de-4cba-9e97-22768c324f2d -p "Revise o código do repositório X em busca de melhorias."
```

Exemplo usando profile:
```
python q.py -r us-east-1 --profile my-aws-profile
```

## Variáveis de ambiente suportadas
- `APPLICATION_ID` — Id da aplicação Amazon Q (quando não passado via `--application-id`).
- `Q_PROMPT` — Prompt padrão (quando não passado via `--prompt`).
- `AWS_REGION` — Região AWS (quando não passado via `--region`).
- `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN` — Credenciais opcionais; se não estiverem presentes, o boto3 utilizará seu mecanismo padrão (profiles, shared credentials, roles, etc).

## Saídas e formato
O script tenta extrair de forma segura:
- `systemMessage` — texto principal da resposta (impresso como "Resposta do Amazon Q").
- `sourceAttributions` — lista de fontes, onde cada item pode conter `title`, `snippet` e `url`. Estes são formatados em seções legíveis.
- Se a resposta não contiver campos esperados, o script imprime uma mensagem indicando resposta vazia ou inesperada.

## Códigos de saída
O `main()` retorna códigos para facilitar automação:
- `0` — sucesso.
- `2` — falha ao criar sessão AWS (BotoCoreError).
- `3` — falha ao obter identidade via STS (ClientError ou erro inesperado).
- `4` — erro ao interagir com Amazon Q (ClientError ou erro inesperado).

## Segurança e boas práticas
- Evite hardcodar credenciais. Use profiles, roles ou variáveis de ambiente seguras (preferencialmente mecanismos gerenciados).
- Limite o acesso da role/usuário AWS à aplicação Q necessária.
- Não exponha logs sensíveis em ambientes públicos; o modo `--debug` amplia o nível de logs.

## Possíveis melhorias
- Adicionar testes unitários/mocks para chamadas AWS.
- Extrair cliente Amazon Q para um módulo separado e permitir injeção/mocking fácil.
- Adicionar `requirements.txt` e GitHub Actions para linting/testes.
- Tratar paginação / respostas grandes e oferecer saída em JSON opcional.

## Contribuição
Sinta-se à vontade para abrir issues ou pull-requests com melhorias. Se for submeter PR, descreva o propósito, os testes adicionados e como validar localmente.

## Licença
Nenhuma licença foi especificada neste repositório. Adicione um arquivo `LICENSE` conforme necessário.
