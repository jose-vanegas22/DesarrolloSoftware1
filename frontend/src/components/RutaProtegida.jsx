import { Navigate } from "react-router";
import { haySesion } from "../api/authApi";

export default function RutaProtegida({ children }) {
  return haySesion() ? children : <Navigate to="/login" />;
}
// Si hay sesion muestra la pantalla de inicio, si no hay sesion redirige a login