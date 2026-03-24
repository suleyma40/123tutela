from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from backend.db import get_connection


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


def create_user(name: str, email: str, password_hash: str, *, role: str = "citizen") -> dict[str, Any]:
    query = """
        INSERT INTO app_users (name, email, password_hash, role)
        VALUES (%(name)s, %(email)s, %(password_hash)s, %(role)s)
        RETURNING id, name, email, document_number, phone, city, department, address, role, created_at, updated_at;
    """
    with get_connection() as connection, connection.cursor() as cursor:
        cursor.execute(
            query,
            {"name": name, "email": email.lower(), "password_hash": password_hash, "role": role},
        )
        return cursor.fetchone()


def get_user_by_email(email: str) -> dict[str, Any] | None:
    query = """
        SELECT id, name, email, password_hash, document_number, phone, city, department, address, role, created_at, updated_at
        FROM app_users
        WHERE email = %(email)s;
    """
    with get_connection() as connection, connection.cursor() as cursor:
        cursor.execute(query, {"email": email.lower()})
        return cursor.fetchone()


def get_user_by_id(user_id: str) -> dict[str, Any] | None:
    query = """
        SELECT id, name, email, document_number, phone, city, department, address, role, created_at, updated_at
        FROM app_users
        WHERE id = %(user_id)s;
    """
    with get_connection() as connection, connection.cursor() as cursor:
        cursor.execute(query, {"user_id": user_id})
        return cursor.fetchone()


def update_user_profile(
    user_id: str,
    *,
    name: str,
    document_number: str,
    phone: str,
    city: str,
    department: str,
    address: str,
) -> dict[str, Any] | None:
    query = """
        UPDATE app_users
        SET name = %(name)s,
            document_number = %(document_number)s,
            phone = %(phone)s,
            city = %(city)s,
            department = %(department)s,
            address = %(address)s,
            updated_at = %(updated_at)s
        WHERE id = %(user_id)s
        RETURNING id, name, email, document_number, phone, city, department, address, role, created_at, updated_at;
    """
    with get_connection() as connection, connection.cursor() as cursor:
        cursor.execute(
            query,
            {
                "user_id": user_id,
                "name": name,
                "document_number": document_number,
                "phone": phone,
                "city": city,
                "department": department,
                "address": address,
                "updated_at": datetime.now(timezone.utc),
            },
        )
        return cursor.fetchone()


