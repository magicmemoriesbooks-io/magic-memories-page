"""
Pruebas standalone (sin pytest) del modulo services/shadow_delivery.py.
Ejecutar con: python3 tests/test_shadow_delivery.py

Cubren unicamente el modulo shadow (Fase 0). No tocan email_service.py,
no envian correos, no acceden a story_previews/ reales.
"""
import os
import sys
import json
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.shadow_delivery import (
    resolve_order_entitlements,
    build_delivery_plan,
    record_shadow_comparison,
    run_shadow_comparison_safe,
    SHADOW_LOG_PATH,
)

PASSED = 0
FAILED = 0


def check(label, condition):
    global PASSED, FAILED
    if condition:
        PASSED += 1
        print(f"  OK  {label}")
    else:
        FAILED += 1
        print(f"  FAIL {label}")


def test_resolve_entitlements_with_order_id():
    story_data = {
        'paypal_order_id': 'PAYPAL123',
        'customer_email': 'cliente@example.com',
        'product_type': 'personalized_pdf',
        'lang': 'es',
        'child_name': 'Sofia',
        'paid': True,
        'want_pdf': True,
        'want_ebook': False,
        'want_print': False,
        'ebook_is_gift': False,
        'admin_gift': False,
        'cp_submitted': False,
    }
    ent = resolve_order_entitlements(story_data, preview_id='preview_abc')
    check('order_id resuelto desde paypal_order_id', ent.order_id == 'PAYPAL123')
    check('identity_source == order_id', ent.identity_source == 'order_id')
    check('preview_id preservado', ent.preview_id == 'preview_abc')
    check('want_pdf True', ent.want_pdf is True)
    check('ebook_permanent_purchased False (want_ebook False)', ent.ebook_permanent_purchased is False)
    check('admin_gift_book False', ent.admin_gift_book is False)


def test_ebook_semantics_admin_gift_vs_temp_gift_are_distinct():
    # Caso 1: regalo administrativo total del libro (admin_gift=True) -> NUNCA
    # debe confundirse con la elegibilidad calculada de eBook temporal.
    story_admin_gift = {
        'paypal_order_id': 'PPADM', 'paid': True,
        'want_pdf': True, 'want_ebook': False, 'want_print': False,
        'admin_gift': True, 'ebook_is_gift': True,
    }
    ent_admin = resolve_order_entitlements(story_admin_gift, 'p_admin')
    plan_admin = build_delivery_plan(ent_admin)
    check('admin_gift_book True se detecta', ent_admin.admin_gift_book is True)
    check('admin_gift_book suprime TODOS los emails', plan_admin.planned_emails == [])
    check('admin_gift no depende del eBook temporal', ent_admin.temp_gift_ebook_eligible is False)

    # Caso 2: compra normal (PDF, sin eBook permanente, sin admin_gift) ->
    # SI debe ser elegible al eBook temporal de 6 meses.
    story_normal = {
        'paypal_order_id': 'PPNORM', 'paid': True,
        'want_pdf': True, 'want_ebook': False, 'want_print': False,
        'admin_gift': False, 'ebook_is_gift': False,
    }
    ent_normal = resolve_order_entitlements(story_normal, 'p_normal')
    check('elegible a gift temporal cuando compro solo PDF', ent_normal.temp_gift_ebook_eligible is True)
    check('fuente de elegibilidad == pdf', ent_normal.temp_gift_ebook_source == 'pdf')

    # Caso 3: compro el eBook permanente -> NUNCA elegible al temporal,
    # sin importar el valor crudo (posiblemente ambiguo) de ebook_is_gift.
    story_permanent = {
        'paypal_order_id': 'PPPERM', 'paid': True,
        'want_pdf': True, 'want_ebook': True, 'want_print': False,
        'admin_gift': False, 'ebook_is_gift': False,
    }
    ent_permanent = resolve_order_entitlements(story_permanent, 'p_perm')
    check('eBook permanente comprado se detecta', ent_permanent.ebook_permanent_purchased is True)
    check('NO elegible a gift temporal si ya compro el permanente', ent_permanent.temp_gift_ebook_eligible is False)


def test_resolve_entitlements_fallback_to_preview_id():
    story_data = {'paid': True, 'want_pdf': True}
    ent = resolve_order_entitlements(story_data, preview_id='preview_xyz')
    check('sin order_id -> None', ent.order_id is None)
    check('identity_source == preview_id_fallback', ent.identity_source == 'preview_id_fallback')


def test_plan_pdf_only_includes_gift():
    story_data = {
        'paypal_order_id': 'PP1', 'paid': True,
        'want_pdf': True, 'want_ebook': False, 'want_print': False,
    }
    ent = resolve_order_entitlements(story_data, 'p1')
    plan = build_delivery_plan(ent)
    check('pdf_ready planificado', 'pdf_ready' in plan.planned_emails)
    check('gift_ebook incluido (no compro ebook ni print)', 'gift_ebook_temp_6mo' in plan.planned_emails)
    check('sin supresiones', plan.suppressed_emails == [])


