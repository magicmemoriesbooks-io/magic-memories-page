---
name: OrderEntitlements semantics (admin gift vs temp gift eBook)
description: How the unified email/delivery shadow-mode layer disambiguates the legacy ebook_is_gift flag, and why full cutover was paused.
---

The legacy `story_data['ebook_is_gift']` field was overloaded for two unrelated concepts across different call sites: a whole-book admin giveaway (skips all emails/print) vs. a computed temporary 6-month eBook entitlement (customer bought PDF and/or print but not the permanent eBook). Different files spelled the second concept differently (`_include_gift`, `give_gift_ebook`, `_visor_is_gift_cs`), making it hard to verify they implemented the same rule.

**Why:** conflating the two caused real bugs (double-send races, wrong suppression logic) because "is this a gift" answered two different questions depending on which code path read it.

**How to apply:** any new code resolving eBook entitlements should compute admin-gift and temp-gift-eligibility as separate, explicitly named fields (never derive one from the legacy flag), and treat the legacy flag as diagnostic-only during any coexistence/shadow period.

**Cutover dependency pattern:** when a shadow-mode validation's own approval criterion requires real production traffic (e.g. "shadow plan matches real recent orders"), and the environment forbids sending real emails or using real test data, that is a legitimate hard stop — do not fabricate traffic to force validation. Ship the shadow instrumentation complete and correct, document the dependency explicitly, and defer the cutover phase until real data exists outside the sandbox.
