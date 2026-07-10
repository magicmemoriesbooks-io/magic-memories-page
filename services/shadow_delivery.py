"""
Shadow Delivery Module — unificacion transaccional de emails (modo sombra).

ESTADO: SOLO SOMBRA (shadow mode). Este modulo:
  - NO envia ningun email.
  - NO bloquea ningun email actual.
  - NO sustituye ninguna decision del flujo real todavia.
  - Se ejecuta EN PARALELO a los flujos activos, solo para comparar y
    registrar si el nuevo modelo (OrderEntitlements + DeliveryPlan) habria
    tomado la misma decision que el codigo legacy que sigue en produccion.

Cualquier excepcion dentro de este modulo debe quedar contenida en el
propio modulo (o en el call site que lo invoque con try/except) y jamas
debe interrumpir el envio real de un email transaccional.

Identidad:
  - `order_id` es la identidad transaccional principal para pedidos pagados
    (hoy tomado de `paypal_order_id` cuando existe en story_data).
  - `preview_id` se mantiene como trazabilidad y se usa como identificador
    alternativo unicamente cuando no existe `order_id` documentado.

--------------------------------------------------------------------------
SEMANTICA DE "eBook" (aclaracion explicita, ver docs/unified_email_delivery_architecture.md
seccion "Semantica de eBook permanente vs eBook temporal de regalo")
--------------------------------------------------------------------------
El codigo legacy usa el MISMO nombre de campo (`ebook_is_gift`) para DOS
conceptos distintos que NO deben confundirse:

  1. `admin_gift_book` (antes escrito en algunos puntos como
     `story_data['ebook_is_gift'] = True` cuando `admin_gift` es True,
     ver app.py ~linea 12942): un libro COMPLETO regalado manualmente por
     un administrador. No tiene relacion con lo que el cliente compro.

  2. Elegibilidad calculada de "eBook temporal de 6 meses" (en el codigo
     legacy aparece como variables ad-hoc distintas segun el archivo:
     `_include_gift` en `_dispatch_printable_pdf_email`, `give_gift_ebook`
     en la composicion de libros personalizados, `_visor_is_gift_cs` en
     `confirm_and_send` para Quick Stories): el cliente NO compro el eBook
     permanente, pero SI compro PDF y/o impreso, y por eso recibe acceso
     temporal (6 meses) al visor como cortesia. Esta elegibilidad se anula
     si el cliente SI compro el eBook permanente.

Esta arquitectura los separa con nombres inequivocos en `OrderEntitlements`:
  - `ebook_permanent_purchased`: el cliente compro el eBook permanente
    (`want_ebook` en el legacy).
  - `admin_gift_book`: bandera administrativa de regalo total del libro,
    independiente de lo que el cliente pago (`admin_gift` en el legacy).
  - `temp_gift_ebook_eligible` (calculado, NO almacenado): True solo si
    el pedido esta pagado, NO es un regalo administrativo, y el cliente
    NO compro el eBook permanente pero SI compro PDF y/o impreso.
  - `temp_gift_ebook_source`: de donde viene esa elegibilidad —
    'pdf' | 'print' | 'pdf_and_print' | 'none'.

El campo legacy `ebook_is_gift` se sigue LEYENDO solo con fines de
comparacion/diagnostico (`legacy_admin_gift_flag_raw`), nunca se usa como
fuente de la decision nueva.
"""

from __future__ import annotations

import json
import os
import threading
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional, List, Dict, Any

SHADOW_LOG_PATH = os.path.join('data', 'shadow_delivery_log.jsonl')
_shadow_log_lock = threading.Lock()


@dataclass
class OrderEntitlements:
    """
    Instantanea de solo-lectura de "que compro y que le corresponde",
    derivada de un story_data (story_previews/{preview_id}.json) ya cargado
    en memoria por el flujo real. No realiza I/O propio: recibe el dict que
    el flujo real ya leyo, para no duplicar lecturas de disco ni introducir
    condiciones de carrera nuevas.
    """
    preview_id: str
    order_id: Optional[str]
    identity_source: str  # 'order_id' | 'preview_id_fallback'
    customer_email: str
    product_type: str
    lang: str
    child_name: str

    paid: bool
    want_pdf: bool
    want_print: bool
    cp_submitted: bool

    ebook_permanent_purchased: bool     # antes: want_ebook
    admin_gift_book: bool               # antes: admin_gift / uso ambiguo de ebook_is_gift
    legacy_admin_gift_flag_raw: bool    # solo diagnostico, valor crudo de story_data['ebook_is_gift']

    is_quick_story: bool = False

    resolved_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    @property
    def temp_gift_ebook_source(self) -> str:
        if self.ebook_permanent_purchased or self.admin_gift_book or not self.paid:
            return 'none'
        if self.want_pdf and self.want_print:
            return 'pdf_and_print'
        if self.want_pdf:
            return 'pdf'
        if self.want_print:
            return 'print'
        return 'none'

    @property
    def temp_gift_ebook_eligible(self) -> bool:
        return self.temp_gift_ebook_source != 'none'

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d['temp_gift_ebook_eligible'] = self.temp_gift_ebook_eligible
        d['temp_gift_ebook_source'] = self.temp_gift_ebook_source
        return d


