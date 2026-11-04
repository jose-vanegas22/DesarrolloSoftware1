import { Link } from "react-router";

export default function PanelAcceso({ esRegistro }) {
  return (
    <aside className="acceso-panel">
      <span className="acceso-panel-icono" aria-hidden="true">
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
          <path d="M12 6.5C10 5 7 4.5 3.5 5v14c3.5-.5 6.5 0 8.500 1.500 2-1.500 5-2 8.500-1.500V5c-3.500-.5-6.500 0-8.500 1.500Z" />
          <path d="M12 6.500v14" />
        </svg>
      </span>
      <p className="acceso-panel-texto">
        {esRegistro ? "¿Ya tienes una cuenta?" : "¿Eres autor y no tienes cuenta?"}
      </p>
      <Link className="boton boton-secundario" to={esRegistro ? "/login" : "/registro"}>
        {esRegistro ? "Iniciar sesión" : "Crear cuenta"}
      </Link>
    </aside>
  );
}
