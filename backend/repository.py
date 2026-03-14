from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from backend.db import get_connection


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


def create_user(name: str, email: str, password_hash: str) -> dict[str, Any]:
    query = """
        INSERT INTO app_users (name, email, password_hash)
        VALUES (%(name)s, %(email)s, %(password_hash)s)
        RETURNING id, name, email, created_at;
    """
    with get_connection() as connection, connection.cursor() as cursor:
        cursor.execute(query, {"name": name, "email": email.lower(), "password_hash": password_hash})
        return cursor.fetchone()


def get_user_by_email(email: str) -> dict[str, Any] | None:
    query = """
        SELECT id, name, email, password_hash, created_at
        FROM app_users
        WHERE email = %(email)s;
    """
    with get_connection() as connection, connection.cursor() as cursor:
        cursor.execute(query, {"email": email.lower()})
        return cursor.fetchone()


def get_user_by_id(user_id: str) -> dict[str, Any] | None:
    query = """
        SELECT id, name, email, created_at
        FROM app_users
        WHERE id = %(user_id)s;
    """
    with get_connection() as connection, connection.cursor() as cursor:
        cursor.execute(query, {"user_id": user_id})
        return cursor.fetchone()


def create_case_record(
    *,
    user_id: str,
    user_name: str,
    user_email: str,
    city: str,
    department: str,
    category: str,
    description: str,
    attachments: list[str],
    recommended_action: str,
    strategy_text: str,
    facts: dict[str, Any],
    legal_analysis: dict[str, Any],
    routing: dict[str, Any],
) -> dict[str, Any]:
    query = """
        INSERT INTO casos (
            user_id,
            usuario_nombre,
            usuario_email,
            usuario_ciudad,
            usuario_departamento,
            categoria,
            descripcion,
            attachments,
            recommended_action,
            strategy_text,
            facts,
            legal_analysis,
            routing,
            estado
        )
        VALUES (
            %(user_id)s,
            %(user_name)s,
            %(user_email)s,
            %(city)s,
            %(department)s,
            %(category)s,
            %(description)s,
            %(attachments)s::jsonb,
            %(recommended_action)s,
            %(strategy_text)s,
            %(facts)s::jsonb,
            %(legal_analysis)s::jsonb,
            %(routing)s::jsonb,
            'analizado'
        )
        RETURNING *;
    """
    params = {
        "user_id": user_id,
        "user_name": user_name,
        "user_email": user_email.lower(),
        "city": city,
        "department": department,
        "category": category,
        "description": description,
        "attachments": _json(attachments),
        "recommended_action": recommended_action,
        "strategy_text": strategy_text,
        "facts": _json(facts),
        "legal_analysis": _json(legal_analysis),
        "routing": _json(routing),
    }
    with get_connection() as connection, connection.cursor() as cursor:
        cursor.execute(query, params)
        return cursor.fetchone()


def list_cases_for_user(user_id: str) -> list[dict[str, Any]]:
    query = """
        SELECT *
        FROM casos
        WHERE user_id = %(user_id)s
        ORDER BY created_at DESC;
    """
    with get_connection() as connection, connection.cursor() as cursor:
        cursor.execute(query, {"user_id": user_id})
        return cursor.fetchall()


def get_case_for_user(case_id: str, user_id: str) -> dict[str, Any] | None:
    query = """
        SELECT *
        FROM casos
        WHERE id = %(case_id)s AND user_id = %(user_id)s;
    """
    with get_connection() as connection, connection.cursor() as cursor:
        cursor.execute(query, {"case_id": case_id, "user_id": user_id})
        return cursor.fetchone()


def update_case_document(case_id: str, document: str, status: str = "documento_generado") -> dict[str, Any] | None:
    query = """
        UPDATE casos
        SET generated_document = %(document)s,
            estado = %(status)s,
            updated_at = %(updated_at)s
        WHERE id = %(case_id)s
        RETURNING *;
    """
    with get_connection() as connection, connection.cursor() as cursor:
        cursor.execute(
            query,
            {
                "case_id": case_id,
                "document": document,
                "status": status,
                "updated_at": datetime.now(timezone.utc),
            },
        )
        return cursor.fetchone()


def search_best_court(city: str, department: str) -> dict[str, Any] | None:
    query = """
        SELECT *
        FROM juzgados
        WHERE UPPER(municipio) = UPPER(%(city)s)
           OR UPPER(departamento) = UPPER(%(department)s)
           OR UPPER(codigo_interno) = 'NAC-001'
        ORDER BY
            CASE
                WHEN UPPER(municipio) = UPPER(%(city)s) THEN 0
                WHEN UPPER(departamento) = UPPER(%(department)s) THEN 1
                WHEN UPPER(codigo_interno) = 'NAC-001' THEN 2
                ELSE 3
            END,
            created_at ASC
        LIMIT 1;
    """
    with get_connection() as connection, connection.cursor() as cursor:
        cursor.execute(query, {"city": city, "department": department})
        return cursor.fetchone()


