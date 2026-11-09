import api from "./axios";

// localStorage es un objeto que permite almacenar datos en el navegador del usuario de manera persistente, incluso después de cerrar la pestaña o el navegador. 
// En este caso, se utiliza para guardar información relacionada con la sesión del usuario, como tokens de acceso y roles.
const guardarSesion = ({ access, refresh, roles, rol_activo }) => {
  localStorage.setItem("access", access);
  localStorage.setItem("refresh", refresh);
  localStorage.setItem("roles", JSON.stringify(roles)); // Se convierte el array de roles a una cadena JSON antes de guardarlo en localStorage

  if (rol_activo) {
    localStorage.setItem("rol_activo", rol_activo); // Se guarda el rol activo en localStorage si está presente
  } else {
    localStorage.removeItem("rol_activo");
  }
};

// Envia una solicitud POST al endpoint "/token/" con el correo, la contraseña y el captcha del usuario.
export const iniciarSesion = async (correo, password, captcha) => {
  const { data } = await api.post("/token/", { correo, password, captcha });
  guardarSesion(data);
  return data;
};

// async para indicar que debe esperar  y await para decirle que espere hasta aqui la respuesta
// const { data } es para que tome la parte util de la respuesta y no el json completo que devuelve mucha cosa
export const seleccionarRol = async (rol) => {
  const { data } = await api.post("/usuarios/seleccionar-rol/", { rol }); // api porque es la instancia de axios y post metodo HTTP para enviar los datos
  guardarSesion(data); // Le pasa la respuesta a la funcion que guarda la sesion en localStorage navegador
  return data;  // Entrega los datos a quien llama a la funcion, en este caso el componente Login.jsx
};


// Envia los datos del formulario para que se cree la cuenta del autor en el backend. La función devuelve la respuesta del servidor, que puede incluir información sobre el éxito o fracaso del registro.
export const registrarAutor = (datos) => api.post("/usuarios/registro/", datos); 


// Invalida el refresh token en el backend y luego borra los datos del navegador
export const cerrarSesion = async () => {
  const refresh = localStorage.getItem("refresh");

  try {
    if (refresh) await api.post("/token/blacklist/", { refresh });
  } catch {
    // Si el backend no responde, igual se cierra la sesion en el navegador
  }

  localStorage.removeItem("access");
  localStorage.removeItem("refresh");
  localStorage.removeItem("roles");
  localStorage.removeItem("rol_activo");
};

export const haySesion = () => Boolean(localStorage.getItem("access"));

export const obtenerRoles = () => JSON.parse(localStorage.getItem("roles") ?? "[]");

export const obtenerRolActivo = () => localStorage.getItem("rol_activo");
