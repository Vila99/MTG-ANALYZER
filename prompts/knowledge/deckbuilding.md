# Criterios de análisis de decks de Commander

Este documento es la base de conocimiento del analizador. Recoge criterios de construcción de decks de Commander para evaluar un deck y proponer mejoras. Son **valores por defecto, no leyes**: ajústalos siempre al plan del deck, al comandante y al bracket objetivo del usuario, y explica por qué te desvías cuando lo hagas.

---

## 1. Orden del análisis

Analiza el deck en este orden. Cada paso usa las conclusiones del anterior.

1. **Objetivo del deck** (sección 2): ¿qué hace, cómo lo capitaliza y cómo gana?
2. **Forma del deck** (sección 3): rol del comandante y equilibrio entre generadores, amplificadores y payoffs.
3. **Pilares de ventaja** (sección 4): robo, maná e interacción, ajustados al plan.
4. **Resiliencia** (sección 5): ¿cómo puede perder el deck y qué lo protege?
5. **Curva y tierras** (sección 6).
6. **Sinergias y nonbos** (sección 7).
7. **Prueba de victoria** (sección 8): ¿puede ganar en el turno objetivo?
8. **Ajuste al bracket y criterio social** (sección 9).
9. **Cortes y añadidos** (sección 10).

---

## 2. Objetivo del deck

Todo deck debe tener un objetivo claro en tres pasos:

1. **Acción principal:** lo que el deck hace la mayor parte del tiempo (crear tokens, poner contadores +1/+1, sacrificar, llenar el cementerio, disparar ETBs…).
2. **Capitalización:** cómo convierte esa acción en una ventaja grande (p. ej. muchos tokens → un efecto que cuenta permanentes; cementerio lleno → reanimación masiva).
3. **Victoria:** cómo esa ventaja termina la partida o da una ventaja insalvable.

Reglas:
- Si no puedes rellenar los tres pasos con cartas concretas del deck, **ese es el primer problema** a señalar.
- Saca las **palabras clave del comandante** (enters, attacks, sacrifice, dies, counters, leaves the battlefield…). Definen qué cartas tienen sinergia.
- En brackets 1–2 se puede ganar "acumulando una mesa potente". En brackets 3–4 el deck necesita un camino a la victoria claro.
- Un buen deck debería poder ganar **sin su comandante en mesa**: las cartas del 99 tienen que tener sinergia entre sí, no solo con el comandante.

---

## 3. Forma del deck

### Tipos estructurales de carta

Además de su rol funcional (ramp, robo, removal…), clasifica cada carta por su papel en el plan:

| Tipo | Qué hace | Prueba rápida |
|---|---|---|
| **Generador** | Ejecuta la acción principal del deck | Sin generadores, el deck no hace nada |
| **Amplificador** | Hace que los generadores rindan más (duplicadores, copias, bonificaciones) | Por sí solo no hace nada |
| **Payoff** | Gana la partida con una mesa suficiente | Con la mesa típica del turno 7–8, ¿gana? |
| **Ventaja** | Robo, maná, interacción o protección | Sostiene el plan, no lo ejecuta |

### El rol del comandante define la forma

El comandante está siempre disponible, así que **se reduce la categoría en la que cae**:

- **Comandante generador:** menos generadores en el 99, más amplificadores (forma de "diamante").
- **Comandante amplificador:** menos amplificadores, más generadores (forma de T o triángulo invertido).
- **Comandante payoff:** casi no hacen falta más payoffs.
- **Comandante de ventaja** (roba, ramp o protege): menos cartas de ese pilar.
- **Comandante decorativo:** el deck se construye como si no hubiera comandante.

Señala desequilibrios: demasiados generadores y ningún amplificador, ningún payoff, o generadores que repiten lo que ya hace el comandante.

Algunos planes cambian la forma: si generadores y amplificadores ya ganan solos, sobran payoffs; si el plan necesita mucho maná o es lento en arrancar, se refuerzan los pilares correspondientes.

---

## 4. Pilares de ventaja

### 4.1 Ventaja de cartas

**Definición estricta:** solo cuenta lo que deja al jugador con **más cartas netas** (roba al menos 2, o 1 por turno de forma repetida). Los *looters* (roba y descarta) **no** son ventaja de cartas.

Mide por separado:
- **Ventaja de cartas neta.**
- **Selección y llenado del cementerio:** looting, surveil, scry, self-mill, conjure. Importa, sobre todo en decks de cementerio, pero no sustituye a la anterior.

Rangos por defecto:
- **Mínimo 12** piezas dedicadas; **14–17** es mejor.
- Curva: unas **2/3 de valor de maná 3 o menos** (motores que roban 1 por turno o 1–2 cartas) y **1/3 de 4 o más**.
- Las caras (4+) deben robar de forma **explosiva**: potencial de 5 o más cartas.

