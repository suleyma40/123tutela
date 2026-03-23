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
        print(out)
    if err:
        print(err)
    if status != 0:
        raise RuntimeError(f"Remote command failed with status {status}: {command}")


def deploy_backend() -> None:
    host = os.getenv("VPS_IP")
    user = os.getenv("VPS_USER", "root")
    password = os.getenv("VPS_PASSWORD")
    remote_dir = os.getenv("REMOTE_REPO_DIR", "/tmp/tutelaapp-build")
    service_name = os.getenv("BACKEND_SERVICE_NAME", "tutela-backend-rgqxzr")

    if not host or not password:
        raise RuntimeError("Faltan VPS_IP o VPS_PASSWORD en .env")

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, username=user, password=password, timeout=30)
    try:
        _run(ssh, f"cd {remote_dir} && git fetch origin main && git checkout main && git pull --ff-only origin main")
        _run(ssh, f"cd {remote_dir} && docker build -f Dockerfile.backend -t {service_name}:latest .", timeout=3600)
        _run(ssh, f"docker service update --force {service_name}")
        _run(ssh, "curl -fsS https://api.123tutelaapp.com/health", timeout=120)
    finally:
        ssh.close()


if __name__ == "__main__":
    deploy_backend()
