import { useEffect, useRef, useState } from "react";
import { deshabilitarArticulo } from "../../../api/articulosApi";

// Advertencia y confirmacion antes de deshabilitar. La accion no se puede deshacer.
export default function DeshabilitarArticuloModal({ articulo, onCerrar, onDeshabilitado }) {
  const [error, setError] = useState("");
  const [deshabilitando, setDeshabilitando] = useState(false);
  const modalRef = useRef(null);

  useEffect(() => {
    modalRef.current.showModal();
  }, []);

  const handleDeshabilitar = async () => {
    setError("");
    setDeshabilitando(true);

    try {
      await deshabilitarArticulo(articulo.id);
      onDeshabilitado();
    } catch (err) {
      const estado = err.response?.status;
      setError(
        estado === 403
          ? "No tienes permiso para deshabilitar artículos."
          : estado === 404
            ? "El artículo no existe o ya fue deshabilitado."
            : "No se pudo deshabilitar el artículo. Intenta de nuevo."
      );
      setDeshabilitando(false);
    }
  };

  return (
    <dialog className="detalle-modal" ref={modalRef} onCancel={onCerrar}>
      <h2>Deshabilitar artículo</h2>
      <p>
        ¿Seguro que quieres deshabilitar <strong>{articulo.titulo}</strong>?
      </p>
      <p className="mensaje-error">
        Esta acción no se puede deshacer. El artículo dejará de aparecer en las consultas y no se podrá volver a habilitar.
      </p>

      {error && <p className="mensaje-error">{error}</p>}

      <div className="detalle-modal-acciones">
        <button className="boton boton-secundario" type="button" onClick={onCerrar}>Cancelar</button>
        <button className="boton boton-principal" type="button" disabled={deshabilitando} onClick={handleDeshabilitar}>
          {deshabilitando ? "Deshabilitando..." : "Sí, deshabilitar"}
        </button>
      </div>
    </dialog>
  );
}