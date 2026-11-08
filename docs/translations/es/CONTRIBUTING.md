# Guías de Contribución / Contributing Guidelines

Gracias por tu interés en contribuir a **opensource-agents**. Damos la bienvenida a todo tipo de contribuciones: reportes de bugs, solicitudes de nuevas características, mejoras en la documentación y cambios de código.

Terima kasih atas minat Anda untuk berkontribusi. Kami menerima semua bentuk kontribusi: laporan bug, permintaan fitur, perbaikan dokumentasi, dan kode.

---

## Código de Conducta

- Sé acogedor, inclusivo y respetuoso con todos los colaboradores.
- Mantén las discusiones constructivas y enfocadas en el trabajo técnico.
- No se tolerará ninguna forma de acoso o discriminación.

---

## Cómo Contribuir

### 1. Reportar Issues
- Revisa los issues existentes antes de abrir uno nuevo para evitar duplicados.
- Utiliza títulos claros y descriptivos.
- Para los reportes de bugs, incluye los pasos para reproducir, el comportamiento esperado frente al real y los detalles del sistema.

### 2. Pull Requests
1. Haz un fork del repositorio y crea tu rama desde `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```
2. Instala las dependencias:
   ```bash
   pip install -r requirements.txt
   ```
3. Realiza tus cambios:
   - Sigue las convenciones PEP 8 para los scripts de Python.
   - Incluye docstrings y anotaciones de tipos donde sea razonable.
   - Si modificas scripts, asegúrate de implementar un manejo de errores y logging adecuados.
   - Mantén los workflows de YAML válidos y utiliza controles de concurrencia.
4. Prueba localmente antes de hacer push:
   ```bash
   # Syntax check all scripts
   python -m py_compile scripts/*.py
   ```
5. Haz commit con mensajes descriptivos (ej. `feat: add retry logic to pr_reviewer.py`).
6. Haz push a tu fork y envía un pull request dirigido a `main`.

---

## Pautas de Desarrollo

- **Agentes de IA**: Los scripts utilizan la sintaxis de `openai` v1+ y apuntan a `gpt-4o-mini` para mantener los costos de la API al mínimo.
- **Prompts**: Almacena los system prompts en `.github/prompts/<agent_name>.txt` en lugar de incrustar cadenas largas de texto en el código de Python.
- **Secrets**: NUNCA hagas commit de API keys o tokens. Todos los scripts deben leer los secrets a través de variables de entorno.

---

## Traductores

Mantenemos traducciones comunitarias para los archivos de documentación en `docs/translations/`:
- `id` — Indonesio (Bahasa Indonesia)
- `zh` — Chino simplificado (简体中文)
- `ja` — Japonés (日本語)
- `es` — Español (Español)
- `ar` — Árabe (العربية)

Para activar actualizaciones de traducción automatizadas, etiqueta un issue con `translate` o ejecuta el workflow manualmente a través de GitHub Actions.