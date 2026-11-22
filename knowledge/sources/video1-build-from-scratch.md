# Análisis del vídeo «How to Build a Commander Deck from Scratch»

Nov 22, 2026 · @Guillem

## Resumen

Es una fuente muy buena para el analizador de decks. Tiene mucho más contenido útil que relleno, y lo mejor es que da **criterios concretos y medibles**, que es justo lo que necesita el analizador.

## Lo que vale oro

### Números que encajan directamente en el rubric

| Categoría | Recomendación del vídeo |
| --- | --- |
| Ventaja de cartas | Mínimo 12, idealmente 16–17. Unas 8 de valor de maná 3 o menos y unas 4 de 4 o más; las caras tienen que robar de forma explosiva (5 o más cartas) |
| Ramp | 10–11 «normales» (cuanto más baratas, mejor) más 2–4 de ramp explosivo, según el bracket |
| Interacción | Unas 10 piezas dedicadas más 2–4 wipes; se puede bajar 1–2 si hay interacción incidental en el resto del deck |
| Tierras | 38 (él mismo baja a 37: «haz lo que digo, no lo que hago») |
| Cartas caras | Solo 3–4 de valor de maná 6 o más |
| Condiciones de victoria | 3–4 |

### Una definición que mejora el clasificador

Solo cuenta como ventaja de cartas lo que te deja con **más cartas netas**. Faithless Looting dice «roba», pero no es ventaja de cartas. Si se clasifica por la palabra «draw» en el texto, el clasificador fallaría justo ahí.

### Un baremo por valor de maná

Útil para que Claude justifique los cortes:

- **6 o más:** tiene que cambiar la partida en un turno; si no, se corta.
- **5:** ventaja enorme inmediata, o una amenaza que gana sola si nadie la responde.
- **4:** pieza potente y muy sinérgica.
- **1–3:** motores que den valor turno tras turno.

### Métodos que se pueden convertir en pasos del análisis

- Sacar las **palabras clave del comandante** (enters, attacks, sacrifice, counters…) y premiar las cartas con **varias sinergias solapadas**, no solo una.
- Ante la duda entre dos cartas: primero la afinidad con el resto del deck, después el valor de maná.
- La prueba del **goldfish hasta el turno 7**: «¿podría ganar con esta mesa? ¿Hay alguna carta que, robada ahora, me haga ganar?». Es una pregunta excelente para que Claude la razone sobre el deck.

## Lo que hay que tener en cuenta

- **Los subtítulos automáticos destrozan los nombres.** El comandante (probablemente Hei Bai, Spirit of Balance, de la colección de Avatar) sale como «Heiwei», «Hayabusa», «Haywire» y «Hey, by». También hay nombres como «Brina», «Dargul Coller» o «like your wellspring» que no se pueden identificar con seguridad. Es justo el caso para el paso de validación contra Scryfall: los criterios sirven, pero los nombres de cartas de la transcripción no son fiables.
- **Es la opinión de un solo creador** y está pensada para un deck de **bracket 2**. Los números son razonables y bastante estándar, pero conviene contrastarlos con otros vídeos y dejarlos como valores por defecto ajustables según el bracket. Él mismo dice que en bracket 3 subiría el ramp explosivo y que a más nivel hace falta interacción más eficiente.
- **Tiene un componente social** («no juegues cosas que impidan jugar a los demás») que también conviene recoger como criterio, ligado al bracket.

## Siguiente paso

Convertir este análisis en `prompts/knowledge/deckbuilding.md`, con los criterios ordenados, los rangos por bracket y una sección de «preguntas que Claude debe hacerse sobre el deck». Cada vídeo nuevo solo añadirá o matizará reglas sobre esa base.
