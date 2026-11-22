"use client";

import { useId, useState, type FormEvent } from "react";
import { ResultsView } from "./components/ResultsView";
import { AnalyzeRequest, AnalyzeResponse } from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export default function Home() {
  const deckTextId = useId();
  const bracketId = useId();
  const budgetId = useId();
  const styleId = useId();
  const avoidId = useId();
  const aiId = useId();

  const [deckText, setDeckText] = useState("");
  const [bracket, setBracket] = useState("");
  const [budget, setBudget] = useState("");
  const [style, setStyle] = useState<AnalyzeRequest["style"]>("casual");
  const [allowCombos, setAllowCombos] = useState(false);
  const [avoid, setAvoid] = useState("");
  const [ai, setAi] = useState(false);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<AnalyzeResponse | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError(null);

    const body: AnalyzeRequest = {
      deck_text: deckText,
      bracket: bracket ? Number(bracket) : undefined,
      budget: budget ? Number(budget) : undefined,
      style,
      allow_combos: allowCombos,
      avoid: avoid
        .split(",")
        .map((item) => item.trim())
        .filter(Boolean),
      ai,
    };

    try {
      const response = await fetch(`${API_URL}/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });

      if (!response.ok) {
        const payload = await response.json().catch(() => null);
        throw new Error(payload?.detail ?? `Error ${response.status} al analizar el deck.`);
      }

      setResult(await response.json());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error desconocido al analizar el deck.");
      setResult(null);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="mx-auto max-w-4xl w-full px-4 py-8 flex flex-col gap-8">
      <header>
        <h1 className="text-2xl font-bold" style={{ color: "var(--foreground)" }}>
          MTG Commander Deck Analyzer
        </h1>
        <p style={{ color: "var(--ink-secondary)" }}>
          Pega la lista de tu deck de Commander/EDH para ver sus métricas y, si lo pides, un análisis de Claude.
        </p>
      </header>

      <form onSubmit={handleSubmit} aria-labelledby="analyze-form-heading" className="flex flex-col gap-4">
        <h2 id="analyze-form-heading" className="sr-only">
          Formulario de análisis de deck
        </h2>

        <div className="flex flex-col gap-1">
          <label htmlFor={deckTextId} style={{ color: "var(--foreground)" }}>
            Lista del deck
          </label>
          <textarea
            id={deckTextId}
            name="deck_text"
            required
            rows={12}
            placeholder={"Commander:\n1 Atraxa, Praetors' Voice\n\nDeck:\n1 Sol Ring\n..."}
            value={deckText}
            onChange={(e) => setDeckText(e.target.value)}
            className="rounded-lg border p-3 font-mono text-sm"
            style={{ borderColor: "var(--border)", background: "var(--surface)", color: "var(--foreground)" }}
          />
        </div>

        <fieldset className="rounded-lg border p-4 flex flex-col gap-3" style={{ borderColor: "var(--border)" }}>
          <legend className="px-1 font-semibold" style={{ color: "var(--foreground)" }}>
            Parámetros
          </legend>

          <div className="grid sm:grid-cols-3 gap-3">
            <div className="flex flex-col gap-1">
              <label htmlFor={bracketId} style={{ color: "var(--foreground)" }}>
                Bracket (1-5)
              </label>
              <input
                id={bracketId}
                name="bracket"
                type="number"
                min={1}
                max={5}
                inputMode="numeric"
                value={bracket}
                onChange={(e) => setBracket(e.target.value)}
                className="rounded-lg border p-2"
                style={{ borderColor: "var(--border)", background: "var(--surface)", color: "var(--foreground)" }}
              />
            </div>

            <div className="flex flex-col gap-1">
              <label htmlFor={budgetId} style={{ color: "var(--foreground)" }}>
                Presupuesto máx. ($)
              </label>
              <input
                id={budgetId}
                name="budget"
                type="number"
                min={0}
                step="0.01"
                inputMode="decimal"
                value={budget}
                onChange={(e) => setBudget(e.target.value)}
                className="rounded-lg border p-2"
                style={{ borderColor: "var(--border)", background: "var(--surface)", color: "var(--foreground)" }}
              />
            </div>

            <div className="flex flex-col gap-1">
              <label htmlFor={styleId} style={{ color: "var(--foreground)" }}>
                Estilo
              </label>
              <select
                id={styleId}
                name="style"
                value={style}
                onChange={(e) => setStyle(e.target.value as AnalyzeRequest["style"])}
                className="rounded-lg border p-2"
                style={{ borderColor: "var(--border)", background: "var(--surface)", color: "var(--foreground)" }}
              >
                <option value="casual">Casual</option>
                <option value="focused">Focused</option>
                <option value="cedh">cEDH</option>
              </select>
            </div>
          </div>

          <div className="flex flex-col gap-1">
            <label htmlFor={avoidId} style={{ color: "var(--foreground)" }}>
              Cartas o mecánicas a evitar (separadas por comas)
            </label>
            <input
              id={avoidId}
              name="avoid"
              type="text"
              value={avoid}
              onChange={(e) => setAvoid(e.target.value)}
              className="rounded-lg border p-2"
              style={{ borderColor: "var(--border)", background: "var(--surface)", color: "var(--foreground)" }}
            />
          </div>

          <div className="flex items-center gap-2">
            <input
              id="allow-combos"
              name="allow_combos"
              type="checkbox"
              checked={allowCombos}
              onChange={(e) => setAllowCombos(e.target.checked)}
            />
            <label htmlFor="allow-combos" style={{ color: "var(--foreground)" }}>
              Permitir sugerir combos
            </label>
          </div>

          <div className="flex items-center gap-2">
            <input id={aiId} name="ai" type="checkbox" checked={ai} onChange={(e) => setAi(e.target.checked)} />
            <label htmlFor={aiId} style={{ color: "var(--foreground)" }}>
              Pedir análisis de Claude (requiere ANTHROPIC_API_KEY en el servidor)
            </label>
          </div>
        </fieldset>

        <button
          type="submit"
          disabled={loading}
          className="self-start rounded-lg px-4 py-2 font-semibold text-white disabled:opacity-60"
          style={{ background: "var(--chart-mana)" }}
        >
          {loading ? "Analizando..." : "Analizar deck"}
        </button>
      </form>

      <div role="status" aria-live="polite">
        {error && (
          <p className="rounded-lg border p-3" style={{ borderColor: "var(--status-critical)", color: "var(--foreground)" }}>
            {error}
          </p>
        )}
      </div>

      {result && <ResultsView result={result} />}
    </main>
  );
}
