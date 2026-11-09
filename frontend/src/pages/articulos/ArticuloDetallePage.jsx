import { ArrowLeft } from "lucide-react";
import { useEffect, useState } from "react";
import { Link, useParams } from "react-router";
import { getArticulo } from "../../api/articulosApi";
import "./ArticuloDetallePage.css";

const formatearFecha = (fecha) =>
  new Date(fecha).toLocaleString("es-CO", { day: "2-digit", month: "long", year: "numeric", hour: "2-digit", minute: "2-digit" });

export default function ArticuloDetallePage() {
  const { id } = useParams();
  const [articulo, setArticulo] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    getArticulo(id)
      .then(({ data }) => setArticulo(data))
      .catch((err) => setError(err.response?.status === 404
        ? "No se encontró el artículo o no tienes permiso para verlo."
        : "No se pudo cargar el artículo."));
  }, [id]);

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
                <li key={autor.correo}>
                  <strong>{autor.nombre}</strong>
                  {indice === 0 && <span className="detalle-etiqueta">Responsable</span>}
                  <p>{autor.afiliacion}</p>
                  <p>{autor.correo}</p>
                </li>
              ))}
            </ul>
          </div>
        </div>

        <div className="detalle-tarjeta">
          <h2>Artículo en PDF</h2>
          {articulo.fecha_pdf
            ? <p className="detalle-texto">Entregado el {formatearFecha(articulo.fecha_pdf)}</p>
            : <p className="detalle-texto">Todavía no se ha entregado el PDF.</p>}
        </div>
      </div>
    </section>
  );
}
