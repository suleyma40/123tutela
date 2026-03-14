from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

import paramiko
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

load_dotenv()


def sql_literal(value: Any) -> str:
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return str(value)
    text = str(value).strip()
    if not text:
        return "NULL"
    return "'" + text.replace("'", "''") + "'"


def build_seed_sql() -> str:
    statements = [Path("execution/schema_mvp.sql").read_text(encoding="utf-8").strip()]

    rules = json.loads(Path("execution/business_rules.json").read_text(encoding="utf-8"))
    for index, rule in enumerate(rules, start=1):
        statements.append(
            f"""
            INSERT INTO business_rules (rule_key, title, description, action_text, priority)
            VALUES (
                {sql_literal(f'business-rule-{index}')},
                {sql_literal(rule.get('Regla', f'Regla {index}'))},
                {sql_literal(rule.get('Descripción', ''))},
                {sql_literal(rule.get('Acción'))},
                {sql_literal(rule.get('Prioridad'))}
            )
            ON CONFLICT (rule_key)
            DO UPDATE SET title = EXCLUDED.title, description = EXCLUDED.description, action_text = EXCLUDED.action_text, priority = EXCLUDED.priority;
            """.strip()
        )

    return "BEGIN;\n" + "\n".join(statements) + "\nCOMMIT;\n"


def bootstrap_remote() -> None:
    host = os.getenv("VPS_IP")
    user = os.getenv("VPS_USER", "root")
    password = os.getenv("VPS_PASSWORD")
    container = os.getenv("DB_CONTAINER_NAME", "bw7aj85ekz1p65w04lptq93j")

    if not host or not password:
        raise RuntimeError("Faltan VPS_IP o VPS_PASSWORD en el entorno.")

    local_sql_path = ROOT / ".tmp" / "bootstrap_123tutela.sql"
    local_sql_path.parent.mkdir(parents=True, exist_ok=True)
    local_sql_path.write_text(build_seed_sql(), encoding="utf-8")

    remote_sql_path = f"/root/{local_sql_path.name}"

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, username=user, password=password, timeout=20)

    try:
        sftp = ssh.open_sftp()
        sftp.put(str(local_sql_path), remote_sql_path)
        sftp.close()

        command = f"docker exec -i {container} psql -U postgres -d postgres < {remote_sql_path}"
        stdin, stdout, stderr = ssh.exec_command(command, timeout=300)
        output = stdout.read().decode("utf-8", errors="ignore")
        error = stderr.read().decode("utf-8", errors="ignore")
        if output.strip():
            print(output.strip())
        if error.strip():
            print(error.strip())
    finally:
        ssh.close()


if __name__ == "__main__":
    bootstrap_remote()
