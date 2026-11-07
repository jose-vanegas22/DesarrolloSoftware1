import { ArrowLeft, Plus, X } from "lucide-react";
import { useEffect, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router";
import { createArticulo } from "../../api/articulosApi";
import { getEventos } from "../../api/eventosApi";
import { getPerfil } from "../../api/usuariosApi";
import CampoFormulario from "../../components/CampoFormulario";
import "./PostularArticuloPage.css";

const LINEAS_TEMATICAS = [
  { valor: "sistemas_inteligentes", texto: "Sistemas Inteligentes" },
  { valor: "tecnologias_informatica", texto: "Tecnologías en Informática" },
  { valor: "educacion_informatica", texto: "Educación en Informática" },
  { valor: "sistemas_software", texto: "Sistemas de Software" },
  { valor: "software_practica", texto: "Software en la práctica" },
];

export default function PostularArticuloPage() {
  const [parametros] = useSearchParams(); // Nos ayuda a ller el evento que esta seleccionado en la URL para dejarla seleccionada
  const navigate = useNavigate();
  const [conferencias, setConferencias] = useState([]);
  const [autor, setAutor] = useState(null);
  const [formulario, setFormulario] = useState({
    evento: parametros.get("evento") ?? "",
    titulo: "",
    resumen: "",
    palabras_clave: "",
    linea_tematica: "",
    afiliacion: "",
  });
  const [coautores, setCoautores] = useState([]);
  const [errores, setErrores] = useState({});
  const [error, setError] = useState("");
  const [enviando, setEnviando] = useState(false);

  // Carga al mismo tiempo los eventos y el perfil del autor, para que no se haga una llamada tras otra y se demore mas
  useEffect(() => {
    Promise.all([getEventos({}), getPerfil()])
      .then(([eventos, perfil]) => {
        const abiertas = eventos.data.filter((conferencia) => conferencia.postulacion_abierta);
        setConferencias(abiertas);
        setAutor(perfil.data);
        setFormulario((actual) => ( // Si el evento que estaba seleccionado en la URL ya no esta en la lista de conferencias abiertas, lo dejamos vacio
          abiertas.some((conferencia) => String(conferencia.id) === actual.evento)
            ? actual
            : { ...actual, evento: "" }
        ));
      })
      .catch(() => setError("No se pudo cargar el formulario."));
  }, []);

  const handleChange = (e) => {
    setFormulario({ ...formulario, [e.target.name]: e.target.value });
  };

  const handleAgregarCoautor = () => {
    setCoautores([...coautores, { nombre: "", afiliacion: "", correo: "" }]);
  };

  const handleQuitarCoautor = (indice) => {
    setCoautores(coautores.filter((_, posicion) => posicion !== indice));
    setErrores({});
  };

  const handleChangeCoautor = (indice, e) => {
    setCoautores(coautores.map((coautor, posicion) => (
      posicion === indice ? { ...coautor, [e.target.name]: e.target.value } : coautor
    )));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrores({});
    setEnviando(true);

    try {
      await createArticulo({ ...formulario, coautores });
      navigate("/conferencias", { state: { mensaje: "Artículo postulado correctamente." } }); // Redirige a la pagina de conferencias y le pasa un mensaje cuando el articulo se creo con exito
    } catch (err) {
      const datos = err.response?.data;
      setErrores(typeof datos === "object" && datos !== null
        ? datos
        : { general: ["No se pudo postular el artículo. Intenta de nuevo."] });
      setEnviando(false);
    }
  };

  const mostrarError = (campo) => errores[campo] && <p className="mensaje-error">{[errores[campo]].flat()[0]}</p>;

  const errorCoautor = (indice, campo) => {
    const mensaje = errores.coautores?.[indice]?.[campo]?.[0];
    return mensaje && <p className="mensaje-error">{mensaje}</p>;
  };

  if (!autor) {
    return (
      <section className="articulo-pagina">
        <h1>Postular artículo</h1>
        {error ? <p className="mensaje-error">{error}</p> : <p>Cargando formulario...</p>}
      </section>
    );
  }

  return (
    <section className="articulo-pagina">
      <div className="articulo-encabezado">
        <Link className="articulo-volver" to="/conferencias" aria-label="Volver a conferencias">
          <ArrowLeft size={18} aria-hidden="true" />
        </Link>
        <h1>Postular artículo</h1>
      </div>

      <form className="articulo-tarjeta" onSubmit={handleSubmit}>
        <h2>Datos del artículo</h2>

        <div>
          <CampoFormulario id="articulo-titulo" name="titulo" etiqueta="Título" maxLength={255} value={formulario.titulo} onChange={handleChange} required />
          {mostrarError("titulo")}
        </div>

        <div className="articulo-campos">
          <div>
            <div className="campo">
              <label htmlFor="articulo-evento">Conferencia</label>
              <select id="articulo-evento" name="evento" value={formulario.evento} onChange={handleChange} required>
                <option value="">Selecciona una conferencia</option>
                {conferencias.map((conferencia) => (
                  <option key={conferencia.id} value={conferencia.id}>{conferencia.nombre}</option>
                ))}
              </select>
            </div>
            {mostrarError("evento")}
          </div>
          <div>
            <div className="campo">
              <label htmlFor="articulo-linea">Línea temática</label>
              <select id="articulo-linea" name="linea_tematica" value={formulario.linea_tematica} onChange={handleChange} required>
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
            <label htmlFor="articulo-resumen">Resumen</label>
            <textarea id="articulo-resumen" name="resumen" rows={5} value={formulario.resumen} onChange={handleChange} required />
          </div>
          {mostrarError("resumen")}
        </div>

        <div>
          <CampoFormulario id="articulo-palabras" name="palabras_clave" etiqueta="Palabras clave" maxLength={255} value={formulario.palabras_clave} onChange={handleChange} required />
          {mostrarError("palabras_clave")}
        </div>

        <h2>Autor responsable</h2>

        <div className="articulo-autor">
          <CampoFormulario id="articulo-nombre" etiqueta="Nombre" value={`${autor.nombres} ${autor.apellidos}`} disabled />
          <div>
            <CampoFormulario id="articulo-afiliacion" name="afiliacion" etiqueta="Afiliación universitaria" maxLength={200} value={formulario.afiliacion} onChange={handleChange} required />
            {mostrarError("afiliacion")}
          </div>
          <CampoFormulario id="articulo-correo" etiqueta="Correo electrónico" type="email" value={autor.correo} disabled />
        </div>

        
        <h2>Coautores</h2>

        {coautores.map((coautor, indice) => (
          <div className="articulo-coautor" key={indice}>
            <div>
              <CampoFormulario id={`coautor-nombre-${indice}`} name="nombre" etiqueta="Nombre" maxLength={200} value={coautor.nombre} onChange={(e) => handleChangeCoautor(indice, e)} required />
              {errorCoautor(indice, "nombre")}
            </div>
            <div>
              <CampoFormulario id={`coautor-afiliacion-${indice}`} name="afiliacion" etiqueta="Afiliación universitaria" maxLength={200} value={coautor.afiliacion} onChange={(e) => handleChangeCoautor(indice, e)} required />
              {errorCoautor(indice, "afiliacion")}
            </div>
            <div>
              <CampoFormulario id={`coautor-correo-${indice}`} name="correo" etiqueta="Correo electrónico" type="email" value={coautor.correo} onChange={(e) => handleChangeCoautor(indice, e)} required />
              {errorCoautor(indice, "correo")}
            </div>
            <button className="articulo-quitar" type="button" aria-label={`Quitar coautor ${indice + 1}`} title="Quitar coautor" onClick={() => handleQuitarCoautor(indice)}>
              <X size={18} aria-hidden="true" />
            </button>
          </div>
        ))}

        {typeof errores.coautores?.[0] === "string" && <p className="mensaje-error">{errores.coautores[0]}</p>}

        <button className="boton boton-secundario articulo-agregar" type="button" onClick={handleAgregarCoautor}>
          <Plus size={16} aria-hidden="true" />
          Agregar coautor
        </button>

        {mostrarError("non_field_errors")}
        {mostrarError("detail")}
        {mostrarError("general")}

        <div className="articulo-acciones">
          <Link className="boton boton-secundario" to="/conferencias">Cancelar</Link>
          <button className="boton boton-principal" type="submit" disabled={enviando}>
            {enviando ? "Postulando..." : "Postular artículo"}
          </button>
        </div>
      </form>
    </section>
  );
}
