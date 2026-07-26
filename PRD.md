# ¿Qué me pongo? — PRD (documento de producto)

*Versión 2 (fusionada) · 25 jul 2026 · APROBADO por Toño*

> **Eslogan:** Tu clóset. Tu estilo. Tu mejor versión.

---

## 1. Qué es

Una app que **fotografía tu clóset** y te dice **qué ponerte hoy** — explicándote *por qué*
funciona y **qué imagen estás proyectando**. No es un combinador de colores: es un **asesor de
imagen personal** que solo usa **tu** ropa.

**El problema real:** "no tengo nada que ponerme" con el clóset lleno.

Producto **multiusuario y vendible** (mismo motor que Ágora y Sonrisa: cada clóset es privado,
aislado por base de datos).

---

## 2. El cerebro: Claude AI (`claude-opus-5`)

1. **Clasifica la foto** al tomarla → tipo, color, estilos, **formalidad 1–10**, temporada.
   Tú confirmas o corriges.
2. **Recomienda y explica** → recibe tu clóset + ocasión + **lo que quieres proyectar** +
   clima, y devuelve el outfit con su explicación honesta.

**Personalidad del asesor** (regla firme): honesto pero nunca hiriente, siempre explica el
*por qué*, siempre ofrece una alternativa, y se adapta a tu estilo — no al de una revista.

> *"Puedes, pero no es la mejor combinación. Esa camisa tiene presencia elegante y ese
> pantalón le resta fuerza. Yo la usaría con el oscuro y tus zapatos cafés: vas a proyectar
> una imagen mucho más segura."*

**Costo y privacidad (v1):** las fotos viven **en tu teléfono**. Cada foto se manda **una vez**
a Claude para clasificarla. Para recomendar solo se manda la **lista en texto** (barato y
rápido). Sin internet o sin cupo → **reglas locales**, la app nunca se queda muda.

---

## 3. MVP — la v1

1. **Registro** simple: correo + contraseña. **Sin cuestionario** — la IA deduce tu estilo de
   tu propia ropa (las preferencias finas van en Ajustes, opcionales).
2. **Agregar prenda**: cámara **o galería** → Claude clasifica → confirmas.
3. **Clóset** por categorías: 👕 arriba · 👖 abajo · 🧥 abrigo · 👞 calzado · 🎩 **accesorios**.
4. **🔥 ¿QUÉ ME PONGO?** — la pantalla estrella:
   - **¿Para qué ocasión?** trabajo · cita · fiesta · reunión · escuela · evento formal ·
     salida casual · viaje · día normal
   - **¿Qué quieres proyectar?** elegante · seguro · atractivo · moderno · relajado ·
     profesional · poderoso
5. **Resultado**: las fotos de *tus* prendas + **"imagen proyectada"** + la **explicación
   honesta** (con el "pero" incluido, sin calificación numérica inventada).
6. **¿Con qué combino esto?** — eliges una prenda, te da 5 caminos (casual, moderno, rockero,
   elegante, para una cita).
7. **🎲 Sorpréndeme** — combinaciones distintas a las que ya usas, explicando el cambio.
8. **Favoritos** — guardas outfits; la app aprende qué te gusta.
9. **Clima y hora** integrados en la recomendación.
10. **Estilos**: Casual · Moderno · Clásico · Rockero · Deportivo · Elegante · Streetwear ·
    Ranchero · Ejecutivo · Minimalista.
11. **Prueba gratis 7 días** + modo lectura al vencer (motor de Ágora).

### Fuera de la v1 (y por qué)

| Después | Razón |
|---|---|
| Test de estilo al registrarse | Fricción antes de demostrar valor; la IA lo deduce sola |
| Chat abierto con el asesor | Es un producto en sí; en v1 el asesor ya habla en cada outfit |
| Calificación 8.7/10 | Un número inventado suena falso; la explicación honesta aporta más |
| Historial "qué usé cada día" | v2 |
| Fotos en la nube / sync entre teléfonos | v2 |
| Premium $4.99 activo | Candado listo, se enciende después |
| Comunidad, tienda afiliada, tendencias | Producto *después* de tener usuarios |

---

## 4. Pantallas (móvil)

1. Registro / entrar → 2. **Inicio** (botón gigante ¿QUÉ ME PONGO?) → 3. Mi Clóset →
4. Agregar prenda → 5. Ocasión + proyección → 6. Resultado del outfit →
7. ¿Con qué combino esto? → 8. Favoritos → 9. Ajustes.

---

## 5. Datos

- **Prenda**: categoría, tipo, nombre, color, estilos, **formalidad (1–10)**, temporada,
  foto local.
- **Perfil**: estilo(s) preferido(s), colores que no le gustan (opcional).
- **Outfit / Favorito**: prendas usadas, ocasión, proyección, explicación, fecha.
- Todo **privado por usuario** (RLS de Postgres).

---

## 6. Monetización

- **Gratis**: 7 días de prueba, luego hasta 30 prendas.
- **Premium (después)**: clóset ilimitado, todos los estilos, historial, análisis de color.

---

## 7. Método de trabajo (decisión)

**Construir primero, diseñar después.** En vez de dibujar 10 pantallas en papel, se construye
la pantalla estrella funcionando y Toño opina sobre el teléfono real. Cada fase compila y se
puede enseñar.

**Orden:** backend (ampliar prendas + perfil + favoritos + IA) → móvil (cámara + asesor) →
marca → panel web → despliegue.

**Falta de Toño:** un **logo** (para splash e ícono) y, al desplegar, una **llave de Claude**.
