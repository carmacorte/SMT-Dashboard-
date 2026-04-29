# SMT-Dashboard-
Daily Meetings

## Diagnóstico rápido: pantalla negra en `index.html`

Si al abrir el dashboard solo ves pantalla negra, normalmente **no es corrupción del archivo**, sino fallo de carga en runtime:

1. **Dependencias CDN bloqueadas/no disponibles**
   - El `index.html` depende de React/ReactDOM y otras librerías por CDN.
   - Si la red bloquea `cdnjs` o `jsdelivr`, el render de `#root` no ocurre.

2. **Abrir con `file://` en vez de servidor local**
   - Parte del flujo está preparado para entorno web y puede omitir módulos cuando detecta modo local.
   - Levanta un servidor local (ej. `python3 -m http.server`) y entra por `http://localhost:8000`.

3. **Error JS temprano**
   - Abre DevTools → Console y revisa errores rojos.
   - El archivo incluye manejadores globales de error, así que cualquier excepción de arranque debería mostrarse ahí.

### Verificaciones concretas en este repo

- Existe `div#root` principal para montar React.
- Hay carga explícita de React y ReactDOM por CDN.
- Hay múltiples bloques HTML dentro de templates para exports; esto **es intencional** y no implica corrupción por sí mismo.

Si quieres, en el siguiente paso te dejo un parche para que el dashboard funcione también **offline** (bundlear React localmente y eliminar dependencia crítica de CDN).
