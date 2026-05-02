from __future__ import annotations

import smtplib
import ssl
import json
import urllib.request
import urllib.error
import re
from email.message import EmailMessage
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from backend.config import settings
from backend.storage import absolute_path


def _notification_sender_email() -> str:
    return settings.notification_from_email or settings.notifications_email


def _notification_reply_to_email() -> str:
    return settings.notification_reply_to or settings.support_email


def _notification_smtp_user() -> str:
    return settings.notification_smtp_user or _notification_sender_email()


def _notification_smtp_password() -> str:
    return settings.notification_smtp_password


def _radication_sender_email() -> str:
    return settings.radications_email


def _radication_reply_to_email() -> str:
    return settings.radications_email


def _radication_smtp_user() -> str:
    return settings.radications_smtp_user or settings.notification_smtp_user or _radication_sender_email()


def _radication_smtp_password() -> str:
    return settings.radications_smtp_password or settings.notification_smtp_password


def _is_email_configured() -> bool:
    return bool(
        settings.notification_smtp_host
        and settings.notification_smtp_port
        and (_notification_sender_email() or _radication_sender_email())
    )


def _is_whatsapp_configured() -> bool:
    if not settings.whatsapp_enabled:
        return False
    return bool(settings.evolution_base_url and settings.evolution_api_key and settings.evolution_instance)


def _is_n8n_whatsapp_configured() -> bool:
    if not settings.whatsapp_enabled:
        return False
    return bool(settings.n8n_whatsapp_webhook_url)


def _n8n_whatsapp_headers() -> dict[str, str]:
    headers = {"Content-Type": "application/json"}
    if settings.n8n_whatsapp_webhook_api_key:
        headers["x-api-key"] = settings.n8n_whatsapp_webhook_api_key
    return headers


def _normalize_whatsapp_number(phone: str | None) -> str:
    digits = re.sub(r"\D+", "", str(phone or ""))
    if not digits:
        return ""
    if digits.startswith("57") and len(digits) >= 12:
        return digits
    if len(digits) == 10:
        return f"57{digits}"
    if digits.startswith("0") and len(digits) == 11:
        return f"57{digits[1:]}"
    return digits


def _post_json(url: str, payload: dict[str, Any], headers: dict[str, str]) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=20) as response:  # nosec - controlled host from env
        body = response.read().decode("utf-8", errors="ignore")
        try:
            return json.loads(body) if body else {}
        except json.JSONDecodeError:
            return {"raw": body}


def _attach_files(message: EmailMessage, attachments: list[dict[str, str]] | None = None) -> list[str]:
    attached_files: list[str] = []
    for item in attachments or []:
        relative_path = str(item.get("relative_path") or "").strip()
        filename = str(item.get("filename") or Path(relative_path).name or "adjunto.bin").strip()
        mime_type = str(item.get("mime_type") or "application/octet-stream").strip()
        if not relative_path:
            continue
        file_path = absolute_path(relative_path)
        if not file_path.exists():
            continue
        maintype, _, subtype = mime_type.partition("/")
        message.add_attachment(file_path.read_bytes(), maintype=maintype or "application", subtype=subtype or "octet-stream", filename=filename)
        attached_files.append(filename)
    return attached_files


