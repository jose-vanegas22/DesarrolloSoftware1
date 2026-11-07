import { Filter, Plus } from "lucide-react";
import { useEffect, useState } from "react";
import { obtenerRolActivo } from "../../api/authApi";
import { getEventos } from "../../api/eventosApi";
import CampoFormulario from "../../components/CampoFormulario";
import ConferenciaModal from "./components/ConferenciaModal";
import ConferenciasTabla from "./components/ConferenciasTabla";
import FechasLimiteModal from "./components/FechasLimiteModal";
import "./ConferenciasPage.css";
import { useLocation } from "react-router";

export default function ConferenciasPage() {
  const [conferencias, setConferencias] = useState([]);
  const [buscar, setBuscar] = useState("");
  const [filtros, setFiltros] = useState({});
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState("");
  const [creando, setCreando] = useState(false);
  const [conferenciaEditada, setConferenciaEditada] = useState(null);
  const [conferenciaFechas, setConferenciaFechas] = useState(null);
  const { state } = useLocation(); // Nos permite recibir un mensaje desde otra pagina, por ejemplo cuando se postula un articulo y se redirige a esta pagina
  const [mensaje, setMensaje] = useState(state?.mensaje ?? ""); // Si hay un mensaje en el estado de la ubicacion, lo usamos, sino dejamos vacio
  const esGestor = ["administrador", "comite"].includes(obtenerRolActivo());
  const esAutor = obtenerRolActivo() === "autor";

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

  const handleCerrarModal = () => {
    setCreando(false);
    setConferenciaEditada(null);
    setConferenciaFechas(null);
  };

  const handleGuardado = () => {
    setMensaje(conferenciaEditada ? "Conferencia actualizada correctamente." : "Conferencia creada correctamente.");
    handleCerrarModal();
    handleFiltrar({ ...filtros });
  };

  const handleFechasGuardadas = () => {
    setMensaje("Fechas límite guardadas correctamente.");
    handleCerrarModal();
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
      {!cargando && !error && conferencias.length > 0 && (
        <ConferenciasTabla
          conferencias={conferencias}
          onEditar={esGestor ? setConferenciaEditada : undefined}
          onFechas={setConferenciaFechas}
          esAutor={esAutor}
        />
      )}

      {(creando || conferenciaEditada) && (
        <ConferenciaModal conferencia={conferenciaEditada} onCerrar={handleCerrarModal} onGuardado={handleGuardado} />
      )}

      {conferenciaFechas && (
        <FechasLimiteModal conferencia={conferenciaFechas} onCerrar={handleCerrarModal} onGuardado={handleFechasGuardadas} />
      )}
    </section>
  );
}
