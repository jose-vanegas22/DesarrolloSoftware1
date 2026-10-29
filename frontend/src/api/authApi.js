import api from "./axios";

export const iniciarSesion = async (username, password) => {
  const { data } = await api.post("/token/", { username, password });
  localStorage.setItem("access", data.access);
  localStorage.setItem("refresh", data.refresh);
};

export const cerrarSesion = () => {
  localStorage.removeItem("access");
  localStorage.removeItem("refresh");
};

export const haySesion = () => Boolean(localStorage.getItem("access"));
