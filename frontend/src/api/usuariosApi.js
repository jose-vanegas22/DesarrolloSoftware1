import api from "./axios";

export const getUsuarios = (filtros) => api.get("/usuarios/", { params: filtros }); // params agrega los filtros a la url para que el backend los reciba como query params
export const createUsuario = (datos) => api.post("/usuarios/", datos);
export const updateUsuario = (id, datos) => api.patch(`/usuarios/${id}/`, datos);
export const deleteUsuario = (id) => api.delete(`/usuarios/${id}/`);
export const getPerfil = () => api.get("/usuarios/perfil/");
export const updatePerfil = (datos) => api.patch("/usuarios/perfil/", datos);