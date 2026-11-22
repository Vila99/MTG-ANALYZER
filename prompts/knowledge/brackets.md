# Brackets de Commander y Game Changers

Este documento enseña al analizador a **deducir el bracket de un deck** a partir de su contenido, en lugar de preguntárselo al usuario.

> **Estado:** sistema de brackets de Wizards of the Coast, todavía en **beta**. Reglas según la actualización del 21 de octubre de 2025. Lista de Game Changers según la actualización del 9 de febrero de 2026 (53 cartas). Revisar este archivo y `data/game_changers.json` cada vez que Wizards publique un anuncio de Commander o de cartas prohibidas y restringidas.

---

## 1. Principios del sistema

- Los brackets son **una herramienta para la conversación previa a la partida** (rule zero), no una regla estricta. Excepto en cEDH, siempre manda lo que acuerde la mesa.
- **La intención importa más que el cumplimiento técnico.** Un deck puede cumplir todas las restricciones de un bracket y jugar a un nivel superior.
- **Una sola infracción no mueve el deck de bracket automáticamente.** Las expectativas son una guía.
- El **bracket 1 es temático**: un deck no es bracket 1 solo por ser flojo.
- Los **turnos esperados** indican cuándo sería razonable que la partida terminara, no que tenga que terminar entonces.
- **No hay restricciones de tutores** en ningún bracket. Los tutores más eficientes ya están en la lista de Game Changers.

---

## 2. Los cinco brackets

| Bracket | Nombre | Game Changers | Destrucción masiva de tierras | Turnos extra | Combos de 2 cartas (infinitos / que ganan) | Partida esperada |
|---|---|---|---|---|---|---|
| 1 | Exhibition | 0 | No | No | No | 9+ turnos |
| 2 | Core | 0 | No | No encadenados | No | 8+ turnos |
| 3 | Upgraded | Hasta 3 | No | No encadenados | No antes del turno 6 | 6+ turnos |
| 4 | Optimized | Sin límite | Sí | Sí | Sí | 4+ turnos |
| 5 | cEDH | Sin límite | Sí | Sí | Sí | Cualquier turno |

### Descripción de cada bracket

- **1 · Exhibition.** El deck prioriza un tema, una idea o un objetivo por encima del poder. Las condiciones de victoria son temáticas o deliberadamente débiles; la partida es una ocasión para enseñar el deck. Se admite legalidad flexible (cartas "Un-", comandantes poco habituales) si la mesa está de acuerdo.
- **2 · Core.** Decks sin optimizar y directos, con algunas cartas elegidas por creatividad o diversión. Las condiciones de victoria se construyen poco a poco, se ven en la mesa y se pueden interrumpir. Juego de baja presión y social.
- **3 · Upgraded.** Decks reforzados con sinergia y mejor calidad de cartas, capaces de interrumpir a los rivales. Sus Game Changers suelen ser motores de valor o hechizos que cierran la partida. Pueden ganar en un turno grande desde la mano, normalmente tras acumular recursos.
- **4 · Optimized.** Decks que buscan ganar rápido y de forma consistente, pero **no** construidos para el metajuego de cEDH. Sus Game Changers suelen ser maná rápido, motores que se disparan, interrupción gratuita y tutores. Victorias eficientes y casi instantáneas.
- **5 · cEDH.** Decks construidos para el metajuego competitivo, a menudo a partir de listas cEDH conocidas. Optimizados para velocidad y consistencia; casi no hay margen de error.

---

## 3. Game Changers

Cartas que, según Wizards, **deforman con facilidad y de forma drástica** las partidas de Commander: dan una ventaja de recursos enorme, impiden jugar a los demás o buscan cartas potentes sin coste. El poder por sí solo no basta para entrar en la lista; la carta también tiene que ser disruptiva o poco divertida.

**Regla de conteo:**
- **0 Game Changers** → compatible con brackets 1 y 2.
- **1–3 Game Changers** → bracket 3 como mínimo.
- **4 o más** → bracket 4 como mínimo.

El comandante cuenta si está en la lista (hoy solo lo están algunos legendarios, como Braids, Cabal Minion, Grand Arbiter Augustin IV, Narset, Parter of Veils o Tergrid, God of Fright).

### Lista actual (53 cartas, febrero de 2026)

> La fuente de verdad para el código es `data/game_changers.json`. Esta lista es para que Claude entienda el contexto; el conteo lo hace el código.

**Blanco (7):** Drannith Magistrate · Enlightened Tutor · Farewell · Humility · Serra's Sanctum · Smothering Tithe · Teferi's Protection

**Azul (10):** Consecrated Sphinx · Cyclonic Rift · Fierce Guardianship · Force of Will · Gifts Ungiven · Intuition · Mystical Tutor · Narset, Parter of Veils · Rhystic Study · Thassa's Oracle

**Negro (10):** Ad Nauseam · Bolas's Citadel · Braids, Cabal Minion · Demonic Tutor · Imperial Seal · Necropotence · Opposition Agent · Orcish Bowmasters · Tergrid, God of Fright · Vampiric Tutor

**Rojo (3):** Gamble · Jeska's Will · Underworld Breach

**Verde (7):** Biorhythm · Crop Rotation · Gaea's Cradle · Natural Order · Seedborn Muse · Survival of the Fittest · Worldly Tutor

**Multicolor (4):** Aura Shards · Coalition Victory · Grand Arbiter Augustin IV · Notion Thief

**Incoloras y tierras (12):** Ancient Tomb · Chrome Mox · Field of the Dead · Glacial Chasm · Grim Monolith · Lion's Eye Diamond · Mana Vault · Mishra's Workshop · Mox Diamond · Panoptic Mirror · The One Ring · The Tabernacle at Pendrell Vale

