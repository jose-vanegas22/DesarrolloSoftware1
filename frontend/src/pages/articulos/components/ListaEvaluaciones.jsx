import { useEffect, useState } from "react";
import { getEvaluaciones } from "../../../api/articulosApi";

// El backend devuelve "aceptar" o "rechazar"; aqui se convierte en texto para mostrar
const DECISIONES = {
  aceptar: "Recomienda aceptar",
  rechazar: "Recomienda rechazar",
};

const formatearFecha = (fecha) =>
  new Date(fecha).toLocaleDateString("es-CO", { day: "2-digit", month: "long", year: "numeric" });

// Lista las evaluaciones del articulo. Solo la ve el autor y no muestra quien evaluo.
export default function ListaEvaluaciones({ articuloId }) {
  const [evaluaciones, setEvaluaciones] = useState([]);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    getEvaluaciones(articuloId)
      .then(({ data }) => setEvaluaciones(data))
      .catch(() => setError("No se pudieron cargar las evaluaciones."))
      .finally(() => setCargando(false));
  }, [articuloId]);

  return (
    <div className="detalle-tarjeta">
      <h2>Evaluaciones</h2>

      {cargando && <p className="detalle-texto">Cargando evaluaciones...</p>}
      {error && <p className="mensaje-error">{error}</p>}
      {!cargando && !error && evaluaciones.length === 0 && (
        <p className="detalle-texto">Tu artículo todavía no tiene evaluaciones.</p>
      )}

      {evaluaciones.length > 0 && (
        <ul className="detalle-autores">
          {evaluaciones.map((evaluacion, indice) => (
            <li key={evaluacion.id}>
              <div>
                <strong>Evaluación {indice + 1}</strong>
                <span className="detalle-etiqueta">{DECISIONES[evaluacion.decision] ?? evaluacion.decision}</span>
                <p>{formatearFecha(evaluacion.creado)}</p>
                <p className="detalle-texto">{evaluacion.comentarios}</p>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}