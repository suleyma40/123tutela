from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

FILING_PRICE_COP = 34_000
CURRENCY = "COP"


@dataclass(frozen=True, slots=True)
class Product:
    code: str
    name: str
    price_cop: int
    short_description: str
    detailed_description: str
    next_step_hint: str

    @property
    def price_with_filing_cop(self) -> int:
        return self.price_cop + FILING_PRICE_COP

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["price_with_filing_cop"] = self.price_with_filing_cop
        payload["currency"] = CURRENCY
        payload["supports_filing"] = True
        return payload


PRODUCTS: tuple[Product, ...] = (
    Product(
        code="pago_prueba",
        name="Pago de prueba",
        price_cop=10_000,
        short_description="Producto temporal para validar el flujo de pago en producción.",
        detailed_description="Producto temporal de prueba para verificar checkout, webhook, cambio de estado del expediente y generación posterior del documento.",
        next_step_hint="Una vez validado el pago, se elimina este producto del catálogo.",
    ),
    Product(
        code="carta_formal",
        name="Carta formal a entidad",
        price_cop=29_900,
        short_description="Documento formal para pedir, exigir o dejar constancia ante una entidad o empresa.",
        detailed_description="Redaccion completa del documento con hechos, peticiones y estructura clara para presentarlo ante la entidad correspondiente.",
        next_step_hint="Si no responden o incumplen, puede continuar con queja formal, reclamo o derecho de petición.",
    ),
    Product(
        code="queja_formal",
        name="Queja formal",
        price_cop=33_900,
        short_description="Queja escrita por mala atención, incumplimiento o irregularidad ante una entidad o autoridad de control.",
        detailed_description="Documento formal para dejar trazabilidad de la inconformidad y solicitar intervención o respuesta institucional.",
        next_step_hint="Si la respuesta es insuficiente, puede seguir con derecho de petición o tutela según el caso.",
    ),
    Product(
        code="reclamo_administrativo",
        name="Reclamo administrativo",
        price_cop=33_900,
        short_description="Reclamo escrito para exigir corrección, respuesta o solución frente a una actuación o servicio.",
        detailed_description="Documento administrativo completo para sustentar el reclamo con hechos, pretensiones y soporte jurídico básico.",
        next_step_hint="Según la respuesta, puede continuar con recurso, queja formal o tutela.",
    ),
    Product(
        code="derecho_peticion",
        name="Derecho de petición",
        price_cop=38_900,
        short_description="Solicitud formal para pedir respuesta, información, copias o una actuación concreta.",
        detailed_description="Documento jurídico estructurado para exigir una respuesta oficial dentro de los términos legales aplicables.",
        next_step_hint="Si no responden o vulneran derechos fundamentales, el siguiente paso frecuente es una tutela.",
    ),
    Product(
        code="habeas_data",
        name="Habeas data",
        price_cop=38_900,
        short_description="Solicitud para corregir, actualizar o eliminar información personal en bases de datos o centrales de riesgo.",
        detailed_description="Documento especializado en protección de datos personales para exigir corrección, actualización o supresión.",
        next_step_hint="Si persiste la vulneración, puede seguir con queja ante la SIC o tutela.",
    ),
    Product(
        code="recurso_reposicion_apelacion",
        name="Recurso de reposición o apelación",
        price_cop=46_900,
        short_description="Recurso para pedir que una decisión sea revisada, corregida o revocada.",
        detailed_description="Documento recursivo completo para controvertir una decisión administrativa o institucional ante la misma autoridad o su superior.",
        next_step_hint="Si la respuesta sigue siendo desfavorable, puede continuar con tutela o acción de cumplimiento según el caso.",
    ),
    Product(
        code="queja_disciplinaria",
        name="Queja disciplinaria",
        price_cop=46_900,
        short_description="Escrito para denunciar conductas irregulares de funcionarios o servidores públicos.",
        detailed_description="Documento completo para exponer hechos, soportes y solicitud de investigación ante la autoridad disciplinaria competente.",
        next_step_hint="Normalmente continúa con seguimiento del trámite disciplinario.",
    ),
    Product(
        code="accion_cumplimiento",
        name="Acción de cumplimiento",
        price_cop=63_900,
        short_description="Demanda para exigir que una autoridad cumpla una ley o un acto administrativo obligatorio.",
        detailed_description="Documento técnico para reclamar judicialmente el cumplimiento de una obligación normativa o administrativa clara.",
        next_step_hint="Luego debe hacerse seguimiento del proceso y de la orden judicial correspondiente.",
    ),
    Product(
        code="accion_tutela",
        name="Acción de tutela",
        price_cop=72_900,
        short_description="Documento para proteger derechos fundamentales cuando existe amenaza o vulneración urgente.",
        detailed_description="Tutela completa con hechos, fundamentos constitucionales, jurisprudencia y pretensiones listas para presentar.",
        next_step_hint="Los pasos posteriores más comunes son impugnación o incidente de desacato.",
    ),
    Product(
        code="impugnacion_tutela",
        name="Impugnación de tutela",
        price_cop=72_900,
        short_description="Recurso para controvertir una decisión de tutela cuando fue negada o limitada.",
        detailed_description="Documento completo para solicitar revisión de la decisión de tutela con base en errores, omisiones o valoración jurídica insuficiente.",
        next_step_hint="Luego corresponde hacer seguimiento a la decisión de segunda instancia.",
    ),
    Product(
        code="incidente_desacato",
        name="Incidente de desacato",
        price_cop=79_900,
        short_description="Documento para denunciar incumplimiento de un fallo de tutela.",
        detailed_description="Escrito para pedir al juez medidas frente al incumplimiento de una orden judicial ya emitida en tutela.",
        next_step_hint="Después se hace seguimiento al cumplimiento del fallo y a las órdenes del juez.",
    ),
    Product(
        code="accion_popular",
        name="Acción popular",
        price_cop=79_900,
        short_description="Acción para proteger derechos e intereses colectivos cuando hay afectación general.",
        detailed_description="Documento jurídico para proteger intereses colectivos y reclamar intervención judicial cuando la afectación trasciende a una sola persona.",
        next_step_hint="Luego se hace seguimiento al proceso y a las actuaciones posteriores.",
    ),
)

