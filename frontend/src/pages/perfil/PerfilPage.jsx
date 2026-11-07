import { useEffect, useState } from "react";
import { getPerfil, updatePerfil } from "../../api/usuariosApi";
import CampoFormulario from "../../components/CampoFormulario";
import "./PerfilPage.css";

export default function PerfilPage() {
  const [perfil, setPerfil] = useState(null);
  const [errores, setErrores] = useState({});
  const [error, setError] = useState("");
  const [mensaje, setMensaje] = useState("");
  const [guardando, setGuardando] = useState(false);

  // Carga los datos del usuario que inicio sesion
  useEffect(() => {
    getPerfil()
      .then(({ data }) => setPerfil(data))
      .catch(() => setError("No se pudo cargar tu perfil."));
  }, []);

  const handleChange = (e) => {
    setPerfil({ ...perfil, [e.target.name]: e.target.value });
  };

  // Envia solo nombres, apellidos y telefono, el correo esta deshabilitado y los roles es solo informativo
  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrores({});
    setError("");
    setMensaje("");
    setGuardando(true);

    try {
      const { nombres, apellidos, telefono } = perfil;
      const { data } = await updatePerfil({ nombres, apellidos, telefono });
      setPerfil(data);
      setMensaje("Perfil actualizado correctamente.");
    } catch (err) {
      const datos = err.response?.data;
      if (typeof datos === "object" && datos !== null) {
        setErrores(datos);
      } else {
        setError("No se pudo actualizar tu perfil. Intenta de nuevo.");
      }
    } finally {
      setGuardando(false);
    }
  };

  const mostrarError = (campo) => errores[campo] && <p className="mensaje-error">{errores[campo][0]}</p>;

  // Muestra cargando o el error mientras no haya datos
  if (!perfil) {
    return (
      <section className="perfil-pagina">
        <h1>Mi perfil</h1>
        {error ? <p className="mensaje-error">{error}</p> : <p>Cargando perfil...</p>}
      </section>
    );
  }

  const roles = [
    perfil.es_administrador && "Administrador",
    perfil.es_comite && "Comité científico",
    perfil.es_autor && "Autor",
  ].filter(Boolean);

  return (
    <section className="perfil-pagina">
      <h1>Mi perfil</h1>

      <form className="perfil-tarjeta" onSubmit={handleSubmit}>
        <h2>Datos personales</h2>

        <div className="perfil-campos">
          <div>
            <CampoFormulario id="perfil-nombres" name="nombres" etiqueta="Nombres" value={perfil.nombres} onChange={handleChange} required />
            {mostrarError("nombres")}
          </div>
          <div>
            <CampoFormulario id="perfil-apellidos" name="apellidos" etiqueta="Apellidos" value={perfil.apellidos} onChange={handleChange} required />
            {mostrarError("apellidos")}
          </div>
          <CampoFormulario id="perfil-correo" etiqueta="Correo electrónico" type="email" value={perfil.correo} disabled />
          <div>
            <CampoFormulario id="perfil-telefono" name="telefono" etiqueta="Teléfono" type="tel" value={perfil.telefono} onChange={handleChange} />
            {mostrarError("telefono")}
          </div>
        </div>

        <h2>Roles</h2>
        <div className="perfil-roles">
          {roles.map((rol) => <span className="perfil-etiqueta" key={rol}>{rol}</span>)}
        </div>

        {mensaje && <p className="mensaje-exito">{mensaje}</p>}
        {error && <p className="mensaje-error">{error}</p>}

        <div className="perfil-acciones">
          <button className="boton boton-principal" type="submit" disabled={guardando}>
            {guardando ? "Guardando..." : "Guardar cambios"}
          </button>
        </div>
      </form>
    </section>
  );
}
