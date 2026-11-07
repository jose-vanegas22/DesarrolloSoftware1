import { Filter } from "lucide-react";
import { useState } from "react";
import CampoFormulario from "../../../components/CampoFormulario";

const FILTROS_INICIALES = { buscar: "", rol: "", activo: "" }; // Para limpiar el formulario

// Este componente es un formulario que permite filtrar los usuarios por nombre, apellido, correo, rol y estado. Al enviar el formulario, 
// llama a la función onFiltrar con los filtros seleccionados. Al limpiar el formulario, llama a onFiltrar con los filtros iniciales.
export default function UsuariosFiltros({ onFiltrar }) {
  const [filtros, setFiltros] = useState(FILTROS_INICIALES); // Valores actuales y los cambia

  // Cambia el valor del filtro correspondiente al input que se modificó
  const handleChange = (e) => {
    setFiltros({ ...filtros, [e.target.name]: e.target.value });
  };
 
  // Caundo se presiona el boton de filtrar
  const handleSubmit = (e) => {
    e.preventDefault(); // Evita que la pagina se recargue al enviar el formulario
    onFiltrar(filtros); // Le entrega los filtros al componente padre
  };

  // Cuando se presiona el boton de limpiar
  const handleLimpiar = () => {
    setFiltros(FILTROS_INICIALES);
    onFiltrar(FILTROS_INICIALES);
  };

  return (
    <form className="usuarios-filtros" onSubmit={handleSubmit}>
      <CampoFormulario
        id="filtro-buscar"
        name="buscar"
        etiqueta="Buscar"
        placeholder="Nombre, apellido o correo"
        value={filtros.buscar}
        onChange={handleChange}
      />

      <div className="campo">
        <label htmlFor="filtro-rol">Rol</label>
        <select id="filtro-rol" name="rol" value={filtros.rol} onChange={handleChange}>
          <option value="">Todos</option>
          <option value="administrador">Administrador</option>
          <option value="comite">Comité científico</option>
          <option value="autor">Autor</option>
        </select>
      </div>

      <div className="campo">
        <label htmlFor="filtro-activo">Estado</label>
        <select id="filtro-activo" name="activo" value={filtros.activo} onChange={handleChange}>
          <option value="">Todos</option>
          <option value="true">Activo</option>
          <option value="false">Inactivo</option>
        </select>
      </div>

      <button className="boton boton-principal" type="submit">
        <Filter size={16} aria-hidden="true" />
        Filtrar
      </button>
      <button className="boton boton-secundario" type="button" onClick={handleLimpiar}>Limpiar</button>
    </form>
  );
}
