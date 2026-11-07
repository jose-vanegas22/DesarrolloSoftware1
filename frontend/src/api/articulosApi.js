import api from "./axios";

export const createArticulo = (datos) => api.post("/articulos/", datos); // Llama al endpoint para crear un articulo