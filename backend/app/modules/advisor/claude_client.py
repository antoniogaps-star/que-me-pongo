"""El cerebro: Claude clasifica las fotos y arma/explica los outfits.

Dos usos, ambos con salida estructurada (JSON garantizado) para que el móvil no tenga que
adivinar nada:

1. `classify_photo` — se llama UNA vez por prenda, al fotografiarla.
2. `recommend` — se llama al pedir "¿qué me pongo?"; solo manda la lista en texto (barato).

Si no hay llave configurada o la API falla, se levanta `AdvisorUnavailable` y el router cae
a las reglas locales: la app nunca se queda muda.
"""

from __future__ import annotations

import json
from typing import Any

from app.core.config import settings

MODEL = "claude-opus-5"

# La personalidad del asesor (PRD §2). Es lo que separa "combinador de colores" de
# "asesor de imagen": honesto, explica el porqué, y nunca hace sentir mal al usuario.
ADVISOR_SYSTEM = """Eres un asesor de imagen personal de alto nivel, mexicano, cercano y \
honesto. Hablas en español claro, sin tecnicismos de moda.

Reglas que nunca rompes:
- Solo recomiendas prendas que están en el clóset del usuario. Jamás inventas ropa.
- Siempre explicas POR QUÉ funciona el conjunto, en una o dos frases.
- Eres honesto: si algo no queda del todo, lo dices con tacto y ofreces la alternativa.
- Nunca insultas ni haces sentir mal a la persona por su ropa o su cuerpo.
- Respetas el estilo del usuario; no lo empujas a vestirse como otra persona.
- La formalidad manda: no pones tenis deportivos en un evento formal aunque el color combine.
- Consideras el clima: con frío agregas abrigo; con calor mantienes el conjunto ligero.

Tono: como un amigo que sabe de moda y te dice la verdad. Nada robótico, nada de listas \
interminables. Frases cortas y con seguridad."""

CLASSIFY_SYSTEM = """Eres un clasificador de prendas de ropa. Miras la foto de UNA prenda y \
devuelves su ficha. Si la foto no es clara, eliges la opción más probable en vez de dejar \
campos vacíos: el usuario puede corregir después.

La formalidad va de 1 a 10: 1 = pants de dormir, 5 = jeans y playera, 8 = camisa y saco, \
10 = traje de etiqueta."""

_STYLES = [
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
]

CLASSIFY_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "category": {
            "type": "string",
            "enum": ["arriba", "abajo", "abrigo", "calzado", "accesorio", "completo"],
        },
        "name": {
            "type": "string",
            "description": "Nombre corto en español, ej. 'Camisa azul marino'",
        },
        "color": {"type": "string", "description": "Color principal en español"},
        "styles": {
            "type": "array",
            "items": {"type": "string", "enum": _STYLES},
            "description": "Uno a tres estilos que le quedan a la prenda",
        },
        "formality": {"type": "integer", "minimum": 1, "maximum": 10},
        "season": {"type": "string", "enum": ["todo", "calor", "frio"]},
    },
    "required": ["category", "name", "color", "styles", "formality", "season"],
    "additionalProperties": False,
}

RECOMMEND_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "outfits": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "garment_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": (
                            "IDs EXACTOS de las prendas del clóset que forman el conjunto"
                        ),
                    },
                    "explanation": {
                        "type": "string",
                        "description": (
                            "Una o dos frases: por qué funciona, con el 'pero' honesto si lo hay"
                        ),
                    },
                    "projected_image": {
                        "type": "string",
                        "description": (
                            "Qué imagen proyecta, en pocas palabras. Ej: 'Seguridad y estilo "
                            "moderno'"
                        ),
                    },
                },
                "required": ["garment_ids", "explanation", "projected_image"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["outfits"],
    "additionalProperties": False,
}


class AdvisorUnavailable(Exception):
    """La IA no está disponible (sin llave, sin red, o rechazó la petición)."""


def is_configured() -> bool:
    return bool(settings.anthropic_api_key)


def _client() -> Any:
    if not is_configured():
        raise AdvisorUnavailable("Falta ANTHROPIC_API_KEY")
    try:
        from anthropic import AsyncAnthropic
    except ImportError as exc:  # pragma: no cover - dependencia declarada en pyproject
        raise AdvisorUnavailable("Falta el paquete 'anthropic'") from exc
    return AsyncAnthropic(api_key=settings.anthropic_api_key)


