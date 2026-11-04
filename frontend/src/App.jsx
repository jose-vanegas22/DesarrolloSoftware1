import { BrowserRouter, Navigate, Route, Routes } from "react-router";
import RutaProtegida from "./components/RutaProtegida";
import AccesoPage from "./pages/acceso/AccesoPage";
import InicioPage from "./pages/inicio/InicioPage";
import SeleccionarRolPage from "./pages/seleccionar-rol/SeleccionarRolPage";

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
          path="/inicio"
          element={
            <RutaProtegida>
              <InicioPage />
            </RutaProtegida>
          }
        />
        <Route path="*" element={<Navigate to="/inicio" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
