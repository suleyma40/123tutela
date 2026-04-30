from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app_v2 import _run_whatsapp_abandonment_reminders


def main() -> int:
    parser = argparse.ArgumentParser(description="Ejecuta recordatorios de abandono por WhatsApp.")
    parser.add_argument("--dry-run", action="store_true", help="No envía mensajes; solo simula elegibilidad.")
    args = parser.parse_args()
    result = _run_whatsapp_abandonment_reminders(dry_run=bool(args.dry_run))
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
