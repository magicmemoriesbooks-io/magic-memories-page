# Magic Memories Books

## Overview
Magic Memories Books is a bilingual web application that uses AI to generate personalized children's storybooks with custom text and illustrations. It supports both digital and print formats, aiming to create unique, age-appropriate narratives with dynamic character personalization to foster imagination and create cherished family memories. The project targets a global market with ambitions for high-quality, personalized children's literature.

## User Preferences
- **PDF Testing**: Always offer PDFs WITHOUT Ghostscript sanitization for testing (add `?raw=1` or use skip_sanitize=True). Only apply Ghostscript in production.
- **Language**: Spanish preferred for communication. SIEMPRE documentar procesos en español.
- **Legal Compliance**: Páginas legales separadas: `/terms` (Términos) y `/privacy` (Política de Privacidad). Cumplimiento COPPA/GDPR para fotos de menores. **NO HAY REEMBOLSO** - el usuario revisa y aprueba antes de pagar, y tiene 1 oportunidad de regeneración post-pago. Fotos se eliminan automáticamente en 72h (scheduler cada 6h + cleanup al iniciar). Admin: `/admin/uploaded-photos` para gestionar fotos. Consent checkbox obligatorio antes de subir fotos (client + server-side validation). Upload endpoint requiere `consent=true`.
- **Fixed Pages Documentation**: Ver `docs/fixed_pages/` para especificaciones de páginas fijas (créditos, dedicatoria, contraportadas, estructura PDF, reglas de generación de imágenes, especificaciones Lulu)
- **Flujo Unificado**: El pago (PayPal) y la impresión (Lulu) están separados. Primero pago digital → luego opcionalmente libro impreso via /print-order/<preview_id>.
- **Tu Amor Peludo Documentation**: Ver `docs/templates/tu_amor_peludo.md` para documentación completa del producto furry_love (formulario, prompts, flujo dual-referencia, checklist para replicar).
- **FLUX Dev Prompt Guidelines (CRITICAL - Read Every Session)**: Aplica a TODOS los productos que usen FLUX Dev (Quick Stories, Personalized Books).
  - **Guidance**: SIEMPRE 3.5. NUNCA subir a 7.0 (causa alucinaciones: colas rojas, elementos inventados). Si falta detalle, subir steps a 25-30, NO guidance.
  - **Estructura de prompts OBLIGATORIA** (validada Feb 2026 con baby_puppy_love - éxito total):
    ```
    Disney 3D Pixar-style illustration.
    CHARACTER: A single {gender_word} ({age_display}), {hair_desc}, {eye_desc}, {skin_tone} skin, [rasgos faciales].
    WEARING: [ropa exacta]
    ACTION: [qué hace, pose exacta, interacción con companion]
    ENVIRONMENT: [escenario/fondo] WIDE VIEW, [detalles]
    ATMOSPHERE: [efectos mágicos, iluminación]
    STRICT: [restricciones explícitas - no duplicates, no animal features, etc.]
    ```
  - **{hair_desc} y {eye_desc} SIEMPRE separados** - NUNCA concatenar pelo+ojos. El código detecta automáticamente si el template tiene `{eye_desc}` y ajusta.
  - **Companions con NOMBRE fijo** - POMPOM (perrito), NUBE (conejito), MISU (gatito), LUCERO (luz guardiana). Para consistencia en FLUX.
  - **Poses de bebés**: NO hacer reemplazos automáticos de poses. Los scene_templates ya tienen poses exactas por escena. Solo para edad 0 se añade constraint "CANNOT stand or walk".
  - **Prompts de escena**: Los `scene_template` en fixed_stories.py contienen TODA la info del personaje (pelo, piel, pose, estilo). Pasan directo a FLUX sin modificaciones genéricas.
