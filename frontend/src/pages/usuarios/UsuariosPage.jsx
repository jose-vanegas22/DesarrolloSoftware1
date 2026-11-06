import { useEffect, useState } from "react";
import { getUsuarios } from "../../api/usuariosApi";
import UsuariosFiltros from "./components/UsuariosFiltros";
import UsuariosTabla from "./components/UsuariosTabla";
import "./UsuariosPage.css";

export default function UsuariosPage() {
  const [usuarios, setUsuarios] = useState([]);
  const [filtros, setFiltros] = useState({});
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState("");

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

  return (
    <section className="usuarios-pagina">
      <h1>Usuarios</h1>
      <UsuariosFiltros onFiltrar={handleFiltrar} />

      {error && <p className="mensaje-error">{error}</p>}
      {cargando && <p>Cargando usuarios...</p>}
      {!cargando && !error && usuarios.length === 0 && <p>No se encontraron usuarios.</p>}
      {!cargando && !error && usuarios.length > 0 && <UsuariosTabla usuarios={usuarios} />}
    </section>
  );
}
