import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import { listOutfits } from "@/features/advisor/api";
import { CATEGORIAS, listGarments } from "@/features/closet/api";

import { fetchMe } from "./api";

/** Portada del panel: el estado del clóset de un vistazo y el acceso al asesor. */
export function DashboardPage() {
  const me = useQuery({ queryKey: ["me"], queryFn: fetchMe });
  const prendas = useQuery({ queryKey: ["garments"], queryFn: listGarments });
  const favoritos = useQuery({ queryKey: ["outfits"], queryFn: listOutfits });

  const lista = prendas.data ?? [];
  const porCategoria = new Map<string, number>();
  for (const p of lista) {
    porCategoria.set(p.category, (porCategoria.get(p.category) ?? 0) + 1);
  }

  // Para vestir a alguien hace falta, como mínimo, arriba + abajo + calzado.
  const faltantes = (["arriba", "abajo", "calzado"] as const).filter(
    (c) => (porCategoria.get(c) ?? 0) === 0,
  );

  return (
    <div className="page">
      <h1>Inicio</h1>
      <p className="landing-note" style={{ marginTop: "-0.2rem" }}>
        {me.data ? `Hola, ${me.data.email}.` : "Bienvenido."} Tu clóset, de un vistazo.
      </p>

      <div className="stat-grid" style={{ margin: "1.5rem 0" }}>
        <div className="stat">
          <div className="value">{lista.length}</div>
          <div className="label">Prendas en tu clóset</div>
        </div>
        <div className="stat">
          <div className="value">{favoritos.data?.length ?? "—"}</div>
          <div className="label">Conjuntos favoritos</div>
        </div>
        <div className="stat">
          <div className="value">{porCategoria.size}</div>
          <div className="label">Categorías cubiertas</div>
        </div>
      </div>

      {faltantes.length > 0 && lista.length > 0 && (
        <section className="card">
          <h2>Para poder vestirte me falta…</h2>
          <p className="explicacion">
            Agrega al menos una prenda de:{" "}
            {faltantes.map((c) => (CATEGORIAS[c] ?? c).toLowerCase()).join(", ")}. Con eso
            ya puedo armarte un conjunto completo.
          </p>
          <Link to="/closet" className="landing-btn landing-btn-ghost">
            Ir a mi clóset
          </Link>
        </section>
      )}

      {lista.length === 0 && (
        <section className="card">
          <h2>Tu clóset está vacío</h2>
          <p className="explicacion">
            Toma la foto de tus prendas desde la app del celular, o captúralas aquí si
            prefieres el teclado. Con tres o cuatro ya puedo vestirte.
          </p>
          <Link to="/closet" className="landing-btn landing-btn-primary">
            Agregar mi primera prenda
          </Link>
        </section>
      )}

      {lista.length > 0 && (
        <section className="card">
          <h2>Qué tienes</h2>
          <table>
            <thead>
              <tr>
                <th>Categoría</th>
                <th>Prendas</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(CATEGORIAS).map(([clave, texto]) => (
                <tr key={clave}>
                  <td>{texto}</td>
                  <td>{porCategoria.get(clave) ?? 0}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}

      <Link to="/asesor" className="landing-btn landing-btn-primary">
        ¿Qué me pongo hoy?
      </Link>
    </div>
  );
}
