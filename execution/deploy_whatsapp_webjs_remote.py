from __future__ import annotations

import os
from pathlib import Path

import paramiko
from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parents[1]
SERVICE_DIR = ROOT / "execution" / "whatsapp_webjs_service"
load_dotenv(ROOT / ".env")


def _env(name: str, default: str = "") -> str:
    return str(os.getenv(name) or default).strip()


def connect() -> paramiko.SSHClient:
    host = _env("DEPLOY_SSH_HOST") or _env("VPS_IP")
    user = _env("DEPLOY_SSH_USER") or _env("VPS_USER") or "root"
    password = _env("DEPLOY_SSH_PASSWORD") or _env("VPS_PASSWORD")
    port = int(_env("DEPLOY_SSH_PORT") or _env("VPS_SSH_PORT") or "22")
    if not host:
        raise RuntimeError("No SSH host configured.")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, username=user, password=password, port=port, timeout=30)
    return client


def run(client: paramiko.SSHClient, command: str, *, timeout: int = 240) -> str:
    stdin, stdout, stderr = client.exec_command(command, timeout=timeout)
    code = stdout.channel.recv_exit_status()
    out = stdout.read().decode("utf-8", errors="ignore")
    err = stderr.read().decode("utf-8", errors="ignore")
    if code != 0:
        raise RuntimeError(f"Remote command failed ({code}): {command}\n{err or out}")
    return out


def main() -> None:
    api_key = _env("WHATSAPP_WEBJS_API_KEY") or _env("EVOLUTION_API_KEY")
    if not api_key:
        raise RuntimeError("Set WHATSAPP_WEBJS_API_KEY or EVOLUTION_API_KEY in .env")
    instance = _env("EVOLUTION_INSTANCE", "123tutela")
    remote_root = "/opt/whatsapp-webjs"
    vps_ip = _env("VPS_IP")
    if not vps_ip:
        raise RuntimeError("VPS_IP missing in .env")
    remote_url = f"http://{vps_ip}:3001/send"
    backend_service = "tutela-backend-rgqxzr"

    client = connect()
    try:
        run(client, f"mkdir -p {remote_root}", timeout=30)
        sftp = client.open_sftp()
        try:
            for filename in ("Dockerfile", "package.json", "server.js"):
                sftp.put(str(SERVICE_DIR / filename), f"{remote_root}/{filename}")
        finally:
            sftp.close()

        compose = f"""
services:
  webjs:
    build: .
    container_name: tutela-whatsapp-webjs
    restart: unless-stopped
    ports:
      - "3001:3000"
    environment:
      - WEBJS_API_KEY={api_key}
      - WEBJS_INSTANCE={instance}
    volumes:
      - ./session:/app/.wwebjs_auth
"""
        run(client, f"cat > {remote_root}/docker-compose.yml << 'EOF'\n{compose}\nEOF", timeout=30)
        run(client, f"cd {remote_root} && docker compose up -d --build", timeout=900)
        run(client, "curl -sS http://127.0.0.1:3001/health", timeout=60)
        run(
            client,
            f"docker service update "
            f"--env-rm N8N_WHATSAPP_WEBHOOK_URL --env-add N8N_WHATSAPP_WEBHOOK_URL={remote_url} "
            f"--env-rm N8N_WHATSAPP_WEBHOOK_API_KEY --env-add N8N_WHATSAPP_WEBHOOK_API_KEY={api_key} "
            f"{backend_service}",
            timeout=240,
        )
        print("WhatsApp Web.js deployed")
        print(f"SEND_URL={remote_url}")
        print(f"QR_URL=http://{vps_ip}:3001/qr (header x-api-key)")
    finally:
        client.close()


if __name__ == "__main__":
    main()
