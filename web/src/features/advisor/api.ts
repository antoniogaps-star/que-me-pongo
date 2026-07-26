import { z } from "zod";

import { api } from "@/shared/api/client";

/** Para qué es el outfit. La clave es lo que se manda; el valor, lo que se muestra. */
export const OCASIONES = {
  "dia normal": "Día normal",
  trabajo: "Trabajo",
  cita: "Cita",
  fiesta: "Fiesta",
  reunion: "Reunión",
  escuela: "Escuela",
  "evento formal": "Evento formal",
  "salida casual": "Salida casual",
  viaje: "Viaje",
} as const;

/** Qué imagen quiere dar el usuario: lo que convierte esto en asesor de imagen. */
export const PROYECCIONES = [
  "Elegante",
  "Seguro",
  "Atractivo",
  "Moderno",
  "Relajado",
  "Profesional",
  "Poderoso",
] as const;

export const sugerenciaSchema = z.object({
  garment_ids: z.array(z.string()),
  explanation: z.string(),
  projected_image: z.string(),
});
export type Sugerencia = z.infer<typeof sugerenciaSchema>;

export const recomendacionSchema = z.object({
  outfits: z.array(sugerenciaSchema),
  /** "claude" si lo armó la IA; "reglas" si fue el motor local. */
  source: z.string(),
});
export type Recomendacion = z.infer<typeof recomendacionSchema>;

export interface PeticionAsesor {
  occasion?: string;
  projection?: string;
  temperature_c?: number;
  with_garment_id?: string;
  surprise?: boolean;
  count?: number;
}

export async function recomendar(peticion: PeticionAsesor): Promise<Recomendacion> {
  const { data } = await api.post("/advisor/recommend", peticion);
  return recomendacionSchema.parse(data);
}

// ── Favoritos ──────────────────────────────────────────────
export const outfitSchema = z.object({
  id: z.string(),
  garment_ids: z.array(z.string()),
  occasion: z.string(),
  projection: z.string(),
  explanation: z.string(),
});
export type Outfit = z.infer<typeof outfitSchema>;

export async function listOutfits(): Promise<Outfit[]> {
  const { data } = await api.get("/outfits");
  return z.array(outfitSchema).parse(data);
}

export async function saveOutfit(outfit: {
  garment_ids: string[];
  occasion: string;
  projection: string;
  explanation: string;
}): Promise<Outfit> {
  const { data } = await api.post("/outfits", outfit);
  return outfitSchema.parse(data);
}

export async function deleteOutfit(id: string): Promise<void> {
  await api.delete(`/outfits/${id}`);
}
