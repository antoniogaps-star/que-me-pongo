"""Las reglas locales: el respaldo sin IA. Deben ser correctas, no geniales."""

from app.modules.advisor import rules

CLOSET = [
    {"id": "1", "category": "arriba", "name": "Playera gris", "color": "gris",
     "styles": ["casual"], "formality": 3, "season": "calor"},
    {"id": "2", "category": "arriba", "name": "Camisa blanca", "color": "blanco",
     "styles": ["elegante"], "formality": 9, "season": "todo"},
    {"id": "3", "category": "abajo", "name": "Jeans azules", "color": "azul",
     "styles": ["casual"], "formality": 4, "season": "todo"},
    {"id": "4", "category": "abajo", "name": "Pantalón de vestir", "color": "negro",
     "styles": ["elegante"], "formality": 9, "season": "todo"},
    {"id": "5", "category": "calzado", "name": "Tenis blancos", "color": "blanco",
     "styles": ["deportivo"], "formality": 3, "season": "todo"},
    {"id": "6", "category": "calzado", "name": "Zapatos negros", "color": "negro",
     "styles": ["elegante"], "formality": 9, "season": "todo"},
    {"id": "7", "category": "abrigo", "name": "Chamarra negra", "color": "negro",
     "styles": ["casual"], "formality": 5, "season": "frio"},
]


def test_evento_formal_elige_lo_formal() -> None:
    """A un evento formal NO se va en tenis, aunque el color combine."""
    outfit = rules.build_outfit(CLOSET, occasion="evento formal")
    assert outfit is not None
    assert set(outfit.garment_ids) == {"2", "4", "6"}


def test_dia_normal_elige_lo_casual() -> None:
    outfit = rules.build_outfit(CLOSET, occasion="dia normal")
    assert outfit is not None
    assert set(outfit.garment_ids) == {"1", "3", "5"}


def test_con_frio_agrega_abrigo() -> None:
    outfit = rules.build_outfit(CLOSET, occasion="dia normal", temperature_c=10)
    assert outfit is not None
    assert "7" in outfit.garment_ids
    assert "abrigo" in outfit.explanation.lower()


def test_con_calor_no_usa_prendas_de_frio() -> None:
    outfit = rules.build_outfit(CLOSET, occasion="dia normal", temperature_c=32)
    assert outfit is not None
    assert "7" not in outfit.garment_ids


def test_closet_incompleto_no_inventa_outfit() -> None:
    """Sin calzado no hay conjunto: es mejor pedir más prendas que mentir."""
    sin_calzado = [g for g in CLOSET if g["category"] != "calzado"]
    assert rules.build_outfit(sin_calzado, occasion="dia normal") is None


def test_explicacion_es_honesta_cuando_algo_no_cuadra() -> None:
    """Si solo hay tenis para un evento formal, el asesor lo dice en vez de callarlo."""
    limitado = [g for g in CLOSET if g["id"] in {"2", "4", "5"}]
    outfit = rules.build_outfit(limitado, occasion="evento formal")
    assert outfit is not None
    assert "detalle" in outfit.explanation.lower()


def test_proyeccion_del_usuario_se_respeta() -> None:
    outfit = rules.build_outfit(CLOSET, occasion="cita", projection="Seguro")
    assert outfit is not None
    assert outfit.projected_image == "Seguro"


def test_proponme_otro_no_repite() -> None:
    """Cada "Proponme otro" baja por la lista: nunca repite mientras haya opciones."""
    vistos: list[list[str]] = []
    for _ in range(8):  # 2 arriba x 2 abajo x 2 calzado = 8 combinaciones
        outfit = rules.build_outfit(CLOSET, occasion="dia normal", exclude=vistos)
        assert outfit is not None
        assert set(outfit.garment_ids) not in [set(v) for v in vistos]
        vistos.append(outfit.garment_ids)
    # Agotadas todas, vuelve a empezar y lo dice.
    outfit = rules.build_outfit(CLOSET, occasion="dia normal", exclude=vistos)
    assert outfit is not None
    assert "todas las combinaciones" in outfit.explanation


def test_la_proyeccion_cambia_el_conjunto() -> None:
    """El mismo día normal: 'Relajado' va casual, 'Elegante' sube a lo formal."""
    relajado = rules.build_outfit(CLOSET, occasion="dia normal", projection="Relajado")
    elegante = rules.build_outfit(CLOSET, occasion="dia normal", projection="Elegante")
    assert relajado is not None and elegante is not None
    assert set(relajado.garment_ids) == {"1", "3", "5"}
    assert set(elegante.garment_ids) == {"2", "4", "6"}
    assert "elegante" in elegante.explanation.lower()


def test_profesional_con_ropa_casual_lo_dice() -> None:
    """Pants y tenis no dan imagen profesional: el asesor lo dice, no lo maquilla."""
    casual = [
        {"id": "a", "category": "arriba", "name": "Playera", "color": "gris",
         "styles": ["casual"], "formality": 3, "season": "todo"},
        {"id": "b", "category": "abajo", "name": "Pants", "color": "azul marino",
         "styles": ["deportivo"], "formality": 2, "season": "todo"},
        {"id": "c", "category": "calzado", "name": "Tenis", "color": "negro",
         "styles": ["deportivo"], "formality": 3, "season": "todo"},
    ]
    outfit = rules.build_outfit(casual, occasion="trabajo", projection="Profesional")
    assert outfit is not None
    texto = outfit.explanation.lower()
    assert "detalle" in texto and "informal" in texto
    assert "única combinación" in texto


def test_evita_dos_colores_fuertes() -> None:
    closet = [
        {"id": "r", "category": "arriba", "name": "Playera roja", "color": "rojo",
         "formality": 4},
        {"id": "w", "category": "arriba", "name": "Playera blanca", "color": "blanco",
         "formality": 4},
        {"id": "v", "category": "abajo", "name": "Pantalón verde", "color": "verde",
         "formality": 4},
        {"id": "t", "category": "calzado", "name": "Tenis", "color": "blanco", "formality": 4},
    ]
    outfit = rules.build_outfit(closet, occasion="dia normal")
    assert outfit is not None
    assert "r" not in outfit.garment_ids


def test_con_que_combino_esto_incluye_la_prenda() -> None:
    outfit = rules.build_outfit(CLOSET, occasion="evento formal", anchor_garment_id="5")
    assert outfit is not None
    assert "5" in outfit.garment_ids


def test_vestido_completo_cuenta_como_base() -> None:
    closet = [
        {"id": "d", "category": "completo", "name": "Vestido negro", "color": "negro",
         "styles": ["elegante"], "formality": 8},
        {"id": "z", "category": "calzado", "name": "Zapatillas", "color": "negro",
         "styles": ["elegante"], "formality": 8},
    ]
    outfit = rules.build_outfit(closet, occasion="cita", projection="Elegante")
    assert outfit is not None
    assert set(outfit.garment_ids) == {"d", "z"}
