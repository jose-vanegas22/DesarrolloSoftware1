import { useRef, useState } from "react";
import ReCAPTCHA from "react-google-recaptcha";
import { useNavigate } from "react-router";
import { registrarAutor } from "../../../api/authApi";
import CampoFormulario from "../../../components/CampoFormulario";

const FORMULARIO_INICIAL = {
  nombres: "",
  apellidos: "",
  correo: "",
  telefono: "",
  password: "",
  confirmacion: "",
};

export default function RegistroForm() {
  const [formulario, setFormulario] = useState(FORMULARIO_INICIAL);
  const [captcha, setCaptcha] = useState("");
  const [errores, setErrores] = useState([]);
  const [enviando, setEnviando] = useState(false);
  const captchaRef = useRef(null);
  const navigate = useNavigate();

  const handleChange = (e) => {
    setFormulario({ ...formulario, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (formulario.password !== formulario.confirmacion) {
      setErrores(["Las contraseñas no coinciden"]);
      return;
    }

    setErrores([]);
    setEnviando(true);

    try {
      const { nombres, apellidos, correo, telefono, password } = formulario;
      await registrarAutor({ nombres, apellidos, correo, telefono, password, captcha });
      navigate("/login", { state: { mensaje: "Cuenta creada. Ya puedes iniciar sesión." } });
    } catch (err) {
      const datos = err.response?.data;
      setErrores(typeof datos === "object" ? Object.values(datos).flat() : ["No se pudo crear la cuenta. Intenta de nuevo."]);
      captchaRef.current?.reset();
      setCaptcha("");
    } finally {
      setEnviando(false);
    }
  };

  return (
    <form className="acceso-formulario" onSubmit={handleSubmit}>
      <h1>Crear cuenta de autor</h1>

      <div className="acceso-fila">
        <CampoFormulario
          id="registro-nombres"
          name="nombres"
          etiqueta="Nombres"
          autoComplete="given-name"
          placeholder="Ej. Ana"
          value={formulario.nombres}
          onChange={handleChange}
          required
        />
        <CampoFormulario
          id="registro-apellidos"
          name="apellidos"
          etiqueta="Apellidos"
          autoComplete="family-name"
          placeholder="Ej. Gómez"
          value={formulario.apellidos}
          onChange={handleChange}
          required
        />
      </div>

      <CampoFormulario
        id="registro-correo"
        name="correo"
        etiqueta="Correo electrónico"
        type="email"
        autoComplete="email"
        placeholder="autor@universidad.edu"
        value={formulario.correo}
        onChange={handleChange}
        required
      />
      <CampoFormulario
        id="registro-telefono"
        name="telefono"
        etiqueta="Teléfono (opcional)"
        type="tel"
        autoComplete="tel"
        placeholder="3001234567"
        value={formulario.telefono}
        onChange={handleChange}
      />

      <div className="acceso-fila">
        <CampoFormulario
          id="registro-password"
          name="password"
          etiqueta="Contraseña"
          type="password"
          autoComplete="new-password"
          placeholder="••••••••••••"
          value={formulario.password}
          onChange={handleChange}
          required
        />
        <CampoFormulario
          id="registro-confirmacion"
          name="confirmacion"
          etiqueta="Confirmar contraseña"
          type="password"
          autoComplete="new-password"
          placeholder="••••••••••••"
          value={formulario.confirmacion}
          onChange={handleChange}
          required
        />
      </div>

      <div className="acceso-captcha">
        <ReCAPTCHA
          ref={captchaRef}
          sitekey={import.meta.env.VITE_RECAPTCHA_SITE_KEY}
          onChange={(token) => setCaptcha(token ?? "")}
        />
      </div>

      {errores.map((mensaje) => <p className="mensaje-error" key={mensaje}>{mensaje}</p>)}

      <button className="boton boton-principal" type="submit" disabled={!captcha || enviando}>
        {enviando ? "Creando cuenta..." : "Crear cuenta"}
      </button>
    </form>
  );
}
