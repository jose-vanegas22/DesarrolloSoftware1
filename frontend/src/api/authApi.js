import api from "./axios";

export const iniciarSesion = async (correo, password, captcha) => {
  const { data } = await api.post("/token/", { correo, password, captcha });
  localStorage.setItem("access", data.access);
  localStorage.setItem("refresh", data.refresh);
};


export const cerrarSesion = () => {
  localStorage.removeItem("access");
  localStorage.removeItem("refresh");
};

export const haySesion = () => Boolean(localStorage.getItem("access"));
