from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

FILING_PRICE_COP = 36_000
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
        code="carta_formal",
        name="Carta formal a entidad",
        price_cop=32_900,
        short_description="Documento formal para pedir, exigir o dejar constancia ante una entidad o empresa.",
        detailed_description="Redaccion completa del documento con hechos, peticiones y estructura clara para presentarlo ante la entidad correspondiente.",
        next_step_hint="Si no responden o incumplen, puede continuar con queja formal, reclamo o derecho de peticion.",
    ),
    Product(
        code="queja_formal",
        name="Queja formal",
        price_cop=36_900,
        short_description="Queja escrita por mala atencion, incumplimiento o irregularidad ante una entidad o autoridad de control.",
        detailed_description="Documento formal para dejar trazabilidad de la inconformidad y solicitar intervencion o respuesta institucional.",
        next_step_hint="Si la respuesta es insuficiente, puede seguir con derecho de peticion o tutela segun el caso.",
    ),
    Product(
        code="reclamo_administrativo",
        name="Reclamo administrativo",
        price_cop=36_900,
        short_description="Reclamo escrito para exigir correccion, respuesta o solucion frente a una actuacion o servicio.",
        detailed_description="Documento administrativo completo para sustentar el reclamo con hechos, pretensiones y soporte juridico basico.",
        next_step_hint="Segun la respuesta, puede continuar con recurso, queja formal o tutela.",
    ),
    Product(
        code="derecho_peticion",
        name="Derecho de peticion",
        price_cop=41_900,
        short_description="Solicitud formal para pedir respuesta, informacion, copias o una actuacion concreta.",
        detailed_description="Documento juridico estructurado para exigir una respuesta oficial dentro de los terminos legales aplicables.",
        next_step_hint="Si no responden o vulneran derechos fundamentales, el siguiente paso frecuente es una tutela.",
    ),
    Product(
        code="habeas_data",
        name="Habeas data",
        price_cop=41_900,
        short_description="Solicitud para corregir, actualizar o eliminar informacion personal en bases de datos o centrales de riesgo.",
        detailed_description="Documento especializado en proteccion de datos personales para exigir correccion, actualizacion o supresion.",
        next_step_hint="Si persiste la vulneracion, puede seguir con queja ante la SIC o tutela.",
    ),
    Product(
        code="recurso_reposicion_apelacion",
        name="Recurso de reposicion o apelacion",
        price_cop=49_900,
        short_description="Recurso para pedir que una decision sea revisada, corregida o revocada.",
        detailed_description="Documento recursivo completo para controvertir una decision administrativa o institucional ante la misma autoridad o su superior.",
        next_step_hint="Si la respuesta sigue siendo desfavorable, puede continuar con tutela o accion de cumplimiento segun el caso.",
    ),
    Product(
        code="queja_disciplinaria",
        name="Queja disciplinaria",
        price_cop=49_900,
        short_description="Escrito para denunciar conductas irregulares de funcionarios o servidores publicos.",
        detailed_description="Documento completo para exponer hechos, soportes y solicitud de investigacion ante la autoridad disciplinaria competente.",
        next_step_hint="Normalmente continua con seguimiento del tramite disciplinario.",
    ),
    Product(
        code="accion_cumplimiento",
        name="Accion de cumplimiento",
        price_cop=67_900,
        short_description="Demanda para exigir que una autoridad cumpla una ley o un acto administrativo obligatorio.",
        detailed_description="Documento tecnico para reclamar judicialmente el cumplimiento de una obligacion normativa o administrativa clara.",
        next_step_hint="Luego debe hacerse seguimiento del proceso y de la orden judicial correspondiente.",
    ),
    Product(
        code="accion_tutela",
        name="Accion de tutela",
        price_cop=76_900,
        short_description="Documento para proteger derechos fundamentales cuando existe amenaza o vulneracion urgente.",
        detailed_description="Tutela completa con hechos, fundamentos constitucionales, jurisprudencia y pretensiones listas para presentar.",
        next_step_hint="Los pasos posteriores mas comunes son impugnacion o incidente de desacato.",
    ),
    Product(
        code="impugnacion_tutela",
        name="Impugnacion de tutela",
        price_cop=76_900,
        short_description="Recurso para controvertir una decision de tutela cuando fue negada o limitada.",
        detailed_description="Documento completo para solicitar revision de la decision de tutela con base en errores, omisiones o valoracion juridica insuficiente.",
        next_step_hint="Luego corresponde hacer seguimiento a la decision de segunda instancia.",
    ),
    Product(
        code="incidente_desacato",
        name="Incidente de desacato",
        price_cop=84_900,
        short_description="Documento para denunciar incumplimiento de un fallo de tutela.",
        detailed_description="Escrito para pedir al juez medidas frente al incumplimiento de una orden judicial ya emitida en tutela.",
        next_step_hint="Despues se hace seguimiento al cumplimiento del fallo y a las ordenes del juez.",
    ),
    Product(
        code="accion_popular",
        name="Accion popular",
        price_cop=84_900,
        short_description="Accion para proteger derechos e intereses colectivos cuando hay afectacion general.",
        detailed_description="Documento juridico para proteger intereses colectivos y reclamar intervencion judicial cuando la afectacion trasciende a una sola persona.",
        next_step_hint="Luego se hace seguimiento al proceso y a las actuaciones posteriores.",
    ),
)

PRODUCT_MAP = {product.code: product for product in PRODUCTS}

RECOMMENDED_ACTION_TO_PRODUCT = {
    "accion de tutela": "accion_tutela",
    "derecho de peticion": "derecho_peticion",
    "incidente de desacato": "incidente_desacato",
    "impugnacion de tutela": "impugnacion_tutela",
    "accion popular": "accion_popular",
    "accion de cumplimiento": "accion_cumplimiento",
    "habeas data": "habeas_data",
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