Prioriza la **ventaja de cartas sinérgica**: robo que se alimenta del plan del deck (tokens, artefactos, sacrificios, tierras…). Es más barata que los staples y rinde más.

En brackets 3–4 el deck tiene que poder **excavar** hasta sus condiciones de victoria y respuestas.

### 4.2 Ventaja de maná

Tres tipos:

1. **Ramp básico:** adelanta la curva de forma permanente (rocas, dorks, búsqueda de tierras).
   - **Mínimo 10**, más si el comandante o la curva son caros.
   - Más barato es mejor: 1 maná > 2 > 3, salvo que la sinergia justifique otra cosa.
2. **Ramp explosivo:** multiplica el maná durante uno o varios turnos (duplicadores, rituales, tesoros en masa).
   - **2 en bracket 2**, **3–4 en bracket 3** o más.
3. **Maná sinérgico:** usa el plan del deck para producir mucho maná turno tras turno (p. ej. artefactos que pagan hechizos con *improvise*, tokens que producen maná).

El ramp de **tierras** es el más resiliente: casi no se destruye en Commander casual y sobrevive a los wipes.

### 4.3 Ventaja de mesa (interacción y protección)

Incluye removal puntual, contrahechizos, protección y wipes.

Rango por defecto: **~10 piezas dedicadas + 2–4 wipes**. Se puede bajar 1–2 si hay interacción incidental en otras cartas.

**Ajusta la cantidad al deck:**
- Más interacción si el deck es **lento, de valor o frágil**.
- Menos si es **explosivo** (gana de golpe) o **muy resiliente**.
- A mayor bracket, interacción más **eficiente** (barata, instantánea). En brackets 1–3 vale interacción más sinérgica aunque sea menos eficiente.

**Ajusta el tipo:**
- Deck que es una amenaza visible (pega, da miedo) → más **protección**.
- Deck que crece bajo el radar → más **removal** para frenar a los demás.
- Con mucho maná sobrante → removal "comodín" (que quita cualquier tipo de permanente) por encima de la eficiencia.

Busca **interacción que gana partidas**: wipes o efectos que, con el plan del deck, dejan una ventaja insalvable (wipes asimétricos, wipes instantáneos que dejan tu mesa en pie).

---

## 5. Resiliencia

Un deck pierde de dos formas:
1. **Le impiden ganar** (le quitan las piezas clave, le contrarrestan el plan).
2. **No puede impedir que gane otro.**

Evalúa ambas. Un deck resiliente no tiene por qué ser rápido: gana siendo el último en pie.

### Capas de resiliencia

Cuantas más capas se integren **en el plan principal**, más resiliente es el deck:

- **Ganar vida.**
- **Piezas clave que no son criaturas** (artefactos, encantamientos, tierras): más difíciles de quitar.
- **Recursión** desde el cementerio.
- **Ramp de tierras.**
- **Velocidad instantánea:** protección, contrahechizos, outlets de sacrificio, flash, habilidades activadas.
- **Poder en la mano** (difícil de interactuar).
- **Reconstrucción rápida** tras un wipe (mucho maná, mucha mano, tokens).

### Resiliencia por color

Cruza esta tabla con la identidad de color del comandante para detectar huecos:

| Color | Fortalezas | Debilidades | Cómo compensarlo |
|---|---|---|---|
| **Blanco** | Protección, fogs, indestructible, ganar vida, removal y wipes; segundo mejor en ramp de tierras y recursión de permanentes | Pocas | Combinar varias capas |
| **Azul** | Contrahechizos, robo, jugar en la pila | Mal ramp, mala recursión de permanentes | Dejar maná abierto, jugar a velocidad instantánea, guardar el poder en la mano |
| **Negro** | Recursión (sobre todo de criaturas), ganar vida en masa, wipes | Poca protección en la pila, débil al exilio, se hace mucho daño con "paga vida" | Outlets de sacrificio instantáneos, respuestas al hate de cementerio, controlar la pérdida de vida |
| **Rojo** | Redirección, daño en la pila, recupera instantáneos y artefactos | El más frágil: no gana vida, casi sin protección, robo temporal (impulse) | Permanentes que no sean criaturas, 3–4 *wheels* para recargar la mano, jugar desde el cementerio, velocidad instantánea |
| **Verde** | Ramp de tierras y robo masivos; reconstruye muy rápido | Poca protección | Volumen de cartas y maná para recuperarse |

---

## 6. Curva y tierras

### Tierras

- **37–38** por defecto. Fallar caídas de tierra hunde el porcentaje de victorias.
- **36** solo con mucho ramp barato o una curva muy baja.
- Mono color: muchas básicas y tierras de utilidad incoloras.
- 3 o más colores: mayoría de tierras que dan varios colores.
- Comprueba que las **fuentes de cada color** estén a la altura de los **símbolos de maná** (pips) que pide el deck. Es un fallo muy común.

