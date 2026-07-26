import { createBrowserRouter } from "react-router-dom";

import { AdvisorPage } from "@/features/advisor/AdvisorPage";
import { LoginPage } from "@/features/auth/LoginPage";
import { RegisterPage } from "@/features/auth/RegisterPage";
import { ClosetPage } from "@/features/closet/ClosetPage";
import { DashboardPage } from "@/features/dashboard/DashboardPage";
import { FavoritesPage } from "@/features/favorites/FavoritesPage";
import { LandingPage } from "@/features/landing/LandingPage";
import { UsersPage } from "@/features/users/UsersPage";

import { AppLayout } from "./AppLayout";
import { ProtectedRoute } from "./ProtectedRoute";

export const router = createBrowserRouter([
  { path: "/inicio", element: <LandingPage /> },
  { path: "/login", element: <LoginPage /> },
  { path: "/register", element: <RegisterPage /> },
  {
    element: <ProtectedRoute />,
    children: [
      {
        element: <AppLayout />,
        children: [
          { path: "/", element: <DashboardPage /> },
          { path: "/asesor", element: <AdvisorPage /> },
          { path: "/closet", element: <ClosetPage /> },
          { path: "/favoritos", element: <FavoritesPage /> },
          { path: "/usuarios", element: <UsersPage /> },
        ],
      },
    ],
  },
]);
