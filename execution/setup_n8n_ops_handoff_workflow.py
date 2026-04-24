from __future__ import annotations

import os
from pathlib import Path

import paramiko
from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / "execution" / "ops_handoff_workflow.json"
N8N_CONTAINER = "compose-bypass-online-matrix-scwu2e-n8n-1"
DB_CONTAINER = "tutela-n8n-db-eziicq.1.k9kfbwbxw8fov413sckx2xn1t"
BACKEND_SERVICE = "tutela-backend-rgqxzr"
WORKFLOW_ID = "0f1e2d3c-4b5a-6789-8c7d-6e5f4a3b2c10"
PUBLIC_BASE_URL = "https://n8ntutela.123tutelaapp.com/webhook/"
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

    remote_path = "/tmp/ops_handoff_workflow.json"

    client = connect()
    try:
        sftp = client.open_sftp()
        try:
            sftp.put(str(WORKFLOW), remote_path)
        finally:
            sftp.close()

        run(client, f"docker cp {remote_path} {N8N_CONTAINER}:{remote_path}", timeout=30)
        run(client, f"docker exec {N8N_CONTAINER} n8n import:workflow --input={remote_path}", timeout=120)
        run(client, f"docker exec {N8N_CONTAINER} n8n update:workflow --id={WORKFLOW_ID} --active=true", timeout=60)
        run(client, f"docker exec {N8N_CONTAINER} n8n publish:workflow --id={WORKFLOW_ID}", timeout=60)
        run(client, f"docker restart {N8N_CONTAINER}", timeout=60)

        webhook_path = run(
            client,
            "docker exec "
            f"{DB_CONTAINER} "
            "psql -U postgres -d n8n -At -c "
            f"\"select \\\"webhookPath\\\" from webhook_entity where \\\"workflowId\\\"='{WORKFLOW_ID}' limit 1;\"",
            timeout=60,
        ).strip()
        if not webhook_path:
            raise RuntimeError("No se encontro webhookPath para el workflow de ops.")

        webhook_url = PUBLIC_BASE_URL + webhook_path.replace("%", "%25")
        run(
            client,
            f"docker service update --env-rm N8N_OPS_WEBHOOK_URL --env-add N8N_OPS_WEBHOOK_URL={webhook_url} {BACKEND_SERVICE}",
            timeout=120,
        )

        print(run(client, f"docker exec {N8N_CONTAINER} n8n list:workflow", timeout=60))
        print(f"N8N_OPS_WEBHOOK_URL={webhook_url}")
    finally:
        client.close()


if __name__ == "__main__":
    main()
