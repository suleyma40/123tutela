from __future__ import annotations

import os
from pathlib import Path

import paramiko
from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / "execution" / "whatsapp_post_radicado_workflow.json"
load_dotenv(ROOT / ".env")


def connect() -> paramiko.SSHClient:
    host = os.getenv("DEPLOY_SSH_HOST") or os.getenv("VPS_IP")
    user = os.getenv("DEPLOY_SSH_USER") or os.getenv("VPS_USER") or "root"
    password = os.getenv("DEPLOY_SSH_PASSWORD") or os.getenv("VPS_PASSWORD")
    port = int(os.getenv("DEPLOY_SSH_PORT") or os.getenv("VPS_SSH_PORT") or "22")
    if not host:
        raise RuntimeError("No se encontro host SSH.")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, username=user, password=password, port=port, timeout=20)
    return client


def run(client: paramiko.SSHClient, command: str, *, timeout: int = 120) -> str:
    stdin, stdout, stderr = client.exec_command(command, timeout=timeout)
    code = stdout.channel.recv_exit_status()
    out = stdout.read().decode("utf-8", errors="ignore")
    err = stderr.read().decode("utf-8", errors="ignore")
    if code != 0:
        raise RuntimeError(f"Comando remoto fallo ({code}): {command}\n{err or out}")
    return out


def main() -> None:
    if not WORKFLOW.exists():
        raise FileNotFoundError(f"No existe {WORKFLOW}")
    remote_path = "/tmp/whatsapp_post_radicado_workflow.json"
    container_name = "compose-bypass-online-matrix-scwu2e-n8n-1"
    workflow_id = "6a9ad4a0-7b87-44ea-98ea-61e6b0f88b31"

    client = connect()
    try:
        sftp = client.open_sftp()
        try:
            sftp.put(str(WORKFLOW), remote_path)
        finally:
            sftp.close()
        run(client, f"docker cp {remote_path} {container_name}:{remote_path}", timeout=30)
        run(client, f"docker exec {container_name} n8n import:workflow --input={remote_path}", timeout=120)
        run(client, f"docker exec {container_name} n8n update:workflow --id={workflow_id} --active=true", timeout=60)
        run(client, f"docker exec {container_name} n8n publish:workflow --id={workflow_id}", timeout=60)
        run(client, f"docker restart {container_name}", timeout=60)
        webhook_path = run(
            client,
            "docker exec $(docker ps --format '{{.Names}}' | grep 'tutela-n8n-db-eziicq' | head -n 1) "
            f"psql -U postgres -d n8n -At -c \"select \\\"webhookPath\\\" from webhook_entity where \\\"workflowId\\\"='{workflow_id}' limit 1;\"",
            timeout=60,
        ).strip()
        encoded_path = webhook_path.replace("%", "%25")
        print(run(client, f"docker exec {container_name} n8n list:workflow", timeout=60))
        print(f"WEBHOOK_URL=https://n8ntutela.123tutelaapp.com/webhook/{encoded_path}")
    finally:
        client.close()


if __name__ == "__main__":
    main()
