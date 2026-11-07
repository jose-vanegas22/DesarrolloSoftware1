import api from "./axios";

export const getEventos = (filtros) => api.get("/eventos/", { params: filtros });
export const createEvento = (datos) => api.post("/eventos/", datos);
export const updateEvento = (id, datos) => api.patch(`/eventos/${id}/`, datos);
export const getFechasLimite = (id) => api.get(`/eventos/${id}/fechas-limite/`);
export const updateFechasLimite = (id, datos) => api.patch(`/eventos/${id}/fechas-limite/`, datos);