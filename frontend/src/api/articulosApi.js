import api from "./axios";

export const getArticulos = (filtros) => api.get("/articulos/", { params: filtros }); // Para traer o listar
export const createArticulo = (datos) => api.post("/articulos/", datos); // Llama al endpoint para crear un articulo