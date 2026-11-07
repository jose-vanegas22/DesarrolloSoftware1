import { useState } from "react";
import { NavLink, Outlet, useNavigate } from "react-router";
import { cerrarSesion, obtenerRolActivo } from "../api/authApi";
import "./MenuPrincipal.css";
import { Menu, X } from "lucide-react";

// Indica que opciones puede ver cada rol, y el texto que se muestra en el menu
const OPCIONES = [
  { ruta: "/inicio", texto: "Inicio", roles: ["administrador", "comite", "autor"] },
  { ruta: "/usuarios", texto: "Usuarios", roles: ["administrador", "comite"] },
  { ruta: "/conferencias", texto: "Conferencias", roles: ["administrador", "comite", "autor"] },
  { ruta: "/perfil", texto: "Mi perfil", roles: ["administrador", "comite", "autor"] },
];

const ROLES = {
  administrador: "Administrador",
  comite: "Comité científico",
  autor: "Autor",
};

export default function MenuPrincipal() {
  const [abierto, setAbierto] = useState(false);
  const navigate = useNavigate();
  const rolActivo = obtenerRolActivo();
  const opciones = OPCIONES.filter((opcion) => opcion.roles.includes(rolActivo)); // Deja unicamente las opciones del rol activo, para que no se muestren opciones que no puede ver el usuario

  const handleCerrarSesion = () => {
    cerrarSesion();
    navigate("/login", { replace: true });
  };

  return (
    <div className="menu-pagina">
      <aside className="menu-lateral">
        <div className="menu-encabezado">
          <div className="menu-marca">
            <span className="menu-logo" aria-hidden="true">C</span>
            <span>Conecta</span>
          </div>
          <button
            className="menu-boton"
            type="button"
            aria-label="Abrir o cerrar menú"
            aria-expanded={abierto}
            onClick={() => setAbierto(!abierto)}
          >
            {abierto ? <X size={22} aria-hidden="true" /> : <Menu size={22} aria-hidden="true" />}
          </button>
        </div>

        <div className={`menu-contenido ${abierto ? "menu-contenido-abierto" : ""}`}>
          <p className="menu-rol">{ROLES[rolActivo]}</p>

          <nav className="menu-opciones" aria-label="Menú principal">
            {opciones.map((opcion) => (
                // Crea cada enlace y marca automaticamente la opcion abierta
              <NavLink key={opcion.ruta} to={opcion.ruta} onClick={() => setAbierto(false)}> 
                {opcion.texto}
              </NavLink>
            ))}
          </nav>

          <button className="boton boton-secundario" type="button" onClick={handleCerrarSesion}>
            Cerrar sesión
          </button>
        </div>
      </aside>
    
      <main className="menu-principal">
        <Outlet /> 
      </main>
    </div>
  );
}
