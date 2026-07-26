/**
 * Convierte el nombre de la cuenta en un identificador válido para el backend
 * (minúsculas, sin acentos ni espacios; solo a-z, 0-9 y guiones).
 *
 * Debe coincidir con `slugify` de la app móvil para que el mismo nombre produzca
 * el mismo identificador en ambas plataformas.
 *
 *   'Modelorama Toño' -> 'modelorama-tono'
 */
export function slugify(input: string): string {
  let s = input.toLowerCase().trim();
  const from = "áàäâãéèëêíìïîóòöôõúùüûñç";
  const to = "aaaaaeeeeiiiiooooouuuunc";
  for (let i = 0; i < from.length; i++) {
    s = s.split(from[i]).join(to[i]);
  }
  s = s
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/-{2,}/g, "-")
    .replace(/^-+|-+$/g, "");
  return s;
}
