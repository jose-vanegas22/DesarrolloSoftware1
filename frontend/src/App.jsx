import { BrowserRouter, Navigate, Route, Routes } from "react-router";
import MenuPrincipal from "./components/MenuPrincipal";
import RutaProtegida from "./components/RutaProtegida";
import AccesoPage from "./pages/acceso/AccesoPage";
import InicioPage from "./pages/inicio/InicioPage";
import PerfilPage from "./pages/perfil/PerfilPage";
import SeleccionarRolPage from "./pages/seleccionar-rol/SeleccionarRolPage";
import UsuariosPage from "./pages/usuarios/UsuariosPage";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Navigate to="/inicio" replace />} />
        <Route element={<AccesoPage />}>
          <Route path="/login" element={null} />
          <Route path="/registro" element={null} />
        </Route>
        <Route
          path="/seleccionar-rol"
          element={
            <RutaProtegida requiereRol={false}>
              <SeleccionarRolPage />
            </RutaProtegida>
          }
        />
        <Route
          element={
            <RutaProtegida>
              <MenuPrincipal />
            </RutaProtegida>
          }
        >
          <Route path="/inicio" element={<InicioPage />} />
          <Route path="/usuarios" element={<UsuariosPage />} />
          <Route path="/perfil" element={<PerfilPage />} />
        </Route>
        <Route path="*" element={<Navigate to="/inicio" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
