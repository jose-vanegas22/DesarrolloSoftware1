import { Filter, Plus } from "lucide-react";
import { useEffect, useState } from "react";
import { obtenerRolActivo } from "../../api/authApi";
import { getEventos } from "../../api/eventosApi";
import CampoFormulario from "../../components/CampoFormulario";
import ConferenciaModal from "./components/ConferenciaModal";
import ConferenciasTabla from "./components/ConferenciasTabla";
import "./ConferenciasPage.css";

export default function ConferenciasPage() {
  const [conferencias, setConferencias] = useState([]);
  const [buscar, setBuscar] = useState("");
  const [filtros, setFiltros] = useState({});
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState("");
  const [creando, setCreando] = useState(false);
  const [mensaje, setMensaje] = useState("");
  const esGestor = ["administrador", "comite"].includes(obtenerRolActivo());

  useEffect(() => {
    getEventos(filtros)
      .then(({ data }) => setConferencias(data))
      .catch(() => setError("No se pudieron cargar las conferencias."))
      .finally(() => setCargando(false));
  }, [filtros]);

  const handleFiltrar = (nuevosFiltros) => {
    setError("");
    setCargando(true);
    setFiltros(nuevosFiltros);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    handleFiltrar({ buscar });
  };

  const handleLimpiar = () => {
    setBuscar("");
    handleFiltrar({});
  };

  const handleGuardado = () => {
    setCreando(false);
    setMensaje("Conferencia creada correctamente.");
    handleFiltrar({ ...filtros });
  };

  return (
    <section className="conferencias-pagina">
      <div className="conferencias-encabezado">
        <h1>Conferencias</h1>
        {esGestor && (
          <button className="boton boton-principal" type="button" onClick={() => setCreando(true)}>
            <Plus size={16} aria-hidden="true" />
            Crear conferencia
          </button>
        )}
      </div>

      <form className="conferencias-filtros" onSubmit={handleSubmit}>
        <CampoFormulario
          id="conferencia-buscar"
          etiqueta="Buscar"
          placeholder="Buscar por nombre..."
          value={buscar}
          onChange={(e) => setBuscar(e.target.value)}
        />
        <button className="boton boton-principal" type="submit">
          <Filter size={16} aria-hidden="true" />
          Filtrar
        </button>
        <button className="boton boton-secundario" type="button" onClick={handleLimpiar}>Limpiar</button>
      </form>

      {mensaje && <p className="mensaje-exito">{mensaje}</p>}
      {error && <p className="mensaje-error">{error}</p>}
      {cargando && <p>Cargando conferencias...</p>}
      {!cargando && !error && conferencias.length === 0 && <p>No se encontraron conferencias.</p>}
      {!cargando && !error && conferencias.length > 0 && <ConferenciasTabla conferencias={conferencias} />}

      {creando && <ConferenciaModal onCerrar={() => setCreando(false)} onGuardado={handleGuardado} />}
    </section>
  );
}
