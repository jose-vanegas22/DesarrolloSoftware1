import { Navigate } from "react-router";
import { haySesion, obtenerRolActivo } from "../api/authApi";

export default function RutaProtegida({ children, requiereRol = true, roles }) {
  if (!haySesion()) return <Navigate to="/login" replace />;
  if (requiereRol && !obtenerRolActivo()) return <Navigate to="/seleccionar-rol" replace />;
  if (roles && !roles.includes(obtenerRolActivo())) return <Navigate to="/inicio" replace />;
  return children;
}
// Si hay sesion muestra la pantalla de inicio, si no hay sesion redirige a login