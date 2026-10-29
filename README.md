# Genomic Atlas 🧬🌎

**Explora la ciencia. Encuentra tu lugar.**

> **Estado:** `v0.1.0 · estructura inicial / pre-MVP`. La taxonomía está publicada; el directorio de oportunidades reales todavía está vacío. **Este proyecto no representa oficialmente a la UNAM ni a las instituciones que puedan mencionarse en el futuro.**

**Genomic Atlas** es un proyecto de código abierto para ayudar a estudiantes de **Ciencias Genómicas** y otras disciplinas afines a descubrir campos científicos y encontrar oportunidades de formación: laboratorios, estancias, años de investigación, *summer research programs*, congresos, seminarios, cursos, talleres y becas. Nace con estudiantes de licenciatura en México como público prioritario, con vocación latinoamericana y global.

## ¿Qué problema queremos resolver?

Una persona que estudia ciencias genómicas puede investigar neuroinmunología, paleogenómica, medicina de precisión, microbiología, agricultura sostenible, conservación y muchos otros campos. Sin embargo, las oportunidades están dispersas entre páginas institucionales, convocatorias anuales y contactos de laboratorios. Además, no siempre se informa con claridad si **aceptan estudiantes de licenciatura**, si hay **financiamiento** o cuáles son las **fechas de aplicación**.

Este atlas une dos formas de explorar:

- **Por curiosidad:** área → subespecialidad → laboratorios / oportunidades.
- **Por necesidad:** tipo de programa → elegibilidad → país → costos / becas → convocatoria.

## Qué incluye esta versión

- [x] Taxonomía inicial de **15 macroáreas científicas** y sus subespecialidades.
- [x] Sitio Astro en español con explorador y búsqueda de áreas.
- [x] Directorio de oportunidades listo para recibir datos verificados (vacío de inicio).
- [x] Modelos separados para instituciones, laboratorios, oportunidades, convocatorias y financiamiento.
- [x] Validación automática de datos y pruebas básicas en Python.
- [x] Plantillas de propuesta y flujos de integración/despliegue GitHub Actions.
- [ ] Primera colección de oportunidades reales verificadas.
- [ ] Filtros de nivel académico, país, financiamiento y fechas.
- [ ] Seguimiento automático de convocatorias y enlaces.

**Importante:** el sitio no inventa convocatorias. Tener una ficha de laboratorio no significa que ofrezca una estancia abierta. Las fechas y condiciones deben verificarse en las fuentes originales.

## Ejecutar en tu equipo

Requisitos: **Node.js 22.12+**, **npm** y **Python 3.10+**.

```bash
# 1. Clona este repositorio (cuando esté publicado):
git clone https://github.com/gitsselcc/genomic-atlas.git
cd genomic-atlas

# 2. Instala dependencias:
npm install

# 3. Inicia el sitio:
npm run dev
# Abre http://localhost:4321/genomic-atlas/

# 4. Comprueba los datos y las pruebas:
python scripts/validate_data.py
python -m unittest discover -s tests -v

# 5. Construye el sitio estático:
npm run build
```

> **Nota de instalación:** no se incluye `package-lock.json` en esta primera entrega porque no se pudieron descargar dependencias en el entorno de generación. `npm install` lo crea en tu equipo (con conexión a internet); después, **sube ese archivo al repositorio** y cambia a `npm ci` en CI para instalaciones reproducibles.

## Estructura

```text
genomic-atlas/
├── .github/
│   ├── ISSUE_TEMPLATE/         # Propuesta de oportunidades y áreas
│   ├── workflows/              # Validación y despliegue
│   └── PULL_REQUEST_TEMPLATE.md
├── docs/
│   ├── taxonomy.md             # Criterios de clasificación científica
│   ├── data-dictionary.md      # Entidades, relaciones y campos
│   ├── verification-policy.md  # Política de revisión de fuentes
│   └── roadmap.md              # Entregables por versión
├── scripts/
│   ├── validate_data.py        # Validación y referencias cruzadas
│   └── check_deadlines.py      # Alertas de fechas próximas
├── src/
│   ├── components/             # Componentes UI reutilizables
│   ├── data/                   # Catálogo JSON versionado
│   ├── layouts/                # Layout global
│   ├── pages/                  # Rutas Astro
│   ├── styles/                 # Estilos
│   └── types.ts                # Tipos de entidades
├── tests/                      # Pruebas de validación
├── astro.config.mjs
├── package.json
└── README.md
```

## Estructura de los datos

| Archivo | Entidad | Ejemplos de datos |
|---|---|---|
| `areas.json` | Área científica | ID, nombre, descripción, subespecialidades |
| `institutions.json` | Institución | País, ciudad, URL institucional |
| `laboratories.json` | Laboratorio | Institución, áreas, enlace del grupo |
| `opportunities.json` | Oportunidad estable | Tipo, elegibilidad académica, áreas, URL oficial, estado de verificación |
| `calls.json` | Convocatoria por edición | Ciclo 2027, apertura, cierre, fuente |
| `funding.json` | Financiamiento | Cobertura, tipo de apoyo, evidencia |

**Relación clave:** una oportunidad de verano permanece en `opportunities.json`, mientras que su convocatoria **2027** y la de **2028** se almacenan por separado en `calls.json`. Los laboratorios no se confunden con convocatorias; las opciones de apoyo UNAM requieren confirmación individual.

Consulta [diccionario de datos](docs/data-dictionary.md) y [política de verificación](docs/verification-policy.md).

## ¿Cómo contribuir?

1. Revisa [CONTRIBUTING.md](CONTRIBUTING.md).
2. Abre un **Issue** con una fuente oficial o una corrección de datos.
3. Si puedes editar archivos, prepara un **Pull Request**. Ejecuta `python scripts/validate_data.py` antes de enviarlo.
4. No agregues correos privados, documentos personales o datos sensibles de estudiantes.

Aceptamos propuestas de oportunidades de México, América Latina y otras regiones. No priorizamos instituciones por prestigio: la relevancia científica, elegibilidad y acceso al financiamiento son fundamentales.

## Roadmap

- **v0.1:** taxonomía, repositorio, validación, sitio inicial. **Esta versión.**
- **v0.2:** 30–50 registros reales con fuentes oficiales y pruebas de calidad.
- **v0.3:** buscador multiatributo y fichas detalladas.
- **v0.4:** flujo comunitario de contribuciones y revisión periódica.
- **v1.0:** cobertura ampliada y sostenibilidad del catálogo.

Ver [roadmap completo](docs/roadmap.md).

## Publicación en GitHub Pages

1. Crea un repositorio **`genomic-atlas`** en tu cuenta GitHub (preferentemente público, si quieres colaboraciones).
2. Sube todos los archivos a la rama `main`. Tras ejecutar `npm install` localmente, sube también el `package-lock.json` generado.
3. Abre **Settings → Pages → Build and deployment → Source: GitHub Actions**.
4. El workflow `.github/workflows/deploy.yml` desplegará el sitio en `https://gitsselcc.github.io/genomic-atlas/` después del push a `main`.
5. Si cambias de usuario o nombre de repositorio, edita `site` y `base` en `astro.config.mjs` y los enlaces del proyecto.

## Licencia

Código y documentación disponibles bajo [MIT](LICENSE). Las convocatorias y contenidos externos conservan los derechos de sus respectivas instituciones; aquí se registran metadatos y enlaces a fuentes originales, no copias de sus textos completos.

---

**Genomic Atlas** — una herramienta en construcción para que las oportunidades de investigación sean más fáciles de descubrir, comparar y compartir.
