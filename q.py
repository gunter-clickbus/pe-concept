#!/usr/bin/env python3

from __future__ import annotations

import argparse
import logging
import os
import sys
from typing import Any, Dict, Optional

import boto3
import botocore
from botocore.config import Config

# Defaults
DEFAULT_APPLICATION_ID = "0e33f74d-01de-4cba-9e97-22768c324f2d"
DEFAULT_REGION = "us-east-1"
DEFAULT_PROMPT = (
    "Revise o código do repositório 'bug-cabuloso' em busca de melhorias de código. "
    "Aponte os arquivos e as linhas a serem melhoradas."
)


def configure_logging(debug: bool = False) -> None:
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Query Amazon Q (qbusiness) with a prompt.")
    parser.add_argument("--application-id", "-a", default=os.environ.get("APPLICATION_ID", DEFAULT_APPLICATION_ID),
                        help="Amazon Q application ID (or set APPLICATION_ID env var).")
    parser.add_argument("--prompt", "-p", default=os.environ.get("Q_PROMPT", DEFAULT_PROMPT),
                        help="Prompt to send to Amazon Q.")
    parser.add_argument("--region", "-r", default=os.environ.get("AWS_REGION", DEFAULT_REGION),
                        help="AWS region (or set AWS_REGION env var).")
    parser.add_argument("--profile", help="AWS named profile to use (optional).")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging.")
    return parser.parse_args()


def create_session(region: str, profile: Optional[str] = None) -> boto3.Session:
    """
    Create a boto3 Session. If AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY are present
    in the environment they will be used automatically by boto3; otherwise boto3's
    standard credential resolution (profiles, IAM role, etc.) is used.
    """
    session_kwargs: Dict[str, Any] = {}
    if profile:
        session_kwargs["profile_name"] = profile

    # Let boto3 handle credential resolution; only set region here so clients pick it up by default.
    session = boto3.Session(region_name=region, **session_kwargs)
    return session


def get_caller_identity(session: boto3.Session) -> Dict[str, Any]:
    sts = session.client("sts")
    return sts.get_caller_identity()


def ask_amazon_q(session: boto3.Session, application_id: str, user_message: str, region: str) -> Dict[str, Any]:
    """
    Call the qbusiness chat_sync API. Returns the raw response dictionary.
    """
    # Configure retries and timeouts if desired
    config = Config(retries={"max_attempts": 3, "mode": "standard"})
    client = session.client("qbusiness", region_name=region, config=config)
    # The API expects applicationId and userMessage based on original code
    return client.chat_sync(applicationId=application_id, userMessage=user_message)


def format_response(resp: Dict[str, Any]) -> str:
    """
    Safely extract useful fields from the response and format a human-readable string.
    """
    parts = []
    system_message = resp.get("systemMessage")
    if system_message:
        parts.append("--- Resposta do Amazon Q ---")
        parts.append(system_message)

    source_attrs = resp.get("sourceAttributions") or []
    if source_attrs:
        parts.append("\n--- Fontes Citadas (Arquivos do Repositório) ---")
        for attr in source_attrs:
            title = attr.get("title", "<sem título>")
            snippet = attr.get("snippet", "")
            url = attr.get("url", "")
            parts.append(f"- Título: {title}")
            if snippet:
                parts.append(f'  Snippet: "{snippet}"')
            if url:
                parts.append(f"  URL: {url}")
            parts.append("-" * 20)
    if not parts:
        parts.append("Resposta vazia ou em formato inesperado.")
    return "\n".join(parts)


def main() -> int:
    args = parse_args()
    configure_logging(debug=args.debug)
    logger = logging.getLogger("qclient")

    logger.debug("Starting with args: %s", args)

    # Inform about credential environment but do not fail immediately: allow boto3 to resolve creds
    env_access_key = os.environ.get("AWS_ACCESS_KEY_ID")
    env_secret_key = os.environ.get("AWS_SECRET_ACCESS_KEY")
    if not (env_access_key and env_secret_key):
        logger.warning(
            "AWS_ACCESS_KEY_ID and/or AWS_SECRET_ACCESS_KEY not found in environment. "
            "boto3 will use its default credential resolution chain (profiles, shared credentials, instance role, etc.)."
        )

    try:
        session = create_session(region=args.region, profile=args.profile)
    except botocore.exceptions.BotoCoreError as e:
        logger.exception("Failed to create AWS session: %s", e)
        return 2

    try:
        identity = get_caller_identity(session)
        arn = identity.get("Arn", "<unknown>")
        account = identity.get("Account", "<unknown>")
        logger.info("Executando com a identidade ARN: %s (Account: %s)", arn, account)
    except botocore.exceptions.ClientError as e:
        logger.exception("Não foi possível obter a identidade (STS): %s", e)
        return 3
    except Exception as e:
        logger.exception("Erro inesperado ao chamar STS: %s", e)
        return 3

    try:
        logger.info("Enviando pergunta para a aplicação %s...", args.application_id)
        response = ask_amazon_q(session, args.application_id, args.prompt, args.region)
        output = format_response(response)
        print(output)
    except botocore.exceptions.ClientError as e:
        logger.exception("Erro ao interagir com o Amazon Q (client error): %s", e)
        return 4
    except Exception as e:
        logger.exception("Erro inesperado ao interagir com o Amazon Q: %s", e)
        return 4

    return 0


if __name__ == "__main__":
    sys.exit(main())
