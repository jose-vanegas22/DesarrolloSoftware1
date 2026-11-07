import { Pencil } from "lucide-react";
import { Link } from "react-router";


const formatearFecha = (fecha) =>
  new Date(`${fecha}T00:00:00`).toLocaleDateString("es-CO", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });

export default function ConferenciasTabla({ conferencias, onEditar, onFechas, esAutor }) {
  return (
    <div className="conferencias-tabla">
      <table>
        <thead>
          <tr>
            <th>Nombre</th>
            <th>Fecha de inicio</th>
            <th>Fecha de fin</th>
            <th>Estado</th>
            {(onEditar || esAutor) && <th>Acciones</th>}
          </tr>
        </thead>
        <tbody>
          {conferencias.map((conferencia) => (
            <tr key={conferencia.id}>
              <td className="conferencias-nombre">{conferencia.nombre}</td>
              <td className="conferencias-fecha">{formatearFecha(conferencia.fecha_inicio)}</td>
              <td className="conferencias-fecha">{formatearFecha(conferencia.fecha_fin)}</td>
              <td className="conferencias-estado">
                <span className="conferencias-etiqueta">{conferencia.activo ? "Activa" : "Inactiva"}</span>
              </td>
              {esAutor && (
                <td className="conferencias-acciones">
                  {conferencia.postulacion_abierta && (
                    <div className="conferencias-botones">
                      <Link
                        className="boton boton-secundario"
                        aria-label={`Postular artículo a ${conferencia.nombre}`}
                        to={`/articulos/postular?evento=${conferencia.id}`}
                      >
                        Postular artículo
                      </Link>
                    </div>
                  )}
                </td>
              )}
              {onEditar && (
                <td className="conferencias-acciones">
                  <div className="conferencias-botones">
                    <button
                      className="conferencias-accion"
                      type="button"
                      aria-label={`Editar ${conferencia.nombre}`}
                      onClick={() => onEditar(conferencia)}
                    >
                      <Pencil size={16} aria-hidden="true" />
                    </button>
                    <button
                      className="boton boton-secundario"
                      type="button"
                      aria-label={`Fechas límite de ${conferencia.nombre}`}
                      onClick={() => onFechas(conferencia)}
                    >
                      Fechas límite
                    </button>
                  </div>
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
