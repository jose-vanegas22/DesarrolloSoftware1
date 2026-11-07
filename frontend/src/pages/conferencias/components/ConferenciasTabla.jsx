const formatearFecha = (fecha) =>
  new Date(`${fecha}T00:00:00`).toLocaleDateString("es-CO", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });

export default function ConferenciasTabla({ conferencias }) {
  return (
    <div className="conferencias-tabla">
      <table>
        <thead>
          <tr>
            <th>Nombre</th>
            <th>Fecha de inicio</th>
            <th>Fecha de fin</th>
            <th>Estado</th>
          </tr>
        </thead>
        <tbody>
          {conferencias.map((conferencia) => (
            <tr key={conferencia.id}>
              <td className="conferencias-nombre">{conferencia.nombre}</td>
              <td className="conferencias-fecha">{formatearFecha(conferencia.fecha_inicio)}</td>
              <td className="conferencias-fecha">{formatearFecha(conferencia.fecha_fin)}</td>
              <td>
                <span className="conferencias-etiqueta">{conferencia.activo ? "Activa" : "Inactiva"}</span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
