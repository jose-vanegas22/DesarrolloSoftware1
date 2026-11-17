import { useState } from "react";
import { Link, useNavigate } from "react-router";
import { restablecerContrasena, solicitarCodigo } from "../../../api/authApi";
import CampoFormulario from "../../../components/CampoFormulario";

export default function RecuperarForm() {
  const [correo, setCorreo] = useState("");
  const [codigo, setCodigo] = useState("");
  const [password, setPassword] = useState("");
  const [confirmacion, setConfirmacion] = useState("");
  const [codigoEnviado, setCodigoEnviado] = useState(false); // false = paso 1 (pedir codigo), true = paso 2 (restablecer)
  const [mensaje, setMensaje] = useState("");
  const [error, setError] = useState("");
  const [enviando, setEnviando] = useState(false);
  const navigate = useNavigate();

  // Paso 1: pide el codigo al correo
  const handleSolicitar = async (e) => {
    e.preventDefault();
    setMensaje("");
    setError("");
    setEnviando(true);

    try {
      const { data } = await solicitarCodigo(correo);
      setMensaje(data.detail); // El backend responde lo mismo exista o no el correo
      setCodigoEnviado(true);
    } catch (err) {
      setError(err.response?.data?.correo?.[0] || "No se pudo enviar el código. Intenta de nuevo.");
    } finally {
      setEnviando(false);
    }
  };

  // Paso 2: envia el codigo y la contraseña nueva
  const handleRestablecer = async (e) => {
    e.preventDefault();
    setError("");

    if (password !== confirmacion) {
      setError("Las contraseñas no coinciden.");
      return;
    }

    setEnviando(true);
    try {
      const { data } = await restablecerContrasena(correo, codigo, password);
      navigate("/login", { state: { mensaje: data.detail } }); // El login muestra el mensaje de exito
    } catch (err) {
      const datos = err.response?.data;
      setError(
        datos?.detail ||
          datos?.codigo?.[0] ||
          datos?.password?.join(" ") ||
          "No se pudo restablecer la contraseña. Intenta de nuevo."
      );
    } finally {
      setEnviando(false);
    }
  };

  if (codigoEnviado) {
    return (
      <form className="acceso-formulario" onSubmit={handleRestablecer}>
        <h1>Restablecer contraseña</h1>
        {mensaje && <p className="mensaje-exito">{mensaje}</p>}

        <CampoFormulario
          id="recuperar-codigo"
          etiqueta="Código de 6 dígitos"
          inputMode="numeric"
          maxLength={6}
          autoComplete="one-time-code"
          value={codigo}
          onChange={(e) => setCodigo(e.target.value)}
          required
        />
        <CampoFormulario
          id="recuperar-password"
          etiqueta="Contraseña nueva"
          type="password"
          autoComplete="new-password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />
        <CampoFormulario
          id="recuperar-confirmacion"
          etiqueta="Confirmar contraseña nueva"
          type="password"
          autoComplete="new-password"
          value={confirmacion}
          onChange={(e) => setConfirmacion(e.target.value)}
          required
        />

        {error && <p className="mensaje-error">{error}</p>}

        <button className="boton boton-principal" type="submit" disabled={enviando}>
          {enviando ? "Restableciendo..." : "Restablecer contraseña"}
        </button>
        <button className="acceso-olvido" type="button" onClick={() => setCodigoEnviado(false)}>
          Pedir otro código
        </button>
      </form>
    );
  }

  return (
    <form className="acceso-formulario" onSubmit={handleSolicitar}>
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

      {error && <p className="mensaje-error">{error}</p>}

      <button className="boton boton-principal" type="submit" disabled={enviando}>
        {enviando ? "Enviando..." : "Enviar código"}
      </button>
      <Link className="acceso-olvido" to="/login">Volver a iniciar sesión</Link>
    </form>
  );
}
