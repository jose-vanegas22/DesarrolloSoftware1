import { useState } from "react";
import { Navigate, useNavigate } from "react-router";
import { obtenerRoles, seleccionarRol } from "../../api/authApi";
import "./SeleccionarRolPage.css";

const ETIQUETAS = {
  administrador: "Administrador del sistema",
  comite: "Miembro del comité científico",
  autor: "Autor",
};

export default function SeleccionarRolPage() {
  const [enviando, setEnviando] = useState(false);
  const [error, setError] = useState("");
  const navigate = useNavigate();
  const roles = obtenerRoles();

  const handleSeleccionar = async (rol) => {
    setError("");
    setEnviando(true);

    try {
      await seleccionarRol(rol);
      navigate("/inicio", { replace: true });
    } catch {
      setError("No se pudo seleccionar el rol. Intenta de nuevo.");
      setEnviando(false);
    }
  };

  if (roles.length === 0) return <Navigate to="/login" replace />;

  return (
    <main className="rol-pagina">
      <section className="rol-tarjeta">
        <h1>¿Con qué rol quieres ingresar?</h1>
        <p>Tus permisos dependerán del rol que elijas.</p>

        {roles.map((rol) => (
          <button
            className="boton boton-secundario"
            type="button"
            key={rol}
            disabled={enviando}
            onClick={() => handleSeleccionar(rol)}
          >
            {ETIQUETAS[rol]}
          </button>
        ))}

        {error && <p className="mensaje-error">{error}</p>}
      </section>
    </main>
  );
}
