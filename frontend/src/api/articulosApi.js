import api from "./axios";

export const getArticulos = (filtros) => api.get("/articulos/", { params: filtros }); // Para traer o listar
export const getArticulo = (id) => api.get(`/articulos/${id}/`);
export const evaluarArticulo = (id, datos) => api.post(`/articulos/${id}/evaluacion/`, datos);
export const quitarCoautor = (id, autorId) => api.delete(`/articulos/${id}/autores/${autorId}/`);
export const createArticulo = (datos) => api.post("/articulos/", datos); // Llama al endpoint para crear un articulo

export const subirPdf = (id, archivo) => {
  const datos = new FormData();
  datos.append("archivo", archivo);
  return api.post(`/articulos/${id}/pdf/`, datos);
};

export const reemplazarPdfArticulo = (id, formData) => {
  return api.patch(`/articulos/${id}/reemplazar-pdf/`, formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });
};
// Revisores asignados a un articulo
export const getRevisores = (id) => api.get(`/articulos/${id}/revisores/`);

// Asigna los tres revisores. revisores es una lista con los id de los usuarios
export const asignarRevisores = (id, revisores) => api.post(`/articulos/${id}/revisores/`, { revisores });
