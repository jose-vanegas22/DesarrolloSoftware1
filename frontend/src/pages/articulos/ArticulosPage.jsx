import { Eye, Filter, Plus } from "lucide-react";
import { useEffect, useState } from "react";
import { Link } from "react-router";
import { getArticulos } from "../../api/articulosApi";
import { obtenerRolActivo } from "../../api/authApi";
import CampoFormulario from "../../components/CampoFormulario";
import "./ArticulosPage.css";

const FILTROS_INICIALES = { buscar: "", autor: "", estado: "" };

const ESTADOS = [
  { valor: "postulado", texto: "Postulado" },
  { valor: "en_revision", texto: "En revisión" },
  { valor: "aceptado", texto: "Aceptado" },
  { valor: "rechazado", texto: "Rechazado" },
];

export default function ArticulosPage() {
  const [articulos, setArticulos] = useState([]);
  const [formulario, setFormulario] = useState(FILTROS_INICIALES);
  const [filtros, setFiltros] = useState(FILTROS_INICIALES);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState("");
  const esAutor = obtenerRolActivo() === "autor";

  useEffect(() => {
    getArticulos(filtros)
      .then(({ data }) => setArticulos(data))
      .catch(() => setError("No se pudieron cargar los artículos."))
      .finally(() => setCargando(false));
  }, [filtros]);

  const handleChange = (e) => {
    setFormulario({ ...formulario, [e.target.name]: e.target.value });
  };

  const handleFiltrar = (nuevosFiltros) => {
    setError("");
    setCargando(true);
    setFiltros(nuevosFiltros);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    handleFiltrar(formulario);
  };

  const handleLimpiar = () => {
    setFormulario(FILTROS_INICIALES);
    handleFiltrar(FILTROS_INICIALES);
  };

  return (
    <section className="articulos-pagina">
      <div className="articulos-encabezado">
        <h1>Artículos</h1>
        {esAutor && (
          <Link className="boton boton-principal" to="/articulos/postular">
            <Plus size={16} aria-hidden="true" />
            Postular artículo
          </Link>
        )}
      </div>

      <form className="articulos-filtros" onSubmit={handleSubmit}>
        <CampoFormulario id="filtro-titulo" name="buscar" etiqueta="Título" placeholder="Buscar por título..." value={formulario.buscar} onChange={handleChange} />
        {!esAutor && (
          <CampoFormulario id="filtro-autor" name="autor" etiqueta="Autor" placeholder="Nombre..." value={formulario.autor} onChange={handleChange} />
        )}
        <div className="campo">
          <label htmlFor="filtro-estado">Estado</label>
          <select id="filtro-estado" name="estado" value={formulario.estado} onChange={handleChange}>
            <option value="">Todos</option>
            {ESTADOS.map((estado) => (
              <option key={estado.valor} value={estado.valor}>{estado.texto}</option>
            ))}
          </select>
        </div>
        <button className="boton boton-principal" type="submit">
          <Filter size={16} aria-hidden="true" />
          Filtrar
        </button>
        <button className="boton boton-secundario" type="button" onClick={handleLimpiar}>Limpiar</button>
      </form>

      {error && <p className="mensaje-error">{error}</p>}
      {cargando && <p>Cargando artículos...</p>}
      {!cargando && !error && articulos.length === 0 && <p>No se encontraron artículos.</p>}
      {!cargando && !error && articulos.length > 0 && (
        <div className="articulos-tabla">
          <table>
            <thead>
              <tr>
                <th>Título</th>
                <th>Línea temática</th>
                <th>Conferencia</th>
                <th>Estado</th>
                <th>Acciones</th>
              </tr>
            </thead>
            <tbody>
              {articulos.map((articulo) => (
                <tr key={articulo.id}>
                  <td className="articulos-titulo">{articulo.titulo}</td>
                  <td className="articulos-dato">{articulo.linea_tematica_nombre}</td>
                  <td className="articulos-dato">{articulo.evento_nombre}</td>
                  <td className="articulos-estado">
                    <span className="articulos-etiqueta">{articulo.estado_nombre}</span>
                  </td>
                  
                  <td className="articulos-acciones">
                    <Link className="articulos-accion" to={`/articulos/${articulo.id}`} aria-label={`Ver detalle de ${articulo.titulo}`} title="Ver detalle">
                      <Eye size={16} aria-hidden="true" />
                    </Link>
                  </td>

                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
