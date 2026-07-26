import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import {
  CATEGORIAS,
  ESTILOS,
  TEMPORADAS,
  createGarment,
  deleteGarment,
  describeFormalidad,
  listGarments,
} from "./api";

const ICONOS: Record<string, string> = {
  arriba: "👕",
  abajo: "👖",
  abrigo: "🧥",
  calzado: "👞",
  accesorio: "⌚",
  completo: "🕴️",
};

/**
 * Mi clóset en el escritorio: alta y baja de prendas.
 *
 * Aquí NO se toman fotos — la cámara vive en el móvil. Este panel sirve para capturar
 * en lote (más cómodo con teclado) y para revisar el clóset en una pantalla grande.
 */
export function ClosetPage() {
  const qc = useQueryClient();
  const prendas = useQuery({ queryKey: ["garments"], queryFn: listGarments });

  const [nombre, setNombre] = useState("");
  const [color, setColor] = useState("");
  const [categoria, setCategoria] = useState<string>("arriba");
  const [estilos, setEstilos] = useState<string[]>([]);
  const [formalidad, setFormalidad] = useState(5);
  const [temporada, setTemporada] = useState("todo");
  const [error, setError] = useState("");

  const crear = useMutation({
    mutationFn: createGarment,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["garments"] });
      setNombre("");
      setColor("");
      setEstilos([]);
      setFormalidad(5);
      setError("");
    },
    onError: () => setError("No se pudo guardar la prenda. Revisa tu conexión."),
  });

  const borrar = useMutation({
    mutationFn: deleteGarment,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["garments"] }),
  });

  function alternarEstilo(e: string) {
    setEstilos((previos) =>
      previos.includes(e) ? previos.filter((x) => x !== e) : [...previos, e],
    );
  }

  function guardar(evento: React.FormEvent) {
    evento.preventDefault();
    if (!nombre.trim()) {
      setError("Ponle un nombre a la prenda.");
      return;
    }
    crear.mutate({
      category: categoria,
      name: nombre.trim(),
      color: color.trim() || null,
      styles: estilos,
      formality: formalidad,
      season: temporada,
    });
  }

  return (
    <div className="page">
      <h1>Mi clóset</h1>
      <p className="landing-note" style={{ marginTop: "-0.2rem" }}>
        Las fotos se toman desde la app del celular. Aquí puedes capturar prendas en lote
        y revisarlas en pantalla grande.
      </p>

      <section className="card" style={{ marginTop: "1.5rem" }}>
        <h2>Agregar prenda</h2>
        <form onSubmit={guardar}>
          <label htmlFor="nombre">Nombre de la prenda</label>
          <input
            id="nombre"
            value={nombre}
            onChange={(e) => setNombre(e.target.value)}
            placeholder="Camisa azul marino"
          />

          <label htmlFor="color">Color</label>
          <input
            id="color"
            value={color}
            onChange={(e) => setColor(e.target.value)}
            placeholder="Azul marino"
          />

          <label>¿Qué es?</label>
          <div className="chips">
            {Object.entries(CATEGORIAS).map(([clave, texto]) => (
              <button
                key={clave}
                type="button"
                className={`chip${categoria === clave ? " on" : ""}`}
                onClick={() => setCategoria(clave)}
              >
                {ICONOS[clave]} {texto}
              </button>
            ))}
          </div>

          <label style={{ marginTop: "1.1rem" }}>Estilos que le quedan</label>
          <div className="chips">
            {ESTILOS.map((e) => (
              <button
                key={e}
                type="button"
                className={`chip${estilos.includes(e) ? " on" : ""}`}
                onClick={() => alternarEstilo(e)}
              >
                {e[0].toUpperCase() + e.slice(1)}
              </button>
            ))}
          </div>

          <label htmlFor="formalidad" style={{ marginTop: "1.1rem" }}>
            ¿Qué tan formal es? — {describeFormalidad(formalidad)}
          </label>
          <input
            id="formalidad"
            type="range"
            min={1}
            max={10}
            value={formalidad}
            onChange={(e) => setFormalidad(Number(e.target.value))}
          />

          <label style={{ marginTop: "0.6rem" }}>¿Para qué clima?</label>
          <div className="chips">
            {Object.entries(TEMPORADAS).map(([clave, texto]) => (
              <button
                key={clave}
                type="button"
                className={`chip${temporada === clave ? " on" : ""}`}
                onClick={() => setTemporada(clave)}
              >
                {texto}
              </button>
            ))}
          </div>

          {error && <p className="error">{error}</p>}
          <button type="submit" disabled={crear.isPending}>
            {crear.isPending ? "Guardando…" : "Guardar en mi clóset"}
          </button>
        </form>
      </section>

      <h2 style={{ marginTop: "2rem" }}>
        {prendas.data ? `${prendas.data.length} prendas` : "Prendas"}
      </h2>

      {prendas.isLoading && <p className="empty">Cargando tu clóset…</p>}
      {prendas.data?.length === 0 && (
        <p className="empty">
          Tu clóset está vacío. Agrega tu primera prenda aquí arriba, o tómale una foto
          desde la app del celular.
        </p>
      )}

      <div className="closet-grid">
        {prendas.data?.map((p) => (
          <article key={p.id} className="prenda">
            <div className="marco">{ICONOS[p.category] ?? "👕"}</div>
            <span className="nombre">{p.name}</span>
            <span className="meta">
              {CATEGORIAS[p.category as keyof typeof CATEGORIAS] ?? p.category}
              {p.color ? ` · ${p.color}` : ""}
            </span>
            <span className="meta">
              {describeFormalidad(p.formality)}
              {p.styles.length > 0 ? ` · ${p.styles.join(" · ")}` : ""}
            </span>
            <div className="acciones">
              <button
                type="button"
                className="linkbtn"
                onClick={() => borrar.mutate(p.id)}
              >
                Quitar
              </button>
            </div>
          </article>
        ))}
      </div>
    </div>
  );
}
