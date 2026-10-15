# Resolutor de Integrales Múltiples

Herramienta académica para **Cálculo Integral Multivariable** (tercer semestre de
Ingeniería Catastral y Geodesia). Resuelve integrales dobles y triples, cambios a
coordenadas polares/cilíndricas/esféricas y cálculos de área y volumen, mostrando
**todo el procedimiento paso a paso**, como una solución hecha en el tablero.

No es una simple calculadora: explica cada etapa (identificación, límites, cambio de
coordenadas y jacobiano, antiderivada, evaluación en los límites, simplificación) y
**verifica** el resultado con integración numérica independiente.

---

## 1. Características

- **Integrales dobles:** límites constantes o variables, regiones rectangulares y
  delimitadas por curvas, órdenes `dy dx` / `dx dy`, cambio de orden, cálculo de áreas.
- **Coordenadas polares:** conversión automática de `∫∫ f(x,y) dA` a polares con el
  jacobiano `dA = r dr dθ` para círculos, semicírculos, sectores, coronas y curvas
  polares (cardioide, rosa).
- **Integrales triples:** en cartesianas y en coordenadas cilíndricas y esféricas, con
  el jacobiano correcto (`r` y `ρ²·sin φ`).
- **Volúmenes:** sólidos predefinidos (esfera, cilindro, cono, paraboloide) y volumen
  entre dos superficies, con representación en 3D.
- **Funciones exponenciales, trigonométricas, polinómicas y con radicales.**
- **Detección de funciones especiales:** avisa cuándo la antiderivada **no es elemental**
  (por ejemplo `x ↦ e^{x²}`, que usa `erfi`) y cuándo solo hay resultado **numérico**.
- **Verificación automática** del resultado simbólico contra una integración numérica
  independiente (SciPy).
- **Control de errores:** valida sintaxis y límites, detecta ejercicios incompletos o
  ambiguos y **pide aclaración en lugar de inventar datos**.
- **Interfaz en español** con notación matemática renderizada (KaTeX), gráfica de la
  región en 2D, dibujo del sólido en 3D, copia del procedimiento y **descarga en PDF**.
- **OCR opcional** desde una fotografía (con revisión manual antes de resolver).

---

## 2. Decisiones técnicas

| Componente | Tecnología | Motivo |
|---|---|---|
| Motor simbólico | **SymPy** | Cálculo exacto, simplificación y funciones especiales; es un CAS real, no una IA generativa. |
| Cálculo numérico | **SciPy** (`quad` anidado) | Verificación independiente y respaldo. Se usa `quad` anidado en vez de `nquad` porque es más robusto con límites de derivada singular como `√(1−x²)`. |
| Gráficas | **Matplotlib** | Gráficas 2D/3D y exportación directa a PDF. |
| Interfaz | **Streamlit** | UI web moderna en Python puro, con renderizado **LaTeX nativo (KaTeX)** y respuesta dinámica. |

> El cálculo **nunca** depende de una IA generativa: lo realiza el motor matemático real.
> La IA solo sería un apoyo opcional para interpretar un enunciado redactado en lenguaje
> natural (no implementado aquí para no introducir resultados no verificables).

---

## 3. Instalación

Requisitos: **Python 3.10 o superior** (probado en Python 3.14, Windows 11).

```bash
# 1) Situarse en la carpeta del proyecto
cd integrales

# 2) (Recomendado) Crear un entorno virtual
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# 3) Instalar dependencias
pip install -r requirements.txt
```

---

## 4. Cómo ejecutar

### Aplicación gráfica (recomendado)

```bash
streamlit run app.py
```

Se abrirá el navegador en `http://localhost:8501`. Si no se abre, entra manualmente.

En Windows también puedes usar el script incluido:

```bat
ejecutar.bat
```

### Pruebas automáticas

```bash
python tests/test_motor.py      # pruebas del motor matemático (14 pruebas)
python tests/test_app.py        # pruebas de la interfaz (runtime simulado)
```

---

## 5. Uso de la aplicación

1. En la barra lateral elige el **tipo de ejercicio** (o deja *Detección automática*).
2. Escribe o pega el ejercicio en notación LaTeX o texto plano, por ejemplo:

   ```latex
   \int_0^1\int_0^{\sqrt{1-x^2}}(x^2+y^2)\,dy\,dx
   \int_0^{2\pi}\int_0^1 e^{r^2} r\,dr\,d\theta
   \int_0^{1}\int_0^{1-x}\int_0^{1-x-y} dz\,dy\,dx
   ```

3. Pulsa **▶ Resolver**. Aparecerán pestañas con:
   - **Procedimiento** (paso a paso),
   - **Resultado** exacto y aproximado,
   - **Fórmulas** empleadas,
   - **Región (2D)** y **Sólido (3D)**,
   - **Verificación** numérica,
   - **Exportar** (copiar procedimiento y descargar PDF/TXT).

