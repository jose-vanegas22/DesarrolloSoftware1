import { useRef, useState } from "react";
import ReCAPTCHA from "react-google-recaptcha";
import { useLocation, useNavigate } from "react-router";
import { iniciarSesion } from "../../../api/authApi";
import CampoFormulario from "../../../components/CampoFormulario";

// useState guarda el estado de las variables y useRef guarda la referencia del componente captcha para poder resetearlo

export default function LoginForm() {
  const [correo, setCorreo] = useState(""); // El set captura el valor del input y el useState lo guarda en la variable correo, que se envia al backend para iniciar sesion
  const [password, setPassword] = useState("");
  const [captcha, setCaptcha] = useState("");
  const [errores, setErrores] = useState([]);
  const [enviando, setEnviando] = useState(false);
  const captchaRef = useRef(null); // Guarda la referencia del componente captcha para poder resetearlo en caso de error
  const navigate = useNavigate(); // Crea la funcion para ir a otra pestaña, en este caso a la de inicio o seleccionar rol
  const { state } = useLocation(); // Toma el mensaje que envia el resgistro

  const handleSubmit = async (e) => { // Se ejecuta al presionar iniciar sesion
    e.preventDefault(); // Evita que se recargue la pagina al enviar el formulario
    setErrores([]); // Limpia los errores anteriores
    setEnviando(true); // Marca que se esta enviando el formulario para deshabilitar el boton de enviar

    try {
      const { rol_activo } = await iniciarSesion(correo, password, captcha);
      navigate(rol_activo ? "/inicio" : "/seleccionar-rol", { replace: true });
    } catch (err) {
      const datos = err.response?.data;
      setErrores([datos?.detail || datos?.captcha?.[0] || "No se pudo iniciar sesión. Intenta de nuevo."]);
      captchaRef.current?.reset();
      setCaptcha("");
    } finally {
      setEnviando(false);
    }
  };

// Todo lo que se ve en pantalla
  return (
    <form className="acceso-formulario" onSubmit={handleSubmit}>
      <h1>Iniciar sesión</h1>
      {state?.mensaje && <p className="mensaje-exito">{state.mensaje}</p>}

      <CampoFormulario
        id="login-correo"
        etiqueta="Correo electrónico"
        type="email"
        autoComplete="email"
        placeholder="autor@universidad.edu"
        value={correo}
        onChange={(e) => setCorreo(e.target.value)}
        required
      />
      <CampoFormulario
        id="login-password"
        etiqueta="Contraseña"
        type="password"
        autoComplete="current-password"
        placeholder="••••••••••••"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        required
      />
      <span className="acceso-olvido">¿Olvidaste tu contraseña?</span>


      <div className="acceso-captcha"> 
        <ReCAPTCHA
          ref={captchaRef}
          sitekey={import.meta.env.VITE_RECAPTCHA_SITE_KEY}
          onChange={(token) => setCaptcha(token ?? "")} // Recibe el token del captcha y lo guarda en la variable captcha, si no hay token lo deja vacio
        />
      </div>

      {errores.map((mensaje) => <p className="mensaje-error" key={mensaje}>{mensaje}</p>)}

      <button className="boton boton-principal" type="submit" disabled={!captcha || enviando}>
        {enviando ? "Ingresando..." : "Iniciar sesión"}
      </button>
    </form>
  );
}
