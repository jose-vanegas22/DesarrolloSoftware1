import { useState } from "react";
import { NavLink, Outlet, useNavigate } from "react-router";
import { cerrarSesion, obtenerRolActivo } from "../api/authApi";
import "./MenuPrincipal.css";
import { CalendarDays, House, LogOut, Menu, PanelLeftClose, PanelLeftOpen, UserRound, Users, X } from "lucide-react";


// Indica que opciones puede ver cada rol, y el texto que se muestra en el menu
const OPCIONES = [
  { ruta: "/inicio", texto: "Inicio", icono: House, roles: ["administrador", "comite", "autor"] },
  { ruta: "/usuarios", texto: "Usuarios", icono: Users, roles: ["administrador", "comite"] },
  { ruta: "/conferencias", texto: "Conferencias", icono: CalendarDays, roles: ["administrador", "comite", "autor"] },
  { ruta: "/perfil", texto: "Mi perfil", icono: UserRound, roles: ["administrador", "comite", "autor"] },
];

const ROLES = {
  administrador: "Administrador",
  comite: "Comité científico",
  autor: "Autor",
};

export default function MenuPrincipal() {
  const [abierto, setAbierto] = useState(false);
  const [colapsado, setColapsado] = useState(false);
  const navigate = useNavigate();
  const rolActivo = obtenerRolActivo();
  const opciones = OPCIONES.filter((opcion) => opcion.roles.includes(rolActivo)); // Deja unicamente las opciones del rol activo, para que no se muestren opciones que no puede ver el usuario

  const handleCerrarSesion = () => {
    cerrarSesion();
    navigate("/login", { replace: true });
  };

  return (
    <div className="menu-pagina">
      <aside className={`menu-lateral ${colapsado ? "menu-colapsado" : ""}`}>
        <div className="menu-encabezado">
          <div className="menu-marca">
            <span className="menu-logo" aria-hidden="true">C</span>
            <span className="menu-texto">Conecta</span>
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
              <NavLink key={opcion.ruta} to={opcion.ruta} aria-label={opcion.texto} title={opcion.texto} onClick={() => setAbierto(false)}>
                <opcion.icono size={18} aria-hidden="true" />
                <span className="menu-texto">{opcion.texto}</span>
              </NavLink>
            ))}
          </nav>

          <button className="boton boton-secundario menu-cerrar-sesion" type="button" aria-label="Cerrar sesión" title="Cerrar sesión" onClick={handleCerrarSesion}>
            <LogOut size={18} aria-hidden="true" />
            <span className="menu-texto">Cerrar sesión</span>
          </button>
          <button
            className="menu-colapsar"
            type="button"
            aria-label={colapsado ? "Expandir menú" : "Colapsar menú"}
            aria-expanded={!colapsado}
            title={colapsado ? "Expandir menú" : "Colapsar menú"}
            onClick={() => setColapsado(!colapsado)}
          >
            {colapsado ? <PanelLeftOpen size={18} aria-hidden="true" /> : <PanelLeftClose size={18} aria-hidden="true" />}
          </button>

        </div>
      </aside>
    
      <main className="menu-principal">
        <Outlet /> 
      </main>
    </div>
  );
}
