from __future__ import annotations

import argparse
import json
import os
import secrets
import textwrap
import time
import urllib.error
import urllib.request
from pathlib import Path

import paramiko
from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")


def env_first(*keys: str, default: str | None = None) -> str | None:
    for key in keys:
        value = os.getenv(key)
        if value:
            return value
    return default


def connect_ssh() -> paramiko.SSHClient:
    host = env_first("DEPLOY_SSH_HOST", "VPS_IP")
    user = env_first("DEPLOY_SSH_USER", "VPS_USER", default="root")
    password = env_first("DEPLOY_SSH_PASSWORD", "VPS_PASSWORD")
    port = int(env_first("DEPLOY_SSH_PORT", "VPS_SSH_PORT", default="22") or "22")
    if not host:
        raise RuntimeError("No se encontro host SSH en el entorno.")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, port=port, username=user, password=password, timeout=20)
    return client


def run(client: paramiko.SSHClient, command: str, *, timeout: int = 120, check: bool = True) -> tuple[int, str, str]:
    stdin, stdout, stderr = client.exec_command(command, timeout=timeout)
    code = stdout.channel.recv_exit_status()
    out = stdout.read().decode("utf-8", errors="ignore")
    err = stderr.read().decode("utf-8", errors="ignore")
    if check and code != 0:
        raise RuntimeError(f"Comando remoto fallo ({code}): {command}\n{err or out}")
    return code, out, err


def write_remote_file(client: paramiko.SSHClient, remote_path: str, content: str) -> None:
    escaped = content.replace("\\", "\\\\").replace("'", "'\"'\"'")
    run(client, f"mkdir -p {Path(remote_path).parent.as_posix()}", timeout=30)
    run(client, f"printf '%s' '{escaped}' > {remote_path}", timeout=30)


def http_json(method: str, url: str, payload: dict | None = None, headers: dict[str, str] | None = None) -> tuple[int, dict]:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8") if payload is not None else None,
        headers=headers or {},
        method=method,
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:  # nosec - controlled host
            body = response.read().decode("utf-8", errors="ignore")
            return response.status, json.loads(body) if body else {}
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="ignore")
        try:
            parsed = json.loads(body) if body else {}
        except json.JSONDecodeError:
            parsed = {"raw": body}
        return exc.code, parsed


def remote_http_json(
    client: paramiko.SSHClient,
    *,
    method: str,
    url: str,
    payload: dict | None = None,
    headers: dict[str, str] | None = None,
) -> tuple[int, dict]:
    def shell_escape(value: str) -> str:
        return value.replace("'", "'\"'\"'")

    payload_text = json.dumps(payload) if payload is not None else ""
    header_args = " ".join(
        f"-H '{shell_escape(name)}: {shell_escape(value)}'"
        for name, value in (headers or {}).items()
    )
    data_arg = f"-d '{shell_escape(payload_text)}'" if payload is not None else ""
    command = f"curl -sS -X {method.upper()} {header_args} {data_arg} '{url}'".strip()
    _, out, _ = run(client, command, timeout=60, check=False)
    try:
        return 200, json.loads(out) if out.strip() else {}
    except json.JSONDecodeError:
        return 200, {"raw": out}


