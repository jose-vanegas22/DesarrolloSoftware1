const obtenerRoles = (usuario) => {
  const roles = [];
  if (usuario.es_administrador) roles.push("Administrador");
  if (usuario.es_comite) roles.push("Comité científico");
  if (usuario.es_autor) roles.push("Autor");
  return roles;
};

export default function UsuariosTabla({ usuarios }) {
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
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
