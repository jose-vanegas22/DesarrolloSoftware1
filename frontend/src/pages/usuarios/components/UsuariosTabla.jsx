import { Pencil } from "lucide-react";

const obtenerRoles = (usuario) => {
  const roles = [];
  if (usuario.es_administrador) roles.push("Administrador");
  if (usuario.es_comite) roles.push("Comité científico");
  if (usuario.es_autor) roles.push("Autor");
  return roles;
};

export default function UsuariosTabla({ usuarios, onEditar }) {
  return (
    <div className="usuarios-tabla">
      <table>
        <thead>
          <tr>
            <th>Nombre</th>
            <th>Correo</th>
            <th>Teléfono</th>
            <th>Roles</th>
            <th>Estado</th>
            {onEditar && <th>Acciones</th>}
          </tr>
        </thead>
        <tbody>
          {usuarios.map((usuario) => (
            <tr key={usuario.id}>
              <td className="usuarios-nombre">{usuario.nombres} {usuario.apellidos}</td>
              <td className="usuarios-dato">{usuario.correo}</td>
              <td className="usuarios-dato">{usuario.telefono || "Sin teléfono"}</td>
              <td>
                <div className="usuarios-roles">
                  {obtenerRoles(usuario).map((rol) => (
                    <span className="usuarios-etiqueta" key={rol}>{rol}</span>
                  ))}
                </div>
              </td>
              <td className="usuarios-estado">{usuario.activo ? "Activo" : "Inactivo"}</td>
              {onEditar && (
                <td className="usuarios-acciones">
                  <button
                    className="usuarios-accion"
                    type="button"
                    aria-label={`Editar a ${usuario.nombres} ${usuario.apellidos}`}
                    onClick={() => onEditar(usuario)}
                  >
                    <Pencil size={16} aria-hidden="true" />
                  </button>
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
