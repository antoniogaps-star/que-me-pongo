import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { listGarments } from "@/features/closet/api";

import {
  OCASIONES,
  PROYECCIONES,
  type Recomendacion,
  type Sugerencia,
  recomendar,
  saveOutfit,
} from "./api";

/**
 * El asesor en el escritorio: eliges ocasión y qué quieres proyectar, y te arma el
 * conjunto con TUS prendas, explicando por qué funciona.
 */
export function AdvisorPage() {
  const [ocasion, setOcasion] = useState<string>("dia normal");
  const [proyeccion, setProyeccion] = useState<string>("");
  const [resultado, setResultado] = useState<Recomendacion | null>(null);
  const [error, setError] = useState("");

  const prendas = useQuery({ queryKey: ["garments"], queryFn: listGarments });

  const pedir = useMutation({
    mutationFn: (sorpresa: boolean) =>
      recomendar({
        occasion: ocasion,
        projection: proyeccion,
        surprise: sorpresa,
      }),
    onSuccess: (r) => {
      setResultado(r);
      setError("");
    },
    onError: (e: unknown) => {
      setResultado(null);
      setError(mensajeDeError(e));
    },
  });

  const nombrePorId = new Map((prendas.data ?? []).map((p) => [p.id, p]));

  return (
    <div className="page">
      <h1>¿Qué me pongo?</h1>
      <p className="landing-note" style={{ marginTop: "-0.2rem" }}>
        Solo uso prendas que están en tu clóset. Nunca te recomiendo ropa que no tienes.
      </p>

      <section className="card" style={{ marginTop: "1.5rem" }}>
        <h2>¿Para qué ocasión?</h2>
        <div className="chips">
          {Object.entries(OCASIONES).map(([clave, texto]) => (
            <button
              key={clave}
              type="button"
              className={`chip${ocasion === clave ? " on" : ""}`}
              onClick={() => setOcasion(clave)}
            >
              {texto}
            </button>
          ))}
        </div>

        <h2 style={{ marginTop: "1.7rem" }}>¿Qué quieres proyectar?</h2>
        <p className="landing-note" style={{ margin: "0 0 0.3rem" }}>
          Opcional — si lo dejas en blanco, lo decido por la ocasión.
        </p>
        <div className="chips">
          {PROYECCIONES.map((p) => (
            <button
              key={p}
              type="button"
              className={`chip${proyeccion === p ? " on" : ""}`}
              // Volver a tocar el mismo quita la selección.
              onClick={() => setProyeccion(proyeccion === p ? "" : p)}
            >
              {p}
            </button>
          ))}
        </div>

        {error && <p className="error">{error}</p>}

        <div className="row" style={{ marginTop: "1.5rem" }}>
          <button
            type="button"
            style={{ flex: 1, marginTop: 0 }}
            disabled={pedir.isPending}
            onClick={() => pedir.mutate(false)}
          >
            {pedir.isPending ? "Pensando…" : "Vísteme"}
          </button>
          <button
            type="button"
            className="secondary"
            style={{ flex: "0 0 auto", marginTop: 0, width: "auto", padding: "0.75rem 1.4rem" }}
            disabled={pedir.isPending}
            onClick={() => pedir.mutate(true)}
          >
            🎲 Sorpréndeme
          </button>
        </div>
      </section>

      {resultado?.outfits.map((sugerencia, i) => (
        <TarjetaOutfit
          key={i}
          sugerencia={sugerencia}
          ocasion={ocasion}
          nombres={sugerencia.garment_ids.map(
            (id) => nombrePorId.get(id)?.name ?? "Prenda",
          )}
        />
      ))}

      {resultado && resultado.source !== "claude" && (
        <p className="aviso-reglas">
          ⚠ Sin conexión al asesor: esta es una combinación básica por reglas.
        </p>
      )}
    </div>
  );
}

function TarjetaOutfit({
  sugerencia,
  ocasion,
  nombres,
}: {
  sugerencia: Sugerencia;
  ocasion: string;
  nombres: string[];
}) {
  const qc = useQueryClient();
  const [guardado, setGuardado] = useState(false);

  const guardar = useMutation({
    mutationFn: () =>
      saveOutfit({
        garment_ids: sugerencia.garment_ids,
        occasion: ocasion,
        projection: sugerencia.projected_image,
        explanation: sugerencia.explanation,
      }),
    onSuccess: () => {
      setGuardado(true);
      qc.invalidateQueries({ queryKey: ["outfits"] });
    },
  });

  return (
    <section className="card">
      <ul style={{ margin: "0 0 1.2rem", paddingLeft: "1.1rem" }}>
        {nombres.map((n, i) => (
          <li key={i} style={{ marginBottom: "0.3rem" }}>
            {n}
          </li>
        ))}
      </ul>

      {sugerencia.projected_image && (
        <>
          <span className="proyeccion-label">Imagen que proyectas</span>
          <p className="proyeccion">{sugerencia.projected_image}</p>
        </>
      )}

      <p className="explicacion">{sugerencia.explanation}</p>

      <button
        type="button"
        className="secondary"
        style={{ width: "auto", padding: "0.55rem 1.2rem" }}
        disabled={guardado || guardar.isPending}
        onClick={() => guardar.mutate()}
      >
        {guardado ? "★ Guardado" : "☆ Me gusta"}
      </button>
    </section>
  );
}

/** Traduce los errores del servidor a algo accionable para el usuario. */
function mensajeDeError(e: unknown): string {
  const texto = JSON.stringify(e ?? "");
  if (texto.includes("EMPTY_CLOSET")) {
    return "Tu clóset está vacío. Agrega tu primera prenda para que pueda vestirte.";
  }
  if (texto.includes("NOT_ENOUGH_GARMENTS")) {
    return "Aún faltan prendas. Agrega al menos una de arriba, una de abajo y un calzado.";
  }
  return "No pude armar el conjunto. Revisa tu conexión e inténtalo de nuevo.";
}
