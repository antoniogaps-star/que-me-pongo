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

/**
 * Qué prendas tienen foto respaldada. Una sola petición para todo el clóset, en vez de
 * pedir la imagen de cada una para averiguar si existe.
 */
export async function fetchGarmentsWithPhoto(): Promise<Set<string>> {
  const { data } = await api.get("/garments/fotos");
  return new Set(z.array(z.string()).parse(data));
}

/**
 * Descarga la foto de una prenda y la convierte en una URL que el navegador pueda pintar.
 *
 * No se puede poner la dirección directo en un `<img src>`: la API exige el token de la
 * sesión en la cabecera, y una etiqueta `<img>` no manda cabeceras. Por eso se baja como
 * archivo y se crea una URL temporal en memoria.
 */
export async function fetchGarmentPhotoUrl(id: string): Promise<string> {
  const { data } = await api.get(`/garments/${id}/foto`, { responseType: "blob" });
  return URL.createObjectURL(data as Blob);
}
