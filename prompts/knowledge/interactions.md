# Interacciones no obvias entre mecánicas

Este documento recoge implicaciones de reglas que un jugador con experiencia
dactiva sin pensarlo, pero que no están escritas literalmente en el texto de
una carta. Dos cartas pueden tener sinergia real aunque **ninguna mencione a
la otra ni compartan palabra clave** — la conexión está en lo que la regla
implica, no en el texto de superficie.

Úsalo para no evaluar una carta solo por su efecto principal, sobre todo
antes de proponer un corte: si el **coste** o un **efecto secundario** de la
carta alimenta un motor del deck, puede ser una pieza querida aunque su
efecto de superficie parezca ajeno al arquetipo.

## 1. Qué termina en el cementerio (y qué no)

- **Descartar una carta** (como coste o como efecto, propio o ajeno) la
  manda al cementerio salvo que el texto diga explícitamente lo contrario
  (p. ej. "exilia la carta descartada"). Alimenta flashback, aftermath,
  jump-start, madness (de la carta descartada), disturb, escape, delve,
  threshold, umbral/cuenta de cartas en el cementerio.
- **Mill / poner cartas de la biblioteca en el cementerio** alimenta lo
  mismo que descartar: reanimación, flashback, delve, threshold.
- **Sacrificar una criatura o permanente** lo manda al cementerio (salvo
  que el efecto diga "exilia") y **además** dispara cualquier "muere" /
  "deja el campo de batalla" / "es sacrificada". Esto alimenta dos motores
  a la vez: reanimación y aristócratas (death triggers), aunque la carta
  nunca vuelva a la mesa.
- **Una criatura que muere en combate o por un hechizo** va al cementerio
  igual que si se sacrificara: dispara los mismos "muere" que un sacrificio
  deliberado. Un deck con removal/wipes propio alimenta su propio motor de
  aristócratas tanto como uno con sacrificio directo.
