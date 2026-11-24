import { Suspense } from "react";
import { notFound } from "next/navigation";
import sampleIndex from "../../../../../public/samples/index.json";
import { AnalyzerApp } from "../../../components/AnalyzerApp";
import type { SampleIndexEntry } from "../../../lib/sampleAnalyses";

/** `/analizar/ejemplo/<id>`: abre un análisis de ejemplo de public/samples/.
 * Al ser una ruta propia (y no `/analizar?ejemplo=`), el servidor ya sabe que
 * viene un ejemplo y pinta "Cargando…" en vez del formulario.
 *
 * El índice se importa como módulo JSON (resuelto al compilar) en vez de
 * leerse con fs: con Cache Components, un acceso a disco sin caché durante
 * el render impide prerenderizar la página. */
const SAMPLES: SampleIndexEntry[] = sampleIndex;

// Con Cache Components tiene que devolver al menos un id: se prerenderiza
// una página por cada ejemplo publicado en public/samples/index.json.
export function generateStaticParams() {
  return SAMPLES.map((entry) => ({ id: entry.id }));
}

function SampleAnalyzer({ id }: { id: string }) {
  if (!SAMPLES.some((entry) => entry.id === id)) notFound();
  return <AnalyzerApp initialSampleId={id} />;
}

// `params` se lee dentro de Suspense (lo pide Cache Components para que la
// navegación sea instantánea); el fallback es el mismo "Cargando…" que pinta
// el analizador, así que el relevo no se ve.
export default function SamplePage({ params }: PageProps<"/analizar/ejemplo/[id]">) {
  return (
    <Suspense fallback={<AnalyzerApp sampleLoadingPlaceholder />}>
      {params.then(({ id }) => (
        <SampleAnalyzer id={id} />
      ))}
    </Suspense>
  );
}
