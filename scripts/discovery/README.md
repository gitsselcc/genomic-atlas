# Source Discovery Engine (v0.1)

Primer recolector de Genomic Atlas. Revisa fuentes registradas explícitamente y guarda candidatos con procedencia. No rastrea todo Internet, no verifica convocatorias y no publica directamente en el catálogo.

## Requisitos y ejecución

Python 3.10+. Sin dependencias externas obligatorias.

```bash
python scripts/discovery/discover.py
python -m unittest discover -s tests -v
```

El registro `research/sources/registry.json` es JSON válido (también YAML válido), para evitar PyYAML en esta versión. Cada entrada define `source_id`, `name`, `url`, `source_type` (`rss`, `sitemap`, `webpage`), país, idiomas, áreas, palabras clave y estado activo.

La salida `research/discovery/candidates.jsonl` guarda un objeto JSON por línea: URL canónica, título, resumen breve, procedencia, fecha detectada, fecha declarada por la fuente, hash de contenido, áreas sugeridas y estado `pending_review`. Las URLs sin cambios se omiten en ejecuciones posteriores; cambios de título/resumen generan una nueva línea.

## Límites y seguridad

- Solo se consultan fuentes del registro; no hay rastreo recursivo arbitrario.
- Se consulta `robots.txt` antes de cada dominio; si no puede verificarse, se omite.
- Hay límite de tamaño de respuesta y timeout.
- Se usa un User-Agent identificable.
- No se almacenan páginas completas ni se copian textos protegidos.
- Respeta términos de uso y límites del sitio aunque robots.txt permita el acceso.
- Los errores se reportan y hacen fallar el proceso para que no pasen inadvertidos.
- No se infieren fechas futuras, elegibilidad, admisión ni financiamiento.

## Conectores

RSS/Atom: títulos, enlaces, resúmenes y fechas declaradas. Sitemap XML: URLs y lastmod, con límite de sitemaps secundarios. HTML: título, descripción, canonical y enlaces del mismo dominio.

No resuelve JavaScript, CAPTCHA, autenticación, newsletters ni PDF. La búsqueda web mediante API autorizada será un conector posterior. `check_frequency` es metadato; la ejecución diaria la determina GitHub Actions.

El workflow diario sube el JSONL como artefacto de Actions. No hace commits automáticos a main ni publica candidatos en la web.
