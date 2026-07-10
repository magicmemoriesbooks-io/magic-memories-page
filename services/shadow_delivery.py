"""
Shadow Delivery Module — Fase 0 de la unificacion transaccional de emails.

ESTADO: SOLO SOMBRA (shadow mode). Este modulo:
  - NO envia ningun email.
  - NO bloquea ningun email actual.
  - NO sustituye ninguna decision del flujo real.
  - Se ejecuta EN PARALELO al flujo activo, solo para comparar y registrar
    si el nuevo modelo (OrderEntitlements + DeliveryPlan) habria tomado la
    misma decision que el codigo legacy que ya esta en produccion.

Cualquier excepcion dentro de este modulo debe quedar contenida en el
propio modulo (o en el call site que lo invoque con try/except) y jamas
debe interrumpir el envio real de un email transaccional.

Identidad:
  - `order_id` es la identidad transaccional principal para pedidos pagados
    (hoy tomado de `paypal_order_id` cuando existe en story_data).
  - `preview_id` se mantiene como trazabilidad y se usa como identificador
    alternativo unicamente cuando no existe `order_id` documentado.
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
    want_ebook: bool
    want_print: bool
    ebook_is_gift: bool
    cp_submitted: bool

    resolved_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


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

    return OrderEntitlements(
        preview_id=preview_id,
        order_id=order_id,
        identity_source=identity_source,
        customer_email=story_data.get('customer_email', '') or story_data.get('email', ''),
        product_type=story_data.get('product_type', story_data.get('story_id', '')),
        lang=story_data.get('lang', 'es'),
        child_name=story_data.get('child_name', ''),
        paid=bool(story_data.get('paid', False)),
        want_pdf=bool(story_data.get('want_pdf', False)),
        want_ebook=bool(story_data.get('want_ebook', False)),
        want_print=bool(story_data.get('want_print', False)),
        ebook_is_gift=bool(story_data.get('ebook_is_gift', False)),
        cp_submitted=bool(story_data.get('cp_submitted', False)),
    )


def build_delivery_plan(entitlements: OrderEntitlements) -> DeliveryPlan:
    """
    Replica en forma declarativa las reglas que HOY viven dispersas en
    app.py (p.ej. `_include_gift` en `_dispatch_printable_pdf_email`), para
    poder comparar contra la decision real sin haberla tocado.

    Regla replicada (ver app.py:13559, comentario original conservado):
      Se incluye el eBook de regalo solo cuando el cliente NO compro
      separadamente el eBook Y NO compro tambien el libro impreso.
    """
    planned: List[str] = []
    suppressed: List[Dict[str, str]] = []
    notes: List[str] = []

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

        include_gift = (not entitlements.want_ebook) and (not entitlements.want_print)
        if include_gift:
            planned.append('gift_ebook')
        else:
            reason = 'ebook_already_purchased_separately' if entitlements.want_ebook else 'print_confirmation_owns_gift_ebook'
            suppressed.append({'email_type': 'gift_ebook', 'reason': reason})

    if entitlements.want_ebook:
        planned.append('ebook_delivery')

    if entitlements.want_print:
        if entitlements.cp_submitted:
            planned.append('print_confirmation')
        else:
            notes.append('print_wanted_but_not_yet_submitted_to_cloudprinter')

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
    'dispatch_printable_pdf_email') para poder filtrar el log por origen
    mientras se agregan mas puntos de integracion en fases futuras.
    """
    try:
        actual_emails = set(actual_decision.get('planned_emails', []))
        plan_emails = set(plan.planned_emails)
        match = actual_emails == plan_emails

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
                  f"actual={sorted(actual_emails)} shadow={sorted(plan_emails)}")

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
