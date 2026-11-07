import { X } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { createEvento, updateEvento } from "../../../api/eventosApi";
import CampoFormulario from "../../../components/CampoFormulario";

const FORMULARIO_INICIAL = { nombre: "", fecha_inicio: "", fecha_fin: "" };

export default function ConferenciaModal({ conferencia, onCerrar, onGuardado }) {
  const editando = Boolean(conferencia);
  const [formulario, setFormulario] = useState(() => (
    editando
      ? { nombre: conferencia.nombre, fecha_inicio: conferencia.fecha_inicio, fecha_fin: conferencia.fecha_fin }
      : FORMULARIO_INICIAL
  ));
  const [errores, setErrores] = useState({});
  const [enviando, setEnviando] = useState(false);
  const modalRef = useRef(null);

  useEffect(() => {
    modalRef.current.showModal();
  }, []);

  const handleChange = (e) => {
    setFormulario({ ...formulario, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrores({});
    setEnviando(true);

    try {
      if (editando) {
        await updateEvento(conferencia.id, formulario);
      } else {
        await createEvento(formulario);
      }

      onGuardado();
    } catch (err) {
      const datos = err.response?.data;
      setErrores(typeof datos === "object" && datos !== null
        ? datos
        : { general: ["No se pudo guardar la conferencia. Intenta de nuevo."] });
      setEnviando(false);
    }
  };

  const mostrarError = (campo) => errores[campo] && <p className="mensaje-error">{[errores[campo]].flat()[0]}</p>;

  return (
    <dialog className="conferencia-modal" ref={modalRef} onCancel={onCerrar}>
      <form onSubmit={handleSubmit}>
        <div className="conferencia-modal-encabezado">
          <h2>{editando ? "Editar conferencia" : "Crear conferencia"}</h2>
          <button className="conferencia-modal-cerrar" type="button" aria-label="Cerrar" onClick={onCerrar}>
            <X size={18} aria-hidden="true" />
          </button>
        </div>

        <div>
          <CampoFormulario id="conferencia-nombre" name="nombre" etiqueta="Nombre" value={formulario.nombre} onChange={handleChange} required />
          {mostrarError("nombre")}
        </div>

        <div className="conferencia-modal-fechas">
          <div>
            <CampoFormulario id="conferencia-inicio" name="fecha_inicio" etiqueta="Fecha de inicio" type="date" value={formulario.fecha_inicio} onChange={handleChange} required />
            {mostrarError("fecha_inicio")}
          </div>
          <div>
            <CampoFormulario id="conferencia-fin" name="fecha_fin" etiqueta="Fecha de fin" type="date" value={formulario.fecha_fin} onChange={handleChange} required />
            {mostrarError("fecha_fin")}
          </div>
        </div>

        {mostrarError("non_field_errors")}
        {mostrarError("detail")}
        {mostrarError("general")}

        <div className="conferencia-modal-acciones">
          <button className="boton boton-secundario" type="button" onClick={onCerrar}>Cancelar</button>
          <button className="boton boton-principal" type="submit" disabled={enviando}>
            {enviando ? "Guardando..." : "Guardar conferencia"}
          </button>
        </div>
      </form>
    </dialog>
  );
}