- **Exiliar NO alimenta el cementerio.** Impulsive draw ("exile the top
  card of your library, you may play it this turn"), suspend, foretell,
  plot, cascade, cartas que dicen "exile" en vez de "put into graveyard":
  nada de esto deja una carta en el cementerio. No asumas sinergia con
  reanimación/flashback a menos que la carta vuelva primero al cementerio
  o la mecánica lo diga explícitamente (p. ej. foretell sí permite
  lanzarla después desde el exilio, pero no la pone en el cementerio).

## 2. Sacrificar y morir no son solo "alimentar el cementerio"

- Un death trigger ("whenever a creature you control dies") se dispara
  tanto si la criatura muere en combate, por un hechizo, como si se
  sacrifica a propósito. Un deck de aristócratas no necesita sacrificio
  dedicado si ya tiene remoción/wipes propios o combate agresivo.
- "Sacrificar" y "la criatura muere" no son sinónimos para efectos que
  cuidan específicamente de uno u otro (p. ej. "whenever you sacrifice a
  permanent" no se dispara si la criatura simplemente muere en combate).
  Distíngelos al razonar sobre qué dispara qué.

## 3. Costes que parecen penalizaciones pero alimentan algo

- **Pagar vida / perder vida** (como coste o efecto) alimenta payoffs de
  vida perdida (p. ej. devociones a dioses de vida, drenaje, umbral de
  vida), independientemente de si la carta menciona esos payoffs.
- **Tapear criaturas como coste** (convoke, costes de activación) compite
  con tenerlas listas para bloquear o atacar; la vigilancia soluciona esa
  tensión sin texto que mencione "convoke" ni "tap".
- **Exiliar cartas propias de la mano o la biblioteca como coste** (p. ej.
  algunos costes alternativos) alimenta "cast from exile" si otra carta lo
  permite, igual que el impulsive draw del punto 1.

## 4. Contadores y "mejorar cosas" no siempre significan lo que parece

- **Proliferate** avanza *todos* los contadores que ya existan sobre
  permanentes y jugadores: +1/+1, lealtad, veneno, carga, experiencia. Un
  deck con contadores de veneno propios puede llevarse un proliferate ajeno
  igual que uno pensado para +1/+1 — y al revés, cuidado con proliferate en
  una mesa con venganza/veneno de otro jugador.
- **Duplicar una criatura** (clonarla o copiarla, no crear un token
  genérico) vuelve a disparar sus "enters the battlefield". Duplicar un
  **hechizo de un solo uso** (instantáneo/sorcery) repite su efecto una
  vez más; no crea una criatura ni dura en el campo de batalla salvo que
  la carta original lo haga.

## 5. No basta con la palabra clave: comprueba los números

Que dos cartas compartan una palabra ("token", "entra al campo de
batalla") no significa que la sinergia rinda lo que parece. Antes de
afirmar que una carta alimenta un payoff del deck, comprueba los números
concretos de ambas:

- **"Deals damage equal to that creature's power"** (Terror of the
  Peaks y similares) escala con el **poder** del token/criatura que
  entra, no con que "sea una criatura que entra". Un token de poder 0
  (p. ej. un Clue-maker que también crea un 0/X, un token defensivo)
  dispara el efecto por **0 de daño**: la palabra "dispara" es literal
  pero el resultado es nulo. Esto es distinto de triggers de daño **fijo**
  ("deals 1 damage to each opponent", Impact Tremors) o que no dependen
  del poder (ganar vida, energía): esos sí rinden igual con cualquier
  token, poder 0 incluido. No generalices "genera un token → sinergiza
  con los payoffs de ETB del deck" sin mirar qué pide cada payoff en
  concreto.
- Si el plan del deck es **tokens de criatura atacando** (para payoffs de
  combate, duplicadores que buscan más atacantes), un generador de
  **tokens que no atacan de forma realista** (defensivos, 0 de poder,
  artefactos tipo Clue/Treasure que ni siquiera son criaturas) no sirve
  ese plan aunque el deck tenga duplicadores de tokens genéricos. Un
  duplicador de tokens no convierte un token que no encaja en uno que sí
  — multiplica lo que sea, pero el jugador seguía queriendo *ese* tipo de
  token.
- Antes de recomendar un añadido citando un payoff concreto del deck como
  motivo, confirma que el añadido de verdad alimenta ESE payoff con los
  números que tiene, no solo que comparte categoría con él.

## 6. Cómo escala un efecto con el número de rivales

- Un disparador del tipo **"whenever an opponent..."** / "cada vez que un
  rival hace X" se dispara **una vez por cada rival que cumpla la
  condición**, no una vez por turno propio. En una mesa de 3 rivales rinde
  **más** que en un 1 contra 1, no menos: más jugadores → más
  oportunidades de disparo. No asumas que "más rivales" diluye el valor
  de una carta con este patrón — normalmente es al revés. Ejemplo real:
  Esper Sentinel ("whenever an opponent casts their first noncreature
  spell each turn, draw a card unless...") puede robar hasta una carta
  por cada rival cada ronda; con 3 rivales es *mejor*, no peor, que en 1
  contra 1.
- Esto no aplica a disparadores por turno **propio** ("at the beginning
  of your upkeep", "whenever you cast...") ni a los que se disparan **una
  vez por turno de cualquiera** (esos sí rinden menos cuantos más
  jugadores compitan por disparar primero).
- Tampoco aplica si el rival puede **evitar pagar el coste** de forma
  trivial (p. ej. Esper Sentinel: X es el poder de la criatura, así que
  un X bajo hace fácil que el rival pague y no cuente como robo real) —
  eso sí reduce su fiabilidad, pero por el coste a pagar, no por el
  número de rivales en la mesa.

## 7. Cómo usar esto

- Antes de cortar una carta, comprueba si su **coste** (no solo su efecto)
  conecta con alguno de los puntos de arriba y con lo que el deck ya hace.
- Si decides mantenerla o la citas como punto fuerte, señala la conexión
  indirecta en el motivo (p. ej. "su coste de descarte alimenta la
  recursión de cementerio del comandante") en vez de evaluarla solo por su
  efecto de superficie.
- No fuerces una conexión que no existe: si una carta de verdad no aporta
  nada al plan ni por su coste ni por su efecto, sigue siendo un corte
  razonable.