@dataclass
class DeliveryPlan:
    """
    Plan de entregas derivado exclusivamente de OrderEntitlements, sin
    ningun acceso a estado externo (JSON de logs, scheduler, etc.).
    """
    preview_id: str
    order_id: Optional[str]
    planned_emails: List[str]
    suppressed_emails: List[Dict[str, str]]  # [{"email_type": ..., "reason": ...}]
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def resolve_order_entitlements(story_data: Dict[str, Any], preview_id: str) -> OrderEntitlements:
    """
    Traduce un story_data ya cargado a OrderEntitlements. Pura funcion de
    mapeo — no abre archivos, no llama a servicios externos, no muta
    story_data.
    """
    order_id = story_data.get('paypal_order_id') or story_data.get('order_id') or None
    identity_source = 'order_id' if order_id else 'preview_id_fallback'

    is_quick_story = False
    try:
        from services.quick_stories.checkout import is_quick_story as _check_qs
        is_quick_story = bool(_check_qs(story_data.get('story_id', '')))
    except Exception:
        # No es critico para el calculo de entitlements; si el checker no
        # esta disponible en este contexto, se deja en False y se registra
        # como nota en el plan (ver build_delivery_plan).
        pass

    want_pdf = (
        story_data.get('product_type') == 'personalized_pdf'
        or bool(story_data.get('pdf_order'))
        or bool(story_data.get('want_pdf', False))
        or bool(story_data.get('pdf_paid', False))
    )

    return OrderEntitlements(
        preview_id=preview_id,
        order_id=order_id,
        identity_source=identity_source,
        customer_email=story_data.get('customer_email', '') or story_data.get('email', ''),
        product_type=story_data.get('product_type', story_data.get('story_id', '')),
        lang=story_data.get('lang', 'es'),
        child_name=story_data.get('child_name', ''),
        paid=bool(story_data.get('paid', False)),
        want_pdf=want_pdf,
        want_print=bool(story_data.get('want_print', False)),
        cp_submitted=bool(story_data.get('cp_submitted', False)),
        ebook_permanent_purchased=bool(story_data.get('want_ebook', False)),
        admin_gift_book=bool(story_data.get('admin_gift', False)),
        legacy_admin_gift_flag_raw=bool(story_data.get('ebook_is_gift', False)),
        is_quick_story=is_quick_story,
    )


def build_delivery_plan(entitlements: OrderEntitlements) -> DeliveryPlan:
    """
    Replica en forma declarativa las reglas que HOY viven dispersas en
    app.py bajo nombres distintos segun el archivo (`_include_gift` en
    `_dispatch_printable_pdf_email`, `give_gift_ebook` en la composicion de
    libros personalizados, `_visor_is_gift_cs` en `confirm_and_send`), para
    poder comparar contra la decision real sin haberlas tocado todavia.

    IMPORTANTE: esta funcion NO lee `_include_gift` ni ninguna variable
    legacy — calcula el resultado exclusivamente desde OrderEntitlements,
    tal como exige la arquitectura final (ver seccion "eBook temporal" del
    documento de arquitectura). El call site es responsable de comparar
    este resultado contra la variable legacy correspondiente, no al reves.
    """
    planned: List[str] = []
    suppressed: List[Dict[str, str]] = []
    notes: List[str] = []

    if entitlements.admin_gift_book:
        notes.append('admin_gift_book_skips_customer_email_and_print_by_design')
        return DeliveryPlan(
            preview_id=entitlements.preview_id,
            order_id=entitlements.order_id,
            planned_emails=[],
            suppressed_emails=[{'email_type': 'ALL', 'reason': 'admin_gift_book'}],
            notes=notes,
        )

    if not entitlements.paid:
        notes.append('order_not_paid_no_plan_generated')
        return DeliveryPlan(
            preview_id=entitlements.preview_id,
            order_id=entitlements.order_id,
            planned_emails=[],
            suppressed_emails=[{'email_type': 'ALL', 'reason': 'not_paid'}],
            notes=notes,
        )

    if entitlements.want_pdf:
        planned.append('pdf_ready')

    if entitlements.ebook_permanent_purchased:
        planned.append('ebook_permanent_delivery')

    if entitlements.temp_gift_ebook_eligible:
        planned.append('gift_ebook_temp_6mo')
    elif entitlements.ebook_permanent_purchased:
        suppressed.append({'email_type': 'gift_ebook_temp_6mo', 'reason': 'ebook_permanent_already_purchased'})

    if entitlements.want_print:
        if entitlements.cp_submitted:
            planned.append('print_confirmation')
        else:
            notes.append('print_wanted_but_not_yet_submitted_to_cloudprinter')

    if not entitlements.want_pdf and not entitlements.want_print and not entitlements.ebook_permanent_purchased:
        notes.append('digital_only_no_pdf_case_ebook_temp_gift_is_sole_delivery')

    if entitlements.identity_source == 'preview_id_fallback':
        notes.append('no_order_id_found_using_preview_id_as_identity')

    return DeliveryPlan(
        preview_id=entitlements.preview_id,
        order_id=entitlements.order_id,
        planned_emails=planned,
        suppressed_emails=suppressed,
        notes=notes,
    )


