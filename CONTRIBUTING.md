# Cómo contribuir a Genomic Atlas

Gracias por ayudar a que otros estudiantes encuentren oportunidades de investigación.

## Qué se puede proponer

- Nuevas áreas o subespecialidades y correcciones de la taxonomía.
- Programas de verano, estancias, años de investigación, cursos, congresos, seminarios y becas.
- Instituciones o laboratorios con una fuente institucional verificable.
- Correcciones a fechas, elegibilidad, financiamiento o enlaces.

## Antes de enviar una propuesta

1. Comprueba que ya no exista la misma oportunidad, edición o laboratorio.
2. Incluye **URL oficial**, institución y el **ciclo/año** de la convocatoria.
3. Distingue lo **confirmado** de lo **desconocido**. No inferir que aceptar graduados implica aceptar licenciatura.
4. Nunca publiques información personal de postulantes ni correos privados.
5. No copies el contenido íntegro de páginas externas: escribe una síntesis original y enlaza la fuente.

## Flujo de contribución

**Opción A — Sin programar:** abre un Issue usando la plantilla “Proponer oportunidad” o “Proponer área”. Un mantenedor revisará la fuente.

**Opción B — Pull Request:** haz fork y crea una rama `data/nombre-corto`; añade o corrige entradas JSON; ejecuta validación y abre un PR describiendo qué cambió.

```bash
python scripts/validate_data.py
python -m unittest discover -s tests -v
npm run build
```

Los **identificadores (id)** son estables, en minúsculas y con guiones. Las fechas usan ISO `AAAA-MM-DD`. Usa `null` u omite valores desconocidos en lugar de fabricar datos. La evidencia de becas y movilidad se valida por separado.

Consulta `docs/data-dictionary.md` y `docs/verification-policy.md` antes de añadir registros.

## Criterios para aceptar un PR

- Datos consistentes y sin duplicados.
- Fuente institucional verificable.
- Área científica correctamente asociada.
- Elegibilidad y financiamiento respaldados, o marcados expresamente como pendientes.
- Sin datos personales sensibles, enlaces engañosos o materiales protegidos copiados.
