# Magic Memories Books

Magic Memories Books is a bilingual web application that uses AI to generate personalized children's storybooks with custom text and illustrations, offering both digital and print formats.

## Run & Operate

**GitHub Sync Obligatorio**: Antes y después de cualquier cambio, sincronizar con GitHub (`magicmemoriesbooks-io/magic-memories-page`) usando la API de GitHub (`PUT /repos/{owner}/{repo}/contents/{path}`).

**Env Vars**:
- `PAYPAL_CLIENT_ID`, `PAYPAL_CLIENT_SECRET`, `PAYPAL_MODE` (sandbox/live)
- `GELATO_API_KEY`, `GELATO_USE_SANDBOX` (true/false)
- Otros tokens para OpenAI, Replicate, etc. (gestionados por `.env` o secretos de Replit)

## Stack

- **Framework**: Flask
- **Runtime**: Python (version no especificada, asumir reciente)
- **ORM**: SQLAlchemy (inferido por DB usage)
- **Validation**: _Populate as you build_
- **Build Tool**: _Populate as you build_
- **AI**: OpenAI GPT-4o (text), Replicate FLUX (FLUX Dev, FLUX 2 Pro, FLUX 2 Dev), Ideogram Character (images)
- **DB**: SQLite (development/VPS), MySQL (production)

## Where things live

- `services/`: Core application logic, AI integrations, payment processing.
- `services/personalized_books/`: Logic and prompt files for personalized stories.
- `docs/fixed_pages/`: Specifications for fixed pages (credits, dedication, back covers).
- `docs/templates/tu_amor_peludo.md`: Detailed documentation for the `furry_love` product.
- `static/images/fixed_pages/`: Static images for back covers.
- `templates/`: HTML templates.
- `static/`: Static assets (CSS, JS, images).
- `data/magicbooks.db`: SQLite database file (VPS deployment).
- `visor_qs/`, `visor_pb/`: eBook viewer applications for Quick Stories and Personalized Books.

## Architecture decisions

- **Unified Two-Stage Flow**: All personalized books follow a pre-payment preview (character, cover, text) and a post-payment background generation (scenes, cover) using FLUX 2 Dev + reference, followed by user illustration approval, PDF composition, and print submission.
- **AI Image Generation Strategy**: Uses FLUX Dev (guidance 3.5, steps 25-30) for character consistency and FLUX 2 Dev/Pro with PuLID for human photo integration (teen/adult) or visual fidelity (baby/adventure). Ideogram Character is used for baby story scenes.
- **Negative Prompting for FLUX**: `negative_prompt` is passed as a separate API parameter for FLUX 2 Dev calls to reliably suppress unwanted animal features, using gender-specific additions.
- **Text-in-Image Composition**: All book types compose text directly into scene images using PIL at generation time, rather than layering text on PDFs.
- **Cloudprinter Combined PDF**: For Cloudprinter printing, a single combined PDF is generated, including cover wrap and interior pages, with specific page counts and bleed requirements.

## Product

- **Personalized Children's Storybooks**: AI-generated stories and illustrations tailored to user input.
- **Bilingual Support**: Content available in multiple languages (Spanish primary).
- **Digital & Print Formats**: Offers eBooks, PDFs, and physical printed books via Cloudprinter.
- **Multiple Story Types**: Includes "Cuentos Mágicos Express" (digital), "Aventuras a tu Medida" (illustrated, print), "Cuentos FotoMágicos" (photo integration), "Cuentos de Cumple", and "Haz tu Historia" (custom AI stories).
- **Interactive Previews**: Dynamic previews of generated text and illustrations before purchase.
- **Payment & Printing Integration**: Seamless integration with PayPal for payments and Cloudprinter for print fulfillment.
- **Print Partner**: Cloudprinter ONLY. No Gelato, no Lulu. Books already printed and validated.
- **Print Specs (Haz tu Historia & Universos Ilustrados)**: A4, 28 pages, hardcover or softcover. Digital formats: PDF A4 (Europe) and PDF Letter/Carta (Americas).

## User preferences

