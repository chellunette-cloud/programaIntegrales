# Guía: publicar la aplicación y enviar el enlace al profesor

Esta guía explica cómo **publicar la aplicación en internet (gratis)** para
obtener un **enlace público** que el profesor puede abrir desde cualquier
navegador, **sin instalar nada y sin tener Python**.

Se usa **Streamlit Community Cloud**, el servicio oficial y gratuito de
Streamlit. La app quedará en una dirección parecida a:

```
https://<tu-usuario>-integrales-multiples.streamlit.app
```

---

## Resumen rápido

1. Subir el proyecto a **GitHub** (una sola vez).
2. Entrar a <https://share.streamlit.io> con la cuenta de GitHub.
3. Crear la app indicando el repositorio y el archivo `app.py`.
4. Copiar el enlace que aparece y enviárselo al profesor.

> El profesor **no** necesita cuenta, ni GitHub, ni instalar Python. Solo abre el
> enlace. La primera vez que se abre tarda ~30–60 s en "despertar"; luego carga
> normal.

---

## Paso 0. Requisitos previos (en tu computador)

- Tener **git** instalado. Ya está instalado (`git --version` funciona).
- Tener (o crear) una cuenta gratuita en **GitHub**: <https://github.com/signup>

---

## Paso 1. Preparar el repositorio local (solo la primera vez)

Abre una terminal en la carpeta del proyecto y ejecuta:

```powershell
cd "C:\Users\samyl\OneDrive\Documentos\integrales"

# Inicializar el repositorio (si no existe)
git init -b main

# Guardar la primera versión
git add .
git commit -m "Resolutor de Integrales Múltiples"
```

> La carpeta de depuración y los archivos temporales ya están excluidos por
> `.gitignore`, así que no se subirán.

---

## Paso 2. Crear el repositorio en GitHub y subir el código

1. Entra a <https://github.com/new>.
2. **Repository name:** por ejemplo `integrales-multiples`.
3. Déjalo en **Public** (debe ser público para desplegar gratis) y **no** marques
   "Add a README" (ya tienes uno).
4. Pulsa **Create repository**.
5. GitHub te mostrará dos comandos como estos. Cópialos y pégalos en la terminal
   (reemplaza `TU-USUARIO` por tu nombre de usuario de GitHub):

```powershell
git remote add origin https://github.com/TU-USUARIO/integrales-multiples.git
git push -u origin main
```

Si es la primera vez que usas git con GitHub, te pedirá iniciar sesión. La forma
más sencilla es instalar **GitHub Desktop** (<https://desktop.github.com>), que
gestiona el inicio de sesión con un par de clics; también puedes usar un
**token de acceso personal** si git te lo pide por consola.

Verifica que el código aparece en `https://github.com/TU-USUARIO/integrales-multiples`.

---

## Paso 3. Desplegar en Streamlit Community Cloud

1. Entra a <https://share.streamlit.io> y pulsa **Sign in with GitHub**
   (autoriza el acceso).
2. Pulsa **Create app** → **Deploy a public app from GitHub**.
3. Rellena:
   - **Repository:** `TU-USUARIO/integrales-multiples`
   - **Branch:** `main`
   - **Main file path:** `app.py`
4. (Opcional) En **Advanced settings** puedes elegir la versión de Python. El
   proyecto incluye `runtime.txt` con `python-3.11`, que es la recomendada.
5. Pulsa **Deploy!** y espera a que termine la instalación (1–3 minutos la
   primera vez; instala las dependencias de `requirements.txt`).

Cuando termine, arriba aparecerá tu app funcionando y el enlace público. Cópialo.

---

## Paso 4. Enviar el enlace al profesor

Comparte simplemente la URL, por ejemplo:

```
https://TU-USUARIO-integrales-multiples.streamlit.app
```

Sugerencia de mensaje:

> Profesor, le comparto la aplicación que desarrollé para resolver integrales
> múltiples paso a paso (dobles/triples, coordenadas polares/cilíndricas/esféricas,
> áreas y volúmenes, con verificación numérica y descarga en PDF). Puede abrirla
> desde el navegador aquí: <enlace>. No requiere instalar nada.

---

## Actualizar la aplicación (cuando cambies el código)

Cada vez que modifiques el proyecto, sube los cambios y la nube se actualiza sola:

```powershell
git add .
git commit -m "Descripción del cambio"
git push
```

A los pocos segundos, Streamlit Community Cloud vuelve a desplegar la nueva
versión automáticamente.

---

## Notas y consejos

- **¿La app está "dormida"?** Las apps gratuitas se suspenden tras un rato sin
  uso. Al abrir el enlace, espera ~30–60 s a que despierte. Si quieres que esté
  siempre despierta, puedes visitarla de vez en cuando desde el panel de
  Streamlit.
- **Uso responsable:** el plan gratuito tiene recursos y tiempo de cómputo
  limitados; es suficiente para este proyecto.
- **OCR desde foto:** esa función opcional requiere Tesseract instalado en el
  servidor y **no** está activa en la nube. La app lo indica con un aviso y el
  resto de funciones (lo importante) funciona con normalidad.
- **Alternativa sin git ni GitHub:** puedes subir la app a **Hugging Face Spaces**
  (<https://huggingface.co/new-space>), eligiendo SDK *Streamlit*. Allí se pueden
  arrastrar los archivos directamente desde el navegador (sin comandos `git`) y
  también se obtiene un enlace público.

---

## Problemas frecuentes

| Síntoma | Solución |
|---|---|
| El build falla al instalar dependencias | Revisa el registro ("Manage app" → *Logs*) en Streamlit. Comprueba que `requirements.txt` está en la raíz del repositorio. |
| "Oh no. Something went wrong." | Abre **Manage app** → **Logs** para ver el error de Python real. |
| La app carga pero un ejercicio es lento | Los cálculos simbólicos pueden tardar; hay un límite de **30 s** por operación y se recurre a método numérico si se excede. |
| No aparece el botón *Create app* | Asegúrate de haber iniciado sesión con GitHub y de que el repositorio es **público**. |
