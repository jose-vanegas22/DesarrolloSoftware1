import { useRef, useState } from "react";
import ReCAPTCHA from "react-google-recaptcha";
import { useNavigate } from "react-router";
import { iniciarSesion } from "../../api/authApi";

export default function LoginPage() {
  const [correo, setCorreo] = useState("");
  const [password, setPassword] = useState("");
  const [captcha, setCaptcha] = useState("");
  const [error, setError] = useState("");
  const captchaRef = useRef(null);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await iniciarSesion(correo, password, captcha);
      navigate("/inicio");
    } catch (err) {
      const datos = err.response?.data;
      setError(datos?.detail || datos?.captcha?.[0] || "Correo o contraseña incorrectos");
      captchaRef.current?.reset();
      setCaptcha("");
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <h1>Iniciar sesión</h1>
      <input type="email" placeholder="Correo" value={correo} onChange={(e) => setCorreo(e.target.value)} />
      <input type="password" placeholder="Contraseña" value={password} onChange={(e) => setPassword(e.target.value)} />
      <ReCAPTCHA
        ref={captchaRef}
        sitekey={import.meta.env.VITE_RECAPTCHA_SITE_KEY}
        onChange={(token) => setCaptcha(token || "")}
      />
      <button type="submit" disabled={!captcha}>Entrar</button>
      {error && <p>{error}</p>}
    </form>
  );
}
