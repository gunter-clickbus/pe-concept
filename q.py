import boto3
import os
import sys


APPLICATION_ID = os.environ.get("APPLICATION_ID", "0e33f74d-01de-4cba-9e97-22768c324f2d")
AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")

prompt = "Revise o código do repositório 'bug-cabuloso' em busca de melhorias de código. Aponte os arquivos e as linhas a serem melhoradas."

if not AWS_ACCESS_KEY_ID or not AWS_SECRET_ACCESS_KEY:
    print("Erro: As variáveis de ambiente AWS_ACCESS_KEY_ID e AWS_SECRET_ACCESS_KEY devem ser definidas.")
    sys.exit(1)

try:
    session = boto3.Session(
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_REGION
    )

    sts_client = session.client('sts')
    identity = sts_client.get_caller_identity()
    print("Executando com a identidade ARN:", identity['Arn'])
except Exception as e:
    print(f"Não foi possível obter a identidade ou inicializar a sessão AWS: {e}")
    sys.exit(1)

try:
    qbusiness_client = session.client(
        service_name='qbusiness',
        region_name=AWS_REGION
    )

    print(f"Enviando pergunta para a aplicação {APPLICATION_ID}...")

    response = qbusiness_client.chat_sync(
        applicationId=APPLICATION_ID,
        userMessage=prompt
    )

    print("\n--- Resposta do Amazon Q ---")
    print(response['systemMessage'])

    if 'sourceAttributions' in response and response['sourceAttributions']:
        print("\n--- Fontes Citadas (Arquivos do Repositório) ---")
        for attr in response['sourceAttributions']:
            print(f"- Título: {attr.get('title')}")
            print(f"  Snippet: \"{attr.get('snippet')}\"")
            print(f"  URL (se disponível): {attr.get('url')}")
            print("-" * 20)

except Exception as e:
    print(f"Ocorreu um erro ao interagir com o Amazon Q: {e}")
    sys.exit(1)