def wait_for_remote_http(client: paramiko.SSHClient, *, port: str, timeout_s: int = 120) -> None:
    start = time.time()
    while time.time() - start < timeout_s:
        code, out, err = run(
            client,
            f"curl -sS --max-time 10 http://127.0.0.1:{port}/ || true",
            timeout=20,
            check=False,
        )
        if "Welcome to the Evolution API" in out:
            return
        time.sleep(3)
    raise TimeoutError(f"Evolution API no respondio a tiempo en el VPS sobre el puerto {port}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Despliega Evolution API en el VPS y crea una instancia base.")
    parser.add_argument("--instance", default=env_first("EVOLUTION_INSTANCE", default="123tutela"), help="Nombre de la instancia WhatsApp")
    parser.add_argument("--port", default="8080", help="Puerto publico para Evolution API")
    parser.add_argument("--api-key", default=env_first("EVOLUTION_API_KEY"), help="API key de Evolution")
    parser.add_argument("--base-url", default=env_first("EVOLUTION_BASE_URL"), help="Base URL publica de Evolution")
    parser.add_argument("--webhook-url", default=env_first("N8N_WHATSAPP_WEBHOOK_URL", default=""), help="Webhook opcional para eventos de Evolution")
    args = parser.parse_args()

    api_key = args.api_key or secrets.token_urlsafe(32)
    host = env_first("DEPLOY_SSH_HOST", "VPS_IP")
    if not host:
        raise RuntimeError("No se encontro VPS_IP/DEPLOY_SSH_HOST.")
    base_url = (args.base_url or f"http://{host}:{args.port}").rstrip("/")

    remote_dir = "/opt/evolution-api"
    env_text = textwrap.dedent(
        f"""
        SERVER_TYPE=http
        SERVER_PORT=8080
        SERVER_URL={base_url}
        AUTHENTICATION_API_KEY={api_key}
        TZ=America/Bogota
        CORS_ORIGIN=*
        WEBSOCKET_ENABLED=true
        WEBSOCKET_GLOBAL_EVENTS=true
        LOG_LEVEL=ERROR,WARN,INFO,LOG,WEBHOOKS
        LOG_BAILEYS=debug
        CONFIG_SESSION_PHONE_CLIENT=Chrome
        CONFIG_SESSION_PHONE_NAME=Chrome
        DEL_INSTANCE=false
        DATABASE_ENABLED=true
        DATABASE_PROVIDER=postgresql
        DATABASE_CONNECTION_URI=postgresql://postgres:evolution-postgres-pass@evolution-postgres:5432/evolution
        DATABASE_CONNECTION_CLIENT_NAME=evolution_v2
        DATABASE_SAVE_DATA_INSTANCE=true
        DATABASE_SAVE_DATA_NEW_MESSAGE=true
        DATABASE_SAVE_MESSAGE_UPDATE=true
        DATABASE_SAVE_DATA_CONTACTS=true
        DATABASE_SAVE_DATA_CHATS=true
        DATABASE_SAVE_DATA_LABELS=true
        DATABASE_SAVE_DATA_HISTORIC=true
        CACHE_REDIS_ENABLED=true
        CACHE_REDIS_URI=redis://evolution-redis:6379/6
        CACHE_REDIS_PREFIX_KEY=evolution
        CACHE_REDIS_SAVE_INSTANCES=false
        CACHE_LOCAL_ENABLED=false
        """
    ).strip() + "\n"
    compose_text = textwrap.dedent(
        f"""
        services:
          evolution-postgres:
            image: postgres:15-alpine
            container_name: evolution-postgres
            restart: unless-stopped
            environment:
              POSTGRES_DB: evolution
              POSTGRES_USER: postgres
              POSTGRES_PASSWORD: evolution-postgres-pass
            volumes:
              - evolution_postgres_data:/var/lib/postgresql/data
          evolution-redis:
            image: redis:7-alpine
            container_name: evolution-redis
            restart: unless-stopped
          evolution-api:
            image: atendai/evolution-api:v2.1.1
            container_name: evolution-api
            restart: unless-stopped
            ports:
              - "{args.port}:8080"
            env_file:
              - .env
            volumes:
              - evolution_instances:/evolution/instances
            depends_on:
              - evolution-postgres
              - evolution-redis
        volumes:
          evolution_instances:
          evolution_postgres_data:
        """
    ).strip() + "\n"

    client = connect_ssh()
    try:
        run(client, f"mkdir -p {remote_dir}", timeout=30)
        write_remote_file(client, f"{remote_dir}/.env", env_text)
        write_remote_file(client, f"{remote_dir}/docker-compose.yml", compose_text)
        run(client, f"cd {remote_dir} && docker compose up -d", timeout=300)
        wait_for_remote_http(client, port=args.port, timeout_s=180)
        headers = {"Content-Type": "application/json", "apikey": api_key}
        create_payload: dict[str, object] = {
            "instanceName": args.instance,
            "integration": "WHATSAPP-BAILEYS",
            "qrcode": True,
        }
        if args.webhook_url:
            create_payload["webhook"] = {
                "url": args.webhook_url,
                "byEvents": True,
                "base64": False,
                "events": ["MESSAGES_UPSERT", "MESSAGES_UPDATE", "CONNECTION_UPDATE"],
            }
        create_status, create_response = remote_http_json(
            client,
            method="POST",
            url=f"http://127.0.0.1:{args.port}/instance/create",
            payload=create_payload,
            headers=headers,
        )
        connect_status, connect_response = remote_http_json(
            client,
            method="GET",
            url=f"http://127.0.0.1:{args.port}/instance/connect/{args.instance}",
            headers={"apikey": api_key},
        )
        summary = {
            "base_url": base_url,
            "api_key": api_key,
            "instance": args.instance,
            "create_status": create_status,
            "create_response": create_response,
            "connect_status": connect_status,
            "connect_response": connect_response,
        }
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    finally:
        client.close()


if __name__ == "__main__":
    main()
