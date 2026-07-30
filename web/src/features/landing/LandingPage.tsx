import { Link } from "react-router-dom";

/**
 * Enlace CORTO de descarga: `/app`.
 *
 * Es una redirección (ver `vercel.json`) hacia la última versión del APK en GitHub. Se
 * usa el corto y no el de GitHub porque este se dicta por teléfono sin equivocarse y
 * cabe donde sea. Y si mañana el archivo cambia de nombre o de lugar, se cambia la
 * redirección y lo ya compartido sigue funcionando.
 */
const APK_URL = "/app";

/** La app descargable es solo Android; iPhone y computadora usan el panel web. */
const isIOS =
  typeof navigator !== "undefined" && /iPad|iPhone|iPod/.test(navigator.userAgent);

const BENEFICIOS = [
  {
    emoji: "📸",
    titulo: "Fotografía tu clóset",
    texto:
      "Le tomas foto a cada prenda y la app la reconoce sola: qué es, de qué color y con qué ocasión va. Tú solo confirmas.",
  },
  {
    emoji: "✨",
    titulo: "Te dice qué ponerte",
    texto:
      "Eliges a dónde vas y qué quieres proyectar. Te arma el conjunto con la ropa que YA tienes — nunca con ropa que no tienes.",
  },
  {
    emoji: "💬",
    titulo: "Y te explica por qué",
    texto:
      "No es un combinador de colores. Es un asesor que te dice qué imagen estás proyectando y te avisa, con tacto, cuando algo no cuadra.",
  },
  {
    emoji: "🧥",
    titulo: "¿Con qué combino esto?",
    texto:
      "Escoges una prenda y te propone con qué usarla. Deja de usar siempre las mismas tres combinaciones.",
  },
  {
    emoji: "🎲",
    titulo: "Sorpréndeme",
    texto:
      "Para los días sin ganas de decidir. Te propone algo distinto a lo que ya usas, sin salirse de tu estilo.",
  },
  {
    emoji: "🌤️",
    titulo: "Toma en cuenta el clima",
    texto:
      "Con frío te agrega abrigo; con calor mantiene el conjunto ligero. Y la formalidad manda: nunca tenis en un evento formal.",
  },
];

/** Página pública de venta. Se comparte con prospectos para su prueba gratis. */
export function LandingPage() {
  return (
    <div className="landing">
      {/* La portada va como fondo, con un velo oscuro encima: sin él, el texto dorado
          se pierde sobre las zonas claras de la foto. */}
      <header className="landing-hero landing-hero-foto">
        <div className="landing-brand">
          <img src="/logo-mark.png" alt="¿Qué me pongo?" />
          <h1>¿Qué me pongo?</h1>
          <div className="filete" aria-hidden="true">
            ◆
          </div>
          <p className="landing-slogan">Tu clóset. Tu estilo. Tu mejor versión.</p>

          <p className="landing-lead">
            Tienes el clóset lleno y sigues diciendo <em>"no tengo nada que ponerme"</em>.
            Fotografía tu ropa una vez y deja que un asesor de imagen te vista todos los
            días — con lo que ya tienes.
          </p>

          {isIOS && (
            <p
              className="landing-note"
              style={{
                background: "var(--carbon)",
                border: "1px solid var(--borde)",
                borderRadius: "10px",
                padding: "0.7rem 1rem",
                maxWidth: "460px",
                margin: "0.5rem auto 0",
              }}
            >
              La app para instalar es de Android. En iPhone entra desde el navegador:
              funciona igual.
            </p>
          )}

          <div className="landing-cta">
            {!isIOS && (
              <a className="landing-btn landing-btn-primary" href={APK_URL}>
                Descargar la app
              </a>
            )}
            <Link className="landing-btn landing-btn-ghost" to="/register">
              Probar gratis 7 días
            </Link>
          </div>

          <p className="landing-note" style={{ marginTop: "1.4rem" }}>
            Sin tarjeta. Sin compromiso. Tu clóset es privado: solo tú lo ves.
          </p>
        </div>
      </header>

      <section className="landing-features">
        {BENEFICIOS.map((b) => (
          <article key={b.titulo} className="landing-feature">
            <div className="landing-emoji">{b.emoji}</div>
            <h3>{b.titulo}</h3>
            <p>{b.texto}</p>
          </article>
        ))}
      </section>

      <section className="landing-steps">
        <h2 style={{ textAlign: "center", marginBottom: "1.6rem" }}>Cómo funciona</h2>
        <ol>
          <li>
            <strong>Fotografía tus prendas.</strong> Una foto por prenda, con la cámara o
            desde tu galería. La app las clasifica sola.
          </li>
          <li>
            <strong>Dime a dónde vas.</strong> Trabajo, cita, fiesta, evento formal… y qué
            quieres proyectar: elegante, seguro, profesional.
          </li>
          <li>
            <strong>Vístete.</strong> Te armo el conjunto, te digo qué imagen proyectas y
            por qué funciona. Si algo no cuadra, te lo digo de frente.
          </li>
        </ol>
        <p className="landing-note" style={{ textAlign: "center" }}>
          Funciona aunque no tengas internet: en ese caso te visto con reglas de
          vestimenta y te aviso que fue así.
        </p>
      </section>

      <footer className="landing-foot">
        <p>
          ¿Ya tienes cuenta? <Link to="/login">Entrar al panel</Link>
        </p>
        <p style={{ marginTop: "1.2rem" }}>
          ¿Qué me pongo? — Tu clóset. Tu estilo. Tu mejor versión.
        </p>
      </footer>
    </div>
  );
}
