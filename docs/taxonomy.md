# Taxonomía científica — versión 0.1

La taxonomía se organiza por **macroáreas** (identificador estable), **subespecialidades** y, en futuras versiones, **etiquetas transversales**.

El listado canónico que lee el sitio es `src/data/areas.json`. Este documento explica el modelo; los cambios reales deben hacerse en JSON y pasar por una revisión.

## Las 15 macroáreas iniciales

1. Biomedicina y medicina de precisión
2. Inmunología e inmunogenómica
3. Neurociencias y neurogenómica
4. Oncología y genómica del cáncer
5. Microbiología y enfermedades infecciosas
6. Genética humana y salud pública
7. Biología molecular, celular y del desarrollo
8. Evolución, filogenómica y paleogenómica
9. Ecología, biodiversidad y conservación
10. Agricultura, plantas y seguridad alimentaria
11. Ciencias ambientales y sostenibilidad
12. Biotecnología y biología sintética
13. Bioinformática, IA y genómica computacional
14. Biología interdisciplinaria y campos emergentes
15. Ciencia, sociedad y comunidades

## Principios

- **No exclusividad:** un programa puede pertenecer a varias macroáreas mediante `research_area_ids`.
- **Método ≠ disciplina:** RNA-seq, CRISPR, GWAS, eDNA o trabajo de campo son técnicas, no necesariamente áreas principales.
- **Sistema de estudio ≠ disciplina:** humano, microorganismos, plantas o ecosistemas son filtros complementarios.
- **Etiquetas abiertas:** nuevas subespecialidades pueden agregarse sin crear una macroárea distinta cada vez.
- **Sin jerarquía de prestigio:** la clasificación científica no usa rankings de instituciones.

### Ejemplo conceptual

Un proyecto de microglía en Alzheimer puede pertenecer a `neurociencias`, `inmunologia` y `biomedicina-precision`. Sus etiquetas metodológicas futuras podrían incluir `scRNA-seq`, `epigenómica` y `cultivo-celular`.

**Pendiente v0.2:** catálogo independiente de métodos, sistemas biológicos y problemas científicos con sinónimos.
