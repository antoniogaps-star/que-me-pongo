import { z } from "zod";

import { api } from "@/shared/api/client";

/** Dónde va la prenda en el outfit. */
export const CATEGORIAS = {
  arriba: "Parte de arriba",
  abajo: "Parte de abajo",
  abrigo: "Abrigo",
  calzado: "Calzado",
  accesorio: "Accesorio",
  completo: "Conjunto completo",
} as const;

/** Los 10 estilos del PRD. */
export const ESTILOS = [
  "casual",
  "moderno",
  "clasico",
  "rockero",
  "deportivo",
  "elegante",
  "streetwear",
  "ranchero",
  "ejecutivo",
  "minimalista",
] as const;

export const TEMPORADAS = {
  todo: "Todo el año",
  calor: "Para calor",
  frio: "Para frío",
} as const;

export const garmentSchema = z.object({
  id: z.string(),
  category: z.string(),
  name: z.string(),
  color: z.string().nullable(),
  styles: z.array(z.string()),
  formality: z.number(),
  season: z.string(),
});
export type Garment = z.infer<typeof garmentSchema>;

export async function listGarments(): Promise<Garment[]> {
  const { data } = await api.get("/garments");
  return z.array(garmentSchema).parse(data);
}

export interface NuevaPrenda {
  category: string;
  name: string;
  color?: string | null;
  styles: string[];
  formality: number;
  season: string;
}

export async function createGarment(prenda: NuevaPrenda): Promise<Garment> {
  const { data } = await api.post("/garments", prenda);
  return garmentSchema.parse(data);
}

export async function deleteGarment(id: string): Promise<void> {
  await api.delete(`/garments/${id}`);
}

/** Traduce la formalidad a algo que una persona entienda de inmediato. */
export function describeFormalidad(v: number): string {
  if (v <= 2) return "Para andar en casa";
  if (v <= 4) return "Informal, del diario";
  if (v <= 6) return "Arreglado sin exagerar";
  if (v <= 8) return "Formal: oficina, reunión";
  return "De etiqueta";
}
