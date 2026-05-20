# Post de LinkedIn — Brecha salarial México

## Versión texto + imagen (~1,500 caracteres)

---

Las mujeres ocupadas en México tienen MÁS escolaridad y MÁS presencia en sector formal que los hombres. Y aun así, se llevan a casa 23% menos al mes.

Tomé los microdatos de la ENOE 4T 2025 (INEGI, 110 mil personas ocupadas) y descompuse esa brecha con Oaxaca-Blinder. Quería entender cuánto se justifica con variables observables y cuánto queda sin explicar.

Cómo lo hice:
📊 Datos: ENOE 4T 2025, ponderados por factor de expansión
🛠️ Stack: Python, pandas, statsmodels
⚙️ Técnica: Mincer separado por sexo + Oaxaca-Blinder pooled (Neumark) + bootstrap (240 réplicas) + Heckman para robustez

Lo que encontré:

1. La brecha del 23% se descompone casi exactamente en mitades — 49% lo explican las horas trabajadas (las mujeres trabajan 8 hrs menos por semana en el mercado remunerado), 50% queda residual.

2. La composición observable — educación, sector, formalidad, entidad federativa — aporta 0.5% (IC 95%: −2%, +3%). No es estadísticamente distinta de cero. El cliché "ganan menos porque están menos calificadas" no se sostiene con datos.

3. El residual del 50% equivale a 16% de salario adicional sin explicación. A todo igual, las mujeres se llevan ese 16% menos al mes.

4. La corrección Heckman por sesgo de selección no mueve el resultado (Mills p=0.52). El 50% residual es robusto.

Lo que me llevo: la conversación pública mezcla brecha mensual con brecha por hora y eso confunde la pregunta de fondo. Las mujeres mexicanas no ganan menos porque sean menos productivas — ganan menos porque trabajan menos horas remuneradas (y eso abre una pregunta sociológica más grande sobre cuidados no pagados) y porque queda un residual que ninguna variable observable explica.

¿Qué variable omitida creen que pesa más en ese residual? Yo apuesto a antigüedad en el puesto y discriminación directa en negociación, pero no las tengo en ENOE.

📊 Dashboard interactivo (Plotly + mapa coroplético):
https://darioomar-blip.github.io/brecha-salarial-mexico/

🔗 Repo + notebooks en el primer comentario 👇

#DataAnalytics #Python #BrechaSalarial #México #PeopleAnalytics #DatosAbiertos #INEGI

---

## Versión carrusel (8 slides)

### Slide 1 — Portada / hook
**Las mujeres mexicanas ocupadas tienen MÁS escolaridad y MÁS formalidad que los hombres.**

Y aun así se llevan 23% menos al mes.

¿Por qué?

📊 Análisis con microdatos ENOE 4T 2025 (INEGI)

### Slide 2 — La sorpresa
La cifra famosa es "las mujeres ganan 23% menos al mes".
Cierto.

Pero la cifra "menos calificadas" no aplica:
- Escolaridad: 11.0 años vs 10.3 (más mujeres)
- Sector formal: 57.8% vs 55.1% (más mujeres)
- Experiencia: 22.7 vs 23.0 (iguales)

La única variable Mincer donde difieren fuerte: horas trabajadas.

### Slide 3 — Las horas
Hombres: 45.9 hrs/semana
Mujeres: 37.6 hrs/semana

8.4 horas menos por semana en el mercado remunerado.

Eso solo ya explica casi la mitad de la brecha mensual.

[Aquí va el histograma de horas con la doble distribución femenina]

### Slide 4 — La pregunta real
La pregunta no es "¿pagan menos a las mujeres por hora?"

La pregunta es:

**¿Por qué a fin de mes se llevan menos?**

Y la respuesta requiere descomponer la brecha en sus partes.

### Slide 5 — La descomposición Oaxaca-Blinder
De la brecha mensual del 32% (en log):

🔵 49% se explica por horas trabajadas
🟠 50% queda sin explicar
⚪ 0.5% lo aporta la composición observable (estadísticamente cero)

[Aquí va el gráfico de barras apiladas]

### Slide 6 — Lo no explicado
50% de la brecha = 16% de salario adicional sin justificación.

A todo igual — mismas horas, misma educación, mismo sector, misma entidad — las mujeres ganan ese 16% menos.

¿Es discriminación? Es un techo. Puede ser discriminación directa, habilidades no observadas, redes profesionales, o todo lo anterior.

### Slide 7 — La robustez
¿Y si las mujeres ocupadas son una muestra "buena" no aleatoria?

Apliqué Heckman para corregir por sesgo de selección.

Resultado: Mills no es significativo (p = 0.52). La brecha residual del 50% se mantiene.

### Slide 8 — Lo que aprendí
Tres lecciones del proyecto:

1. La conversación pública mezcla brecha mensual con brecha por hora. Son cosas distintas.

2. Las explicaciones "estructurales" (educación, sector) no sostienen los datos del 4T 2025.

3. La pregunta interesante no es de mercado laboral — es sociológica. ¿Por qué las mujeres trabajan menos horas remuneradas? Empieza por el trabajo doméstico no pagado, que ENOE captura mal.

🔗 Análisis completo (Python + notebooks) en el primer comentario 👇
¿Qué variable omitida creen que pesa más en ese residual?

---

## Reglas aplicadas

- Hook directo (más calificación, menos paga)
- 1 emoji por slide máximo, solo cuando aporta
- Frases cortas
- Reflexión personal en cierre, no estructura aspiracional
- Pregunta abierta específica al final
- Sin marcas tipo "es real y estadísticamente significativo"

## Mejor horario para publicar

Martes o miércoles, 8-10am (hora CDMX).
Ventana objetivo: primera semana de julio 2026.
