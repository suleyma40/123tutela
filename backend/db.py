from __future__ import annotations

from contextlib import contextmanager

import psycopg
from psycopg.rows import dict_row

from backend.config import settings


@contextmanager
def get_connection():
    if not settings.database_url:
        raise RuntimeError("DATABASE_URL no está configurada.")

    connection = psycopg.connect(settings.database_url, row_factory=dict_row)
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
