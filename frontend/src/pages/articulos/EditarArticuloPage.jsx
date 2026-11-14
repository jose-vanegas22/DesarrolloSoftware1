import { ArrowLeft } from "lucide-react";
import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router";
import { getArticulo, updateArticulo } from "../../api/articulosApi";
import CampoFormulario from "../../components/CampoFormulario";
import { LINEAS_TEMATICAS } from "./lineasTematicas";
import "./PostularArticuloPage.css";

const CAMPOS_EDITABLES = ["titulo", "resumen", "palabras_clave", "linea_tematica"];

// Toma del articulo solo los campos que el autor puede modificar
const tomarCamposEditables = (articulo) =>
  Object.fromEntries(CAMPOS_EDITABLES.map((campo) => [campo, articulo[campo] ?? ""]));

export default function EditarArticuloPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [articulo, setArticulo] = useState(null);
  const [formulario, setFormulario] = useState(null);
  const [errores, setErrores] = useState({});
  const [error, setError] = useState("");
  const [enviando, setEnviando] = useState(false);

  useEffect(() => {
    getArticulo(id)
      .then(({ data }) => {
        setArticulo(data);
        setFormulario(tomarCamposEditables(data));
      })
      .catch((err) => setError(err.response?.status === 404
        ? "No se encontró el artículo o no tienes permiso para editarlo."
        : "No se pudo cargar el artículo."));
  }, [id]);

  const handleChange = (e) => {
    setFormulario({ ...formulario, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrores({});

    // Con PATCH solo se envian los campos que el autor cambio
    const cambios = Object.fromEntries(
      Object.entries(formulario).filter(([campo, valor]) => valor !== (articulo[campo] ?? ""))
    );
    if (Object.keys(cambios).length === 0) {
      setErrores({ general: ["No has hecho ningún cambio."] });
      return;
    }

    setEnviando(true);
    try {
      await updateArticulo(id, cambios);
      navigate(`/articulos/${id}`, { state: { mensaje: "Artículo actualizado correctamente." } });
    } catch (err) {
      const estado = err.response?.status;
      const datos = err.response?.data;
      if (estado === 403) {
        setErrores({ general: [datos?.detail ?? "No tienes permiso para editar este artículo."] });
      } else if (estado === 404) {
        setErrores({ general: ["No se encontró el artículo o no tienes permiso para editarlo."] });
      } else {
        setErrores(typeof datos === "object" && datos !== null
          ? datos
          : { general: ["No se pudo actualizar el artículo. Intenta de nuevo."] });
      }
      setEnviando(false);
    }
  };

  const mostrarError = (campo) => errores[campo] && <p className="mensaje-error">{[errores[campo]].flat()[0]}</p>;

  const volver = (
    <Link className="articulo-volver" to={`/articulos/${id}`} aria-label="Volver al detalle del artículo">
      <ArrowLeft size={18} aria-hidden="true" />
    </Link>
  );

  if (!articulo) {
    return (
      <section className="articulo-pagina">
        <div className="articulo-encabezado">
          {volver}
          <h1>Editar artículo</h1>
        </div>
        {error ? <p className="mensaje-error">{error}</p> : <p>Cargando artículo...</p>}
      </section>
    );
  }

  // El backend tiene la ultima palabra, pero si ya sabemos que la postulacion cerro no dejamos editar
  const bloqueado = !articulo.postulacion_abierta;

  return (
    <section className="articulo-pagina">
      <div className="articulo-encabezado">
        {volver}
        <h1>Editar artículo</h1>
      </div>

      {bloqueado && (
        <p className="mensaje-error">
          La postulación de esta conferencia ya cerró, por eso no puedes modificar el artículo.
        </p>
      )}

      <form className="articulo-tarjeta" onSubmit={handleSubmit}>
        <fieldset className="articulo-datos" disabled={bloqueado || enviando}>
          <h2>Datos del artículo</h2>

          <div>
            <CampoFormulario id="editar-titulo" name="titulo" etiqueta="Título" maxLength={255} value={formulario.titulo} onChange={handleChange} required />
            {mostrarError("titulo")}
          </div>

          <div className="articulo-campos">
            <CampoFormulario id="editar-evento" etiqueta="Conferencia" value={articulo.evento_nombre} disabled />
            <div>
              <div className="campo">
                <label htmlFor="editar-linea">Línea temática</label>
                <select id="editar-linea" name="linea_tematica" value={formulario.linea_tematica} onChange={handleChange} required>
                  <option value="">Selecciona una línea</option>
                  {LINEAS_TEMATICAS.map((linea) => (
                    <option key={linea.valor} value={linea.valor}>{linea.texto}</option>
                  ))}
                </select>
              </div>
              {mostrarError("linea_tematica")}
            </div>
          </div>

          <div>
            <div className="campo">
              <label htmlFor="editar-resumen">Resumen</label>
              <textarea id="editar-resumen" name="resumen" rows={6} value={formulario.resumen} onChange={handleChange} required />
            </div>
            {mostrarError("resumen")}
          </div>

          <div>
            <CampoFormulario id="editar-palabras" name="palabras_clave" etiqueta="Palabras clave" maxLength={255} value={formulario.palabras_clave} onChange={handleChange} required />
            {mostrarError("palabras_clave")}
          </div>
        </fieldset>

        {mostrarError("non_field_errors")}
        {mostrarError("detail")}
        {mostrarError("general")}

        <div className="articulo-acciones">
          <Link className="boton boton-secundario" to={`/articulos/${id}`}>Cancelar</Link>
          <button className="boton boton-principal" type="submit" disabled={bloqueado || enviando}>
            {enviando ? "Guardando..." : "Guardar cambios"}
          </button>
        </div>
      </form>
    </section>
  );
}
