import { Plus } from "lucide-react";
import { useEffect, useState } from "react";
import { obtenerRolActivo } from "../../api/authApi";
import { getUsuarios } from "../../api/usuariosApi";
import UsuarioModal from "./components/UsuarioModal";
import UsuariosFiltros from "./components/UsuariosFiltros";
import UsuariosTabla from "./components/UsuariosTabla";
import "./UsuariosPage.css";

export default function UsuariosPage() {
  const [usuarios, setUsuarios] = useState([]);
  const [filtros, setFiltros] = useState({});
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState("");
  const [creando, setCreando] = useState(false);
  const [mensaje, setMensaje] = useState("");
  const esGestor = ["administrador", "comite"].includes(obtenerRolActivo());

  useEffect(() => {
    getUsuarios(filtros)
      .then(({ data }) => setUsuarios(data))
      .catch(() => setError("No se pudieron cargar los usuarios."))
      .finally(() => setCargando(false));
  }, [filtros]);

  const handleFiltrar = (nuevosFiltros) => {
    setError("");
    setCargando(true);
    setFiltros(nuevosFiltros);
  };

  const handleGuardado = () => {
    setCreando(false);
    setMensaje("Usuario creado correctamente.");
    handleFiltrar({ ...filtros });
  };

  return (
    <section className="usuarios-pagina">
      <div className="usuarios-encabezado">
        <h1>Usuarios</h1>
        {esGestor && (
          <button className="boton boton-principal" type="button" onClick={() => setCreando(true)}>
            <Plus size={16} aria-hidden="true" />
            Crear usuario
          </button>
        )}
      </div>

      <UsuariosFiltros onFiltrar={handleFiltrar} />

      {mensaje && <p className="mensaje-exito">{mensaje}</p>}
      {error && <p className="mensaje-error">{error}</p>}
      {cargando && <p>Cargando usuarios...</p>}
      {!cargando && !error && usuarios.length === 0 && <p>No se encontraron usuarios.</p>}
      {!cargando && !error && usuarios.length > 0 && <UsuariosTabla usuarios={usuarios} />}

      {creando && <UsuarioModal onCerrar={() => setCreando(false)} onGuardado={handleGuardado} />}
    </section>
  );
}
