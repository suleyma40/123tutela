from __future__ import annotations

import os
from pathlib import Path

import paramiko
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")


def main() -> None:
    host = os.getenv("VPS_IP")
    user = os.getenv("VPS_USER", "root")
    password = os.getenv("VPS_PASSWORD")
    if not host or not password:
        raise RuntimeError("Faltan VPS_IP o VPS_PASSWORD en .env")

    backend_service = "tutela-backend-rgqxzr"
    frontend_service = os.getenv("FRONTEND_SERVICE_NAME", "tutela-frontend-qn2lo4")
    cmd = (
        "set -e; "
        "echo '=== service ps backend ==='; "
        f"docker service ps {backend_service} --no-trunc --format 'table {{.Name}}\\t{{.CurrentState}}\\t{{.Error}}'; "
        "echo '=== service ps frontend ==='; "
        f"docker service ps {frontend_service} --no-trunc --format 'table {{.Name}}\\t{{.CurrentState}}\\t{{.Error}}'; "
        "echo '=== backend logs (last 300) ==='; "
        f"docker service logs --raw --tail 300 {backend_service} 2>&1; "
        "echo '=== frontend logs (last 120) ==='; "
        f"docker service logs --raw --tail 120 {frontend_service} 2>&1; "
    )

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, username=user, password=password, timeout=30)
    try:
        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=240)
        out = stdout.read().decode("utf-8", errors="ignore")
        err = stderr.read().decode("utf-8", errors="ignore")
        if out.strip():
            print(out)
        if err.strip():
            print(err)
    finally:
        ssh.close()


if __name__ == "__main__":
    main()

