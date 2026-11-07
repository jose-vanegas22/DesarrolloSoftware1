import api from "./axios";

export const getEventos = (filtros) => api.get("/eventos/", { params: filtros });
export const createEvento = (datos) => api.post("/eventos/", datos);