def record_shadow_comparison(
    stage: str,
    entitlements: OrderEntitlements,
    plan: DeliveryPlan,
    actual_decision: Dict[str, Any],
) -> None:
    """
    Escribe una linea JSONL en data/shadow_delivery_log.jsonl comparando la
    decision del flujo legacy (actual_decision, pasada por el call site tal
    cual la calcula el codigo real) contra el plan generado por
    build_delivery_plan(). NUNCA lanza excepciones hacia el llamador: un
    fallo aqui debe quedar contenido y visible solo en el propio log/consola,
    jamas debe interrumpir un envio real.

    `stage` identifica el punto de integracion (p.ej.
    'dispatch_printable_pdf_email', 'confirm_and_send') para poder filtrar
    el log por origen mientras se agregan mas puntos de integracion.
    """
    try:
        actual_emails = set(actual_decision.get('planned_emails', []))
        plan_emails = set(plan.planned_emails)
        # Comparacion semantica: 'gift_ebook' (nombre usado por el hook mas
        # antiguo, antes de esta aclaracion de nombres) se homologa a
        # 'gift_ebook_temp_6mo' unicamente para esta comparacion, para no
        # generar falsos MISMATCH mientras coexisten call sites con nombres
        # de transicion.
        _alias = {'gift_ebook': 'gift_ebook_temp_6mo'}
        actual_emails_normalized = {_alias.get(e, e) for e in actual_emails}
        match = actual_emails_normalized == plan_emails

        entry = {
            'ts': datetime.utcnow().isoformat(),
            'stage': stage,
            'preview_id': entitlements.preview_id,
            'order_id': entitlements.order_id,
            'identity_source': entitlements.identity_source,
            'match': match,
            'actual_decision': actual_decision,
            'shadow_plan': plan.to_dict(),
            'entitlements': entitlements.to_dict(),
        }

        os.makedirs(os.path.dirname(SHADOW_LOG_PATH), exist_ok=True)
        with _shadow_log_lock:
            with open(SHADOW_LOG_PATH, 'a', encoding='utf-8') as f:
                f.write(json.dumps(entry, ensure_ascii=False) + '\n')

        if not match:
            print(f"[SHADOW-DELIVERY] MISMATCH at stage={stage} preview_id={entitlements.preview_id}: "
                  f"actual={sorted(actual_emails_normalized)} shadow={sorted(plan_emails)}")

    except Exception as _shadow_err:  # pragma: no cover - defensive, must never bubble up
        try:
            print(f"[SHADOW-DELIVERY] WARNING: shadow comparison failed non-fatally: {_shadow_err}")
        except Exception:
            pass


def run_shadow_comparison_safe(
    stage: str,
    story_data: Dict[str, Any],
    preview_id: str,
    actual_decision: Dict[str, Any],
) -> None:
    """
    Punto de entrada unico y "a prueba de fallos" para que el codigo real
    invoque el modulo shadow con una sola linea, envuelta en su propio
    try/except interno, de modo que el call site en app.py no necesite
    duplicar manejo de errores.
    """
    try:
        entitlements = resolve_order_entitlements(story_data, preview_id)
        plan = build_delivery_plan(entitlements)
        record_shadow_comparison(stage, entitlements, plan, actual_decision)
    except Exception as _err:  # pragma: no cover - defensive, must never bubble up
        try:
            print(f"[SHADOW-DELIVERY] WARNING: shadow resolution failed non-fatally at stage={stage}: {_err}")
        except Exception:
            pass
