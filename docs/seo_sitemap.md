# Sitemap.xml — Documentación SEO

## Qué genera `/sitemap.xml`

La ruta `/sitemap.xml` (en `app.py`) genera el mapa del sitio **dinámicamente**
(no es una lista hardcodeada). Incluye:

- Páginas núcleo: home, catálogos (Express, Universos, Cumpleaños), pricing,
  FAQ, contacto, about, legales (`/terms`, `/privacy`).
- Listado de Cuentos Solidarios (`/cuentos-solidarios`) + cada historia con
  `status='published'` consultada en vivo desde la tabla `community_stories`.
  Las historias `draft`, `hidden` o `archived` NO aparecen.
- Las 24 páginas de cuentos personalizados (`SITEMAP_PERSONALIZED_STORIES` en
  `app.py`), cada una con su URL real:
  - Cuentos Express/Universos/Cumpleaños → `/personalize-story?story=<id>`
  - Tu Amor Peludo (las 4 variantes) → `/personalize-furry-love?story=<variant>`

Cada URL bilingüe declara `<xhtml:link rel="alternate" hreflang="es|en|x-default">`
usando el namespace `xmlns:xhtml` en `<urlset>`, consistente con las etiquetas
`hreflang` que ya pone `base.html` en el `<head>` de cada página.

`<lastmod>` usa la fecha real de `updated_at`/`created_at` para Cuentos
Solidarios, y la fecha de generación del sitemap (deploy) como fallback para
el resto. `<changefreq>` y `<priority>` están diferenciados: home/catálogos
más alto, cuentos individuales prioridad media (0.6), legales baja (0.3).

## Corrección de canonical/hreflang con query params

`templates/base.html` calculaba antes el `canonical` y los `hreflang` usando
solo `request.path`, **sin el query string**. Esto hacía que TODAS las 24
páginas de `/personalize-story?story=...` y `/personalize-furry-love?story=...`
apuntaran al mismo canonical (`/personalize-story` sin el `story=`), haciendo
que Google las tratara como contenido duplicado.

Ahora `base.html` detecta `request.args.get('story')` y lo incluye tanto en
el `canonical` como en los `hreflang` (agregando `&lang=es`/`&lang=en` cuando
corresponde). Esto no afecta a páginas sin `?story=` (catálogos, home, etc.),
que siguen comportándose igual que antes.

## Añadir un nuevo cuento al sitemap

Cuando se publique un cuento personalizado nuevo:
1. Agregar su id/variant a `SITEMAP_PERSONALIZED_STORIES` en `app.py`.
2. Si es un cuento de Amor Peludo, usar el variant corto (sin `_illustrated`),
   igual que hacen los demás furry_love.

Cuando se publique un nuevo Cuento Solidario, no hace falta tocar el código:
en cuanto su `status` pase a `published` en la base de datos, aparece
automáticamente en el sitemap.

## Reenviar el sitemap en Google Search Console

Después de cada deploy con cambios en el sitemap:

1. Entrar a [Google Search Console](https://search.google.com/search-console)
   con la propiedad `magicmemoriesbooks.com`.
2. Ir a **Sitemaps** (menú lateral izquierdo).
3. Si `sitemap.xml` ya está listado, hacer clic en los 3 puntos → **Volver a
   enviar** (Resubmit). Si no está, escribir `sitemap.xml` en el campo y
   pulsar **Enviar**.
4. Esperar 24–48h y revisar el estado: debe decir "Correcto" (Success) con el
   número de URLs descubiertas (debería subir a ~36+ desde las ~20 anteriores).
5. Revisar **Páginas** → **Indexación** para confirmar que no aparecen nuevos
   errores de "Duplicada, Google eligió una URL canónica distinta" en las
   páginas de `/personalize-story` o `/personalize-furry-love` (ese era el
   problema que causaba el canonical roto con query params).
6. Si aparecen URLs viejas indexadas incorrectamente (por ejemplo, sin el
   `?story=`), usar la herramienta **Inspección de URLs** para solicitar una
   nueva indexación de la URL correcta una vez que Google haya vuelto a
   rastrear el sitio.

No hace falta volver a enviar el sitemap en cada deploy — solo cuando cambian
significativamente las URLs incluidas (nuevos cuentos, nuevas landing pages,
etc.).