def create_temp_file(
    *,
    uploaded_by: str,
    file_kind: str,
    original_name: str,
    stored_name: str,
    mime_type: str,
    file_size: int,
    relative_path: str,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    query = """
        INSERT INTO case_files (
            case_id,
            uploaded_by,
            file_kind,
            status,
            original_name,
            stored_name,
            mime_type,
            file_size,
            relative_path,
            metadata
        )
        VALUES (
            NULL,
            %(uploaded_by)s,
            %(file_kind)s,
            'temporary',
            %(original_name)s,
            %(stored_name)s,
            %(mime_type)s,
            %(file_size)s,
            %(relative_path)s,
            %(metadata)s::jsonb
        )
        RETURNING *;
    """
    with get_connection() as connection, connection.cursor() as cursor:
        cursor.execute(
            query,
            {
                "uploaded_by": uploaded_by,
                "file_kind": file_kind,
                "original_name": original_name,
                "stored_name": stored_name,
                "mime_type": mime_type,
                "file_size": file_size,
                "relative_path": relative_path,
                "metadata": _json(metadata or {}),
            },
        )
        return cursor.fetchone()


def attach_files_to_case(case_id: str, user_id: str, file_ids: list[str]) -> list[dict[str, Any]]:
    if not file_ids:
        return []

    query = """
        UPDATE case_files
        SET case_id = %(case_id)s,
            status = 'attached'
        WHERE uploaded_by = %(user_id)s
          AND case_id IS NULL
          AND id = ANY(%(file_ids)s::uuid[])
        RETURNING *;
    """
    with get_connection() as connection, connection.cursor() as cursor:
        cursor.execute(query, {"case_id": case_id, "user_id": user_id, "file_ids": file_ids})
        return cursor.fetchall()


def create_case_file(
    *,
    case_id: str,
    uploaded_by: str,
    file_kind: str,
    original_name: str,
    stored_name: str,
    mime_type: str,
    file_size: int,
    relative_path: str,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    query = """
        INSERT INTO case_files (
            case_id,
            uploaded_by,
            file_kind,
            status,
            original_name,
            stored_name,
            mime_type,
            file_size,
            relative_path,
            metadata
        )
        VALUES (
            %(case_id)s,
            %(uploaded_by)s,
            %(file_kind)s,
            'attached',
            %(original_name)s,
            %(stored_name)s,
            %(mime_type)s,
            %(file_size)s,
            %(relative_path)s,
            %(metadata)s::jsonb
        )
        RETURNING *;
    """
    with get_connection() as connection, connection.cursor() as cursor:
        cursor.execute(
            query,
            {
                "case_id": case_id,
                "uploaded_by": uploaded_by,
                "file_kind": file_kind,
                "original_name": original_name,
                "stored_name": stored_name,
                "mime_type": mime_type,
                "file_size": file_size,
                "relative_path": relative_path,
                "metadata": _json(metadata or {}),
            },
        )
        return cursor.fetchone()


def find_duplicate_case_file(
    *,
    case_id: str,
    uploaded_by: str,
    original_name: str,
    mime_type: str,
    file_size: int,
) -> dict[str, Any] | None:
    query = """
        SELECT *
        FROM case_files
        WHERE case_id = %(case_id)s
          AND uploaded_by = %(uploaded_by)s
          AND status = 'attached'
          AND lower(original_name) = lower(%(original_name)s)
          AND mime_type = %(mime_type)s
          AND file_size = %(file_size)s
        ORDER BY created_at ASC
        LIMIT 1;
    """
    with get_connection() as connection, connection.cursor() as cursor:
        cursor.execute(
            query,
            {
                "case_id": case_id,
                "uploaded_by": uploaded_by,
                "original_name": original_name,
                "mime_type": mime_type,
                "file_size": file_size,
            },
        )
        return cursor.fetchone()


def update_file_location(file_id: str, *, case_id: str | None, relative_path: str, status: str = "attached") -> dict[str, Any] | None:
    query = """
        UPDATE case_files
        SET case_id = COALESCE(%(case_id)s, case_id),
            relative_path = %(relative_path)s,
            status = %(status)s
        WHERE id = %(file_id)s
        RETURNING *;
    """
    with get_connection() as connection, connection.cursor() as cursor:
        cursor.execute(
            query,
            {"file_id": file_id, "case_id": case_id, "relative_path": relative_path, "status": status},
        )
        return cursor.fetchone()


def list_files_for_case(case_id: str) -> list[dict[str, Any]]:
    query = """
        SELECT *
        FROM case_files
        WHERE case_id = %(case_id)s
        ORDER BY created_at ASC;
    """
    with get_connection() as connection, connection.cursor() as cursor:
        cursor.execute(query, {"case_id": case_id})
        return cursor.fetchall()


def get_file_by_id(file_id: str) -> dict[str, Any] | None:
    query = "SELECT * FROM case_files WHERE id = %(file_id)s;"
    with get_connection() as connection, connection.cursor() as cursor:
        cursor.execute(query, {"file_id": file_id})
        return cursor.fetchone()


def create_case_record(
    *,
    user_id: str,
    user_name: str,
    user_email: str,
    user_document: str,
    user_phone: str,
    city: str,
    department: str,
    address: str,
    workflow_type: str,
    category: str,
    description: str,
    recommended_action: str,
    strategy_text: str,
    facts: dict[str, Any],
    legal_analysis: dict[str, Any],
    routing: dict[str, Any],
    prerequisites: list[dict[str, Any]],
    warnings: list[str],
    attachment_ids: list[str],
) -> dict[str, Any]:
    query = """
        INSERT INTO casos (
            user_id,
            usuario_nombre,
            usuario_email,
            usuario_documento,
            usuario_telefono,
            usuario_ciudad,
            usuario_departamento,
            usuario_direccion,
            workflow_type,
            categoria,
            descripcion,
            attachments,
            facts,
            legal_analysis,
            routing,
            prerequisites,
            warnings,
            recommended_action,
            strategy_text,
            payment_status,
            estado
        )
        VALUES (
            %(user_id)s,
            %(user_name)s,
            %(user_email)s,
            %(user_document)s,
            %(user_phone)s,
            %(city)s,
            %(department)s,
            %(address)s,
            %(workflow_type)s,
            %(category)s,
            %(description)s,
            %(attachments)s::jsonb,
            %(facts)s::jsonb,
            %(legal_analysis)s::jsonb,
            %(routing)s::jsonb,
            %(prerequisites)s::jsonb,
            %(warnings)s::jsonb,
            %(recommended_action)s,
            %(strategy_text)s,
            'pendiente',
            'pendiente_pago'
        )
        RETURNING *;
    """
    params = {
        "user_id": user_id,
        "user_name": user_name,
        "user_email": user_email.lower(),
        "user_document": user_document,
        "user_phone": user_phone,
        "city": city,
        "department": department,
        "address": address,
        "workflow_type": workflow_type,
        "category": category,
        "description": description,
        "attachments": _json(attachment_ids),
        "facts": _json(facts),
        "legal_analysis": _json(legal_analysis),
        "routing": _json(routing),
        "prerequisites": _json(prerequisites),
        "warnings": _json(warnings),
        "recommended_action": recommended_action,
        "strategy_text": strategy_text,
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


def list_internal_cases(
    *,
    status: str | None = None,
    workflow_type: str | None = None,
    category: str | None = None,
) -> list[dict[str, Any]]:
    query = """
        SELECT *
        FROM casos
        WHERE (%(status)s IS NULL OR estado = %(status)s)
          AND (%(workflow_type)s IS NULL OR workflow_type = %(workflow_type)s)
          AND (%(category)s IS NULL OR categoria = %(category)s)
        ORDER BY created_at DESC;
    """
    with get_connection() as connection, connection.cursor() as cursor:
        cursor.execute(
            query,
            {"status": status, "workflow_type": workflow_type, "category": category},
        )
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


def delete_case_for_user(case_id: str, user_id: str) -> bool:
    query = """
        DELETE FROM casos
        WHERE id = %(case_id)s AND user_id = %(user_id)s
        RETURNING id;
    """
    with get_connection() as connection, connection.cursor() as cursor:
        cursor.execute(query, {"case_id": case_id, "user_id": user_id})
        return bool(cursor.fetchone())


def get_case_by_id(case_id: str) -> dict[str, Any] | None:
    query = "SELECT * FROM casos WHERE id = %(case_id)s;"
    with get_connection() as connection, connection.cursor() as cursor:
        cursor.execute(query, {"case_id": case_id})
        return cursor.fetchone()


def update_case_intake(
    case_id: str,
    *,
    workflow_type: str,
    description: str,
    facts: dict[str, Any],
    legal_analysis: dict[str, Any],
    routing: dict[str, Any],
    prerequisites: list[dict[str, Any]],
    warnings: list[str],
    recommended_action: str,
    strategy_text: str,
) -> dict[str, Any] | None:
    query = """
        UPDATE casos
        SET workflow_type = %(workflow_type)s,
            descripcion = %(description)s,
            facts = %(facts)s::jsonb,
            legal_analysis = %(legal_analysis)s::jsonb,
            routing = %(routing)s::jsonb,
            prerequisites = %(prerequisites)s::jsonb,
            warnings = %(warnings)s::jsonb,
            recommended_action = %(recommended_action)s,
            strategy_text = %(strategy_text)s,
            updated_at = %(updated_at)s
        WHERE id = %(case_id)s
        RETURNING *;
    """
    with get_connection() as connection, connection.cursor() as cursor:
        cursor.execute(
            query,
            {
                "case_id": case_id,
                "workflow_type": workflow_type,
                "description": description,
                "facts": _json(facts),
                "legal_analysis": _json(legal_analysis),
                "routing": _json(routing),
                "prerequisites": _json(prerequisites),
                "warnings": _json(warnings),
                "recommended_action": recommended_action,
                "strategy_text": strategy_text,
                "updated_at": datetime.now(timezone.utc),
            },
        )
        return cursor.fetchone()


def create_payment_order(
    *,
    case_id: str,
    user_id: str,
    environment: str,
    product_code: str,
    product_name: str,
    include_filing: bool,
    amount_cop: int,
    amount_in_cents: int,
    currency: str,
    reference: str,
    checkout_payload: dict[str, Any],
) -> dict[str, Any]:
    query = """
        INSERT INTO payment_orders (
            case_id,
            user_id,
            environment,
            product_code,
            product_name,
            include_filing,
            amount_cop,
            amount_in_cents,
            currency,
            reference,
            checkout_payload
        )
        VALUES (
            %(case_id)s,
            %(user_id)s,
            %(environment)s,
            %(product_code)s,
            %(product_name)s,
            %(include_filing)s,
            %(amount_cop)s,
            %(amount_in_cents)s,
            %(currency)s,
            %(reference)s,
            %(checkout_payload)s::jsonb
        )
        RETURNING *;
    """
    with get_connection() as connection, connection.cursor() as cursor:
        cursor.execute(
            query,
            {
                "case_id": case_id,
                "user_id": user_id,
                "environment": environment,
                "product_code": product_code,
                "product_name": product_name,
                "include_filing": include_filing,
                "amount_cop": amount_cop,
                "amount_in_cents": amount_in_cents,
                "currency": currency,
                "reference": reference,
                "checkout_payload": _json(checkout_payload),
            },
        )
        return cursor.fetchone()


def get_payment_order_by_reference(reference: str) -> dict[str, Any] | None:
    query = "SELECT * FROM payment_orders WHERE reference = %(reference)s;"
    with get_connection() as connection, connection.cursor() as cursor:
        cursor.execute(query, {"reference": reference})
        return cursor.fetchone()


def list_payment_orders_for_case(case_id: str) -> list[dict[str, Any]]:
    query = """
        SELECT *
        FROM payment_orders
        WHERE case_id = %(case_id)s
        ORDER BY created_at DESC;
    """
    with get_connection() as connection, connection.cursor() as cursor:
        cursor.execute(query, {"case_id": case_id})
        return cursor.fetchall()


def update_payment_order_status(
    reference: str,
    *,
    status: str,
    provider_transaction_id: str | None = None,
    provider_status: str | None = None,
    webhook_payload: dict[str, Any] | None = None,
    approved_at: datetime | None = None,
) -> dict[str, Any] | None:
    query = """
        UPDATE payment_orders
        SET status = %(status)s,
            provider_transaction_id = COALESCE(%(provider_transaction_id)s, provider_transaction_id),
            provider_status = COALESCE(%(provider_status)s, provider_status),
            webhook_payload = CASE
                WHEN %(webhook_payload)s IS NULL THEN webhook_payload
                ELSE %(webhook_payload)s::jsonb
            END,
            approved_at = COALESCE(%(approved_at)s, approved_at),
            updated_at = %(updated_at)s
        WHERE reference = %(reference)s
        RETURNING *;
    """
    with get_connection() as connection, connection.cursor() as cursor:
        cursor.execute(
            query,
            {
                "reference": reference,
                "status": status,
                "provider_transaction_id": provider_transaction_id,
                "provider_status": provider_status,
                "webhook_payload": _json(webhook_payload) if webhook_payload is not None else None,
                "approved_at": approved_at,
                "updated_at": datetime.now(timezone.utc),
            },
        )
        return cursor.fetchone()


def update_case_payment(case_id: str, payment_reference: str, payment_status: str = "pagado") -> dict[str, Any] | None:
    next_state = "listo_para_envio" if payment_status == "pagado" else "pendiente_pago"
    query = """
        UPDATE casos
        SET payment_status = %(payment_status)s,
            payment_reference = %(payment_reference)s,
            estado = %(estado)s,
            updated_at = %(updated_at)s
        WHERE id = %(case_id)s
        RETURNING *;
    """
    with get_connection() as connection, connection.cursor() as cursor:
        cursor.execute(
            query,
            {
                "case_id": case_id,
                "payment_status": payment_status,
                "payment_reference": payment_reference,
                "estado": next_state,
                "updated_at": datetime.now(timezone.utc),
            },
        )
        return cursor.fetchone()


def update_case_document(case_id: str, document: str) -> dict[str, Any] | None:
    query = """
        UPDATE casos
        SET generated_document = %(document)s,
            estado = 'listo_para_envio',
            updated_at = %(updated_at)s
        WHERE id = %(case_id)s
        RETURNING *;
    """
    with get_connection() as connection, connection.cursor() as cursor:
        cursor.execute(
            query,
            {"case_id": case_id, "document": document, "updated_at": datetime.now(timezone.utc)},
        )
        return cursor.fetchone()


def update_case_submission(
    case_id: str,
    *,
    status: str,
    manual_contact: dict[str, Any] | None = None,
    submission_summary: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    query = """
        UPDATE casos
        SET estado = %(status)s,
            manual_contact = %(manual_contact)s::jsonb,
            submission_summary = %(submission_summary)s::jsonb,
            updated_at = %(updated_at)s
        WHERE id = %(case_id)s
        RETURNING *;
    """
    with get_connection() as connection, connection.cursor() as cursor:
        cursor.execute(
            query,
            {
                "case_id": case_id,
                "status": status,
                "manual_contact": _json(manual_contact or {}),
                "submission_summary": _json(submission_summary or {}),
                "updated_at": datetime.now(timezone.utc),
            },
        )
        return cursor.fetchone()


def update_case_status(
    case_id: str,
    *,
    status: str,
    submission_summary: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    query = """
        UPDATE casos
        SET estado = %(status)s,
            submission_summary = CASE
                WHEN %(submission_summary)s IS NULL THEN submission_summary
                ELSE %(submission_summary)s::jsonb
            END,
            updated_at = %(updated_at)s
        WHERE id = %(case_id)s
        RETURNING *;
    """
    with get_connection() as connection, connection.cursor() as cursor:
        cursor.execute(
            query,
            {
                "case_id": case_id,
                "status": status,
                "submission_summary": _json(submission_summary) if submission_summary is not None else None,
                "updated_at": datetime.now(timezone.utc),
            },
        )
        return cursor.fetchone()


def create_submission_attempt(
    *,
    case_id: str,
    channel: str,
    destination_name: str | None,
    destination_contact: str | None,
    subject: str | None,
    cc: list[str],
    status: str,
    radicado: str | None,
    response_payload: dict[str, Any] | None = None,
    error_text: str | None = None,
) -> dict[str, Any]:
    query = """
        INSERT INTO submission_attempts (
            case_id,
            channel,
            destination_name,
            destination_contact,
            subject,
            cc,
            status,
            radicado,
            response_payload,
            error_text
        )
        VALUES (
            %(case_id)s,
            %(channel)s,
            %(destination_name)s,
            %(destination_contact)s,
            %(subject)s,
            %(cc)s::jsonb,
            %(status)s,
            %(radicado)s,
            %(response_payload)s::jsonb,
            %(error_text)s
        )
        RETURNING *;
    """
    with get_connection() as connection, connection.cursor() as cursor:
        cursor.execute(
            query,
            {
                "case_id": case_id,
                "channel": channel,
                "destination_name": destination_name,
                "destination_contact": destination_contact,
                "subject": subject,
                "cc": _json(cc),
                "status": status,
                "radicado": radicado,
                "response_payload": _json(response_payload or {}),
                "error_text": error_text,
            },
        )
        return cursor.fetchone()


def list_submission_attempts(case_id: str) -> list[dict[str, Any]]:
    query = """
        SELECT *
        FROM submission_attempts
        WHERE case_id = %(case_id)s
        ORDER BY created_at DESC;
    """
    with get_connection() as connection, connection.cursor() as cursor:
        cursor.execute(query, {"case_id": case_id})
        return cursor.fetchall()


def create_event(
    *,
    case_id: str,
    event_type: str,
    actor_type: str = "system",
    actor_id: str | None = None,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    query = """
        INSERT INTO case_events (case_id, event_type, actor_type, actor_id, payload)
        VALUES (%(case_id)s, %(event_type)s, %(actor_type)s, %(actor_id)s, %(payload)s::jsonb)
        RETURNING *;
    """
    with get_connection() as connection, connection.cursor() as cursor:
        cursor.execute(
            query,
            {
                "case_id": case_id,
                "event_type": event_type,
                "actor_type": actor_type,
                "actor_id": actor_id,
                "payload": _json(payload or {}),
            },
        )
        return cursor.fetchone()


def list_case_events(case_id: str) -> list[dict[str, Any]]:
    query = """
        SELECT *
        FROM case_events
        WHERE case_id = %(case_id)s
        ORDER BY created_at ASC;
    """
    with get_connection() as connection, connection.cursor() as cursor:
        cursor.execute(query, {"case_id": case_id})
        return cursor.fetchall()


def search_court_targets(city: str, department: str) -> list[dict[str, Any]]:
    query = """
        SELECT *
        FROM juzgados
        WHERE UPPER(codigo_interno) = 'NAC-001'
           OR UPPER(municipio) = UPPER(%(city)s)
           OR UPPER(departamento) = UPPER(%(department)s)
        ORDER BY
            CASE
                WHEN UPPER(municipio) = UPPER(%(city)s) THEN 0
                WHEN UPPER(departamento) = UPPER(%(department)s) THEN 1
                WHEN UPPER(codigo_interno) = 'NAC-001' THEN 2
                ELSE 3
            END,
            created_at ASC
        LIMIT 5;
    """
    with get_connection() as connection, connection.cursor() as cursor:
        cursor.execute(query, {"city": city, "department": department})
        return cursor.fetchall()


def search_entities(category: str, entity_names: list[str]) -> list[dict[str, Any]]:
    patterns = [f"%{category.lower()}%"] + [f"%{name.lower()}%" for name in entity_names if name]
    query = """
        SELECT *
        FROM entidades
        WHERE LOWER(modulo) LIKE LOWER(%(category)s)
           OR LOWER(nombre_entidad) LIKE ANY(%(patterns)s)
        ORDER BY prioridad ASC NULLS LAST, created_at ASC
        LIMIT 6;
    """
    with get_connection() as connection, connection.cursor() as cursor:
        cursor.execute(query, {"category": f"%{category}%", "patterns": patterns})
        return cursor.fetchall()


def search_entity_directory(query_text: str, limit: int = 12) -> list[dict[str, Any]]:
    pattern = f"%{query_text.strip().lower()}%"
    query = """
        SELECT *
        FROM entidades
        WHERE LOWER(nombre_entidad) LIKE %(pattern)s
        ORDER BY prioridad ASC NULLS LAST, created_at ASC
        LIMIT %(limit)s;
    """
    with get_connection() as connection, connection.cursor() as cursor:
        cursor.execute(query, {"pattern": pattern, "limit": limit})
        return cursor.fetchall()


def list_business_rules() -> list[dict[str, Any]]:
    query = "SELECT * FROM business_rules ORDER BY created_at ASC;"
    with get_connection() as connection, connection.cursor() as cursor:
        cursor.execute(query)
        return cursor.fetchall()


def upsert_knowledge_item(source_key: str, title: str, content: dict[str, Any], source: str, tags: list[str]) -> None:
    query = """
        INSERT INTO conocimiento_legal (source_key, titulo, contenido, fuente, tags)
        VALUES (%(source_key)s, %(title)s, %(content)s::jsonb, %(source)s, %(tags)s)
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


def upsert_business_rule(
    rule_key: str,
    title: str,
    description: str,
    action_text: str | None,
    priority: str | None,
    metadata: dict[str, Any] | None = None,
) -> None:
    query = """
        INSERT INTO business_rules (rule_key, title, description, action_text, priority, metadata)
        VALUES (%(rule_key)s, %(title)s, %(description)s, %(action_text)s, %(priority)s, %(metadata)s::jsonb)
        ON CONFLICT (rule_key)
        DO UPDATE SET
            title = EXCLUDED.title,
            description = EXCLUDED.description,
            action_text = EXCLUDED.action_text,
            priority = EXCLUDED.priority,
            metadata = EXCLUDED.metadata;
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
                "metadata": _json(metadata or {}),
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