def _post_radicado_user_guidance(case: dict[str, Any], guidance: dict[str, Any]) -> dict[str, Any]:
    submission_policy = guidance.get("submission_policy") or {}
    document_family = str(submission_policy.get("document_family") or "").lower()
    product = str(case.get("recommended_action") or "tramite")
    destination = ((case.get("routing") or {}).get("primary_target") or {}).get("name") or "la entidad o autoridad competente"
    panel_steps = [
        "En tu panel veras si el caso esta enviado, si ya hay radicado y si aparece una novedad nueva.",
        "Si la EPS, la entidad o el juzgado te llaman o te escriben, registra ese dato en tu panel o repórtalo a soporte para dejar trazabilidad.",
        "Si te piden documentos adicionales, respuesta o aclaracion, debes reportarlo de inmediato para definir el siguiente paso.",
    ]
    if "tutela" in document_family or "impugnacion" in document_family or "desacato" in document_family:
        timeline_title = "Que puede pasar ahora con esta actuacion judicial"
        timeline_items = [
            f"El despacho o el sistema de reparto puede asignar el caso y generar constancia o radicado a nombre de {destination}.",
            "El juzgado puede notificar a la EPS o a la entidad accionada y pedir respuesta o soportes en un termino corto.",
            "La EPS o la entidad te puede llamar, escribir o pedir verificaciones sobre los hechos, la orden medica o los anexos.",
            "Si hay decision favorable pero no cumplen, el siguiente paso puede ser seguimiento, impugnacion o desacato segun corresponda.",
        ]
        expected_window = (
            "En tutela no aplica una espera general de 15 dias habiles: el reparto y las actuaciones suelen moverse en horas o pocos dias, "
            "y la decision judicial normalmente es mas rapida que un tramite administrativo ordinario."
        )
    elif "derecho_peticion" in document_family:
        timeline_title = "Que puede pasar ahora con tu peticion"
        timeline_items = [
            f"La entidad destinataria debe recibir y tramitar la solicitud enviada a {destination}.",
            "La entidad puede responder por correo, por su portal o llamarte para validar informacion o soportes.",
            "Si no responden de fondo dentro del termino legal o la respuesta es insuficiente, puede tocar escalar a tutela.",
        ]
        expected_window = (
            "En peticiones ordinarias la entidad suele tener un termino de respuesta de hasta 15 dias habiles, "
            "salvo reglas especiales del sector o del tipo de solicitud."
        )
    else:
        timeline_title = "Que puede pasar ahora"
        timeline_items = [
            f"La entidad o autoridad destinataria en {destination} puede emitir radicado, acuse o respuesta inicial.",
            "Pueden llamarte o escribirte para validar hechos, anexos o datos de contacto.",
            "Si aparece una respuesta, requerimiento o incumplimiento, el siguiente paso se define desde tu panel.",
        ]
        expected_window = guidance.get("estimated_response_window") or "El tiempo de respuesta depende del canal y del tipo de tramite."

    return {
        "timeline_title": timeline_title,
        "timeline_items": timeline_items,
        "expected_window": expected_window,
        "panel_steps": panel_steps,
        "support_copy": (
            "Si pagaste envio o seguimiento, no necesitas salirte del flujo: revisa tu panel, conserva tus llamadas o correos y repórtanos cualquier novedad "
            f"en {settings.support_email} para actualizar el expediente."
        ),
        "customer_copy": (
            "Recibiras este correo con copia del documento enviado y, cuando exista, el comprobante disponible en el expediente. "
            "Si el juzgado, la EPS o la entidad te responde a tu correo o por llamada directa, esa novedad no entra sola al panel: debes reportarla o subir la evidencia."
        ),
        "product": product,
        "destination": destination,
    }


