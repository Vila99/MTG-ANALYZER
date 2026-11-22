# Análisis de los vídeos «Never Lose» y «Fixing its shape»

Nov 22, 2026 · @Guillem

Son incluso mejores que el primer vídeo para el analizador de decks. El primero daba **números**; estos dos dan **marcos para razonar**, que es justo lo que Claude puede aplicar sobre un deck y un script no.

## «How to Build Commander Decks That Never Lose»

La idea central es la **resiliencia**: construir el deck alrededor de *no perder*, no de ganar rápido.

- **Las dos formas de perder:** que te impidan ganar, o que no puedas impedir que gane otro. Son dos preguntas muy buenas para el análisis.
- **Capas de resiliencia** que se suman: ganar vidas, piezas clave que sean artefactos o encantamientos (más difíciles de quitar que las criaturas), recursión desde el cementerio, ramp de tierras (casi nadie destruye tierras) y jugar a velocidad instantánea.
- **Fortalezas y debilidades de cada color** en resiliencia: blanco el más resiliente, rojo el más frágil (necesita 3–4 *wheels* para recargar la mano), negro débil contra el exilio y la pérdida de vida, azul malo en ramp y recursión de permanentes, verde con poca protección. Esto se puede convertir en una tabla que Claude cruce con la identidad de color del comandante.
- **Decidir a velocidad instantánea**, idealmente al final del turno anterior al tuyo, porque así decides con más información. Su deck lleva unas 30 cartas así.
- **Esconder las amenazas** a partir de bracket 3: ser el *archienemigo secreto*, no el evidente.
- **El goldfish como diagnóstico encadenado:** ¿puedo ganar en el turno objetivo? Si no, ¿hay alguna carta que me haga ganar? Si no, ¿falta valor en la mesa? Si sí, ¿tengo suficiente robo para llegar a mi condición de victoria? Si no, más condiciones de victoria o más robo sinérgico.

## «Make Any Deck Busted by fixing its shape»

Para la app, este es probablemente el más valioso de los tres.

- **Objetivo claro en 3 pasos:** lo que hace el deck → cómo lo capitaliza → cómo eso gana la partida. Por ejemplo: tokens → Warp World → cartas que ganan al salir. Si Claude no sabe rellenar los tres pasos, ya ha encontrado el primer problema del deck.
- **Cuatro tipos de carta:** *generadores* (hacen lo que el deck quiere), *amplificadores* (lo multiplican), *payoffs* (ganan con una mesa suficiente) y *ganadores de ventaja* (cartas, maná, mesa).
- **El rol del comandante define la «forma» del deck:** se reduce la categoría en la que cae el comandante. Si el comandante es generador, menos generadores y más amplificadores.
- **Tres pilares:** ventaja de cartas, de maná y de mesa. Y el tipo más infravalorado de cada uno: el **sinérgico**, que además es barato. Por ejemplo, robo que se alimenta de los tokens del propio deck.
- **La cantidad de interacción depende del deck:** si es rápido o lento, explosivo o de valor, resiliente o frágil. Si el deck da miedo, más protección; si va bajo el radar, más removal. Y busca «interacción que gana», tipo Cyclonic Rift.
- **Detecta los «nonbos»**, cartas que se estorban entre sí (Thunderfoot Baloth con Warp World, encantamientos que Warp World retrasa). Es exactamente el tipo de análisis en el que Claude aporta algo que un script no puede.
- **El turno de victoria en el goldfish da una pista del bracket:** ganar en el turno 5–6 tiende a bracket 4; en el 7 o más, a bracket 3.

## Qué cambia en el diseño de la app

1. **Clasificación en dos capas:** los roles funcionales que ya teníamos (ramp, robo, removal…) más el rol estructural (generador / amplificador / payoff / ventaja), incluyendo el del comandante. Con eso, Claude puede decir «tu deck tiene forma de X y debería tener forma de Y».
2. **El rubric tiene que ser condicional, no fijo.** Los vídeos se contradicen en apariencia: el primero pide unas 10 piezas de interacción más 2–4 wipes, y el tercero lleva menos a propósito porque el deck es resiliente y explosivo. La regla real es «depende de la resiliencia y la velocidad del deck», y eso es lo que debe evaluar Claude.
3. **Separar dos métricas de robo:** la ventaja de cartas *neta* (la definición estricta del primer vídeo) y la *selección y llenado del cementerio* (el segundo cuenta mill, looting y sumideros de maná). Las dos importan, pero miden cosas distintas.
4. **Nuevas preguntas para el prompt:** el objetivo en 3 pasos, las dos formas de perder, las capas de resiliencia según los colores, los nonbos y cuántas cartas se pueden usar a velocidad instantánea.
5. **Para más adelante:** simular el goldfish en código (miles de manos aleatorias para medir en qué turno sueles tener X maná). Es determinista, barato, y le daría a Claude un dato objetivo sobre el que razonar.

## Precauciones

- **Los tres vídeos parecen del mismo creador**, por el estilo y porque repite cartas (Angel of Indemnity, Final Showdown, Sun Titan). Son coherentes entre sí, pero conviene sumar otras voces para no heredar las manías de una sola persona.
- **El 53 % de victorias** (9 de 17) es una muestra pequeña, y él mismo reconoce que su habilidad cuenta. El vídeo está patrocinado por Mythic Tools, aunque la función que enseña (comparar los pips de cada color con las fuentes de maná) es justo lo que ya está previsto en `metrics.py`.
- **Los nombres de cartas siguen igual de mal:** «Citrus Supplier» es Stitcher's Supplier, «Gaia's Emilating Inferno» es Jaya's Immolating Inferno, «Perose» es Purphoros y «Paragan Tuk» debe de ser Peregrin Took. De las transcripciones se sacan criterios, no listas de cartas.

## Siguiente paso

Juntar este análisis con el del primer vídeo en `prompts/knowledge/deckbuilding.md`, con el rubric condicional y la lista de preguntas para Claude.