### Curva

- Solo **3–4 cartas de valor de maná 6 o más**, salvo que el deck genere maná de sobra.
- La mayoría de cartas temáticas deben ser baratas.
- Si el comandante cuesta X, se puede ir más ligero en cartas de coste X (se jugará el comandante en ese turno).
- Si el comandante necesita mesa previa para rendir, refuerza las cartas de 1–3.

### Baremo por valor de maná

Úsalo para justificar cortes:

| Valor de maná | Exigencia mínima |
|---|---|
| **6+** | Cambia la partida de forma drástica o da una ventaja insalvable **en un turno**. Si no, se corta. |
| **5** | Ventaja enorme el turno que entra, o amenaza que gana sola en pocos turnos si no la responden. |
| **4** | Pieza potente y muy sinérgica que acelera el plan. |
| **1–3** | Motores que dan valor turno tras turno, no solo al entrar. |

---

## 7. Sinergias y nonbos

- Premia las cartas con **varias sinergias solapadas** con el comandante y con el resto del deck. Una carta con una sola sinergia es candidata a corte.
- Ante la duda entre dos cartas: **primero la afinidad** con el deck, **después el valor de maná**.
- Detecta **nonbos**: cartas que se anulan o estorban entre sí, o que no funcionan con el plan principal (p. ej. un efecto que retrasa la entrada de encantamientos combinado con payoffs que son encantamientos; cartas que dependen del comandante en mesa con efectos que lo barajan en la biblioteca).
- Señala las **cartas trampa**: aparentan potencia pero suelen costar un turno entero sin impacto real.
- Señala las cartas caras sin ETB ni efecto inmediato en decks que dependen de entrar en mesa.

---

## 8. Prueba de victoria (goldfish)

Razona sobre la mesa típica del deck en el **turno objetivo** (normalmente el 7–8; antes en brackets altos) y hazte estas preguntas en orden:

1. **¿Puede ganar con esta mesa y esta mano?** Si sí, bien.
2. Si no: **¿hay alguna carta en el deck que, robada ahora, le haga ganar?**
3. Si no: **¿hay suficiente valor en la mesa?**
   - Si no lo hay, el problema es el ritmo o el plan: hay que revisar generadores, amplificadores o maná.
   - Si lo hay, falta una condición de victoria: propón una que encaje con las sinergias del deck.
4. **¿Tiene suficiente robo para llegar a sus condiciones de victoria?** Si no, añade más condiciones de victoria (densidad) o más robo sinérgico.

Reglas:
- **3–4 condiciones de victoria** como mínimo: cartas que, con la mesa típica, probablemente ganan la partida.
- El turno de victoria orienta sobre el bracket: **turno 5–6 tiende a bracket 4**, **7 o más a bracket 3**, más tarde y sin camino claro, bracket 2. Tenlo en cuenta junto con el resto de criterios.

---

## 9. Bracket, velocidad y criterio social

- **Decisiones a velocidad instantánea:** valora cuántas cartas permiten actuar en el turno de los rivales, sobre todo al final del turno anterior al propio. Decidir más tarde es decidir con más información. Un deck con muchas opciones instantáneas juega mejor de lo que su lista sugiere.
- **Esconder amenazas** (bracket 3+): conviene que el deck no parezca la mayor amenaza de la mesa hasta que gana. Ayudan el poder en la mano, en el cementerio o repartido en muchas piezas pequeñas, y no acelerar demasiado al principio.
- **Criterio social:** el objetivo de Commander es divertirse. Señala las cartas que **impiden jugar a los demás** (bloqueos, destrucción masiva de tierras, turnos extra encadenados, combos muy rápidos) si no encajan con el bracket declarado por el usuario.
- Respeta el bracket objetivo: no propongas subir el nivel de poder si el usuario no lo pide. Para subirlo, empieza por el ramp explosivo, la eficiencia de la interacción y el robo.

---

## 10. Cortes y añadidos

Al proponer cambios:

- **Corta primero** cartas que no cumplan el baremo de valor de maná, cartas con una sola sinergia, nonbos, cartas trampa y generadores que repiten al comandante.
- **Añade primero** lo que más falte según el análisis: un paso del objetivo sin cubrir, un pilar por debajo del rango, una capa de resiliencia que el color permite y el deck no usa.
- Cada añadido debe indicar **a qué carta reemplaza** y **por qué**, citando el criterio de este documento.
- Prefiere cartas con **varias sinergias** con el deck y, ante dos opciones similares, la más barata en maná y en precio.
- Respeta el presupuesto y el bracket del usuario.
- **Solo sugiere cartas reales que encajen en la identidad de color.** Si hay un pool de candidatas, elige de él.
