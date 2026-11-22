const MANA_CLASS: Record<string, string> = {
  W: "ms-w",
  U: "ms-u",
  B: "ms-b",
  R: "ms-r",
  G: "ms-g",
};

/** Icono real del símbolo de maná (fuente "Mana" de andrewgioia) en vez de
 * la letra suelta W/U/B/R/G. */
export function ManaIcon({ color }: { color: string }) {
  const cls = MANA_CLASS[color];
  if (!cls) return null;
  return <i className={`ms ${cls} ms-cost`} aria-hidden="true" />;
}
