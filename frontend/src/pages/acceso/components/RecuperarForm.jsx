import { useState } from "react";
import { Link } from "react-router";
import { solicitarCodigo } from "../../../api/authApi";
import CampoFormulario from "../../../components/CampoFormulario";

export default function RecuperarForm() {
  const [correo, setCorreo] = useState("");
  const [mensaje, setMensaje] = useState("");
  const [error, setError] = useState("");
  const [enviando, setEnviando] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setMensaje("");
    setError("");
    setEnviando(true);

    try {
      const { data } = await solicitarCodigo(correo);
      setMensaje(data.detail); // El backend responde lo mismo exista o no el correo
    } catch (err) {
      setError(err.response?.data?.correo?.[0] || "No se pudo enviar el código. Intenta de nuevo.");
    } finally {
      setEnviando(false);
    }
  };

  return (
    <form className="acceso-formulario" onSubmit={handleSubmit}>
      <h1>Recuperar contraseña</h1>
      <p>Escribe el correo de tu cuenta y te enviaremos un código de 6 dígitos.</p>

      <CampoFormulario
        id="recuperar-correo"
        etiqueta="Correo electrónico"
        type="email"
        autoComplete="email"
        placeholder="autor@universidad.edu"
        value={correo}
        onChange={(e) => setCorreo(e.target.value)}
        required
      />

      {mensaje && <p className="mensaje-exito">{mensaje}</p>}
      {error && <p className="mensaje-error">{error}</p>}

      <button className="boton boton-principal" type="submit" disabled={enviando}>
        {enviando ? "Enviando..." : "Enviar código"}
      </button>
      <Link className="acceso-olvido" to="/login">Volver a iniciar sesión</Link>
    </form>
  );
}
