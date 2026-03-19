from __future__ import annotations

import argparse
import json
from typing import Any

from backend.notifications import send_post_radicado_email, send_signed_submission_email


def _build_demo_case(recipient: str) -> dict[str, Any]:
    return {
        "recommended_action": "Accion de tutela en salud",
        "usuario_email": recipient,
        "usuario_nombre": "Maria Prueba",
        "routing": {
            "primary_target": {
                "name": "Juzgado de reparto de prueba",
            }
        },
    }


def _build_demo_guidance() -> dict[str, Any]:
    return {
        "channel": "email",
        "proof_type": "acuse de envio",
        "estimated_response_window": "Prueba tecnica sin termino procesal real.",
        "next_step_suggestion": "Validar remitente, reply-to, cuerpo y ubicacion del correo.",
        "continuity_offers": ["seguimiento del caso"],
        "post_radicado_copy": {
            "headline": "Prueba real de correo de 123tutela",
            "body": (
                "Este es un correo de validacion tecnica del flujo de salud. "
                "Si lo estas leyendo con contenido visible, el canal SMTP base esta funcionando."
            ),
        },
        "routing_snapshot": {
            "radicado": "TEST-RAD-EMAIL-001",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke test real de correo para 123tutela.")
    parser.add_argument("--recipient", required=True, help="Correo destino para la prueba.")
    args = parser.parse_args()

    case = _build_demo_case(args.recipient)
    guidance = _build_demo_guidance()

    post_result = send_post_radicado_email(recipient=args.recipient, case=case, guidance=guidance)
    signed_result = send_signed_submission_email(
        recipient=args.recipient,
        subject="Prueba de radicacion por correo | 123tutela",
        body_text=(
            "Esta es una prueba tecnica de radicacion por correo.\n\n"
            "Debe salir desde radicaciones@123tutelaapp.com y mostrar contenido visible.\n"
            "Si respondes este correo, la respuesta debe regresar al buzon de radicaciones."
        ),
        body_html=(
            "<h2>Prueba tecnica de radicacion por correo</h2>"
            "<p>Debe salir desde <strong>radicaciones@123tutelaapp.com</strong> y mostrar contenido visible.</p>"
            "<p>Si respondes este correo, la respuesta debe regresar al buzon de radicaciones.</p>"
        ),
        attachments=[],
    )

    print(
        json.dumps(
            {
                "post_radicado_email": post_result,
                "signed_submission_email": signed_result,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