### Notación aceptada

- Integrales: `\int`, `\iint`, `\iiint` o los símbolos `∫`, `∬`, `∭`, o `int`.
- Límites: `\int_0^1`, `\int_{0}^{2\pi}`, `\int_{-\infty}^{\infty}`.
- Funciones: `\sin`, `\cos`, `\tan`, `\ln`, `\log`, `\exp`, potencias `\cos^2 x`, raíces
  `\sqrt{1-x^2}`, `\sqrt[3]{x}`, fracciones `\frac{1}{2}`, constantes `\pi`, `e`, `\infty`.
- Variables griegas: `\theta`, `\phi`, `\rho`, etc.
- No hace falta escribir paréntesis en funciones (`\sin\phi` equivale a `\sin(\phi)`).

> Para la multiplicación, si escribes dos variables juntas usa un espacio o `*`
> (por ejemplo `x y`, `x*y`, `2x`). `xy` sin separación se interpreta como un único
> símbolo llamado `xy`.

---

## 6. Estructura del proyecto

```
integrales/
├── app.py                     # Interfaz Streamlit
├── requirements.txt
├── README.md
├── ejecutar.bat / ejecutar.sh # Scripts de arranque
├── motor/                     # Motor matemático (independiente de la interfaz)
│   ├── especificacion.py      # Estructuras de datos (Capa, Especificacion, Paso, Solucion)
│   ├── latex_utils.py         # LaTeX ⇄ SymPy y representación LaTeX/Unicode
│   ├── parser.py              # Interpretación del ejercicio escrito
│   ├── motor_integracion.py   # Resolución paso a paso + verificación numérica
│   ├── ejecutor.py            # Límite de tiempo en operaciones simbólicas
│   ├── coordenadas.py         # Jacobianos y cambio a polares
│   ├── volumenes.py           # Sólidos predefinidos
│   ├── graficas.py            # Región 2D y sólido 3D
│   ├── reportes.py            # Procedimiento en texto y PDF
│   └── ejemplos.py            # Biblioteca de ejemplos
└── tests/
    ├── test_motor.py          # Pruebas del motor (casos obligatorios)
    └── test_app.py            # Pruebas de la interfaz
```

---

## 7. Ejemplos verificados

| Ejercicio | Resultado | Comprobación |
|---|---|---|
| `∫₀²∫₀¹ (x+y) dy dx` | `3` | exacto |
| `∫₀¹∫₀^{√(1−x²)} (x²+y²) dy dx` | `π/8` | ≈ 0.3927 |
| `∫₀^{2π}∫₀¹ e^{r²} r dr dθ` | `π(e−1)` | ≈ 5.3981 |
| `∫₀¹∫₀¹∫₀¹ xyz dz dy dx` | `1/8` | = 0.125 |
| Esfera de radio 5 | `500π/3` | ≈ 523.6 |
| Volumen bajo `z=4−x²−y²` sobre `[0,1]²` | `10/3` | ≈ 3.3333 |
| `∫₀¹ e^{x²} dx` | `½√π·erfi(1)` | ≈ 1.4627 (función especial) |
| `∫_{−∞}^{∞} e^{−x²} dx` | `√π` | ≈ 1.7725 |

---

## 8. Limitaciones conocidas

- **Orden de integración:** se respeta el orden escrito (los diferenciales más a la
  derecha corresponden a la integral más externa). El cambio de orden *automático* no se
  realiza; hay que escribir el nuevo orden explícitamente.
- **Regiones muy generales:** la conversión automática a polares cubre las regiones
  típicas (disco, semicírculo, cuarto de círculo, corona, cardioide, rosa). Para otras
  regiones hay que plantear los límites a mano.
- **Verificación numérica:** en casos con límites infinitos o singularidades raras la
  comprobación puede no ser fiable; se avisa al usuario.
- **Integrales impropias divergentes**: se detecta la no convergencia numérica, pero no
  se realiza un estudio analítico de convergencia.
- **OCR:** es una función **opcional** y de apoyo. El OCR genérico (Tesseract) reconoce
  mal exponentes, signos y diferenciales; por eso siempre debes **revisar y corregir** el
  texto reconocido. Para escritura a mano se recomienda *pix2tex (LaTeX-OCR)* y pegar el
  resultado corregido.
- Las gráficas son **aproximadas** y tienen fines ilustrativos.

---

## 9. Nota académica

El objetivo es servir de apoyo de estudio: transcribe y comprende el procedimiento,
y comprueba siempre el resultado con la verificación numérica y con tus apuntes.
