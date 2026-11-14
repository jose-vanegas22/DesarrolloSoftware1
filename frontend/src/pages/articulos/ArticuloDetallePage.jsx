import { ArrowLeft, X } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { Link, useParams } from "react-router";
import { getArticulo, reemplazarPdfArticulo } from "../../api/articulosApi";
import { obtenerRolActivo } from "../../api/authApi";
import QuitarCoautorModal from "./components/QuitarCoautorModal";
import "./ArticuloDetallePage.css";

const formatearFecha = (fecha) =>
  new Date(fecha).toLocaleString("es-CO", {
    day: "2-digit",
    month: "long",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });

export default function ArticuloDetallePage() {
  const { id } = useParams();
  const [articulo, setArticulo] = useState(null);
  const [error, setError] = useState("");
  const [coautorQuitado, setCoautorQuitado] = useState(null);
  const [mensaje, setMensaje] = useState("");
  const esAutor = obtenerRolActivo() === "autor";
  const [nuevoArchivo, setNuevoArchivo] = useState(null);
  const [cargandoPdf, setCargandoPdf] = useState(false);
  const [errorPdf, setErrorPdf] = useState("");
  const inputArchivoRef = useRef(null);

  useEffect(() => {
    setArticulo(null);
    setError("");
    getArticulo(id)
      .then(({ data }) => setArticulo(data))
      .catch((err) =>
        setError(
          err.response?.status === 404
            ? "No se encontró el artículo o no tienes permiso para verlo."
            : "No se pudo cargar el artículo."
        )
      );
  }, [id]);

  const handleCambioArchivo = (event) => {
    const file = event.target.files?.[0];
    setErrorPdf("");

    if (!file) {
      setNuevoArchivo(null);
      return;
    }

    if (file.type !== "application/pdf") {
      setErrorPdf("El archivo debe ser un PDF.");
      setNuevoArchivo(null);
      return;
    }

    setNuevoArchivo(file);
  };

  const handleReemplazarPdf = async (event) => {
    event.preventDefault();
    if (!nuevoArchivo) return;

    setCargandoPdf(true);
    setErrorPdf("");

    const formData = new FormData();
    formData.append("archivo", nuevoArchivo);

    try {
      await reemplazarPdfArticulo(articulo.id, formData);
      setMensaje("El PDF fue reemplazado correctamente.");
      setNuevoArchivo(null);
      if (inputArchivoRef.current) inputArchivoRef.current.value = "";
      setArticulo((prev) => ({
        ...prev,
        fecha_pdf: new Date().toISOString(),
      }));
    } catch (err) {
      const status = err.response?.status;
      setErrorPdf(
        status === 403
          ? "No tienes permiso para reemplazar el PDF de este artículo."
          : status === 413
            ? "El archivo es demasiado grande."
            : "No se pudo reemplazar el PDF. Intenta de nuevo."
      );
    } finally {
      setCargandoPdf(false);
    }
  };

  const handleQuitado = () => {
    const idQuitado = coautorQuitado.id;
    setArticulo((prev) => ({
      ...prev,
      autores: prev.autores.filter((autor) => autor.id !== idQuitado),
    }));
    setMensaje("Coautor quitado correctamente.");
    setCoautorQuitado(null);
  };

  const volver = (
    <Link className="detalle-volver" to="/articulos" aria-label="Volver a artículos">
      <ArrowLeft size={18} aria-hidden="true" />
    </Link>
  );

  if (!articulo) {
    return (
      <section className="detalle-pagina">
        <div className="detalle-encabezado">
          {volver}
          <h1>Detalle del artículo</h1>
        </div>
        {error ? <p className="mensaje-error">{error}</p> : <p>Cargando artículo...</p>}
      </section>
    );
  }

  return (
    <section className="detalle-pagina">
      <div className="detalle-encabezado">
        {volver}
        <div>
          <h1>{articulo.titulo}</h1>
          <span className="detalle-etiqueta">{articulo.estado_nombre}</span>
        </div>
      </div>

      {mensaje && <p className="mensaje-exito">{mensaje}</p>}

      <div className="detalle-columnas">
        <div className="detalle-columna">
          <div className="detalle-tarjeta">
            <h2>Información</h2>
            <dl className="detalle-datos">
              <div>
                <dt>Conferencia</dt>
                <dd>{articulo.evento_nombre}</dd>
              </div>
              <div>
                <dt>Línea temática</dt>
                <dd>{articulo.linea_tematica_nombre}</dd>
              </div>
              <div>
                <dt>Fecha de postulación</dt>
                <dd>{formatearFecha(articulo.creado)}</dd>
              </div>
            </dl>
            <h3>Resumen</h3>
            <p className="detalle-texto">{articulo.resumen}</p>
            <h3>Palabras clave</h3>
            <p className="detalle-texto">{articulo.palabras_clave}</p>
          </div>

          <div className="detalle-tarjeta">
            <h2>Autores</h2>
            <ul className="detalle-autores">
              {articulo.autores.map((autor, indice) => (
                <li key={autor.id}>
                  <div>
                    <strong>{autor.nombre}</strong>
                    {indice === 0 && <span className="detalle-etiqueta">Responsable</span>}
                    <p>{autor.afiliacion}</p>
                    <p>{autor.correo}</p>
                  </div>
                  {esAutor && articulo.postulacion_abierta && indice > 0 && (
                    <button
                      className="detalle-quitar"
                      type="button"
                      aria-label={`Quitar a ${autor.nombre}`}
                      title="Quitar coautor"
                      onClick={() => {
                        setMensaje("");
                        setCoautorQuitado(autor);
                      }}
                    >
                      <X size={16} aria-hidden="true" />
                    </button>
                  )}
                </li>
              ))}
            </ul>
          </div>
        </div>

        <div className="detalle-tarjeta">
          <h2>Artículo en PDF</h2>
          {articulo.fecha_pdf ? (
            <p className="detalle-texto">Entregado el {formatearFecha(articulo.fecha_pdf)}</p>
          ) : (
            <p className="detalle-texto">Todavía no se ha entregado el PDF.</p>
          )}

          {esAutor && articulo.postulacion_abierta ? (
            <form
              onSubmit={handleReemplazarPdf}
              style={{ marginTop: "1rem", borderTop: "1px solid #eee", paddingTop: "1rem" }}
            >
              <h3>Reemplazar archivo PDF</h3>
              <input
                ref={inputArchivoRef}
                type="file"
                accept="application/pdf"
                onChange={handleCambioArchivo}
                style={{ display: "block", margin: "0.5rem 0" }}
              />
              {errorPdf && <p style={{ color: "red", fontSize: "0.85rem" }}>{errorPdf}</p>}

              <button
                type="submit"
                disabled={!nuevoArchivo || cargandoPdf}
                style={{
                  marginTop: "0.5rem",
                  padding: "0.5rem 1rem",
                  cursor: nuevoArchivo ? "pointer" : "not-allowed",
                }}
              >
                {cargandoPdf ? "Subiendo..." : "Subir nuevo PDF"}
              </button>
            </form>
          ) : (
            <p style={{ fontSize: "0.85rem", color: "#666", marginTop: "1rem" }}>
              El plazo para reemplazar el PDF ha finalizado o no tienes permisos de autor.
            </p>
          )}
        </div>
      </div>

      {coautorQuitado && (
        <QuitarCoautorModal
          articuloId={articulo.id}
          coautor={coautorQuitado}
          onCerrar={() => setCoautorQuitado(null)}
          onQuitado={handleQuitado}
        />
      )}
    </section>
  );
}