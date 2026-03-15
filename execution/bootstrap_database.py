from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.db import get_connection


def apply_schema(schema_path: str = "execution/schema_mvp_v3.sql") -> None:
    sql = Path(schema_path).read_text(encoding="utf-8")
    with get_connection() as connection, connection.cursor() as cursor:
        cursor.execute(sql)
    print(f"Schema aplicado desde {schema_path}.")


if __name__ == "__main__":
    apply_schema()
