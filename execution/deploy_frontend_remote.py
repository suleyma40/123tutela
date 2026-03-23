from __future__ import annotations

import os
from pathlib import Path

import paramiko
from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")


def _run(ssh: paramiko.SSHClient, command: str, *, timeout: int = 1800) -> None:
    print(f"$ {command}")
    stdin, stdout, stderr = ssh.exec_command(command, timeout=timeout)
    out = stdout.read().decode("utf-8", errors="ignore").strip()
    err = stderr.read().decode("utf-8", errors="ignore").strip()
    status = stdout.channel.recv_exit_status()
    if out:
        print(out.encode("ascii", "ignore").decode("ascii", errors="ignore"))
    if err:
        print(err.encode("ascii", "ignore").decode("ascii", errors="ignore"))
    if status != 0:
        raise RuntimeError(f"Remote command failed with status {status}: {command}")


def deploy_frontend() -> None:
    host = os.getenv("VPS_IP")
    user = os.getenv("VPS_USER", "root")
    password = os.getenv("VPS_PASSWORD")
    remote_dir = os.getenv("REMOTE_REPO_DIR", "/tmp/tutelaapp-build/frontend")
    service_name = os.getenv("FRONTEND_SERVICE_NAME", "tutela-frontend-qn2lo4")

    if not host or not password:
        raise RuntimeError("Faltan VPS_IP o VPS_PASSWORD en .env")

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, username=user, password=password, timeout=30)
    try:
        _run(ssh, "cd /tmp/tutelaapp-build && git fetch origin main && git checkout main && git reset --hard origin/main")
        _run(ssh, f"cd {remote_dir} && docker build -t {service_name}:latest .", timeout=3600)
        _run(ssh, f"docker service update --force {service_name}")
        _run(ssh, "curl -I https://123tutelaapp.com/dashboard", timeout=120)
    finally:
        ssh.close()


if __name__ == "__main__":
    deploy_frontend()