PRODUCT_MAP = {product.code: product for product in PRODUCTS}

RECOMMENDED_ACTION_TO_PRODUCT = {
    "acción de tutela": "accion_tutela",
    "accion de tutela": "accion_tutela",
    "derecho de petición": "derecho_peticion",
    "derecho de peticion": "derecho_peticion",
    "incidente de desacato": "incidente_desacato",
    "impugnación de tutela": "impugnacion_tutela",
    "impugnacion de tutela": "impugnacion_tutela",
    "acción popular": "accion_popular",
    "accion popular": "accion_popular",
    "acción de cumplimiento": "accion_cumplimiento",
    "accion de cumplimiento": "accion_cumplimiento",
    "habeas data": "habeas_data",
    "recurso de reposición o apelación": "recurso_reposicion_apelacion",
    "recurso de reposicion o apelacion": "recurso_reposicion_apelacion",
    "queja disciplinaria": "queja_disciplinaria",
    "queja formal": "queja_formal",
    "reclamo administrativo": "reclamo_administrativo",
    "carta formal a entidad": "carta_formal",
}


def list_catalog() -> list[dict[str, Any]]:
    return [product.to_dict() for product in PRODUCTS]


def get_product(code: str) -> Product | None:
    return PRODUCT_MAP.get(code)


def suggest_product_code(recommended_action: str | None) -> str | None:
    if not recommended_action:
        return None
    return RECOMMENDED_ACTION_TO_PRODUCT.get(recommended_action.strip().lower())
