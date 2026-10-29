import { BrowserRouter, Navigate, Route, Routes } from "react-router";
import RutaProtegida from "./components/RutaProtegida";
import InicioPage from "./pages/inicio/InicioPage";
import LoginPage from "./pages/login/LoginPage";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Navigate to="/inicio" />} />
        <Route path="/login" element={<LoginPage />} />
        <Route
          path="/inicio"
          element={
            <RutaProtegida>
              <InicioPage />
            </RutaProtegida>
          }
        />
        <Route path="*" element={<Navigate to="/inicio" />} />
      </Routes>
    </BrowserRouter>
  );
}