def search_entities(category: str, entity_names: list[str]) -> list[dict[str, Any]]:
    patterns = [f"%{category.lower()}%"] + [f"%{name.lower()}%" for name in entity_names if name]
    query = """
        SELECT *
        FROM entidades
        WHERE LOWER(modulo) LIKE LOWER(%(category)s)
           OR LOWER(nombre_entidad) LIKE ANY(%(patterns)s)
        ORDER BY prioridad ASC NULLS LAST, created_at ASC
        LIMIT 3;
    """
    with get_connection() as connection, connection.cursor() as cursor:
        cursor.execute(query, {"category": f"%{category}%", "patterns": patterns})
        return cursor.fetchall()


def upsert_knowledge_item(source_key: str, title: str, content: dict[str, Any], source: str, tags: list[str]) -> None:
    query = """
        INSERT INTO conocimiento_legal (source_key, titulo, contenido, fuente, tags)
        VALUES (%(source_key)s, %(title)s, %(content)s, %(source)s, %(tags)s)
        ON CONFLICT (source_key)
        DO UPDATE SET
            titulo = EXCLUDED.titulo,
            contenido = EXCLUDED.contenido,
            fuente = EXCLUDED.fuente,
            tags = EXCLUDED.tags;
    """
    with get_connection() as connection, connection.cursor() as cursor:
        cursor.execute(
            query,
            {
                "source_key": source_key,
                "title": title,
                "content": _json(content),
                "source": source,
                "tags": tags,
            },
        )


def upsert_business_rule(rule_key: str, title: str, description: str, action_text: str | None, priority: str | None) -> None:
    query = """
        INSERT INTO business_rules (rule_key, title, description, action_text, priority)
        VALUES (%(rule_key)s, %(title)s, %(description)s, %(action_text)s, %(priority)s)
        ON CONFLICT (rule_key)
        DO UPDATE SET
            title = EXCLUDED.title,
            description = EXCLUDED.description,
            action_text = EXCLUDED.action_text,
            priority = EXCLUDED.priority;
    """
    with get_connection() as connection, connection.cursor() as cursor:
        cursor.execute(
            query,
            {
                "rule_key": rule_key,
                "title": title,
                "description": description,
                "action_text": action_text,
                "priority": priority,
            },
        )


def upsert_entity(record: dict[str, Any]) -> None:
    query = """
        INSERT INTO entidades (
            modulo,
            paso_flujo,
            nombre_entidad,
            canal_envio,
            contacto_envio,
            genera_radicado,
            plazo_respuesta,
            observaciones,
            automatizable,
            prioridad
        )
        VALUES (
            %(modulo)s,
            %(paso_flujo)s,
            %(nombre_entidad)s,
            %(canal_envio)s,
            %(contacto_envio)s,
            %(genera_radicado)s,
            %(plazo_respuesta)s,
            %(observaciones)s,
            %(automatizable)s,
            %(prioridad)s
        )
        ON CONFLICT (nombre_entidad, canal_envio, contacto_envio)
        DO UPDATE SET
            modulo = EXCLUDED.modulo,
            paso_flujo = EXCLUDED.paso_flujo,
            genera_radicado = EXCLUDED.genera_radicado,
            plazo_respuesta = EXCLUDED.plazo_respuesta,
            observaciones = EXCLUDED.observaciones,
            automatizable = EXCLUDED.automatizable,
            prioridad = EXCLUDED.prioridad;
    """
    with get_connection() as connection, connection.cursor() as cursor:
        cursor.execute(query, record)


def upsert_court(record: dict[str, Any]) -> None:
    query = """
        INSERT INTO juzgados (
            departamento,
            municipio,
            tipo_oficina,
            correo_reparto,
            correo_alternativo,
            tipo_tutela,
            asunto_recomendado,
            plataforma_oficial,
            url_referencia,
            codigo_interno,
            prioridad,
            notas
        )
        VALUES (
            %(departamento)s,
            %(municipio)s,
            %(tipo_oficina)s,
            %(correo_reparto)s,
            %(correo_alternativo)s,
            %(tipo_tutela)s,
            %(asunto_recomendado)s,
            %(plataforma_oficial)s,
            %(url_referencia)s,
            %(codigo_interno)s,
            %(prioridad)s,
            %(notas)s
        )
        ON CONFLICT (codigo_interno)
        DO UPDATE SET
            departamento = EXCLUDED.departamento,
            municipio = EXCLUDED.municipio,
            tipo_oficina = EXCLUDED.tipo_oficina,
            correo_reparto = EXCLUDED.correo_reparto,
            correo_alternativo = EXCLUDED.correo_alternativo,
            tipo_tutela = EXCLUDED.tipo_tutela,
            asunto_recomendado = EXCLUDED.asunto_recomendado,
            plataforma_oficial = EXCLUDED.plataforma_oficial,
            url_referencia = EXCLUDED.url_referencia,
            prioridad = EXCLUDED.prioridad,
            notas = EXCLUDED.notas;
    """
    with get_connection() as connection, connection.cursor() as cursor:
        cursor.execute(query, record)
