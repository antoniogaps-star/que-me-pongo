import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { deleteOutfit, listOutfits } from "@/features/advisor/api";
import { listGarments } from "@/features/closet/api";

/** Los conjuntos que marcaste con ★, con la explicación que dio el asesor. */
export function FavoritesPage() {
  const qc = useQueryClient();
  const favoritos = useQuery({ queryKey: ["outfits"], queryFn: listOutfits });
  const prendas = useQuery({ queryKey: ["garments"], queryFn: listGarments });

  const quitar = useMutation({
    mutationFn: deleteOutfit,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["outfits"] }),
  });

  const porId = new Map((prendas.data ?? []).map((p) => [p.id, p]));

  return (
    <div className="page">
      <h1>Favoritos</h1>
      <p className="landing-note" style={{ marginTop: "-0.2rem" }}>
        Tus conjuntos guardados. También me sirven para el modo sorpresa: así te propongo
        algo distinto a lo que ya usas.
      </p>

      {favoritos.isLoading && <p className="empty">Cargando…</p>}
      {favoritos.data?.length === 0 && (
        <p className="empty">
          Sin favoritos todavía. Cuando un conjunto te guste, guárdalo con ★.
        </p>
      )}

      <div style={{ marginTop: "1.5rem" }}>
        {favoritos.data?.map((o) => (
          <section key={o.id} className="card">
            <span className="proyeccion-label">
              {o.occasion || "Conjunto guardado"}
            </span>
            {o.projection && <p className="proyeccion">{o.projection}</p>}

            <ul style={{ margin: "0 0 1rem", paddingLeft: "1.1rem" }}>
              {o.garment_ids.map((id) => (
                <li key={id} style={{ marginBottom: "0.25rem" }}>
                  {porId.get(id)?.name ?? "Prenda que ya no está en tu clóset"}
                </li>
              ))}
            </ul>

            {o.explanation && <p className="explicacion">{o.explanation}</p>}

            <button
              type="button"
              className="linkbtn"
              style={{ marginTop: "1rem" }}
              onClick={() => quitar.mutate(o.id)}
            >
              Quitar de favoritos
            </button>
          </section>
        ))}
      </div>
    </div>
  );
}