def _first_json(response: Any) -> dict[str, Any]:
    """Saca el JSON del primer bloque de texto de la respuesta.

    Con `output_config.format` la salida ya viene validada contra el esquema, pero el
    primer bloque puede ser de razonamiento: hay que buscar el de tipo 'text'.
    """
    if getattr(response, "stop_reason", None) == "refusal":
        raise AdvisorUnavailable("La IA declinó responder")
    for block in response.content:
        if block.type == "text":
            return dict(json.loads(block.text))
    raise AdvisorUnavailable("La IA no devolvió contenido")


async def classify_photo(image_base64: str, media_type: str = "image/jpeg") -> dict[str, Any]:
    """Mira la foto de una prenda y devuelve su ficha lista para guardar."""
    client = _client()
    try:
        response = await client.messages.create(
            model=MODEL,
            max_tokens=1024,
            system=CLASSIFY_SYSTEM,
            # Tarea acotada: esfuerzo bajo = rápido y barato, sin perder calidad.
            output_config={
                "effort": "low",
                "format": {"type": "json_schema", "schema": CLASSIFY_SCHEMA},
            },
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": image_base64,
                            },
                        },
                        {"type": "text", "text": "Clasifica esta prenda."},
                    ],
                }
            ],
        )
    except AdvisorUnavailable:
        raise
    except Exception as exc:
        raise AdvisorUnavailable(f"Error al clasificar la foto: {exc}") from exc
    return _first_json(response)


def _closet_lines(garments: list[dict[str, Any]]) -> str:
    """El clóset en texto plano: una línea por prenda. Barato de mandar y fácil de leer."""
    lines = []
    for g in garments:
        styles = g.get("styles") or []
        styles_txt = "/".join(styles) if isinstance(styles, list) else str(styles)
        lines.append(
            f"- id={g['id']} | {g.get('category')} | {g.get('name')} | color: "
            f"{g.get('color') or 'sin dato'} | estilos: {styles_txt or 'sin dato'} | "
            f"formalidad: {g.get('formality', 5)}/10 | clima: {g.get('season', 'todo')}"
        )
    return "\n".join(lines)


async def recommend(
    garments: list[dict[str, Any]],
    *,
    occasion: str,
    projection: str = "",
    temperature_c: float | None = None,
    preferred_styles: list[str] | None = None,
    avoid_colors: list[str] | None = None,
    recent_combos: list[list[str]] | None = None,
    anchor_garment_id: str | None = None,
    surprise: bool = False,
    count: int = 1,
) -> list[dict[str, Any]]:
    """Arma de 1 a 3 conjuntos con explicación. Devuelve la lista tal cual del esquema."""
    client = _client()

    partes = [f"CLÓSET DEL USUARIO:\n{_closet_lines(garments)}", f"\nOCASIÓN: {occasion}"]
    if projection:
        partes.append(f"QUIERE PROYECTAR: {projection}")
    if temperature_c is not None:
        partes.append(f"CLIMA: {temperature_c:.0f}°C")
    if preferred_styles:
        partes.append(f"ESTILO DEL USUARIO: {', '.join(preferred_styles)}")
    if avoid_colors:
        partes.append(f"COLORES QUE NO LE GUSTAN: {', '.join(avoid_colors)}")
    if anchor_garment_id:
        partes.append(
            f"OBLIGATORIO: el conjunto DEBE incluir la prenda id={anchor_garment_id}."
        )
    if surprise:
        combos = "; ".join(", ".join(c) for c in (recent_combos or []))
        partes.append(
            "MODO SORPRESA: propón una combinación DISTINTA a las que ya usa, sin salirte "
            "de su estilo, y menciona en la explicación qué cambiaste."
            + (f" Combinaciones que ya usa: {combos}." if combos else "")
        )
    partes.append(
        f"\nArma {count} conjunto(s) usando SOLO los id del clóset. Incluye arriba, abajo y "
        "calzado; agrega abrigo si el clima lo pide y accesorio si suma."
    )

    try:
        response = await client.messages.create(
            model=MODEL,
            max_tokens=4096,
            system=ADVISOR_SYSTEM,
            # Esfuerzo medio: hay criterio real que aplicar, pero el usuario espera respuesta
            # en segundos, no en minutos.
            output_config={
                "effort": "medium",
                "format": {"type": "json_schema", "schema": RECOMMEND_SCHEMA},
            },
            messages=[{"role": "user", "content": "\n".join(partes)}],
        )
    except AdvisorUnavailable:
        raise
    except Exception as exc:
        raise AdvisorUnavailable(f"Error al recomendar: {exc}") from exc

    data = _first_json(response)
    outfits = data.get("outfits", [])
    return list(outfits) if isinstance(outfits, list) else []