def build_post_radicado_email(case: dict[str, Any], guidance: dict[str, Any]) -> dict[str, str]:
    helper = _post_radicado_user_guidance(case, guidance)
    product = helper["product"]
    destination = helper["destination"]
    radicado = ((guidance.get("routing_snapshot") or {}).get("radicado")) or "Pendiente de confirmacion"
    channel = guidance.get("channel") or "manual"
    proof_type = guidance.get("proof_type") or "constancia"
    estimated = guidance.get("estimated_response_window") or "Pendiente de definir"
    next_step = guidance.get("next_step_suggestion") or "Sigue el caso desde tu panel."
    continuity = guidance.get("continuity_offers") or []
    continuity_text = ", ".join(str(item) for item in continuity) or "seguimiento del caso"
    headline = (guidance.get("post_radicado_copy") or {}).get("headline") or "Tu tramite fue enviado."
    body = (guidance.get("post_radicado_copy") or {}).get("body") or "Ya puedes revisar el detalle en tu panel."
    timeline_title = helper["timeline_title"]
    timeline_items = helper["timeline_items"]
    panel_steps = helper["panel_steps"]
    support_copy = helper["support_copy"]
    customer_copy = helper["customer_copy"]
    expected_window = helper["expected_window"]
    timeline_text = "\n".join(f"- {item}" for item in timeline_items)
    panel_steps_text = "\n".join(f"- {item}" for item in panel_steps)
    timeline_html = "".join(f"<li>{item}</li>" for item in timeline_items)
    panel_html = "".join(f"<li>{item}</li>" for item in panel_steps)

    subject = f"123tutela | Tu tramite fue enviado: {product}"
    text_body = f"""
{headline}

{body}

Que sigue ahora:
{timeline_title}
{timeline_text}

Producto: {product}
Destino: {destination}
Canal usado: {channel}
Evidencia disponible: {proof_type}
Radicado o comprobante: {radicado}

Tiempo estimado y expectativa real:
{expected_window}

Como seguirlo desde tu panel:
{panel_steps_text}

Si pagaste envio o seguimiento:
{support_copy}

Canales de copia y respuesta:
{customer_copy}

Siguiente paso sugerido:
{next_step}

Continuidad posible:
{continuity_text}

Panel del cliente:
{settings.frontend_url}
""".strip()
    html_body = f"""
<h2>{headline}</h2>
<p>{body}</p>
<p><strong>Que sigue ahora:</strong><br>{timeline_title}</p>
<ul>{timeline_html}</ul>
<p><strong>Producto:</strong> {product}</p>
<p><strong>Destino:</strong> {destination}</p>
<p><strong>Canal usado:</strong> {channel}</p>
<p><strong>Evidencia disponible:</strong> {proof_type}</p>
<p><strong>Radicado o comprobante:</strong> {radicado}</p>
<p><strong>Tiempo estimado y expectativa real:</strong><br>{expected_window}</p>
<p><strong>Como seguirlo desde tu panel:</strong></p>
<ul>{panel_html}</ul>
<p><strong>Si pagaste envio o seguimiento:</strong><br>{support_copy}</p>
<p><strong>Canales de copia y respuesta:</strong><br>{customer_copy}</p>
<p><strong>Siguiente paso sugerido:</strong><br>{next_step}</p>
<p><strong>Continuidad posible:</strong><br>{continuity_text}</p>
<p><strong>Panel del cliente:</strong><br><a href="{settings.frontend_url}">{settings.frontend_url}</a></p>
""".strip()
    return {"subject": subject, "text": text_body, "html": html_body}


def build_post_radicado_whatsapp(case: dict[str, Any], guidance: dict[str, Any]) -> str:
    helper = _post_radicado_user_guidance(case, guidance)
    product = helper["product"]
    radicado = ((guidance.get("routing_snapshot") or {}).get("radicado")) or "pendiente de confirmacion"
    next_step = guidance.get("next_step_suggestion") or "Sigue el caso desde tu panel."
    return (
        f"123tutela: tu tramite fue enviado.\n\n"
        f"Documento: {product}\n"
        f"Radicado o comprobante: {radicado}\n"
        f"Siguiente paso: {next_step}\n\n"
        f"Si el juzgado, la EPS o la entidad te llama o te escribe por fuera del panel, repórtalo en tu expediente.\n"
        f"Panel: {settings.frontend_url}"
    )


