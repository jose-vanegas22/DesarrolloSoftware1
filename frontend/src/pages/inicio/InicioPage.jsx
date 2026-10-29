import { useNavigate } from "react-router";
import { cerrarSesion } from "../../api/authApi";

export default function InicioPage() {
  const navigate = useNavigate();

  const handleCerrarSesion = () => {
    cerrarSesion();
    navigate("/login");
  };

  return (
    <div>
      <h1>Inicio</h1>
      <p>Sesión iniciada correctamente.</p>
      <button onClick={handleCerrarSesion}>Cerrar sesión</button>
    </div>
  );
}
