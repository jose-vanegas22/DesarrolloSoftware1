import { useEffect, useRef, useState } from "react";
import { quitarCoautor } from "../../../api/articulosApi";

export default function QuitarCoautorModal({ articuloId, coautor, onCerrar, onQuitado }) {
  const [error, setError] = useState("");
  const [quitando, setQuitando] = useState(false);
  const modalRef = useRef(null);

  useEffect(() => {
    modalRef.current.showModal();
  }, []);

  const handleQuitar = async () => {
    setError("");
    setQuitando(true);

    try {
      await quitarCoautor(articuloId, coautor.id);
      onQuitado();
    } catch (err) {
      const detalle = err.response?.data?.detail;
      setError(detalle ? [detalle].flat()[0] : "No se pudo quitar el coautor. Intenta de nuevo.");
      setQuitando(false);
    }
  };

  return (
    <dialog className="detalle-modal" ref={modalRef} onCancel={onCerrar}>
      <h2>Quitar coautor</h2>
      <p>
        ¿Seguro que quieres quitar a <strong>{coautor.nombre}</strong> de los autores de este artículo?
      </p>

      {error && <p className="mensaje-error">{error}</p>}

      <div className="detalle-modal-acciones">
        <button className="boton boton-secundario" type="button" onClick={onCerrar}>Cancelar</button>
        <button className="boton boton-principal" type="button" disabled={quitando} onClick={handleQuitar}>
          {quitando ? "Quitando..." : "Quitar coautor"}
        </button>
      </div>
    </dialog>
  );
}
