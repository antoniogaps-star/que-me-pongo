# Cómo poner "¿Qué me pongo?" en internet

Guía para Toño. Escrita para seguirse sin ayuda, en orden. Cada paso dice **qué hacer**
y **cómo saber que salió bien**.

Todo esto usa capas **gratuitas**. La única cosa de paga es la llave de Claude (paso 5),
y es opcional: sin ella la app funciona, solo que el asesor pierde criterio fino.

| Pieza | Dónde vive | Para qué |
|---|---|---|
| Código | GitHub — `antoniogaps-star/que-me-pongo` | Guarda todo y compila el APK solo |
| Base de datos | Neon | Guarda cuentas, prendas y favoritos |
| Servidor (API) | Render | El cerebro: atiende a la app y al panel |
| Panel y landing | Vercel | La página web pública y el panel |
| App Android | GitHub Releases | El APK que se instala en el celular |

---

## 1. GitHub — ✅ hecho

El código está en `https://github.com/antoniogaps-star/que-me-pongo`.

Cada vez que se toca la carpeta `mobile/`, GitHub **compila el APK solo** y lo publica.
El enlace de descarga **nunca cambia**:

```
https://github.com/antoniogaps-star/que-me-pongo/releases/latest/download/quemepongo.apk
```

**Cómo ver cómo va:** pestaña **Actions** del repositorio. Verde = listo.

---

## 2. Neon — la base de datos

1. Entra a <https://neon.com> → **Sign in** → entra **con GitHub**.
2. **New project**:
   - *Project name*: `que-me-pongo`
   - *Region*: **AWS US East (Ohio)** (la más cercana a Render)
3. Copia la **cadena de conexión** que te muestra.

> ⚠️ **Lo más importante de todo el despliegue.** Neon da dos cadenas y **hay que usar la
> que dice `-pooler`**. Se ve así:
>
> ```
> postgresql://...@ep-algo-123456-pooler.us-east-2.aws.neon.tech/neondb?sslmode=require
> ```
>
> Si usas la que NO tiene `-pooler`, el servidor **no conecta** y el error que sale no
> dice por qué. Ya nos pasó con Sonrisa.

**Cómo saber que salió bien:** la cadena que guardaste contiene el texto `-pooler`.

---

## 3. Render — el servidor

1. Entra a <https://render.com> → **Sign in with GitHub**.
2. **New** → **Blueprint**.
3. Elige el repositorio `que-me-pongo` y confirma. Render lee el archivo `render.yaml`
   y configura el servicio solo.
4. Te va a pedir **tres valores** (los demás los pone él):

   | Variable | Qué poner |
   |---|---|
   | `DATABASE_URL` | La cadena de Neon del paso 2 (**la del `-pooler`**) |
   | `LICENSE_ADMIN_SECRET` | Una palabra secreta tuya, para generar claves de activación. Anótala. |
   | `ANTHROPIC_API_KEY` | La llave de Claude (paso 5). Si aún no la tienes, **déjala vacía** y la agregas después. |

5. **Apply / Create**. Tarda unos 5 minutos en la primera compilación.

**Cómo saber que salió bien:** abre en el navegador
`https://quemepongo-api.onrender.com/health`
Debe responder: `{"status":"ok","env":"production"}`

> 💤 **Ojo con la capa gratuita:** si nadie usa el servidor por 15 minutos, se duerme.
> La siguiente petición tarda ~50 segundos en despertar. Es normal; la app está hecha
> para esperar ese arranque sin fallar.

---

## 4. Vercel — el panel y la landing

1. Entra a <https://vercel.com> → **Sign in with GitHub**.
2. **Add New** → **Project** → elige `que-me-pongo` → **Import**.
3. Configúralo así:

   | Campo | Valor |
   |---|---|
   | *Root Directory* | `web` ← **importante**, no lo dejes vacío |
   | *Framework Preset* | Vite (lo detecta solo) |
   | *Build Command* | `npm run build` (por defecto) |
   | *Output Directory* | `dist` (por defecto) |

4. **Deploy**.
5. Cuando termine, copia el dominio que te da (algo como
   `que-me-pongo.vercel.app`).

### 4.1 Conectar el panel con el servidor (no te saltes esto)

Por seguridad, el servidor solo acepta peticiones de dominios que conoce. Hay que
avisarle del dominio nuevo:

1. En **Render** → tu servicio → **Environment**
2. Edita `CORS_ORIGINS` y pon tu dominio de Vercel:
   ```
   https://que-me-pongo.vercel.app
   ```
3. Guarda (Render reinicia solo).

**Cómo saber que salió bien:** entra a `https://que-me-pongo.vercel.app/inicio`, da clic
en **Probar gratis 7 días** y crea una cuenta. Si entra al panel, todo está conectado.

---

## 5. La llave de Claude — el criterio del asesor (opcional, de paga)

Sin esta llave **la app funciona completa**: te arma conjuntos correctos con reglas de
vestimenta (la formalidad manda, el clima cuenta) y te avisa honestamente que la
sugerencia no vino del asesor.

Con la llave, el asesor **entiende matices y explica con personalidad**.

1. Entra a <https://console.anthropic.com> y crea tu cuenta.
2. **Settings** → **Billing** → agrega saldo (se cobra por uso, no es mensualidad).
3. **API Keys** → **Create Key**. Cópiala (solo se muestra una vez).
4. En **Render** → tu servicio → **Environment** → pega la llave en `ANTHROPIC_API_KEY`.

**Cómo saber que salió bien:** pide una recomendación en la app. Si **ya no aparece** el
aviso *"Sin conexión al asesor: combinación básica"*, la llave está funcionando.

### Cuánto cuesta, en cristiano

Se paga por uso. Dos cosas gastan:

- **Clasificar una foto** — una sola vez por prenda, al darla de alta.
- **Armar un outfit** — cada vez que tocas "Vísteme".

Un clóset de 50 prendas se clasifica una vez y ya. Las recomendaciones son de texto,
que es lo barato. Para uso personal hablamos de **centavos de dólar al mes**; lo que
conviene vigilar es si un día lo usan cientos de personas.

> 💡 **Consejo:** en la consola de Anthropic puedes ponerle un **límite de gasto mensual**.
> Hazlo desde el primer día: si algo se dispara, se corta solo en vez de sorprenderte.

---

## 6. El APK en tu celular

1. Entra desde el celular a `https://que-me-pongo.vercel.app/inicio`
2. Botón **Descargar la app**
3. Android va a advertir *"archivo de origen desconocido"* — es normal, es porque la app
   no viene de la Play Store. Dale **Permitir** e **Instalar**.

---

## Si algo falla

| Síntoma | Causa casi siempre | Solución |
|---|---|---|
| La app dice "no pude conectar" | El servidor gratuito está dormido | Espera ~50 s y reintenta |
| El panel no entra, error de red | Falta el dominio en `CORS_ORIGINS` | Paso 4.1 |
| Render no arranca, error de base | La cadena de Neon **sin** `-pooler` | Paso 2 |
| El botón de descarga da 404 | Aún no ha terminado la primera compilación | Pestaña **Actions** en GitHub |
| El asesor siempre dice "combinación básica" | Falta `ANTHROPIC_API_KEY` | Paso 5 |
