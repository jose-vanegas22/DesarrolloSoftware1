import api from "./axios";

export const getUsuarios = (filtros) => api.get("/usuarios/", { params: filtros }); // params agrega los filtros a la url para que el backend los reciba como query params
export const createUsuario = (datos) => api.post("/usuarios/", datos);