**Ya no son Game Changers** (retiradas en octubre de 2025; no contarlas): Expropriate · Jin-Gitaxias, Core Augur · Sway of the Stars · Vorinclex, Voice of Hunger · Kinnan, Bonder Prodigy · Urza, Lord High Artificer · Winota, Joiner of Forces · Yuriko, the Tiger's Shadow · Deflecting Swat · Food Chain

---

## 4. Cómo deducir el bracket

El bracket se calcula en dos capas: un **suelo** objetivo (lo que el deck no puede bajar de ningún modo) y una **estimación** de cómo juega realmente. El resultado final es el mayor de los dos.

### 4.1 Suelo: señales duras

El código las calcula y se las pasa a Claude ya contadas. Claude las confirma y las explica, pero no las recalcula de memoria.

| Señal | Suelo mínimo |
|---|---|
| 1–3 Game Changers | Bracket 3 |
| 4+ Game Changers | Bracket 4 |
| Destrucción masiva de tierras (Armageddon, Ravages of War, Winter Orb y similares: efectos que destruyen, bloquean o impiden enderezar muchas tierras) | Bracket 4 |
| Cartas de turno extra que se pueden **encadenar** (recursión, copias, varias cartas de turno extra con forma de repetirlas) | Bracket 4 |
| Alguna carta de turno extra suelta | Bracket 2 (no es bracket 1) |
| Combo de 2 cartas que gana o es infinito, **montable antes del turno 6** (piezas baratas, tutores para buscarlas) | Bracket 4 |
| Combo de 2 cartas que gana o es infinito, **solo viable tarde** | Bracket 3 |

Notas:
- **Combos:** llegan ya verificados contra Commander Spellbook en `bracket_suelo.combos` (lista de `{cartas, produce, descripcion, velocidad}`; `velocidad` es `"temprano"` o `"tardío"`, una heurística por coste de maná combinado de las piezas — trátala como aproximada, no como una certeza absoluta sobre cuándo se puede montar en la práctica). El suelo que corresponde a cada velocidad ya está aplicado en `floor`/`razones_suelo`: no lo vuelvas a calcular. Si `combos` está vacío, no inventes combos de memoria — di que no se detectó ninguno en el pool verificado. Solo señala un combo que no aparezca en esa lista si tienes mucha seguridad, y dilo explícitamente como **no verificado**.
- **Destrucción masiva de tierras:** el código marca candidatas por el texto oracle; Claude confirma si realmente lo son (Field of the Dead no es destrucción de tierras; Armageddon sí).
- Una señal dura aislada en un deck claramente casual se informa como **infracción puntual**, no se ignora: el suelo se aplica, pero Claude explica que bastaría con cambiar esa carta para bajar de bracket.

### 4.2 Estimación: señales blandas

Con el suelo fijado, Claude estima cómo juega el deck usando el análisis de `deckbuilding.md`:

| Señal | Bracket 1–2 | Bracket 3 | Bracket 4–5 |
|---|---|---|---|
| **Turno de victoria** con la mesa típica (sección 8 de `deckbuilding.md`) | 8–9 o más, o sin camino claro | 6–7 | 4–5 o antes |
| **Camino a la victoria** | Temático, poco a poco, visible y fácil de interrumpir | Claro; puede ganar en un turno grande tras acumular recursos | Eficiente, casi instantáneo, a menudo desde la mano |
| **Maná rápido** (rocas de 0–2 que dan más de 1, rituales) | Sol Ring y poco más | Algunas piezas | Mucho |
| **Tutores** | Pocos o ninguno | Algunos, sobre todo para el plan | Muchos y eficientes |
| **Interacción** | Escasa, lenta o de sorcery | Eficiente, algo de instantánea | Barata, instantánea, interrupción gratuita |
| **Calidad de cartas** | Muchas cartas por tema o diversión | Sinergia alta y buena calidad | Optimización por cada hueco |
| **Curva media** (sin tierras) | ≥ 3,5 | ~3–3,5 | ≤ 3 (cEDH, a menudo < 2,5) |

Reglas:
- **Bracket 1** solo si el deck es claramente temático o deliberadamente débil. Un deck simplemente flojo y sin tema es bracket 2.
- **Bracket 5** solo si el deck parece construido para el metajuego cEDH: casi todo el maná rápido disponible, interrupción gratuita, combo compacto, curva muy baja. Ante la duda entre 4 y 5, di **"4 (posible 5)"** y explica qué falta para confirmarlo.
- Un deck con **0 Game Changers puede ser bracket 3** si su sinergia, calidad y velocidad lo justifican. No asumas bracket 2 solo porque no lleva Game Changers.

### 4.3 Resultado

- **Bracket final** = el mayor entre el suelo y la estimación.
- **Confianza**: alta cuando suelo y estimación coinciden; media o baja cuando hay una sola señal dura en un deck casual, o cuando la estimación depende de un combo no verificado.
- **Razones**: las 2–4 señales que más pesan.
- **Qué lo movería**: los cambios concretos que subirían o bajarían un bracket (por ejemplo: "quitando Cyclonic Rift y Rhystic Study pasa a 0 Game Changers; con su curva y su camino a la victoria jugaría como un bracket 2 alto").

---

## 5. Formato de salida

Añadir al JSON del análisis:

```json
"bracket": {
  "deducido": 3,
  "confianza": "alta | media | baja",
  "suelo": 3,
  "estimacion_juego": 3,
  "game_changers": ["Rhystic Study", "Smothering Tithe"],
  "senales_duras": [
    { "tipo": "game_changers", "detalle": "2 Game Changers → mínimo bracket 3" }
  ],
  "razones": ["string"],
  "que_lo_moveria": {
    "bajar": ["string"],
    "subir": ["string"]
  }
}
```
