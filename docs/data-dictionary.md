# Diccionario de datos (v0.1)

El sitio lee archivos JSON en `src/data/`. Cada archivo contiene un **arreglo de objetos**. Estos archivos están vacíos (salvo las áreas) para evitar publicar convocatorias inventadas.

## Entidades

| Entidad | Campos obligatorios | Comentario |
|---|---|---|
| Área | `id`, `name`, `description`, `subareas` | Macroáreas y subespecialidades |
| Institución | `id`, `name`, `country`, `website` | `city` es opcional |
| Laboratorio | `id`, `institution_id`, `name`, `research_area_ids`, `website` | Receptor **potencial**, no equivale a convocatoria |
| Oportunidad | `id`, `title`, `type`, `institution_id`, `research_area_ids`, `level`, `official_url`, `description`, `verification_status` | Programa o evento estable |
| Convocatoria | `id`, `opportunity_id`, `cycle`, `source_url` | Una entrada por edición; fechas opcionales |
| Financiamiento | `id`, `opportunity_id`, `type`, `details`, `source_url` | Una entrada por fuente de apoyo |

## Enumeraciones

`opportunity.type`: `summer`, `research_stay`, `research_year`, `congress`, `seminar`, `workshop`, `course`, `fellowship`, `mobility`.

`opportunity.level`: lista de `undergraduate`, `master`, `phd`.

`opportunity.verification_status`: `verified` (verificada), `pending` (pendiente), `outdated` (desactualizada).

`funding.type`: `full`, `partial`, `none`, `unknown`. **No asumir que una beca cubre el costo total sin evidencia.**

## Relaciones

```text
AREA ←(muchas a muchas)→ OPPORTUNITY
INSTITUTION 1 ── N LABORATORY
INSTITUTION 1 ── N OPPORTUNITY
OPPORTUNITY 1 ── N CALL (ediciones por año)
OPPORTUNITY 1 ── N FUNDING (fuentes de apoyo)
```

## Convenciones

- `id`: minúsculas ASCII, números y guiones (`mi-programa-2027`).
- Fechas: formato `YYYY-MM-DD`, o campo omitido / `null` si se desconoce.
- URLs: `https://...` preferido; deben llevar a fuentes oficiales o páginas institucionales.
- `last_verified`: fecha del último cotejo humano con la fuente institucional; no es la fecha en que se añadió el registro.
- `cycle`: etiqueta de edición, por ejemplo `2027`; **no implica que la convocatoria esté abierta**.
- Evitar datos personales privados de postulantes e investigadores.

## Registro de ejemplo (NO REAL)

Para pruebas existe `tests/fixtures/example-opportunity.json`. Es una **estructura ficticia**, con dominio `.invalid`, que no forma parte del catálogo público.

## Campos futuros (no implementados todavía)

- Elegibilidad detallada: ciudadanía, carrera, semestre, idioma, mínimo de créditos.
- Condiciones económicas: costo, estipendio, transporte, vivienda y moneda.
- Compatibilidad potencial con movilidad UNAM (evidencia y restricciones).
- Etiquetas metodológicas, organismos, modalidad presencial/remota.
- Historial de revisiones y deduplicación de convocatorias por edición.

Mantener este alcance acotado evita diseñar un gran catálogo sin datos suficientes para validarlo.
