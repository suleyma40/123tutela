from __future__ import annotations

import smtplib
import ssl
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


def build_post_radicado_email(case: dict[str, Any], guidance: dict[str, Any]) -> dict[str, str]:
    product = str(case.get("recommended_action") or "tramite")
    destination = ((case.get("routing") or {}).get("primary_target") or {}).get("name") or "la entidad o autoridad competente"
    radicado = ((guidance.get("routing_snapshot") or {}).get("radicado")) or "Pendiente de confirmacion"
    channel = guidance.get("channel") or "manual"
    proof_type = guidance.get("proof_type") or "constancia"
    estimated = guidance.get("estimated_response_window") or "Pendiente de definir"
    next_step = guidance.get("next_step_suggestion") or "Sigue el caso desde tu panel."
    continuity = guidance.get("continuity_offers") or []
    continuity_text = ", ".join(str(item) for item in continuity) or "seguimiento del caso"
    headline = (guidance.get("post_radicado_copy") or {}).get("headline") or "Tu tramite fue enviado."
    body = (guidance.get("post_radicado_copy") or {}).get("body") or "Ya puedes revisar el detalle en tu panel."

    subject = f"123tutela | Tu tramite fue enviado: {product}"
    text_body = f"""
{headline}

{body}

Producto: {product}
Destino: {destination}
Canal usado: {channel}
Evidencia disponible: {proof_type}
Radicado o comprobante: {radicado}

Tiempo estimado:
{estimated}

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
<p><strong>Producto:</strong> {product}</p>
<p><strong>Destino:</strong> {destination}</p>
<p><strong>Canal usado:</strong> {channel}</p>
<p><strong>Evidencia disponible:</strong> {proof_type}</p>
<p><strong>Radicado o comprobante:</strong> {radicado}</p>
<p><strong>Tiempo estimado:</strong><br>{estimated}</p>
<p><strong>Siguiente paso sugerido:</strong><br>{next_step}</p>
<p><strong>Continuidad posible:</strong><br>{continuity_text}</p>
<p><strong>Panel del cliente:</strong><br><a href="{settings.frontend_url}">{settings.frontend_url}</a></p>
""".strip()
    return {"subject": subject, "text": text_body, "html": html_body}


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
        }

    return {
        **base_result,
        "status": "sent",
        "subject": content["subject"],
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