- **Cover Reuse Fix**: Para furry_love books, la portada pre-generada (cover_raw.png) se reutiliza en `_generate_personalized_book_scenes_background`. Se pasa como single reference a `generate_cover_spread` (sin ref_path_2) para triggear `reuse_preview_as_cover=True`. Fallback chain: story_data.cover_raw_path → disco cover_raw.png → refs originales. `original_cover` se preserva para furry_love books (no se sobreescribe con la portada extraída del spread).
- **FLUX PuLID para preview humano con foto (Tu Amor Peludo)**: PuLID solo para teen/adult (mejor fidelidad de edad). Baby/adventure usan FLUX 2 Dev (mejor fidelidad visual). Routing condicional en AMBOS endpoints: `/api/generate-baby-preview` y `/api/regenerate-furry-preview`. Parámetros PuLID: `main_face_image` (foto), `id_weight: 1.2`, `start_step: 0`, `guidance_scale: 4.0`, `num_steps: 20`. Fallback a FLUX 2 Dev si PuLID falla. Preview de mascota y escenas siguen usando FLUX 2 Dev. Función: `generate_with_flux_pulid()` en `preview.py`.
- **FLUX Negation Rule (CRITICAL)**: FLUX 2 Dev/Pro reads "NO X" / "NEVER X" as presence of X. All prompts use ONLY positive affirmations. Applied Feb 2026 across all 4 furry_love prompt files + illustrated_book_service.py. Examples: "NO text" → "pure illustration only"; "NEVER carried" → "walks on its own four paws"; "NO duplicates" → removed entirely. "MUST" and "EXACTLY" also replaced with simple declarative statements.
- **Adult Form Fields (Tu Amor Peludo)**: For `furry_love_adult_illustrated` without photo, form shows optional fields: facial hair (none/stubble/short_beard/full_beard/mustache), glasses (none/glasses/sunglasses), build (average/slim/athletic/stocky). Hidden when photo uploaded. Fields passed in traits → appended to human_desc in preview.py.
  - **Glasses field**: Available for ALL 4 furry_love stories (baby, kids, teen, adult) — not just adult. Hidden when photo is uploaded. Babies and kids can wear glasses too.
  - **human_desc construction**: The extras (glasses, facial_hair, build) are appended to `human_desc` in ALL routes: `/api/generate-baby-preview`, `/api/regenerate-furry-preview`, AND `/api/generate-fixed-story`. This ensures the description flows through to scene prompts, cover prompts, and all post-payment generation.
  - **Scene prompt placeholders (Adult)**: `{glasses_desc}` and `{facial_hair_desc}` are present in ALL 19 scene prompts + CLOSING_SCENE + FRONT_COVER of `furry_love_adult_prompts.py`. These are short strings (e.g., ", wearing glasses", ", with short beard") or empty string when none. Injected via `build_scene_prompt()` which receives `glasses` and `facial_hair` from `traits` dict in `illustrated_book_service.py`. This ensures glasses/beard appear consistently across all scenes, not just the cover.
- **Ideogram Character**: Usado para escenas de baby stories (baby_soft_world primero).
  - **Flujo**: FLUX 2 Pro genera preview (con descripción completa del personaje) → Ideogram Character usa preview como referencia para escenas (auto-detecta cara/pelo)
  - **Formato de prompts Ideogram**: [Estilo] + [Acción/Pose] + [Entorno] + [Mood]. SIN descripción de personaje (lo toma de la referencia).
  - **Parámetros**: style_type="Fiction", aspect_ratio="1:1", magic_prompt_option="Auto"
  - **Flag**: `use_ideogram_scenes: True` en story config para activar
  - **Costo**: ~$0.04-0.06 por escena. Total por cuento: ~$0.37-0.53

## System Architecture
The application is a Flask-based web application with a modular architecture supporting bilingual content and dynamic user flows. It integrates AI for story and image generation, and third-party services for payments and printing.

**Modular Architecture (Core Products):**
- **Cuentos Mágicos Express / Magic Express Stories**: Digital stories for babies and toddlers.
- **Aventuras a tu Medida / Adventures Made for You**: Illustrated books with Lulu printing and PayPal payments, including "Mi Mejor Amigo Peludo / My Furry Best Friend" with 4 age-range stories.
- **Cuentos de Cumple / Birthday Tales**: Personalized birthday stories.
- **Haz tu Historia (Make Your Story)**: Custom AI stories with PayPal payment. Libro impreso: flujo separado /print-order.