def test_plan_pdf_plus_ebook_suppresses_gift():
    story_data = {
        'paypal_order_id': 'PP2', 'paid': True,
        'want_pdf': True, 'want_ebook': True, 'want_print': False,
    }
    ent = resolve_order_entitlements(story_data, 'p2')
    plan = build_delivery_plan(ent)
    check('pdf_ready planificado', 'pdf_ready' in plan.planned_emails)
    check('gift_ebook NO incluido (ya compro ebook)', 'gift_ebook_temp_6mo' not in plan.planned_emails)
    check('ebook_permanent_delivery planificado', 'ebook_permanent_delivery' in plan.planned_emails)
    reasons = [s['reason'] for s in plan.suppressed_emails]
    check('razon de supresion correcta', 'ebook_permanent_already_purchased' in reasons)


def test_plan_pdf_plus_print_suppresses_gift():
    story_data = {
        'paypal_order_id': 'PP3', 'paid': True,
        'want_pdf': True, 'want_ebook': False, 'want_print': True, 'cp_submitted': True,
    }
    ent = resolve_order_entitlements(story_data, 'p3')
    plan = build_delivery_plan(ent)
    check('gift_ebook_temp_6mo SI incluido (no compro ebook permanente, elegible via print)', 'gift_ebook_temp_6mo' in plan.planned_emails)
    check('fuente de elegibilidad == pdf_and_print', ent.temp_gift_ebook_source == 'pdf_and_print')
    check('print_confirmation planificado (cp_submitted=True)', 'print_confirmation' in plan.planned_emails)


def test_plan_unpaid_order_produces_empty_plan():
    story_data = {'paid': False, 'want_pdf': True}
    ent = resolve_order_entitlements(story_data, 'p4')
    plan = build_delivery_plan(ent)
    check('plan vacio si no esta pagado', plan.planned_emails == [])
    check('nota de no-pagado presente', 'order_not_paid_no_plan_generated' in plan.notes)


def test_shadow_log_match_and_mismatch(tmp_log_path):
    import services.shadow_delivery as sd
    original_path = sd.SHADOW_LOG_PATH
    sd.SHADOW_LOG_PATH = tmp_log_path
    try:
        story_data = {
            'paypal_order_id': 'PP5', 'paid': True,
            'want_pdf': True, 'want_ebook': False, 'want_print': False,
        }
        ent = resolve_order_entitlements(story_data, 'p5')
        plan = build_delivery_plan(ent)

        # Caso 1: actual coincide con el plan (match=True esperado)
        record_shadow_comparison(
            'unit_test_stage', ent, plan,
            actual_decision={'planned_emails': ['pdf_ready', 'gift_ebook']},
        )
        # Caso 2: actual difiere del plan (match=False esperado)
        record_shadow_comparison(
            'unit_test_stage', ent, plan,
            actual_decision={'planned_emails': ['pdf_ready']},
        )

        with open(tmp_log_path, 'r', encoding='utf-8') as f:
            lines = [json.loads(l) for l in f.readlines()]

        check('se escribieron 2 lineas en el log shadow', len(lines) == 2)
        check('primera entrada: match=True', lines[0]['match'] is True)
        check('segunda entrada: match=False', lines[1]['match'] is False)
        check('log incluye order_id', lines[0]['order_id'] == 'PP5')
        check('log incluye preview_id', lines[0]['preview_id'] == 'p5')
    finally:
        sd.SHADOW_LOG_PATH = original_path


def test_run_shadow_comparison_safe_never_raises():
    # story_data intencionalmente incompleto/invalido para forzar rutas de error
    try:
        run_shadow_comparison_safe(
            stage='unit_test_defensive',
            story_data=None,  # tipo invalido a proposito
            preview_id='p6',
            actual_decision={'planned_emails': []},
        )
        check('run_shadow_comparison_safe no lanza excepcion con story_data invalido', True)
    except Exception:
        check('run_shadow_comparison_safe no lanza excepcion con story_data invalido', False)


if __name__ == '__main__':
    print('test_resolve_entitlements_with_order_id')
    test_resolve_entitlements_with_order_id()
    print('test_resolve_entitlements_fallback_to_preview_id')
    test_resolve_entitlements_fallback_to_preview_id()
    print('test_plan_pdf_only_includes_gift')
    test_plan_pdf_only_includes_gift()
    print('test_plan_pdf_plus_ebook_suppresses_gift')
    test_plan_pdf_plus_ebook_suppresses_gift()
    print('test_plan_pdf_plus_print_suppresses_gift')
    test_plan_pdf_plus_print_suppresses_gift()
    print('test_plan_unpaid_order_produces_empty_plan')
    test_plan_unpaid_order_produces_empty_plan()

    print('test_shadow_log_match_and_mismatch')
    with tempfile.TemporaryDirectory() as d:
        tmp_path = os.path.join(d, 'shadow_test_log.jsonl')
        test_shadow_log_match_and_mismatch(tmp_path)

    print('test_run_shadow_comparison_safe_never_raises')
    test_run_shadow_comparison_safe_never_raises()

    print(f"\n{PASSED} passed, {FAILED} failed")
    sys.exit(1 if FAILED else 0)
