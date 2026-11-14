import { useState } from "react";
import { evaluarArticulo } from "../../../api/articulosApi";

export default function FormularioEvaluacion({ articuloId, evaluacion, onEvaluado }) {
  const [decision, setDecision] = useState("");
  const [comentarios, setComentarios] = useState("");
  const [enviando, setEnviando] = useState(false);
  const [error, setError] = useState("");
  const [registrada, setRegistrada] = useState(null);
  const revision = registrada || evaluacion?.revision;

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (enviando || registrada) return;
    if (!decision || !comentarios.trim()) {
      setError("Selecciona una decisión y escribe los comentarios de retroalimentación.");
      return;
    }
    setEnviando(true);
    setError("");
    try {
      const { data } = await evaluarArticulo(articuloId, { decision, comentarios: comentarios.trim() });
      setRegistrada(data);
      onEvaluado();
    } catch (err) {
      const datos = err.response?.data;
      setError(
        typeof datos === "string" ? datos :
          Object.values(datos || {}).flat().join(" ") || "No se pudo registrar la evaluación. Intenta de nuevo."
      );
    } finally {
      setEnviando(false);
    }
  };

  return (
    <section className="detalle-tarjeta evaluacion-tarjeta">
      <h2>Evaluación del artículo</h2>
      {revision ? (
        <>
          <p className="mensaje-exito" role="status">Tu evaluación quedó registrada.</p>
          <p><strong>Decisión:</strong> {revision.decision === "aceptar" ? "Aceptar" : "Rechazar"}</p>
          <h3>Comentarios de retroalimentación</h3>
          <p className="detalle-texto">{revision.comentarios}</p>
        </>
      ) : evaluacion?.puede_evaluar ? (
        <form className="evaluacion-formulario" onSubmit={handleSubmit}>
          <p className="detalle-texto">Revisa el PDF antes de enviar. La evaluación se registra una sola vez.</p>
          <fieldset disabled={enviando}>
            <div className="campo">
              <label htmlFor="evaluacion-decision">Decisión</label>
              <select id="evaluacion-decision" required value={decision} onChange={(e) => setDecision(e.target.value)}>
                <option value="">Selecciona una decisión</option>
                <option value="aceptar">Aceptar</option>
                <option value="rechazar">Rechazar</option>
              </select>
            </div>
            <div className="campo">
              <label htmlFor="evaluacion-comentarios">Comentarios de retroalimentación</label>
              <textarea id="evaluacion-comentarios" required rows={7} value={comentarios} onChange={(e) => setComentarios(e.target.value)} />
            </div>
            {error && <p className="mensaje-error" role="alert">{error}</p>}
            <button className="boton boton-principal" type="submit">{enviando ? "Registrando..." : "Registrar evaluación"}</button>
          </fieldset>
        </form>
      ) : <p className="detalle-texto">{evaluacion?.motivo || "La evaluación no está disponible."}</p>}
    </section>
  );
}