def send_post_radicado_email(*, recipient: str | None, case: dict[str, Any], guidance: dict[str, Any]) -> dict[str, Any]:
    attempted_at = datetime.now(timezone.utc).isoformat()
    base_result = {
        "provider": settings.notification_provider,
        "transport": "smtp",
        "attempted_at": attempted_at,
        "recipient": recipient,
        "from_email": _notification_sender_email(),
        "reply_to": _notification_reply_to_email(),
    }
    if not recipient:
        return {**base_result, "status": "skipped", "reason": "missing_recipient"}
    if not _is_email_configured():
        return {**base_result, "status": "pending_configuration", "reason": "smtp_not_configured"}

    content = build_post_radicado_email(case, guidance)
    message = EmailMessage()
    message["Subject"] = content["subject"]
    message["From"] = _notification_sender_email()
    message["To"] = recipient
    if _notification_reply_to_email():
        message["Reply-To"] = _notification_reply_to_email()
    message.set_content(content["text"])
    message.add_alternative(content["html"], subtype="html")
    signed_artifacts = ((case.get("submission_summary") or {}).get("signed_artifacts") or {})
    attached_files = _attach_files(
        message,
        attachments=[
            {
                "relative_path": signed_artifacts.get("docx_relative_path", ""),
                "filename": signed_artifacts.get("docx_filename", "documento_firmado.docx"),
                "mime_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            },
            {
                "relative_path": signed_artifacts.get("pdf_relative_path", ""),
                "filename": signed_artifacts.get("pdf_filename", "documento_firmado.pdf"),
                "mime_type": "application/pdf",
            },
        ],
    )

    try:
        if settings.notification_smtp_use_ssl:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(
                settings.notification_smtp_host,
                settings.notification_smtp_port,
                context=context,
                timeout=20,
            ) as server:
                if _notification_smtp_user():
                    server.login(_notification_smtp_user(), _notification_smtp_password())
                server.send_message(message)
        else:
            with smtplib.SMTP(
                settings.notification_smtp_host,
                settings.notification_smtp_port,
                timeout=20,
            ) as server:
                if settings.notification_smtp_use_starttls:
                    server.starttls(context=ssl.create_default_context())
                if _notification_smtp_user():
                    server.login(_notification_smtp_user(), _notification_smtp_password())
                server.send_message(message)
    except Exception as exc:  # pragma: no cover
        return {
            **base_result,
            "status": "error",
            "reason": str(exc),
            "subject": content["subject"],
            "attachments": attached_files,
        }

    return {
        **base_result,
        "status": "sent",
        "subject": content["subject"],
        "attachments": attached_files,
    }


def send_post_radicado_whatsapp(*, phone: str | None, case: dict[str, Any], guidance: dict[str, Any]) -> dict[str, Any]:
    attempted_at = datetime.now(timezone.utc).isoformat()
    normalized_phone = _normalize_whatsapp_number(phone)
    message_text = build_post_radicado_whatsapp(case, guidance)
    base_result = {
        "provider": "n8n" if _is_n8n_whatsapp_configured() else "evolution",
        "transport": "whatsapp",
        "attempted_at": attempted_at,
        "recipient": normalized_phone or phone,
        "instance": settings.evolution_instance,
    }
    if not settings.whatsapp_enabled:
        return {**base_result, "status": "disabled", "reason": "whatsapp_disabled"}
    if not normalized_phone:
        return {**base_result, "status": "skipped", "reason": "missing_phone"}
    if _is_n8n_whatsapp_configured():
        payload = {
            "number": normalized_phone,
            "text": message_text,
            "case_id": case.get("id"),
            "document": case.get("recommended_action"),
            "radicado": ((guidance.get("routing_snapshot") or {}).get("radicado")) or "",
            "evolution_base_url": settings.evolution_base_url,
            "evolution_api_key": settings.evolution_api_key,
            "evolution_instance": settings.evolution_instance,
        }
        try:
            response_payload = _post_json(
                settings.n8n_whatsapp_webhook_url,
                payload,
                _n8n_whatsapp_headers(),
            )
        except urllib.error.HTTPError as exc:  # pragma: no cover
            body = exc.read().decode("utf-8", errors="ignore")
            return {
                **base_result,
                "status": "error",
                "reason": f"http_{exc.code}",
                "response_body": body[:500],
            }
        except Exception as exc:  # pragma: no cover
            return {
                **base_result,
                "status": "error",
                "reason": str(exc),
            }
        return {
            **base_result,
            "status": "sent",
            "response_payload": response_payload,
        }
    if not _is_whatsapp_configured():
        return {**base_result, "status": "pending_configuration", "reason": "evolution_not_configured"}

    version = str(settings.evolution_api_version or "v2").strip().lower()
    base_url = settings.evolution_base_url.rstrip("/")
    if version == "v1":
        url = f"{base_url}/message/sendText/{settings.evolution_instance}"
    else:
        url = f"{base_url}/message/sendText/{settings.evolution_instance}"
    payload = {
        "number": normalized_phone,
        "text": message_text,
        "linkPreview": False,
    }
    headers = {
        "Content-Type": "application/json",
        "apikey": settings.evolution_api_key,
    }
    try:
        response_payload = _post_json(url, payload, headers)
    except urllib.error.HTTPError as exc:  # pragma: no cover
        body = exc.read().decode("utf-8", errors="ignore")
        return {
            **base_result,
            "status": "error",
            "reason": f"http_{exc.code}",
            "response_body": body[:500],
        }
    except Exception as exc:  # pragma: no cover
        return {
            **base_result,
            "status": "error",
            "reason": str(exc),
        }

    return {
        **base_result,
        "status": "sent",
        "response_payload": response_payload,
    }


def send_signed_submission_email(
    *,
    recipient: str | None,
    subject: str,
    body_text: str,
    body_html: str,
    attachments: list[dict[str, str]] | None = None,
    reply_to: str | None = None,
) -> dict[str, Any]:
    attempted_at = datetime.now(timezone.utc).isoformat()
    base_result = {
        "provider": settings.notification_provider,
        "transport": "smtp",
        "attempted_at": attempted_at,
        "recipient": recipient,
        "from_email": _radication_sender_email(),
        "reply_to": reply_to or _radication_reply_to_email(),
    }
    if not recipient:
        return {**base_result, "status": "skipped", "reason": "missing_recipient"}
    if not _is_email_configured():
        return {**base_result, "status": "pending_configuration", "reason": "smtp_not_configured"}

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = _radication_sender_email()
    message["To"] = recipient
    if reply_to or _radication_reply_to_email():
        message["Reply-To"] = reply_to or _radication_reply_to_email()
    message.set_content(body_text)
    message.add_alternative(body_html, subtype="html")

    attached_files = _attach_files(message, attachments)

    try:
        if settings.notification_smtp_use_ssl:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(settings.notification_smtp_host, settings.notification_smtp_port, context=context, timeout=20) as server:
                if _radication_smtp_user():
                    server.login(_radication_smtp_user(), _radication_smtp_password())
                server.send_message(message)
        else:
            with smtplib.SMTP(settings.notification_smtp_host, settings.notification_smtp_port, timeout=20) as server:
                if settings.notification_smtp_use_starttls:
                    server.starttls(context=ssl.create_default_context())
                if _radication_smtp_user():
                    server.login(_radication_smtp_user(), _radication_smtp_password())
                server.send_message(message)
    except Exception as exc:  # pragma: no cover
        return {
            **base_result,
            "status": "error",
            "reason": str(exc),
            "subject": subject,
            "attachments": attached_files,
        }

    return {
        **base_result,
        "status": "sent",
        "subject": subject,
        "attachments": attached_files,
    }


def build_guest_delivery_email(case: dict[str, Any], delivery_package: dict[str, Any], note: str | None = None) -> dict[str, str]:
    guide = delivery_package.get("customer_guide") or {}
    attachments = guide.get("required_attachments") or []
    asks = guide.get("what_to_ask_for") or []
    customer_name = str(case.get("usuario_nombre") or case.get("user_name") or "cliente").strip()
    first_name = customer_name.split()[0] if customer_name else "cliente"
    subject = f"HazloPorMi | Tu documento esta listo: {case.get('recommended_action') or 'tramite'}"
    text = f"""
Hola {first_name},

Tu documento ya esta listo.

Documento recomendado: {case.get('recommended_action') or 'tramite'}
Categoria: {case.get('categoria') or ''}

Que vas a presentar:
{guide.get('what_you_will_present') or ''}

Donde presentarlo:
{guide.get('where_to_submit') or ''}

Como presentarlo:
{guide.get('how_to_submit') or ''}

Documentos que debes llevar o adjuntar:
{chr(10).join(f"- {item}" for item in attachments)}

Que pedir exactamente:
{chr(10).join(f"- {item}" for item in asks)}

Como guardar prueba:
{guide.get('how_to_keep_proof') or ''}

Tiempo esperado:
{guide.get('estimated_response_window') or ''}

Si no responden:
{guide.get('next_step_if_no_response') or ''}

Si niegan la solicitud:
{guide.get('next_step_if_denied') or ''}

Servicio adicional disponible:
Si quieres que 123tutela lo haga por ti, puedes activar por $65.000 adicionales un paquete de elaboracion, radicacion y seguimiento del mismo caso hasta desacato (no incluye demandas), segun lineamientos y tiempos disponibles.

Te deseamos muchos exitos en la solucion de tu caso. Tambien te recordamos que con tu pago aprobado quedas participando en la rifa vigente del mes.

{note or ''}
""".strip()
    html = f"""
<h2>Hola {first_name}, tu documento ya esta listo</h2>
<p><strong>Documento recomendado:</strong> {case.get('recommended_action') or 'tramite'}</p>
<p><strong>Categoria:</strong> {case.get('categoria') or ''}</p>
<p><strong>Que vas a presentar:</strong><br>{guide.get('what_you_will_present') or ''}</p>
<p><strong>Donde presentarlo:</strong><br>{guide.get('where_to_submit') or ''}</p>
<p><strong>Como presentarlo:</strong><br>{guide.get('how_to_submit') or ''}</p>
<p><strong>Documentos que debes llevar o adjuntar:</strong></p>
<ul>{''.join(f'<li>{item}</li>' for item in attachments)}</ul>
<p><strong>Que pedir exactamente:</strong></p>
<ul>{''.join(f'<li>{item}</li>' for item in asks)}</ul>
<p><strong>Como guardar prueba:</strong><br>{guide.get('how_to_keep_proof') or ''}</p>
<p><strong>Tiempo esperado:</strong><br>{guide.get('estimated_response_window') or ''}</p>
<p><strong>Si no responden:</strong><br>{guide.get('next_step_if_no_response') or ''}</p>
<p><strong>Si niegan la solicitud:</strong><br>{guide.get('next_step_if_denied') or ''}</p>
<p><strong>Servicio adicional disponible:</strong><br>Si quieres que 123tutela lo haga por ti, puedes activar por $65.000 adicionales un paquete de elaboracion, radicacion y seguimiento del mismo caso hasta desacato (no incluye demandas), segun lineamientos y tiempos disponibles.</p>
<p>Te deseamos muchos exitos en la solucion de tu caso. Con tu pago aprobado participas en la rifa vigente del mes.</p>
<p>{note or ''}</p>
""".strip()
    return {"subject": subject, "text": text, "html": html}


def send_guest_delivery_email(
    *,
    recipient: str | None,
    case: dict[str, Any],
    delivery_package: dict[str, Any],
    note: str | None = None,
    attachments: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    content = build_guest_delivery_email(case, delivery_package, note)
    return send_signed_submission_email(
        recipient=recipient,
        subject=content["subject"],
        body_text=content["text"],
        body_html=content["html"],
        attachments=attachments,
        reply_to=_notification_reply_to_email(),
    )


def send_guest_delivery_whatsapp(
    *,
    phone: str | None,
    case: dict[str, Any],
    delivery_package: dict[str, Any],
) -> dict[str, Any]:
    guide = delivery_package.get("customer_guide") or {}
    message = (
        f"HazloPorMi: tu documento ya esta listo.\n\n"
        f"Documento: {case.get('recommended_action') or 'tramite'}\n"
        f"Donde presentarlo: {guide.get('where_to_submit') or ''}\n"
        f"Tiempo esperado: {guide.get('estimated_response_window') or ''}\n"
        f"Si no responden: {guide.get('next_step_if_no_response') or ''}"
    )
    attempted_at = datetime.now(timezone.utc).isoformat()
    normalized_phone = _normalize_whatsapp_number(phone)
    base_result = {
        "provider": "n8n" if _is_n8n_whatsapp_configured() else "evolution",
        "transport": "whatsapp",
        "attempted_at": attempted_at,
        "recipient": normalized_phone or phone,
    }
    if not settings.whatsapp_enabled:
        return {**base_result, "status": "disabled", "reason": "whatsapp_disabled"}
    if not normalized_phone:
        return {**base_result, "status": "skipped", "reason": "missing_phone"}
    if _is_n8n_whatsapp_configured():
        try:
            response_payload = _post_json(
                settings.n8n_whatsapp_webhook_url,
                {"number": normalized_phone, "text": message, "case_id": case.get("id"), "document": case.get("recommended_action")},
                _n8n_whatsapp_headers(),
            )
            return {**base_result, "status": "sent", "response_payload": response_payload}
        except urllib.error.HTTPError as exc:  # pragma: no cover
            body = exc.read().decode("utf-8", errors="ignore")
            return {**base_result, "status": "error", "reason": f"http_{exc.code}", "response_body": body[:500]}
        except Exception as exc:  # pragma: no cover
            return {**base_result, "status": "error", "reason": str(exc)}
    if not _is_whatsapp_configured():
        return {**base_result, "status": "pending_configuration", "reason": "evolution_not_configured"}
    try:
        response_payload = _post_json(
            f"{settings.evolution_base_url.rstrip('/')}/message/sendText/{settings.evolution_instance}",
            {"number": normalized_phone, "text": message, "linkPreview": False},
            {"Content-Type": "application/json", "apikey": settings.evolution_api_key},
        )
        return {**base_result, "status": "sent", "response_payload": response_payload}
    except urllib.error.HTTPError as exc:  # pragma: no cover
        body = exc.read().decode("utf-8", errors="ignore")
        return {**base_result, "status": "error", "reason": f"http_{exc.code}", "response_body": body[:500]}
    except Exception as exc:  # pragma: no cover
        return {**base_result, "status": "error", "reason": str(exc)}


def send_diagnosis_abandonment_whatsapp(
    *,
    phone: str | None,
    case: dict[str, Any],
    reminder_minutes: int,
    resume_url: str,
) -> dict[str, Any]:
    action = str(case.get("recommended_action") or "tu documento recomendado")
    first_name = str(case.get("usuario_nombre") or "").strip().split(" ")[0] or "Hola"
    message = (
        f"{first_name}, tu diagnostico en 123tutela ya quedo listo.\n\n"
        f"Accion sugerida: {action}\n"
        f"Llevas {int(reminder_minutes)} minutos sin activar el pago.\n"
        f"Retoma aqui: {resume_url}\n\n"
        "Si necesitas ayuda, responde este mensaje."
    )
    attempted_at = datetime.now(timezone.utc).isoformat()
    normalized_phone = _normalize_whatsapp_number(phone)
    base_result = {
        "provider": "n8n" if _is_n8n_whatsapp_configured() else "evolution",
        "transport": "whatsapp",
        "attempted_at": attempted_at,
        "recipient": normalized_phone or phone,
        "reminder_minutes": int(reminder_minutes),
    }
    if not settings.whatsapp_enabled:
        return {**base_result, "status": "disabled", "reason": "whatsapp_disabled"}
    if not normalized_phone:
        return {**base_result, "status": "skipped", "reason": "missing_phone"}
    if _is_n8n_whatsapp_configured():
        try:
            response_payload = _post_json(
                settings.n8n_whatsapp_webhook_url,
                {
                    "number": normalized_phone,
                    "text": message,
                    "case_id": case.get("id"),
                    "document": case.get("recommended_action"),
                    "kind": "diagnosis_abandonment",
                    "reminder_minutes": int(reminder_minutes),
                },
                _n8n_whatsapp_headers(),
            )
            return {**base_result, "status": "sent", "response_payload": response_payload}
        except urllib.error.HTTPError as exc:  # pragma: no cover
            body = exc.read().decode("utf-8", errors="ignore")
            return {**base_result, "status": "error", "reason": f"http_{exc.code}", "response_body": body[:500]}
        except Exception as exc:  # pragma: no cover
            return {**base_result, "status": "error", "reason": str(exc)}
    if not _is_whatsapp_configured():
        return {**base_result, "status": "pending_configuration", "reason": "evolution_not_configured"}
    try:
        response_payload = _post_json(
            f"{settings.evolution_base_url.rstrip('/')}/message/sendText/{settings.evolution_instance}",
            {"number": normalized_phone, "text": message, "linkPreview": False},
            {"Content-Type": "application/json", "apikey": settings.evolution_api_key},
        )
        return {**base_result, "status": "sent", "response_payload": response_payload}
    except urllib.error.HTTPError as exc:  # pragma: no cover
        body = exc.read().decode("utf-8", errors="ignore")
        return {**base_result, "status": "error", "reason": f"http_{exc.code}", "response_body": body[:500]}
    except Exception as exc:  # pragma: no cover
        return {**base_result, "status": "error", "reason": str(exc)}
