import { X } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { createUsuario, updateUsuario } from "../../../api/usuariosApi";
import CampoFormulario from "../../../components/CampoFormulario";

const FORMULARIO_INICIAL = {
  nombres: "",
  apellidos: "",
  correo: "",
  telefono: "",
  password: "",
  confirmacion: "",
  es_administrador: false,
  es_comite: false,
  es_autor: false,
  activo: true,
};

const ROLES = [
  { campo: "es_administrador", texto: "Administrador" },
  { campo: "es_comite", texto: "Comité científico" },
  { campo: "es_autor", texto: "Autor" },
];

const obtenerFormulario = (usuario) => {
  if (!usuario) return FORMULARIO_INICIAL;

  return {
    ...FORMULARIO_INICIAL,
    nombres: usuario.nombres,
    apellidos: usuario.apellidos,
    correo: usuario.correo,
    telefono: usuario.telefono,
    es_administrador: usuario.es_administrador,
    es_comite: usuario.es_comite,
    es_autor: usuario.es_autor,
    activo: usuario.activo,
  };
};


export default function UsuarioModal({ usuario, onCerrar, onGuardado }) {
  const editando = Boolean(usuario);
  const [formulario, setFormulario] = useState(() => obtenerFormulario(usuario));
  const [errores, setErrores] = useState({});
  const [enviando, setEnviando] = useState(false);
  const modalRef = useRef(null);

  useEffect(() => {
    modalRef.current.showModal();
  }, []);

  const handleChange = (e) => {
    const { name, type, checked, value } = e.target;
    setFormulario({ ...formulario, [name]: type === "checkbox" ? checked : value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (formulario.password !== formulario.confirmacion) {
      setErrores({ confirmacion: ["Las contraseñas no coinciden."] });
      return;
    }

    setErrores({});
    setEnviando(true);

    try {
      const datos = { ...formulario };
      delete datos.confirmacion;

      if (editando) {
        if (!datos.password) delete datos.password;
        await updateUsuario(usuario.id, datos);
      } else {
        await createUsuario(datos);
      }

      onGuardado();

    } catch (err) {
      const datos = err.response?.data;
      setErrores(typeof datos === "object" && datos !== null
        ? datos
        : { general: ["No se pudo guardar el usuario. Intenta de nuevo."] });
      setEnviando(false);
    }
  };

  const mostrarError = (campo) => errores[campo] && <p className="mensaje-error">{errores[campo][0]}</p>;

  return (
    <dialog className="usuario-modal" ref={modalRef} onCancel={onCerrar}>
      <form onSubmit={handleSubmit}>
        <div className="usuario-modal-encabezado">
          <h2>{editando ? "Editar usuario" : "Crear usuario"}</h2>
          <button className="usuario-modal-cerrar" type="button" aria-label="Cerrar" onClick={onCerrar}>
            <X size={18} aria-hidden="true" />
          </button>
        </div>

        <div className="usuario-modal-campos">
          <div>
            <CampoFormulario id="usuario-nombres" name="nombres" etiqueta="Nombres" value={formulario.nombres} onChange={handleChange} required />
            {mostrarError("nombres")}
          </div>
          <div>
            <CampoFormulario id="usuario-apellidos" name="apellidos" etiqueta="Apellidos" value={formulario.apellidos} onChange={handleChange} required />
            {mostrarError("apellidos")}
          </div>
          <div>
            <CampoFormulario id="usuario-correo" name="correo" etiqueta="Correo electrónico" type="email" value={formulario.correo} onChange={handleChange} required />
            {mostrarError("correo")}
          </div>
          <div>
            <CampoFormulario id="usuario-telefono" name="telefono" etiqueta="Teléfono (opcional)" type="tel" value={formulario.telefono} onChange={handleChange} />
            {mostrarError("telefono")}
          </div>
          <div>
            <CampoFormulario id="usuario-password" name="password" etiqueta={editando ? "Nueva contraseña (opcional)" : "Contraseña"} type="password" autoComplete="new-password" value={formulario.password} onChange={handleChange} required={!editando} />
            {mostrarError("password")}
          </div>
          <div>
            <CampoFormulario id="usuario-confirmacion" name="confirmacion" etiqueta="Confirmar contraseña" type="password" autoComplete="new-password" value={formulario.confirmacion} onChange={handleChange} required={!editando} />
            {mostrarError("confirmacion")}
          </div>
        </div>

        <fieldset className="usuario-modal-roles">
          <legend>Roles</legend>
          {ROLES.map((rol) => (
            <label key={rol.campo}>
              <input type="checkbox" name={rol.campo} checked={formulario[rol.campo]} onChange={handleChange} />
              {rol.texto}
            </label>
          ))}
        </fieldset>

        {editando && (
          <fieldset className="usuario-modal-roles">
            <legend>Estado</legend>
            <label>
              <input type="checkbox" name="activo" checked={formulario.activo} onChange={handleChange} />
              Usuario activo
            </label>
          </fieldset>
        )}

        {mostrarError("non_field_errors")}
        {mostrarError("general")}

        <div className="usuario-modal-acciones">
          <button className="boton boton-secundario" type="button" onClick={onCerrar}>Cancelar</button>
          <button className="boton boton-principal" type="submit" disabled={enviando}>
            {enviando ? "Guardando..." : "Guardar usuario"}
          </button>
        </div>
      </form>
    </dialog>
  );
}