- **PDF Testing**: Always offer PDFs WITHOUT Ghostscript sanitization for testing (add `?raw=1` or use skip_sanitize=True). Only apply Ghostscript in production.
- **Language**: Spanish preferred for communication. SIEMPRE documentar procesos en español.
- **Legal Compliance**: Páginas legales separadas: `/terms` (Términos) y `/privacy` (Política de Privacidad). Cumplimiento COPPA/GDPR para fotos de menores. **NO HAY REEMBOLSO** - el usuario revisa y aprueba antes de pagar, y tiene 1 oportunidad de regeneración post-pago. Fotos se eliminan automáticamente en 72h (scheduler cada 6h + cleanup al iniciar). Admin: `/admin/uploaded-photos` para gestionar fotos. Consent checkbox obligatorio antes de subir fotos (client + server-side validation). Upload endpoint requiere `consent=true`.
- **Fixed Pages Documentation**: Ver `docs/fixed_pages/` para especificaciones de páginas fijas (créditos, dedicatoria, contraportadas, estructura PDF, reglas de generación de imágenes, especificaciones Cloudprinter)
- **Sitemap.xml (Jul 2026)**: `/sitemap.xml` es dinámico (`SITEMAP_PERSONALIZED_STORIES` en `app.py`), incluye las 24 páginas de cuentos personalizados, catálogos, legales y Cuentos Solidarios publicados (consulta viva a `community_stories`), con `hreflang` xhtml por URL. `base.html` ahora incluye `?story=` en el `canonical`/`hreflang` para evitar contenido duplicado en Search Console. Ver `docs/seo_sitemap.md` para detalle y pasos de verificación en Google Search Console. Al agregar un cuento personalizado nuevo, sumarlo a `SITEMAP_PERSONALIZED_STORIES`.
- **Flujo Unificado**: El pago (PayPal) y la impresión (Cloudprinter) están separados. Primero pago digital → luego opcionalmente libro impreso via /print-order/<preview_id>.
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
- **negative_prompt (CRITICAL FIX Apr 2026)**: FLUX 2 Dev accepts `negative_prompt` as a SEPARATE API parameter (not inside prompt text). This is the only reliable way to suppress animal features (fox tail, animal ears, etc.) on the child character. Applied to ALL FLUX 2 Dev calls: preview generation (`preview.py`), scene generation (`illustrated_book_service.py:generate_scene_complete`), closing scene, and front cover. Uses `get_gender_negative_prompt(gender)` from `replicate_service.py` which includes fox tail, dragon tail, bunny tail, animal ears, animal features on human, etc. Gender-specific additions (earrings/bows for male; boy haircut for female).
- **Hair Color Palette (May 2026)**: Paleta final aprobada para `hair_color` form keys → descriptores FLUX. SOLO cambiar `blonde` y `very_light_blonde`; el resto (`black`, `brown`, `light_brown`, `red`, `auburn`) no se toca.
  - `black` → `jet black`
  - `brown` → `medium brown` / `medium chestnut brown`
  - `light_brown` → `warm light brown (caramel-honey tone)`
  - `blonde` → **`dark dirty blonde`** (rubio oscuro ceniciento, no dorado, no rojizo)
  - `very_light_blonde` → **`pale platinum blonde`** (platino frío)
  - Swatches HTML: `blonde` = `#C4953A`, `very_light_blonde` = `#F1D88A`
  - Mapas actualizados en: `fixed_stories.py` (7 mapas), `app.py` (2), `illustrated_book_service.py` (2), `furry_love_prompts.py` (1), `ai_service.py` (texto descriptivo)
- **Hair lengths (Apr 2026)**: Added `very_short` as new hair_length option (between `very_little` and `short`). Boys: crew cut with high fade. Girls: pixie cut. Added "Muy corto / Very short" UI radio button in `personalize_story.html`. Removed "tousled" descriptor from straight male short hair (was contradicting "straight"). Fixed `get_hair_action()` in all 5 FotoMágicos prompt files to handle `very_short`, `bald`, `very_little` correctly.
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

## Estructura de PDFs — Cuentos Personalizados (todos los 9 libros PhotoMagic)

**PDF Digital (28 páginas — lo que recibe el usuario por email y descarga):**
| Pág | Contenido |
|-----|-----------|
| 1 | Portada |
| 2 | Blanca |
| 3 | Portadilla |
| 4 | Dedicatoria |
| 5–23 | Historia (19 escenas) |
| 24 | Colorín A |
| 25 | Colorín B |
| 26 | Créditos |
| 27 | Blanca |
| 28 | Contraportada fija |

**CP content.pdf (26 páginas — interior para Cloudprinter, portada/contraportada van en cover.pdf):**
| Pág | Contenido |
|-----|-----------|
| 1 | Blanca |
| 2 | Portadilla |
| 3 | Dedicatoria |
| 4–22 | Historia (19 escenas) |
| 23 | Colorín A |
| 24 | Colorín B |
| 25 | Créditos |
| 26 | Blanca |

**REGLA CRÍTICA**: `cp_pdf_service.py` y `generate_cw_content_pdf` — NO TOCAR. Validado en sandbox y live, impreso y perfecto.

## Gotchas

- **GitHub Sync**: Normal `git push` will fail due to divergent histories and large binaries. Always use GitHub API for file modifications.
- **VPS Drift (CRÍTICO)**: El VPS tiene docenas de archivos modificados directamente por SSH en sesiones anteriores que nunca se sincronizaron de vuelta a git. Por eso `git pull` falla en el VPS. NUNCA volver a hacer cambios directamente en el VPS por SSH sin antes hacer commit+push desde Replit. El flujo correcto es: editar en Replit → commit → push a GitHub → pull en VPS.
- **FLUX Dev Guidance**: Do NOT set guidance to 7.0 for FLUX Dev; it causes hallucinations. Stick to 3.5 and increase steps for detail.
- **FLUX Negative Prompting**: FLUX interprets "NO X" in the main prompt as the presence of X. Use the dedicated `negative_prompt` API parameter instead.
- **Cloudprinter Cover Image**: The fixed PNG (`static/images/fixed_pages/{book_id}_back_cover.png`) must be used for Cloudprinter back covers, not the `visor page_24.jpg` (which has a pre-baked logo from legacy provider).

## Pointers

- [Replicate Documentation](https://replicate.com/docs)
- [OpenAI API Documentation](https://platform.openai.com/docs)
- [PayPal REST API Documentation](https://developer.paypal.com/docs/api/overview/)
- [Cloudprinter API Documentation](https://www.cloudprinter.com/api)
- [Flask Documentation](https://flask.palletsprojects.com/en/latest/)