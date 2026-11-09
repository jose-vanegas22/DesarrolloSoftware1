import { useEffect, useRef, useState } from "react";
import { deleteUsuario } from "../../../api/usuariosApi";

export default function BorrarUsuarioModal({ usuario, onCerrar, onBorrado }) {
  const [error, setError] = useState("");
  const [borrando, setBorrando] = useState(false);
  const modalRef = useRef(null);

  useEffect(() => {
    modalRef.current.showModal();
  }, []);

  const handleBorrar = async () => {
    setError("");
    setBorrando(true);

    try {
      await deleteUsuario(usuario.id);
      onBorrado();
    } catch (err) {
      const detalle = err.response?.data?.detail;
      setError(detalle ? [detalle].flat()[0] : "No se pudo borrar el usuario. Intenta de nuevo.");
      setBorrando(false);
    }
  };

  return (
    <dialog className="usuario-modal usuario-modal-borrar" ref={modalRef} onCancel={onCerrar}>
      <h2>Borrar usuario</h2>
      <p>
        ¿Seguro que quieres borrar a <strong>{usuario.nombres} {usuario.apellidos}</strong>?
        Esta acción no se puede deshacer.
      </p>

      {error && <p className="mensaje-error">{error}</p>}

      <div className="usuario-modal-acciones">
        <button className="boton boton-secundario" type="button" onClick={onCerrar}>Cancelar</button>
        <button className="boton boton-peligro" type="button" disabled={borrando} onClick={handleBorrar}>
          {borrando ? "Borrando..." : "Borrar usuario"}
        </button>
      </div>
    </dialog>
  );
}
