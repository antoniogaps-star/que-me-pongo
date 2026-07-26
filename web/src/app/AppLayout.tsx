import { useQuery } from "@tanstack/react-query";
import { NavLink, Outlet, useNavigate } from "react-router-dom";

import { logout as logoutApi } from "@/features/auth/api";
import { fetchMe } from "@/features/dashboard/api";
import { useAuthStore } from "@/shared/auth/store";
import { useSubscriptionStore } from "@/shared/billing/subscription";

const LINKS = [
  { to: "/", label: "Inicio", end: true },
  { to: "/asesor", label: "¿Qué me pongo?", end: false },
  { to: "/closet", label: "Mi clóset", end: false },
  { to: "/favoritos", label: "Favoritos", end: false },
  { to: "/usuarios", label: "Usuarios", end: false },
];

export function AppLayout() {
  const navigate = useNavigate();
  const clear = useAuthStore((s) => s.clear);
  const me = useQuery({ queryKey: ["me"], queryFn: fetchMe });
  const subExpired = useSubscriptionStore((s) => s.message);
  const clearSub = useSubscriptionStore((s) => s.clear);

  async function logout() {
    const refresh = useAuthStore.getState().refreshToken;
    if (refresh) {
      try {
        await logoutApi(refresh);
      } catch {
        /* cerramos igual localmente */
      }
    }
    clear();
    navigate("/login");
  }

  return (
    <div>
      <nav className="topnav">
        <span className="brand">
          <img src="/mark.svg" alt="" />
          ¿Qué me pongo?
        </span>
        <div className="navlinks">
          {LINKS.map((l) => (
            <NavLink
              key={l.to}
              to={l.to}
              end={l.end}
              className={({ isActive }) => (isActive ? "active" : "")}
            >
              {l.label}
            </NavLink>
          ))}
        </div>
        <div className="navuser">
          <span>{me.data?.email}</span>
          <button type="button" className="linkbtn" onClick={logout}>
            Salir
          </button>
        </div>
      </nav>
      {subExpired && (
        <div
          role="alert"
          style={{
            background: "#241f16",
            borderBottom: "1px solid #b8935c",
            color: "#e8cfa0",
            padding: "0.6rem 1rem",
            display: "flex",
            alignItems: "center",
            gap: "0.75rem",
          }}
        >
          <span style={{ flex: 1 }}>⚠️ {subExpired}</span>
          <button
            type="button"
            className="linkbtn"
            onClick={clearSub}
            aria-label="Cerrar aviso"
          >
            Entendido
          </button>
        </div>
      )}
      <main className="content">
        <Outlet />
      </main>
    </div>
  );
}
