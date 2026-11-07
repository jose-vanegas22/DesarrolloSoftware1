import { X } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { getFechasLimite, updateFechasLimite } from "../../../api/eventosApi";
import CampoFormulario from "../../../components/CampoFormulario";

const ETAPAS = [
  { campo: "postulacion", texto: "Postulación" },
  { campo: "revision", texto: "Revisión" },
  { campo: "version_corregida", texto: "Versión corregida" },
  { campo: "version_final", texto: "Versión final" },
];

const FORMULARIO_INICIAL = { postulacion: "", revision: "", version_corregida: "", version_final: "" };

const obtenerFormulario = (datos) => Object.fromEntries(
  ETAPAS.map(({ campo }) => [campo, datos[campo]?.slice(0, 16) ?? ""]),
);

export default function FechasLimiteModal({ conferencia, onCerrar, onGuardado }) {
  const [formulario, setFormulario] = useState(FORMULARIO_INICIAL);
  const [errores, setErrores] = useState({});
  const [cargando, setCargando] = useState(true);
  const [enviando, setEnviando] = useState(false);
  const modalRef = useRef(null);

  useEffect(() => {
    modalRef.current.showModal();
  }, []);

  useEffect(() => {
    getFechasLimite(conferencia.id)
      .then(({ data }) => setFormulario(obtenerFormulario(data)))
      .catch(() => setErrores({ general: ["No se pudieron cargar las fechas límite."] }))
      .finally(() => setCargando(false));
  }, [conferencia.id]);

  const handleChange = (e) => {
    setFormulario({ ...formulario, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrores({});
    setEnviando(true);

    try {
      await updateFechasLimite(conferencia.id, formulario);
      onGuardado();
    } catch (err) {
      const datos = err.response?.data;
      setErrores(typeof datos === "object" && datos !== null
        ? datos
        : { general: ["No se pudieron guardar las fechas límite. Intenta de nuevo."] });
      setEnviando(false);
    }
  };

  const mostrarError = (campo) => errores[campo] && <p className="mensaje-error">{[errores[campo]].flat()[0]}</p>;

  return (
    <dialog className="conferencia-modal conferencia-modal-fechas-limite" ref={modalRef} onCancel={onCerrar}>
      <form onSubmit={handleSubmit}>
        <div className="conferencia-modal-encabezado">
          <div>
            <h2>Fechas límite</h2>
            <p className="conferencia-modal-subtitulo">{conferencia.nombre}</p>
          </div>
          <button className="conferencia-modal-cerrar" type="button" aria-label="Cerrar" onClick={onCerrar}>
            <X size={18} aria-hidden="true" />
          </button>
        </div>

        <div className="conferencia-modal-fechas">
          {ETAPAS.map((etapa) => (
            <div key={etapa.campo}>
              <CampoFormulario
                id={`fecha-${etapa.campo}`}
                name={etapa.campo}
                etiqueta={etapa.texto}
                type="datetime-local"
                value={formulario[etapa.campo]}
                onChange={handleChange}
                disabled={cargando}
                required
              />
              {mostrarError(etapa.campo)}
            </div>
          ))}
        </div>

        {mostrarError("detail")}
        {mostrarError("general")}

        <div className="conferencia-modal-acciones">
          <button className="boton boton-secundario" type="button" onClick={onCerrar}>Cancelar</button>
          <button className="boton boton-principal" type="submit" disabled={cargando || enviando}>
            {enviando ? "Guardando..." : "Guardar fechas"}
          </button>
        </div>
      </form>
    </dialog>
  );
}
