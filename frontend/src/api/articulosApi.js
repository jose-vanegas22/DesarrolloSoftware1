import api from "./axios";

export const getArticulos = (filtros) => api.get("/articulos/", { params: filtros }); // Para traer o listar
export const getArticulo = (id) => api.get(`/articulos/${id}/`);
export const quitarCoautor = (id, autorId) => api.delete(`/articulos/${id}/autores/${autorId}/`);
export const createArticulo = (datos) => api.post("/articulos/", datos); // Llama al endpoint para crear un articulo

export const subirPdf = (id, archivo) => {
  const datos = new FormData();
  datos.append("archivo", archivo);
  return api.post(`/articulos/${id}/pdf/`, datos);
};