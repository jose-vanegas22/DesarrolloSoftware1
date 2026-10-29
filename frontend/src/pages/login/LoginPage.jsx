import { useState } from "react";
import { useNavigate } from "react-router";
import { iniciarSesion } from "../../api/authApi";

export default function LoginPage() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await iniciarSesion(username, password);
      navigate("/inicio");
    } catch {
      setError("Usuario o contraseña incorrectos");
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <h1>Iniciar sesión</h1>
      <input placeholder="Usuario" value={username} onChange={(e) => setUsername(e.target.value)} />
      <input type="password" placeholder="Contraseña" value={password} onChange={(e) => setPassword(e.target.value)} />
      <button type="submit">Entrar</button>
      {error && <p>{error}</p>}
    </form>
  );
}
