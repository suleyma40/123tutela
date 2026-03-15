from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

import paramiko
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")


def safe_print(message: str = "", *, stream = sys.stdout, end: str = "\n", flush: bool = False) -> None:
    text = str(message)
    encoding = getattr(stream, "encoding", None) or "utf-8"
    sanitized = text.encode(encoding, errors="replace").decode(encoding, errors="replace")
    print(sanitized, file=stream, end=end, flush=flush)


def env_first(*keys: str, default: str | None = None) -> str | None:
    for key in keys:
        value = os.getenv(key)
        if value:
            return value
    return default


def connect_ssh() -> tuple[paramiko.SSHClient, str]:
    host = env_first("DEPLOY_SSH_HOST", "VPS_IP")
    user = env_first("DEPLOY_SSH_USER", "VPS_USER", default="root")
    password = env_first("DEPLOY_SSH_PASSWORD", "VPS_PASSWORD")
    key_path = env_first("DEPLOY_SSH_PRIVATE_KEY_PATH", "VPS_SSH_KEY_PATH")
    port = int(env_first("DEPLOY_SSH_PORT", default="22") or "22")

    if not host:
        raise RuntimeError("No se encontró DEPLOY_SSH_HOST ni VPS_IP en el entorno.")

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    connect_kwargs = {
        "hostname": host,
        "port": port,
        "username": user,
        "timeout": 20,
        "allow_agent": False,
        "look_for_keys": False,
    }
    if key_path:
        connect_kwargs["key_filename"] = key_path
    if password:
        connect_kwargs["password"] = password

    client.connect(**connect_kwargs)
    return client, host


def run_command(
    client: paramiko.SSHClient,
    command: str,
    *,
    timeout: int = 120,
    check: bool = True,
    get_pty: bool = False,
) -> tuple[int, str, str]:
    safe_print(f"$ {command}")
    stdin, stdout, stderr = client.exec_command(command, timeout=timeout, get_pty=get_pty)
    exit_code = stdout.channel.recv_exit_status()
    output = stdout.read().decode("utf-8", errors="ignore")
    error = stderr.read().decode("utf-8", errors="ignore")

    if output.strip():
        safe_print(output.rstrip())
    if error.strip():
        safe_print(error.rstrip(), stream=sys.stderr)

    if check and exit_code != 0:
        raise RuntimeError(f"El comando falló con código {exit_code}: {command}")
    return exit_code, output, error


def stream_command(client: paramiko.SSHClient, command: str, *, timeout: int = 900) -> None:
    safe_print(f"$ {command}")
    stdin, stdout, stderr = client.exec_command(command, get_pty=True)
    start = time.time()

    while True:
        if stdout.channel.recv_ready():
            chunk = stdout.channel.recv(4096).decode("utf-8", errors="ignore")
            if chunk:
                safe_print(chunk, end="", flush=True)
        if stderr.channel.recv_stderr_ready():
            chunk = stderr.channel.recv_stderr(4096).decode("utf-8", errors="ignore")
            if chunk:
                safe_print(chunk, stream=sys.stderr, end="", flush=True)
        if stdout.channel.exit_status_ready():
            break
        if time.time() - start > timeout:
            raise TimeoutError(f"Timeout esperando la finalización de: {command}")
        time.sleep(1)

    exit_code = stdout.channel.recv_exit_status()
    if exit_code != 0:
        raise RuntimeError(f"El comando falló con código {exit_code}: {command}")


def inspect_vps(client: paramiko.SSHClient) -> None:
    commands = [
        "hostnamectl || hostname",
        "uname -a",
        "free -h",
        "df -h",
        "docker --version || true",
        "docker ps -a --format 'table {{.Names}}\\t{{.Status}}\\t{{.Ports}}' || true",
        "docker volume ls || true",
        "docker network ls || true",
        "ss -lntp | grep -E ':(80|443|3000|5432|5678|8000)\\b' || true",
    ]
    for command in commands:
        run_command(client, command, check=False)


def wipe_for_dokploy(client: paramiko.SSHClient) -> None:
    commands = [
        "for service in coolify coolify-proxy dokploy traefik nginx apache2 caddy; do systemctl stop \"$service\" 2>/dev/null || true; done",
        "ids=$(docker ps -aq); if [ -n \"$ids\" ]; then docker rm -f $ids; fi",
        "vols=$(docker volume ls -q); if [ -n \"$vols\" ]; then docker volume rm $vols; fi",
        "docker system prune -af --volumes || true",
        "docker swarm leave --force || true",
        "rm -rf /data/coolify /var/lib/coolify /etc/dokploy /var/lib/dokploy",
    ]
    for command in commands:
        run_command(client, command, timeout=300, check=False)


def ensure_swarm_compatible_docker(client: paramiko.SSHClient) -> None:
    _, daemon_raw, _ = run_command(client, "cat /etc/docker/daemon.json 2>/dev/null || echo {}", check=False)
    daemon_text = daemon_raw.strip() or "{}"

    try:
        daemon_config = json.loads(daemon_text)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"No fue posible parsear /etc/docker/daemon.json: {exc}") from exc

    changed = False
    if daemon_config.pop("live-restore", None) is not None:
        changed = True

    if changed:
        payload = json.dumps(daemon_config, indent=2, ensure_ascii=True)
        escaped = payload.replace("\\", "\\\\").replace("'", "'\"'\"'")
        run_command(client, f"printf '%s\n' '{escaped}' > /etc/docker/daemon.json", timeout=60)
        run_command(client, "systemctl restart docker", timeout=120)
        run_command(client, "docker info --format '{{json .Swarm}}'", timeout=60, check=False)


def install_dokploy(client: paramiko.SSHClient) -> None:
    ensure_swarm_compatible_docker(client)
    install_cmd = "curl -sSL https://dokploy.com/install.sh | sh"
    stream_command(client, install_cmd)
    inspect_commands = [
        "docker service ls || true",
        "docker ps --format 'table {{.Names}}\\t{{.Status}}\\t{{.Ports}}' || true",
        "curl -I http://127.0.0.1:3000 || true",
    ]
    for command in inspect_commands:
        run_command(client, command, check=False)


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspección, limpieza e instalación remota de Dokploy.")
    parser.add_argument(
        "action",
        choices=["inspect", "wipe", "install", "all"],
        help="inspect: solo diagnóstico, wipe: limpieza, install: instala Dokploy, all: inspección + limpieza + instalación",
    )
    parser.add_argument(
        "--confirm-wipe",
        action="store_true",
        help="Requerido para ejecutar la limpieza destructiva del VPS.",
    )
    args = parser.parse_args()

    client, host = connect_ssh()
    safe_print(f"Conectado a {host}")

    try:
        if args.action in {"inspect", "all"}:
            inspect_vps(client)

        if args.action in {"wipe", "all"}:
            if not args.confirm_wipe:
                raise RuntimeError("La limpieza requiere --confirm-wipe para evitar borrados accidentales.")
            wipe_for_dokploy(client)

        if args.action in {"install", "all"}:
            install_dokploy(client)
    finally:
        client.close()


if __name__ == "__main__":
    main()
