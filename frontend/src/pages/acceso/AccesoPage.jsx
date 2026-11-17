import { NavLink, useLocation } from "react-router";
import LoginForm from "./components/LoginForm";
import PanelAcceso from "./components/PanelAcceso";
import RegistroForm from "./components/RegistroForm";
import RecuperarForm from "./components/RecuperarForm";
import "./AccesoPage.css";

export default function AccesoPage() {
  const { pathname } = useLocation();
  const esRegistro = pathname === "/registro";
  const esRecuperar = pathname === "/recuperar";


  return (
    <main className="acceso-pagina">
      <div className={`acceso-tarjeta ${esRegistro ? "acceso-tarjeta-registro" : ""}`}>
        <section className="acceso-contenido" key={pathname}>
          <div className="acceso-marca">
            <span className="acceso-logo" aria-hidden="true">C</span>
            <span>Conecta</span>
          </div>

          <nav className="acceso-pestanas" aria-label="Acceso">
            <NavLink to="/login">Iniciar sesión</NavLink>
            <NavLink to="/registro">Crear cuenta</NavLink>
          </nav>

          {esRegistro ? <RegistroForm /> : esRecuperar ? <RecuperarForm /> : <LoginForm />}
        </section>

        <PanelAcceso esRegistro={esRegistro} />
      </div>
    </main>
  );
}