**UI/UX and Technical Implementations:**
- **Homepage Design**: Interactive hero section with flipbook, DALL-E 3 background, and animations. Features sections for "How It Works", "Products", "Gallery marquee", "Social Proof", "Delivery Formats comparison", and a final CTA. Glassmorphism footer with newsletter, social media, and payment icons.
- **AI-driven Content**: GPT-4o for story text, FLUX (FLUX Dev, FLUX 2 Pro, FLUX 2 Dev + reference) and Ideogram Character for image generation.
- **Character Personalization**: Customizable appearance and story elements.
- **Dynamic Story Preview**: Previews of generated text and illustrations.
- **PDF Generation**: Supports various page formats (26-page personalized, 24-page A4 custom, 12-page 8.5"x8.5" quick stories).
- **Print Specifications**: Adheres to Lulu's casewrap hardcover for Personalized Books and saddle stitch for Quick Stories.
- **User Flow**: Consistent flow from story selection, personalization, AI generation, preview, shipping, payment, to order confirmation.
- **Cover Design**: Dynamic and fixed back covers, spine text for hardcover books.
- **Pricing Models**: Digital: eBook $7, PDF $20, Personalizado $30. Libro impreso: flujo separado /print-order con calculadora Lulu real + PayPal (precio base + envío real).
- **Email Service**: Unified email template system (`services/email_service.py`) for customer and admin communications with distinct styling.
- **Background Generation**: Post-payment scene generation runs in a TaskQueue.
- **Background Book Composition (Personalized Books)**: Post-payment process for page composition, cover generation, Lulu PDF creation, submission, and customer email.
- **Unified Two-Stage Flow for ALL Personalized Books**: Pre-payment character preview, cover and text review; post-payment background generation of scenes and cover using FLUX 2 Dev + reference, user approval of illustrations; then PDF composition and Lulu submission.
- **Automatic Scene Retry System**: Failed FLUX 2 Dev scene generations trigger automatic retries (max 6, 10 minutes apart).
- **Unified Prompt Architecture**: Modular prompt files for all personalized books, defining scenes, covers, and character descriptions, all in Disney Pixar 3D style.
- **eBook Product**: Standalone ($7) with permanent viewer access or free gift with print purchase (6-month access).
- **Unified Text-in-Image Architecture**: All book types compose text directly into scene images using PIL at generation time. PDFs and eBooks render images only.
- **eBook Viewers**: `visor_qs/` (Quick Stories) for square, `visor_pb/` (Personalized Books + Tu Amor Peludo) for A4 vertical. Both use image-only pages with text pre-composed, StPageFlip, canvas-confetti, and Web Speech API (TTS).
- **eBook Structure (Unified)**: Portada → Dedicatoria → Scene images (text integrated) → Cierre (if any) → Contraportada.
- **Newsletter/Community System**: Voluntary subscription with `NewsletterSubscriber` model and admin panel.
- **Rate Limiting + Email Capture (Preview Protection)**: 3 preview generations per 3 hours per IP, shared across products. Email mandatory for preview generation, storing `PreviewLead` data.
- **VPS Deployment**: Export ZIPs for migration, deployment guide (`GUIA_VPS.md`), environment configuration (`.env.example`), systemd service (`magicmemories.service`), and automated deploy script (`deploy.sh`). Production/sandbox controlled by environment variables. Fixes for Nginx proxy, local visor mode, admin error emails, and required VPS environment variables are implemented.

## External Dependencies
- **OpenAI API**: GPT-4o for story text generation.
- **Replicate**: FLUX (FLUX Dev, FLUX 2 Pro) for image generation; Ideogram Character for baby story scenes.
- **PayPal**: Payment processing via REST API (sandbox: PAYPAL_CLIENT_ID, PAYPAL_CLIENT_SECRET, PAYPAL_MODE=sandbox). Rutas: /api/paypal/create-order, /api/paypal/capture-order, /api/paypal/create-print-order, /api/paypal/capture-print-order. Flujo libros impresos separado en /print-order/<preview_id>, panel admin en /admin/print-requests.
- **Lulu**: Physical book printing and order submission API.
- **SQLite/MySQL**: Database.
- **SMTP**: Email delivery services.
- **Ghostscript**: PDF sanitization (production only).
- **Paramiko**: SFTP client for uploading visor books to VPS.