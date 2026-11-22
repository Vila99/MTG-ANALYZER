import { AnalyzeResponse, COLOR_LABELS, ROLE_LABELS } from "../types";
import { SingleSeriesBarChart } from "./SingleSeriesBarChart";

const RUBRIC_ORDER = ["land", "ramp", "draw", "removal", "wipe"];
const STATUS_LABEL: Record<string, string> = { bajo: "Bajo", ok: "Dentro de rango", alto: "Alto" };
const STATUS_COLOR_VAR: Record<string, string> = {
  bajo: "var(--status-warning)",
  ok: "var(--status-good)",
  alto: "var(--status-critical)",
};

function StatTile({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-lg border p-4" style={{ borderColor: "var(--border)", background: "var(--surface)" }}>
      <p className="text-sm" style={{ color: "var(--ink-secondary)" }}>
        {label}
      </p>
      <p className="text-2xl font-semibold" style={{ color: "var(--foreground)" }}>
        {value}
      </p>
    </div>
  );
}

export function ResultsView({ result }: { result: AnalyzeResponse }) {
  const manaCurveData = Object.entries(result.curva_mana)
    .sort((a, b) => Number(a[0]) - Number(b[0]))
    .map(([cmc, count]) => ({ label: cmc, value: count }));

  const rolesData = Object.entries(result.roles)
    .filter(([role]) => role !== "other")
    .map(([role, count]) => ({ label: ROLE_LABELS[role] ?? role, value: count }));

  return (
    <div className="flex flex-col gap-6">
      <section>
        <h2 className="text-lg font-semibold mb-2" style={{ color: "var(--foreground)" }}>
          Comandante{result.comandantes.length > 1 ? "s" : ""}
        </h2>
        {result.comandantes.length > 0 ? (
          <ul className="list-disc list-inside" style={{ color: "var(--ink-secondary)" }}>
            {result.comandantes.map((name) => (
              <li key={name}>{name}</li>
            ))}
          </ul>
        ) : (
          <p style={{ color: "var(--ink-muted)" }}>No se detectó comandante.</p>
        )}
      </section>

      <section className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <StatTile label="Tamaño del deck" value={result.tamano_deck} />
        <StatTile label="Tierras" value={result.tierras} />
        <StatTile label="CMC medio" value={result.cmc_medio.toFixed(2)} />
        <StatTile label="Cartas no encontradas" value={result.no_encontradas.length} />
      </section>

      {(result.no_encontradas.length > 0 || result.no_legales.length > 0) && (
        <section
          className="rounded-lg border p-4"
          style={{ borderColor: "var(--status-critical)", background: "var(--surface)" }}
        >
          {result.no_encontradas.length > 0 && (
            <p style={{ color: "var(--foreground)" }}>
              <strong>No encontradas:</strong> {result.no_encontradas.join(", ")}
            </p>
          )}
          {result.no_legales.length > 0 && (
            <p style={{ color: "var(--foreground)" }}>
              <strong>No legales en Commander:</strong> {result.no_legales.join(", ")}
            </p>
          )}
        </section>
      )}

      <section className="grid sm:grid-cols-2 gap-4">
        <SingleSeriesBarChart
          title="Curva de maná (sin tierras)"
          data={manaCurveData}
          colorVar="var(--chart-mana)"
          valueLabel="cartas"
        />
        <SingleSeriesBarChart
          title="Cartas por rol"
          data={rolesData}
          colorVar="var(--chart-roles)"
          valueLabel="cartas"
        />
      </section>

      <section>
        <h2 className="text-lg font-semibold mb-2" style={{ color: "var(--foreground)" }}>
          Comparación con el rubric base
        </h2>
        <div
          tabIndex={0}
          role="region"
          aria-labelledby="rubric-table-caption"
          className="table-wrapper overflow-auto rounded-lg border"
          style={{ borderColor: "var(--border)" }}
        >
          <table className="w-full text-sm">
            <caption id="rubric-table-caption" className="sr-only">
              Comparación de roles del deck contra el rubric de referencia
            </caption>
            <thead>
              <tr style={{ background: "var(--surface-muted)" }}>
                <th className="text-left p-2" style={{ color: "var(--ink-secondary)" }}>
                  Rol
                </th>
                <th className="text-left p-2" style={{ color: "var(--ink-secondary)" }}>
                  Cantidad
                </th>
                <th className="text-left p-2" style={{ color: "var(--ink-secondary)" }}>
                  Estado
                </th>
              </tr>
            </thead>
            <tbody>
              {RUBRIC_ORDER.map((role) => {
                const status = result.rubric[role];
                return (
                  <tr key={role} style={{ borderTop: "1px solid var(--border)" }}>
                    <th scope="row" className="text-left p-2 font-normal" style={{ color: "var(--foreground)" }}>
                      {ROLE_LABELS[role] ?? role}
                    </th>
                    <td className="p-2" style={{ color: "var(--foreground)" }}>
                      {result.roles[role] ?? 0}
                    </td>
                    <td className="p-2">
                      <span className="inline-flex items-center gap-1.5" style={{ color: "var(--foreground)" }}>
                        <span
                          aria-hidden="true"
                          className="inline-block w-2.5 h-2.5 rounded-full"
                          style={{ background: STATUS_COLOR_VAR[status] }}
                        />
                        {STATUS_LABEL[status] ?? status}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </section>

      <section>
        <h2 className="text-lg font-semibold mb-2" style={{ color: "var(--foreground)" }}>
          Pips vs. fuentes de maná por color
        </h2>
        <div
          tabIndex={0}
          role="region"
          aria-labelledby="pips-table-caption"
          className="table-wrapper overflow-auto rounded-lg border"
          style={{ borderColor: "var(--border)" }}
        >
          <table className="w-full text-sm">
            <caption id="pips-table-caption" className="sr-only">
              Pips de maná requeridos frente a fuentes disponibles, por color
            </caption>
            <thead>
              <tr style={{ background: "var(--surface-muted)" }}>
                <th className="text-left p-2" style={{ color: "var(--ink-secondary)" }}>
                  Color
                </th>
                <th className="text-left p-2" style={{ color: "var(--ink-secondary)" }}>
                  Pips
                </th>
                <th className="text-left p-2" style={{ color: "var(--ink-secondary)" }}>
                  Fuentes
                </th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(COLOR_LABELS).map(([code, label]) => (
                <tr key={code} style={{ borderTop: "1px solid var(--border)" }}>
                  <th scope="row" className="text-left p-2 font-normal" style={{ color: "var(--foreground)" }}>
                    {label}
                  </th>
                  <td className="p-2" style={{ color: "var(--foreground)" }}>
                    {result.pips[code] ?? 0}
                  </td>
                  <td className="p-2" style={{ color: "var(--foreground)" }}>
                    {result.fuentes_mana[code] ?? 0}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {result.analisis && (
        <section className="flex flex-col gap-4 rounded-lg border p-4" style={{ borderColor: "var(--border)", background: "var(--surface)" }}>
          <h2 className="text-lg font-semibold" style={{ color: "var(--foreground)" }}>
            Análisis de Claude
          </h2>
          <p style={{ color: "var(--foreground)" }}>
            <strong>Estrategia detectada:</strong> {result.analisis.estrategia_detectada}
          </p>
          <p style={{ color: "var(--foreground)" }}>
            <strong>Arquetipo:</strong> {result.analisis.arquetipo}
          </p>

          {result.analisis.puntos_fuertes.length > 0 && (
            <div>
              <h3 className="font-semibold mb-1" style={{ color: "var(--foreground)" }}>
                Puntos fuertes
              </h3>
              <ul className="list-disc list-inside" style={{ color: "var(--ink-secondary)" }}>
                {result.analisis.puntos_fuertes.map((punto, i) => (
                  <li key={i}>{punto}</li>
                ))}
              </ul>
            </div>
          )}

          {result.analisis.problemas.length > 0 && (
            <div>
              <h3 className="font-semibold mb-1" style={{ color: "var(--foreground)" }}>
                Problemas detectados
              </h3>
              <ul className="list-disc list-inside" style={{ color: "var(--ink-secondary)" }}>
                {result.analisis.problemas.map((problema, i) => (
                  <li key={i}>
                    <span
                      className="font-semibold"
                      style={{
                        color:
                          problema.severidad === "alta"
                            ? "var(--status-critical)"
                            : problema.severidad === "media"
                              ? "var(--status-warning)"
                              : "var(--ink-secondary)",
                      }}
                    >
                      [{problema.severidad}]
                    </span>{" "}
                    {problema.categoria}: {problema.explicacion}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {result.analisis.cortes_sugeridos.length > 0 && (
            <div>
              <h3 className="font-semibold mb-1" style={{ color: "var(--foreground)" }}>
                Cortes sugeridos
              </h3>
              <ul className="list-disc list-inside" style={{ color: "var(--ink-secondary)" }}>
                {result.analisis.cortes_sugeridos.map((cut, i) => (
                  <li key={i}>
                    <strong style={{ color: "var(--foreground)" }}>{cut.carta}</strong>: {cut.motivo}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {result.analisis.añadidos_sugeridos.length > 0 && (
            <div>
              <h3 className="font-semibold mb-1" style={{ color: "var(--foreground)" }}>
                Añadidos sugeridos
              </h3>
              <ul className="list-disc list-inside" style={{ color: "var(--ink-secondary)" }}>
                {result.analisis.añadidos_sugeridos.map((addition, i) => (
                  <li key={i}>
                    <strong style={{ color: "var(--foreground)" }}>{addition.carta}</strong> [{addition.rol}]
                    {addition.reemplaza_a ? ` (reemplaza a ${addition.reemplaza_a})` : ""}: {addition.motivo}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </section>
      )}
    </div>
  );
}
