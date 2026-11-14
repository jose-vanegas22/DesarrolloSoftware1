import { ArrowLeft } from "lucide-react";
import { useEffect, useState } from "react";
import { Link, useParams } from "react-router";
import { asignarRevisores, getArticulo, getRevisores } from "../../api/articulosApi";
import { getUsuarios } from "../../api/usuariosApi";
import "./ArticuloDetallePage.css";
import "./AsignarRevisoresPage.css";

const TOTAL_REVISORES = 3;

const obtenerMensajeError = (err) => {
    const estado = err.response?.status;
    const datos = err.response?.data;

    if (!err.response) return "No hay conexión con el servidor. Intenta de nuevo.";
    if (estado === 403) return "No tienes permiso para asignar revisores.";
    if (estado === 404) return "No se encontró el artículo.";
    if (typeof datos === "string") return "No se pudieron asignar los revisores.";
    if (datos?.detail) return datos.detail;


    const mensajes = Object.values(datos || {}).flat().filter((mensaje) => typeof mensaje === "string");
    return mensajes.length > 0 ? mensajes.join(" ") : "No se pudieron asignar los revisores.";
};

export default function AsignarRevisoresPage() {
    const { id } = useParams();
    const [articulo, setArticulo] = useState(null);
    const [comite, setComite] = useState([]);
    const [seleccionados, setSeleccionados] = useState([]);
    const [error, setError] = useState("");
    const [mensaje, setMensaje] = useState("");
    const [guardando, setGuardando] = useState(false);

    useEffect(() => {

        Promise.all([getArticulo(id), getUsuarios({ rol: "comite" })])
            .then(([respuestaArticulo, respuestaComite]) => {
                setArticulo(respuestaArticulo.data);
                setComite(respuestaComite.data);
            })
            .catch(() => setError("No se pudo cargar la información del artículo."));


        getRevisores(id)
            .then(({ data }) => setSeleccionados(data.map((asignacion) => asignacion.revisor)))
            .catch(() => { });
    }, [id]);

    const handleMarcar = (usuarioId) => {
        setMensaje("");
        if (seleccionados.includes(usuarioId)) {
            setSeleccionados(seleccionados.filter((actual) => actual !== usuarioId));
        } else if (seleccionados.length < TOTAL_REVISORES) {
            setSeleccionados([...seleccionados, usuarioId]);
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError("");
        setMensaje("");
        setGuardando(true);
        try {
            await asignarRevisores(id, seleccionados);
            setMensaje("Revisores asignados correctamente.");
        } catch (err) {
            setError(obtenerMensajeError(err));
        } finally {
            setGuardando(false);
        }
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
                    <h1>Asignar revisores</h1>
                </div>
                {error ? <p className="mensaje-error">{error}</p> : <p>Cargando...</p>}
            </section>
        );
    }

    // Un autor o coautor no puede revisar su propio articulo
    const correosAutores = articulo.autores.map((autor) => autor.correo.toLowerCase());
    const candidatos = comite.filter((usuario) => !correosAutores.includes(usuario.correo.toLowerCase()));

    return (
        <section className="detalle-pagina">
            <div className="detalle-encabezado">
                {volver}
                <div>
                    <h1>Asignar revisores</h1>
                    <span className="detalle-etiqueta">{articulo.linea_tematica_nombre}</span>
                </div>
            </div>

            {error && <p className="mensaje-error">{error}</p>}
            {mensaje && <p className="mensaje-exito">{mensaje}</p>}
            {articulo.postulacion_abierta && (
                <p className="mensaje-error">
                    La postulación de esta conferencia sigue abierta. Podrás asignar revisores cuando termine.
                </p>
            )}

            <form className="detalle-tarjeta" onSubmit={handleSubmit}>

                <h2>{articulo.titulo}</h2>
                <p className="detalle-texto">
                    Selecciona {TOTAL_REVISORES} miembros del comité. Llevas {seleccionados.length} de {TOTAL_REVISORES}.
                </p>

                {candidatos.length === 0 ? (
                    <p className="detalle-texto">No hay miembros del comité disponibles.</p>
                ) : (
                    <ul className="revisores-lista">
                        {candidatos.map((usuario) => {
                            const marcado = seleccionados.includes(usuario.id);
                            return (
                                <li key={usuario.id}>
                                    <label>
                                        <input
                                            type="checkbox"
                                            checked={marcado}
                                            disabled={!marcado && seleccionados.length >= TOTAL_REVISORES}
                                            onChange={() => handleMarcar(usuario.id)}
                                        />
                                        <span>
                                            <strong>{usuario.nombres} {usuario.apellidos}</strong>
                                            <small>{usuario.correo}</small>
                                        </span>
                                    </label>
                                </li>
                            );
                        })}
                    </ul>
                )}

                <button
                    className="boton boton-principal"
                    type="submit"
                    disabled={seleccionados.length !== TOTAL_REVISORES || guardando || articulo.postulacion_abierta}
                >
                    {guardando ? "Guardando..." : "Asignar revisores"}
                </button>
            </form>
        </section>
    );
}